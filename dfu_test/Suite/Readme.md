# Google Cloud Data Fusion API Testing Suite

A comprehensive Python-based testing framework for Google Cloud Data Fusion APIs with automated test case execution, detailed reporting, and CSV export capabilities.

## 📋 Overview

This testing suite provides two specialized scripts for comprehensive Data Fusion API validation:

1. **Main Operations Script** (`data_fusion_main.py`) - Core instance and pipeline operations
2. **Namespace & System Admin Script** (`data_fusion_namespace_system.py`) - Administrative operations

Both scripts feature complete test automation, CSV reporting, and tabulated output with operation type categorization.

## 🚀 Features

- **Comprehensive API Coverage**: Tests all major Data Fusion operations across 40+ endpoints
- **Automated Test Execution**: Pass/Fail tracking with detailed results and timing metrics
- **CSV Report Generation**: Exportable results with timestamps, error details, and categorization
- **Tabulated Output**: Formatted console display with operation type classification
- **Operation Type Categorization**: Organized by 8 distinct operation types for better analysis
- **Error Handling**: Detailed error tracking and debugging information
- **High-level Validation**: Basic health checks without complex validations
- **PUT Method Usage**: Proper use of PUT for creating/updating operations as per API specs

## 📁 Project Structure

```
data-fusion-testing-suite/
├── data_fusion_main.py                    # Main operations script
├── data_fusion_namespace_system.py        # Namespace & system admin script
├── README.md                             # This documentation
├── requirements.txt                      # Python dependencies
└── reports/                              # Generated test reports
    ├── data_fusion_main_test_results_*.csv
    └── data_fusion_namespace_system_test_results_*.csv
```

## 🛠️ Prerequisites

### Software Requirements
- Python 3.7+
- Google Cloud CLI (gcloud)
- Valid Google Cloud Project with Data Fusion API enabled
- Existing Data Fusion instance (for full testing)

### Python Dependencies
```bash
pip install requests tabulate google-auth
```

### Authentication Setup
```bash
# Authenticate with Google Cloud
gcloud auth login

# Set your default project
gcloud config set project YOUR_PROJECT_ID

# Enable Data Fusion API (if not already enabled)
gcloud services enable datafusion.googleapis.com

# Generate auth token (required before each script run)
export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)
```

## 📊 Operation Types & Test Coverage

### Script 1: Main Operations (`data_fusion_main.py`)
| Type | Description | Test Count | Key Operations |
|------|-------------|------------|----------------|
| **Instance Level Operation** | Instance lifecycle management | 6 tests | CREATE, GET, UPDATE, DELETE, LIST, RESTART |
| **Pipeline Level Operation** | Pipeline deployment and management | 5 tests | DEPLOY, GET, UPDATE, DELETE, LIST |
| **Pipeline Level Execution** | Pipeline runtime operations | 5 tests | START/STOP (batch/realtime), GET_RUNS |
| **Compute Profile Operation** | Compute profile management | 5 tests | CREATE, GET, UPDATE, DELETE, LIST |
| **Security Operation** | Security and access control | 4 tests | CREATE, GET, DELETE secure keys, LIST |

**Total: 25 Test Cases**

### Script 2: Namespace & System Admin (`data_fusion_namespace_system.py`)
| Type | Description | Test Count | Key Operations |
|------|-------------|------------|----------------|
| **Instance Level Operation** | Basic instance information | 2 tests | GET, LIST instances |
| **Namespace Level Operation** | Namespace management | 6 tests | CREATE, GET, DELETE, LIST, UPDATE/GET preferences |
| **System Admin Level Operation** | System monitoring and config | 6 tests | GET services/config/artifacts/metrics, SERVICE_STATUS |
| **System Admin Level Execution** | Administrative actions | 1 test | RESTART_SERVICE |

**Total: 15 Test Cases**

**Combined Total: 40+ Test Cases**

## 🏃‍♂️ Usage

### Configuration
Update the project configuration in both scripts:

```python
# Configuration (update these values)
PROJECT_ID = "your-project-id"     # Replace with your GCP project ID
LOCATION = "us-central1"          # Replace with your preferred location
```

