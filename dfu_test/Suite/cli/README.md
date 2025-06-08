# Google Cloud Data Fusion CLI Test Cases Documentation

## Overview
This document provides detailed information about all test cases implemented in the Cloud Data Fusion CLI test script. Each test case validates specific functionality of the `gcloud beta data-fusion` commands.

## Test Environment Requirements
- Google Cloud SDK installed and configured
- Valid GCP Project with Data Fusion API enabled
- Existing Data Fusion instance
- Appropriate IAM permissions

## Test Cases Summary

| Test ID | Test Case Name | Command Category | Description | Expected Result | Notes |
|---------|----------------|------------------|-------------|-----------------|-------|
| TC001 | Check gcloud installation | Environment | Verifies gcloud CLI is installed and accessible | PASS | Prerequisite check |
| TC002 | Set project | Environment | Sets the GCP project context | PASS | Required for subsequent commands |
| TC003 | Check Data Fusion API | API Status | Verifies Data Fusion API is enabled | PASS | Must be enabled for any operations |
| TC004 | List instances | Instance Management | Lists all Data Fusion instances in location | PASS | Returns JSON array of instances |
| TC005 | Describe instance | Instance Management | Gets detailed information about specific instance | PASS | Returns complete instance metadata |
| TC006 | Get IAM policy | Security | Retrieves IAM policy for the instance | PASS | Shows current access permissions |
| TC007 | List operations | Operations | Lists all operations in the location | PASS | Shows ongoing and completed operations |
| TC008 | Update instance labels | Instance Management | Adds test label to instance | PASS | Tests metadata update capability |
| TC009 | Update instance options | Instance Management | Updates instance configuration options | PASS | Tests runtime configuration changes |
| TC010 | Restart instance | Instance Management | Initiates instance restart | PASS | Tests instance lifecycle management |
| TC011 | Wait for restart | Operations | Waits for restart operation to complete | N/A | Ensures instance is ready |
| TC012 | Enable Stackdriver logging | Monitoring | Enables Cloud Logging for instance | PASS | Tests logging configuration |
| TC013 | Enable Stackdriver monitoring | Monitoring | Enables Cloud Monitoring for instance | PASS | Tests monitoring configuration |
| TC014 | Update instance description | Instance Management | Updates instance description field | PASS | Tests metadata modification |
| TC015 | Add IAM policy binding | Security | Adds viewer role to test user | EXPECTED_FAIL | May fail if user doesn't exist |
| TC016 | Remove IAM policy binding | Security | Removes viewer role from test user | EXPECTED_FAIL | May fail if binding doesn't exist |
| TC017 | Get API endpoint | Instance Info | Retrieves CDAP API endpoint URL | PASS | Required for REST API calls |
| TC018 | Get service endpoint | Instance Info | Retrieves service endpoint URL | PASS | UI access endpoint |
| TC019 | Get instance state | Instance Info | Checks current instance state | PASS | Should return RUNNING |
| TC020 | Get instance version | Instance Info | Gets current Data Fusion version | PASS | Version information |
| TC021 | List available versions | Instance Info | Lists available upgrade versions | PASS | For upgrade planning |
| TC022 | Get instance type | Instance Info | Gets instance type (BASIC/ENTERPRISE) | PASS | Instance tier information |
| TC023 | Get private instance status | Instance Info | Checks if instance is private | PASS | Network configuration |
| TC024 | Get network config | Instance Info | Retrieves network configuration | PASS | VPC and network details |
| TC025 | Update instance zone | Instance Management | Attempts to update instance zone | EXPECTED_FAIL | Zone is immutable |
| TC026 | Clear instance labels | Instance Management | Removes all labels from instance | PASS | Cleanup operation |
| TC027 | List operations with filter | Operations | Lists operations filtered by instance | PASS | Filtered operation listing |
| TC028 | Describe latest operation | Operations | Gets details of most recent operation | EXPECTED_FAIL | May fail if no operations |
| TC029 | Set IAM policy from file | Security | Sets complete IAM policy from JSON | EXPECTED_FAIL | Requires valid policy file |
| TC030 | Get instance creation time | Instance Info | Retrieves instance creation timestamp | PASS | Instance age information |

