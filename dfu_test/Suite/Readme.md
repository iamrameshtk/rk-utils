# Google Cloud Data Fusion API Testing Suite

A comprehensive Python-based testing framework for Google Cloud Data Fusion APIs with automated test case execution, detailed reporting, and CSV export capabilities with service-level status monitoring.

## 📋 Overview

This testing suite provides two specialized scripts for comprehensive Data Fusion API validation:

1. **Main Operations Script** (`gcp_data_fusion_cp_and_dp.py`) - Core instance and pipeline operations
2. **Namespace & System Admin Script** (`gcp_data_fusion_namespace_system.py`) - Administrative operations with detailed service monitoring

Both scripts feature complete test automation, CSV reporting, tabulated output with operation type categorization, and **duplicate entry prevention** for clean reports.

## 🚀 Features

- **Comprehensive API Coverage**: Tests all major Data Fusion operations across 40+ endpoints
- **Complete CRUD Operations**: Full Create, Read, Update, Delete functionality for namespaces and system admin
- **Service-Level Status Monitoring**: Detailed service health reporting with individual service status
- **Duplicate Prevention**: Ensures no duplicate test entries in reports
- **Google Documentation Compliance**: Parameter naming follows Google Cloud/CDAP standards
- **Automated Test Execution**: Pass/Fail tracking with detailed results and timing metrics
- **CSV Report Generation**: Exportable results with timestamps, error details, and service status
- **Tabulated Output**: Formatted console display with operation type classification
- **Operation Type Categorization**: Organized by 8 distinct operation types for better analysis
- **Error Handling**: Detailed error tracking and debugging information
- **Enhanced Service Reporting**: Individual service names and health status in reports

## 📁 Project Structure

```
data-fusion-testing-suite/
├── gcp_data_fusion_cp_and_dp.py         # Main operations script
├── gcp_data_fusion_namespace_system.py  # Namespace & system admin script (enhanced)
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

Create a `requirements.txt` file:
```txt
requests>=2.25.0
tabulate>=0.8.9
google-auth>=2.0.0
google-auth-oauthlib>=0.4.0
google-auth-httplib2>=0.1.0
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

### Script 1: Main Operations (`gcp_data_fusion_cp_and_dp.py`)
| Type | Description | Test Count | Key Operations |
|------|-------------|------------|----------------|
| **Instance Level Operation** | Instance lifecycle management | 6 tests | CREATE, GET, UPDATE, DELETE, LIST, RESTART |
| **Pipeline Level Operation** | Pipeline deployment and management | 5 tests | DEPLOY, GET, UPDATE, DELETE, LIST |
| **Pipeline Level Execution** | Pipeline runtime operations | 5 tests | START/STOP (batch/realtime), GET_RUNS |
| **Compute Profile Operation** | Compute profile management | 5 tests | CREATE, GET, UPDATE, DELETE, LIST |
| **Security Operation** | Security and access control | 4 tests | CREATE, GET, DELETE secure keys, LIST |

**Total: 25 Test Cases** (No duplicates)

### Script 2: Namespace & System Admin (`gcp_data_fusion_namespace_system.py`) - **Enhanced**
| Type | Description | Test Count | Key Operations | Service Status |
|------|-------------|------------|----------------|----------------|
| **Instance Level Operation** | Basic instance information | 2 tests | GET, LIST instances | N/A |
| **Namespace Level Operation** | Complete namespace CRUD | 6 tests | CREATE, GET, DELETE, LIST, UPDATE/GET preferences | N/A |
| **System Admin Level Operation** | System monitoring and config | 7 tests | GET services/config/artifacts/metrics, SERVICE_STATUS | ✅ Individual service health |
| **System Admin Level Execution** | Administrative actions | 2 tests | RESTART_SERVICE, UPDATE_CONFIG | ✅ Service restart status |

**Total: 17 Test Cases** (Enhanced with service details)

**Combined Total: 42 Test Cases**

## 🔧 Enhanced Features in Latest Version

### **1. Complete CRUD Operations**
All namespace and system admin operations now include full Create, Read, Update, Delete functionality:

```python
# Namespace CRUD
✅ CREATE_NAMESPACE - Create namespaces with configuration
✅ GET_NAMESPACE - Retrieve namespace details  
✅ UPDATE_NAMESPACE_PREFERENCES - Update namespace settings
✅ DELETE_NAMESPACE - Delete namespaces completely
✅ LIST_NAMESPACES - List all namespaces

# System Admin CRUD  
✅ UPDATE_SYSTEM_CONFIG - Update system configuration
✅ RESTART_SERVICE - Restart individual services
✅ GET_SYSTEM_SERVICES - Get all system services with status
```

