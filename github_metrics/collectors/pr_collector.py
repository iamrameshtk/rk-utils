import requests
from datetime import datetime
import pytz
from typing import Dict, List, Optional, Any

class PRCollector:
    """Collects pull request data from GitHub API."""
    
    def __init__(self, headers, logger, base_url, pr_threshold_days):
        """Initialize the collector with required configuration."""
        self.headers = headers
        self.logger = logger
        self.base_url = base_url
        self.pr_threshold_days = pr_threshold_days
        self.utc = pytz.UTC
    
    def fetch_pr_data(self, repo, start_date, end_date, review_collector, commit_collector):
        """
        Fetch enhanced pull request data.
        
        Args:
            repo (str): Repository name in format 'owner/repo'
            start_date (datetime): Start date for PRs
            end_date (datetime): End date for PRs
            review_collector (ReviewCollector): Collector for PR reviews
            commit_collector (CommitCollector): Collector for PR commits
            
        Returns:
            dict: Repository metrics with pull request data
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
                    headers=self.headers,
                    params={
                        'state': 'all',
                        'sort': 'created',
                        'direction': 'desc',
                        'per_page': 100,
                        'page': page
                    }
                )
                
                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch PRs for {repo}: {response.status_code}")
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
                            # Process PR details
                            pr_data = self.process_pr(pr, repo, org_name, review_collector, commit_collector)
                            
                            if pr_data:
                                # Update repository statistics
                                metrics['stats']['total_prs'] += 1
                                metrics['stats']['total_additions'] += pr_data['additions']
                                metrics['stats']['total_deletions'] += pr_data['deletions']
                                metrics['stats']['total_change_requests'] += pr_data['change_request_count']
                                
                                if pr_data['pr_health'] == 'Healthy':
                                    metrics['stats']['healthy_prs'] += 1
                                else:
                                    metrics['stats']['unhealthy_prs'] += 1
                                    
                                if pr_data['merged_at']:
                                    metrics['stats']['merged_prs'] += 1
                                
                                # Add to pull requests list
                                metrics['pull_requests'].append(pr_data)
                            
                    except Exception as e:
                        self.logger.error(f"Error processing PR #{pr.get('number', 'unknown')}: {str(e)}")
                
                page += 1
            
            self.logger.info(f"Collected {metrics['stats']['total_prs']} PRs for {repo}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error fetching PR data for {repo}: {str(e)}")
            return None
    
    def get_pr_details(self, repo, pr_number):
        """
        Fetch detailed information about a specific PR.
        """
        try:
            response = requests.get(
                f'{self.base_url}/repos/{repo}/pulls/{pr_number}',
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to fetch PR details for {repo}#{pr_number}: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error fetching PR details for {repo}#{pr_number}: {str(e)}")
            return {}
    
    def process_pr(self, pr, repo, org_name, review_collector, commit_collector):
        """Process a PR to extract all necessary data."""
        try:
            # Extract basic PR info
            pr_number = pr['number']
            title = pr['title']
            author = pr['user']['login']
            state = pr['state']
            
            # Get creation date
            created_at = datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            created_at = self.utc.localize(created_at)
            
            # Process merged date if available
            merged_at = None
            if pr['merged_at']:
                merged_at = datetime.strptime(pr['merged_at'], '%Y-%m-%dT%H:%M:%SZ')
                merged_at = self.utc.localize(merged_at)
            
            # Get target branch from PR details
            pr_details = self.get_pr_details(repo, pr_number)
            target_branch = pr_details.get('base', {}).get('ref', '') if pr_details else ''
            
            # Calculate PR duration
            pr_duration_days = 0
            if pr['state'] == 'closed' and pr['closed_at']:
                closed_at = datetime.strptime(pr['closed_at'], '%Y-%m-%dT%H:%M:%SZ')
                closed_at = self.utc.localize(closed_at)
                pr_duration_days = (closed_at - created_at).days
            else:
                # For open PRs, calculate days open so far
                pr_duration_days = (datetime.now(self.utc) - created_at).days
            
            # Determine PR health based on duration
            pr_health = 'Healthy'
            if pr_duration_days > self.pr_threshold_days:
                pr_health = 'Unhealthy'
            
            # Get PR reviews
            reviews = review_collector.get_pr_reviews(repo, pr_number)
            
            # Get review analysis
            review_analysis = review_collector.analyze_reviews(reviews, pr, org_name)
            
            # Get PR file changes
            file_data = review_collector.get_pr_files(repo, pr_number)
            
            # Get PR commits
            commits = commit_collector.get_pr_commits(pr['commits_url'])
            
            # Compile the PR data
            pr_data = {
                'number': pr_number,
                'title': title,
                'author': author,
                'state': state,
                'created_at': created_at,
                'merged_at': merged_at,
                'target_branch': target_branch,
                'pr_duration_days': pr_duration_days,
                'pr_health': pr_health,
                'file_count': file_data['file_count'],
                'file_list': file_data['file_list'],
                'additions': file_data['additions'],
                'deletions': file_data['deletions'],
                'commits': commits,
                'reviews': reviews,
                'labels': [label['name'] for label in pr.get('labels', [])]
            }
            
            # Add review analysis data
            pr_data.update(review_analysis)
            
            return pr_data
            
        except Exception as e:
            self.logger.error(f"Error processing PR #{pr.get('number', 'unknown')}: {str(e)}")
            return None