### Running the Main Operations Script

```bash
# Set authentication token
export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)

# Run main operations tests
python data_fusion_main.py
```

### Running the Namespace & System Admin Script

```bash
# Set authentication token  
export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)

# Run namespace and system admin tests
python data_fusion_namespace_system.py
```

## 📈 Example Outputs

### Console Output - Main Script
```
=== Google Cloud Data Fusion Main API Testing Suite ===

✓ List instances test passed
✓ Get non-existent instance test passed (expected failure)
✓ Delete non-existent instance test passed (expected failure)
✓ Get existing instance 'my-datafusion-instance' test passed
✓ Get CDAP client for 'my-datafusion-instance' test passed
✓ List pipelines test passed
✓ List batch pipelines test passed
✓ List compute profiles test passed
✓ Create compute profile test passed
✓ Get compute profile test passed
✓ Delete compute profile test passed
✓ List secure keys test passed
✓ Create secure key test passed
✓ Get secure key metadata test passed
✓ Delete secure key test passed

📄 CSV report generated: data_fusion_main_test_results_20241206_143052.csv
```

### Console Output - Namespace & System Admin Script
```
=== Google Cloud Data Fusion Namespace & System Admin Testing Suite ===

✓ List instances test passed
✓ List namespaces test passed (found 3 namespaces)
✓ Get default namespace test passed
✓ Get namespace preferences test passed
✓ Create test namespace 'test-namespace-1733515234' test passed
✓ Update namespace preferences test passed
✓ Get updated namespace preferences test passed
✓ Namespace health validation test passed (status: HEALTHY)
✓ Delete test namespace test passed
✓ Get system services test passed (found 8 services)
✓ Get system configuration test passed
✓ Get system artifacts test passed (found 15 artifacts)
✓ Get system metrics test passed
✓ Get appfabric service status test passed
✓ System health validation test passed (status: HEALTHY)
✓ System services validation test passed (status: HEALTHY)
✓ Default namespace health validation test passed (status: HEALTHY)

📄 CSV report generated: data_fusion_namespace_system_test_results_20241206_151234.csv

🔍 ADDITIONAL INSIGHTS FOR INSTANCE: my-datafusion-instance
   System Health: HEALTHY
   - Services: HEALTHY
   - Configuration: HEALTHY
   - Artifacts: HEALTHY
   - Metrics: HEALTHY
```

### Tabulated Results Display
```
══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
                                                           MAIN DATA FUSION API TEST RESULTS SUMMARY
══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
┌─────────────────────────────┬────────┬─────────────────────┬────────┬──────┬─────────┬─────────────────────────────────────────────┐
│ Test Case                   │ Method │ Type                │ Status │ Code │ Time    │ Description                                 │
├─────────────────────────────┼────────┼─────────────────────┼────────┼──────┼─────────┼─────────────────────────────────────────────┤
│ LIST_INSTANCES              │ GET    │ Instance Level...   │ PASS   │ 200  │ 0.245s  │ List all Data Fusion instances in project  │
│ GET_INSTANCE_my-instance    │ GET    │ Instance Level...   │ PASS   │ 200  │ 0.432s  │ Retrieve details for Data Fusion instance  │
│ LIST_PIPELINES_default      │ GET    │ Pipeline Level...   │ PASS   │ 200  │ 0.123s  │ List all pipelines in namespace 'default'  │
│ DEPLOY_PIPELINE_test-pipe   │ PUT    │ Pipeline Level...   │ PASS   │ 200  │ 1.234s  │ Deploy pipeline 'test-pipe' in namespace   │
│ START_BATCH_PIPELINE_test   │ POST   │ Pipeline Level...   │ PASS   │ 200  │ 0.567s  │ Start execution of batch pipeline 'test'   │
│ CREATE_COMPUTE_PROFILE_...  │ PUT    │ Compute Profile...  │ PASS   │ 200  │ 0.789s  │ Create compute profile 'test-profile-123'  │
│ CREATE_SECURE_KEY_test-key  │ PUT    │ Security Operation  │ PASS   │ 200  │ 0.345s  │ Create secure key 'test-key-456' in ns     │
└─────────────────────────────┴────────┴─────────────────────┴────────┴──────┴─────────┴─────────────────────────────────────────────┘

📊 SUMMARY STATISTICS:
   Total Tests: 25
   Passed: 23 ✓
   Failed: 2 ✗
   Success Rate: 92.0%
   Average Execution Time: 0.456s

📋 TEST CATEGORIES:
   Instance Level Operations: 6
   Pipeline Level Operations: 8
   Compute Profile Operations: 5
   Security Operations: 4
   Other Operations: 2
```

