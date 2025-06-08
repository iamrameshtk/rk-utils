#!/usr/bin/env python3
"""
Google Cloud Data Fusion Namespace and System Admin Operations Script

This script provides specialized operations for:
1. Namespace-level management and configuration
2. System administration and monitoring
3. High-level validation and health checks

Features:
- Complete namespace CRUD operations with preferences
- System services monitoring and management
- System configuration and metrics
- Basic validation with simple health checks
- Automated test case execution with Pass/Fail tracking
- CSV report generation with detailed test results
- Tabulated output display for easy reading

Requirements:
- Set GOOGLE_AUTH_TOKEN environment variable with your Google Cloud auth token
- Install required packages: requests, google-auth, tabulate

Usage:
    export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)
    python data_fusion_namespace_system.py
"""

import os
import json
import time
import csv
import requests
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin
from dataclasses import dataclass, field
from datetime import datetime
from tabulate import tabulate


@dataclass
class TestResult:
    """Class to store test case results"""
    test_case: str
    api_endpoint: str
    method: str
    description: str
    type: str  # Operation type (Namespace Level, System Admin Level, etc.)
    status: str  # PASS/FAIL
    response_code: int
    response_message: str
    execution_time: float
    timestamp: str
    error_details: str = ""


@dataclass
class Config:
    """Configuration for Cloud Data Fusion operations"""
    project_id: str
    location: str
    auth_token: str
    base_url: str = "https://datafusion.googleapis.com"
    api_version: str = "v1beta1"
    test_results: List[TestResult] = field(default_factory=list)

    def __post_init__(self):
        if not self.auth_token:
            raise ValueError("GOOGLE_AUTH_TOKEN environment variable must be set")


