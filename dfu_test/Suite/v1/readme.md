# Google Cloud Data Fusion Testing Scripts

A comprehensive testing suite for Google Cloud Data Fusion APIs, split into two specialized scripts for Control Plane (Instance) and Data Plane (Pipeline) operations.

## 📋 Overview

This testing suite provides automated testing for Google Cloud Data Fusion through two dedicated scripts:

1. **Instance Operations Script** (`gcp_data_fusion_instance_operations.py`) - Tests Control Plane APIs for instance management
2. **Pipeline Operations Script** (`gcp_data_fusion_pipeline_operations.py`) - Tests Data Plane APIs for pipeline, compute profile, and security operations

Both scripts feature command-line parameter support, automated test execution, CSV report generation, and detailed tabulated output.

## 🚀 Features

### Common Features
- ✅ **Command-line Parameter Support**: Accept project, location, and other parameters
- ✅ **Automated Test Execution**: Pass/Fail tracking with detailed results
- ✅ **CSV Report Generation**: Exportable test results with timestamps
- ✅ **Tabulated Output**: Clean, formatted console display
- ✅ **Summary Statistics**: Success rates, execution times, operation breakdowns
- ✅ **Duplicate Prevention**: Each test case runs only once
- ✅ **Error Handling**: Detailed error tracking and expected failure validation

### Instance Operations Script
- **Instance CRUD**: CREATE, GET, UPDATE, DELETE, LIST operations
- **Instance Management**: RESTART operation
- **Optional Instance Creation**: Test actual instance creation with `--create-instance` flag
- **Expected Failure Tests**: Validates error handling for non-existent resources

### Pipeline Operations Script  
- **Pipeline CRUD**: DEPLOY, GET, UPDATE, DELETE, LIST operations
- **Pipeline Execution**: START, STOP, GET_RUNS for batch pipelines
- **Compute Profiles**: Full CRUD operations for compute profiles
- **Security Keys**: Full CRUD operations for secure keys
- **Namespace Support**: Test in different namespaces
- **Cleanup Control**: Skip resource cleanup with `--skip-cleanup` flag

## 📁 Project Structure

```
data-fusion-testing/
├── gcp_data_fusion_instance_operations.py  # Instance-level operations (Control Plane)
├── gcp_data_fusion_pipeline_operations.py  # Pipeline-level operations (Data Plane)
├── README.md                                # This documentation
├── requirements.txt                         # Python dependencies
└── reports/                                 # Generated CSV reports (created automatically)
    ├── data_fusion_instance_operations_*.csv
    └── data_fusion_pipeline_operations_*.csv
```

## 🛠️ Prerequisites

### System Requirements
- Python 3.7 or higher
- Google Cloud CLI (`gcloud`)
- Active Google Cloud Project
- Data Fusion API enabled
- Appropriate IAM permissions

### Required IAM Roles
```bash
# Minimum required roles
roles/datafusion.admin          # For full Data Fusion operations
roles/iam.serviceAccountUser    # For service account operations
```

### Python Dependencies
Create a `requirements.txt` file:
```txt
requests>=2.25.0
tabulate>=0.8.9
google-auth>=2.0.0
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## 🔐 Authentication Setup

### 1. Login to Google Cloud
```bash
gcloud auth login
```

### 2. Set Default Project
```bash
gcloud config set project YOUR_PROJECT_ID
```

### 3. Enable Data Fusion API
```bash
gcloud services enable datafusion.googleapis.com
```

### 4. Generate Authentication Token
```bash
# Required before running scripts (token expires after 1 hour)
export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)
```

## 📊 Usage

### Instance Operations Script

#### Basic Usage
```bash
# Test existing instances only
python gcp_data_fusion_instance_operations.py \
    --project YOUR_PROJECT_ID \
    --location us-central1
```

#### With Instance Creation (WARNING: Incurs Costs!)
```bash
# Include instance creation and deletion test
python gcp_data_fusion_instance_operations.py \
    --project YOUR_PROJECT_ID \
    --location us-central1 \
    --create-instance
```

#### Custom Output File
```bash
# Specify custom CSV output filename
python gcp_data_fusion_instance_operations.py \
    --project YOUR_PROJECT_ID \
    --location us-central1 \
    --output my-instance-report.csv
```

### Pipeline Operations Script

#### Basic Usage
```bash
# Test pipeline operations on default namespace
python gcp_data_fusion_pipeline_operations.py \
    --project YOUR_PROJECT_ID \
    --location us-central1 \
    --instance YOUR_INSTANCE_NAME
```

#### Specific Namespace
```bash
# Test in a specific namespace
python gcp_data_fusion_pipeline_operations.py \
    --project YOUR_PROJECT_ID \
    --location us-central1 \
    --instance YOUR_INSTANCE_NAME \
    --namespace production