### CSV Report Structure

Both scripts generate CSV files with these 11 columns:

| Column | Description | Example |
|--------|-------------|---------|
| `test_case` | Unique test identifier | `LIST_INSTANCES` |
| `api_endpoint` | Full API endpoint URL | `https://datafusion.googleapis.com/v1beta1/...` |
| `method` | HTTP method | `GET`, `POST`, `PUT`, `DELETE` |
| `description` | Human-readable test description | `List all Data Fusion instances in project` |
| `type` | **Operation category** | `Instance Level Operation` |
| `status` | Test result | `PASS` or `FAIL` |
| `response_code` | HTTP response code | `200`, `404`, `500` |
| `response_message` | HTTP response message | `OK`, `Not Found`, `Internal Server Error` |
| `execution_time` | Test duration | `0.456s` |
| `timestamp` | ISO timestamp | `2024-12-06T14:30:52.123456` |
| `error_details` | Error information (if failed) | Detailed error message |

### Sample CSV Output
```csv
test_case,api_endpoint,method,description,type,status,response_code,response_message,execution_time,timestamp,error_details
LIST_INSTANCES,https://datafusion.googleapis.com/v1beta1/projects/my-project/locations/us-central1/instances,GET,List all Data Fusion instances in project 'my-project',Instance Level Operation,PASS,200,OK,0.245s,2024-12-06T14:30:52.123456,
GET_INSTANCE_my-instance,https://datafusion.googleapis.com/v1beta1/projects/my-project/locations/us-central1/instances/my-instance,GET,Retrieve details for Data Fusion instance 'my-instance',Instance Level Operation,PASS,200,OK,0.432s,2024-12-06T14:30:52.567890,
DEPLOY_PIPELINE_test-pipe,https://my-instance-my-project-dot-usc1.datafusion.googleusercontent.com/api/v3/namespaces/default/apps/test-pipe,PUT,Deploy pipeline 'test-pipe' in namespace 'default',Pipeline Level Operation,PASS,200,OK,1.234s,2024-12-06T14:30:53.801234,
LIST_NAMESPACES,https://my-instance-my-project-dot-usc1.datafusion.googleusercontent.com/api/v3/namespaces,GET,List all available namespaces in the CDAP instance,Namespace Level Operation,PASS,200,OK,0.123s,2024-12-06T14:30:54.123456,
```

## 🔧 Detailed Test Scenarios

### Main Operations Script Tests

#### Instance Level Operations
- ✅ **LIST_INSTANCES**: List all instances in project/location
- ✅ **GET_INSTANCE**: Retrieve specific instance details
- ✅ **CREATE_INSTANCE**: Create new Data Fusion instance (commented for safety)
- ✅ **UPDATE_INSTANCE**: Update instance configuration
- ✅ **DELETE_INSTANCE**: Delete Data Fusion instance (tested with non-existent)
- ✅ **RESTART_INSTANCE**: Restart instance

#### Pipeline Level Operations
- ✅ **LIST_PIPELINES**: List pipelines in namespace
- ✅ **DEPLOY_PIPELINE**: Deploy new pipeline using PUT
- ✅ **GET_PIPELINE**: Retrieve pipeline details
- ✅ **UPDATE_PIPELINE**: Update pipeline configuration (redeploy)
- ✅ **DELETE_PIPELINE**: Delete pipeline

