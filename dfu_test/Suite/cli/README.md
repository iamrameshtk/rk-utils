# Google Cloud Data Fusion CLI Test Cases Documentation

## Overview
This document provides detailed information about all test cases implemented in the Cloud Data Fusion CLI test script. Each test case validates specific functionality of the `gcloud beta data-fusion` commands.

**IMPORTANT**: This test suite is designed for users with **custom role permissions** that include only read operations. All write/update operations are expected to fail due to insufficient permissions.

## Test Environment Requirements
- Google Cloud SDK installed and configured
- Valid GCP Project with Data Fusion API enabled
- Existing Data Fusion instance
- User with a custom IAM role containing only read permissions for Data Fusion

## Permission Model
The test script assumes the executing user has a **custom role with read-only permissions**, which allows:
- ✅ Read operations (list, describe, get)
- ❌ Write operations (create, update, delete, restart)
- ❌ IAM modifications (add/remove bindings, set policies)

### Example Custom Role Definition
```yaml
title: "Data Fusion Read Only"
description: "Custom role for read-only access to Data Fusion instances"
stage: "GA"
includedPermissions:
- datafusion.instances.get
- datafusion.instances.list
- datafusion.operations.get
- datafusion.operations.list
- datafusion.instances.getIamPolicy
```

## Test Cases Summary

| Test ID | Test Case Name | Command Category | Description | Expected Result | Permission Required |
|---------|----------------|------------------|-------------|-----------------|---------------------|
| TC001 | Check gcloud installation | Environment | Verifies gcloud CLI is installed and accessible | PASS | None |
| TC002 | Set project | Environment | Sets the GCP project context | PASS | None |
| TC003 | Check Data Fusion API | API Status | Verifies Data Fusion API is enabled | PASS | Viewer |
| TC004 | List instances | Instance Management | Lists all Data Fusion instances in location | PASS | Viewer |
| TC005 | Describe instance | Instance Management | Gets detailed information about specific instance | PASS | Viewer |
| TC006 | Get IAM policy | Security | Retrieves IAM policy for the instance | PASS | Viewer |
| TC007 | List operations | Operations | Lists all operations in the location | PASS | Viewer |
| TC008 | Update instance labels | Instance Management | Adds test label to instance | **EXPECTED_FAIL** | Editor/Admin |
| TC009 | Update instance options | Instance Management | Updates instance configuration options | **EXPECTED_FAIL** | Editor/Admin |
| TC010 | Restart instance | Instance Management | Initiates instance restart | **EXPECTED_FAIL** | Editor/Admin |
| TC011 | Wait for restart | Operations | Skipped - restart won't happen | N/A | N/A |
| TC012 | Enable Stackdriver logging | Monitoring | Enables Cloud Logging for instance | **EXPECTED_FAIL** | Editor/Admin |
| TC013 | Enable Stackdriver monitoring | Monitoring | Enables Cloud Monitoring for instance | **EXPECTED_FAIL** | Editor/Admin |
| TC014 | Update instance description | Instance Management | Updates instance description field | **EXPECTED_FAIL** | Editor/Admin |
| TC015 | Add IAM policy binding | Security | Adds viewer role to test user | **EXPECTED_FAIL** | Admin |
| TC016 | Remove IAM policy binding | Security | Removes viewer role from test user | **EXPECTED_FAIL** | Admin |
| TC017 | Get API endpoint | Instance Info | Retrieves CDAP API endpoint URL | PASS | Viewer |
| TC018 | Get service endpoint | Instance Info | Retrieves service endpoint URL | PASS | Viewer |
| TC019 | Get instance state | Instance Info | Checks current instance state | PASS | Viewer |
| TC020 | Get instance version | Instance Info | Gets current Data Fusion version | PASS | Viewer |
| TC021 | List available versions | Instance Info | Lists available upgrade versions | PASS | Viewer |
| TC022 | Get instance type | Instance Info | Gets instance type (BASIC/ENTERPRISE) | PASS | Viewer |
| TC023 | Get private instance status | Instance Info | Checks if instance is private | PASS | Viewer |
| TC024 | Get network config | Instance Info | Retrieves network configuration | PASS | Viewer |
| TC025 | Update instance zone | Instance Management | Attempts to update instance zone | **EXPECTED_FAIL** | Editor/Admin |
| TC026 | Clear instance labels | Instance Management | Removes all labels from instance | **EXPECTED_FAIL** | Editor/Admin |
| TC027 | List operations with filter | Operations | Lists operations filtered by instance | PASS | Viewer |
| TC028 | Describe latest operation | Operations | Gets details of most recent operation | EXPECTED_FAIL | Viewer |
| TC029 | Set IAM policy from file | Security | Sets complete IAM policy from JSON | **EXPECTED_FAIL** | Admin |
| TC030 | Get instance creation time | Instance Info | Retrieves instance creation timestamp | PASS | Viewer |

## Command Categories by Permission Level

### ✅ Custom Role Read Permissions (Expected to PASS)
These commands only read information and don't modify any resources:

1. **Instance Information**
   - `gcloud beta data-fusion instances list`
   - `gcloud beta data-fusion instances describe`