### **2. Google Documentation Compliance**
Parameter naming updated to match Google Cloud/CDAP standards:

| Operation | Old Parameter | New Parameter | Compliance |
|-----------|---------------|---------------|------------|
| Namespace Operations | `namespace_name` | `namespace_id` | ✅ CDAP standard |
| System Configuration | `config` | `config_properties` | ✅ Clear naming |
| Service Operations | Basic response | Enhanced with service details | ✅ Detailed status |

### **3. Service-Level Status Monitoring**
Enhanced service status reporting with individual service details:

```python
# Enhanced service status response
{
    "service_name": "appfabric",
    "status_details": {"status": "OK", "description": "Service running"},
    "is_healthy": True
}

# Health validation with service breakdown
{
    "overall_status": "HEALTHY",
    "service_details": {
        "appfabric": {"status": "HEALTHY", "service_name": "appfabric"},
        "dataset.service": {"status": "HEALTHY", "service_name": "dataset.service"}
    },
    "healthy_services": 2,
    "unhealthy_services": 0
}
```

### **4. Duplicate Prevention**
Both scripts now include duplicate test case prevention:

```python
# Duplicate check in _make_request methods
existing_test = next((r for r in self.config.test_results if r.test_case == test_case), None)
if existing_test:
    print(f"Skipping duplicate test case: {test_case}")
    return None, existing_test
```

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
python gcp_data_fusion_cp_and_dp.py
```

### Running the Enhanced Namespace & System Admin Script

```bash
# Set authentication token  
export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)

# Run namespace and system admin tests with service monitoring
python gcp_data_fusion_namespace_system.py
```

## 📈 Example Outputs

### Console Output - Enhanced Namespace & System Admin Script
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
✓ Get system services test passed
✓ Get system configuration test passed
✓ Get system artifacts test passed
✓ Get system metrics test passed
✓ Get appfabric service status test passed (Status: HEALTHY)
✓ Get dataset.service service status test passed (Status: HEALTHY)
✓ Update system configuration test passed

✓ System health validation test passed (Overall Status: HEALTHY)
  - Service 'appfabric': HEALTHY
  - Service 'dataset.service': HEALTHY
  - Service 'metadata.service': HEALTHY

✓ System services validation test passed (Status: HEALTHY)
  - Healthy Services: 3, Unhealthy Services: 0

📄 CSV report generated: data_fusion_namespace_system_test_results_20241206_151234.csv

🔍 ADDITIONAL INSIGHTS FOR INSTANCE: my-datafusion-instance
   System Health: HEALTHY
   - Services: HEALTHY
   - Configuration: HEALTHY
   - Artifacts: HEALTHY
   Service Details:
   - appfabric: HEALTHY
   - dataset.service: HEALTHY
   - metadata.service: HEALTHY
```

### Enhanced Tabulated Results with Service Status
```
══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
                                                 NAMESPACE & SYSTEM ADMIN API TEST RESULTS SUMMARY
══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
┌─────────────────────────────┬────────┬─────────────────────┬────────┬──────┬─────────┬─────────────────────────────────────────────┐
│ Test Case                   │ Method │ Type                │ Status │ Code │ Time    │ Description                                 │
├─────────────────────────────┼────────┼─────────────────────┼────────┼──────┼─────────┼─────────────────────────────────────────────┤
│ LIST_NAMESPACES             │ GET    │ Namespace Level...  │ PASS   │ 200  │ 0.123s  │ List all available namespaces               │
│ CREATE_NAMESPACE_test-ns... │ PUT    │ Namespace Level...  │ PASS   │ 200  │ 0.456s  │ Create namespace 'test-ns-123' with config │
│ DELETE_NAMESPACE_test-ns... │ DELETE │ Namespace Level...  │ PASS   │ 200  │ 0.234s  │ Delete namespace 'test-ns-123' and content │
│ GET_SERVICE_STATUS_appfa... │ GET    │ System Admin Level..│ PASS   │ 200  │ 0.189s  │ Get status for service 'appfabric': HEALTHY │
│ GET_SERVICE_STATUS_datase...│ GET    │ System Admin Level..│ PASS   │ 200  │ 0.145s  │ Get status for service 'dataset.service':.. │
│ UPDATE_SYSTEM_CONFIG        │ PUT    │ System Admin Level..│ PASS   │ 200  │ 0.267s  │ Update system-wide configuration properties │
└─────────────────────────────┴────────┴─────────────────────┴────────┴──────┴─────────┴─────────────────────────────────────────────┘

📊 SUMMARY STATISTICS:
   Total Tests: 17
   Passed: 17 ✓
   Failed: 0 ✗
   Success Rate: 100.0%
   Average Execution Time: 0.234s

📋 TEST CATEGORIES:
   Namespace Level Operations: 6
   System Admin Level Operations: 9
   Instance Level Operations: 2
   Other Operations: 0

🔍 SERVICE HEALTH SUMMARY:
   Healthy Services: 3
   Unhealthy Services: 0
   Error Services: 0
   Overall System Status: HEALTHY
```