#### Pipeline Level Execution
- ✅ **START_BATCH_PIPELINE**: Start batch pipeline execution
- ✅ **STOP_BATCH_PIPELINE**: Stop batch pipeline execution
- ✅ **START_REALTIME_PIPELINE**: Start real-time pipeline execution
- ✅ **STOP_REALTIME_PIPELINE**: Stop real-time pipeline execution
- ✅ **GET_PIPELINE_RUNS**: Retrieve pipeline run history

#### Compute Profile Operations
- ✅ **LIST_COMPUTE_PROFILES**: List compute profiles in namespace
- ✅ **CREATE_COMPUTE_PROFILE**: Create compute profile using PUT
- ✅ **GET_COMPUTE_PROFILE**: Retrieve profile details
- ✅ **UPDATE_COMPUTE_PROFILE**: Update profile configuration using PUT
- ✅ **DELETE_COMPUTE_PROFILE**: Delete compute profile

#### Security Operations
- ✅ **LIST_SECURE_KEYS**: List secure keys in namespace
- ✅ **CREATE_SECURE_KEY**: Create secure key using PUT
- ✅ **GET_SECURE_KEY_METADATA**: Retrieve key metadata
- ✅ **DELETE_SECURE_KEY**: Delete secure key

### Namespace & System Admin Script Tests

#### Instance Level Operations
- ✅ **LIST_INSTANCES**: List all instances for admin access
- ✅ **GET_INSTANCE**: Get instance details for API endpoint

#### Namespace Level Operations
- ✅ **LIST_NAMESPACES**: List all namespaces
- ✅ **CREATE_NAMESPACE**: Create new namespace using PUT
- ✅ **GET_NAMESPACE**: Retrieve namespace details
- ✅ **DELETE_NAMESPACE**: Delete namespace completely
- ✅ **UPDATE_NAMESPACE_PREFERENCES**: Update namespace preferences using PUT
- ✅ **GET_NAMESPACE_PREFERENCES**: Retrieve namespace preferences

#### System Admin Level Operations
- ✅ **GET_SYSTEM_SERVICES**: Retrieve system services status
- ✅ **GET_SYSTEM_SERVICE_STATUS**: Get specific service status
- ✅ **GET_SYSTEM_CONFIG**: Retrieve system configuration
- ✅ **UPDATE_SYSTEM_CONFIG**: Update system configuration using PUT
- ✅ **GET_SYSTEM_ARTIFACTS**: List system artifacts
- ✅ **GET_SYSTEM_METRICS**: Retrieve system metrics

#### System Admin Level Execution
- ✅ **RESTART_SYSTEM_SERVICE**: Restart system service

## 🎯 API Call Examples

### Instance Management
```python
# Create Data Fusion instance
manager.create_instance("my-instance", "BASIC", "Production instance")

# List all instances
instances = manager.list_instances()

# Get instance details
instance_details = manager.instance_client.get_instance("my-instance")
```

### Pipeline Operations with PUT Methods
```python
# Deploy a batch pipeline using PUT
pipeline_config = {
    "name": "data-processing-pipeline",
    "artifact": {
        "name": "cdap-data-pipeline",
        "version": "6.10.0",
        "scope": "system"
    },
    "config": {
        "stages": [
            {
                "name": "Source",
                "plugin": {
                    "name": "File",
                    "type": "batchsource",
                    "properties": {
                        "path": "/data/input.csv",
                        "format": "csv"
                    }
                }
            },
            {
                "name": "Sink",
                "plugin": {
                    "name": "BigQueryTable", 
                    "type": "batchsink",
                    "properties": {
                        "dataset": "analytics",
                        "table": "processed_data"
                    }
                }
            }
        ],
        "connections": [
            {
                "from": "Source",
                "to": "Sink"
            }
        ],
        "engine": "spark"
    }
}

# Deploy using PUT method
cdap_client.deploy_pipeline("default", "my-pipeline", pipeline_config)

# Start pipeline execution
cdap_client.start_batch_pipeline("default", "my-pipeline")
```

