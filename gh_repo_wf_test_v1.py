#!/usr/bin/env python3
"""
GitHub Workflow Log Analyzer

This script extracts test results from GitHub workflow logs for specified workflows.
It retrieves the latest run for each workflow and parses logs to report test success/failure counts.
If the latest workflow run fails, it checks up to 5 previous runs to get valid test results.

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

def get_workflow_runs(repo, workflow_id, headers, per_page=6):
    """Get multiple workflow runs for the specified workflow.
    Returns up to per_page (default 6) runs to allow checking previous runs if latest fails.
    """
    url = f"{GITHUB_API_URL}/repos/{repo}/actions/workflows/{workflow_id}/runs"
    
    # Try first with exact workflow ID
    response = requests.get(url, headers=headers, params={"per_page": per_page})
    
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
                response = requests.get(url, headers=headers, params={"per_page": per_page})
    
    if response.status_code != 200:
        print(f"Error fetching workflow runs: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    if data.get("total_count", 0) == 0:
        print(f"No runs found for workflow {workflow_id}")
        return None
    
    # Return all runs found (up to per_page)
    return data["workflow_runs"]

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
    """
    Parse Chef Inspec logs to extract test counts.
    Specifically designed to handle the format:
    Profile Summary: X successful Control, Y failures, Z controls skipped
    Test Summary: X successful, Y failures, Z skipped
    """
    if not logs:
        return {"status": "Not Run", "passed": 0, "failed": 0, "skipped": 0}
    
    print(f"Parsing InSpec logs (first 100 chars): {logs[:100]}...")
    
    # Look for both Profile Summary and Test Summary patterns
    # We'll prioritize Test Summary as it contains the detailed test counts
    profile_pattern = r"Profile Summary:\s*(\d+)\s+successful\s+Control,\s*(\d+)\s+failures?,\s*(\d+)\s+controls\s+skipped"
    test_pattern = r"Test Summary:\s*(\d+)\s+successful,\s*(\d+)\s+failures?,\s*(\d+)\s+skipped"
    
    profile_match = re.search(profile_pattern, logs, re.IGNORECASE)
    test_match = re.search(test_pattern, logs, re.IGNORECASE)
    
    # Debug information
    if profile_match:
        print(f"Found Profile Summary match: {profile_match.groups()}")
    if test_match:
        print(f"Found Test Summary match: {test_match.groups()}")
    
    # Prefer Test Summary over Profile Summary as it contains detailed test counts
    if test_match:
        return {
            "status": "Success" if int(test_match.group(2)) == 0 else "Failed",
            "passed": int(test_match.group(1)),
            "failed": int(test_match.group(2)),
            "skipped": int(test_match.group(3))
        }
    elif profile_match:
        return {
            "status": "Success" if int(profile_match.group(2)) == 0 else "Failed",
            "passed": int(profile_match.group(1)),
            "failed": int(profile_match.group(2)),
            "skipped": int(profile_match.group(3))
        }
    
    # If the specific patterns above didn't match, search for lines containing both patterns
    inspec_lines = []
    for line in logs.splitlines():
        if "Profile Summary:" in line or "Test Summary:" in line:
            inspec_lines.append(line.strip())
    
    if inspec_lines:
        print(f"Found InSpec summary lines: {inspec_lines}")
        
        # Process each line separately
        profile_data = None
        test_data = None
        
        for line in inspec_lines:
            # Try Profile Summary pattern
            match = re.search(r"Profile Summary:\s*(\d+)\s+successful\s+Control,\s*(\d+)\s+failures?,\s*(\d+)\s+controls\s+skipped", line)
            if match:
                profile_data = {
                    "status": "Success" if int(match.group(2)) == 0 else "Failed",
                    "passed": int(match.group(1)),
                    "failed": int(match.group(2)),
                    "skipped": int(match.group(3))
                }
            
            # Try Test Summary pattern
            match = re.search(r"Test Summary:\s*(\d+)\s+successful,\s*(\d+)\s+failures?,\s*(\d+)\s+skipped", line)
            if match:
                test_data = {
                    "status": "Success" if int(match.group(2)) == 0 else "Failed",
                    "passed": int(match.group(1)),
                    "failed": int(match.group(2)),
                    "skipped": int(match.group(3))
                }
        
        # Prefer test data over profile data
        if test_data:
            print(f"Using test data: {test_data}")
            return test_data
        if profile_data:
            print(f"Using profile data: {profile_data}")
            return profile_data
    
    # If still no match found, extract sections of the log containing "summary" for further analysis
    summary_sections = []
    in_summary_section = False
    summary_lines = []
    
    for line in logs.splitlines():
        # Start of a summary section
        if "Summary" in line:
            in_summary_section = True
            summary_lines = [line]
        # Add lines while in a summary section
        elif in_summary_section:
            if line.strip():  # Not empty line
                summary_lines.append(line)
            else:  # Empty line might end the section
                if summary_lines:
                    summary_sections.append("\n".join(summary_lines))
                in_summary_section = False
                summary_lines = []
    
    # Add the last section if there's one in progress
    if summary_lines:
        summary_sections.append("\n".join(summary_lines))
    
    if summary_sections:
        print(f"Found {len(summary_sections)} summary sections")
        for section in summary_sections:
            # Look for numbers followed by relevant keywords
            successful_match = re.search(r"(\d+)\s+successful", section)
            failures_match = re.search(r"(\d+)\s+failures?", section)
            skipped_match = re.search(r"(\d+)\s+skipped", section)
            
            if successful_match and failures_match and skipped_match:
                return {
                    "status": "Success" if int(failures_match.group(1)) == 0 else "Failed",
                    "passed": int(successful_match.group(1)),
                    "failed": int(failures_match.group(1)),
                    "skipped": int(skipped_match.group(1))
                }
    
    # Last resort: print parts of the log for debugging and return a failure status
    if logs:
        print("Warning: Unable to parse Inspec logs. Here's relevant sections:")
        
        # Extract chunks with keywords for debugging
        keywords = ["profile summary", "test summary", "successful", "failures", "skipped"]
        lines_with_keywords = []
        
        for i, line in enumerate(logs.splitlines()):
            lower_line = line.lower()
            if any(keyword in lower_line for keyword in keywords):
                # Get context (3 lines before and after)
                start = max(0, i - 3)
                end = min(len(logs.splitlines()), i + 4)
                context = logs.splitlines()[start:end]
                lines_with_keywords.append(f"--- Context around line {i+1} ---")
                lines_with_keywords.extend(context)
                lines_with_keywords.append("")
        
        if lines_with_keywords:
            print("\n".join(lines_with_keywords[:20]))  # Print up to 20 lines
    
    return {"status": "Log parsing failed", "passed": 0, "failed": 0, "skipped": 0}

def process_workflow_run(repo, workflow_id, run, headers, config):
    """Process a single workflow run and attempt to extract test results."""
    run_id = run["id"]
    print(f"Processing run ID: {run_id}, created at: {run['created_at']}")
    
    jobs = get_job_details(repo, run_id, headers)
    
    if not jobs:
        print(f"No jobs found for run ID: {run_id}")
        return {
            "run_id": run_id,
            "run_date": run["created_at"],
            "status": "No jobs found",
            "job_id": None,
            "results": {"status": "Not Run", "passed": 0, "failed": 0, "skipped": 0}
        }
    
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
            return {
                "run_id": run_id,
                "run_date": run["created_at"],
                "status": "Job not found",
                "job_id": None,
                "results": {"status": "Not Run", "passed": 0, "failed": 0, "skipped": 0}
            }
    
    job_id = target_job["id"]
    
    # Check if the job was skipped or not completed
    job_conclusion = target_job.get("conclusion")
    job_status = target_job.get("status")
    print(f"Job ID: {job_id}, Status: {job_status}, Conclusion: {job_conclusion}")
    
    if job_conclusion != "success" and job_conclusion != "failure":
        print(f"Job was not completed successfully or with failure. Conclusion: {job_conclusion}")
        return {
            "run_id": run_id,
            "run_date": run["created_at"],
            "status": "Skipped" if job_conclusion == "skipped" else (job_conclusion or job_status),
            "job_id": job_id,
            "results": {"status": "Skipped", "passed": 0, "failed": 0, "skipped": 0}
        }
    
    # Get and parse the logs
    print(f"Fetching logs for workflow in {repo} (Run ID: {run_id}, Job ID: {job_id})")
    logs = get_job_logs(repo, job_id, headers)
    
    if not logs:
        print(f"No logs retrieved for job ID: {job_id}")
        return {
            "run_id": run_id,
            "run_date": run["created_at"],
            "status": job_conclusion or job_status,
            "job_id": job_id,
            "results": {"status": "No logs", "passed": 0, "failed": 0, "skipped": 0}
        }
    
    print(f"Parsing logs using {config['parser']} function")
    parser_func = globals()[config["parser"]]
    
    # Parse logs and extract test counts
    test_results = parser_func(logs)
    print(f"Parsing results: {test_results}")
    
    # Check if the parse was successful (found actual data)
    if test_results["status"] not in ["Not Run", "Log parsing failed"]:
        return {
            "run_id": run_id,
            "run_date": run["created_at"],
            "status": job_conclusion or job_status,
            "job_id": job_id,
            "results": test_results,
            "test_data_found": True
        }
    else:
        return {
            "run_id": run_id,
            "run_date": run["created_at"],
            "status": job_conclusion or job_status,
            "job_id": job_id,
            "results": test_results,
            "test_data_found": False
        }

def get_workflow_results(repo, headers):
    """Get results for all specified workflows in a repository."""
    results = {}
    
    for workflow_id, config in WORKFLOWS.items():
        print(f"\nProcessing workflow: {workflow_id} for repository: {repo}")
        
        # Get multiple workflow runs (up to 6 to allow for checking 5 previous runs)
        workflow_runs = get_workflow_runs(repo, workflow_id, headers, per_page=6)
        
        if not workflow_runs:
            print(f"No runs found for workflow: {workflow_id}")
            results[workflow_id] = {
                "run_id": None,
                "run_date": None,
                "status": "No runs found",
                "job_id": None,
                "results": {"status": "Not Run", "passed": 0, "failed": 0, "skipped": 0}
            }
            continue

        # Process each run until we find one with usable test data or exhaust all options
        test_data_found = False
        runs_checked = 0
        run_results = None
        
        for run in workflow_runs:
            runs_checked += 1
            if runs_checked > 5:  # Only check up to 5 runs
                break
                
            run_results = process_workflow_run(repo, workflow_id, run, headers, config)
            
            # Check if we found usable test data
            if "test_data_found" in run_results and run_results["test_data_found"]:
                test_data_found = True
                # Remove the temporary flag before storing the result
                del run_results["test_data_found"]
                print(f"Found usable test data in run {runs_checked}")
                break
            
            print(f"No usable test data found in run {runs_checked}. Trying next run if available.")
        
        # If we've exhausted all options and still haven't found test data
        if not test_data_found:
            print(f"Could not find usable test data in the last {runs_checked} runs")
            if run_results:
                # Remove the temporary flag if it exists
                if "test_data_found" in run_results:
                    del run_results["test_data_found"]
                    
                # Update the status to reflect this situation
                run_results["results"]["status"] = f"Test_Not_Run_latest_{runs_checked}_workflows"
                results[workflow_id] = run_results
            else:
                results[workflow_id] = {
                    "run_id": None,
                    "run_date": None,
                    "status": f"Test_Not_Run_latest_{runs_checked}_workflows",
                    "job_id": None,
                    "results": {"status": f"Test_Not_Run_latest_{runs_checked}_workflows", "passed": 0, "failed": 0, "skipped": 0}
                }
        else:
            results[workflow_id] = run_results
    
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