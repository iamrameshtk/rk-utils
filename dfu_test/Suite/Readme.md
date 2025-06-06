# Google Cloud Data Fusion API Testing Suite

A comprehensive Python-based testing framework for Google Cloud Data Fusion APIs with automated test case execution, detailed reporting, and CSV export capabilities.

## 📋 Overview

This testing suite provides two specialized scripts for comprehensive Data Fusion API validation:

1. **Main Operations Script** (`data_fusion_main.py`) - Core instance and pipeline operations
2. **Namespace & System Admin Script** (`data_fusion_namespace_system.py`) - Administrative operations

## 🚀 Features

- **Comprehensive API Coverage**: Tests all major Data Fusion operations
- **Automated Test Execution**: Pass/Fail tracking with detailed results
- **CSV Report Generation**: Exportable results with timestamps and metrics
- **Tabulated Output**: Formatted console display for easy reading
- **Operation Type Categorization**: Organized by operation types for better analysis
- **Error Handling**: Detailed error tracking and debugging information
- **High-level Validation**: Basic health checks without complex validations

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

# Generate auth token (required before each script run)
export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)
```

## 📊 Operation Types

### Main Operations Script
| Type | Description | Test Count |
|------|-------------|------------|
| **Instance Level Operation** | Instance lifecycle management | 6 tests |
| **Pipeline Level Operation** | Pipeline deployment and management | 5 tests |
| **Pipeline Level Execution** | Pipeline runtime operations | 4 tests |
| **Compute Profile Operation** | Compute profile management | 5 tests |
| **Security Operation** | Security and access control | 4 tests |

### Namespace & System Admin Script
| Type | Description | Test Count |
|------|-------------|------------|
| **Instance Level Operation** | Basic instance information | 2 tests |
| **Namespace Level Operation** | Namespace management | 6 tests |
| **System Admin Level Operation** | System monitoring and config | 6 tests |
| **System Admin Level Execution** | Administrative actions | 2 tests |

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

## 📈 Example Output

### Console Output
```
=== Google Cloud Data Fusion Main API Testing Suite ===

✓ List instances test passed
✓ Get non-existent instance test passed (expected failure)
✓ Delete non-existent instance test passed (expected failure)
✓ Get existing instance 'my-instance' test passed
✓ Get CDAP client for 'my-instance' test passed
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

### Tabulated Results Display
```
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
                                                    MAIN DATA FUSION API TEST RESULTS SUMMARY
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
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
   Total Tests: 24
   Passed: 22 ✓
   Failed: 2 ✗
   Success Rate: 91.7%
   Average Execution Time: 0.456s

📋 TEST CATEGORIES:
   Instance Level Operations: 6
   Pipeline Level Operations: 8
   Compute Profile Operations: 5
   Security Operations: 4
   Other Operations: 1
```

### CSV Report Structure

The generated CSV files contain the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| `test_case` | Unique test identifier | `LIST_INSTANCES` |
| `api_endpoint` | Full API endpoint URL | `https://datafusion.googleapis.com/v1beta1/projects/...` |
| `method` | HTTP method | `GET`, `POST`, `PUT`, `DELETE` |
| `description` | Human-readable test description | `List all Data Fusion instances in project` |
| `type` | Operation category | `Instance Level Operation` |
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
```

## 🔧 Test Scenarios

### Main Operations Script Tests

#### Instance Level Operations
- ✅ **LIST_INSTANCES**: List all instances in project/location
- ✅ **GET_INSTANCE**: Retrieve specific instance details
- ✅ **CREATE_INSTANCE**: Create new Data Fusion instance
- ✅ **UPDATE_INSTANCE**: Update instance configuration
- ✅ **DELETE_INSTANCE**: Delete Data Fusion instance
- ✅ **RESTART_INSTANCE**: Restart instance

#### Pipeline Level Operations
- ✅ **LIST_PIPELINES**: List pipelines in namespace
- ✅ **DEPLOY_PIPELINE**: Deploy new pipeline using PUT
- ✅ **GET_PIPELINE**: Retrieve pipeline details
- ✅ **UPDATE_PIPELINE**: Update pipeline configuration
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
- ✅ **UPDATE_COMPUTE_PROFILE**: Update profile configuration
- ✅ **DELETE_COMPUTE_PROFILE**: Delete compute profile

#### Security Operations
- ✅ **LIST_SECURE_KEYS**: List secure keys in namespace
- ✅ **CREATE_SECURE_KEY**: Create secure key using PUT
- ✅ **GET_SECURE_KEY_METADATA**: Retrieve key metadata
- ✅ **DELETE_SECURE_KEY**: Delete secure key

### Namespace & System Admin Script Tests

#### Namespace Level Operations
- ✅ **LIST_NAMESPACES**: List all namespaces
- ✅ **CREATE_NAMESPACE**: Create new namespace using PUT
- ✅ **GET_NAMESPACE**: Retrieve namespace details
- ✅ **DELETE_NAMESPACE**: Delete namespace
- ✅ **UPDATE_NAMESPACE_PREFERENCES**: Update namespace preferences
- ✅ **GET_NAMESPACE_PREFERENCES**: Retrieve namespace preferences

#### System Admin Level Operations
- ✅ **GET_SYSTEM_SERVICES**: Retrieve system services status
- ✅ **GET_SYSTEM_SERVICE_STATUS**: Get specific service status
- ✅ **GET_SYSTEM_CONFIG**: Retrieve system configuration
- ✅ **UPDATE_SYSTEM_CONFIG**: Update system configuration
- ✅ **GET_SYSTEM_ARTIFACTS**: List system artifacts
- ✅ **GET_SYSTEM_METRICS**: Retrieve system metrics

#### System Admin Level Execution
- ✅ **RESTART_SYSTEM_SERVICE**: Restart system service
- ✅ **UPDATE_SYSTEM_CONFIG**: Update system-wide settings

## 🎯 Example API Calls

### Instance Management
```python
# Create Data Fusion instance
manager.create_instance("my-instance", "BASIC", "Production instance")