### Compute Profile Management with PUT
```python
# Create Dataproc compute profile using PUT
profile_config = {
    "label": "Production Dataproc Profile",
    "description": "High-performance compute profile for production workloads",
    "provisioner": {
        "name": "gcp-dataproc",
        "properties": [
            {"name": "projectId", "value": "my-project"},
            {"name": "region", "value": "us-central1"},
            {"name": "zone", "value": "us-central1-a"},
            {"name": "masterInstanceType", "value": "n1-standard-4"},
            {"name": "workerInstanceType", "value": "n1-standard-4"},
            {"name": "numWorkers", "value": "3"},
            {"name": "network", "value": "default"},
            {"name": "diskSizeGb", "value": "100"},
            {"name": "stackdriverLoggingEnabled", "value": "true"},
            {"name": "stackdriverMonitoringEnabled", "value": "true"}
        ]
    }
}

# Create using PUT method
cdap_client.create_compute_profile("default", "prod-profile", profile_config)
```

### Security Management with PUT
```python
# Create secure key for database connection using PUT
key_data = {
    "description": "Production database credentials",
    "data": json.dumps({
        "connectionString": "jdbc:mysql://prod-db:3306/analytics",
        "username": "analytics_user",
        "password": "secure_password"
    }),
    "properties": {
        "type": "database-credentials",
        "environment": "production"
    }
}

# Create using PUT method
cdap_client.create_secure_key("default", "prod-db-key", key_data)
```

### Namespace Management with PUT
```python
# Create namespace with preferences using PUT
namespace_config = {
    "description": "Analytics workspace for data processing"
}

# Create namespace using PUT
client.create_namespace("analytics", namespace_config)

# Update preferences using PUT
preferences = {
    "system.log.level": "INFO",
    "system.namespace.scheduler.max.thread.pool.size": "10",
    "app.deploy.timeout.seconds": "300",
    "dataset.table.prefix": "analytics_"
}

# Update using PUT method
client.update_namespace_preferences("analytics", preferences)
```

### System Administration
```python
# Get comprehensive system health
health = manager.get_system_health("my-instance")
print(f"System Status: {health['overall_status']}")

# Restart multiple system services
services_to_restart = ["appfabric", "dataset.service"]
results = manager.restart_system_services("my-instance", services_to_restart)

# Validate system services
validation = manager.validate_system_services("my-instance")
print(f"Service Validation: {validation['overall_status']}")
```

## 🔍 Health Validation Examples

### Namespace Health Check
```python
health_status = manager.validate_namespace_health("my-instance", "default")
# Returns:
{
    "namespace": "default",
    "exists": True,
    "preferences_accessible": True,
    "status": "HEALTHY"
}
```

### System Health Validation
```python
system_health = manager.get_system_health("my-instance")
# Returns:
{
    "instance": "my-instance",
    "timestamp": "2024-12-06T14:30:52.123456",
    "overall_status": "HEALTHY",
    "components": {
        "services": {"status": "HEALTHY", "count": 8, "data": [...]},
        "configuration": {"status": "HEALTHY", "accessible": True, "data": {...}},
        "artifacts": {"status": "HEALTHY", "count": 15, "data": [...]},
        "metrics": {"status": "HEALTHY", "accessible": True, "data": {...}}
    }
}
```

### System Services Validation
```python
service_validation = manager.validate_system_services("my-instance")
# Returns:
{
    "timestamp": "2024-12-06T14:30:52.123456",
    "services": {
        "appfabric": {"status": "HEALTHY", "data": {...}},
        "dataset.service": {"status": "HEALTHY", "data": {...}},
        "metadata.service": {"status": "HEALTHY", "data": {...}},
        "metrics": {"status": "HEALTHY", "data": {...}},
        "streams": {"status": "HEALTHY", "data": {...}}
    },
    "overall_status": "HEALTHY"
}
```

## 🚨 Troubleshooting

### Common Issues

#### Authentication Errors
```bash
# Error: GOOGLE_AUTH_TOKEN environment variable must be set
export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)

# Error: Token expired (tokens expire after 1 hour)
gcloud auth login
export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)

# Error: Insufficient permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:your-email@domain.com" \
    --role="roles/datafusion.admin"
```

