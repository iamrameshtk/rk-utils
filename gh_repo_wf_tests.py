#!/usr/bin/env python3
"""
GitHub Workflow Log Analyzer

This script extracts test results from GitHub workflow logs for specified workflows.
It retrieves the latest run for each workflow and parses logs to report test success/failure counts.

Usage:
  python github_workflow_logs.py --org <organization> --repo <repository>
  python github_workflow_logs.py --file <repos_file_path>

  At least one of the above parameter combinations must be provided.

Environment variables:
  GITHUB_TOKEN - GitHub Personal Access Token with appropriate permissions

Output:
  An Excel report containing the workflow test results
"""

import os
import sys
import re
import json
import argparse
import requests
from datetime import datetime
import pandas as pd

# Constants
GITHUB_API_URL = "https://api.github.com"
WORKFLOWS = {
    "core-checkov-action.yml": {
        "job_name": "checkov-action",
        "stage_name": "Run Checkov action",
        "parser": "parse_checkov_logs"
    },
    "terraform-module-unit-tests.yml": {
        "job_name": "terraform-init-plan",
        "stage_name": "Terraform test",
        "parser": "parse_terraform_logs"
    },
    "core-terraform-module-integration-tests.yml": {
        "job_name": "terraform-init-plan",
        "stage_name": "Run GCP Inspec",
        "parser": "parse_inspec_logs"
    }
}

