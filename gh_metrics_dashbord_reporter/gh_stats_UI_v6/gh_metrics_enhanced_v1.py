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
import re
import time

class GitHubMetricsReporter:
    """
    GitHub repository metrics reporter focused on contributor metrics and PR activity
    with enhanced health indicators, check status tracking, and version type analysis.
    """
    
    def __init__(self):
        """Initialize reporter with configuration and logging setup."""
        self.base_url = 'https://api.github.com'
        self.utc = pytz.UTC
        self.api_calls = 0
        self.start_time = datetime.now(self.utc)
        # PR threshold for health metrics (in days) - updated to 7 days
        self.pr_threshold_days = 7
        # Maximum labels threshold
        self.max_labels_threshold = 2
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
        
        # Check GitHub token environment variable
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
    
    def get_check_runs(self, headers, repo, commit_sha):
        """
        Fetch check runs for a specific commit to track passed and failed checks.
        """
        try:
            self.logger.debug(f"Fetching check runs for {repo} commit {commit_sha}")
            
            response = requests.get(
                f'{self.base_url}/repos/{repo}/commits/{commit_sha}/check-runs',
                headers=headers
            )
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch check runs: {response.status_code}")
                return {'total': 0, 'passed': 0, 'failed': 0}
            
            checks = response.json().get('check_runs', [])
            
            total_checks = len(checks)
            passed_checks = sum(1 for check in checks if check.get('conclusion') == 'success')
            failed_checks = sum(1 for check in checks if check.get('conclusion') in ['failure', 'cancelled', 'timed_out'])
            
            return {
                'total': total_checks,
                'passed': passed_checks,
                'failed': failed_checks
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching check runs for {commit_sha}: {str(e)}")
            return {'total': 0, 'passed': 0, 'failed': 0}

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

    def is_feat_or_fix_pr(self, pr_title):
        """
        Check if a PR title starts with 'feat:', 'feat!:', 'fix:' or contains these as prefixes.
        Also identifies breaking changes with 'feat!'.
        
        Args:
            pr_title (str): The PR title to check
            
        Returns:
            tuple: (is_feat_or_fix, is_breaking_change)
        """
        if not pr_title:
            return (False, False)
            
        # Normalize the title by converting to lowercase
        title_lower = pr_title.lower()
        
        # Check for breaking change pattern
        is_breaking_change = 'feat!' in title_lower[:6]  # Check only at the beginning
        
        # Check for common prefix patterns
        prefixes = ['feat:', 'feat(', 'fix:', 'fix(', 'feat!:', 'feat!(']
        for prefix in prefixes:
            if title_lower.startswith(prefix):
                return (True, is_breaking_change)
        
        # Check for standalone words at the beginning
        if title_lower.startswith('feat ') or title_lower.startswith('fix ') or title_lower.startswith('feat! '):
            return (True, is_breaking_change)
            
        return (False, is_breaking_change)

    def check_folder_in_files(self, file_list, folder_name):
        """
        Check if any file in the list is inside the specified folder.
        
        Args:
            file_list (list): List of file paths
            folder_name (str): Name of the folder to check
            
        Returns:
            bool: True if any file is in the folder, False otherwise
        """
        if not file_list:
            return False
            
        for file_path in file_list:
            if file_path.startswith(f"{folder_name}/") or f"/{folder_name}/" in file_path:
                return True
                
        return False

    def analyze_version_labels(self, labels):
        """
        Analyze PR labels to determine RC, NPD, and Stable version counts.
        
        - RC versions: Labels ending with '-rc' (case insensitive)
        - NPD versions: Labels ending with '-npd' (case insensitive)
        - Stable versions: Labels that don't end with either '-rc' or '-npd'
        """
        rc_versions = 0
        npd_versions = 0
        stable_versions = 0
        
        for label in labels:
            label_lower = label.lower()
            if label_lower.endswith('-rc'):
                rc_versions += 1
            elif label_lower.endswith('-npd'):
                npd_versions += 1
            else:
                stable_versions += 1
        
        return {
            'rc_versions': rc_versions,
            'npd_versions': npd_versions,
            'stable_versions': stable_versions
        }

    def fetch_pr_data(self, headers, repo, start_date, end_date):
        """
        Fetch enhanced pull request data including:
        - File changes and lines added/deleted
        - Target branch information
        - Days to merge/close
        - Approval comments and reviewer change requests
        - PR health metrics based on duration and label count
        - Check runs status (passed/failed)
        - Version type analysis based on labels (RC, NPD, Stable)
        - Comment counts and conversation tracking
        - Breaking change detection
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
                    'unhealthy_due_to_duration': 0,
                    'unhealthy_due_to_labels': 0,
                    'total_additions': 0,
                    'total_deletions': 0,
                    'total_change_requests': 0,
                    'total_passed_checks': 0,
                    'total_failed_checks': 0,
                    'total_rc_versions': 0,
                    'total_npd_versions': 0,
                    'total_stable_versions': 0
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
                            
                            # Extract PR labels
                            labels = [label['name'] for label in pr.get('labels', [])]
                            label_count = len(labels)
                            
                            # Determine PR health based on duration and label count
                            pr_health = 'Healthy'
                            health_reasons = []
                            
                            if pr_duration_days > self.pr_threshold_days:
                                pr_health = 'Needs Attention'
                                metrics['stats']['unhealthy_due_to_duration'] += 1
                                health_reasons.append(f"PR open > {self.pr_threshold_days} days")
                            
                            if label_count > self.max_labels_threshold:
                                pr_health = 'Needs Attention'
                                metrics['stats']['unhealthy_due_to_labels'] += 1
                                health_reasons.append(f"PR has > {self.max_labels_threshold} labels")
                            
                            if pr_health == 'Needs Attention':
                                metrics['stats']['unhealthy_prs'] += 1
                            else:
                                metrics['stats']['healthy_prs'] += 1
                            
                            # Analyze version types based on labels
                            version_analysis = self.analyze_version_labels(labels)
                            
                            # Update version statistics
                            metrics['stats']['total_rc_versions'] += version_analysis['rc_versions']
                            metrics['stats']['total_npd_versions'] += version_analysis['npd_versions']
                            metrics['stats']['total_stable_versions'] += version_analysis['stable_versions']
                            
                            # Fetch PR reviews
                            reviews_response = requests.get(
                                f"{self.base_url}/repos/{repo}/pulls/{pr['number']}/reviews",
                                headers=headers
                            )
                            reviews = reviews_response.json() if reviews_response.status_code == 200 else []
                            
                            # Find approvers and their comments
                            approvers = []
                            approver_comments = []
                            approvals_with_comments = 0
                            approvals_without_comments = 0
                            
                            # Track change requests
                            change_requests = []
                            change_request_count = 0
                            change_request_status = "No changes requested"
                            
                            for review in reviews:
                                review_state = review.get('state', '').upper()
                                reviewer = review.get('user', {}).get('login', '')
                                
                                # Process APPROVED reviews
                                if review_state == 'APPROVED':
                                    approvers.append(reviewer)
                                    
                                    # Check if approver provided comments
                                    if review.get('body') and review.get('body').strip():
                                        approver_comments.append(review.get('body').strip())
                                        approvals_with_comments += 1
                                    else:
                                        approvals_without_comments += 1
                                
                                # Process CHANGES_REQUESTED reviews
                                elif review_state == 'CHANGES_REQUESTED':
                                    change_request_count += 1
                                    change_requests.append({
                                        'reviewer': reviewer,
                                        'comment': review.get('body', ''),
                                        'submitted_at': review.get('submitted_at', '')
                                    })
                            
                            metrics['stats']['total_change_requests'] += change_request_count
                            
                            # Determine if change requests are resolved
                            if change_request_count > 0:
                                # Check if PR is merged or closed
                                if pr['state'] == 'closed' and pr.get('merged_at'):
                                    change_request_status = "All changes resolved"
                                else:
                                    change_request_status = "Changes pending"
                            
                            # Fetch PR comments
                            comments_response = requests.get(
                                f"{self.base_url}/repos/{repo}/issues/{pr['number']}/comments",
                                headers=headers
                            )
                            comments = comments_response.json() if comments_response.status_code == 200 else []
                            
                            # Count reviewer comments and approver comments
                            total_reviewer_comments = 0
                            total_approver_comments = 0
                            
                            # Count approver comments from reviews
                            for review in reviews:
                                reviewer = review.get('user', {}).get('login', '')
                                if reviewer in approvers:
                                    if review.get('body') and review.get('body').strip():
                                        total_approver_comments += 1
                                else:
                                    if review.get('body') and review.get('body').strip():
                                        total_reviewer_comments += 1
                            
                            # Count comments from issue comments
                            for comment in comments:
                                commenter = comment.get('user', {}).get('login', '')
                                if commenter in approvers:
                                    total_approver_comments += 1
                                else:
                                    total_reviewer_comments += 1
                            
                            # Fetch PR review comments (line comments)
                            review_comments_response = requests.get(
                                f"{self.base_url}/repos/{repo}/pulls/{pr['number']}/comments",
                                headers=headers
                            )
                            review_comments = review_comments_response.json() if review_comments_response.status_code == 200 else []
                            
                            # Count resolved and unresolved conversations
                            total_resolved_conversations = 0
                            total_unresolved_conversations = 0
                            
                            # A simple heuristic: a conversation is resolved if it has a reply from the PR author
                            conversation_threads = {}
                            
                            for comment in review_comments:
                                thread_id = comment.get('in_reply_to_id', comment.get('id'))
                                if thread_id not in conversation_threads:
                                    conversation_threads[thread_id] = {
                                        'resolved': False,
                                        'commenters': set()
                                    }
                                conversation_threads[thread_id]['commenters'].add(comment.get('user', {}).get('login', ''))
                                
                                # Count comment by role
                                commenter = comment.get('user', {}).get('login', '')
                                if commenter in approvers:
                                    total_approver_comments += 1
                                else:
                                    total_reviewer_comments += 1
                            
                            # Check if the PR author responded to each thread
                            author = pr['user']['login']
                            for thread_id, thread in conversation_threads.items():
                                if author in thread['commenters']:
                                    total_resolved_conversations += 1
                                else:
                                    total_unresolved_conversations += 1
                            
                            # Fetch commits with pagination - IMPROVED IMPLEMENTATION
                            commits = []
                            page = 1
                            has_more_commits = True
                            max_retries = 3
                            
                            while has_more_commits:
                                try:
                                    # Make sure we explicitly set per_page to 100 (maximum allowed by GitHub API)
                                    # and include proper pagination parameters
                                    commits_url = pr['commits_url']
                                    
                                    # Add debugging to see exact URL and page count
                                    self.logger.debug(f"Fetching PR commits page {page} from {commits_url} for PR #{pr['number']}")
                                    
                                    retry_count = 0
                                    commits_response = None
                                    
                                    # Add retry logic for resilience
                                    while retry_count < max_retries:
                                        try:
                                            commits_response = requests.get(
                                                commits_url,
                                                headers=headers,
                                                params={
                                                    'per_page': 100,  # Request maximum items per page
                                                    'page': page
                                                },
                                                timeout=30  # Add a timeout for network reliability
                                            )
                                            break  # Break out of retry loop if successful
                                        except requests.exceptions.RequestException as e:
                                            retry_count += 1
                                            if retry_count >= max_retries:
                                                self.logger.error(f"Failed to fetch PR commits after {max_retries} retries: {str(e)}")
                                                raise
                                            self.logger.warning(f"Retry {retry_count}/{max_retries} for PR commits: {str(e)}")
                                            time.sleep(2)  # Wait before retrying
                                    
                                    # Check response status
                                    if commits_response.status_code != 200:
                                        self.logger.error(f"Failed to fetch PR commits for {repo}#{pr['number']}: {commits_response.status_code}")
                                        self.logger.error(f"Response: {commits_response.text[:200]}...")  # Log part of the response for debugging
                                        break
                                    
                                    # Get commits from this page
                                    page_commits = commits_response.json()
                                    
                                    # Check if we received any commits
                                    if not page_commits:
                                        self.logger.debug(f"No more commits found for PR #{pr['number']} after page {page-1}")
                                        has_more_commits = False
                                        break
                                    
                                    # Process this page's commits
                                    commits.extend(page_commits)
                                    self.logger.debug(f"Fetched {len(page_commits)} commits from page {page}, total commits so far: {len(commits)}")
                                    
                                    # Check if we should continue to the next page
                                    # GitHub API includes a Link header that indicates if there are more pages
                                    if 'Link' in commits_response.headers and 'rel="next"' in commits_response.headers['Link']:
                                        page += 1
                                    else:
                                        # No more pages indicated by Link header
                                        has_more_commits = False
                                        
                                except Exception as e:
                                    self.logger.error(f"Error fetching commits for PR #{pr['number']}: {str(e)}")
                                    break
                            
                            # After fetching all commits, log the total count for verification
                            self.logger.info(f"Total commits found for PR #{pr['number']}: {len(commits)}")
                            
                            # Process commit data and check status
                            commit_data = []
                            total_passed_checks = 0
                            total_failed_checks = 0
                            
                            for commit in commits:
                                commit_info = commit.get('commit', {})
                                author_info = commit_info.get('author', {})
                                commit_sha = commit.get('sha', '')
                                
                                # Get check runs for this commit
                                check_runs = self.get_check_runs(headers, repo, commit_sha)
                                total_passed_checks += check_runs['passed']
                                total_failed_checks += check_runs['failed']
                                
                                commit_data.append({
                                    'sha': commit_sha,
                                    'message': commit_info.get('message', ''),
                                    'author': author_info.get('name', ''),
                                    'date': author_info.get('date', ''),
                                    'passed_checks': check_runs['passed'],
                                    'failed_checks': check_runs['failed']
                                })
                            
                            metrics['stats']['total_passed_checks'] += total_passed_checks
                            metrics['stats']['total_failed_checks'] += total_failed_checks
                            
                            # Determine if this is a feat/fix PR and if it's a breaking change
                            is_feat_fix, is_breaking_change = self.is_feat_or_fix_pr(pr['title'])

                            # Check for examples, tests, and integration_tests folders in the changed files
                            has_examples = self.check_folder_in_files(file_data['file_list'], 'examples') if is_feat_fix else False
                            has_tests = self.check_folder_in_files(file_data['file_list'], 'tests') if is_feat_fix else False
                            has_integration_tests = self.check_folder_in_files(file_data['file_list'], 'integration_tests') if is_feat_fix else False
                            
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
                                'approvers': approvers,
                                'approver_comments': approver_comments,
                                'approvals_with_comments': approvals_with_comments,
                                'approvals_without_comments': approvals_without_comments,
                                'pr_health': pr_health,
                                'health_reasons': health_reasons,
                                'change_request_count': change_request_count,  # Keep for backward compatibility
                                'change_request_status': change_request_status,  # Keep for backward compatibility
                                'total_reviewer_comments': total_reviewer_comments,
                                'total_approver_comments': total_approver_comments,
                                'total_resolved_conversations': total_resolved_conversations,
                                'total_unresolved_conversations': total_unresolved_conversations,
                                'labels': labels,
                                'label_count': label_count,
                                'rc_versions': version_analysis['rc_versions'],
                                'npd_versions': version_analysis['npd_versions'],
                                'stable_versions': version_analysis['stable_versions'],
                                'commits': commit_data,
                                'commit_count': len(commit_data),
                                'file_count': file_data['file_count'],
                                'file_list': file_data['file_list'],
                                'additions': file_data['additions'],
                                'deletions': file_data['deletions'],
                                'passed_checks': total_passed_checks,
                                'failed_checks': total_failed_checks,
                                'is_feat_fix_pr': is_feat_fix,
                                'is_breaking_change': is_breaking_change,
                                'has_examples': has_examples,
                                'has_tests': has_tests,
                                'has_integration_tests': has_integration_tests
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

    def fetch_additional_contributor_commits(self, headers, repo, start_date, end_date):
        """
        Fetch all contributors who made commits between start_date and end_date,
        regardless of whether they created PRs.
        
        Args:
            headers (dict): API headers
            repo (str): Repository name (org/repo)
            start_date (datetime): Start date for analysis
            end_date (datetime): End date for analysis
            
        Returns:
            dict: Dictionary of contributors with their commit counts
        """
        try:
            self.logger.debug(f"Fetching direct commits for {repo} between {start_date.date()} and {end_date.date()}")
            
            # Track contributors and their commit counts
            contributor_commits = {}
            
            # Format dates for GitHub API (ISO 8601)
            start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Fetch commits within date range with pagination
            page = 1
            max_retries = 3
            while True:
                self.logger.debug(f"Fetching page {page} of direct commits for {repo}")
                
                # Add retry logic
                retry_count = 0
                response = None
                
                while retry_count < max_retries:
                    try:
                        response = requests.get(
                            f'{self.base_url}/repos/{repo}/commits',
                            headers=headers,
                            params={
                                'since': start_date_str,
                                'until': end_date_str,
                                'per_page': 100,
                                'page': page
                            },
                            timeout=30
                        )
                        break
                    except requests.exceptions.RequestException as e:
                        retry_count += 1
                        if retry_count >= max_retries:
                            self.logger.error(f"Failed to fetch commits after {max_retries} retries: {str(e)}")
                            raise
                        self.logger.warning(f"Retry {retry_count}/{max_retries} for commits: {str(e)}")
                        time.sleep(2)  # Wait before retrying
                
                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch commits for {repo}: {response.status_code}")
                    self.logger.error(f"Response: {response.text[:200]}...")  # Log part of the response for debugging
                    break
                
                commits = response.json()
                if not commits:
                    break
                
                for commit in commits:
                    try:
                        # Get author username
                        author_username = commit.get('author', {}).get('login')
                        committer_username = commit.get('committer', {}).get('login')
                        
                        # Track commit for author if available
                        if author_username:
                            if author_username not in contributor_commits:
                                contributor_commits[author_username] = {
                                    'total_commits': 0,
                                    'repository': repo
                                }
                            contributor_commits[author_username]['total_commits'] += 1
                        
                        # Track commit for committer if available and different from author
                        if committer_username and committer_username != author_username:
                            if committer_username not in contributor_commits:
                                contributor_commits[committer_username] = {
                                    'total_commits': 0,
                                    'repository': repo
                                }
                            contributor_commits[committer_username]['total_commits'] += 1
                    except Exception as e:
                        self.logger.error(f"Error processing commit in {repo}: {str(e)}")
                        continue
                
                # Check if we should continue to the next page
                if 'Link' in response.headers and 'rel="next"' in response.headers['Link']:
                    page += 1
                else:
                    break
                
            self.logger.info(f"Found {len(contributor_commits)} contributors who made commits in {repo} between {start_date.date()} and {end_date.date()}")
            return contributor_commits
            
        except Exception as e:
            self.logger.error(f"Error fetching direct commits for {repo}: {str(e)}")
            return {}

    def generate_pr_activity_report(self, all_metrics, output_dir, all_repositories=None):
        """
        Generate enhanced PR activity report with health indicators based on:
        - PR duration (> 7 days = needs attention)
        - Label count (> 2 labels = needs attention)
        
        Includes:
        - Approver details
        - PRs approved with/without comments
        - Label counts
        - Version type analysis (RC, NPD, Stable)
        - Commit counts
        - PR dates and duration
        - Health status and reasons
        - Comment counts and conversation tracking
        - Breaking change indicators
        - Repositories with no PRs marked as 'Stable/No Dev'
        
        Args:
            all_metrics (dict): Dictionary of repository metrics
            output_dir (str): Output directory path
            all_repositories (list, optional): List of all repositories to include
                even if they have no PRs in the analyzed period
        """
        try:
            self.logger.info("Generating PR activity report")
            
            activity_data = []
            summary_data = []
            
            for repo, metrics in all_metrics.items():
                repo_summary = {
                    'Repository': repo,
                    'Total PRs': metrics['stats']['total_prs'],
                    'Merged PRs': metrics['stats']['merged_prs'],
                    'Open PRs': metrics['stats']['total_prs'] - metrics['stats']['merged_prs'],
                    'Healthy PRs': metrics['stats']['healthy_prs'],
                    'Unhealthy PRs': metrics['stats']['unhealthy_prs'],
                    'Unhealthy Due to Duration': metrics['stats']['unhealthy_due_to_duration'],
                    'Unhealthy Due to Labels': metrics['stats']['unhealthy_due_to_labels'],
                    'RC Versions': metrics['stats']['total_rc_versions'],
                    'NPD Versions': metrics['stats']['total_npd_versions'],
                    'Stable Versions': metrics['stats']['total_stable_versions'],
                    'Avg PR Duration (days)': 0,
                    'PRs With Comments': 0,
                    'PRs Without Comments': 0,
                    'Total Change Requests': metrics['stats']['total_change_requests'],
                    'Health Ratio': f"{metrics['stats']['healthy_prs']}/{metrics['stats']['total_prs']}",
                    'Health Percentage': 0,
                    'Feature/Fix PRs': 0,
                    'Breaking Change PRs': 0,
                    'PRs with Examples': 0,
                    'PRs with Tests': 0,
                    'PRs with Integration Tests': 0
                }
                
                if metrics['stats']['total_prs'] > 0:
                    repo_summary['Health Percentage'] = round((metrics['stats']['healthy_prs'] / metrics['stats']['total_prs']) * 100, 1)
                
                total_duration = 0
                
                for pr in metrics['pull_requests']:
                    # Update feature/fix counters
                    if pr.get('is_feat_fix_pr', False):
                        repo_summary['Feature/Fix PRs'] += 1
                        if pr.get('is_breaking_change', False):
                            repo_summary['Breaking Change PRs'] += 1
                        if pr.get('has_examples', False):
                            repo_summary['PRs with Examples'] += 1
                        if pr.get('has_tests', False):
                            repo_summary['PRs with Tests'] += 1
                        if pr.get('has_integration_tests', False):
                            repo_summary['PRs with Integration Tests'] += 1
                    
                    # Create enhanced record with new metrics
                    record = {
                        'Repository': repo,
                        'PR Number': pr['number'],
                        'Title': pr['title'],
                        'Author': pr['author'],
                        'Status': pr['state'].capitalize(),
                        'Target Branch': pr['target_branch'],
                        'PR Health': pr['pr_health'],
                        'Health Reasons': ', '.join(pr['health_reasons']) if pr['health_reasons'] else 'N/A',
                        'Health Threshold': f"> {self.pr_threshold_days} days OR > {self.max_labels_threshold} labels",
                        'Days Open': pr['pr_duration_days'],
                        'Created Date': pr['created_at'].strftime('%Y-%m-%d'),
                        'Merged Date': pr['merged_at'].strftime('%Y-%m-%d') if pr['merged_at'] else 'Not Merged',
                        'Approvers': ', '.join(pr['approvers']) if pr['approvers'] else 'None',
                        'Approvals With Comments': pr['approvals_with_comments'],
                        'Approvals Without Comments': pr['approvals_without_comments'],
                        'Approver Comments': '; '.join(pr['approver_comments'][:3]) if pr['approver_comments'] else 'None',
                        'Total Reviewer Comments': pr.get('total_reviewer_comments', 0),
                        'Total Approver Comments': pr.get('total_approver_comments', 0),
                        'Total Resolved Conversations': pr.get('total_resolved_conversations', 0),
                        'Total Unresolved Conversations': pr.get('total_unresolved_conversations', 0),
                        'Label Count': pr['label_count'],
                        'Labels': ', '.join(pr['labels']) if pr['labels'] else 'None',
                        'RC Versions': pr['rc_versions'],
                        'NPD Versions': pr['npd_versions'],
                        'Stable Versions': pr['stable_versions'],
                        'Commit Count': pr['commit_count'],
                        'Files Changed': pr['file_count'],
                        'Lines Added': pr['additions'],
                        'Lines Deleted': pr['deletions'],
                        'Passed Checks': pr['passed_checks'],
                        'Failed Checks': pr['failed_checks'],
                        'Check Success Rate': round((pr['passed_checks'] / (pr['passed_checks'] + pr['failed_checks'])) * 100, 1) if (pr['passed_checks'] + pr['failed_checks']) > 0 else 'N/A',
                        'Changed Files': ', '.join(pr['file_list'][:5]) + ('...' if len(pr['file_list']) > 5 else ''),
                        'Is Feature/Fix PR': 'Yes' if pr.get('is_feat_fix_pr', False) else 'No',
                        'Is Breaking Change': 'Yes' if pr.get('is_breaking_change', False) else 'No',
                        'Has Examples': 'Yes' if pr.get('has_examples', False) else 'No' if pr.get('is_feat_fix_pr', False) else 'N/A',
                        'Has Tests': 'Yes' if pr.get('has_tests', False) else 'No' if pr.get('is_feat_fix_pr', False) else 'N/A',
                        'Has Integration Tests': 'Yes' if pr.get('has_integration_tests', False) else 'No' if pr.get('is_feat_fix_pr', False) else 'N/A'
                    }
                    activity_data.append(record)
                    
                    total_duration += pr['pr_duration_days']
                    
                    if pr['approvals_with_comments'] > 0:
                        repo_summary['PRs With Comments'] += 1
                    elif pr['approvals_without_comments'] > 0:
                        repo_summary['PRs Without Comments'] += 1
                
                if metrics['stats']['total_prs'] > 0:
                    repo_summary['Avg PR Duration (days)'] = round(total_duration / metrics['stats']['total_prs'], 1)
                
                summary_data.append(repo_summary)
            
            # Add repositories with no PRs in the date range
            if all_repositories:
                # Get list of repos already processed (with PRs)
                processed_repos = [summary.get('Repository') for summary in summary_data]
                
                # Add entries for repos with no PRs
                for repo in all_repositories:
                    if repo not in processed_repos:
                        self.logger.info(f"Adding repo with no PRs: {repo}")
                        repo_summary = {
                            'Repository': repo,
                            'Total PRs': 0,
                            'Merged PRs': 0,
                            'Open PRs': 0,
                            'Healthy PRs': 0,
                            'Unhealthy PRs': 0,
                            'Unhealthy Due to Duration': 0,
                            'Unhealthy Due to Labels': 0,
                            'RC Versions': 0,
                            'NPD Versions': 0,
                            'Stable Versions': 0,
                            'Avg PR Duration (days)': 0,
                            'PRs With Comments': 0,
                            'PRs Without Comments': 0,
                            'Total Change Requests': 0,
                            'Health Ratio': '0/0',
                            'Health Percentage': 100,  # 100% healthy by default
                            'Feature/Fix PRs': 0,
                            'Breaking Change PRs': 0,
                            'PRs with Examples': 0,
                            'PRs with Tests': 0,
                            'PRs with Integration Tests': 0,
                            'Status': 'Stable/No Dev'
                        }
                        
                        # Add the repo to summary data
                        summary_data.append(repo_summary)
            
            # Create DataFrames
            pr_df = pd.DataFrame(activity_data)
            summary_df = pd.DataFrame(summary_data)
            
            # Apply conditional formatting for PR health
            pr_df['PR Health'] = pr_df['PR Health'].apply(lambda x: f"❌ {x}" if x == 'Needs Attention' else f"✅ {x}")
            
            output_file = f"{output_dir}/pr_activity_report.xlsx"
            
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                # Write PR Activity data
                pr_df.to_excel(writer, sheet_name='PR Activity', index=False)
                self._format_excel_sheet(writer.sheets['PR Activity'], pr_df, writer.book)
                
                # Write Summary data
                summary_df.to_excel(writer, sheet_name='Repository Summary', index=False)
                self._format_summary_sheet(writer.sheets['Repository Summary'], summary_df, writer.book)
            
            self.logger.info(f"Saved PR activity report: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error generating activity report: {str(e)}")

    def generate_contributor_report(self, all_metrics, output_dir, all_contributors=None, headers=None, start_date=None, end_date=None):
        """
        Generate enhanced contributor metrics report including:
        - Total commits by each contributor
        - Total PRs by each contributor
        - Average commits per day
        - Total passed/failed checks
        - Health indicators
        
        Args:
            all_metrics (dict): Dictionary of repository metrics
            output_dir (str): Output directory path
            all_contributors (list, optional): List of all contributors to include
                even if they have no activity in the analyzed period
            headers (dict, optional): API headers for additional GitHub API calls
            start_date (datetime, optional): Start date for the analysis period
            end_date (datetime, optional): End date for the analysis period
        """
        try:
            self.logger.info("Generating contributor report")
            
            contributor_data = []
            summary_data = []
            
            # Track contributors across all repositories
            all_contributors_data = {}
            
            for repo, metrics in all_metrics.items():
                # Initialize contributor tracking for this repo
                contributors = {}
                
                # Track first and last commit dates for each contributor
                contributor_first_date = {}
                contributor_last_date = {}
                
                for pr in metrics['pull_requests']:
                    author = pr['author']
                    
                    if author not in contributors:
                        contributors[author] = {
                            'repository': repo,
                            'contributor': author,
                            'total_commits': 0,
                            'total_prs': 0,
                            'healthy_prs': 0,
                            'unhealthy_prs': 0,
                            'passed_checks': 0,
                            'failed_checks': 0,
                            'rc_versions': 0,
                            'npd_versions': 0,
                            'stable_versions': 0,
                            'total_reviewer_comments': 0,
                            'total_approver_comments': 0,
                            'total_resolved_conversations': 0,
                            'total_unresolved_conversations': 0,
                            'breaking_change_prs': 0,
                            'first_commit_date': None,
                            'last_commit_date': None,
                            'active_days': 0,
                            'avg_commits_per_day': 0
                        }
                    
                    # Update contributor metrics
                    stats = contributors[author]
                    stats['total_prs'] += 1
                    stats['passed_checks'] += pr['passed_checks']
                    stats['failed_checks'] += pr['failed_checks']
                    stats['rc_versions'] += pr['rc_versions']
                    stats['npd_versions'] += pr['npd_versions']
                    stats['stable_versions'] += pr['stable_versions']
                    stats['total_reviewer_comments'] += pr.get('total_reviewer_comments', 0)
                    stats['total_approver_comments'] += pr.get('total_approver_comments', 0)
                    stats['total_resolved_conversations'] += pr.get('total_resolved_conversations', 0)
                    stats['total_unresolved_conversations'] += pr.get('total_unresolved_conversations', 0)
                    
                    # Update PR health counts
                    if pr['pr_health'] == 'Needs Attention':
                        stats['unhealthy_prs'] += 1
                    else:
                        stats['healthy_prs'] += 1
                    
                    # Track breaking change PRs
                    if pr.get('is_breaking_change', False):
                        stats['breaking_change_prs'] += 1
                    
                    # Process commit dates to calculate active days
                    for commit in pr['commits']:
                        if commit.get('date'):
                            commit_date = datetime.strptime(commit['date'], '%Y-%m-%dT%H:%M:%SZ')
                            commit_date = self.utc.localize(commit_date)
                            
                            if author not in contributor_first_date or commit_date < contributor_first_date[author]:
                                contributor_first_date[author] = commit_date
                                
                            if author not in contributor_last_date or commit_date > contributor_last_date[author]:
                                contributor_last_date[author] = commit_date
                                
                    # Update commit count
                    stats['total_commits'] += pr['commit_count']
                
                # Calculate active days and average commits per day
                for author, stats in contributors.items():
                    if author in contributor_first_date and author in contributor_last_date:
                        first_date = contributor_first_date[author]
                        last_date = contributor_last_date[author]
                        
                        # Calculate active days (minimum 1 day)
                        active_days = max(1, (last_date - first_date).days + 1)
                        stats['active_days'] = active_days
                        stats['avg_commits_per_day'] = round(stats['total_commits'] / active_days, 2)
                        
                        stats['first_commit_date'] = first_date.strftime('%Y-%m-%d')
                        stats['last_commit_date'] = last_date.strftime('%Y-%m-%d')
                    
                    contributor_data.append(stats)
                    
                    # Update all-repo contributor tracking
                    if author not in all_contributors_data:
                        all_contributors_data[author] = {
                            'contributor': author,
                            'repositories': set(),
                            'total_commits': 0,
                            'total_prs': 0,
                            'healthy_prs': 0,
                            'unhealthy_prs': 0,
                            'passed_checks': 0,
                            'failed_checks': 0,
                            'rc_versions': 0,
                            'npd_versions': 0,
                            'stable_versions': 0,
                            'total_reviewer_comments': 0,
                            'total_approver_comments': 0,
                            'total_resolved_conversations': 0,
                            'total_unresolved_conversations': 0,
                            'breaking_change_prs': 0
                        }
                    
                    all_contributors_data[author]['repositories'].add(repo)
                    all_contributors_data[author]['total_commits'] += stats['total_commits']
                    all_contributors_data[author]['total_prs'] += stats['total_prs']
                    all_contributors_data[author]['healthy_prs'] += stats['healthy_prs']
                    all_contributors_data[author]['unhealthy_prs'] += stats['unhealthy_prs']
                    all_contributors_data[author]['passed_checks'] += stats['passed_checks']
                    all_contributors_data[author]['failed_checks'] += stats['failed_checks']
                    all_contributors_data[author]['rc_versions'] += stats['rc_versions']
                    all_contributors_data[author]['npd_versions'] += stats['npd_versions']
                    all_contributors_data[author]['stable_versions'] += stats['stable_versions']
                    all_contributors_data[author]['total_reviewer_comments'] += stats['total_reviewer_comments']
                    all_contributors_data[author]['total_approver_comments'] += stats['total_approver_comments']
                    all_contributors_data[author]['total_resolved_conversations'] += stats['total_resolved_conversations']
                    all_contributors_data[author]['total_unresolved_conversations'] += stats['total_unresolved_conversations']
                    all_contributors_data[author]['breaking_change_prs'] += stats['breaking_change_prs']
            
            # Fetch additional contributors who made commits in PRs outside the date range
            if headers and start_date and end_date:
                for repo in all_metrics:
                    # Extract org and repo name
                    org_name = repo.split('/')[0]
                    repo_name = repo.split('/')[1]
                    full_repo = f"{org_name}/{repo_name}"
                    
                    # Get additional contributor commits
                    repo_contributors = self.fetch_additional_contributor_commits(headers, full_repo, start_date, end_date)
                    
                    # Process each additional contributor
                    for author, stats in repo_contributors.items():
                        # Skip if already tracked from PRs in date range
                        if author in all_contributors_data:
                            # Update commit count if needed - only add new commits not already counted
                            # We assume PRs in date range already counted these commits
                            continue
                            
                        # New contributor - add to tracking
                        if author not in all_contributors_data:
                            all_contributors_data[author] = {
                                'contributor': author,
                                'repositories': set([full_repo]),
                                'total_commits': stats['total_commits'],
                                'total_prs': 0,  # No PRs in date range
                                'healthy_prs': 0,
                                'unhealthy_prs': 0,
                                'passed_checks': 0,
                                'failed_checks': 0,
                                'rc_versions': 0,
                                'npd_versions': 0,
                                'stable_versions': 0,
                                'total_reviewer_comments': 0,
                                'total_approver_comments': 0,
                                'total_resolved_conversations': 0,
                                'total_unresolved_conversations': 0,
                                'breaking_change_prs': 0
                            }
                            
                            # Add to individual repository stats
                            contributor_data.append({
                                'repository': full_repo,
                                'contributor': author,
                                'total_commits': stats['total_commits'],
                                'total_prs': 0,
                                'healthy_prs': 0,
                                'unhealthy_prs': 0,
                                'passed_checks': 0,
                                'failed_checks': 0,
                                'rc_versions': 0,
                                'npd_versions': 0,
                                'stable_versions': 0,
                                'total_reviewer_comments': 0,
                                'total_approver_comments': 0,
                                'total_resolved_conversations': 0,
                                'total_unresolved_conversations': 0,
                                'breaking_change_prs': 0,
                                'first_commit_date': None,  # We could improve this, but keeping simple for now
                                'last_commit_date': None,
                                'active_days': 0,
                                'avg_commits_per_day': 0
                            })
                            
                            # Add to complete set of all contributors
                            all_contributors.add(author)
            
            # Add contributors who have no activity in this period
            if all_contributors:
                # Get list of contributors already processed
                processed_contributors = [data.get('contributor') for data in contributor_data]
                
                # Add entries for contributors with no activity
                for contributor in all_contributors:
                    if contributor not in processed_contributors:
                        self.logger.info(f"Adding contributor with no activity: {contributor}")
                        contributor_data.append({
                            'repository': 'N/A',
                            'contributor': contributor,
                            'total_commits': 0,
                            'total_prs': 0,
                            'healthy_prs': 0,
                            'unhealthy_prs': 0,
                            'passed_checks': 0,
                            'failed_checks': 0,
                            'rc_versions': 0,
                            'npd_versions': 0,
                            'stable_versions': 0,
                            'total_reviewer_comments': 0,
                            'total_approver_comments': 0,
                            'total_resolved_conversations': 0,
                            'total_unresolved_conversations': 0,
                            'breaking_change_prs': 0,
                            'first_commit_date': None,
                            'last_commit_date': None,
                            'active_days': 0,
                            'avg_commits_per_day': 0
                        })
                        
                        # Add to all contributors tracking if not already there
                        if contributor not in all_contributors_data:
                            all_contributors_data[contributor] = {
                                'contributor': contributor,
                                'repositories': set(),
                                'total_commits': 0,
                                'total_prs': 0,
                                'healthy_prs': 0,
                                'unhealthy_prs': 0,
                                'passed_checks': 0,
                                'failed_checks': 0,
                                'rc_versions': 0,
                                'npd_versions': 0,
                                'stable_versions': 0,
                                'total_reviewer_comments': 0,
                                'total_approver_comments': 0,
                                'total_resolved_conversations': 0,
                                'total_unresolved_conversations': 0,
                                'breaking_change_prs': 0
                            }
            
            # Create summary data
            for author, stats in all_contributors_data.items():
                summary_data.append({
                    'Contributor': author,
                    'Repositories': len(stats['repositories']),
                    'Repository List': ', '.join(list(stats['repositories'])[:3]) + ('...' if len(stats['repositories']) > 3 else ''),
                    'Total Commits': stats['total_commits'],
                    'Total PRs': stats['total_prs'],
                    'Healthy PRs': stats['healthy_prs'],
                    'Unhealthy PRs': stats['unhealthy_prs'],
                    'Health Ratio': f"{stats['healthy_prs']}/{stats['total_prs']}",
                    'Health Percentage': round((stats['healthy_prs'] / stats['total_prs']) * 100, 1) if stats['total_prs'] > 0 else 0,
                    'RC Versions': stats['rc_versions'],
                    'NPD Versions': stats['npd_versions'],
                    'Stable Versions': stats['stable_versions'],
                    'Total Reviewer Comments': stats['total_reviewer_comments'],
                    'Total Approver Comments': stats['total_approver_comments'],
                    'Total Resolved Conversations': stats['total_resolved_conversations'],
                    'Total Unresolved Conversations': stats['total_unresolved_conversations'],
                    'Breaking Change PRs': stats['breaking_change_prs'],
                    'Passed Checks': stats['passed_checks'],
                    'Failed Checks': stats['failed_checks'],
                    'Check Success Rate': round((stats['passed_checks'] / (stats['passed_checks'] + stats['failed_checks'])) * 100, 1) if (stats['passed_checks'] + stats['failed_checks']) > 0 else 'N/A'
                })

            # Create DataFrames
            df = pd.DataFrame(contributor_data)
            summary_df = pd.DataFrame(summary_data)
            
            output_file = f"{output_dir}/contributor_report.xlsx"
            
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                # Write detailed contributor data
                df.to_excel(writer, sheet_name='Contributor Metrics', index=False)
                self._format_excel_sheet(writer.sheets['Contributor Metrics'], df, writer.book)
                
                # Write summary data
                summary_df.to_excel(writer, sheet_name='Contributor Summary', index=False)
                self._format_summary_sheet(writer.sheets['Contributor Summary'], summary_df, writer.book)
            
            self.logger.info(f"Saved contributor report: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error generating contributor report: {str(e)}")

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
            
            # Fix: Use proper non-percentage format for percentages calculated in Python
            percentage_format = workbook.add_format({
                'num_format': '#,##0.0',  # Removed % sign to avoid double-formatting
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
                elif col in ['Days Open', 'Avg Days to Merge', 'PR Days Open', 'Avg Commits Per Day', 'Active Days']:
                    worksheet.set_column(idx, idx, max(8, max_len), decimal_format)
                elif 'Percentage' in col or 'Rate' in col:
                    worksheet.set_column(idx, idx, max(8, max_len), percentage_format)
                elif any(word in col for word in ['Count', 'Added', 'Deleted', 'Number', 'Total', 'PRs', 'Lines', 'Requests', 'Changes', 'Commits', 'Checks', 'Versions', 'Comments', 'Conversations']):
                    worksheet.set_column(idx, idx, max(8, max_len), number_format)
                elif col in ['Title', 'Commit Message', 'Labels', 'Approver Comments', 'Changed Files', 'Health Reasons']:
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
                elif col in ['Has Examples', 'Has Tests', 'Has Integration Tests', 'Is Breaking Change', 'Is Feature/Fix PR']:
                    worksheet.set_column(idx, idx, max(18, max_len))
                    # Add conditional formatting for Yes/No/N/A values
                    worksheet.conditional_format(1, idx, len(dataframe) + 1, idx, {
                        'type': 'cell',
                        'criteria': 'equal to',
                        'value': '"Yes"',
                        'format': health_format_good if not col == 'Is Breaking Change' else health_format_bad
                    })
                    worksheet.conditional_format(1, idx, len(dataframe) + 1, idx, {
                        'type': 'cell',
                        'criteria': 'equal to',
                        'value': '"No"',
                        'format': health_format_bad if not col == 'Is Breaking Change' else health_format_good
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

    def _format_summary_sheet(self, worksheet, dataframe, workbook):
        """Apply formatting to summary sheets with enhanced data visualization."""
        try:
            # Define standard formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',  # Blue header
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True
            })
            
            number_format = workbook.add_format({
                'num_format': '#,##0',
                'align': 'right'
            })
            
            # Fix: Use proper non-percentage format for percentages calculated in Python
            percentage_format = workbook.add_format({
                'num_format': '#,##0.0',  # Removed % sign to avoid double-formatting
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
            
            # Highlight formats for health indicators
            high_health = workbook.add_format({
                'bg_color': '#C6EFCE',  # Light green
                'font_color': '#006100'  # Dark green
            })
            
            medium_health = workbook.add_format({
                'bg_color': '#FFEB9C',  # Light yellow
                'font_color': '#9C5700'  # Dark orange
            })
            
            low_health = workbook.add_format({
                'bg_color': '#FFC7CE',  # Light red
                'font_color': '#9C0006'  # Dark red
            })
            
            # Format for stable/no dev repositories
            stable_no_dev_format = workbook.add_format({
                'bg_color': '#E0E0E0',  # Light gray
                'font_color': '#666666'  # Dark gray
            })
            
            # Format columns based on content type
            for idx, col in enumerate(dataframe.columns):
                max_len = max(
                    dataframe[col].astype(str).apply(len).max(),
                    len(str(col))
                ) + 2
                
                if 'Percentage' in col or 'Rate' in col:
                    worksheet.set_column(idx, idx, max(10, max_len), percentage_format)
                    
                    # Add conditional formatting for health percentages
                    if 'Health Percentage' in col:
                        # Add formatting for repositories with PRs
                        worksheet.conditional_format(1, idx, len(dataframe) + 1, idx, {
                            'type': 'cell',
                            'criteria': 'greater than or equal to',
                            'value': 80,
                            'format': high_health
                        })
                        worksheet.conditional_format(1, idx, len(dataframe) + 1, idx, {
                            'type': 'cell',
                            'criteria': 'less than',
                            'value': 80,
                            'format': medium_health
                        })
                        worksheet.conditional_format(1, idx, len(dataframe) + 1, idx, {
                            'type': 'cell',
                            'criteria': 'less than',
                            'value': 50,
                            'format': low_health
                        })
                
                elif any(word in col for word in ['Total', 'Count', 'PRs', 'Checks', 'Commits', 'Repositories', 'Versions', 'Comments', 'Conversations']):
                    worksheet.set_column(idx, idx, max(8, max_len), number_format)
                
                elif 'Repository' in col or 'Contributor' in col:
                    worksheet.set_column(idx, idx, max(20, max_len), text_format)
                
                elif 'List' in col:
                    worksheet.set_column(idx, idx, min(50, max_len), text_format)
                
                elif 'Duration' in col:
                    worksheet.set_column(idx, idx, max(12, max_len), decimal_format)
                    
                else:
                    worksheet.set_column(idx, idx, min(30, max_len), text_format)
                
                worksheet.write(0, idx, col, header_format)
            
            # Add conditional formatting for Status column (Stable/No Dev)
            if 'Status' in dataframe.columns:
                status_idx = dataframe.columns.get_loc('Status')
                worksheet.conditional_format(1, status_idx, len(dataframe) + 1, status_idx, {
                    'type': 'cell',
                    'criteria': 'equal to',
                    'value': '"Stable/No Dev"',
                    'format': stable_no_dev_format
                })
            
            # Add alternating row colors
            for row in range(1, len(dataframe) + 1):
                if row % 2 == 0:
                    bg_format = workbook.add_format({'bg_color': '#EDF3FE'})  # Light blue for summary
                    worksheet.set_row(row, None, bg_format)
            
            # Freeze header row and left column
            worksheet.freeze_panes(1, 1)
                
        except Exception as e:
            self.logger.error(f"Error formatting summary sheet: {str(e)}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='GitHub Repository Metrics Generator')
    parser.add_argument('--org', required=True, help='GitHub organization/owner name')
    parser.add_argument('--start-date', required=True, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', required=True, help='End date in YYYY-MM-DD format')
    parser.add_argument('--repos-file', help='Path to file containing repository names (optional)')
    parser.add_argument('--token-file', help='Path to file containing GitHub token (optional)')
    parser.add_argument('--output-dir', help='Custom output directory path')
    parser.add_argument('--pr-threshold', type=int, default=7, help='PR health threshold in days (default: 7)')
    parser.add_argument('--label-threshold', type=int, default=2, help='Maximum labels threshold (default: 2)')
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
        
        # Set label threshold from command line if provided
        if args.label_threshold:
            reporter.max_labels_threshold = args.label_threshold
            reporter.logger.info(f"Label threshold set to {reporter.max_labels_threshold}")
        
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
        # Track all repositories for reporting
        all_repositories = [f"{args.org}/{repo}" for repo in repositories]
        # Track all contributors
        all_contributors = set()
        
        for i, repo in enumerate(repositories, 1):
            try:
                full_repo = f"{args.org}/{repo}"
                reporter.logger.info(f"Processing [{i}/{len(repositories)}]: {repo}")
                
                metrics = reporter.fetch_pr_data(headers, full_repo, start_date, end_date)
                if metrics:
                    all_metrics[full_repo] = metrics
                    healthy = metrics['stats']['healthy_prs']
                    unhealthy = metrics['stats']['unhealthy_prs']
                    unhealthy_duration = metrics['stats']['unhealthy_due_to_duration']
                    unhealthy_labels = metrics['stats']['unhealthy_due_to_labels']
                    passed_checks = metrics['stats']['total_passed_checks']
                    failed_checks = metrics['stats']['total_failed_checks']
                    rc_versions = metrics['stats']['total_rc_versions']
                    npd_versions = metrics['stats']['total_npd_versions']
                    stable_versions = metrics['stats']['total_stable_versions']
                    
                    # Collect all contributors from this repo
                    for pr in metrics.get('pull_requests', []):
                        all_contributors.add(pr['author'])
                    
                    reporter.logger.info(
                        f"Found {metrics['stats']['total_prs']} PRs for {repo}: "
                        f"{healthy} healthy, {unhealthy} needs attention "
                        f"({unhealthy_duration} duration, {unhealthy_labels} labels) "
                        f"with {passed_checks} passed checks, {failed_checks} failed checks, "
                        f"{rc_versions} RC versions, {npd_versions} NPD versions, {stable_versions} Stable versions"
                    )
                
            except Exception as e:
                reporter.logger.error(f"Error processing {repo}: {str(e)}")
                continue
                
        # Generate reports
        if all_metrics:
            reporter.generate_pr_activity_report(all_metrics, output_dir, all_repositories)
            reporter.generate_contributor_report(all_metrics, output_dir, list(all_contributors), headers, start_date, end_date)
            reporter.logger.info(f"✓ All reports saved to: {output_dir}")
            
            # Print summary for CI/CD logs
            total_repos = len(all_metrics)
            repos_without_prs = len(all_repositories) - total_repos
            total_prs = sum(metrics['stats']['total_prs'] for metrics in all_metrics.values())
            healthy_prs = sum(metrics['stats']['healthy_prs'] for metrics in all_metrics.values())
            unhealthy_prs = sum(metrics['stats']['unhealthy_prs'] for metrics in all_metrics.values())
            unhealthy_duration = sum(metrics['stats']['unhealthy_due_to_duration'] for metrics in all_metrics.values())
            unhealthy_labels = sum(metrics['stats']['unhealthy_due_to_labels'] for metrics in all_metrics.values())
            total_passed_checks = sum(metrics['stats']['total_passed_checks'] for metrics in all_metrics.values())
            total_failed_checks = sum(metrics['stats']['total_failed_checks'] for metrics in all_metrics.values())
            total_rc_versions = sum(metrics['stats']['total_rc_versions'] for metrics in all_metrics.values())
            total_npd_versions = sum(metrics['stats']['total_npd_versions'] for metrics in all_metrics.values())
            total_stable_versions = sum(metrics['stats']['total_stable_versions'] for metrics in all_metrics.values())
            
            print(f"\nSummary: Processed {total_repos} active repositories, {repos_without_prs} stable/no-dev repositories")
            print(f"PR Stats: {total_prs} total PRs, {healthy_prs} healthy, {unhealthy_prs} needs attention")
            print(f"Needs Attention Breakdown: {unhealthy_duration} due to duration, {unhealthy_labels} due to label count")
            print(f"Check Status: {total_passed_checks} passed checks, {total_failed_checks} failed checks")
            print(f"Version Types: {total_rc_versions} RC, {total_npd_versions} NPD, {total_stable_versions} Stable")
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