#### API Access Issues
```bash
# Enable Data Fusion API
gcloud services enable datafusion.googleapis.com

# Check project permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID

# List available instances
gcloud data-fusion instances list --location=us-central1
```

#### Instance Not Found
```python
# Verify instance exists and is in correct location
instances = manager.list_instances()
print([inst['name'] for inst in instances])

# Check instance state
instance_details = manager.instance_client.get_instance("your-instance-name")
print(f"Instance state: {instance_details.get('state')}")
```

#### CDAP Endpoint Issues
```bash
# Ensure instance is ACTIVE
gcloud data-fusion instances describe your-instance-name \
    --location=us-central1 \
    --format="value(state)"

# Get API endpoint manually
gcloud data-fusion instances describe your-instance-name \
    --location=us-central1 \
    --format="value(apiEndpoint)"
```

### Error Categories in Reports

| Error Type | Description | Common Causes | Solution |
|------------|-------------|---------------|----------|
| `401 Unauthorized` | Authentication failure | Expired token, insufficient permissions | Refresh token, check IAM roles |
| `403 Forbidden` | Access denied | Missing IAM roles, API not enabled | Enable API, add proper roles |
| `404 Not Found` | Resource doesn't exist | Wrong instance name, deleted resource | Verify resource names |
| `409 Conflict` | Resource already exists | Duplicate names, concurrent operations | Use unique names |
| `500 Internal Server Error` | Server-side error | Service outage, invalid configuration | Check GCP status, retry |

### Required IAM Roles

```bash
# Minimum required roles for testing
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:your-email@domain.com" \
    --role="roles/datafusion.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:your-email@domain.com" \
    --role="roles/iam.serviceAccountUser"
```

## 📊 Performance Benchmarks & Analysis

### Expected Performance
- **Instance Operations**: < 2 seconds
- **Pipeline Operations**: < 5 seconds  
- **System Operations**: < 3 seconds
- **Execution Operations**: < 10 seconds
- **Namespace Operations**: < 1 second

### Success Rate Interpretation
- **95-100%**: Excellent - All systems operational
- **85-94%**: Good - Minor issues, investigate failures  
- **70-84%**: Fair - Significant issues need attention
- **Below 70%**: Poor - Major problems, check configuration

### Performance Analysis Tips
1. **High execution times** may indicate network latency or system load
2. **Frequent 5xx errors** suggest system health issues
3. **Authentication errors** indicate token or permission problems
4. **Consistent failures** on specific operations suggest configuration issues

## 🔐 Security Best Practices

### 1. Token Management
```bash
# Use short-lived tokens
export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)

# For automation, use service account keys
gcloud iam service-accounts create datafusion-tester
gcloud iam service-accounts keys create key.json \
    --iam-account=datafusion-tester@PROJECT_ID.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
```

### 2. Access Control
- Follow principle of least privilege
- Use specific IAM roles (not Owner/Editor)
- Monitor API usage through Cloud Logging
- Regular permission audits

### 3. Data Protection
- Encrypt sensitive data in secure keys
- Use appropriate key rotation policies
- Audit access to secure storage
- Never commit credentials to version control

## 📝 Advanced Usage

### Custom Test Development
```python
# Add custom test to main script
def _test_custom_operation(self, instance_name: str):
    """Test custom operation"""
    try:
        cdap_client = self.manager.get_cdap_client(instance_name)
        
        # Your custom API call
        result = cdap_client._make_request(
            'GET', '/custom/endpoint',
            'CUSTOM_TEST_CASE',
            'Description of custom test',
            'Custom Operation Type'
        )
        
        print("✓ Custom test passed")
    except Exception as e:
        print(f"✗ Custom test failed: {e}")
```

### Batch Testing Multiple Instances
```python
# Test multiple instances
instances = manager.list_instances()
for instance_data in instances:
    instance_name = instance_data['name'].split('/')[-1]
    print(f"\nTesting instance: {instance_name}")
    
    # Run tests for each instance
    test_runner = TestRunner(manager)
    test_results = test_runner.run_comprehensive_tests()
```