### Enhanced CSV Report Structure

The CSV files now include enhanced service status information:

| Column | Description | Example |
|--------|-------------|---------|
| `test_case` | Unique test identifier | `GET_SERVICE_STATUS_appfabric` |
| `api_endpoint` | Full API endpoint URL | `https://instance-api/v3/system/services/appfabric/status` |
| `method` | HTTP method | `GET`, `POST`, `PUT`, `DELETE` |
| `description` | **Enhanced with service status** | `Get status for service 'appfabric': checking if service is running and healthy` |
| `type` | **Operation category** | `System Admin Level Operation` |
| `status` | Test result | `PASS` or `FAIL` |
| `response_code` | HTTP response code | `200`, `404`, `500` |
| `response_message` | HTTP response message | `OK`, `Not Found`, `Internal Server Error` |
| `execution_time` | Test duration | `0.456s` |
| `timestamp` | ISO timestamp | `2024-12-06T14:30:52.123456` |
| `error_details` | Error information (if failed) | Detailed error message |

### Sample Enhanced CSV Output
```csv
test_case,api_endpoint,method,description,type,status,response_code,response_message,execution_time,timestamp,error_details
LIST_NAMESPACES,https://instance-api/v3/namespaces,GET,List all available namespaces,Namespace Level Operation,PASS,200,OK,0.123s,2024-12-06T14:30:52.123456,
CREATE_NAMESPACE_test-ns-123,https://instance-api/v3/namespaces/test-ns-123,PUT,Create namespace 'test-ns-123' with configuration,Namespace Level Operation,PASS,200,OK,0.456s,2024-12-06T14:30:53.123456,
GET_SERVICE_STATUS_appfabric,https://instance-api/v3/system/services/appfabric/status,GET,Get status for service 'appfabric': checking if service is running and healthy,System Admin Level Operation,PASS,200,OK,0.189s,2024-12-06T14:30:54.123456,
UPDATE_SYSTEM_CONFIG,https://instance-api/v3/system/config,PUT,Update system-wide configuration properties,System Admin Level Operation,PASS,200,OK,0.267s,2024-12-06T14:30:55.123456,
```

## 🔧 Detailed Test Scenarios

### Enhanced Namespace & System Admin Script Tests

#### Namespace Level Operations (Complete CRUD)
- ✅ **LIST_NAMESPACES**: List all namespaces in CDAP instance
- ✅ **CREATE_NAMESPACE**: Create new namespace with configuration using PUT
- ✅ **GET_NAMESPACE**: Retrieve specific namespace details
- ✅ **DELETE_NAMESPACE**: Delete namespace and all its contents
- ✅ **UPDATE_NAMESPACE_PREFERENCES**: Update namespace preferences using PUT
- ✅ **GET_NAMESPACE_PREFERENCES**: Retrieve namespace preferences

#### System Admin Level Operations (Enhanced with Service Details)
- ✅ **GET_SYSTEM_SERVICES**: Retrieve all system services status
- ✅ **GET_SERVICE_STATUS_{service}**: Get individual service status with health info
  - `appfabric` - Core application framework service
  - `dataset.service` - Dataset management service  
  - `metadata.service` - Metadata management service
- ✅ **GET_SYSTEM_CONFIG**: Retrieve system configuration
- ✅ **UPDATE_SYSTEM_CONFIG**: Update system configuration using PUT
- ✅ **GET_SYSTEM_ARTIFACTS**: List system-level artifacts
- ✅ **GET_SYSTEM_METRICS**: Retrieve system performance metrics