class CloudDataFusionClient:
    """Client for Google Cloud Data Fusion instance operations"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.auth_token}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, url: str, test_case: str, description: str, operation_type: str = "Instance Level Operation", **kwargs) -> Tuple[requests.Response, TestResult]:
        """Make HTTP request with test case tracking"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            response = self.session.request(method, url, **kwargs)
            execution_time = time.time() - start_time
            
            # Determine status based on response
            status = "PASS" if response.status_code < 400 else "FAIL"
            error_details = "" if status == "PASS" else response.text
            
            test_result = TestResult(
                test_case=test_case,
                api_endpoint=url,
                method=method,
                description=description,
                type=operation_type,
                status=status,
                response_code=response.status_code,
                response_message=response.reason,
                execution_time=execution_time,
                timestamp=timestamp,
                error_details=error_details
            )
            
            self.config.test_results.append(test_result)
            
            # Raise for status to maintain original error handling
            response.raise_for_status()
            return response, test_result
            
        except requests.exceptions.RequestException as e:
            execution_time = time.time() - start_time
            error_details = str(e)
            response_code = getattr(e.response, 'status_code', 0) if hasattr(e, 'response') else 0
            response_message = getattr(e.response, 'reason', 'Request Failed') if hasattr(e, 'response') else 'Request Failed'
            
            test_result = TestResult(
                test_case=test_case,
                api_endpoint=url,
                method=method,
                description=description,
                type=operation_type,
                status="FAIL",
                response_code=response_code,
                response_message=response_message,
                execution_time=execution_time,
                timestamp=timestamp,
                error_details=error_details
            )
            
            self.config.test_results.append(test_result)
            
            print(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            raise

    def get_instance(self, instance_name: str) -> Dict[str, Any]:
        """Get details of a Data Fusion instance"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances/{instance_name}"
        
        print(f"Getting Data Fusion instance: {instance_name}")
        response, _ = self._make_request(
            'GET', url,
            f"GET_INSTANCE_{instance_name}",
            f"Retrieve details for Data Fusion instance '{instance_name}'",
            "Instance Level Operation"
        )
        return response.json()
    
    def list_instances(self) -> List[Dict[str, Any]]:
        """List all Data Fusion instances in the project/location"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances"
        
        print("Listing Data Fusion instances")
        response, _ = self._make_request(
            'GET', url,
            "LIST_INSTANCES",
            f"List all Data Fusion instances in project '{self.config.project_id}' and location '{self.config.location}'",
            "Instance Level Operation"
        )
        result = response.json()
        return result.get('instances', [])
    
    def get_instance_api_endpoint(self, instance_name: str) -> str:
        """Get the CDAP API endpoint for an instance"""
        instance_details = self.get_instance(instance_name)
        api_endpoint = instance_details.get('apiEndpoint')
        if not api_endpoint:
            raise ValueError(f"No API endpoint found for instance {instance_name}")
        return api_endpoint


class NamespaceSystemClient:
    """Client for CDAP namespace and system operations with test case tracking"""
    
    def __init__(self, cdap_endpoint: str, auth_token: str, config: Config):
        self.cdap_endpoint = cdap_endpoint.rstrip('/')
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, test_case: str, description: str, operation_type: str = "Namespace Level Operation", **kwargs) -> Tuple[requests.Response, TestResult]:
        """Make HTTP request with test case tracking"""
        url = f"{self.cdap_endpoint}{endpoint}"
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            response = self.session.request(method, url, **kwargs)
            execution_time = time.time() - start_time
            
            # Determine status based on response
            status = "PASS" if response.status_code < 400 else "FAIL"
            error_details = "" if status == "PASS" else response.text
            
            test_result = TestResult(
                test_case=test_case,
                api_endpoint=url,
                method=method,
                description=description,
                type=operation_type,
                status=status,
                response_code=response.status_code,
                response_message=response.reason,
                execution_time=execution_time,
                timestamp=timestamp,
                error_details=error_details
            )
            
            self.config.test_results.append(test_result)
            
            # Raise for status to maintain original error handling
            response.raise_for_status()
            return response, test_result
            
        except requests.exceptions.RequestException as e:
            execution_time = time.time() - start_time
            error_details = str(e)
            response_code = getattr(e.response, 'status_code', 0) if hasattr(e, 'response') else 0
            response_message = getattr(e.response, 'reason', 'Request Failed') if hasattr(e, 'response') else 'Request Failed'
            
            test_result = TestResult(
                test_case=test_case,
                api_endpoint=url,
                method=method,
                description=description,
                type=operation_type,
                status="FAIL",
                response_code=response_code,
                response_message=response_message,
                execution_time=execution_time,
                timestamp=timestamp,
                error_details=error_details
            )
            
            self.config.test_results.append(test_result)
            
            print(f"CDAP Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            raise

    # =====================================
    # NAMESPACE OPERATIONS
    # =====================================
    
    def list_namespaces(self) -> List[Dict[str, Any]]:
        """List all namespaces"""
        endpoint = "/v3/namespaces"
        
        print("Listing namespaces")
        response, _ = self._make_request(
            'GET', endpoint,
            "LIST_NAMESPACES",
            "List all available namespaces in the CDAP instance",
            "Namespace Level Operation"
        )
        return response.json()
    
    def create_namespace(self, namespace_name: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a namespace using PUT"""
        endpoint = f"/v3/namespaces/{namespace_name}"
        payload = config or {}
        
        print(f"Creating namespace: {namespace_name}")
        response, _ = self._make_request(
            'PUT', endpoint,
            f"CREATE_NAMESPACE_{namespace_name}",
            f"Create new namespace '{namespace_name}' with specified configuration",
            "Namespace Level Operation",
            json=payload
        )
        return response.json() if response.text else {"status": "created"}
    
    def get_namespace(self, namespace_name: str) -> Dict[str, Any]:
        """Get namespace details"""
        endpoint = f"/v3/namespaces/{namespace_name}"
        
        print(f"Getting namespace: {namespace_name}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_NAMESPACE_{namespace_name}",
            f"Retrieve details for namespace '{namespace_name}'",
            "Namespace Level Operation"
        )
        return response.json()
    
    def delete_namespace(self, namespace_name: str) -> Dict[str, Any]:
        """Delete a namespace"""
        endpoint = f"/v3/namespaces/{namespace_name}"
        
        print(f"Deleting namespace: {namespace_name}")
        response, _ = self._make_request(
            'DELETE', endpoint,
            f"DELETE_NAMESPACE_{namespace_name}",
            f"Delete namespace '{namespace_name}' and all its contents",
            "Namespace Level Operation"
        )
        return response.json() if response.text else {"status": "deleted"}
    
    def update_namespace_preferences(self, namespace_name: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update namespace preferences using PUT"""
        endpoint = f"/v3/namespaces/{namespace_name}/preferences"
        
        print(f"Updating preferences for namespace: {namespace_name}")
        response, _ = self._make_request(
            'PUT', endpoint,
            f"UPDATE_NAMESPACE_PREFERENCES_{namespace_name}",
            f"Update preferences/properties for namespace '{namespace_name}'",
            "Namespace Level Operation",
            json=preferences
        )
        return response.json() if response.text else {"status": "updated"}
    
    def get_namespace_preferences(self, namespace_name: str) -> Dict[str, Any]:
        """Get namespace preferences"""
        endpoint = f"/v3/namespaces/{namespace_name}/preferences"
        
        print(f"Getting preferences for namespace: {namespace_name}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_NAMESPACE_PREFERENCES_{namespace_name}",
            f"Retrieve preferences/properties for namespace '{namespace_name}'",
            "Namespace Level Operation"
        )
        return response.json()
    
    # =====================================
    # SYSTEM ADMIN LEVEL OPERATIONS
    # =====================================
    
    def get_system_services(self) -> Dict[str, Any]:
        """Get system services status"""
        endpoint = "/v3/system/services"
        
        print("Getting system services status")
        response, _ = self._make_request(
            'GET', endpoint,
            "GET_SYSTEM_SERVICES",
            "Retrieve status of all system services",
            "System Admin Level Operation"
        )
        return response.json()
    
    def get_system_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get specific system service status"""
        endpoint = f"/v3/system/services/{service_name}/status"
        
        print(f"Getting status for system service: {service_name}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_SYSTEM_SERVICE_STATUS_{service_name}",
            f"Retrieve status for system service '{service_name}'",
            "System Admin Level Operation"
        )
        return response.json()
    
    def restart_system_service(self, service_name: str) -> Dict[str, Any]:
        """Restart a system service"""
        endpoint = f"/v3/system/services/{service_name}/restart"
        
        print(f"Restarting system service: {service_name}")
        response, _ = self._make_request(
            'POST', endpoint,
            f"RESTART_SYSTEM_SERVICE_{service_name}",
            f"Restart system service '{service_name}'",
            "System Admin Level Execution",
            json={}
        )
        return response.json() if response.text else {"status": "restarted"}
    
    def get_system_configuration(self) -> Dict[str, Any]:
        """Get system configuration"""
        endpoint = "/v3/system/config"
        
        print("Getting system configuration")
        response, _ = self._make_request(
            'GET', endpoint,
            "GET_SYSTEM_CONFIG",
            "Retrieve current system configuration settings",
            "System Admin Level Operation"
        )
        return response.json()
    
    def update_system_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update system configuration using PUT"""
        endpoint = "/v3/system/config"
        
        print("Updating system configuration")
        response, _ = self._make_request(
            'PUT', endpoint,
            "UPDATE_SYSTEM_CONFIG",
            "Update system-wide configuration settings",
            "System Admin Level Operation",
            json=config
        )
        return response.json() if response.text else {"status": "updated"}
    
    def get_system_artifacts(self) -> List[Dict[str, Any]]:
        """Get system artifacts"""
        endpoint = "/v3/namespaces/system/artifacts"
        
        print("Getting system artifacts")
        response, _ = self._make_request(
            'GET', endpoint,
            "GET_SYSTEM_ARTIFACTS",
            "List all system-level artifacts available for use",
            "System Admin Level Operation"
        )
        return response.json()
    
    def get_system_artifact_details(self, artifact_name: str, artifact_version: str) -> Dict[str, Any]:
        """Get system artifact details"""
        endpoint = f"/v3/namespaces/system/artifacts/{artifact_name}/versions/{artifact_version}"
        
        print(f"Getting system artifact details: {artifact_name}:{artifact_version}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_SYSTEM_ARTIFACT_{artifact_name}_{artifact_version}",
            f"Retrieve details for system artifact '{artifact_name}' version '{artifact_version}'",
            "System Admin Level Operation"
        )
        return response.json()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        endpoint = "/v3/metrics/system"
        
        print("Getting system metrics")
        response, _ = self._make_request(
            'GET', endpoint,
            "GET_SYSTEM_METRICS",
            "Retrieve system-wide performance and health metrics",
            "System Admin Level Operation"
        )
        return response.json()


class NamespaceSystemManager:
    """High-level manager for namespace and system operations"""
    
    def __init__(self, project_id: str, location: str):
        auth_token = os.getenv('GOOGLE_AUTH_TOKEN')
        if not auth_token:
            raise ValueError("GOOGLE_AUTH_TOKEN environment variable must be set")
        
        self.config = Config(
            project_id=project_id,
            location=location,
            auth_token=auth_token
        )
        self.instance_client = CloudDataFusionClient(self.config)
        self.namespace_system_clients = {}  # Cache clients by instance
    
    def get_namespace_system_client(self, instance_name: str) -> NamespaceSystemClient:
        """Get or create namespace/system client for an instance"""
        if instance_name not in self.namespace_system_clients:
            api_endpoint = self.instance_client.get_instance_api_endpoint(instance_name)
            self.namespace_system_clients[instance_name] = NamespaceSystemClient(
                api_endpoint, self.config.auth_token, self.config
            )
        return self.namespace_system_clients[instance_name]
    
    def list_instances(self) -> List[Dict[str, Any]]:
        """List all instances"""
        return self.instance_client.list_instances()
    
    # =====================================
    # HIGH-LEVEL NAMESPACE OPERATIONS
    # =====================================
    
    def create_namespace_with_preferences(self, instance_name: str, namespace_name: str, 
                                        preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a namespace with custom preferences"""
        client = self.get_namespace_system_client(instance_name)
        
        # Create the namespace
        result = client.create_namespace(namespace_name)
        
        # Set preferences if provided
        if preferences:
            client.update_namespace_preferences(namespace_name, preferences)
        
        return result
    
    def delete_namespace_completely(self, instance_name: str, namespace_name: str) -> Dict[str, Any]:
        """Delete a namespace completely"""
        client = self.get_namespace_system_client(instance_name)
        return client.delete_namespace(namespace_name)
    
    def validate_namespace_health(self, instance_name: str, namespace_name: str) -> Dict[str, Any]:
        """Basic validation of namespace health"""
        client = self.get_namespace_system_client(instance_name)
        
        health_status = {
            "namespace": namespace_name,
            "exists": False,
            "preferences_accessible": False,
            "status": "UNHEALTHY"
        }
        
        try:
            # Check if namespace exists
            namespace_info = client.get_namespace(namespace_name)
            health_status["exists"] = True
            
            # Check if preferences are accessible
            preferences = client.get_namespace_preferences(namespace_name)
            health_status["preferences_accessible"] = True
            
            health_status["status"] = "HEALTHY"
            
        except Exception as e:
            health_status["error"] = str(e)
        
        return health_status
    
    # =====================================
    # HIGH-LEVEL SYSTEM OPERATIONS
    # =====================================
    
    def get_system_health(self, instance_name: str) -> Dict[str, Any]:
        """Get comprehensive system health information with basic validation"""
        client = self.get_namespace_system_client(instance_name)
        
        health_info = {
            "instance": instance_name,
            "timestamp": datetime.now().isoformat(),
            "overall_status": "HEALTHY",
            "components": {}
        }
        
        try:
            # Get system services
            services = client.get_system_services()
            health_info["components"]["services"] = {
                "status": "HEALTHY" if services else "UNHEALTHY",
                "count": len(services) if isinstance(services, list) else 0,
                "data": services
            }
        except Exception as e:
            health_info["components"]["services"] = {"status": "ERROR", "error": str(e)}
            health_info["overall_status"] = "UNHEALTHY"
        
        try:
            # Get system configuration
            config = client.get_system_configuration()
            health_info["components"]["configuration"] = {
                "status": "HEALTHY" if config else "UNHEALTHY",
                "accessible": True,
                "data": config
            }
        except Exception as e:
            health_info["components"]["configuration"] = {"status": "ERROR", "error": str(e)}
            health_info["overall_status"] = "UNHEALTHY"
        
        try:
            # Get system artifacts
            artifacts = client.get_system_artifacts()
            health_info["components"]["artifacts"] = {
                "status": "HEALTHY" if artifacts else "UNHEALTHY",
                "count": len(artifacts) if isinstance(artifacts, list) else 0,
                "data": artifacts
            }
        except Exception as e:
            health_info["components"]["artifacts"] = {"status": "ERROR", "error": str(e)}
            health_info["overall_status"] = "UNHEALTHY"
        
        try:
            # Get system metrics
            metrics = client.get_system_metrics()
            health_info["components"]["metrics"] = {
                "status": "HEALTHY" if metrics else "UNHEALTHY",
                "accessible": True,
                "data": metrics
            }
        except Exception as e:
            health_info["components"]["metrics"] = {"status": "ERROR", "error": str(e)}
            health_info["overall_status"] = "UNHEALTHY"
        
        return health_info
    
    def validate_system_services(self, instance_name: str) -> Dict[str, Any]:
        """Basic validation of system services"""
        client = self.get_namespace_system_client(instance_name)
        
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "overall_status": "HEALTHY"
        }
        
        try:
            services = client.get_system_services()
            
            # Basic validation for common services
            common_services = ["appfabric", "dataset.service", "metadata.service", "metrics", "streams"]
            
            for service in common_services:
                try:
                    status = client.get_system_service_status(service)
                    validation_result["services"][service] = {
                        "status": "HEALTHY" if status else "UNHEALTHY",
                        "data": status
                    }
                except Exception as e:
                    validation_result["services"][service] = {
                        "status": "ERROR",
                        "error": str(e)
                    }
                    validation_result["overall_status"] = "UNHEALTHY"
            
        except Exception as e:
            validation_result["error"] = str(e)
            validation_result["overall_status"] = "ERROR"
        
        return validation_result
    
    def restart_system_services(self, instance_name: str, service_names: List[str]) -> Dict[str, Any]:
        """Restart multiple system services with basic validation"""
        client = self.get_namespace_system_client(instance_name)
        results = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "overall_status": "SUCCESS"
        }
        
        for service_name in service_names:
            try:
                result = client.restart_system_service(service_name)
                results["services"][service_name] = {
                    "status": "SUCCESS",
                    "data": result
                }
            except Exception as e:
                results["services"][service_name] = {
                    "status": "ERROR",
                    "error": str(e)
                }
                results["overall_status"] = "PARTIAL_FAILURE"
        
        return results


class TestRunner:
    """Test runner for namespace and system admin operations"""
    
    def __init__(self, manager: NamespaceSystemManager):
        self.manager = manager
        self.test_namespace_name = f"test-namespace-{int(time.time())}"
    
    def run_comprehensive_tests(self) -> List[TestResult]:
        """Run comprehensive test suite for namespace and system operations"""
        print("=== Starting Namespace and System Admin Test Suite ===\n")
        
        # Test 1: List existing instances
        self._test_list_instances()
        
        # Test 2: Test with existing instances (if any)
        instances = self.manager.list_instances()
        if instances:
            existing_instance = instances[0]['name'].split('/')[-1]
            self._test_namespace_operations(existing_instance)
            self._test_system_admin_operations(existing_instance)
            self._test_health_validation(existing_instance)
        else:
            print("No instances found for testing namespace and system operations")
        
        return self.manager.config.test_results
    
    def _test_list_instances(self):
        """Test listing instances"""
        try:
            self.manager.list_instances()
            print("✓ List instances test passed")
        except Exception as e:
            print(f"✗ List instances test failed: {e}")
    
    def _test_namespace_operations(self, instance_name: str):
        """Test namespace-level operations with basic validation"""
        try:
            client = self.manager.get_namespace_system_client(instance_name)
            
            # Test listing namespaces
            namespaces = client.list_namespaces()
            print(f"✓ List namespaces test passed (found {len(namespaces)} namespaces)")
            
            # Test getting default namespace details
            default_namespace = client.get_namespace("default")
            print(f"✓ Get default namespace test passed")
            
            # Test namespace preferences
            preferences = client.get_namespace_preferences("default")
            print(f"✓ Get namespace preferences test passed")
            
            # Test creating a test namespace
            try:
                client.create_namespace(self.test_namespace_name, {"description": "Test namespace"})
                print(f"✓ Create test namespace '{self.test_namespace_name}' test passed")
                
                # Test updating namespace preferences
                test_preferences = {
                    "test.property": "test-value",
                    "environment": "testing"
                }
                client.update_namespace_preferences(self.test_namespace_name, test_preferences)
                print(f"✓ Update namespace preferences test passed")
                
                # Test getting updated preferences
                updated_prefs = client.get_namespace_preferences(self.test_namespace_name)
                print(f"✓ Get updated namespace preferences test passed")
                
                # Test namespace health validation
                health = self.manager.validate_namespace_health(instance_name, self.test_namespace_name)
                print(f"✓ Namespace health validation test passed (status: {health.get('status')})")
                
                # Clean up - delete test namespace
                client.delete_namespace(self.test_namespace_name)
                print(f"✓ Delete test namespace test passed")
                
            except Exception as e:
                print(f"✗ Namespace CRUD operations test failed: {e}")
            
        except Exception as e:
            print(f"✗ Namespace operations test failed: {e}")
    
    def _test_system_admin_operations(self, instance_name: str):
        """Test system admin level operations with basic validation"""
        try:
            client = self.manager.get_namespace_system_client(instance_name)
            
            # Test system services
            services = client.get_system_services()
            print(f"✓ Get system services test passed (found {len(services)} services)" if isinstance(services, list) else "✓ Get system services test passed")
            
            # Test system configuration
            config = client.get_system_configuration()
            print(f"✓ Get system configuration test passed")
            
            # Test system artifacts
            artifacts = client.get_system_artifacts()
            print(f"✓ Get system artifacts test passed (found {len(artifacts)} artifacts)" if isinstance(artifacts, list) else "✓ Get system artifacts test passed")
            
            # Test system metrics
            metrics = client.get_system_metrics()
            print(f"✓ Get system metrics test passed")
            
            # Test getting specific service status (basic validation)
            try:
                appfabric_status = client.get_system_service_status("appfabric")
                print(f"✓ Get appfabric service status test passed")
            except Exception as e:
                print(f"✗ Get appfabric service status test failed: {e}")
            
        except Exception as e:
            print(f"✗ System admin operations test failed: {e}")
    
    def _test_health_validation(self, instance_name: str):
        """Test health validation operations"""
        try:
            # Test system health validation
            system_health = self.manager.get_system_health(instance_name)
            print(f"✓ System health validation test passed (status: {system_health.get('overall_status')})")
            
            # Test service validation
            service_validation = self.manager.validate_system_services(instance_name)
            print(f"✓ System services validation test passed (status: {service_validation.get('overall_status')})")
            
            # Test namespace health for default namespace
            namespace_health = self.manager.validate_namespace_health(instance_name, "default")
            print(f"✓ Default namespace health validation test passed (status: {namespace_health.get('status')})")
            
        except Exception as e:
            print(f"✗ Health validation test failed: {e}")


class ReportGenerator:
    """Generate CSV reports and display results"""
    
    @staticmethod
    def generate_csv_report(test_results: List[TestResult], filename: str = None) -> str:
        """Generate CSV report of test results"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_fusion_namespace_system_test_results_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'test_case', 'api_endpoint', 'method', 'description', 'type', 'status',
                'response_code', 'response_message', 'execution_time', 'timestamp', 'error_details'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in test_results:
                writer.writerow({
                    'test_case': result.test_case,
                    'api_endpoint': result.api_endpoint,
                    'method': result.method,
                    'description': result.description,
                    'type': result.type,
                    'status': result.status,
                    'response_code': result.response_code,
                    'response_message': result.response_message,
                    'execution_time': f"{result.execution_time:.3f}s",
                    'timestamp': result.timestamp,
                    'error_details': result.error_details[:200] + '...' if len(result.error_details) > 200 else result.error_details
                })
        
        return filename
    
    @staticmethod
    def display_results_table(test_results: List[TestResult]):
        """Display test results in a formatted table"""
        if not test_results:
            print("No test results to display.")
            return
        
        # Prepare data for tabulation
        table_data = []
        for result in test_results:
            table_data.append([
                result.test_case[:25] + '...' if len(result.test_case) > 25 else result.test_case,
                result.method,
                result.type[:20] + '...' if len(result.type) > 20 else result.type,
                result.status,
                result.response_code,
                f"{result.execution_time:.3f}s",
                result.description[:45] + '...' if len(result.description) > 45 else result.description
            ])
        
        headers = ['Test Case', 'Method', 'Type', 'Status', 'Code', 'Time', 'Description']
        
        print("\n" + "="*130)
        print("NAMESPACE & SYSTEM ADMIN API TEST RESULTS SUMMARY")
        print("="*130)
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Summary statistics
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r.status == "PASS"])
        failed_tests = total_tests - passed_tests
        avg_time = sum(r.execution_time for r in test_results) / total_tests if total_tests > 0 else 0
        
        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✓")
        print(f"   Failed: {failed_tests} ✗")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"   Average Execution Time: {avg_time:.3f}s")
        
        # Category breakdown by type
        namespace_tests = len([r for r in test_results if 'Namespace Level' in r.type])
        system_tests = len([r for r in test_results if 'System Admin Level' in r.type])
        instance_tests = len([r for r in test_results if 'Instance Level' in r.type])
        
        print(f"\n📋 TEST CATEGORIES:")
        print(f"   Namespace Level Operations: {namespace_tests}")
        print(f"   System Admin Level Operations: {system_tests}")
        print(f"   Instance Level Operations: {instance_tests}")
        print(f"   Other Operations: {total_tests - namespace_tests - system_tests - instance_tests}")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in test_results:
                if result.status == "FAIL":
                    print(f"   - {result.test_case}: {result.response_code} {result.response_message}")
                    if result.error_details:
                        error_preview = result.error_details[:100] + '...' if len(result.error_details) > 100 else result.error_details
                        print(f"     Error: {error_preview}")