# List all instances
instances = manager.list_instances()

# Get instance details
instance_details = manager.instance_client.get_instance("my-instance")
```

### Pipeline Operations
```python
# Deploy a batch pipeline
pipeline_config = {
    "name": "data-processing-pipeline",
    "artifact": {
        "name": "cdap-data-pipeline",
        "version": "6.10.0",
        "scope": "system"
    },
    "config": {
        "stages": [...],
        "connections": [...],
        "engine": "spark"
    }
}

cdap_client.deploy_pipeline("default", "my-pipeline", pipeline_config)

# Start pipeline execution
cdap_client.start_batch_pipeline("default", "my-pipeline")
```

### Compute Profile Management
```python
# Create Dataproc compute profile
profile_config = {
    "label": "Production Dataproc Profile",
    "description": "High-performance compute profile",
    "provisioner": {
        "name": "gcp-dataproc",
        "properties": [
            {"name": "projectId", "value": "my-project"},
            {"name": "region", "value": "us-central1"},
            {"name": "masterInstanceType", "value": "n1-standard-4"},
            {"name": "workerInstanceType", "value": "n1-standard-4"},
            {"name": "numWorkers", "value": "3"}
        ]
    }
}

cdap_client.create_compute_profile("default", "prod-profile", profile_config)
```

### Security Management
```python
# Create secure key for database connection
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

cdap_client.create_secure_key("default", "prod-db-key", key_data)
```

### Namespace Management
```python
# Create namespace with preferences
preferences = {
    "system.log.level": "INFO",
    "system.namespace.scheduler.max.thread.pool.size": "10",
    "app.deploy.timeout.seconds": "300"
}

client.create_namespace("analytics", {"description": "Analytics workspace"})
client.update_namespace_preferences("analytics", preferences)
```

### System Administration
```python
# Get system health
health = manager.get_system_health("my-instance")
print(f"System Status: {health['overall_status']}")

# Restart system services
services_to_restart = ["appfabric", "dataset.service"]
results = manager.restart_system_services("my-instance", services_to_restart)
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
        "services": {"status": "HEALTHY", "count": 8},
        "configuration": {"status": "HEALTHY", "accessible": True},
        "artifacts": {"status": "HEALTHY", "count": 15},
        "metrics": {"status": "HEALTHY", "accessible": True}
    }
}
```

## 🚨 Troubleshooting

### Common Issues

#### Authentication Errors
```bash
# Error: GOOGLE_AUTH_TOKEN environment variable must be set
export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)

# Error: Token expired
gcloud auth login
export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)
```

#### API Access Issues
```bash
# Enable Data Fusion API
gcloud services enable datafusion.googleapis.com

# Check project permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID
```

#### Instance Not Found
```python
# Verify instance exists and is in correct location
instances = manager.list_instances()
print([inst['name'] for inst in instances])
```

### Error Categories in Reports

| Error Type | Description | Common Causes |
|------------|-------------|---------------|
| `401 Unauthorized` | Authentication failure | Expired token, insufficient permissions |
| `403 Forbidden` | Access denied | Missing IAM roles, API not enabled |
| `404 Not Found` | Resource doesn't exist | Wrong instance name, deleted resource |
| `409 Conflict` | Resource already exists | Duplicate names, concurrent operations |
| `500 Internal Server Error` | Server-side error | Service outage, invalid configuration |

## 📊 Report Analysis

### Success Rate Interpretation
- **90-100%**: Excellent - All core operations working
- **80-89%**: Good - Minor issues, investigate failures
- **70-79%**: Fair - Significant issues need attention
- **Below 70%**: Poor - Major problems, check configuration

### Performance Benchmarks
- **Instance Operations**: < 2 seconds
- **Pipeline Operations**: < 5 seconds
- **System Operations**: < 3 seconds
- **Execution Operations**: < 10 seconds

## 🔐 Security Best Practices

1. **Token Management**
   - Rotate auth tokens regularly
   - Use service accounts for automation
   - Never commit tokens to version control

2. **Access Control**
   - Follow principle of least privilege
   - Use IAM roles appropriately
   - Monitor API usage

3. **Data Protection**
   - Encrypt sensitive data in secure keys
   - Use appropriate key rotation policies
   - Audit access to secure storage

## 📝 Contributing

### Adding New Test Cases
1. Add test method to appropriate class
2. Update operation type categorization
3. Include proper error handling
4. Update documentation

### Extending Functionality
1. Follow existing patterns for API calls
2. Include comprehensive test coverage
3. Update CSV report structure if needed
4. Add examples to README

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review Google Cloud Data Fusion documentation
3. Check Google Cloud status page
4. Contact your GCP support team

## 📚 Additional Resources

- [Google Cloud Data Fusion Documentation](https://cloud.google.com/data-fusion/docs)
- [CDAP Documentation](https://cdap.atlassian.net/wiki/spaces/DOCS/)
- [Google Cloud API Reference](https://cloud.google.com/data-fusion/docs/reference/rest)
- [Google Cloud CLI Documentation](https://cloud.google.com/sdk/gcloud)

---

**Last Updated**: December 6, 2024  
**Version**: 2.0  
**Compatibility**: Google Cloud Data Fusion API v1beta1, CDAP v6.10+