2. **IAM Policy Reading**
   - `gcloud beta data-fusion get-iam-policy`

3. **Operations Listing**
   - `gcloud beta data-fusion operations list`
   - `gcloud beta data-fusion operations describe`

### ❌ Write Permissions Required (Expected to FAIL)
These commands modify resources and require write permissions not included in the custom read-only role:

1. **Instance Management**
   - `gcloud beta data-fusion instances create`
   - `gcloud beta data-fusion instances update`
   - `gcloud beta data-fusion instances delete`
   - `gcloud beta data-fusion instances restart`

2. **IAM Policy Modification**
   - `gcloud beta data-fusion set-iam-policy`
   - `gcloud beta data-fusion add-iam-policy-binding`
   - `gcloud beta data-fusion remove-iam-policy-binding`

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

## Expected Test Results for Custom Role Permissions

### Success Criteria
With custom read-only role permissions, the test is considered successful when:
- All read-only commands (list, describe, get) execute successfully
- All write/update commands fail with permission denied errors
- No unexpected failures occur for read operations
- Success rate = (PASS + EXPECTED_FAIL) / Total Tests

### Expected Results Summary
- **~15 tests should PASS** (all read operations)
- **~15 tests should EXPECTED_FAIL** (all write operations)
- **0 tests should FAIL** (unexpected failures indicate issues)

### Permission Error Messages
When running with custom read-only role permissions, expect error messages like:
- `ERROR: (gcloud.beta.data-fusion.instances.update) PERMISSION_DENIED`
- `User does not have permission to access instance`
- `Request had insufficient authentication scopes`
- `Missing required permissions: datafusion.instances.update`

## Troubleshooting Guide for Custom Role Permissions

### Common Issues and Solutions

1. **Unexpected PASS for Update Commands**
   - Issue: Update command succeeded when it should have failed
   - Cause: Custom role includes write permissions
   - Solution: Review custom role definition and remove write permissions

2. **Read Commands Failing**
   - Issue: List/Describe commands fail with permission errors
   - Cause: Custom role missing required read permissions
   - Solution: Add missing permissions like `datafusion.instances.get` to custom role

3. **Authentication Errors on All Commands**
   - Issue: All commands fail with authentication errors
   - Cause: Not properly authenticated
   - Solution: Run `gcloud auth login` and ensure correct account

4. **Custom Role Not Found**
   - Issue: IAM policy shows role doesn't exist
   - Cause: Custom role not created or wrong project
   - Solution: Create custom role with: `gcloud iam roles create`

## IAM Roles and Custom Roles Reference

### Predefined Roles
| Role | Permissions | Test Impact |
|------|-------------|-------------|
| `roles/datafusion.viewer` | Read-only access to instances | Only read operations pass |
| `roles/datafusion.editor` | Read/write access, no IAM | Most operations pass except IAM |
| `roles/datafusion.admin` | Full access including IAM | All operations pass |

### Custom Role Example for This Test
```bash
# Create a custom read-only role
gcloud iam roles create dataFusionReadOnly \
    --project=PROJECT_ID \
    --title="Data Fusion Read Only" \
    --description="Custom role for read-only Data Fusion access" \
    --permissions=datafusion.instances.get,datafusion.instances.list,datafusion.operations.get,datafusion.operations.list,datafusion.instances.getIamPolicy

# Grant the custom role to a user
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member=user:EMAIL@example.com \
    --role=projects/PROJECT_ID/roles/dataFusionReadOnly
```

## Best Practices for Custom Role Testing

1. **Define Minimal Permissions**: Include only necessary read permissions in custom role
2. **Document Custom Role**: Keep track of what permissions are included
3. **Expected Failure Handling**: The script marks write operations as expected failures
4. **Focus on Read Operations**: Custom read-only roles are meant for monitoring and inspection
5. **Success Rate Calculation**: Includes both PASS and EXPECTED_FAIL in success rate
6. **Use for Validation**: Perfect for validating read access and instance health
7. **Regular Review**: Periodically review custom role permissions for security

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

## Reporting with Custom Role Permissions

The test script generates multiple output formats optimized for custom read-only role scenarios:

1. **CSV File**: Machine-readable test results with EXPECTED_FAIL status for write operations
2. **HTML Report**: Human-readable test report with color coding:
   - Green: Successful read operations (PASS)
   - Yellow: Expected failures for write operations (EXPECTED_FAIL)
   - Red: Unexpected failures (FAIL)
3. **Log File**: Detailed execution logs showing permission denied errors
4. **Summary File**: High-level summary showing success rate including expected failures

### Sample Test Summary Output
```
Test Results:
-------------
Total Tests Executed: 30
Passed (Read Operations): 15
Failed (Unexpected): 0
Expected Failures (Write Operations): 15
Success Rate: 100.0%

Note: Success rate includes both PASS and EXPECTED_FAIL results.
Write operations are expected to fail with custom role read-only permissions.
```

## Version Compatibility

- Requires gcloud SDK version 300.0.0 or later
- Compatible with Cloud Data Fusion versions 6.x and above
- Beta commands may change in future releases
