# main.py
import argparse
import sys
import os
from datetime import datetime
import pytz
import shutil

from metrics_reporter import GitHubMetricsReporter

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='GitHub Repository Metrics Generator')
    parser.add_argument('--org', required=True, help='GitHub organization/owner name')
    parser.add_argument('--start-date', required=True, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', required=True, help='End date in YYYY-MM-DD format')
    parser.add_argument('--repos-file', required=True, help='Path to file containing repository names (one per line)')
    parser.add_argument('--token-file', help='Path to file containing GitHub token (optional)')
    parser.add_argument('--output-dir', default='github_reports', help='Output directory path (default: github_reports)')
    parser.add_argument('--pr-threshold', type=int, default=2, help='PR health threshold in days (default: 2)')
    parser.add_argument('--streamlit', action='store_true', help='Launch Streamlit dashboard after generating reports')
    return parser.parse_args()

def main():
    """Main execution flow."""
    try:
        args = parse_arguments()
        
        print("\nGitHub Repository Metrics Reporter")
        print("=================================")
        
        # Create the reporter
        reporter = GitHubMetricsReporter()
        
        # Set PR threshold days from command line if provided
        if args.pr_threshold:
            reporter.pr_threshold_days = args.pr_threshold
            reporter.logger.info(f"PR health threshold set to {reporter.pr_threshold_days} days")
        
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
            # Read repositories from the specified file
            with open(args.repos_file, 'r', encoding='utf-8') as f:
                repositories = [line.strip() for line in f if line.strip()]
            reporter.logger.info(f"Loaded {len(repositories)} repositories from {args.repos_file}")
            
            if not repositories:
                reporter.logger.error(f"The repository file {args.repos_file} is empty. Please specify at least one repository.")
                sys.exit(1)
        else:
            reporter.logger.error(f"Repository file {args.repos_file} not found. This is a required parameter.")
            sys.exit(1)
        
        # Create or clean output directory
        output_dir = args.output_dir
        if os.path.exists(output_dir):
            reporter.logger.info(f"Cleaning existing output directory: {output_dir}")
            # Instead of deleting everything, just remove Excel and pickle files
            for filename in os.listdir(output_dir):
                if filename.endswith(('.xlsx', '.pkl')):
                    os.remove(os.path.join(output_dir, filename))
        else:
            os.makedirs(output_dir, exist_ok=True)
        
        # Run the reporter
        success = reporter.run(
            args.org,
            repositories,
            start_date,
            end_date,
            args.token_file,
            output_dir,
            args.streamlit
        )
        
        if not success:
            reporter.logger.error("Failed to generate reports.")
            sys.exit(1)
        
        # Create standalone dashboard file
        if args.streamlit:
            create_standalone_dashboard(output_dir)
            
        print(f"\nReports successfully generated in: {output_dir}")
        if args.streamlit:
            print(f"Run the dashboard with: streamlit run {output_dir}/dashboard.py")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

def create_standalone_dashboard(output_dir):
    """Create a standalone dashboard file that doesn't rely on imports."""
    dashboard_path = os.path.join(output_dir, "dashboard.py")
    
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        # Notice the encoding parameter added here
        f.write("""
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
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'data:file/csv;base64,{b64}'
    return f'<a href="{href}" download="{filename}">{text}</a>'

# Main dashboard function
def main():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load the data
    data_path = os.path.join(current_dir, "report_data.pkl")
    
    try:
        with open(data_path, 'rb') as f:
            report_data = pickle.load(f)
        
        # Unpack the data
        activity_df = report_data['activity_df']
        contributor_df = report_data['contributor_df'] 
        commit_df = report_data['commit_df']
        summary_metrics = report_data['summary_metrics']
        pr_threshold_days = report_data['pr_threshold_days']
        
        # Set up the dashboard
        st.set_page_config(
            page_title="GitHub Metrics Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.sidebar.title("GitHub Metrics Dashboard")
        st.sidebar.markdown(f"Data range: {summary_metrics.get('date_range', 'Not specified')}")
        
        # Create main tabs
        tabs = st.tabs(["Summary", "PR Activity", "Contributors", "Commits"])
        
        # --- SUMMARY TAB --- 
        with tabs[0]:
            st.header("GitHub Repository Metrics Summary")
            
            # Display key metrics
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
            
            st.subheader("Code Changes")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Lines Added", summary_metrics.get('total_additions', 0))
            with col2:
                st.metric("Lines Deleted", summary_metrics.get('total_deletions', 0))
            
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
            
            # Repositories bar chart
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
            
            # Top contributors
            if 'pr_by_author' in summary_metrics and summary_metrics['pr_by_author']:
                st.subheader("Top Contributors")
                author_df = pd.DataFrame({
                    'Author': list(summary_metrics['pr_by_author'].keys()),
                    'PR Count': list(summary_metrics['pr_by_author'].values())
                })
                author_df = author_df.sort_values('PR Count', ascending=False).head(10)
                fig = px.bar(author_df, x='Author', y='PR Count', color='PR Count',
                            color_continuous_scale=px.colors.sequential.Plasma)
                st.plotly_chart(fig, use_container_width=True)
        
        # --- PR ACTIVITY TAB --- 
        with tabs[1]:
            st.header("Pull Request Activity")
            
            if activity_df is not None and not activity_df.empty:
                # Filter options
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
                
                # Show metrics
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
                
                # PR Days Distribution
                st.subheader("PR Duration Distribution")
                fig = px.histogram(filtered_df, x='Days Open', nbins=20,
                                color_discrete_sequence=['#3366CC'])
                fig.add_vline(x=pr_threshold_days, line_dash="dash", line_color="red",
                            annotation_text=f"Health Threshold ({pr_threshold_days} days)")
                st.plotly_chart(fig, use_container_width=True)
                
                # PR Health distribution
                st.subheader("PR Health Distribution")
                health_counts = filtered_df['PR Health'].value_counts().reset_index()
                health_counts.columns = ['Health Status', 'Count']
                fig = px.pie(health_counts, values='Count', names='Health Status',
                            color='Health Status',
                            color_discrete_map={'✅ Healthy': '#4CAF50', '❌ Unhealthy': '#F44336'})
                st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                st.subheader("PR Data Table")
                st.dataframe(filtered_df, use_container_width=True)
                
                # Download link
                st.markdown(generate_download_link(filtered_df, 'pr_activity.csv', 'Download PR Activity Data'), unsafe_allow_html=True)
            else:
                st.error("No PR activity data available.")

        # --- CONTRIBUTORS TAB --- 
        with tabs[2]:
            st.header("Contributor Analytics")
            
            if contributor_df is not None and not contributor_df.empty:
                # Filter options
                col1, col2 = st.columns(2)
                with col1:
                    repos = sorted(contributor_df['Repository'].unique())
                    selected_repos = st.multiselect("Select Repositories", repos, 
                                                default=repos[:min(3, len(repos))],
                                                key="contributor_repos")
                
                with col2:
                    contrib_min = st.slider("Minimum PRs Created", 1, 
                                            max(contributor_df['PRs Created']), 1)
                
                # Apply filters
                filtered_df = contributor_df.copy()
                if selected_repos:
                    filtered_df = filtered_df[filtered_df['Repository'].isin(selected_repos)]
                filtered_df = filtered_df[filtered_df['PRs Created'] >= contrib_min]
                
                # Top Contributors chart
                st.subheader("Top Contributors by PRs Created")
                top_contributors = filtered_df.sort_values('PRs Created', ascending=False).head(10)
                fig = px.bar(top_contributors, x='Contributor', y='PRs Created', 
                            color='Repository', barmode='group')
                st.plotly_chart(fig, use_container_width=True)
                
                # Health ratio by contributor
                st.subheader("Health Ratio by Contributor")
                # Extract numeric health ratio
                filtered_df['Health Ratio Numeric'] = filtered_df['Health Ratio'].apply(
                    lambda x: float(x.split('/')[0]) / float(x.split('/')[1]) * 100 if '/' in str(x) and float(x.split('/')[1]) > 0 else 0
                )
                
                health_df = filtered_df.sort_values('PRs Created', ascending=False).head(10)
                fig = px.bar(health_df, x='Contributor', y='Health Ratio Numeric',
                            color='Health Ratio Numeric', color_continuous_scale='RdYlGn',
                            labels={'Health Ratio Numeric': 'Health Ratio (%)'})
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
                
                # Productivity metrics
                st.subheader("Contributor Productivity")
                col1, col2 = st.columns(2)
                
                with col1:
                    code_df = filtered_df.sort_values('Lines Added', ascending=False).head(10)
                    fig = px.bar(code_df, x='Contributor', y=['Lines Added', 'Lines Deleted'],
                                barmode='group', labels={'value': 'Lines of Code', 'variable': 'Type'})
                    fig.update_layout(title="Code Changes by Contributor")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    avg_days_df = filtered_df[filtered_df['Avg Days to Merge'] > 0].sort_values('Avg Days to Merge').head(10)
                    if not avg_days_df.empty:
                        fig = px.bar(avg_days_df, x='Contributor', y='Avg Days to Merge',
                                    color='Avg Days to Merge', color_continuous_scale='Blues_r')
                        fig.update_layout(title="Average Days to Merge by Contributor")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No merge data available for display.")
                
                # Data table
                st.subheader("Contributor Data Table")
                st.dataframe(filtered_df, use_container_width=True)
                
                # Download link
                st.markdown(generate_download_link(filtered_df, 'contributor_data.csv', 'Download Contributor Data'), unsafe_allow_html=True)
            else:
                st.error("No contributor data available.")

        # --- COMMITS TAB ---
        with tabs[3]:
            st.header("Commit Analysis")
            
            if commit_df is not None and not commit_df.empty:
                # Filter options
                col1, col2, col3 = st.columns(3)
                with col1:
                    repos = sorted(commit_df['Repository'].unique())
                    selected_repos = st.multiselect("Select Repositories", repos, 
                                                default=repos[:min(3, len(repos))],
                                                key="commit_repos")
                
                with col2:
                    authors = sorted(commit_df['Author'].unique())
                    selected_authors = st.multiselect("Select Authors", authors, default=[])
                
                with col3:
                    try:
                        date_range = st.date_input(
                            "Commit Date Range",
                            [
                                pd.to_datetime(commit_df['Commit Date']).min(),
                                pd.to_datetime(commit_df['Commit Date']).max()
                            ]
                        )
                    except:
                        st.warning("Invalid date format in commit data. Date filtering is disabled.")
                        date_range = None
                
                # Apply filters
                filtered_df = commit_df.copy()
                if selected_repos:
                    filtered_df = filtered_df[filtered_df['Repository'].isin(selected_repos)]
                if selected_authors:
                    filtered_df = filtered_df[filtered_df['Author'].isin(selected_authors)]
                if date_range and len(date_range) == 2:
                    try:
                        start_date, end_date = date_range
                        filtered_df = filtered_df[
                            (pd.to_datetime(filtered_df['Commit Date']) >= pd.to_datetime(start_date)) &
                            (pd.to_datetime(filtered_df['Commit Date']) <= pd.to_datetime(end_date))
                        ]
                    except:
                        st.warning("Error applying date filter. Showing all dates.")
                
                # Show metrics
                st.subheader("Commit Metrics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Commits", len(filtered_df))
                with col2:
                    st.metric("Unique Authors", filtered_df['Author'].nunique())
                with col3:
                    st.metric("Unique PRs", filtered_df['PR Number'].nunique())
                
                # Commit timeline
                st.subheader("Commit Timeline")
                filtered_df['Commit Date'] = pd.to_datetime(filtered_df['Commit Date'])
                commit_counts = filtered_df.groupby(filtered_df['Commit Date'].dt.date).size().reset_index()
                commit_counts.columns = ['Date', 'Commit Count']
                fig = px.line(commit_counts, x='Date', y='Commit Count', markers=True)
                st.plotly_chart(fig, use_container_width=True)
                
                # Commits by author
                st.subheader("Commits by Author")
                author_counts = filtered_df['Author'].value_counts().reset_index().head(10)
                author_counts.columns = ['Author', 'Commit Count']
                fig = px.bar(author_counts, x='Author', y='Commit Count',
                            color='Commit Count', color_continuous_scale='Viridis')
                st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                st.subheader("Commit Data Table")
                st.dataframe(filtered_df, use_container_width=True)
                
                # Download link
                st.markdown(generate_download_link(filtered_df, 'commit_data.csv', 'Download Commit Data'), unsafe_allow_html=True)
            else:
                st.error("No commit data available.")
    except FileNotFoundError:
        st.error(f"Data file not found at {data_path}. Please run the metrics collector first.")
    except Exception as e:
        st.error(f"An error occurred while loading the dashboard: {str(e)}")
        st.error("For troubleshooting, verify that the report_data.pkl file contains valid data.")
        st.error(f"Current directory: {current_dir}")
        st.error(f"Error details: {type(e).__name__}: {str(e)}")
        
        # List available files for debugging
        try:
            files = os.listdir(current_dir)
            st.warning(f"Files in current directory: {', '.join(files)}")
        except:
            pass

if __name__ == "__main__":
    main()
""")

if __name__ == "__main__":
    main()