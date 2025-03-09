# dashboard/streamlit_app.py
import os
import sys
import pickle
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import base64
from pathlib import Path

class ReportUtility:
    """Utility class for the Streamlit dashboard."""
    
    @staticmethod
    def generate_download_link(df, filename, text):
        """Generate a download link for a dataframe."""
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'data:file/csv;base64,{b64}'
        return f'<a href="{href}" download="{filename}">{text}</a>'

def run_dashboard(data_path):
    """
    Run the Streamlit dashboard application.
    
    Args:
        data_path (str): Path to the pickled report data file
    """
    try:
        # Load the serialized data
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
        
        # Create main tabs
        tabs = st.tabs(["Summary", "PR Activity", "Contributors", "Commits"])
        
        # --- SUMMARY TAB --- 
        with tabs[0]:
            st.header("GitHub Repository Metrics Summary")
            
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total PRs", summary_metrics['total_prs'])
                st.metric("Repositories", summary_metrics['total_repos'])
            with col2:
                st.metric("Healthy PRs", summary_metrics['healthy_prs'])
                st.metric("Merged PRs", summary_metrics['merged_prs'])
            with col3:
                st.metric("Unhealthy PRs", summary_metrics['unhealthy_prs'])
                st.metric("Health Ratio", f"{summary_metrics['health_ratio']:.1f}%")
            with col4:
                st.metric("Avg PR Duration", f"{summary_metrics['avg_pr_duration']:.1f} days")
                st.metric("Change Requests", summary_metrics['total_change_requests'])
            
            st.subheader("Code Changes")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Lines Added", summary_metrics['total_additions'])
            with col2:
                st.metric("Lines Deleted", summary_metrics['total_deletions'])
            
            # PR Timeline chart
            st.subheader("PR Creation Timeline")
            date_df = pd.DataFrame({
                'Date': list(summary_metrics['pr_by_date'].keys()),
                'PRs Created': list(summary_metrics['pr_by_date'].values())
            })
            date_df['Date'] = pd.to_datetime(date_df['Date'])
            fig = px.line(date_df, x='Date', y='PRs Created', markers=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # Repositories bar chart
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
            if 'pr_by_author' in summary_metrics:
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
            
            if activity_df is not None:
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
                            color_discrete_map={'Healthy': '#4CAF50', 'Unhealthy': '#F44336'})
                st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                st.subheader("PR Data Table")
                st.dataframe(filtered_df, use_container_width=True)
                
                # Download link
                st.markdown(ReportUtility.generate_download_link(filtered_df, 'pr_activity.csv', 'Download PR Activity Data'), unsafe_allow_html=True)
            else:
                st.error("No PR activity data available.")

        # --- CONTRIBUTORS TAB --- 
        with tabs[2]:
            st.header("Contributor Analytics")
            
            if contributor_df is not None:
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
                    lambda x: float(x.split('/')[0]) / float(x.split('/')[1]) * 100 if '/' in str(x) else 0
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
                    fig = px.bar(avg_days_df, x='Contributor', y='Avg Days to Merge',
                                color='Avg Days to Merge', color_continuous_scale='Blues_r')
                    fig.update_layout(title="Average Days to Merge by Contributor")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                st.subheader("Contributor Data Table")
                st.dataframe(filtered_df, use_container_width=True)
                
                # Download link
                st.markdown(ReportUtility.generate_download_link(filtered_df, 'contributor_data.csv', 'Download Contributor Data'), unsafe_allow_html=True)
            else:
                st.error("No contributor data available.")

        # --- COMMITS TAB ---
        with tabs[3]:
            st.header("Commit Analysis")
            
            if commit_df is not None:
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
                st.markdown(ReportUtility.generate_download_link(filtered_df, 'commit_data.csv', 'Download Commit Data'), unsafe_allow_html=True)
            else:
                st.error("No commit data available.")
                
    except Exception as e:
        st.error(f"An error occurred while loading the dashboard: {str(e)}")
        st.error("If you're seeing this error, try running the script from the directory containing the report files.")