def get_github_token():
    """Get GitHub token from environment variable."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is not set.")
        sys.exit(1)
    return token

def get_headers(token):
    """Return headers for GitHub API requests."""
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

def load_repositories_from_file(file_path):
    """Load repository list from the given file."""
    try:
        with open(file_path, 'r') as file:
            repos = []
            for line in file:
                line = line.strip()
                if not line:
                    continue
                if '/' in line:
                    repos.append(line)
                else:
                    print(f"Warning: Invalid repository format in line: {line}. Expected format: 'org/repo'")
            return repos
    except FileNotFoundError:
        print(f"Error: Repository list file '{file_path}' not found.")
        sys.exit(1)

def get_workflow_runs(repo, workflow_id, headers):
    """Get the latest workflow run for the specified workflow."""
    url = f"{GITHUB_API_URL}/repos/{repo}/actions/workflows/{workflow_id}/runs"
    
    # Try first with exact workflow ID
    response = requests.get(url, headers=headers, params={"per_page": 1})
    
    # If not found, try to list all workflows and find a match
    if response.status_code == 404:
        print(f"Workflow {workflow_id} not found directly. Attempting to find it in the workflow list.")
        
        # Get all workflows
        all_workflows_url = f"{GITHUB_API_URL}/repos/{repo}/actions/workflows"
        all_response = requests.get(all_workflows_url, headers=headers)
        
        if all_response.status_code == 200:
            all_workflows = all_response.json().get("workflows", [])
            matching_workflow = None
            
            # Look for exact or partial match
            for workflow in all_workflows:
                wf_name = workflow.get("name", "")
                wf_id = workflow.get("id")
                wf_path = workflow.get("path", "")
                
                # Check if name contains our target ID without the .yml extension
                if (workflow_id.replace(".yml", "") in wf_name.lower() or 
                    workflow_id in wf_path):
                    matching_workflow = workflow
                    print(f"Found matching workflow: {wf_name} (ID: {wf_id})")
                    break
            
            if matching_workflow:
                # Try again with the workflow ID
                wf_id = matching_workflow.get("id")
                url = f"{GITHUB_API_URL}/repos/{repo}/actions/workflows/{wf_id}/runs"
                response = requests.get(url, headers=headers, params={"per_page": 1})
    
    if response.status_code != 200:
        print(f"Error fetching workflow runs: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    if data.get("total_count", 0) == 0:
        print(f"No runs found for workflow {workflow_id}")
        return None
    
    return data["workflow_runs"][0]

def get_job_details(repo, run_id, headers):
    """Get job details for a specific workflow run."""
    url = f"{GITHUB_API_URL}/repos/{repo}/actions/runs/{run_id}/jobs"
    
    # GitHub API may paginate results, so we need to handle multiple pages
    all_jobs = []
    page = 1
    per_page = 100
    
    while True:
        params = {
            "per_page": per_page,
            "page": page
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching job details (page {page}): {response.status_code}")
            print(response.text)
            break
        
        data = response.json()
        jobs = data.get("jobs", [])
        all_jobs.extend(jobs)
        
        # Check if we need to fetch more pages
        if len(jobs) < per_page:
            break
            
        page += 1
    
    print(f"Retrieved {len(all_jobs)} jobs for run ID {run_id}")
    return all_jobs

def get_job_logs(repo, job_id, headers):
    """Get logs for a specific job."""
    url = f"{GITHUB_API_URL}/repos/{repo}/actions/jobs/{job_id}/logs"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching job logs: {response.status_code}")
        return None
    
    log_content = response.text
    
    # Simple validation check
    if not log_content or len(log_content.strip()) < 10:
        print(f"Warning: Retrieved log content is empty or too short for job ID {job_id}")
    
    print(f"Successfully retrieved logs for job {job_id} - {len(log_content)} characters")
    return log_content

def parse_checkov_logs(logs):
    """Parse Checkov logs to extract test counts."""
    if not logs:
        return {"status": "Not Run", "passed": 0, "failed": 0, "skipped": 0}
    
    # First try the exact pattern mentioned in requirements
    pattern = r"terraform scan results:\s*\n\s*Passed checks: (\d+), Failed checks: (\d+), Skipped checks: (\d+)"
    match = re.search(pattern, logs)
    
    # If not found, try a more general pattern
    if not match:
        pattern = r"Passed checks: (\d+), Failed checks: (\d+), Skipped checks: (\d+)"
        match = re.search(pattern, logs)
    
    # If still not found, try another common format
    if not match:
        pattern = r"PASSED: (\d+)\s+FAILED: (\d+)\s+SKIPPED: (\d+)"
        match = re.search(pattern, logs)
        
    if match:
        return {
            "status": "Success" if int(match.group(2)) == 0 else "Failed",
            "passed": int(match.group(1)),
            "failed": int(match.group(2)),
            "skipped": int(match.group(3))
        }
    
    # Log sections of the logs for debugging
    if logs:
        print("Warning: Unable to parse Checkov logs. Here's a sample:")
        print(logs[:500] + "..." if len(logs) > 500 else logs)
    
    return {"status": "Log parsing failed", "passed": 0, "failed": 0, "skipped": 0}

def parse_terraform_logs(logs):
    """Parse Terraform test logs to extract test counts."""
    if not logs:
        return {"status": "Not Run", "passed": 0, "failed": 0}
    
    # Print first few characters for debugging
    print(f"Parsing Terraform logs (first 100 chars): {logs[:100]}...")
    
    # First try the exact pattern mentioned in requirements (case insensitive)
    pattern = r"Success!\s*(\d+)\s+passed,\s*(\d+)\s+failed"
    match = re.search(pattern, logs, re.IGNORECASE)
    
    # If not found, try alternative formats
    if not match:
        pattern = r"(\d+)\s+passing,\s*(\d+)\s+failing"
        match = re.search(pattern, logs, re.IGNORECASE)
    
    # Try another common format
    if not match:
        pattern = r"Tests:\s*(\d+)\s+passed,\s*(\d+)\s+failed"
        match = re.search(pattern, logs, re.IGNORECASE)
    
    # Try format with parentheses
    if not match:
        pattern = r"(\d+)\s+tests\s+passed\s*\((\d+)\s+failed\)"
        match = re.search(pattern, logs, re.IGNORECASE)
    
    # Try plain "passed/failed" format
    if not match:
        passed_match = re.search(r"(\d+)\s+passed", logs, re.IGNORECASE)
        failed_match = re.search(r"(\d+)\s+failed", logs, re.IGNORECASE)
        if passed_match and failed_match:
            return {
                "status": "Success" if int(failed_match.group(1)) == 0 else "Failed",
                "passed": int(passed_match.group(1)),
                "failed": int(failed_match.group(1))
            }
    
    # Try extracting numbers after specific keywords
    if not match:
        all_pass_matches = re.findall(r"[Pp]ass(?:ed|ing)[:=\s]+(\d+)", logs)
        all_fail_matches = re.findall(r"[Ff]ail(?:ed|ing|ures)[:=\s]+(\d+)", logs)
        
        if all_pass_matches and all_fail_matches:
            # Use the largest numbers found as they're likely the summary
            passed = max([int(x) for x in all_pass_matches]) if all_pass_matches else 0
            failed = max([int(x) for x in all_fail_matches]) if all_fail_matches else 0
            return {
                "status": "Success" if failed == 0 else "Failed",
                "passed": passed,
                "failed": failed
            }
        
    if match:
        return {
            "status": "Success" if int(match.group(2)) == 0 else "Failed",
            "passed": int(match.group(1)),
            "failed": int(match.group(2))
        }
    
    # As a fallback, search for text lines containing the specific format mentioned
    exact_format_line = None
    for line in logs.splitlines():
        if "Success!" in line and "passed" in line and "failed" in line:
            exact_format_line = line
            break
    
    if exact_format_line:
        nums = re.findall(r'\d+', exact_format_line)
        if len(nums) >= 2:
            return {
                "status": "Success" if int(nums[1]) == 0 else "Failed",
                "passed": int(nums[0]),
                "failed": int(nums[1])
            }
    
    # Log sections of the logs for debugging
    if logs:
        print("Warning: Unable to parse Terraform logs. Here's a sample:")
        print("First 200 chars:")
        print(logs[:200])
        print("\nLast 200 chars:")
        print(logs[-200:])
        
        # Extract lines containing keywords that might help diagnosis
        keywords = ["test", "pass", "fail", "success"]
        relevant_lines = []
        for line in logs.splitlines():
            if any(keyword in line.lower() for keyword in keywords):
                relevant_lines.append(line)
        
        if relevant_lines:
            print("\nRelevant lines containing test-related keywords:")
            for line in relevant_lines[:10]:  # Print first 10 relevant lines
                print(f"  {line}")
    
    return {"status": "Log parsing failed", "passed": 0, "failed": 0}

def parse_inspec_logs(logs):
    """Parse Chef Inspec logs to extract test counts."""
    if not logs:
        return {"status": "Not Run", "passed": 0, "failed": 0, "skipped": 0}
    
    # Print first few characters for debugging
    print(f"Parsing InSpec logs (first 100 chars): {logs[:100]}...")
    
    # First try the Test Summary exact pattern mentioned in requirements (case insensitive)
    test_summary_pattern = r"Test Summary:\s*(\d+)\s+successful,\s*(\d+)\s+failures,\s*(\d+)\s+skipped"
    test_match = re.search(test_summary_pattern, logs, re.IGNORECASE)
    
    # Also look for Profile Summary pattern
    profile_summary_pattern = r"Profile Summary:\s*(\d+)\s+successful\s+Control,\s*(\d+)\s+failures,\s*(\d+)\s+controls\s+skipped"
    profile_match = re.search(profile_summary_pattern, logs, re.IGNORECASE)
    
    # If both patterns are found, prefer the Test Summary as it typically has more detailed counts
    if test_match and profile_match:
        return {
            "status": "Success" if int(test_match.group(2)) == 0 else "Failed",
            "passed": int(test_match.group(1)),
            "failed": int(test_match.group(2)),
            "skipped": int(test_match.group(3))
        }
    # If only Test Summary is found
    elif test_match:
        return {
            "status": "Success" if int(test_match.group(2)) == 0 else "Failed",
            "passed": int(test_match.group(1)),
            "failed": int(test_match.group(2)),
            "skipped": int(test_match.group(3))
        }
    # If only Profile Summary is found
    elif profile_match:
        return {
            "status": "Success" if int(profile_match.group(2)) == 0 else "Failed",
            "passed": int(profile_match.group(1)),
            "failed": int(profile_match.group(2)),
            "skipped": int(profile_match.group(3))
        }
    
    # Try patterns with more flexible spacing and wording
    if not test_match and not profile_match:
        # More flexible patterns for Test Summary
        test_patterns = [
            r"[Tt]est\s+[Ss]ummary\s*:?\s*(\d+)\s+successful,?\s*(\d+)\s+failures?,?\s*(\d+)\s+skipped",
            r"[Tt]est\s+[Ss]ummary\s*:?\s*(\d+)\s+successful,?\s*(\d+)\s+failed,?\s*(\d+)\s+skipped",
            r"[Tt]ests?\s*:?\s*(\d+)\s+successful,?\s*(\d+)\s+failures?,?\s*(\d+)\s+skipped",
            r"[Tt]ests?\s*:?\s*(\d+)\s+passed,?\s*(\d+)\s+failed,?\s*(\d+)\s+skipped"
        ]
        
        for pattern in test_patterns:
            match = re.search(pattern, logs, re.IGNORECASE)
            if match:
                return {
                    "status": "Success" if int(match.group(2)) == 0 else "Failed",
                    "passed": int(match.group(1)),
                    "failed": int(match.group(2)),
                    "skipped": int(match.group(3))
                }
    
    # Try to find independent numbers for successful, failures, and skipped
    if not test_match and not profile_match:
        # Look for separate metrics across the entire log
        successful_patterns = [
            r"(\d+)\s+successful(?!\s+Control)",  # Match "successful" but not "successful Control"
            r"(\d+)\s+passed",
            r"(\d+)\s+successful\s+tests"
        ]
        
        failures_patterns = [
            r"(\d+)\s+failures",
            r"(\d+)\s+failed(?!\s+to)",  # Match "failed" but not "failed to"
            r"(\d+)\s+failing"
        ]
        
        skipped_patterns = [
            r"(\d+)\s+skipped(?!\s+controls)",  # Match "skipped" but not "skipped controls"
            r"(\d+)\s+skipped\s+tests"
        ]
        
        successful = 0
        failures = 0
        skipped = 0
        
        # Find all matches for each pattern and use the largest value
        for pattern in successful_patterns:
            matches = re.findall(pattern, logs, re.IGNORECASE)
            if matches:
                successful = max([int(m) for m in matches] + [successful])
        
        for pattern in failures_patterns:
            matches = re.findall(pattern, logs, re.IGNORECASE)
            if matches:
                failures = max([int(m) for m in matches] + [failures])
        
        for pattern in skipped_patterns:
            matches = re.findall(pattern, logs, re.IGNORECASE)
            if matches:
                skipped = max([int(m) for m in matches] + [skipped])
        
        if successful > 0 or failures > 0:  # Only return if we found at least something
            return {
                "status": "Success" if failures == 0 else "Failed",
                "passed": successful,
                "failed": failures,
                "skipped": skipped
            }
    
    # Look for specific lines containing summaries
    summary_lines = []
    for line in logs.splitlines():
        if "summary" in line.lower() or "successful" in line.lower() or "failures" in line.lower():
            summary_lines.append(line)
    
    # Try to parse each potential summary line
    for line in summary_lines:
        numbers = re.findall(r'\d+', line)
        if len(numbers) >= 3:  # If we have at least three numbers, they might be our metrics
            # Heuristic: If "fail" comes before "skip" in the line, then the order is likely pass, fail, skip
            if "fail" in line.lower() and "skip" in line.lower() and line.lower().index("fail") < line.lower().index("skip"):
                return {
                    "status": "Success" if int(numbers[1]) == 0 else "Failed",
                    "passed": int(numbers[0]),
                    "failed": int(numbers[1]),
                    "skipped": int(numbers[2])
                }
            # Otherwise, use standard ordering
            return {
                "status": "Success" if int(numbers[1]) == 0 else "Failed",
                "passed": int(numbers[0]),
                "failed": int(numbers[1]),
                "skipped": int(numbers[2])
            }
    
    # Log sections of the logs for debugging
    if logs:
        print("Warning: Unable to parse Inspec logs. Here's a sample:")
        print("First 200 chars:")
        print(logs[:200])
        print("\nLast 200 chars:")
        print(logs[-200:])
        
        # Extract lines containing keywords that might help diagnosis
        keywords = ["summary", "successful", "failures", "skipped", "control"]
        relevant_lines = []
        for line in logs.splitlines():
            if any(keyword in line.lower() for keyword in keywords):
                relevant_lines.append(line)
        
        if relevant_lines:
            print("\nRelevant lines containing InSpec-related keywords:")
            for line in relevant_lines[:10]:  # Print first 10 relevant lines
                print(f"  {line}")
    
    return {"status": "Log parsing failed", "passed": 0, "failed": 0, "skipped": 0}

def get_workflow_results(repo, headers):
    """Get results for all specified workflows in a repository."""
    results = {}
    
    for workflow_id, config in WORKFLOWS.items():
        print(f"\nProcessing workflow: {workflow_id} for repository: {repo}")
        
        workflow_run = get_workflow_runs(repo, workflow_id, headers)
        
        if not workflow_run:
            print(f"No runs found for workflow: {workflow_id}")
            results[workflow_id] = {
                "run_id": None,
                "run_date": None,
                "status": "No runs found",
                "job_id": None,
                "results": {"status": "Not Run", "passed": 0, "failed": 0, "skipped": 0}
            }
            continue
        
        run_id = workflow_run["id"]
        print(f"Found latest run ID: {run_id}, created at: {workflow_run['created_at']}")
        
        jobs = get_job_details(repo, run_id, headers)
        
        if not jobs:
            print(f"No jobs found for run ID: {run_id}")
            results[workflow_id] = {
                "run_id": run_id,
                "run_date": workflow_run["created_at"],
                "status": "No jobs found",
                "job_id": None,
                "results": {"status": "Not Run", "passed": 0, "failed": 0, "skipped": 0}
            }
            continue
        
        print(f"Found {len(jobs)} job(s) for this run")
        
        # Debug job names
        job_names = [job.get("name", "unnamed") for job in jobs]
        print(f"Available job names: {', '.join(job_names)}")
        
        target_job = None
        for job in jobs:
            job_name = job.get("name", "")
            if job_name == config["job_name"]:
                target_job = job
                print(f"Found matching job: {job_name}")
                break
        
        if not target_job:
            print(f"Target job '{config['job_name']}' not found")
            # Try a partial match if exact match fails
            for job in jobs:
                job_name = job.get("name", "")
                if config["job_name"].lower() in job_name.lower():
                    target_job = job
                    print(f"Found partial matching job: {job_name}")
                    break
            
            if not target_job:
                results[workflow_id] = {
                    "run_id": run_id,
                    "run_date": workflow_run["created_at"],
                    "status": "Job not found",
                    "job_id": None,
                    "results": {"status": "Not Run", "passed": 0, "failed": 0, "skipped": 0}
                }
                continue
        
        job_id = target_job["id"]
        
        # Check if the job was skipped or not completed
        job_conclusion = target_job.get("conclusion")
        job_status = target_job.get("status")
        print(f"Job ID: {job_id}, Status: {job_status}, Conclusion: {job_conclusion}")
        
        if job_conclusion != "success" and job_conclusion != "failure":
            print(f"Job was not completed successfully or with failure. Conclusion: {job_conclusion}")
            results[workflow_id] = {
                "run_id": run_id,
                "run_date": workflow_run["created_at"],
                "status": "Skipped" if job_conclusion == "skipped" else (job_conclusion or job_status),
                "job_id": job_id,
                "results": {"status": "Skipped", "passed": 0, "failed": 0, "skipped": 0}
            }
            continue
        
        # Get and parse the logs
        print(f"Fetching logs for {workflow_id} in {repo} (Run ID: {run_id}, Job ID: {job_id})")
        logs = get_job_logs(repo, job_id, headers)
        
        if not logs:
            print(f"No logs retrieved for job ID: {job_id}")
            results[workflow_id] = {
                "run_id": run_id,
                "run_date": workflow_run["created_at"],
                "status": job_conclusion or job_status,
                "job_id": job_id,
                "results": {"status": "No logs", "passed": 0, "failed": 0, "skipped": 0}
            }
            continue
        
        print(f"Parsing logs using {config['parser']} function")
        parser_func = globals()[config["parser"]]
        
        # Parse logs and extract test counts
        test_results = parser_func(logs)
        print(f"Parsing results: {test_results}")
        
        results[workflow_id] = {
            "run_id": run_id,
            "run_date": workflow_run["created_at"],
            "status": job_conclusion or job_status,
            "job_id": job_id,
            "results": test_results
        }
    
    return results

def format_results(repo, results):
    """Format results for display."""
    output = f"\n{'=' * 80}\n"
    output += f"Repository: {repo}\n"
    output += f"{'=' * 80}\n\n"
    
    for workflow_id, data in results.items():
        output += f"Workflow: {workflow_id}\n"
        output += f"  Run Date: {data['run_date'] or 'N/A'}\n"
        output += f"  Workflow Status: {data['status']}\n"
        
        workflow_config = WORKFLOWS[workflow_id]
        output += f"  Job Name: {workflow_config['job_name']}\n"
        output += f"  Stage Name: {workflow_config['stage_name']}\n"
        
        test_results = data['results']
        output += f"  Test Results Status: {test_results['status']}\n"
        
        if "passed" in test_results:
            output += f"  Passed: {test_results['passed']}\n"
        if "failed" in test_results:
            output += f"  Failed: {test_results['failed']}\n"
        if "skipped" in test_results:
            output += f"  Skipped: {test_results['skipped']}\n"
        
        output += "\n"
    
    return output

def generate_excel_report(all_results, output_file=None):
    """Generate an Excel report from all results."""
    if output_file is None:
        output_file = f"workflow_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # Create a Pandas ExcelWriter object
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    
    # Convert results to DataFrame format
    data = []
    
    for repo, workflows in all_results.items():
        for workflow_id, workflow_data in workflows.items():
            row = {
                "Repository": repo,
                "Workflow": workflow_id,
                "Run ID": workflow_data.get("run_id"),
                "Job ID": workflow_data.get("job_id"),
                "Run Date": workflow_data.get("run_date"),
                "Workflow Status": workflow_data.get("status"),
                "Job Name": WORKFLOWS[workflow_id]["job_name"],
                "Stage Name": WORKFLOWS[workflow_id]["stage_name"],
                "Test Status": workflow_data["results"]["status"],
                "Passed": workflow_data["results"].get("passed", 0),
                "Failed": workflow_data["results"].get("failed", 0),
                "Skipped": workflow_data["results"].get("skipped", 0) if "skipped" in workflow_data["results"] else 0
            }
            data.append(row)
    
    df = pd.DataFrame(data)
    
    # Write to the Excel file
    df.to_excel(writer, sheet_name="Workflow Results", index=False)
    
    # Get workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets["Workflow Results"]
    
    # Add some formatting
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D8E4BC',
        'border': 1
    })
    
    number_format = workbook.add_format({'num_format': '0'})
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
    
    # Apply formatting to header row
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)
    
    # Apply number formatting to numeric columns
    passed_col = df.columns.get_loc("Passed") + 1
    failed_col = df.columns.get_loc("Failed") + 1
    skipped_col = df.columns.get_loc("Skipped") + 1
    run_id_col = df.columns.get_loc("Run ID") + 1
    job_id_col = df.columns.get_loc("Job ID") + 1
    date_col = df.columns.get_loc("Run Date") + 1
    
    for row_num in range(1, len(df) + 1):
        worksheet.write_number(row_num, passed_col - 1, df.iloc[row_num-1]["Passed"], number_format)
        worksheet.write_number(row_num, failed_col - 1, df.iloc[row_num-1]["Failed"], number_format)
        worksheet.write_number(row_num, skipped_col - 1, df.iloc[row_num-1]["Skipped"], number_format)
        
        # Format IDs as numbers if they exist
        if pd.notna(df.iloc[row_num-1]["Run ID"]):
            worksheet.write_number(row_num, run_id_col - 1, df.iloc[row_num-1]["Run ID"], number_format)
        if pd.notna(df.iloc[row_num-1]["Job ID"]):
            worksheet.write_number(row_num, job_id_col - 1, df.iloc[row_num-1]["Job ID"], number_format)
        
        # Format date if it exists
        if pd.notna(df.iloc[row_num-1]["Run Date"]):
            try:
                date_str = df.iloc[row_num-1]["Run Date"]
                # Try to convert to datetime if it's a string
                if isinstance(date_str, str):
                    date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                    worksheet.write_datetime(row_num, date_col - 1, date_obj, date_format)
            except:
                # If conversion fails, just write as is
                worksheet.write(row_num, date_col - 1, df.iloc[row_num-1]["Run Date"])
    
    # Adjust columns width
    for i, col in enumerate(df.columns):
        max_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
        worksheet.set_column(i, i, max_len)
    
    # Add conditional formatting for test status
    success_format = workbook.add_format({'bg_color': '#C6EFCE'})
    fail_format = workbook.add_format({'bg_color': '#FFC7CE'})
    skip_format = workbook.add_format({'bg_color': '#FFEB9C'})
    
    test_status_col = df.columns.get_loc("Test Status") + 1  # +1 because Excel is 1-indexed
    worksheet.conditional_format(1, test_status_col - 1, len(df) + 1, test_status_col - 1,
                               {'type': 'cell',
                                'criteria': 'equal to',
                                'value': '"Success"',
                                'format': success_format})
    
    worksheet.conditional_format(1, test_status_col - 1, len(df) + 1, test_status_col - 1,
                               {'type': 'cell',
                                'criteria': 'equal to',
                                'value': '"Failed"',
                                'format': fail_format})
    
    worksheet.conditional_format(1, test_status_col - 1, len(df) + 1, test_status_col - 1,
                               {'type': 'cell',
                                'criteria': 'equal to',
                                'value': '"Skipped"',
                                'format': skip_format})
    
    # Add conditional formatting for test counts
    # Highlight non-zero values in Failed column
    worksheet.conditional_format(1, failed_col - 1, len(df) + 1, failed_col - 1,
                               {'type': 'cell',
                                'criteria': 'greater than',
                                'value': 0,
                                'format': fail_format})
    
    # Highlight passed counts
    worksheet.conditional_format(1, passed_col - 1, len(df) + 1, passed_col - 1,
                                {'type': 'cell',
                                 'criteria': 'greater than',
                                 'value': 0,
                                 'format': success_format})
    
    # Write the Excel file
    writer.close()
    
    return output_file

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='GitHub Workflow Log Analyzer')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', type=str, help='Path to file containing repository list (org/repo format)')
    group.add_argument('--repo', type=str, help='Specific repository name')
    
    parser.add_argument('--org', type=str, help='Organization name (required when using --repo)')
    parser.add_argument('--output', type=str, help='Output Excel file name (optional)')
    
    args = parser.parse_args()
    
    # Validate args
    if args.repo and not args.org:
        parser.error("--org is required when using --repo")
    
    return args

def main():
    """Main function to execute the script."""
    args = parse_args()
    token = get_github_token()
    headers = get_headers(token)
    all_results = {}
    
    # Get repositories list
    repositories = []
    if args.file:
        repositories = load_repositories_from_file(args.file)
    elif args.org and args.repo:
        repositories = [f"{args.org}/{args.repo}"]
    
    if not repositories:
        print("No valid repositories specified.")
        sys.exit(1)
    
    # Process each repository
    for repo in repositories:
        print(f"Processing repository: {repo}")
        try:
            results = get_workflow_results(repo, headers)
            all_results[repo] = results
            print(format_results(repo, results))
        except Exception as e:
            print(f"Error processing repository {repo}: {str(e)}")
    
    # Generate Excel report
    excel_file = generate_excel_report(all_results, args.output)
    print(f"Excel report saved to {excel_file}")

if __name__ == "__main__":
    main()