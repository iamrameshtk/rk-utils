# GCP Resource Cleanup Utility

A comprehensive Python utility for cleaning up resources in Google Cloud Platform projects. This script helps you safely delete multiple resource types across your GCP project, with built-in safeguards, detailed logging, and interactive confirmation.

## Features

- **Interactive Interface**: Guided process with clear prompts and explicit confirmation
- **Multiple Authentication Methods**: Support for both GCP Access Tokens and Service Account Tokens
- **Comprehensive Resource Cleanup**: Handles multiple GCP resource types
- **Concurrent Operations**: Uses thread pooling for faster resource deletion
- **Dry Run Mode**: Preview what would be deleted without making any changes
- **Enhanced Logging**: Detailed logs for tracking operations
- **Error Handling**: Robust error catching and reporting
- **Tabular Results**: Clean summary tables of deleted and failed resources

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
- Appropriate GCP permissions to list and delete resources

## Installation

1. Clone or download this script to your local machine
2. Install required dependencies:

```bash
pip install tabulate
```

3. Ensure Google Cloud SDK is installed and available in your PATH

## Usage

### Basic Execution

```bash
python gcp_cleanup.py
```

### Additional Options

```bash
# Dry run mode (list resources without deleting)
python gcp_cleanup.py --dry-run

# Increase concurrent workers (faster deletion)
python gcp_cleanup.py --workers 10

# Enable verbose logging
python gcp_cleanup.py --verbose
```

### Command-line Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--dry-run` | `-d` | List resources without deleting them |
| `--workers` | `-w` | Number of concurrent deletion operations (default: 5) |
| `--verbose` | `-v` | Enable detailed logging |

## Interactive Workflow

When you run the script, it will guide you through the following steps:

1. **Project Selection**: Enter your GCP Project ID
2. **Authentication**: Choose between Access Token or Service Account authentication
3. **Resource Preview**: See a list of resource types that will be affected
4. **Confirmation**: Explicitly confirm before any deletions occur
5. **Execution**: Resources are deleted (or just listed in dry-run mode)
6. **Summary**: View a tabular report of results

## Authentication Methods

The script supports two authentication methods:

1. **GCP Access Token** (Preferred)
   - Temporary token with limited scope
   - Typically used for short-lived operations
   - Less privileged and safer

2. **Service Account Token**
   - JSON key for a service account
   - Typically has broader permissions
   - Used for automated processes

## Security Considerations

- Authentication tokens are handled securely and not stored permanently
- Temporary files are created only when necessary and cleaned up after use
- Passwords/tokens are masked during input
- The script requires explicit confirmation before performing deletions

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

FAILED DELETIONS:
+----------------+------------------+-------------------------------+
| Resource Type  | Name             | Error                         |
+================+==================+===============================+
| Storage Bucket | protected-bucket | ❌ Bucket has deletion protection |
+----------------+------------------+-------------------------------+

SUMMARY STATISTICS:
Total resources deleted: 15
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

- Missing permissions
- Resource dependencies
- API rate limits
- Authentication failures
- Network issues

## Best Practices

- Always run with `--dry-run` first to see what would be deleted
- Use the least privileged token necessary for the operation
- Consider backing up critical data before running the script
- Run during off-peak hours for large projects

## Limitations

- Cannot restore deleted resources (deletions are permanent)
- Some resources may have dependencies that prevent deletion
- Certain managed services may have additional protection mechanisms

## License

This script is provided under the MIT License.

## Disclaimer

This utility can permanently delete resources in your GCP project. Always use with caution, particularly in production environments. The authors are not responsible for any data loss or service disruption resulting from the use of this script.