```

#### Skip Cleanup
```bash
# Keep test resources after testing
python gcp_data_fusion_pipeline_operations.py \
    --project YOUR_PROJECT_ID \
    --location us-central1 \
    --instance YOUR_INSTANCE_NAME \
    --skip-cleanup
```

#### All Options Combined
```bash
# Full example with all options
python gcp_data_fusion_pipeline_operations.py \
    --project YOUR_PROJECT_ID \
    --location us-central1 \
    --instance YOUR_INSTANCE_NAME \
    --namespace test-namespace \
    --skip-cleanup \
    --output pipeline-test-results.csv
```

## 📈 Test Coverage

### Instance Operations (Control Plane)
| Operation | Method | Description | Expected Result |
|-----------|--------|-------------|-----------------|
| LIST_INSTANCES | GET | List all instances in project/location | PASS |
| GET_INSTANCE | GET | Get specific instance details | PASS for existing |
| UPDATE_INSTANCE | PATCH | Update instance configuration | PASS for existing |
| DELETE_INSTANCE | DELETE | Delete an instance | PASS for existing |
| RESTART_INSTANCE | POST | Restart a running instance | PASS for running |
| CREATE_INSTANCE | POST | Create new instance (optional) | PASS (long-running) |

### Pipeline Operations (Data Plane)
| Category | Operations | Count |
|----------|------------|-------|
| **Pipeline CRUD** | DEPLOY, GET, UPDATE, DELETE, LIST | 5 |
| **Pipeline Execution** | START_BATCH, STOP_BATCH, GET_RUNS | 3 |
| **Compute Profiles** | CREATE, GET, UPDATE, DELETE, LIST | 5 |
| **Security Keys** | CREATE, GET_METADATA, DELETE, LIST | 4 |

## 📊 Output Examples

### Console Output
```
==============================================================
GOOGLE CLOUD DATA FUSION - INSTANCE LEVEL OPERATIONS TEST
==============================================================
Project: my-project
Location: us-central1
Timestamp: 2024-12-06 15:30:45
==============================================================

Testing LIST_INSTANCES...
✓ LIST_INSTANCES passed - found 2 instance(s)
  [1] instance-1 - RUNNING
  [2] instance-2 - CREATING

Testing operations on existing instance: instance-1
✓ GET_INSTANCE_instance-1 passed
  - State: RUNNING
  - Type: BASIC
  - Version: 6.10.0
✓ UPDATE_INSTANCE_instance-1 passed
✓ RESTART_INSTANCE_instance-1 passed

Testing operations on non-existent instance (expected failures)...
✓ GET_INSTANCE_non-existent-instance-12345 failed as expected
✓ UPDATE_INSTANCE_non-existent-instance-12345 failed as expected
✓ DELETE_INSTANCE_non-existent-instance-12345 failed as expected
✓ RESTART_INSTANCE_non-existent-instance-12345 failed as expected

📄 CSV report generated: data_fusion_instance_operations_20241206_153045.csv
```

### Tabulated Results
```
======================================================================
INSTANCE LEVEL OPERATIONS - TEST RESULTS
======================================================================
┌────────────────────────────────┬────────┬────────┬──────┬─────────┬──────────────────────────────────────────────────┐
│ Test Case                      │ Method │ Status │ Code │ Time    │ Description                                      │
├────────────────────────────────┼────────┼────────┼──────┼─────────┼──────────────────────────────────────────────────┤
│ LIST_INSTANCES                 │ GET    │ PASS   │ 200  │ 0.523s  │ List all Data Fusion instances in project 'my... │
│ GET_INSTANCE_instance-1        │ GET    │ PASS   │ 200  │ 0.312s  │ Retrieve details for Data Fusion instance 'in... │
│ UPDATE_INSTANCE_instance-1     │ PATCH  │ PASS   │ 200  │ 0.456s  │ Update Data Fusion instance 'instance-1' conf... │
│ RESTART_INSTANCE_instance-1    │ POST   │ PASS   │ 200  │ 0.789s  │ Restart Data Fusion instance 'instance-1'        │
│ GET_INSTANCE_non-existent-...  │ GET    │ FAIL   │ 404  │ 0.234s  │ Retrieve details for Data Fusion instance 'no... │
└────────────────────────────────┴────────┴────────┴──────┴─────────┴──────────────────────────────────────────────────┘

📊 SUMMARY STATISTICS:
   Total Tests: 8
   Passed: 4 ✓
   Failed: 4 ✗ (expected failures)
   Success Rate: 50.0%
   Average Execution Time: 0.427s

📋 OPERATION BREAKDOWN:
   GET: 3
   LIST: 1
   RESTART: 2
   UPDATE: 2
