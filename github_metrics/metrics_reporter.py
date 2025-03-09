import logging
import os
import pytz
from datetime import datetime
import pandas as pd
import pickle
import sys

class GitHubMetricsReporter:
    """
    Core GitHub metrics reporting class that orchestrates data collection and report generation.
    """
    
    def __init__(self):
        """Initialize reporter with configuration and logging setup."""
        self.base_url = 'https://api.github.com'
        self.utc = pytz.UTC
        self.api_calls = 0
        self.start_time = datetime.now(self.utc)
        self.pr_threshold_days = 2
        self._setup_logging()
        self.logger.info("GitHub Metrics Reporter initialized")
        
        # Storage for dataframes
        self.activity_df = None
        self.contributor_df = None
        self.commit_df = None
        self.summary_metrics = None

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

    def run(self, org_name, repositories, start_date, end_date, token_file, output_dir, streamlit=False):
        """
        Execute the full reporting workflow.
        
        Args:
            org_name (str): GitHub organization name
            repositories (List[str]): List of repository names to analyze
            start_date (datetime): Start date for analysis
            end_date (datetime): End date for analysis
            token_file (str): Path to GitHub token file
            output_dir (str): Output directory for reports
            streamlit (bool): Whether to generate Streamlit dashboard
        """
        # Import necessary modules
        from utils.api_utils import validate_github_token
        from collectors.pr_collector import PRCollector
        from collectors.review_collector import ReviewCollector
        from collectors.commit_collector import CommitCollector
        from generators.activity_report import ActivityReportGenerator
        from generators.contributor_report import ContributorReportGenerator
        from generators.commit_report import CommitReportGenerator
        from generators.summary_metrics import calculate_summary_metrics
        
        # Validate token and get API headers
        headers = validate_github_token(token_file, self.logger)
        if not headers:
            self.logger.error("Failed to authenticate with GitHub.")
            return False
        
        # Create collectors
        pr_collector = PRCollector(headers, self.logger, self.base_url, self.pr_threshold_days)
        review_collector = ReviewCollector(headers, self.logger, self.base_url)
        commit_collector = CommitCollector(headers, self.logger)
        
        # Collect data
        all_metrics = {}
        for i, repo in enumerate(repositories, 1):
            try:
                full_repo = f"{org_name}/{repo}"
                self.logger.info(f"Processing [{i}/{len(repositories)}]: {repo}")
                
                # Get PR data including reviews and commits
                metrics = pr_collector.fetch_pr_data(full_repo, start_date, end_date, review_collector, commit_collector)
                
                if metrics and metrics.get('pull_requests'):
                    all_metrics[full_repo] = metrics
                    
                    # Log summary statistics
                    healthy = metrics['stats']['healthy_prs']
                    unhealthy = metrics['stats']['unhealthy_prs']
                    additions = metrics['stats']['total_additions']
                    deletions = metrics['stats']['total_deletions']
                    change_requests = metrics['stats']['total_change_requests']
                    
                    self.logger.info(
                        f"Found {metrics['stats']['total_prs']} PRs for {repo} "
                        f"({healthy} healthy, {unhealthy} unhealthy) "
                        f"with {change_requests} change requests, "
                        f"{additions} lines added and {deletions} lines deleted"
                    )
                else:
                    self.logger.warning(f"No PRs found for {repo} in the specified date range")
            except Exception as e:
                self.logger.error(f"Error processing {repo}: {str(e)}")
                continue
        
        if not all_metrics:
            self.logger.error("No metrics collected. Please check your date range and repositories.")
            return False
        
        # Create report generators
        activity_generator = ActivityReportGenerator(self.logger, self.pr_threshold_days)
        contributor_generator = ContributorReportGenerator(self.logger)
        commit_generator = CommitReportGenerator(self.logger, self.pr_threshold_days)
        
        # Generate reports
        self.activity_df = activity_generator.generate_report(all_metrics, output_dir)
        if self.activity_df is None or self.activity_df.empty:
            self.logger.error("Failed to generate PR activity report")
        else:
            self.logger.info(f"PR activity report generated with {len(self.activity_df)} records")
            
        self.contributor_df = contributor_generator.generate_report(all_metrics, output_dir)
        if self.contributor_df is None or self.contributor_df.empty:
            self.logger.error("Failed to generate contributor report")
        else:
            self.logger.info(f"Contributor report generated with {len(self.contributor_df)} records")
            
        self.commit_df = commit_generator.generate_report(all_metrics, output_dir)
        if self.commit_df is None or self.commit_df.empty:
            self.logger.error("Failed to generate commit report")
        else:
            self.logger.info(f"Commit report generated with {len(self.commit_df)} records")
        
        # Calculate summary metrics
        self.summary_metrics = calculate_summary_metrics(all_metrics, self.logger)
        
        # Generate Streamlit dashboard
        if streamlit:
            dashboard_path = self.create_dashboard(output_dir)
            if dashboard_path:
                self.logger.info(f"Dashboard created at: {dashboard_path}")
                self.logger.info(f"Run with: streamlit run {dashboard_path}")
            else:
                self.logger.error("Failed to create dashboard")
                
        return True
    
    def create_dashboard(self, output_dir):
        """Create the dashboard file and export data."""
        try:
            # Export data for dashboard
            data_path = os.path.join(output_dir, "report_data.pkl")
            
            # Create data dictionary
            data = {
                'activity_df': self.activity_df.copy() if isinstance(self.activity_df, pd.DataFrame) and not self.activity_df.empty else pd.DataFrame(),
                'contributor_df': self.contributor_df.copy() if isinstance(self.contributor_df, pd.DataFrame) and not self.contributor_df.empty else pd.DataFrame(),
                'commit_df': self.commit_df.copy() if isinstance(self.commit_df, pd.DataFrame) and not self.commit_df.empty else pd.DataFrame(),
                'summary_metrics': self.summary_metrics if self.summary_metrics else {},
                'pr_threshold_days': self.pr_threshold_days
            }
            
            # Export data
            with open(data_path, 'wb') as f:
                pickle.dump(data, f)
            
            # Create dashboard script
            dashboard_path = os.path.join(output_dir, "dashboard.py")
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write('''
import os
import sys
import pickle
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import base64
from datetime import datetime

# Utility functions
def generate_download_link(df, filename, text):
    """Generate a download link for a dataframe."""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'data:file/csv;base64,{b64}'
    return f'<a href="{href}" download="{filename}">{text}</a>'

# Main dashboard function
def main():
    # Configure page
    st.set_page_config(
        page_title="GitHub Metrics Dashboard", 
        page_icon=":bar_chart:", 
        layout="wide"
    )
    
    st.title("GitHub Metrics Dashboard")
    st.sidebar.title("Navigation")
    
    # Load data
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, "report_data.pkl")
        
        with open(data_path, 'rb') as f:
            data = pickle.load(f)
        
        activity_df = data.get('activity_df', pd.DataFrame())
        contributor_df = data.get('contributor_df', pd.DataFrame())
        commit_df = data.get('commit_df', pd.DataFrame())
        summary_metrics = data.get('summary_metrics', {})
        pr_threshold_days = data.get('pr_threshold_days', 2)
        
        # Create tabs
        tabs = st.tabs(["Summary", "PR Activity", "Contributors", "Commits"])
        
        # Summary tab
        with tabs[0]:
            st.header("GitHub Repository Metrics Summary")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total PRs", summary_metrics.get('total_prs', 0))
                st.metric("Repositories", summary_metrics.get('total_repos', 0))
            with col2:
                st.metric("Healthy PRs", summary_metrics.get('healthy_prs', 0))
                st.metric("Merged PRs", summary_metrics.get('merged_prs', 0))
            with col3:
                st.metric("Unhealthy PRs", summary_metrics.get('unhealthy_prs', 0))
                st.metric("Health Ratio", f"{summary_metrics.get('health_ratio', 0):.1f}%")
            with col4:
                st.metric("Avg PR Duration", f"{summary_metrics.get('avg_pr_duration', 0):.1f} days")
                st.metric("Change Requests", summary_metrics.get('total_change_requests', 0))
            
            # PR Timeline chart
            if 'pr_by_date' in summary_metrics and summary_metrics['pr_by_date']:
                st.subheader("PR Creation Timeline")
                date_df = pd.DataFrame({
                    'Date': list(summary_metrics['pr_by_date'].keys()),
                    'PRs Created': list(summary_metrics['pr_by_date'].values())
                })
                date_df['Date'] = pd.to_datetime(date_df['Date'])
                fig = px.line(date_df, x='Date', y='PRs Created', markers=True)
                st.plotly_chart(fig, use_container_width=True)
            
            # Repositories chart
            if 'pr_by_repo' in summary_metrics and summary_metrics['pr_by_repo']:
                st.subheader("PRs by Repository")
                repo_df = pd.DataFrame({
                    'Repository': list(summary_metrics['pr_by_repo'].keys()),
                    'PR Count': list(summary_metrics['pr_by_repo'].values())
                })
                repo_df = repo_df.sort_values('PR Count', ascending=False)
                fig = px.bar(repo_df, x='Repository', y='PR Count', color='PR Count',
                            color_continuous_scale=px.colors.sequential.Viridis)
                st.plotly_chart(fig, use_container_width=True)
        
        # PR Activity tab
        with tabs[1]:
            st.header("Pull Request Activity")
            
            if not activity_df.empty:
                # Filters
                col1, col2, col3 = st.columns(3)
                with col1:
                    repos = sorted(activity_df['Repository'].unique())
                    selected_repos = st.multiselect("Select Repositories", repos, default=repos[:min(3, len(repos))])
                
                with col2:
                    statuses = sorted(activity_df['Status'].unique())
                    selected_statuses = st.multiselect("Select PR Status", statuses, default=statuses)
                
                with col3:
                    health_options = sorted(activity_df['PR Health'].unique())
                    selected_health = st.multiselect("Select PR Health", health_options, default=health_options)
                
                # Apply filters
                filtered_df = activity_df.copy()
                if selected_repos:
                    filtered_df = filtered_df[filtered_df['Repository'].isin(selected_repos)]
                if selected_statuses:
                    filtered_df = filtered_df[filtered_df['Status'].isin(selected_statuses)]
                if selected_health:
                    filtered_df = filtered_df[filtered_df['PR Health'].isin(selected_health)]
                
                # Metrics
                st.subheader("PR Metrics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total PRs", len(filtered_df))
                with col2:
                    st.metric("Avg Files Changed", f"{filtered_df['Files Changed'].mean():.1f}")
                with col3:
                    st.metric("Avg Lines Added", f"{filtered_df['Lines Added'].mean():.1f}")
                with col4:
                    st.metric("Avg Days Open", f"{filtered_df['Days Open'].mean():.1f}")
                
                # Duration chart
                st.subheader("PR Duration Distribution")
                fig = px.histogram(filtered_df, x='Days Open', nbins=20, color_discrete_sequence=['#3366CC'])
                fig.add_vline(x=pr_threshold_days, line_dash="dash", line_color="red", 
                            annotation_text=f"Health Threshold ({pr_threshold_days} days)")
                st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                st.subheader("PR Data Table")
                st.dataframe(filtered_df)
                
                # Download link
                st.markdown(generate_download_link(filtered_df, 'pr_activity.csv', 'Download PR Activity Data'), unsafe_allow_html=True)
            else:
                st.error("No PR activity data available")
        
        # Contributors tab
        with tabs[2]:
            st.header("Contributor Analytics")
            
            if not contributor_df.empty:
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    repos = sorted(contributor_df['Repository'].unique())
                    selected_repos = st.multiselect("Select Repositories", repos, 
                                                default=repos[:min(3, len(repos))],
                                                key="contributor_repos")
                
                with col2:
                    contrib_min = st.slider("Minimum PRs Created", 1, max(contributor_df['PRs Created']), 1)
                
                # Apply filters
                filtered_df = contributor_df.copy()
                if selected_repos:
                    filtered_df = filtered_df[filtered_df['Repository'].isin(selected_repos)]
                filtered_df = filtered_df[filtered_df['PRs Created'] >= contrib_min]
                
                # Top contributors chart
                st.subheader("Top Contributors by PRs Created")
                top_contributors = filtered_df.sort_values('PRs Created', ascending=False).head(10)
                fig = px.bar(top_contributors, x='Contributor', y='PRs Created', color='Repository', barmode='group')
                st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                st.subheader("Contributor Data Table")
                st.dataframe(filtered_df)
                
                # Download link
                st.markdown(generate_download_link(filtered_df, 'contributor_data.csv', 'Download Contributor Data'), unsafe_allow_html=True)
            else:
                st.error("No contributor data available")
        
        # Commits tab
        with tabs[3]:
            st.header("Commit Analysis")
            
            if not commit_df.empty:
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    repos = sorted(commit_df['Repository'].unique())
                    selected_repos = st.multiselect("Select Repositories", repos, 
                                                default=repos[:min(3, len(repos))],
                                                key="commit_repos")
                
                with col2:
                    authors = sorted(commit_df['Author'].unique())
                    selected_authors = st.multiselect("Select Authors", authors, default=[])
                
                # Apply filters
                filtered_df = commit_df.copy()
                if selected_repos:
                    filtered_df = filtered_df[filtered_df['Repository'].isin(selected_repos)]
                if selected_authors:
                    filtered_df = filtered_df[filtered_df['Author'].isin(selected_authors)]
                
                # Metrics
                st.subheader("Commit Metrics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Commits", len(filtered_df))
                with col2:
                    st.metric("Unique Authors", filtered_df['Author'].nunique())
                with col3:
                    st.metric("Unique PRs", filtered_df['PR Number'].nunique())
                
                # Data table
                st.subheader("Commit Data Table")
                st.dataframe(filtered_df)
                
                # Download link
                st.markdown(generate_download_link(filtered_df, 'commit_data.csv', 'Download Commit Data'), unsafe_allow_html=True)
            else:
                st.error("No commit data available")
    
    except FileNotFoundError:
        st.error(f"Data file not found. Please run the metrics collector first.")
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.text(f"Detailed error: {str(type(e))}: {str(e)}")

if __name__ == "__main__":
    main()
''')
            
            return dashboard_path
        except Exception as e:
            self.logger.error(f"Error creating dashboard: {str(e)}")
            return None