def main():
    """Main function for namespace and system admin testing"""
    # Configuration
    PROJECT_ID = "your-project-id"  # Replace with your actual project ID
    LOCATION = "us-central1"        # Replace with your preferred location
    
    try:
        print("=== Google Cloud Data Fusion Namespace & System Admin Testing Suite ===\n")
        
        # Initialize manager
        manager = NamespaceSystemManager(PROJECT_ID, LOCATION)
        
        # Run comprehensive tests
        test_runner = TestRunner(manager)
        test_results = test_runner.run_comprehensive_tests()
        
        # Generate CSV report
        csv_filename = ReportGenerator.generate_csv_report(test_results)
        print(f"\n📄 CSV report generated: {csv_filename}")
        
        # Display results table
        ReportGenerator.display_results_table(test_results)
        
        print(f"\n✅ Namespace & System Admin testing completed. Check '{csv_filename}' for detailed results.")
        
        # Display additional insights
        instances = manager.list_instances()
        if instances:
            instance_name = instances[0]['name'].split('/')[-1]
            print(f"\n🔍 ADDITIONAL INSIGHTS FOR INSTANCE: {instance_name}")
            
            # Show system health summary
            try:
                health = manager.get_system_health(instance_name)
                print(f"   System Health: {health.get('overall_status')}")
                
                components = health.get('components', {})
                for component, info in components.items():
                    status = info.get('status', 'UNKNOWN')
                    print(f"   - {component.title()}: {status}")
                    
            except Exception as e:
                print(f"   Could not retrieve system health: {e}")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
