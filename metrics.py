import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
import os
import pytz
from typing import Dict, List, Optional, Tuple
from tqdm import tqdm
import psutil
import time

class GitHubMetricsReporter:
    """
    A class that generates consolidated GitHub repository metrics reports.
    Creates three main reports: PR Activity, Contributor Metrics, and Commit Details.
    All repository data is consolidated into these reports for easier analysis.
    """
    
    def __init__(self):
        """Initialize reporter with basic configuration and logging setup."""
        self.base_url = 'https://api.github.com'
        self.utc = pytz.UTC
        self.api_calls = 0
        self.start_time = time.time()
        self._setup_logging()
        self.logger.info("GitHub Metrics Reporter initialized")

    def _setup_logging(self):
        """Configure logging with separate file and console handlers."""
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now(self.utc).strftime("%Y%m%d_%H%M%S")
        log_file = f'{log_dir}/github_metrics_{timestamp}.log'
        
        file_formatter = logging.Formatter(
            '%(asctime)s UTC - %(levelname)s - [%(name)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter('%(message)s')
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8', errors='replace')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        
        self.logger = logging.getLogger('GitHubMetrics')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        process = psutil.Process(os.getpid())
        self.logger.debug(f"Script initialized with PID: {process.pid}")
        self.logger.debug(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")

    def validate_token(self, token: str) -> Optional[Dict[str, str]]:
        """Validate GitHub token and prepare API headers."""
        try:
            self.logger.info("Validating GitHub token...")
            
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(
                f'{self.base_url}/user',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Token validated successfully")
                
                rate_response = requests.get(
                    f'{self.base_url}/rate_limit',
                    headers=headers
                )
                
                if rate_response.status_code == 200:
                    limits = rate_response.json()['rate']
                    self.logger.info(f"API Rate Limits: {limits['remaining']}/{limits['limit']} remaining")
                
                return headers
            
            self.logger.error(f"Token validation failed: Status {response.status_code}")
            return None
            
        except Exception as e:
            self.logger.error(f"Token validation error: {str(e)}")
            return None

    def fetch_pr_data(self, headers: Dict, repo: str, start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """Fetch pull request data including commits and reviews."""
        try:
            self.logger.debug(f"Fetching PR data for {repo}")
            
            metrics = {
                'pull_requests': [],
                'stats': {
                    'total_prs': 0,
                    'merged_prs': 0
                }
            }
            
            page = 1
            while True:
                response = requests.get(
                    f'{self.base_url}/repos/{repo}/pulls',
                    headers=headers,
                    params={
                        'state': 'all',
                        'sort': 'created',
                        'direction': 'desc',
                        'per_page': 100,
                        'page': page
                    }
                )
                
                if response.status_code != 200:
                    break
                
                prs = response.json()
                if not prs:
                    break
                
                for pr in prs:
                    try:
                        created_at = datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                        created_at = self.utc.localize(created_at)
                        
                        if start_date <= created_at <= end_date:
                            # Get commits
                            commits_response = requests.get(
                                pr['commits_url'],
                                headers=headers
                            )
                            commits = commits_response.json() if commits_response.status_code == 200 else []
                            
                            # Get reviews
                            reviews_response = requests.get(
                                f"{self.base_url}/repos/{repo}/pulls/{pr['number']}/reviews",
                                headers=headers
                            )
                            reviews = reviews_response.json() if reviews_response.status_code == 200 else []
                            
                            # Find approver
                            approver = next(
                                (review['user']['login'] for review in reviews 
                                 if review['state'].upper() == 'APPROVED'),
                                ''
                            )
                            
                            pr_data = {
                                'number': pr['number'],
                                'title': pr['title'],
                                'author': pr['user']['login'],
                                'state': pr['state'],
                                'created_at': created_at,
                                'merged_at': None,
                                'approver': approver,
                                'labels': [label['name'] for label in pr.get('labels', [])],
                                'commits': [],
                                'reviews': reviews
                            }
                            
                            # Process commits
                            for commit in commits:
                                commit_info = commit['commit']
                                pr_data['commits'].append({
                                    'sha': commit['sha'],
                                    'message': commit_info['message'],
                                    'author': commit_info['author']['name'],
                                    'date': commit_info['author']['date']
                                })
                            
                            # Process merge info
                            if pr['merged_at']:
                                merged_at = datetime.strptime(pr['merged_at'], '%Y-%m-%dT%H:%M:%SZ')
                                pr_data['merged_at'] = self.utc.localize(merged_at)
                                metrics['stats']['merged_prs'] += 1
                            
                            metrics['pull_requests'].append(pr_data)
                            metrics['stats']['total_prs'] += 1
                            
                    except Exception as e:
                        self.logger.error(f"Error processing PR #{pr.get('number', 'unknown')}: {str(e)}")
                
                page += 1
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error fetching PR data for {repo}: {str(e)}")
            return None

    def generate_activity_report(self, all_metrics: Dict[str, Dict], output_dir: str):
        """Generate consolidated PR activity report."""
        try:
            self.logger.info("Generating PR activity report")
            
            activity_data = []
            for repo, metrics in all_metrics.items():
                for pr in metrics['pull_requests']:
                    record = {
                        'Repository': repo,
                        'PR Number': pr['number'],
                        'Title': pr['title'],
                        'Author': pr['author'],
                        'Status': pr['state'].capitalize(),
                        'Created Date': pr['created_at'].strftime('%Y-%m-%d'),
                        'Merged Date': pr['merged_at'].strftime('%Y-%m-%d') if pr['merged_at'] else '',
                        'Approver': pr['approver'],
                        'Labels': ', '.join(pr['labels']),
                        'Commit Count': len(pr['commits'])
                    }
                    activity_data.append(record)
            
            df = pd.DataFrame(activity_data)
            output_file = f"{output_dir}/pr_activity_report.xlsx"
            
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='PR Activity', index=False)
                self._format_excel_sheet(writer.sheets['PR Activity'], df, writer.book)
            
            self.logger.info(f"Saved PR activity report: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error generating activity report: {str(e)}")

    def generate_contributor_report(self, all_metrics: Dict[str, Dict], output_dir: str):
        """Generate consolidated contributor metrics report."""
        try:
            self.logger.info("Generating contributor report")
            
            contributor_data = []
            for repo, metrics in all_metrics.items():
                contributors = {}
                
                for pr in metrics['pull_requests']:
                    author = pr['author']
                    
                    if (repo, author) not in contributors:
                        contributors[(repo, author)] = {
                            'prs_created': 0,
                            'prs_merged': 0,
                            'total_commits': 0,
                            'approvals_given': 0
                        }
                    
                    stats = contributors[(repo, author)]
                    stats['prs_created'] += 1
                    stats['total_commits'] += len(pr['commits'])
                    
                    if pr['merged_at']:
                        stats['prs_merged'] += 1
                    
                    # Track approvals
                    for review in pr['reviews']:
                        if review['state'].upper() == 'APPROVED':
                            reviewer = review['user']['login']
                            if (repo, reviewer) not in contributors:
                                contributors[(repo, reviewer)] = {
                                    'prs_created': 0,
                                    'prs_merged': 0,
                                    'total_commits': 0,
                                    'approvals_given': 0
                                }
                            contributors[(repo, reviewer)]['approvals_given'] += 1
                
                for (repo_name, author), stats in contributors.items():
                    contributor_data.append({
                        'Repository': repo_name,
                        'Contributor': author,
                        'PRs Created': stats['prs_created'],
                        'PRs Merged': stats['prs_merged'],
                        'Total Commits': stats['total_commits'],
                        'Approvals Given': stats['approvals_given']
                    })
            
            df = pd.DataFrame(contributor_data)
            output_file = f"{output_dir}/contributor_report.xlsx"
            
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Contributor Metrics', index=False)
                self._format_excel_sheet(writer.sheets['Contributor Metrics'], df, writer.book)
            
            self.logger.info(f"Saved contributor report: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error generating contributor report: {str(e)}")

    def generate_commit_report(self, all_metrics: Dict[str, Dict], output_dir: str):
        """Generate consolidated commit details report."""
        try:
            self.logger.info("Generating commit report")
            
            commit_data = []
            for repo, metrics in all_metrics.items():
                for pr in metrics['pull_requests']:
                    for commit in pr['commits']:
                        record = {
                            'Repository': repo,
                            'PR Number': pr['number'],
                            'PR Title': pr['title'],
                            'PR Author': pr['author'],
                            'Commit SHA': commit['sha'],
                            'Commit Message': commit['message'].split('\n')[0],
                            'Author': commit['author'],
                            'Commit Date': datetime.strptime(commit['date'], 
                                        '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d'),
                            'PR Status': pr['state'].capitalize()
                        }
                        commit_data.append(record)
            
            df = pd.DataFrame(commit_data)
            output_file = f"{output_dir}/commit_report.xlsx"
            
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Commit Details', index=False)
                self._format_excel_sheet(writer.sheets['Commit Details'], df, writer.book)
            
            self.logger.info(f"Saved commit report: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error generating commit report: {str(e)}")

    def _format_excel_sheet(self, worksheet, dataframe, workbook):
        """Apply consistent formatting to Excel worksheets."""
        try:
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D3D3D3',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True
            })
            
            date_format = workbook.add_format({
                'num_format': 'yyyy-mm-dd',
                'align': 'center'
            })
            
            number_format = workbook.add_format({
                'num_format': '#,##0',
                'align': 'right'
            })
            
            text_format = workbook.add_format({
                'text_wrap': True,
                'valign': 'top'
            })
            
            # Format columns
            for idx, col in enumerate(dataframe.columns):
                max_len = max(
                    dataframe[col].astype(str).apply(len).max(),
                    len(str(col))
                ) + 2
                
                if 'Date' in col:
                    worksheet.set_column(idx, idx, max(12, max_len), date_format)
                elif any(word in col for word in ['Count', 'Number', 'Total']):
                    worksheet.set_column(idx, idx, max(8, max_len), number_format)
                elif col in ['Title', 'Commit Message', 'Labels']:
                    worksheet.set_column(idx, idx, min(50, max_len), text_format)
                else:
                    worksheet.set_column(idx, idx, min(30, max_len), text_format)
                
                worksheet.write(0, idx, col, header_format)
            
            # Add alternating row colors
            for row in range(1, len(dataframe) + 1):
                if row % 2 == 0:
                    worksheet.set_row(row, None, workbook.add_format({'bg_color': '#F8F8F8'}))
            
            # Freeze header row
            worksheet.freeze_panes(1, 0)
            
        except Exception as e:
            self.logger.error(f"Error formatting Excel sheet: {str(e)}")

    def generate_reports(self):
        """Generate consolidated reports for all repositories."""
        try:
            self.logger.info("Starting GitHub metrics collection process")
            
            # Get GitHub token from environment
            token = os.getenv('GITHUB_TOKEN')
            if not token:
                raise ValueError("GitHub token not found in environment variables")
            
            # Get organization name
            org_name = input("Organization/owner name: ").strip()
            if not org_name:
                raise ValueError("Organization name cannot be empty")
            
            # Get date range
            start_date_str = input("Start date (YYYY-MM-DD): ").strip()
            end_date_str = input("End date (YYYY-MM-DD): ").strip()
            
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                
                start_date = self.utc.localize(start_date)
                end_date = self.utc.localize(end_date)
                
                if start_date >= end_date:
                    raise ValueError("Start date must be before end date")
            except ValueError as e:
                raise ValueError(f"Invalid date format: {str(e)}")
            
            # Read repositories list
            try:
                with open('repos.txt', 'r', encoding='utf-8') as f:
                    repositories = [line.strip() for line in f if line.strip()]
                if not repositories:
                    raise ValueError("repos.txt is empty")
                self.logger.info(f"Processing {len(repositories)} repositories...")
            except FileNotFoundError:
                raise FileNotFoundError("repos.txt not found in current directory")
            
            # Validate token and get headers
            headers = self.validate_token(token)
            if not headers:
                self.logger.error("Token validation failed. Aborting report generation.")
                return
            
            # Create output directory
            timestamp = datetime.now(self.utc).strftime("%Y%m%d_%H%M%S")
            output_dir = f'reports_{timestamp}'
            os.makedirs(output_dir, exist_ok=True)
            
            # Collect metrics for all repositories
            all_metrics = {}
            total_repos = len(repositories)
            
            for index, repo in enumerate(repositories, 1):
                try:
                    full_repo = f"{org_name}/{repo}"
                    self.logger.info(f"Processing {index}/{total_repos}: {repo}")
                    
                    metrics = self.fetch_pr_data(headers, full_repo, start_date, end_date)
                    if metrics:
                        all_metrics[full_repo] = metrics
                        self.logger.info(f"Found {metrics['stats']['total_prs']} PRs for {repo}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing repository {repo}: {str(e)}")
                    continue
            
            # Generate all reports
            if all_metrics:
                self.generate_activity_report(all_metrics, output_dir)
                self.generate_contributor_report(all_metrics, output_dir)
                self.generate_commit_report(all_metrics, output_dir)
                self.logger.info(f"✓ All reports generated successfully in: {output_dir}")
            else:
                self.logger.error("No data collected. Reports cannot be generated.")
            
        except Exception as e:
            self.logger.error(f"Error in report generation process: {str(e)}")
            raise

def main():
    """Main execution entry point."""
    try:
        print("\nGitHub Repository Metrics Reporter")
        print("=================================")
        print("This script will generate three reports:")
        print("1. PR Activity Report - Shows all pull request activity")
        print("2. Contributor Report - Shows contributor metrics")
        print("3. Commit Report - Shows detailed commit information")
        print("\nPlease ensure:")
        print("- GITHUB_TOKEN environment variable is set")
        print("- repos.txt exists with repository names")
        print("- Repository names are in format: name-of-repo")
        
        reporter = GitHubMetricsReporter()
        reporter.generate_reports()
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        logging.getLogger('GitHubMetrics').warning("Script execution interrupted by user")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        logging.getLogger('GitHubMetrics').error(f"Script execution failed: {str(e)}", exc_info=True)
        print("Please check the log file for detailed error information")

if __name__ == "__main__":
    main()
