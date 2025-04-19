# GCP Resource Cleanup Utility

A comprehensive Python utility for cleaning up resources in Google Cloud Platform projects. This script helps you safely delete multiple resource types across your GCP project, with built-in safeguards, detailed logging, and interactive confirmation for each resource.

## Features

- **Environment Variable Authentication**: Automatically uses GCP access token from `GCP_AUTH_TOKEN` environment variable
- **Interactive Resource Control**: Approve or skip deletion of each individual resource
- **Batch Approval Option**: Option to approve all remaining deletions at once
- **Command-line Project Override**: Specify project ID via command line or interactive prompt
- **Comprehensive Resource Cleanup**: Handles multiple GCP resource types
- **Dry Run Mode**: Preview what would be deleted without making any changes
- **Enhanced Logging**: Detailed logs for tracking operations
- **Error Handling**: Robust error catching and reporting
- **Tabular Results**: Clean summary tables of deleted, skipped, and failed resources

## Resource Types Supported

The script can identify and delete the following GCP resource types:

- Compute Engine instances and disks
- Google Kubernetes Engine (GKE) clusters
- Cloud SQL instances
- Cloud Functions
- Cloud Run services
- Pub/Sub topics
- Firestore indexes
- Storage buckets
- BigQuery datasets
- VPC networks (excluding default)

## Prerequisites

- Python 3.6+
- `tabulate` package (for formatted output)
- Google Cloud SDK (`gcloud` command-line tool)
- A valid GCP access token stored in the `GCP_AUTH_TOKEN` environment variable
- Appropriate GCP permissions to list and delete resources

## Installation

1. Clone or download this script to your local machine
2. Install required dependencies:

```bash
pip install tabulate
```

3. Ensure Google Cloud SDK is installed and available in your PATH
4. Set up your GCP authentication token:

```bash
# Set your GCP authentication token
export GCP_AUTH_TOKEN="your_access_token_here"
```

## Usage

### Basic Execution

```bash
python gcp_cleanup.py
```

### Additional Options

```bash
# Specify project ID directly
python gcp_cleanup.py --project-id=your-project-id

# Dry run mode (list resources without deleting)
python gcp_cleanup.py --dry-run

# Increase concurrent workers (faster deletion)
python gcp_cleanup.py --workers 10

# Enable verbose logging
python gcp_cleanup.py --verbose

# Combine options
python gcp_cleanup.py --project-id=your-project-id --dry-run --verbose
```

### Command-line Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--project-id` | `-p` | GCP Project ID (optional, will prompt if not provided) |
| `--dry-run` | `-d` | List resources without deleting them |
| `--workers` | `-w` | Number of concurrent deletion operations (default: 5) |
| `--verbose` | `-v` | Enable detailed logging |

## Interactive Workflow

When you run the script, it will guide you through the following steps:

1. **Project Selection**: Enter your GCP Project ID (if not provided via command line)
2. **Authentication Verification**: The script checks for the `GCP_AUTH_TOKEN` environment variable
3. **Resource Preview**: See a list of resource types that will be affected
4. **Initial Confirmation**: Confirm that you want to proceed with the resource scan
5. **Per-Resource Confirmation**: For each resource, choose whether to:
   - `yes` - Delete this specific resource
   - `no` - Skip this resource and preserve it
   - `all` - Delete this and all remaining resources without further confirmation
   - `quit` - Stop the deletion process immediately
6. **Summary**: View a tabular report of deleted, skipped, and failed resources

## Authentication

The script uses only the GCP access token stored in the `GCP_AUTH_TOKEN` environment variable:

- If the environment variable is not set, the script will exit with an error message
- The script will attempt to authenticate using the token, and exit immediately if authentication fails
- No service account authentication or other methods are supported

## Per-Resource Deletion Control

One of the key features of this utility is granular control over resource deletion:

### During Cleanup
For each resource, you'll be prompted with:
```
Ready to delete: Compute Instance/instance-name (zone: us-central1-a)
Delete this resource? (yes/no/all/quit):
```

Your options are:
- **yes**: Delete only this specific resource
- **no**: Skip this resource (it will be preserved)
- **all**: Delete this resource and all remaining resources without further prompts
- **quit**: Immediately stop the deletion process

This prevents accidental deletion of critical resources while allowing for efficient bulk cleanup when appropriate.

## Output Format

The script provides a detailed summary of operations in a tabular format:

```
================================================================================
GCP RESOURCE CLEANUP SUMMARY FOR PROJECT: my-project-id
================================================================================

SUCCESSFULLY DELETED RESOURCES:
+------------------+----------------------------+----------+
| Resource Type    | Name                       | Status   |
+==================+============================+==========+
| Compute Instance | test-instance-1            | ✅ success |
+------------------+----------------------------+----------+
| Cloud SQL        | my-database                | ✅ success |
+------------------+----------------------------+----------+

SKIPPED RESOURCES:
+------------------+----------------------------+---------------+
| Resource Type    | Name                       | Reason        |
+==================+============================+===============+
| Storage Bucket   | important-data-bucket      | ⏭️ user-skipped |
+------------------+----------------------------+---------------+

FAILED DELETIONS:
+----------------+------------------+-------------------------------+
| Resource Type  | Name             | Error                         |
+================+==================+===============================+
| Storage Bucket | protected-bucket | ❌ Bucket has deletion protection |
+----------------+------------------+-------------------------------+

SUMMARY STATISTICS:
Total resources deleted: 15
Total resources skipped: 3
Total failed deletions: 1
Resource types with missing permissions: 0
================================================================================
```

## Logging

The script logs all operations to both the console and a timestamped log file:

```
gcp_cleanup_20250418_123045.log
```

## Error Handling

The script handles various error scenarios:

- Missing environment variables
- Authentication failures
- Missing permissions
- Resource dependencies
- API rate limits
- Network issues

## Best Practices

- Always run with `--dry-run` first to see what would be deleted
- Ensure your access token has the minimum required permissions
- Consider backing up critical data before running the script
- Use the per-resource confirmation to selectively clean up your project
- Use the "all" option only after reviewing the initial resources
- Run during off-peak hours for large projects

## Limitations

- Cannot restore deleted resources (deletions are permanent)
- Some resources may have dependencies that prevent deletion
- Certain managed services may have additional protection mechanisms
- Only supports access token authentication via environment variable

## License

This script is provided under the MIT License.

## Disclaimer

This utility can permanently delete resources in your GCP project. Always use with caution, particularly in production environments. The authors are not responsible for any data loss or service disruption resulting from the use of this script.