if __name__ == "__main__":
    # If run directly, look for data in the current directory
    st.sidebar.title("GitHub Metrics Dashboard")
    st.sidebar.info("This is a standalone mode. Upload your report files to view the dashboard.")
    
    uploaded_files = st.sidebar.file_uploader(
        "Upload Excel report files",
        type=["xlsx"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Process the uploaded files
        activity_df = None
        contributor_df = None
        commit_df = None
        
        for file in uploaded_files:
            if "activity" in file.name.lower():
                activity_df = pd.read_excel(file)
            elif "contributor" in file.name.lower():
                contributor_df = pd.read_excel(file)
            elif "commit" in file.name.lower():
                commit_df = pd.read_excel(file)
        
        # Create a data dictionary and save it to a temporary file
        report_data = {
            'activity_df': activity_df,
            'contributor_df': contributor_df,
            'commit_df': commit_df,
            'summary_metrics': calculate_summary_metrics(activity_df, contributor_df, commit_df),
            'pr_threshold_days': 2  # Default value
        }
        
        # Run the dashboard with the data
        run_dashboard(report_data)
    else:
        st.title("GitHub Metrics Dashboard")
        st.info("Please upload the Excel report files generated by the GitHub Metrics Reporter to view the dashboard.")

def calculate_summary_metrics(activity_df, contributor_df, commit_df):
    """Calculate summary metrics from available dataframes when running in standalone mode."""
    summary = {
        'total_repos': 0,
        'total_prs': 0,
        'merged_prs': 0,
        'healthy_prs': 0,
        'unhealthy_prs': 0,
        'total_additions': 0,
        'total_deletions': 0,
        'total_change_requests': 0,
        'avg_pr_duration': 0,
        'health_ratio': 0,
        'pr_by_repo': {},
        'pr_by_author': {},
        'pr_by_date': {}
    }
    
    # Calculate metrics from the activity dataframe
    if activity_df is not None:
        summary['total_prs'] = len(activity_df)
        summary['total_repos'] = activity_df['Repository'].nunique()
        
        # Calculate PR by repo
        repo_counts = activity_df['Repository'].value_counts().to_dict()
        summary['pr_by_repo'] = repo_counts
        
        # Calculate PR by author
        if 'Author' in activity_df.columns:
            author_counts = activity_df['Author'].value_counts().to_dict()
            summary['pr_by_author'] = author_counts
        
        # Calculate PR by date
        if 'Created Date' in activity_df.columns:
            activity_df['Created Date'] = pd.to_datetime(activity_df['Created Date'])
            date_counts = activity_df.groupby(activity_df['Created Date'].dt.date).size()
            summary['pr_by_date'] = {str(d): c for d, c in zip(date_counts.index, date_counts.values)}
        
        # Calculate health metrics
        if 'PR Health' in activity_df.columns:
            summary['healthy_prs'] = len(activity_df[activity_df['PR Health'].str.contains('Healthy')])
            summary['unhealthy_prs'] = len(activity_df[activity_df['PR Health'].str.contains('Unhealthy')])
            
            if summary['total_prs'] > 0:
                summary['health_ratio'] = (summary['healthy_prs'] / summary['total_prs']) * 100
        
        # Calculate merge metrics
        if 'Status' in activity_df.columns:
            summary['merged_prs'] = len(activity_df[activity_df['Status'] == 'Merged'])
        
        # Calculate duration metrics
        if 'Days Open' in activity_df.columns:
            summary['avg_pr_duration'] = activity_df['Days Open'].mean()
        
        # Calculate code change metrics
        if 'Lines Added' in activity_df.columns and 'Lines Deleted' in activity_df.columns:
            summary['total_additions'] = activity_df['Lines Added'].sum()
            summary['total_deletions'] = activity_df['Lines Deleted'].sum()
        
        # Calculate change request metrics
        if 'Change Requests' in activity_df.columns:
            summary['total_change_requests'] = activity_df['Change Requests'].sum()
    
    return summary
                