#### System Admin Level Execution
- ✅ **RESTART_SERVICE_{service}**: Restart individual system services
- ✅ **UPDATE_SYSTEM_CONFIG**: Update system-wide settings

## 🎯 Enhanced API Call Examples

### Complete Namespace CRUD with Google Standards
```python
# Create namespace with proper parameter naming (namespace_id)
namespace_config = {
    "description": "Analytics workspace for data processing",
    "config": {
        "scheduler.max.thread.pool.size": "10"
    }
}
client.create_namespace("analytics", namespace_config)  # Using namespace_id

# Update namespace preferences with PUT
preferences = {
    "system.log.level": "INFO",
    "system.namespace.scheduler.max.thread.pool.size": "10",
    "app.deploy.timeout.seconds": "300"
}
client.update_namespace_preferences("analytics", preferences)

# Delete namespace completely
client.delete_namespace("analytics")
```

### Enhanced System Administration with Service Monitoring
```python
# Get detailed service status with health information
service_status = client.get_system_service_status("appfabric")
print(f"Service: {service_status['service_name']}")
print(f"Healthy: {service_status['is_healthy']}")
print(f"Details: {service_status['status_details']}")

# Update system configuration with proper parameter naming
config_properties = {
    "system.log.level": "DEBUG",
    "test.config.property": "test-value"
}
client.update_system_configuration(config_properties)

# Get comprehensive system health with service breakdown
health = manager.get_system_health_with_services("my-instance")
print(f"Overall Status: {health['overall_status']}")
for service, details in health['service_details'].items():
    print(f"  {service}: {details['status']}")
```

### Detailed Service Validation
```python
# Validate system services with detailed breakdown
validation = manager.validate_system_services_detailed("my-instance")
print(f"Overall Status: {validation['overall_status']}")
print(f"Healthy Services: {validation['healthy_services']}")
print(f"Unhealthy Services: {validation['unhealthy_services']}")

# Individual service details
for service_name, details in validation['services'].items():
    print(f"Service '{details['service_name']}': {details['status']}")
    if details.get('is_running'):
        print(f"  Running: Yes")
```

## 🔍 Enhanced Health Validation

### Namespace Health Check with Details
```python
health_status = manager.validate_namespace_health("my-instance", "default")
# Returns:
{
    "namespace_id": "default",
    "exists": True,
    "preferences_accessible": True,
    "status": "HEALTHY",
    "namespace_info": {...},
    "preferences_count": 5
}
```

### System Health with Service Breakdown
```python
system_health = manager.get_system_health_with_services("my-instance")
# Returns:
{
    "instance": "my-instance",
    "overall_status": "HEALTHY",
    "components": {
        "services": {"status": "HEALTHY", "total_services": 8},
        "configuration": {"status": "HEALTHY", "config_keys": 25},
        "artifacts": {"status": "HEALTHY", "artifact_count": 15}
    },
    "service_details": {
        "appfabric": {
            "status": "HEALTHY",
            "service_name": "appfabric",
            "details": {"status": "OK", "description": "Service running"}
        },
        "dataset.service": {
            "status": "HEALTHY", 
            "service_name": "dataset.service",
            "details": {"status": "OK", "description": "Service running"}
        }
    }
}
```

### Detailed Service Validation
```python
service_validation = manager.validate_system_services_detailed("my-instance")
# Returns:
{
    "overall_status": "HEALTHY",
    "services": {
        "appfabric": {
            "service_name": "appfabric",
            "status": "HEALTHY",
            "is_running": True,
            "details": {"status": "OK"}
        }
    },
    "healthy_services": 3,
    "unhealthy_services": 0,
    "error_services": 0
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

#### Service Status Issues
```bash
# Check if Data Fusion instance is ACTIVE
gcloud data-fusion instances describe your-instance-name \
    --location=us-central1 \
    --format="value(state)"

# Verify API endpoint accessibility
gcloud data-fusion instances describe your-instance-name \
    --location=us-central1 \
    --format="value(apiEndpoint)"
