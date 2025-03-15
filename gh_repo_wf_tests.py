import requests
from github import Github
import json
import os
import pandas as pd
import zipfile
import io

# Load GitHub token from environment variable
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable is not set.")

# Load repository list from repos.txt
with open("repos.txt", "r") as file:
    REPOS = [line.strip() for line in file.readlines() if line.strip()]

# Define the workflow names and their respective scan/test stages
WORKFLOWS = {
    "core-checkov-action.yml": "Run Checkov action",  # Checkov scan stage
    "core-terraform-module-integrations-tests.yml": "Run GCP Inspec",  # Chef Inspec stage
    "terraform-module-unit-tests.yml": "Terraform Test",  # Terraform test stage
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

def parse_test_results(log_content, scan_test_name):
    success_count = 0
    failure_count = 0
    capturing = False
    stage_found = False
    
    for line in log_content.split("\n"):
        if scan_test_name in line:
            capturing = True  # Start capturing logs for the specific scan/test stage
            stage_found = True
        
        if capturing:
            if "✔" in line or "PASSED" in line:
                success_count += 1
            elif "✘" in line or "FAILED" in line:
                failure_count += 1
    
    if not stage_found:
        return "Skipped", "Skipped"  # Indicate that the stage was not found in logs
    return success_count, failure_count

def main():
    results = []
    
    for repo_fullname in REPOS:
        owner, repo = repo_fullname.split("/")
        
        for workflow, scan_test_name in WORKFLOWS.items():
            latest_run = get_latest_workflow_run(owner, repo, workflow)
            if latest_run:
                log_content = get_workflow_logs(owner, repo, latest_run['id'])
                if log_content:
                    success, failure = parse_test_results(log_content, scan_test_name)
                    results.append({
                        "Repository": repo,
                        "Workflow": workflow,
                        "Run ID": latest_run['id'],
                        "Scan/Test Name": scan_test_name,
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
                        "Scan/Test Name": scan_test_name,
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
