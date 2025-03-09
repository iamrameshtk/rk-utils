import pandas as pd
import os
from typing import Dict, List

class ActivityReportGenerator:
    """Generates PR activity reports."""
    
    def __init__(self, logger, pr_threshold_days):
        """Initialize the report generator."""
        self.logger = logger
        self.pr_threshold_days = pr_threshold_days
    
    def generate_report(self, all_metrics, output_dir):
        """Generate enhanced PR activity report with file changes and reviewer metrics."""
        try:
            self.logger.info("Generating PR activity report")
            
            # Import the Excel formatting utility
            from utils.excel_utils import format_excel_sheet
            
            activity_data = []
            for repo, metrics in all_metrics.items():
                for pr in metrics['pull_requests']:
                    # Create enhanced record with new metrics
                    record = self.create_record(repo, pr)
                    activity_data.append(record)
            
            if not activity_data:
                self.logger.warning("No activity data to report")
                return pd.DataFrame()
            
            df = pd.DataFrame(activity_data)
            
            # Apply conditional formatting for PR health
            df['PR Health'] = df['PR Health'].apply(lambda x: f"❌ {x}" if x == 'Unhealthy' else f"✅ {x}")
            
            output_file = os.path.join(output_dir, "pr_activity_report.xlsx")
            
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='PR Activity', index=False)
                format_excel_sheet(writer.sheets['PR Activity'], df, writer.book)
            
            self.logger.info(f"Saved PR activity report: {output_file}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error generating activity report: {str(e)}")
            return pd.DataFrame()
    
    def create_record(self, repo, pr):
        """Create a record for the activity report from a PR."""
        return {
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
            'Approver': pr.get('approver', ''),
            'Approver Teams': ', '.join(pr.get('approver_teams', [])),
            'Approver Comment': pr.get('approver_comment', '')[:100] + '...' if len(pr.get('approver_comment', '')) > 100 else pr.get('approver_comment', ''),
            'Change Requests': pr.get('change_request_count', 0),
            'Changes Status': pr.get('change_request_status', ''),
            'Pending Changes': pr.get('pending_changes', 0),
            'Resolved Changes': pr.get('resolved_changes', 0),
            'Files Changed': pr['file_count'],
            'Lines Added': pr['additions'],
            'Lines Deleted': pr['deletions'],
            'Changed Files': ', '.join(pr['file_list'][:5]) + ('...' if len(pr['file_list']) > 5 else ''),
            'Labels': ', '.join(pr['labels']),
            'Commit Count': len(pr['commits'])
        }