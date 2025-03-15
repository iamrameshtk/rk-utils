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
    response = requests.get(url, headers=headers, params={"per_page": 1})
    
    if response.status_code != 200:
        print(f"Error fetching workflow runs: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    if data.get("total_count", 0) == 0:
        return None
    
    return data["workflow_runs"][0]

def get_job_details(repo, run_id, headers):
    """Get job details for a specific workflow run."""
    url = f"{GITHUB_API_URL}/repos/{repo}/actions/runs/{run_id}/jobs"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching job details: {response.status_code}")
        print(response.text)
        return []
    
    return response.json()["jobs"]

def get_job_logs(repo, job_id, headers):
    """Get logs for a specific job."""
    url = f"{GITHUB_API_URL}/repos/{repo}/actions/jobs/{job_id}/logs"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching job logs: {response.status_code}")
        return None
    
    return response.text

def parse_checkov_logs(logs):
    """Parse Checkov logs to extract test counts."""
    if not logs:
        return {"status": "Not Run", "passed": 0, "failed": 0, "skipped": 0}
    
    pattern = r"terraform scan results:[\s\S]*?Passed checks: (\d+), Failed checks: (\d+), Skipped checks: (\d+)"
    match = re.search(pattern, logs)
    
    if match:
        return {
            "status": "Success" if int(match.group(2)) == 0 else "Failed",
            "passed": int(match.group(1)),
            "failed": int(match.group(2)),
            "skipped": int(match.group(3))
        }
    
    return {"status": "Log parsing failed", "passed": 0, "failed": 0, "skipped": 0}

def parse_terraform_logs(logs):
    """Parse Terraform test logs to extract test counts."""
    if not logs:
        return {"status": "Not Run", "passed": 0, "failed": 0}
    
    pattern = r"Success! (\d+) passed, (\d+) failed"
    match = re.search(pattern, logs)
    
    if match:
        return {
            "status": "Success" if int(match.group(2)) == 0 else "Failed",
            "passed": int(match.group(1)),
            "failed": int(match.group(2))
        }
    
    return {"status": "Log parsing failed", "passed": 0, "failed": 0}

def parse_inspec_logs(logs):
    """Parse Chef Inspec logs to extract test counts."""
    if not logs:
        return {"status": "Not Run", "passed": 0, "failed": 0, "skipped": 0}
    
    pattern = r"Test Summary: (\d+) successful, (\d+) failures, (\d+) skipped"
    match = re.search(pattern, logs)
    
    if match:
        return {
            "status": "Success" if int(match.group(2)) == 0 else "Failed",
            "passed": int(match.group(1)),
            "failed": int(match.group(2)),
            "skipped": int(match.group(3))
        }
    
    return {"status": "Log parsing failed", "passed": 0, "failed": 0, "skipped": 0}

def get_workflow_results(repo, headers):
    """Get results for all specified workflows in a repository."""
    results = {}
    
    for workflow_id, config in WORKFLOWS.items():
        workflow_run = get_workflow_runs(repo, workflow_id, headers)
        
        if not workflow_run:
            results[workflow_id] = {
                "run_date": None,
                "status": "No runs found",
                "results": {"status": "Not Run", "passed": 0, "failed": 0, "skipped": 0}
            }
            continue
        
        run_id = workflow_run["id"]
        jobs = get_job_details(repo, run_id, headers)
        
        target_job = None
        for job in jobs:
            if job["name"] == config["job_name"]:
                target_job = job
                break
        
        if not target_job:
            results[workflow_id] = {
                "run_date": workflow_run["created_at"],
                "status": "Job not found",
                "results": {"status": "Not Run", "passed": 0, "failed": 0, "skipped": 0}
            }
            continue
        
        # Check if the job was skipped or not completed
        if target_job["conclusion"] != "success" and target_job["conclusion"] != "failure":
            results[workflow_id] = {
                "run_date": workflow_run["created_at"],
                "status": "Skipped" if target_job["conclusion"] == "skipped" else target_job["conclusion"],
                "results": {"status": "Skipped", "passed": 0, "failed": 0, "skipped": 0}
            }
            continue
        
        logs = get_job_logs(repo, target_job["id"], headers)
        parser_func = globals()[config["parser"]]
        
        results[workflow_id] = {
            "run_date": workflow_run["created_at"],
            "status": target_job["conclusion"],
            "results": parser_func(logs)
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
                "Run Date": workflow_data.get("run_date"),
                "Workflow Status": workflow_data.get("status"),
                "Job Name": WORKFLOWS[workflow_id]["job_name"],
                "Stage Name": WORKFLOWS[workflow_id]["stage_name"],
                "Test Status": workflow_data["results"]["status"],
                "Passed": workflow_data["results"].get("passed", 0),
                "Failed": workflow_data["results"].get("failed", 0),
                "Skipped": workflow_data["results"].get("skipped", 0)
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
    
    # Apply formatting to header row
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)
    
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