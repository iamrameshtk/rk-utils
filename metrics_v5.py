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
    Comprehensive GitHub repository metrics reporter with advanced PR analytics.
    Includes file changes, lines added/removed, and enhanced health metrics.
    """
    
    def __init__(self):
        """Initialize reporter with configuration and logging setup."""
        self.base_url = 'https://api.github.com'
        self.utc = pytz.UTC
        self.api_calls = 0
        self.start_time = datetime.now(self.utc)
        # PR threshold for health metrics (in days)
        self.pr_threshold_days = 2
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

    def get_pr_details(self, headers, repo, pr_number):
        """
        Fetch detailed information about a specific PR.
        Includes the target branch and other metadata.
        """
        try:
            response = requests.get(
                f'{self.base_url}/repos/{repo}/pulls/{pr_number}',
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to fetch PR details for {repo}#{pr_number}: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error fetching PR details for {repo}#{pr_number}: {str(e)}")
            return {}
    
    def get_user_details(self, headers, username):
        """
        Fetch user information including organization membership.
        """
        try:
            response = requests.get(
                f'{self.base_url}/users/{username}',
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to fetch user details for {username}: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error fetching user details for {username}: {str(e)}")
            return {}
    
    def get_org_membership(self, headers, org, username):
        """
        Check if a user is a member of an organization and get their team memberships.
        """
        try:
            membership_response = requests.get(
                f'{self.base_url}/orgs/{org}/memberships/{username}',
                headers=headers
            )
            
            if membership_response.status_code == 200:
                # Get teams
                teams_response = requests.get(
                    f'{self.base_url}/orgs/{org}/teams',
                    headers=headers
                )
                
                if teams_response.status_code == 200:
                    teams = teams_response.json()
                    user_teams = []
                    
                    for team in teams:
                        team_membership_response = requests.get(
                            f'{self.base_url}/teams/{team["id"]}/memberships/{username}',
                            headers=headers
                        )
                        
                        if team_membership_response.status_code == 200:
                            user_teams.append(team["name"])
                    
                    return {
                        'member': True,
                        'role': membership_response.json().get('role', ''),
                        'teams': user_teams
                    }
            
            return {'member': False, 'teams': []}
            
        except Exception as e:
            self.logger.error(f"Error checking org membership for {username}: {str(e)}")
            return {'member': False, 'teams': []}
            
    def get_pr_files(self, headers, repo, pr_number):
        """
        Fetch the list of files changed in a PR with line addition/deletion stats.
        """
        try:
            files = []
            page = 1
            total_additions = 0
            total_deletions = 0
            
            while True:
                response = requests.get(
                    f'{self.base_url}/repos/{repo}/pulls/{pr_number}/files',
                    headers=headers,
                    params={
                        'per_page': 100,
                        'page': page
                    }
                )
                
                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch PR files for {repo}#{pr_number}: {response.status_code}")
                    break
                    
                page_files = response.json()
                if not page_files:
                    break
                    
                files.extend(page_files)
                
                # Sum up additions and deletions
                for file in page_files:
                    total_additions += file.get('additions', 0)
                    total_deletions += file.get('deletions', 0)
                
                page += 1
            
            file_names = [file.get('filename', '') for file in files]
            
            return {
                'file_list': file_names,
                'file_count': len(file_names),
                'additions': total_additions,
                'deletions': total_deletions
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching PR files for {repo}#{pr_number}: {str(e)}")
            return {
                'file_list': [],
                'file_count': 0,
                'additions': 0,
                'deletions': 0
            }

    def fetch_pr_data(self, headers, repo, start_date, end_date):
        """
        Fetch enhanced pull request data including:
        - File changes and lines added/deleted
        - Target branch information
        - Days to merge/close
        - Approval comments and reviewer change requests
        - PR health metrics based purely on duration
        """
        try:
            self.logger.debug(f"Fetching PR data for {repo}")
            
            metrics = {
                'pull_requests': [],
                'stats': {
                    'total_prs': 0,
                    'merged_prs': 0,
                    'healthy_prs': 0,
                    'unhealthy_prs': 0,
                    'total_additions': 0,
                    'total_deletions': 0,
                    'total_change_requests': 0
                }
            }
            
            # Extract org name from repo full name (org/repo)
            org_name = repo.split('/')[0]
            
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
                            # Get detailed PR information including target branch
                            pr_details = self.get_pr_details(headers, repo, pr['number'])
                            target_branch = pr_details.get('base', {}).get('ref', '') if pr_details else ''
                            
                            # Get files changed in the PR
                            file_data = self.get_pr_files(headers, repo, pr['number'])
                            
                            # Update repository statistics
                            metrics['stats']['total_additions'] += file_data['additions']
                            metrics['stats']['total_deletions'] += file_data['deletions']
                            
                            # Calculate PR duration
                            pr_duration_days = 0
                            if pr['state'] == 'closed' and pr['closed_at']:
                                closed_at = datetime.strptime(pr['closed_at'], '%Y-%m-%dT%H:%M:%SZ')
                                closed_at = self.utc.localize(closed_at)
                                pr_duration_days = (closed_at - created_at).days
                            else:
                                # For open PRs, calculate days open so far
                                pr_duration_days = (datetime.now(self.utc) - created_at).days
                            
                            # Determine PR health based on duration only, regardless of state
                            pr_health = 'Healthy'
                            if pr_duration_days > self.pr_threshold_days:
                                pr_health = 'Unhealthy'
                                metrics['stats']['unhealthy_prs'] += 1
                            else:
                                metrics['stats']['healthy_prs'] += 1
                            
                            # Fetch PR reviews
                            reviews_response = requests.get(
                                f"{self.base_url}/repos/{repo}/pulls/{pr['number']}/reviews",
                                headers=headers
                            )
                            reviews = reviews_response.json() if reviews_response.status_code == 200 else []
                            
                            # Find approver and their comments
                            approver = ''
                            approver_comment = 'Approver not added comment'
                            approver_teams = []
                            
                            # Track change requests
                            change_requests = []
                            change_request_count = 0
                            pending_changes = 0
                            resolved_changes = 0
                            change_request_status = "No changes requested"
                            
                            for review in reviews:
                                review_state = review.get('state', '').upper()
                                reviewer = review.get('user', {}).get('login', '')
                                
                                # Process APPROVED reviews
                                if review_state == 'APPROVED' and not approver:
                                    approver = reviewer
                                    
                                    # Get approver's teams
                                    if approver:
                                        membership = self.get_org_membership(headers, org_name, approver)
                                        approver_teams = membership.get('teams', [])
                                    
                                    # Check if approver provided comments
                                    if review.get('body') and review.get('body').strip():
                                        approver_comment = review.get('body').strip()
                                
                                # Process CHANGES_REQUESTED reviews
                                elif review_state == 'CHANGES_REQUESTED':
                                    change_request_count += 1
                                    change_requests.append({
                                        'reviewer': reviewer,
                                        'comment': review.get('body', ''),
                                        'submitted_at': review.get('submitted_at', '')
                                    })
                            
                            # Determine if change requests are resolved
                            if change_request_count > 0:
                                # Check if PR is merged or closed
                                if pr['state'] == 'closed' and pr['merged_at']:
                                    change_request_status = "All changes resolved"
                                    resolved_changes = change_request_count
                                else:
                                    # Check if there's a later approval
                                    last_change_request = max([datetime.strptime(cr['submitted_at'], '%Y-%m-%dT%H:%M:%SZ') 
                                                            for cr in change_requests if cr['submitted_at']])
                                    
                                    approval_after_change = False
                                    for review in reviews:
                                        if review.get('state', '').upper() == 'APPROVED' and review.get('submitted_at'):
                                            approval_time = datetime.strptime(review['submitted_at'], '%Y-%m-%dT%H:%M:%SZ')
                                            if approval_time > last_change_request:
                                                approval_after_change = True
                                                break
                                    
                                    if approval_after_change:
                                        change_request_status = "Changes resolved"
                                        resolved_changes = change_request_count
                                    else:
                                        change_request_status = "Changes pending"
                                        pending_changes = change_request_count
                            
                            metrics['stats']['total_change_requests'] += change_request_count
                            
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
                            
                            # Build enhanced PR record
                            pr_data = {
                                'number': pr['number'],
                                'title': pr['title'],
                                'author': pr['user']['login'],
                                'state': pr['state'],
                                'created_at': created_at,
                                'merged_at': None,
                                'target_branch': target_branch,
                                'pr_duration_days': pr_duration_days,
                                'approver': approver,
                                'approver_comment': approver_comment,
                                'approver_teams': approver_teams,
                                'pr_health': pr_health,
                                'change_request_count': change_request_count,
                                'pending_changes': pending_changes,
                                'resolved_changes': resolved_changes,
                                'change_request_status': change_request_status,
                                'labels': [label['name'] for label in pr.get('labels', [])],
                                'commits': commit_data,
                                'reviews': reviews,
                                'file_count': file_data['file_count'],
                                'file_list': file_data['file_list'],
                                'additions': file_data['additions'],
                                'deletions': file_data['deletions']
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
        """Generate enhanced PR activity report with file changes and reviewer metrics."""
        try:
            self.logger.info("Generating PR activity report")
            
            activity_data = []
            for repo, metrics in all_metrics.items():
                for pr in metrics['pull_requests']:
                    # Create enhanced record with new metrics
                    record = {
                        'Repository': repo,
                        'PR Number': pr['number'],
                        'Title': pr['title'],
                        'Author': pr['author'],
                        'Status': pr['state'].capitalize(),
                        'Target Branch': pr['target_branch'],
                        'PR Health': pr['pr_health'],
                        'Health Threshold': f"{self.pr_threshold_days} days",
                        'Days Open': pr['pr_duration_days'],
                        'Created Date': pr['created_at'].strftime('%Y-%m-%d'),
                        'Merged Date': pr['merged_at'].strftime('%Y-%m-%d') if pr['merged_at'] else '',
                        'Approver': pr['approver'],
                        'Approver Teams': ', '.join(pr['approver_teams']),
                        'Approver Comment': pr['approver_comment'][:100] + '...' if len(pr['approver_comment']) > 100 else pr['approver_comment'],
                        'Change Requests': pr['change_request_count'],
                        'Changes Status': pr['change_request_status'],
                        'Pending Changes': pr['pending_changes'],
                        'Resolved Changes': pr['resolved_changes'],
                        'Files Changed': pr['file_count'],
                        'Lines Added': pr['additions'],
                        'Lines Deleted': pr['deletions'],
                        'Changed Files': ', '.join(pr['file_list'][:5]) + ('...' if len(pr['file_list']) > 5 else ''),
                        'Labels': ', '.join(pr['labels']),
                        'Commit Count': len(pr['commits'])
                    }
                    activity_data.append(record)
            
            df = pd.DataFrame(activity_data)
            
            # Apply conditional formatting for PR health
            df['PR Health'] = df['PR Health'].apply(lambda x: f"❌ {x}" if x == 'Unhealthy' else f"✅ {x}")
            
            output_file = f"{output_dir}/pr_activity_report.xlsx"
            
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='PR Activity', index=False)
                self._format_excel_sheet(writer.sheets['PR Activity'], df, writer.book)
            
            self.logger.info(f"Saved PR activity report: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error generating activity report: {str(e)}")

    def generate_contributor_report(self, all_metrics, output_dir):
        """Generate consolidated contributor metrics report with enhanced health metrics."""
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
                            'healthy_prs': 0,
                            'unhealthy_prs': 0,
                            'total_additions': 0,
                            'total_deletions': 0,
                            'total_commits': 0,
                            'approvals_given': 0,
                            'change_requests_received': 0,
                            'avg_days_to_merge': []
                        }
                    
                    stats = contributors[(repo, author)]
                    stats['prs_created'] += 1
                    stats['total_commits'] += len(pr['commits'])
                    stats['change_requests_received'] += pr['change_request_count']
                    
                    # Track code changes
                    stats['total_additions'] += pr['additions']
                    stats['total_deletions'] += pr['deletions']
                    
                    # Track PR health
                    if pr['pr_health'] == 'Unhealthy':
                        stats['unhealthy_prs'] += 1
                    else:
                        stats['healthy_prs'] += 1
                    
                    if pr['merged_at']:
                        stats['prs_merged'] += 1
                        stats['avg_days_to_merge'].append(pr['pr_duration_days'])
                    
                    # Track approvals
                    for review in pr['reviews']:
                        if review.get('state', '').upper() == 'APPROVED':
                            reviewer = review.get('user', {}).get('login', '')
                            if reviewer and (repo, reviewer) not in contributors:
                                contributors[(repo, reviewer)] = {
                                    'prs_created': 0,
                                    'prs_merged': 0,
                                    'healthy_prs': 0,
                                    'unhealthy_prs': 0,
                                    'total_additions': 0,
                                    'total_deletions': 0,
                                    'total_commits': 0,
                                    'approvals_given': 0,
                                    'change_requests_received': 0,
                                    'avg_days_to_merge': []
                                }
                            if reviewer:
                                contributors[(repo, reviewer)]['approvals_given'] += 1
                
                for (repo_name, author), stats in contributors.items():
                    avg_days = 0
                    if stats['avg_days_to_merge']:
                        avg_days = sum(stats['avg_days_to_merge']) / len(stats['avg_days_to_merge'])
                        
                    contributor_data.append({
                        'Repository': repo_name,
                        'Contributor': author,
                        'PRs Created': stats['prs_created'],
                        'PRs Merged': stats['prs_merged'],
                        'Healthy PRs': stats['healthy_prs'],
                        'Unhealthy PRs': stats['unhealthy_prs'],
                        'Health Ratio': f"{stats['healthy_prs']}/{stats['prs_created']}",
                        'Avg Days to Merge': round(avg_days, 1),
                        'Lines Added': stats['total_additions'],
                        'Lines Deleted': stats['total_deletions'],
                        'Total Commits': stats['total_commits'],
                        'Approvals Given': stats['approvals_given'],
                        'Change Requests Received': stats['change_requests_received']
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
        """Generate consolidated commit details report with merge dates and correct health status."""
        try:
            self.logger.info("Generating commit report")
            
            commit_data = []
            for repo, metrics in all_metrics.items():
                for pr in metrics['pull_requests']:
                    # Use the already calculated health status directly
                    pr_health = pr['pr_health']
                    
                    for commit in pr['commits']:
                        record = {
                            'Repository': repo,
                            'PR Number': pr['number'],
                            'PR Title': pr['title'],
                            'PR Author': pr['author'],
                            'Target Branch': pr['target_branch'],
                            'PR Days Open': pr['pr_duration_days'],
                            'PR Health': pr_health,  # Use the pre-calculated health status
                            'Health Threshold': f"{self.pr_threshold_days} days",
                            'Commit SHA': commit.get('sha', ''),
                            'Commit Message': commit.get('message', '').split('\n')[0],
                            'Author': commit.get('author', ''),
                            'Commit Date': datetime.strptime(commit.get('date', ''),
                                        '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d'),
                            'PR Status': pr['state'].capitalize(),
                            'Merged Date': pr['merged_at'].strftime('%Y-%m-%d') if pr['merged_at'] else '',
                            'Files Changed': pr['file_count'],
                            'Lines Added': pr['additions'],
                            'Lines Deleted': pr['deletions'],
                            'Change Requests': pr['change_request_count']
                        }
                        commit_data.append(record)
            
            df = pd.DataFrame(commit_data)
            
            # Apply conditional formatting for PR health
            df['PR Health'] = df['PR Health'].apply(lambda x: f"❌ {x}" if x == 'Unhealthy' else f"✅ {x}")
            
            output_file = f"{output_dir}/commit_report.xlsx"
            
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Commit Details', index=False)
                self._format_excel_sheet(writer.sheets['Commit Details'], df, writer.book)
            
            self.logger.info(f"Saved commit report: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error generating commit report: {str(e)}")

    def _format_excel_sheet(self, worksheet, dataframe, workbook):
        """Apply enhanced formatting to Excel worksheets with conditional formatting."""
        try:
            # Define standard formats
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
            
            decimal_format = workbook.add_format({
                'num_format': '#,##0.0',
                'align': 'right'
            })
            
            text_format = workbook.add_format({
                'text_wrap': True,
                'valign': 'top'
            })
            
            # Formats for PR health indicators
            health_format_good = workbook.add_format({
                'bg_color': '#E6F4EA',  # Light green
                'font_color': '#137333'  # Dark green
            })
            
            health_format_bad = workbook.add_format({
                'bg_color': '#FCE8E6',  # Light red
                'font_color': '#C5221F'  # Dark red
            })
            
            # Format for pending changes status
            pending_format = workbook.add_format({
                'bg_color': '#FFF0B3',  # Light yellow
                'font_color': '#994C00'  # Dark orange
            })
            
            # Format for resolved changes status
            resolved_format = workbook.add_format({
                'bg_color': '#E6F4EA',  # Light green
                'font_color': '#137333'  # Dark green
            })
            
            # Format columns based on content type
            for idx, col in enumerate(dataframe.columns):
                max_len = max(
                    dataframe[col].astype(str).apply(len).max(),
                    len(str(col))
                ) + 2
                
                if 'Date' in col:
                    worksheet.set_column(idx, idx, max(12, max_len), date_format)
                elif col in ['Days Open', 'Avg Days to Merge', 'PR Days Open']:
                    worksheet.set_column(idx, idx, max(8, max_len), decimal_format)
                elif any(word in col for word in ['Count', 'Added', 'Deleted', 'Number', 'Total', 'PRs', 'Lines', 'Requests', 'Changes']):
                    worksheet.set_column(idx, idx, max(8, max_len), number_format)
                elif col in ['Title', 'Commit Message', 'Labels', 'Approver Comment', 'Changed Files', 'Approver Teams']:
                    worksheet.set_column(idx, idx, min(50, max_len), text_format)
                elif col == 'PR Health':
                    worksheet.set_column(idx, idx, max(15, max_len))
                    # Add conditional formatting for health column
                    worksheet.conditional_format(1, idx, len(dataframe) + 1, idx, {
                        'type': 'text',
                        'criteria': 'containing',
                        'value': '❌',
                        'format': health_format_bad
                    })
                    worksheet.conditional_format(1, idx, len(dataframe) + 1, idx, {
                        'type': 'text',
                        'criteria': 'containing',
                        'value': '✅',
                        'format': health_format_good
                    })
                elif col == 'Changes Status':
                    worksheet.set_column(idx, idx, max(20, max_len))
                    # Add conditional formatting for change request status
                    worksheet.conditional_format(1, idx, len(dataframe) + 1, idx, {
                        'type': 'text',
                        'criteria': 'containing',
                        'value': 'pending',
                        'format': pending_format
                    })
                    worksheet.conditional_format(1, idx, len(dataframe) + 1, idx, {
                        'type': 'text',
                        'criteria': 'containing',
                        'value': 'resolved',
                        'format': resolved_format
                    })
                else:
                    worksheet.set_column(idx, idx, min(30, max_len), text_format)
                
                worksheet.write(0, idx, col, header_format)
            
            # Add alternating row colors for readability
            for row in range(1, len(dataframe) + 1):
                if row % 2 == 0:
                    bg_format = workbook.add_format({'bg_color': '#F8F8F8'})
                    worksheet.set_row(row, None, bg_format)
            
            # Freeze header row and left columns
            worksheet.freeze_panes(1, 2)
            
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
    parser.add_argument('--pr-threshold', type=int, default=2, help='PR health threshold in days (default: 2)')
    return parser.parse_args()


def main():
    """Main execution flow optimized for CI/CD."""
    try:
        args = parse_arguments()
        
        print("\nGitHub Repository Metrics Reporter")
        print("=================================")
        
        reporter = GitHubMetricsReporter()
        
        # Set PR threshold days from command line if provided
        if args.pr_threshold:
            reporter.pr_threshold_days = args.pr_threshold
            reporter.logger.info(f"PR health threshold set to {reporter.pr_threshold_days} days")
        
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
                    healthy = metrics['stats']['healthy_prs']
                    unhealthy = metrics['stats']['unhealthy_prs']
                    additions = metrics['stats']['total_additions']
                    deletions = metrics['stats']['total_deletions']
                    change_requests = metrics['stats']['total_change_requests']
                    reporter.logger.info(
                        f"Found {metrics['stats']['total_prs']} PRs for {repo} "
                        f"({healthy} healthy, {unhealthy} unhealthy) "
                        f"with {change_requests} change requests, "
                        f"{additions} lines added and {deletions} lines deleted"
                    )
                
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
            healthy_prs = sum(metrics['stats']['healthy_prs'] for metrics in all_metrics.values())
            unhealthy_prs = sum(metrics['stats']['unhealthy_prs'] for metrics in all_metrics.values())
            total_additions = sum(metrics['stats']['total_additions'] for metrics in all_metrics.values())
            total_deletions = sum(metrics['stats']['total_deletions'] for metrics in all_metrics.values())
            total_change_requests = sum(metrics['stats']['total_change_requests'] for metrics in all_metrics.values())
            
            print(f"\nSummary: Processed {total_prs} PRs across {total_repos} repositories")
            print(f"Health Status: {healthy_prs} healthy PRs, {unhealthy_prs} unhealthy PRs")
            print(f"Change Requests: {total_change_requests} total change requests")
            print(f"Code Changes: {total_additions} lines added, {total_deletions} lines deleted")
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
