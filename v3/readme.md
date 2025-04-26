# GitHub Repository Metrics Reporter

A comprehensive tool for analyzing GitHub repository activity, tracking contributor metrics, and visualizing PR and branch health across your organization's projects.

## Overview

The GitHub Repository Metrics Reporter collects detailed metrics from your GitHub repositories, generates Excel reports, and provides an interactive dashboard for visualization. It helps engineering managers and team leads gain insights into repository health, contributor performance, and development workflow patterns.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage Instructions](#usage-instructions)
- [Core Metrics Explained](#core-metrics-explained)
- [Dashboard Guide](#dashboard-guide)
- [Calculation Examples](#calculation-examples)
- [Report Structure](#report-structure)
- [Extending the Tool](#extending-the-tool)
- [Troubleshooting](#troubleshooting)

## Features

- **Pull Request Analysis**: Track PR health, merge rates, cycle time, and reviewer engagement
- **Contributor Performance**: Analyze individual contributor activity, code quality, and test coverage
- **Branch Management**: Monitor active and stale branches across repositories and contributors
- **Version Tracking**: Categorize and analyze RC, NPD, and stable versions
- **Health Indicators**: Visual indicators and metrics for repository and contributor health
- **Interactive Dashboard**: Visualize metrics with filtering, date ranges, and drill-down capabilities
- **Conversation Analysis**: Track comment resolution rates and engagement metrics

## Requirements

- Python 3.7+
- GitHub personal access token with repo permissions
- Required Python packages:
  ```
  pandas>=1.3.0
  requests>=2.25.0
  pytz>=2021.1
  streamlit>=1.10.0
  xlsxwriter>=3.0.3
  ```

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-org/github-metrics-reporter.git
   cd github-metrics-reporter
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a GitHub token with repo permissions (Settings > Developer settings > Personal access tokens)

## Usage Instructions

### Collecting Metrics

```bash
python gh_metrics_enhanced_v1.py --org your-organization \
                                 --start-date 2023-01-01 \
                                 --end-date 2023-12-31 \
                                 --repos-file repos.txt \
                                 --token-file token.txt \
                                 --output-dir metrics_output \
                                 --pr-threshold 7 \
                                 --label-threshold 2 \
                                 --branch-staleness 30
```

#### Arguments Explained:

- **Required:**
  - `--org`: Your GitHub organization name
  - `--start-date`: Analysis start date (YYYY-MM-DD)
  - `--end-date`: Analysis end date (YYYY-MM-DD)

- **Optional:**
  - `--repos-file`: Path to file with repository names (one per line)
  - `--token-file`: Path to file containing GitHub token (alternatively, set GITHUB_TOKEN environment variable)
  - `--output-dir`: Custom output directory path (default: reports_YYYYMMDD_HHMMSS)
  - `--pr-threshold`: PR health threshold in days (default: 7)
  - `--label-threshold`: Maximum labels threshold (default: 2)
  - `--branch-staleness`: Branch staleness threshold in days (default: 30)

### Launching the Dashboard

```bash
streamlit run github_metrics_dashboard.py
```

The dashboard will open in your default browser. Select the report directory to visualize the metrics.

### Processing Reports

```bash
python excel_report_processor.py --report-dir reports_20231231_235959
```

This utility can extract and combine data from multiple reports.

## Core Metrics Explained

### Pull Request Health Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| Healthy PRs | PRs that meet health criteria | Count of PRs that don't exceed thresholds |
| Needs Attention PRs | PRs requiring attention | Count of PRs exceeding duration or label thresholds |
| Health Percentage | Overall PR health indicator | `(Healthy PRs / Total PRs) * 100` |
| Avg PR Duration | Average days PRs remain open | Sum of PR durations / Total PR count |
| Merge Rate | Percentage of PRs that get merged | `(Merged PRs / Total PRs) * 100` |

#### PR Health Formula:
```python
if pr_duration_days > pr_threshold_days or label_count > max_labels_threshold:
    pr_health = 'Needs Attention'
else:
    pr_health = 'Healthy'
```

#### Example:
For a repo with 80 PRs, 70 healthy and 10 needs attention:
- Health Percentage: (70 / 80) * 100 = 87.5%

### Branch Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| Active Branches | Branches with commits within threshold | Count of branches with recent activity |
| Stale Branches | Branches without recent commits | Count of branches without activity in the threshold period |
| Branch Health | Percentage of active branches | `(Active Branches / Total Branches) * 100` |

#### Branch Staleness Formula:
```python
days_since_last_commit = (current_date - last_commit_date).days
is_stale = days_since_last_commit > branch_staleness_threshold
```

#### Example:
For a contributor with 12 active branches and 8 stale branches:
- Active Branches: 12
- Stale Branches: 8
- Branch Health: (12 / 20) * 100 = 60% Active

### Contributor Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| Total PRs | PRs authored by contributor | Count of PRs created |
| Total Commits | Commits authored by contributor | Sum of commits across all PRs |
| Total Active Branches | Active branches owned by contributor | Count of contributor's active branches |
| Total Stale Branches | Stale branches owned by contributor | Count of contributor's stale branches |
| Avg Commits per Day | Commit frequency | `Total Commits / Active Days` |

### Comment and Conversation Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| Total Reviewer Comments | Comments made by reviewers | Sum of comments not by approvers |
| Total Approver Comments | Comments made by approvers | Sum of comments by approvers |
| Resolved Conversations | PR conversations that were addressed | Count of threads with author replies |
| Unresolved Conversations | PR conversations without resolution | Count of threads without author replies |
| Resolution Rate | Percentage of conversations resolved | `(Resolved / Total Conversations) * 100` |

#### Resolution Rate Formula:
```python
total_conversations = resolved_conversations + unresolved_conversations
if total_conversations > 0:
    resolution_rate = (resolved_conversations / total_conversations) * 100
else:
    resolution_rate = 100.0  # Default when no conversations
```

#### Example:
With 45 resolved conversations and 15 unresolved:
- Resolution Rate: (45 / 60) * 100 = 75%

### Code Quality Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| Passed Checks | CI checks that passed | Sum of successful checks |
| Failed Checks | CI checks that failed | Sum of failed checks |
| Success Rate | Percentage of checks that passed | `(Passed Checks / Total Checks) * 100` |
| Feature/Fix PRs | PRs for new features or fixes | Count of PRs with feat: or fix: prefix |
| Breaking Change PRs | PRs with breaking changes | Count of PRs with feat! prefix |

### Coverage Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| With Examples | Feature/fix PRs with examples | Count of PRs including examples folder changes |
| With Tests | Feature/fix PRs with tests | Count of PRs including tests folder changes |
| With Integration Tests | Feature/fix PRs with integration tests | Count of PRs including integration_tests folder changes |
| Examples Coverage | Percentage with examples | `(With Examples / Feature PRs) * 100` |
| Tests Coverage | Percentage with tests | `(With Tests / Feature PRs) * 100` |

#### Example:
For a contributor with 50 feature PRs, 40 with tests, 25 with examples:
- Tests Coverage: (40 / 50) * 100 = 80%
- Examples Coverage: (25 / 50) * 100 = 50%

### Version Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| RC Versions | Release candidate versions | Count of labels ending with -rc |
| NPD Versions | Non-production versions | Count of labels ending with -npd |
| Stable Versions | Production versions | Count of other version labels |

## Dashboard Guide

The dashboard provides three main tabs:

### 1. Overall Summary Tab

Contains high-level metrics across all repositories:

- **Repository Health Summary**: Total repositories, PRs, and contributors
- **PR Health Metrics**: Healthy vs. Needs Attention PRs with breakdown
- **Comment Metrics**: Total comments, resolved/unresolved conversations
- **Version Types**: RC, NPD, and Stable version counts
- **Branch and PR Metrics**: Active/stale branches and PR breakdown
- **Repository Health Overview**: Table with health indicators for each repo

![Overall Summary Tab](https://example.com/overall_summary.png)

### 2. Contributor Summary Tab

Displays metrics by contributor:

- **Contributor Activity**: Total contributors, PRs, commits
- **Branch Activity Metrics**: Active and stale branches by contributor
- **PR Check Metrics**: Passed/failed checks with success rates
- **PR Comment Metrics**: Comments and conversation resolution rates
- **Feature/Fix Coverage**: Test and example coverage by contributor
- **Top Contributors**: Ranking by PR count and other metrics

![Contributor Summary Tab](https://example.com/contributor_summary.png)

### 3. PR Activity Summary Tab

Shows detailed PR metrics:

- **PR Duration and Comments**: Average cycle time and comment rates
- **Breaking Change Analysis**: Breaking changes by repository
- **PR Health by Repository**: Health distribution across repositories
- **PR Checks Status**: Check success rates by repository
- **PR Age Distribution**: PRs grouped by age buckets
- **Feature/Fix Coverage**: Test and example coverage by repository

![PR Activity Tab](https://example.com/pr_activity.png)

## Calculation Examples

### PR Health Example

Consider a repository with:
- 120 total PRs
- 20 PRs open > 7 days
- 10 PRs with > 2 labels
- 5 PRs with both issues

```
Healthy PRs = 120 - (20 + 10 - 5) = 95
Needs Attention PRs = 25
Health Percentage = (95 / 120) * 100 = 79.2%
```

### Branch Health Example

For an organization with:
- 5 active repositories
- 150 total branches
- 35 branches with no commits in last 30 days

```
Active Branches = 150 - 35 = 115
Stale Branches = 35
Branch Health = (115 / 150) * 100 = 76.7% Active
```

### Contributor Performance Example

For a contributor with:
- 25 PRs (20 healthy, 5 needs attention)
- 120 total commits over 45 active days
- 15 active branches, 10 stale branches
- 30 feature/fix PRs (25 with tests, 18 with examples)

```
PR Health = (20 / 25) * 100 = 80%
Avg Commits per Day = 120 / 45 = 2.67
Branch Health = (15 / 25) * 100 = 60% Active
Tests Coverage = (25 / 30) * 100 = 83.3%
Examples Coverage = (18 / 30) * 100 = 60%
```

## Report Structure

The script generates two main Excel files:

### 1. pr_activity_report.xlsx

Contains two sheets:
- **PR Activity**: Detailed information for each PR
- **Repository Summary**: Aggregated metrics by repository

| Repository | Total PRs | Healthy PRs | Needs Attention | Health % | ... |
|------------|-----------|-------------|-----------------|----------|-----|
| repo-one   | 50        | 45          | 5               | 90.0     | ... |
| repo-two   | 120       | 95          | 25              | 79.2     | ... |
| repo-three | 75        | 68          | 7               | 90.7     | ... |

### 2. contributor_report.xlsx

Contains two sheets:
- **Contributor Metrics**: Detailed metrics by contributor and repository
- **Contributor Summary**: Aggregated metrics by contributor

| Contributor | Total PRs | Total Commits | Healthy % | Active Branches | Stale Branches | ... |
|-------------|-----------|---------------|-----------|-----------------|----------------|-----|
| alice       | 45        | 230           | 88.9      | 12              | 5              | ... |
| bob         | 30        | 185           | 76.7      | 8               | 10             | ... |
| charlie     | 75        | 340           | 93.3      | 18              | 3              | ... |

## Extending the Tool

### Adding New Metrics

1. Add data collection to the `fetch_pr_data` or `fetch_contributor_branches` methods
2. Update the `generate_pr_activity_report` and `generate_contributor_report` methods
3. Add visualization to the dashboard in the appropriate sections

### Creating Custom Reports

You can use the `excel_report_processor.py` script to generate custom reports:

```python
processor = ExcelReportProcessor()
summary = processor.generate_repository_summary("reports_20231231_235959")
custom_data = processor.extract_top_contributors(top_n=20)
```

## Troubleshooting

### Common Issues

- **Authentication Errors**: Ensure your GitHub token has the required permissions
- **404 Errors**: These are normal for empty repositories or repos without branches
- **Rate Limiting**: The script implements retries, but you might need to wait if you hit API limits
- **Missing Metrics**: Some metrics require specific repo structures (e.g., tests folder)

### Logging

The script creates detailed logs in the logs directory. Check these logs for troubleshooting:

```
logs/github_metrics_20231231_235959.log
```

### Error Handling

The script is designed to continue processing repositories even if errors occur with specific repositories or branches. Check the summary output for details on any skipped data.

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- GitHub API for providing the data access
- Streamlit for the interactive dashboard capabilities
- The open source community for tools and libraries used in this project