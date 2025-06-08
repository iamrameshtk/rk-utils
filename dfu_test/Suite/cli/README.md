# Google Cloud Data Fusion CLI Test Suite

## Overview

This comprehensive test suite validates all available `gcloud beta data-fusion` CLI commands. It's specifically designed for users with **custom IAM roles containing only read permissions**, making it ideal for:

- Validating Data Fusion instance accessibility
- Testing custom IAM role configurations
- Monitoring instance health and status
- Compliance and security auditing
- Automated testing in CI/CD pipelines

## Key Features

- **Cross-Platform Compatible**: Works on Linux, macOS, and BSD systems
- **Custom Role Support**: Designed for read-only custom IAM roles
- **Comprehensive Testing**: Tests 30+ different CLI commands
- **Multiple Output Formats**: CSV, HTML, detailed logs, and summary reports
- **Expected Failure Handling**: Properly handles permission-denied scenarios
- **Color-Coded Console Output**: Visual feedback during execution
- **Detailed Timing**: Tracks execution time for each command
- **Performance Optimized**: Uses `--async` flag for faster test execution

## Prerequisites

1. **Google Cloud SDK**: Installed and configured
   ```bash
   # Install Google Cloud SDK
   curl https://sdk.cloud.google.com | bash
   ```

2. **Authentication**: Logged into gcloud
   ```bash
   gcloud auth login
   ```

3. **Data Fusion API**: Enabled in your project
   ```bash
   gcloud services enable datafusion.googleapis.com
   ```

4. **Custom IAM Role**: User must have a custom role with read-only permissions
   ```bash
   # Example custom role creation
   gcloud iam roles create dataFusionReadOnly \
       --project=PROJECT_ID \
       --title="Data Fusion Read Only" \
       --permissions=datafusion.instances.get,datafusion.instances.list,datafusion.operations.get,datafusion.operations.list,datafusion.instances.getIamPolicy
   ```

## Installation

1. Download the test script:
   ```bash
   wget https://your-repo/datafusion-cli-test.sh
   # or
   curl -O https://your-repo/datafusion-cli-test.sh
   ```

2. Make it executable:
   ```bash
   chmod +x datafusion-cli-test.sh
   ```

## Usage

### Basic Usage
```bash
./datafusion-cli-test.sh -p PROJECT_ID -l LOCATION -i INSTANCE_NAME
```

### With Custom Namespace
```bash
./datafusion-cli-test.sh -p PROJECT_ID -l LOCATION -i INSTANCE_NAME -n NAMESPACE
```

### Parameters
- `-p PROJECT_ID`: Your GCP Project ID (required)
- `-l LOCATION`: Region/Location (required, e.g., us-central1, europe-west1)
- `-i INSTANCE_NAME`: Data Fusion instance name (required)
- `-n NAMESPACE`: Namespace (optional, default: "default")
- `-h`: Display help message

### Examples
```bash
# Test instance in us-central1
./datafusion-cli-test.sh -p my-project-123 -l us-central1 -i production-etl

# Test with custom namespace
./datafusion-cli-test.sh -p my-project-123 -l europe-west1 -i dev-instance -n development
```

## Understanding the Test Framework

### The "true" Parameter Explained

You might notice some test commands have `"true"` at the end:

```bash
execute_test "TC009" "Update instance options" "gcloud beta data-fusion instances update..." "true"
```

**Important**: The `"true"` is **NOT** part of the gcloud command! It's a parameter for our test framework.

#### How `execute_test` Works:

```bash
execute_test "TEST_ID" "TEST_NAME" "COMMAND" "EXPECTED_TO_FAIL"
#             $1        $2          $3         $4
```

- **Parameter 1**: Test case ID
- **Parameter 2**: Human-readable test name
- **Parameter 3**: The actual gcloud command
- **Parameter 4**: `"true"` if we expect the command to fail, omitted otherwise

#### Why This Matters:

With read-only permissions:
- ✅ **Read operations** should succeed → No `"true"` parameter
- ❌ **Write operations** should fail → Include `"true"` parameter

This allows us to verify that permissions are working correctly!

### Test Result Statuses

| Status | Description | Counts as Success? |
|--------|-------------|-------------------|
| PASS | Command succeeded as expected | ✅ Yes |
| EXPECTED_FAIL | Command failed as expected (permissions working) | ✅ Yes |
| FAIL | Command failed unexpectedly | ❌ No |
| UNEXPECTED_PASS | Command succeeded but should have failed | ❌ No |

## Test Cases Overview

### Read Operations (Should PASS)
- List all instances
- Describe instance details
- Get IAM policies
- List operations
- Retrieve instance properties (version, endpoints, state)

### Write Operations (Should EXPECTED_FAIL)
- Update instance configurations
- Modify labels
- Restart instances
- Enable logging/monitoring
- Modify IAM policies

See the full test case documentation for detailed information about all 30 test cases.

## Output Files

The script generates multiple output files in a timestamped directory:

