# dashboard/dashboard_generator.py
import os
import pickle

class DashboardGenerator:
    """Generates Streamlit dashboard scripts and data files."""
    
    def __init__(self, logger):
        """Initialize the dashboard generator."""
        self.logger = logger
    
    def generate_dashboard(self, output_dir, activity_df, contributor_df, commit_df, summary_metrics, pr_threshold_days):
        """
        Generate a Streamlit dashboard for the collected metrics.
        
        Args:
            output_dir (str): Output directory for dashboard files
            activity_df (DataFrame): PR activity data
            contributor_df (DataFrame): Contributor data
            commit_df (DataFrame): Commit data
            summary_metrics (dict): Summary metrics
            pr_threshold_days (int): PR health threshold in days
        """
        try:
            self.logger.info("Generating Streamlit dashboard data")
            
            # Add date range to summary metrics
            if 'pr_by_date' in summary_metrics and summary_metrics['pr_by_date']:
                dates = list(summary_metrics['pr_by_date'].keys())
                if dates:
                    summary_metrics['date_range'] = f"{min(dates)} to {max(dates)}"
            
            # Create serializable data dictionary with explicit copies
            serializable_data = {
                'activity_df': activity_df.copy() if activity_df is not None else None,
                'contributor_df': contributor_df.copy() if contributor_df is not None else None,
                'commit_df': commit_df.copy() if commit_df is not None else None,
                'summary_metrics': summary_metrics.copy() if summary_metrics is not None else {},
                'pr_threshold_days': pr_threshold_days
            }
            
            # Serialize the data dictionary with absolute path
            pkl_path = os.path.join(os.path.abspath(output_dir), "report_data.pkl")
            with open(pkl_path, 'wb') as f:
                pickle.dump(serializable_data, f)
            
            self.logger.info(f"Dashboard data saved to: {pkl_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard data: {str(e)}")
            return False