## Command Categories

### 1. Instance Management Commands
- `gcloud beta data-fusion instances list`
- `gcloud beta data-fusion instances describe`
- `gcloud beta data-fusion instances create`
- `gcloud beta data-fusion instances update`
- `gcloud beta data-fusion instances delete`
- `gcloud beta data-fusion instances restart`

### 2. IAM and Security Commands
- `gcloud beta data-fusion get-iam-policy`
- `gcloud beta data-fusion set-iam-policy`
- `gcloud beta data-fusion add-iam-policy-binding`
- `gcloud beta data-fusion remove-iam-policy-binding`

### 3. Operations Commands
- `gcloud beta data-fusion operations list`
- `gcloud beta data-fusion operations describe`

## Common Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| --project | GCP Project ID | my-project-123 |
| --location | Region/Location | us-central1 |
| --format | Output format | json, yaml, value() |
| --filter | Resource filter | name:my-instance |
| --limit | Maximum results | 10 |
| --async | Asynchronous execution | (flag only) |

## Update Command Options

### Labels
- `--update-labels`: Add or update labels
- `--remove-labels`: Remove specific labels
- `--clear-labels`: Remove all labels

### Instance Configuration
- `--description`: Update instance description
- `--enable_stackdriver_logging`: Enable Cloud Logging
- `--enable_stackdriver_monitoring`: Enable Cloud Monitoring
- `--options`: Update CDAP configuration options
- `--version`: Upgrade instance version

### Maintenance Window (if supported)
- `--maintenance-window-start`: Set maintenance window start time
- `--maintenance-window-end`: Set maintenance window end time
- `--maintenance-window-recurrence`: Set maintenance recurrence
- `--clear-maintenance-window`: Remove maintenance window

## Expected Test Results

### Success Criteria
- All core instance management commands execute successfully
- Instance information retrieval works correctly
- Update operations complete without errors
- IAM policy retrieval functions properly

### Known Limitations
- Some IAM operations may fail due to permission constraints
- Zone updates are not supported (immutable field)
- Some operations require specific instance states

## Troubleshooting Guide

### Common Issues and Solutions

1. **Authentication Errors**
   - Ensure `gcloud auth login` has been executed
   - Verify project permissions

2. **API Not Enabled**
   - Enable Data Fusion API: `gcloud services enable datafusion.googleapis.com`

3. **Instance Not Found**
   - Verify instance name and location
   - Check if instance is in RUNNING state

4. **Permission Denied**
   - Ensure user has required IAM roles:
     - `roles/datafusion.admin` or
     - `roles/datafusion.editor` or
     - `roles/datafusion.viewer`

5. **Operation Timeouts**
   - Some operations like restart may take several minutes
   - Use `--async` flag for long-running operations

## Best Practices

1. **Always specify location**: Data Fusion instances are regional resources
2. **Use JSON format**: For programmatic parsing of command outputs
3. **Handle async operations**: Check operation status before proceeding
4. **Implement retries**: For transient failures
5. **Log all operations**: For audit and troubleshooting

## Integration with CDAP REST API

After obtaining the API endpoint using CLI commands, you can interact with CDAP REST APIs:

```bash
# Get API endpoint
export CDAP_ENDPOINT=$(gcloud beta data-fusion instances describe \
  --location=LOCATION \
  --format="value(apiEndpoint)" \
  INSTANCE_NAME)

# Get auth token
export AUTH_TOKEN=$(gcloud auth print-access-token)

# Example: List namespaces
curl -H "Authorization: Bearer ${AUTH_TOKEN}" \
  "${CDAP_ENDPOINT}/v3/namespaces"
```

## Reporting

The test script generates multiple output formats:

1. **CSV File**: Machine-readable test results
2. **HTML Report**: Human-readable test report with formatting
3. **Log File**: Detailed execution logs
4. **Summary File**: High-level test execution summary

## Version Compatibility

- Requires gcloud SDK version 300.0.0 or later
- Compatible with Cloud Data Fusion versions 6.x and above
- Beta commands may change in future releases
