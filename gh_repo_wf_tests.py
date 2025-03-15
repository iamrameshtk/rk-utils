import requests
from github import Github
import json
import os
import pandas as pd
import zipfile
import io
import re

# Load GitHub token from environment variable
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable is not set.")

# Load repository list from repos.txt
with open("repos.txt", "r") as file:
    REPOS = [line.strip() for line in file.readlines() if line.strip()]

# Define the workflows and their corresponding jobs and stages
WORKFLOWS = {
    "core-checkov-action.yml": {"job": "checkov-action", "stage": "Run Checkov action"},
    "core-terraform-module-integrations-tests.yml": {"job": "terraform-init-plan", "stage": "Run GCP Inspec"},
    "terraform-module-unit-tests.yml": {"job": "terraform-init-plan", "stage": "Terraform test"},
}

github_client = Github(GITHUB_TOKEN)

def get_latest_workflow_run(owner, repo, workflow_name):
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_name}/runs?per_page=1&status=completed"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        runs = response.json().get("workflow_runs", [])
        if runs:
            return runs[0]  # Get the most recent completed run
        else:
            print(f"No workflow runs found for {workflow_name} in {repo}.")
    else:
        print(f"Failed to fetch workflow runs for {workflow_name} in {repo}: {response.status_code}")
    return None

def get_workflow_logs(owner, repo, run_id):
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            logs = ""
            for filename in z.namelist():
                with z.open(filename) as log_file:
                    logs += log_file.read().decode("utf-8") + "\n"
            return logs
    else:
        print(f"Failed to fetch logs for run {run_id} in {repo}: {response.status_code}")
    return None

def parse_test_results(log_content, job_name, stage_name):
    success_count = 0
    failure_count = 0
    capturing = False
    
    for line in log_content.split("\n"):
        if job_name in line and stage_name in line:
            capturing = True  # Start capturing logs for the specific job-stage
        
        if capturing:
            checkov_match = re.search(r"Passed checks: (\d+), Failed checks: (\d+)", line)
            terraform_match = re.search(r"Success! (\d+) passed, (\d+) failed", line)
            inspec_match = re.search(r"Test Summary: (\d+) successful, (\d+) failures", line)
            
            if checkov_match:
                success_count = int(checkov_match.group(1))
                failure_count = int(checkov_match.group(2))
                break
            
            if terraform_match:
                success_count = int(terraform_match.group(1))
                failure_count = int(terraform_match.group(2))
                break
            
            if inspec_match:
                success_count = int(inspec_match.group(1))
                failure_count = int(inspec_match.group(2))
                break
    
    return success_count, failure_count

def main():
    results = []
    
    for repo_fullname in REPOS:
        owner, repo = repo_fullname.split("/")
        
        for workflow, details in WORKFLOWS.items():
            latest_run = get_latest_workflow_run(owner, repo, workflow)
            if latest_run:
                log_content = get_workflow_logs(owner, repo, latest_run['id'])
                if log_content:
                    success, failure = parse_test_results(log_content, details['job'], details['stage'])
                    results.append({
                        "Repository": repo,
                        "Workflow": workflow,
                        "Run ID": latest_run['id'],
                        "Job Name": details['job'],
                        "Stage Name": details['stage'],
                        "Status": latest_run['status'],
                        "Conclusion": latest_run['conclusion'],
                        "Total Success": success,
                        "Total Failed": failure
                    })
                else:
                    results.append({
                        "Repository": repo,
                        "Workflow": workflow,
                        "Run ID": latest_run['id'],
                        "Job Name": details['job'],
                        "Stage Name": details['stage'],
                        "Status": latest_run['status'],
                        "Conclusion": latest_run['conclusion'],
                        "Total Success": "No Logs",
                        "Total Failed": "No Logs"
                    })
    
    # Save results to an Excel file
    df = pd.DataFrame(results)
    df.to_excel("workflow_results.xlsx", index=False)
    print("Results saved to workflow_results.xlsx")

if __name__ == "__main__":
    main()
