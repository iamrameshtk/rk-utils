from datetime import datetime

def calculate_summary_metrics(all_metrics, logger):
    """Calculate overall summary metrics for all repositories."""
    try:
        logger.info("Calculating summary metrics")
        
        summary = {
            'total_repos': len(all_metrics),
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
        
        all_pr_durations = []
        pr_dates = {}
        
        for repo, metrics in all_metrics.items():
            # Add repo stats
            summary['pr_by_repo'][repo] = metrics['stats']['total_prs']
            
            # Aggregate total stats
            summary['total_prs'] += metrics['stats']['total_prs']
            summary['merged_prs'] += metrics['stats']['merged_prs']
            summary['healthy_prs'] += metrics['stats']['healthy_prs']
            summary['unhealthy_prs'] += metrics['stats']['unhealthy_prs']
            summary['total_additions'] += metrics['stats']['total_additions']
            summary['total_deletions'] += metrics['stats']['total_deletions']
            summary['total_change_requests'] += metrics['stats']['total_change_requests']
            
            # Track PR authors
            for pr in metrics['pull_requests']:
                author = pr['author']
                if author not in summary['pr_by_author']:
                    summary['pr_by_author'][author] = 0
                summary['pr_by_author'][author] += 1
                
                # Track PR durations
                all_pr_durations.append(pr['pr_duration_days'])
                
                # Track PR creation dates for time series
                date_str = pr['created_at'].strftime('%Y-%m-%d')
                if date_str not in pr_dates:
                    pr_dates[date_str] = 0
                pr_dates[date_str] += 1
        
        # Calculate average PR duration
        if all_pr_durations:
            summary['avg_pr_duration'] = sum(all_pr_durations) / len(all_pr_durations)
        
        # Calculate health ratio
        if summary['total_prs'] > 0:
            summary['health_ratio'] = summary['healthy_prs'] / summary['total_prs'] * 100
        
        # Sort PR dates chronologically
        sorted_dates = sorted(pr_dates.keys())
        summary['pr_by_date'] = {date: pr_dates[date] for date in sorted_dates}
        
        # Add date range for dashboard display
        if sorted_dates:
            summary['date_range'] = f"{sorted_dates[0]} to {sorted_dates[-1]}"
        
        logger.info("Summary metrics calculated successfully")
        return summary
        
    except Exception as e:
        logger.error(f"Error calculating summary metrics: {str(e)}")
        return {
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