```

### CSV Report Structure
| Column | Description | Example |
|--------|-------------|---------|
| test_case | Unique test identifier | `GET_INSTANCE_my-instance` |
| api_endpoint | Full API URL | `https://datafusion.googleapis.com/v1beta1/projects/...` |
| method | HTTP method | `GET`, `POST`, `PUT`, `DELETE`, `PATCH` |
| description | Test description | `Retrieve details for Data Fusion instance 'my-instance'` |
| type | Operation category | `Instance Level Operation` |
| status | Test result | `PASS` or `FAIL` |
| response_code | HTTP response code | `200`, `404`, `500` |
| response_message | HTTP response message | `OK`, `Not Found` |
| execution_time | Test duration | `0.523s` |
| timestamp | ISO timestamp | `2024-12-06T15:30:45.123456` |
| error_details | Error info if failed | Detailed error message |

## 🚨 Troubleshooting

### Common Issues

#### 1. Authentication Token Expired
```bash
# Error: 401 Unauthorized
# Solution: Refresh token
export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)
```

#### 2. Missing Permissions
```bash
# Error: 403 Forbidden
# Solution: Add required IAM roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:your-email@domain.com" \
    --role="roles/datafusion.admin"
```

#### 3. Instance Not Found
```bash
# Error: 404 Not Found for pipeline operations
# Solution: Verify instance name and state
gcloud data-fusion instances describe YOUR_INSTANCE_NAME \
    --location=YOUR_LOCATION
```

#### 4. API Not Enabled
```bash
# Error: API datafusion.googleapis.com not enabled
# Solution: Enable the API
gcloud services enable datafusion.googleapis.com
```

### Debugging Tips

1. **Check Instance State**: Ensure instance is `RUNNING` before pipeline tests
2. **Verify API Endpoint**: Instance must have an accessible API endpoint
3. **Token Freshness**: Tokens expire after 1 hour, refresh as needed
4. **Namespace Existence**: Ensure namespace exists before testing
5. **Network Access**: Verify network connectivity to Data Fusion endpoints

## 📊 Performance Expectations

| Operation Type | Expected Time | Notes |
|----------------|---------------|--------|
| Instance LIST/GET | < 1 second | Fast operations |
| Instance UPDATE | 1-3 seconds | Depends on changes |
| Instance RESTART | 2-5 seconds | Initiates restart |
| Instance CREATE | 10-15 minutes | Long-running operation |
| Pipeline CRUD | < 2 seconds | Most operations |
| Compute Profile | < 1 second | Fast operations |
| Security Keys | < 1 second | Fast operations |

## 🔒 Security Best Practices

1. **Token Management**
   - Never commit tokens to version control
   - Refresh tokens regularly
   - Use service accounts for automation

2. **Resource Cleanup**
   - Always clean up test resources unless debugging
   - Use `--skip-cleanup` only when necessary
   - Monitor costs for created resources

3. **Namespace Isolation**
   - Test in dedicated namespaces when possible
   - Avoid testing in production namespaces
   - Clean up test namespaces after use

## 📝 Advanced Usage

### Automation Example
```bash
#!/bin/bash
# Automated testing script

# Set variables
PROJECT_ID="my-project"
LOCATION="us-central1"
INSTANCE="my-instance"

# Refresh token
export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)

# Run instance tests
python gcp_data_fusion_instance_operations.py \
    --project $PROJECT_ID \
    --location $LOCATION \
    --output "instance_report_$(date +%Y%m%d).csv"

# Run pipeline tests
python gcp_data_fusion_pipeline_operations.py \
    --project $PROJECT_ID \
    --location $LOCATION \
    --instance $INSTANCE \
    --output "pipeline_report_$(date +%Y%m%d).csv"

# Check results
echo "Testing completed. Check CSV reports for details."
```

### CI/CD Integration
```yaml
# Example GitHub Actions workflow
name: Data Fusion API Tests

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Run tests
        run: |
          export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)
          python gcp_data_fusion_instance_operations.py --project ${{ vars.PROJECT_ID }} --location ${{ vars.LOCATION }}
          python gcp_data_fusion_pipeline_operations.py --project ${{ vars.PROJECT_ID }} --location ${{ vars.LOCATION }} --instance ${{ vars.INSTANCE }}
```

## 🤝 Contributing

### Adding New Tests
1. Add test method to appropriate `TestRunner` class
2. Use unique test case names
3. Include proper error handling
4. Update documentation

### Code Standards
- Follow PEP 8 style guide
- Add type hints for functions
- Include docstrings for methods
- Handle exceptions gracefully

## 📄 License

These scripts are provided as-is for testing Google Cloud Data Fusion APIs. Use at your own risk and ensure compliance with your organization's policies.

## 📚 Additional Resources

- [Google Cloud Data Fusion Documentation](https://cloud.google.com/data-fusion/docs)
- [Data Fusion API Reference](https://cloud.google.com/data-fusion/docs/reference/rest)
- [CDAP Documentation](https://cdap.atlassian.net/wiki/spaces/DOCS/)
- [Data Fusion Pricing](https://cloud.google.com/data-fusion/pricing)

---

**Version**: 1.0  
**Last Updated**: December 2024  
**Compatibility**: Google Cloud Data Fusion API v1beta1, CDAP v6.10+
