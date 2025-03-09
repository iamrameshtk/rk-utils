import requests
from datetime import datetime

class ReviewCollector:
    """Collects review data for pull requests."""
    
    def __init__(self, headers, logger, base_url):
        """Initialize the review collector."""
        self.headers = headers
        self.logger = logger
        self.base_url = base_url
    
    def get_pr_reviews(self, repo, pr_number):
        """Fetch reviews for a pull request."""
        try:
            response = requests.get(
                f"{self.base_url}/repos/{repo}/pulls/{pr_number}/reviews",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to fetch reviews for {repo}#{pr_number}: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching reviews for {repo}#{pr_number}: {str(e)}")
            return []
    
    def get_pr_files(self, repo, pr_number):
        """Fetch the list of files changed in a PR with line addition/deletion stats."""
        try:
            files = []
            page = 1
            total_additions = 0
            total_deletions = 0
            
            while True:
                response = requests.get(
                    f'{self.base_url}/repos/{repo}/pulls/{pr_number}/files',
                    headers=self.headers,
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
    
    def get_org_membership(self, org, username):
        """Check if a user is a member of an organization and get their team memberships."""
        try:
            membership_response = requests.get(
                f'{self.base_url}/orgs/{org}/memberships/{username}',
                headers=self.headers
            )
            
            if membership_response.status_code == 200:
                # Get teams
                teams_response = requests.get(
                    f'{self.base_url}/orgs/{org}/teams',
                    headers=self.headers
                )
                
                if teams_response.status_code == 200:
                    teams = teams_response.json()
                    user_teams = []
                    
                    for team in teams:
                        team_membership_response = requests.get(
                            f'{self.base_url}/teams/{team["id"]}/memberships/{username}',
                            headers=self.headers
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
    
    def analyze_reviews(self, reviews, pr, org_name):
        """Analyze PR reviews to extract approvers, comments, and change requests."""
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
                    membership = self.get_org_membership(org_name, approver)
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
            if pr['state'] == 'closed' and pr.get('merged_at'):
                change_request_status = "All changes resolved"
                resolved_changes = change_request_count
            else:
                # Check if there's a later approval
                if change_requests and all(cr.get('submitted_at') for cr in change_requests):
                    last_change_request = max([datetime.strptime(cr['submitted_at'], '%Y-%m-%dT%H:%M:%SZ') 
                                          for cr in change_requests])
                    
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
        
        return {
            'approver': approver,
            'approver_comment': approver_comment,
            'approver_teams': approver_teams,
            'change_request_count': change_request_count,
            'pending_changes': pending_changes,
            'resolved_changes': resolved_changes,
            'change_request_status': change_request_status
        }