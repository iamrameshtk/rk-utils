import pandas as pd
import os
from typing import Dict, List

class ContributorReportGenerator:
    """Generates contributor metrics reports."""
    
    def __init__(self, logger):
        """Initialize the report generator."""
        self.logger = logger
    
    def generate_report(self, all_metrics, output_dir):
        """Generate consolidated contributor metrics report with enhanced health metrics."""
        try:
            self.logger.info("Generating contributor report")
            
            # Import the Excel formatting utility
            from utils.excel_utils import format_excel_sheet
            
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
                    stats['change_requests_received'] += pr.get('change_request_count', 0)
                    
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
            
            if not contributor_data:
                self.logger.warning("No contributor data to report")
                return pd.DataFrame()
                
            df = pd.DataFrame(contributor_data)
            
            output_file = os.path.join(output_dir, "contributor_report.xlsx")
            
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Contributor Metrics', index=False)
                format_excel_sheet(writer.sheets['Contributor Metrics'], df, writer.book)
            
            self.logger.info(f"Saved contributor report: {output_file}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error generating contributor report: {str(e)}")
            return pd.DataFrame()