```
data_fusion_test_results_YYYYMMDD_HHMMSS/
├── data_fusion_test_TIMESTAMP.log          # Detailed execution log
├── data_fusion_test_results_TIMESTAMP.csv  # Machine-readable results
├── test_report_TIMESTAMP.html              # Visual HTML report
└── test_summary_TIMESTAMP.txt              # Executive summary
```

### CSV Format
```csv
Test Case ID,Test Case Name,Command,Status,Execution Time,Output,Error Message,Timestamp
TC001,Check gcloud installation,gcloud version,PASS,1,Google Cloud SDK 450.0.0,,(timestamp)
TC008,Update instance labels,gcloud beta data-fusion instances update...,EXPECTED_FAIL,2,,PERMISSION_DENIED,(timestamp)
```

### HTML Report
- Color-coded results (Green=PASS, Yellow=EXPECTED_FAIL, Red=FAIL)
- Sortable table with all test details
- Summary statistics at the top

## Success Criteria

With custom read-only role permissions:
- **Expected**: ~15 PASS (reads) + ~15 EXPECTED_FAIL (writes) = 100% success rate
- **Success Rate Formula**: (PASS + EXPECTED_FAIL) / Total Tests × 100%

## Troubleshooting

### Common Issues

1. **"date: illegal option -- d" Error**
   - **Fixed in v1.3**: Script now uses cross-platform date calculations

2. **All Commands Failing with Auth Errors**
   - Run: `gcloud auth login`
   - Verify: `gcloud config get-value account`

3. **Permission Denied on Read Operations**
   - Check role permissions: `gcloud iam roles describe dataFusionReadOnly --project=PROJECT_ID`
   - Ensure role includes: `datafusion.instances.get`, `datafusion.instances.list`

4. **Write Commands Unexpectedly Passing**
   - User has more than read permissions
   - Verify: `gcloud projects get-iam-policy PROJECT_ID --flatten="bindings[].members" --filter="bindings.members:user:YOUR_EMAIL"`

5. **Instance Not Found**
   - Verify instance exists: `gcloud beta data-fusion instances list --location=LOCATION`
   - Check instance name spelling

## Custom Role Configuration

### Minimal Read-Only Role
```yaml
title: "Data Fusion Read Only"
description: "Custom role for read-only access to Data Fusion"
stage: "GA"
includedPermissions:
- datafusion.instances.get
- datafusion.instances.list
- datafusion.operations.get
- datafusion.operations.list
- datafusion.instances.getIamPolicy
```

### Create and Assign Role
```bash
# Create the role
gcloud iam roles create dataFusionReadOnly \
    --project=PROJECT_ID \
    --file=role-definition.yaml

# Grant to user
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member=user:test-user@example.com \
    --role=projects/PROJECT_ID/roles/dataFusionReadOnly
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Data Fusion Access Test
on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 8 AM

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: google-github-actions/setup-gcloud@v0
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
      - run: |
          ./datafusion-cli-test.sh \
            -p ${{ secrets.PROJECT_ID }} \
            -l us-central1 \
            -i production-instance
```

### Jenkins Pipeline Example
```groovy
pipeline {
    agent any
    stages {
        stage('Test Data Fusion Access') {
            steps {
                sh '''
                    ./datafusion-cli-test.sh \
                        -p ${PROJECT_ID} \
                        -l ${LOCATION} \
                        -i ${INSTANCE_NAME}
                '''
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'data_fusion_test_results_*/*'
            publishHTML([
                reportDir: 'data_fusion_test_results_*',
                reportFiles: 'test_report_*.html',
                reportName: 'Data Fusion Test Report'
            ])
        }
    }
}
```

## Advanced Usage

### Testing Multiple Instances
```bash
#!/bin/bash
INSTANCES=("prod-etl" "dev-etl" "staging-etl")
LOCATION="us-central1"
PROJECT="my-project-123"

for instance in "${INSTANCES[@]}"; do
    echo "Testing instance: $instance"
    ./datafusion-cli-test.sh -p $PROJECT -l $LOCATION -i $instance
done
```

### Custom Success Criteria
Modify the script to check specific success rates:
```bash
if [ $(echo "$SUCCESS_RATE < 95" | bc) -eq 1 ]; then
    echo "ERROR: Success rate below threshold"
    exit 1
fi
```

## Version History

- **v1.4**: Added `--async` flag to all long-running operations for faster execution
- **v1.3**: Cross-platform compatibility (Linux/macOS/BSD)
- **v1.2**: Custom role permissions support
- **v1.1**: Viewer permissions design
- **v1.0**: Initial release

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on multiple platforms
5. Submit a pull request

## License

This script is provided under the Apache License 2.0.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the test case documentation
3. Submit an issue on GitHub
4. Contact your Cloud Support team

## Best Practices

1. **Run Regularly**: Schedule weekly tests to ensure continuous access
2. **Monitor Trends**: Track execution times for performance degradation
3. **Review Failures**: Investigate any unexpected failures immediately
4. **Update Permissions**: Keep custom roles aligned with your needs
5. **Archive Results**: Keep test results for compliance auditing

---

**Note**: This test suite is designed for validation and monitoring purposes. It does not modify any Data Fusion resources when run with appropriate read-only permissions.