### Custom Report Generation
```python
# Generate custom filtered reports
failed_tests = [r for r in test_results if r.status == "FAIL"]
instance_tests = [r for r in test_results if "Instance Level" in r.type]

# Export specific test categories
ReportGenerator.generate_csv_report(
    failed_tests, 
    "failed_tests_only.csv"
)
```

## 📚 API Method Usage Summary

### PUT Methods (Create/Update Operations)
- **DEPLOY_PIPELINE**: Deploy or update pipeline configurations
- **CREATE_COMPUTE_PROFILE**: Create compute profiles for workload execution
- **UPDATE_COMPUTE_PROFILE**: Update existing compute profile settings
- **CREATE_SECURE_KEY**: Store secure credentials and secrets
- **CREATE_NAMESPACE**: Create new namespaces for organization
- **UPDATE_NAMESPACE_PREFERENCES**: Configure namespace-specific settings
- **UPDATE_SYSTEM_CONFIG**: Update system-wide configuration

### GET Methods (Read Operations) 
- **LIST_INSTANCES**: Retrieve all Data Fusion instances
- **GET_INSTANCE**: Get specific instance details and endpoints
- **LIST_PIPELINES**: List deployed pipelines in namespace
- **GET_PIPELINE**: Retrieve pipeline configuration and status
- **LIST_NAMESPACES**: Get available namespaces
- **GET_SYSTEM_SERVICES**: List all system services and their status

### POST Methods (Action Operations)
- **CREATE_INSTANCE**: Create new Data Fusion instances
- **RESTART_INSTANCE**: Restart Data Fusion instances
- **START_BATCH_PIPELINE**: Execute batch data processing pipelines
- **STOP_BATCH_PIPELINE**: Stop running batch pipelines
- **RESTART_SYSTEM_SERVICE**: Restart specific system services

### DELETE Methods (Remove Operations)
- **DELETE_INSTANCE**: Remove Data Fusion instances
- **DELETE_PIPELINE**: Remove deployed pipelines
- **DELETE_COMPUTE_PROFILE**: Remove compute profiles
- **DELETE_SECURE_KEY**: Remove stored secure credentials
- **DELETE_NAMESPACE**: Remove namespaces and all contents

## 🤝 Contributing

### Adding New Test Cases
1. Add test method to appropriate class (`TestRunner`)
2. Update operation type categorization
3. Include proper error handling with try/catch
4. Update documentation and examples

### Extending Functionality
1. Follow existing patterns for API calls
2. Include comprehensive test coverage
3. Update CSV report structure if needed
4. Add examples to README

### Code Standards
- Use descriptive test case names
- Include operation type classification
- Implement proper error handling
- Add timing metrics for performance analysis

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Google Cloud Data Fusion documentation
3. Check Google Cloud status page for service issues
4. Contact your GCP support team for instance-specific issues

## 📚 Additional Resources

- [Google Cloud Data Fusion Documentation](https://cloud.google.com/data-fusion/docs)
- [CDAP Documentation](https://cdap.atlassian.net/wiki/spaces/DOCS/)
- [Google Cloud API Reference](https://cloud.google.com/data-fusion/docs/reference/rest)
- [Google Cloud CLI Documentation](https://cloud.google.com/sdk/gcloud)
- [Data Fusion Pricing](https://cloud.google.com/data-fusion/pricing)
- [IAM Roles for Data Fusion](https://cloud.google.com/data-fusion/docs/concepts/iam)

## 🔧 Dependencies

Create a `requirements.txt` file:
```txt
requests>=2.25.0
tabulate>=0.8.9
google-auth>=2.0.0
google-auth-oauthlib>=0.4.0
google-auth-httplib2>=0.1.0
```

---

**Last Updated**: December 6, 2024  
**Version**: 2.1  
**Compatibility**: Google Cloud Data Fusion API v1beta1, CDAP v6.10+  
**Python**: 3.7+  
**Test Coverage**: 40+ API endpoints across 8 operation types
