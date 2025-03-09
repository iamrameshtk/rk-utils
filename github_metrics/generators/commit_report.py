import pandas as pd
import os
from typing import Dict, List
from datetime import datetime

class CommitReportGenerator:
    """Generates commit detail reports."""
    
    def __init__(self, logger, pr_threshold_days):
        """Initialize the report generator."""
        self.logger = logger
        self.pr_threshold_days = pr_threshold_days
    
    def generate_report(self, all_metrics, output_dir):
        """Generate consolidated commit details report with merge dates and correct health status."""
        try:
            self.logger.info("Generating commit report")
            
            # Import the Excel formatting utility
            from utils.excel_utils import format_excel_sheet
            
            commit_data = []
            for repo, metrics in all_metrics.items():
                for pr in metrics['pull_requests']:
                    # Use the already calculated health status directly
                    pr_health = pr['pr_health']
                    
                    for commit in pr['commits']:
                        try:
                            commit_date = datetime.strptime(commit.get('date', ''), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
                        except:
                            commit_date = ''
                            
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
                            'Commit Date': commit_date,
                            'PR Status': pr['state'].capitalize(),
                            'Merged Date': pr['merged_at'].strftime('%Y-%m-%d') if pr['merged_at'] else '',
                            'Files Changed': pr['file_count'],
                            'Lines Added': pr['additions'],
                            'Lines Deleted': pr['deletions'],
                            'Change Requests': pr.get('change_request_count', 0)
                        }
                        commit_data.append(record)
            
            if not commit_data:
                self.logger.warning("No commit data to report")
                return pd.DataFrame()
                
            df = pd.DataFrame(commit_data)
            
            # Apply conditional formatting for PR health
            df['PR Health'] = df['PR Health'].apply(lambda x: f"❌ {x}" if x == 'Unhealthy' else f"✅ {x}")
            
            output_file = os.path.join(output_dir, "commit_report.xlsx")
            
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Commit Details', index=False)
                format_excel_sheet(writer.sheets['Commit Details'], df, writer.book)
            
            self.logger.info(f"Saved commit report: {output_file}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error generating commit report: {str(e)}")
            return pd.DataFrame()