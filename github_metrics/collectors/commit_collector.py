import requests

class CommitCollector:
    """Collects commit data for pull requests."""
    
    def __init__(self, headers, logger):
        """Initialize the commit collector."""
        self.headers = headers
        self.logger = logger
    
    def get_pr_commits(self, commits_url):
        """Fetch commits for a pull request."""
        try:
            response = requests.get(
                commits_url,
                headers=self.headers
            )
            
            if response.status_code == 200:
                return self.process_commits(response.json())
            else:
                self.logger.error(f"Failed to fetch commits: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching commits: {str(e)}")
            return []
    
    def process_commits(self, commits):
        """Process commit data from the API response."""
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
        
        return commit_data