```

#### Duplicate Test Entries
The latest version automatically prevents duplicate test entries:
```
Skipping duplicate test case: GET_SYSTEM_SERVICES
```

### Error Categories in Enhanced Reports

| Error Type | Description | Service Impact | Solution |
|------------|-------------|----------------|----------|
| `401 Unauthorized` | Authentication failure | All services affected | Refresh token, check IAM roles |
| `403 Forbidden` | Access denied | Specific services | Enable API, add proper roles |
| `404 Not Found` | Resource doesn't exist | Service unavailable | Verify resource names, check instance state |
| `500 Internal Server Error` | Server-side error | Service down | Check GCP status, restart service |
| `503 Service Unavailable` | Service temporarily down | Individual service | Restart specific service |

### Required IAM Roles

```bash
# Minimum required roles for complete testing
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:your-email@domain.com" \
    --role="roles/datafusion.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:your-email@domain.com" \
    --role="roles/iam.serviceAccountUser"

# For system configuration updates
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:your-email@domain.com" \
    --role="roles/datafusion.instanceAdmin"
```

## 📊 Performance Benchmarks & Analysis

### Expected Performance
- **Instance Operations**: < 2 seconds
- **Namespace Operations**: < 1 second  
- **Pipeline Operations**: < 5 seconds  
- **System Operations**: < 3 seconds
- **Service Status Checks**: < 1 second per service
- **System Configuration Updates**: < 2 seconds

### Success Rate Interpretation
- **95-100%**: Excellent - All systems operational, all services healthy
- **85-94%**: Good - Minor issues, some services may be unhealthy  
- **70-84%**: Fair - Significant issues, multiple services down
- **Below 70%**: Poor - Major problems, system health compromised

### Service Health Analysis
- **All Services Healthy**: System running optimally
- **1-2 Services Unhealthy**: Monitor and investigate specific services
- **3+ Services Unhealthy**: System instability, immediate attention required
- **Services in ERROR state**: Configuration or connectivity issues

## 🔐 Security Best Practices

### 1. Token Management
```bash
# Use short-lived tokens for interactive testing
export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)

# For automation, use service account keys
gcloud iam service-accounts create datafusion-tester \
    --display-name="Data Fusion API Tester"

gcloud iam service-accounts keys create key.json \
    --iam-account=datafusion-tester@PROJECT_ID.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
```

### 2. Safe Testing Practices
- **Test namespace creation/deletion** in non-production environments
- **System configuration updates** should be minimal and reversible
- **Service restarts** should be performed during maintenance windows
- **Monitor service health** after any configuration changes

### 3. Data Protection
- Namespace preferences may contain sensitive configuration
- System configuration updates should be reviewed before applying
- Service status information should be treated as internal monitoring data

## 📝 Advanced Usage

### Custom Service Monitoring
```python
# Monitor specific services
services_to_monitor = ["appfabric", "dataset.service", "metadata.service", "metrics"]
for service in services_to_monitor:
    status = client.get_system_service_status(service)
    if not status.get("is_healthy", False):
        print(f"ALERT: Service {service} is unhealthy!")
        # Trigger restart if needed
        client.restart_system_service(service)
```

### Batch Namespace Management
```python
# Create multiple namespaces with configurations
namespaces_config = {
    "analytics": {"description": "Analytics workspace"},
    "development": {"description": "Development environment"},
    "testing": {"description": "Testing environment"}
}

for namespace_id, config in namespaces_config.items():
    try:
        client.create_namespace(namespace_id, config)
        print(f"✓ Created namespace: {namespace_id}")
    except Exception as e:
        print(f"✗ Failed to create {namespace_id}: {e}")
```

### System Health Monitoring Dashboard
```python
def generate_health_dashboard(instance_name):
    """Generate a comprehensive health dashboard"""
    health = manager.get_system_health_with_services(instance_name)
    
    print("="*60)
    print(f"SYSTEM HEALTH DASHBOARD - {instance_name}")
    print("="*60)
    print(f"Overall Status: {health['overall_status']}")
    print(f"Timestamp: {health['timestamp']}")
    
    print("\nCOMPONENT STATUS:")
    for component, details in health['components'].items():
        print(f"  {component.title()}: {details['status']}")
    
    print("\nSERVICE STATUS:")
    for service, details in health['service_details'].items():
        print(f"  {details['service_name']}: {details['status']}")
    
    print("="*60)
