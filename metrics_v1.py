#!/usr/bin/env python3
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
import os
import pytz
from typing import Dict, List, Optional, Tuple
import argparse
import sys

class GitHubMetricsReporter:
    """
    Enhanced GitHub repository metrics reporter optimized for CI/CD pipelines.
    Supports command-line arguments and multiple authentication methods.
    """
    
    def __init__(self):
        """Initialize reporter with configuration and logging setup."""
        self.base_url = 'https://api.github.com'
        self.utc = pytz.UTC
        self.api_calls = 0
        self.start_time = datetime.now(self.utc)
        self._setup_logging()
        self.logger.info("GitHub Metrics Reporter initialized")

    def _setup_logging(self):
        """Configure logging with streamlined output for CI/CD environments."""
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now(self.utc).strftime("%Y%m%d_%H%M%S")
        log_file = f'{log_dir}/github_metrics_{timestamp}.log'
        
        # Use simple formatters for CI/CD
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

    def get_token(self, token_file=None):
        """
        Get GitHub token with flexible sourcing options.
        Prioritizes token file, then environment variables.
        """
        token = None
        
        # Try to read from token file first
        if token_file and os.path.exists(token_file):
            try:
                with open(token_file, 'r') as f:
                    token = f.read().strip()
                self.logger.info("Using GitHub token from file")
                return token
            except Exception as e:
                self.logger.warning(f"Error reading token file: {str(e)}")
        
        # Check Harness GitHub connector token environment variable
        token = os.getenv('GITHUB_TOKEN')
        if token:
            self.logger.info("Using GitHub token from environment variable")
            return token
        
        return None

    def validate_token(self, token=None, token_file=None):
        """Validate GitHub token and prepare API headers."""
        try:
            self.logger.info("Validating GitHub authentication...")
            
            # Get token if not directly provided
            if not token:
                token = self.get_token(token_file)
                
            if not token:
                self.logger.error("No GitHub token found - authentication will fail")
                return None
                
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Verify token works
            response = requests.get(
                f'{self.base_url}/user',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("GitHub authentication successful")
                
                # Check rate limits
                rate_response = requests.get(
                    f'{self.base_url}/rate_limit',
                    headers=headers
                )
                
                if rate_response.status_code == 200:
                    limits = rate_response.json()['rate']
                    self.logger.info(f"API Rate Limits: {limits['remaining']}/{limits['limit']} remaining")
                
                return headers
            
            self.logger.error(f"Authentication failed with status {response.status_code}")
            return None
            
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return None

    def fetch_repositories(self, headers, org_name):
        """
        Fetch all repositories for an organization.
        Used when no repository list file is provided.
        """
        try:
            self.logger.info(f"Fetching repositories for {org_name}")
            repositories = []
            page = 1
            
            while True:
                response = requests.get(
                    f'{self.base_url}/orgs/{org_name}/repos',
                    headers=headers,
                    params={
                        'per_page': 100,
                        'page': page,
                        'type': 'all'
                    }
                )
                
                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch repositories: {response.status_code}")
                    break
                    
                repos = response.json()
                if not repos:
                    break
                    
                for repo in repos:
                    repositories.append(repo['name'])
                    
                page += 1
                
            self.logger.info(f"Found {len(repositories)} repositories")
            return repositories
            
        except Exception as e:
            self.logger.error(f"Error fetching repositories: {str(e)}")
            return []

    def fetch_pr_data(self, headers, repo, start_date, end_date):
        """Fetch pull request data including commits, reviews, and approval info."""
        try:
            self.logger.debug(f"Fetching PR data for {repo}")
            
            metrics = {
                'pull_requests': [],
                'stats': {
                    'total_prs': 0,
                    'merged_prs': 0
                }
            }
            
            # Fetch PRs with pagination
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
                    self.logger.error(f"Failed to fetch PRs: {response.status_code}")
                    break
                
                prs = response.json()
                if not prs:
                    break
                
                # Process each PR
                for pr in prs:
                    try:
                        created_at = datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                        created_at = self.utc.localize(created_at)
                        
                        if start_date <= created_at <= end_date:
                            # Fetch PR reviews
                            reviews_response = requests.get(
                                f"{self.base_url}/repos/{repo}/pulls/{pr['number']}/reviews",
                                headers=headers
                            )
                            reviews = reviews_response.json() if reviews_response.status_code == 200 else []
                            
                            # Find approver
                            approver = ''
                            for review in reviews:
                                if review.get('state', '').upper() == 'APPROVED':
                                    approver = review.get('user', {}).get('login', '')
                                    break
                            
                            # Fetch commits
                            commits_response = requests.get(
                                pr['commits_url'],
                                headers=headers
                            )
                            commits = commits_response.json() if commits_response.status_code == 200 else []
                            
                            # Process commit data
                            commit_data = []
                            for commit in commits:
                                commit_info = commit.get('commit', {})
                                author_info = commit_info.get('author', {})
                                
                                commit_data.append({
                                    'sha': commit.get('sha', ''),
                                    'message': commit_info.get('message', ''),
                                    'author': author_info.get('name', ''),
                                    'date': author_info.get('date', '')
                                })
                            
                            # Build PR record
                            pr_data = {
                                'number': pr['number'],
                                'title': pr['title'],
                                'author': pr['user']['login'],
                                'state': pr['state'],
                                'created_at': created_at,
                                'merged_at': None,
                                'approver': approver,
                                'labels': [label['name'] for label in pr.get('labels', [])],
                                'commits': commit_data,
                                'reviews': reviews
                            }
                            
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

    def generate_activity_report(self, all_metrics, output_dir):
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

    def generate_contributor_report(self, all_metrics, output_dir):
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
                        if review.get('state', '').upper() == 'APPROVED':
                            reviewer = review.get('user', {}).get('login', '')
                            if reviewer and (repo, reviewer) not in contributors:
                                contributors[(repo, reviewer)] = {
                                    'prs_created': 0,
                                    'prs_merged': 0,
                                    'total_commits': 0,
                                    'approvals_given': 0
                                }
                            if reviewer:
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

    def generate_commit_report(self, all_metrics, output_dir):
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
                            'Commit SHA': commit.get('sha', ''),
                            'Commit Message': commit.get('message', '').split('\n')[0],
                            'Author': commit.get('author', ''),
                            'Commit Date': datetime.strptime(commit.get('date', ''),
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


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='GitHub Repository Metrics Generator')
    parser.add_argument('--org', required=True, help='GitHub organization/owner name')
    parser.add_argument('--start-date', required=True, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', required=True, help='End date in YYYY-MM-DD format')
    parser.add_argument('--repos-file', help='Path to file containing repository names (optional)')
    parser.add_argument('--token-file', help='Path to file containing GitHub token (optional)')
    parser.add_argument('--output-dir', help='Custom output directory path')
    return parser.parse_args()


def main():
    """Main execution flow optimized for CI/CD."""
    try:
        args = parse_arguments()
        
        print("\nGitHub Repository Metrics Reporter")
        print("=================================")
        
        reporter = GitHubMetricsReporter()
        
        # Get and validate headers
        headers = reporter.validate_token(token_file=args.token_file)
        if not headers:
            reporter.logger.error("Failed to authenticate with GitHub. Check token or permissions.")
            sys.exit(1)
        
        # Parse dates
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
            
            start_date = reporter.utc.localize(start_date)
            end_date = reporter.utc.localize(end_date)
            
            if start_date >= end_date:
                raise ValueError("Start date must be before end date")
                
            reporter.logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
            
        except ValueError as e:
            reporter.logger.error(f"Invalid date format: {str(e)}")
            sys.exit(1)
        
        # Get repositories
        repositories = []
        if args.repos_file and os.path.exists(args.repos_file):
            # Read from file if provided
            with open(args.repos_file, 'r', encoding='utf-8') as f:
                repositories = [line.strip() for line in f if line.strip()]
            reporter.logger.info(f"Loaded {len(repositories)} repositories from {args.repos_file}")
        else:
            # Fetch repositories dynamically
            repositories = reporter.fetch_repositories(headers, args.org)
        
        if not repositories:
            reporter.logger.error("No repositories found. Check organization name and permissions.")
            sys.exit(1)
            
        # Create output directory
        output_dir = args.output_dir if args.output_dir else f'reports_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.makedirs(output_dir, exist_ok=True)
        
        # Collect metrics
        all_metrics = {}
        for i, repo in enumerate(repositories, 1):
            try:
                full_repo = f"{args.org}/{repo}"
                reporter.logger.info(f"Processing [{i}/{len(repositories)}]: {repo}")
                
                metrics = reporter.fetch_pr_data(headers, full_repo, start_date, end_date)
                if metrics:
                    all_metrics[full_repo] = metrics
                    pr_count = metrics['stats']['total_prs']
                    reporter.logger.info(f"Found {pr_count} PRs for {repo}")
                
            except Exception as e:
                reporter.logger.error(f"Error processing {repo}: {str(e)}")
                continue
                
        # Generate reports
        if all_metrics:
            reporter.generate_activity_report(all_metrics, output_dir)
            reporter.generate_contributor_report(all_metrics, output_dir)
            reporter.generate_commit_report(all_metrics, output_dir)
            reporter.logger.info(f"✓ All reports saved to: {output_dir}")
            
            # Print summary for CI/CD logs
            total_repos = len(all_metrics)
            total_prs = sum(metrics['stats']['total_prs'] for metrics in all_metrics.values())
            print(f"\nSummary: Processed {total_repos} repositories with {total_prs} PRs")
            print(f"Reports are available in: {output_dir}")
        else:
            reporter.logger.error("No metrics data collected. Reports could not be generated.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