```

## 📚 API Method Usage Summary

### Enhanced PUT Methods (Create/Update Operations)
- **CREATE_NAMESPACE**: Create namespaces with Google-compliant parameter naming
- **UPDATE_NAMESPACE_PREFERENCES**: Configure namespace-specific settings
- **UPDATE_SYSTEM_CONFIG**: Update system-wide configuration properties
- **DEPLOY_PIPELINE**: Deploy or update pipeline configurations (Main script)
- **CREATE_COMPUTE_PROFILE**: Create compute profiles (Main script)
- **CREATE_SECURE_KEY**: Store secure credentials (Main script)

### Enhanced GET Methods (Read Operations with Service Details)
- **GET_SYSTEM_SERVICES**: List all system services with status overview
- **GET_SERVICE_STATUS_{service}**: Get detailed individual service health status
- **GET_NAMESPACE**: Retrieve namespace details with proper parameter naming
- **GET_NAMESPACE_PREFERENCES**: Get namespace-specific configuration
- **GET_SYSTEM_CONFIG**: Retrieve system configuration properties
- **GET_SYSTEM_ARTIFACTS**: List system-level artifacts
- **GET_SYSTEM_METRICS**: Get system performance metrics

### POST Methods (Action Operations)
- **RESTART_SERVICE_{service}**: Restart individual system services with status feedback
- **CREATE_INSTANCE**: Create new Data Fusion instances (Main script)
- **START_BATCH_PIPELINE**: Execute batch pipelines (Main script)
- **STOP_BATCH_PIPELINE**: Stop pipeline execution (Main script)

### DELETE Methods (Remove Operations)
- **DELETE_NAMESPACE**: Remove namespaces and all contents completely
- **DELETE_INSTANCE**: Remove Data Fusion instances (Main script)
- **DELETE_PIPELINE**: Remove deployed pipelines (Main script)
- **DELETE_COMPUTE_PROFILE**: Remove compute profiles (Main script)

## 🤝 Contributing

### Adding New Test Cases
1. Add test method to appropriate class (`TestRunner`)
2. Update operation type categorization
3. Include proper error handling with try/catch
4. **Ensure no duplicate test case names**
5. **Follow Google documentation parameter naming**
6. **Include service status details where applicable**

### Extending Service Monitoring
1. Add new services to monitoring lists
2. Update health validation methods
3. Include service-specific error handling
4. Update documentation with new service details

### Code Standards
- Use Google-compliant parameter naming (`namespace_id`, `config_properties`)
- Include service status in descriptions for system operations
- Implement duplicate prevention in all request methods
- Add detailed service health information to reports

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Google Cloud Data Fusion documentation
3. Check Google Cloud status page for service issues
4. Verify individual service health using the enhanced monitoring
5. Contact your GCP support team for instance-specific issues

## 📚 Additional Resources

- [Google Cloud Data Fusion Documentation](https://cloud.google.com/data-fusion/docs)
- [CDAP Documentation](https://cdap.atlassian.net/wiki/spaces/DOCS/)
- [Google Cloud API Reference](https://cloud.google.com/data-fusion/docs/reference/rest)
- [CDAP REST API Reference](https://cloud.google.com/data-fusion/docs/reference/cdap-reference)
- [Google Cloud CLI Documentation](https://cloud.google.com/sdk/gcloud)
- [Data Fusion Pricing](https://cloud.google.com/data-fusion/pricing)
- [IAM Roles for Data Fusion](https://cloud.google.com/data-fusion/docs/concepts/iam)
- [CDAP System Services](https://cdap.atlassian.net/wiki/spaces/DOCS/pages/480412235/System+Services)

## 🔧 Latest Updates Summary

### Version 2.2 - Enhanced Service Monitoring & CRUD Operations

**🔑 Key Improvements:**
- ✅ **Complete CRUD Operations** for namespaces and system admin
- ✅ **Google Documentation Compliance** with proper parameter naming
- ✅ **Enhanced Service Status Monitoring** with individual service health
- ✅ **Duplicate Entry Prevention** for clean, unique reports
- ✅ **Detailed Service Breakdown** in health validation reports
- ✅ **Service-Specific Error Handling** and status reporting

**📊 Enhanced Test Coverage:**
- **42 total test cases** across both scripts
- **17 test cases** in namespace & system admin script (enhanced)
- **Service health monitoring** for critical system services
- **Zero duplicate entries** in all reports

---

**Last Updated**: December 6, 2024  
**Version**: 2.2  
**Compatibility**: Google Cloud Data Fusion API v1beta1, CDAP v6.10+  
**Python**: 3.7+  
**Test Coverage**: 42 API endpoints across 8 operation types with service monitoring  
**Special Features**: Service health monitoring, duplicate prevention, Google documentation compliance
