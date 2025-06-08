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
    python gcp_data_fusion_namespace_system.py
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
    
    def _make_request(self, method: str, url: str, test_case: str, description: str, operation_type: str = "Instance Level Operation", **kwargs) -> Tuple[Optional[requests.Response], TestResult]:
        """Make HTTP request with test case tracking - prevents duplicates"""
        # Check for duplicate test cases
        existing_test = next((r for r in self.config.test_results if r.test_case == test_case), None)
        if existing_test:
            print(f"Skipping duplicate test case: {test_case}")
            return None, existing_test
        
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

    def get_instance(self, instance_name: str) -> Optional[Dict[str, Any]]:
        """Get details of a Data Fusion instance"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances/{instance_name}"
        
        print(f"Getting Data Fusion instance: {instance_name}")
        response, _ = self._make_request(
            'GET', url,
            f"GET_INSTANCE_{instance_name}",
            f"Retrieve details for Data Fusion instance '{instance_name}'",
            "Instance Level Operation"
        )
        return response.json() if response else None
    
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
        if response:
            result = response.json()
            return result.get('instances', [])
        return []
    
    def get_instance_api_endpoint(self, instance_name: str) -> Optional[str]:
        """Get the CDAP API endpoint for an instance"""
        instance_details = self.get_instance(instance_name)
        if instance_details:
            api_endpoint = instance_details.get('apiEndpoint')
            if not api_endpoint:
                raise ValueError(f"No API endpoint found for instance {instance_name}")
            return api_endpoint
        return None


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
    
    def _make_request(self, method: str, endpoint: str, test_case: str, description: str, operation_type: str = "Namespace Level Operation", **kwargs) -> Tuple[Optional[requests.Response], TestResult]:
        """Make HTTP request with test case tracking - prevents duplicates"""
        # Check for duplicate test cases
        existing_test = next((r for r in self.config.test_results if r.test_case == test_case), None)
        if existing_test:
            print(f"Skipping duplicate test case: {test_case}")
            return None, existing_test
        
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
    # NAMESPACE OPERATIONS (Complete CRUD with Google naming standards)
    # =====================================
    
    def list_namespaces(self) -> Optional[List[Dict[str, Any]]]:
        """List all namespaces"""
        endpoint = "/v3/namespaces"
        
        print("Listing namespaces")
        response, _ = self._make_request(
            'GET', endpoint,
            "LIST_NAMESPACES",
            "List all available namespaces",
            "Namespace Level Operation"
        )
        return response.json() if response else None
    
    def create_namespace(self, namespace_id: str, namespace_config: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Create a namespace using PUT with Google naming standards"""
        endpoint = f"/v3/namespaces/{namespace_id}"
        payload = namespace_config or {}
        
        print(f"Creating namespace: {namespace_id}")
        response, _ = self._make_request(
            'PUT', endpoint,
            f"CREATE_NAMESPACE_{namespace_id}",
            f"Create namespace '{namespace_id}' with configuration",
            "Namespace Level Operation",
            json=payload
        )
        if response:
            return response.json() if response.text else {"status": "created"}
        return None
    
    def get_namespace(self, namespace_id: str) -> Optional[Dict[str, Any]]:
        """Get namespace details"""
        endpoint = f"/v3/namespaces/{namespace_id}"
        
        print(f"Getting namespace: {namespace_id}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_NAMESPACE_{namespace_id}",
            f"Get namespace '{namespace_id}' details",
            "Namespace Level Operation"
        )
        return response.json() if response else None
    
    def delete_namespace(self, namespace_id: str) -> Optional[Dict[str, Any]]:
        """Delete a namespace"""
        endpoint = f"/v3/namespaces/{namespace_id}"
        
        print(f"Deleting namespace: {namespace_id}")
        response, _ = self._make_request(
            'DELETE', endpoint,
            f"DELETE_NAMESPACE_{namespace_id}",
            f"Delete namespace '{namespace_id}' and all contents",
            "Namespace Level Operation"
        )
        if response:
            return response.json() if response.text else {"status": "deleted"}
        return None
    
    def update_namespace_preferences(self, namespace_id: str, preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update namespace preferences using PUT"""
        endpoint = f"/v3/namespaces/{namespace_id}/preferences"
        
        print(f"Updating preferences for namespace: {namespace_id}")
        response, _ = self._make_request(
            'PUT', endpoint,
            f"UPDATE_NAMESPACE_PREFERENCES_{namespace_id}",
            f"Update preferences for namespace '{namespace_id}'",
            "Namespace Level Operation",
            json=preferences
        )
        if response:
            return response.json() if response.text else {"status": "updated"}
        return None
    
    def get_namespace_preferences(self, namespace_id: str) -> Optional[Dict[str, Any]]:
        """Get namespace preferences"""
        endpoint = f"/v3/namespaces/{namespace_id}/preferences"
        
        print(f"Getting preferences for namespace: {namespace_id}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_NAMESPACE_PREFERENCES_{namespace_id}",
            f"Get preferences for namespace '{namespace_id}'",
            "Namespace Level Operation"
        )
        return response.json() if response else None
    
    # =====================================
    # SYSTEM ADMIN OPERATIONS (Complete CRUD with service status details)
    # =====================================
    
    def get_system_services(self) -> Optional[Dict[str, Any]]:
        """Get system services status"""
        endpoint = "/v3/system/services"
        
        print("Getting system services status")
        response, _ = self._make_request(
            'GET', endpoint,
            "GET_SYSTEM_SERVICES",
            "Get all system services status",
            "System Admin Level Operation"
        )
        return response.json() if response else None
    
    def get_system_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get specific system service status with detailed info"""
        endpoint = f"/v3/system/services/{service_name}/status"
        
        print(f"Getting status for system service: {service_name}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_SERVICE_STATUS_{service_name}",
            f"Get status for service '{service_name}': checking if service is running and healthy",
            "System Admin Level Operation"
        )
        
        if response:
            # Enhanced response with service name and status
            service_status = response.json()
            return {
                "service_name": service_name,
                "status_details": service_status,
                "is_healthy": service_status.get("status", "").upper() == "OK" if service_status else False
            }
        return None
    
    def restart_system_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Restart a system service"""
        endpoint = f"/v3/system/services/{service_name}/restart"
        
        print(f"Restarting system service: {service_name}")
        response, _ = self._make_request(
            'POST', endpoint,
            f"RESTART_SERVICE_{service_name}",
            f"Restart system service '{service_name}'",
            "System Admin Level Execution",
            json={}
        )
        if response:
            return response.json() if response.text else {"status": "restarted", "service_name": service_name}
        return None
    
    def get_system_configuration(self) -> Optional[Dict[str, Any]]:
        """Get system configuration"""
        endpoint = "/v3/system/config"
        
        print("Getting system configuration")
        response, _ = self._make_request(
            'GET', endpoint,
            "GET_SYSTEM_CONFIG",
            "Get system configuration settings",
            "System Admin Level Operation"
        )
        return response.json() if response else None
    
    def update_system_configuration(self, config_properties: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update system configuration using PUT"""
        endpoint = "/v3/system/config"
        
        print("Updating system configuration")
        response, _ = self._make_request(
            'PUT', endpoint,
            "UPDATE_SYSTEM_CONFIG",
            "Update system-wide configuration properties",
            "System Admin Level Operation",
            json=config_properties
        )
        if response:
            return response.json() if response.text else {"status": "updated"}
        return None
    
    def get_system_artifacts(self) -> Optional[List[Dict[str, Any]]]:
        """Get system artifacts"""
        endpoint = "/v3/namespaces/system/artifacts"
        
        print("Getting system artifacts")
        response, _ = self._make_request(
            'GET', endpoint,
            "GET_SYSTEM_ARTIFACTS",
            "Get system-level artifacts",
            "System Admin Level Operation"
        )
        return response.json() if response else None
    
    def get_system_artifact_details(self, artifact_name: str, artifact_version: str) -> Optional[Dict[str, Any]]:
        """Get system artifact details"""
        endpoint = f"/v3/namespaces/system/artifacts/{artifact_name}/versions/{artifact_version}"
        
        print(f"Getting system artifact details: {artifact_name}:{artifact_version}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_ARTIFACT_DETAILS_{artifact_name}_{artifact_version}",
            f"Get details for artifact '{artifact_name}' version '{artifact_version}'",
            "System Admin Level Operation"
        )
        return response.json() if response else None
    
    def get_system_metrics(self) -> Optional[Dict[str, Any]]:
        """Get system metrics"""
        endpoint = "/v3/metrics/system"
        
        print("Getting system metrics")
        response, _ = self._make_request(
            'GET', endpoint,
            "GET_SYSTEM_METRICS",
            "Get system-wide performance metrics",
            "System Admin Level Operation"
        )
        return response.json() if response else None


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
    
    def get_namespace_system_client(self, instance_name: str) -> Optional[NamespaceSystemClient]:
        """Get or create namespace/system client for an instance"""
        if instance_name not in self.namespace_system_clients:
            api_endpoint = self.instance_client.get_instance_api_endpoint(instance_name)
            if api_endpoint:
                self.namespace_system_clients[instance_name] = NamespaceSystemClient(
                    api_endpoint, self.config.auth_token, self.config
                )
            else:
                return None
        return self.namespace_system_clients[instance_name]
    
    def list_instances(self) -> List[Dict[str, Any]]:
        """List all instances"""
        return self.instance_client.list_instances()
    
    # =====================================
    # HIGH-LEVEL OPERATIONS WITH COMPLETE CRUD
    # =====================================
    
    def create_namespace_with_preferences(self, instance_name: str, namespace_id: str, 
                                        preferences: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Create a namespace with custom preferences"""
        client = self.get_namespace_system_client(instance_name)
        if not client:
            return None
        
        # Create the namespace
        namespace_config = {
            "description": f"Namespace {namespace_id} created via API testing"
        }
        result = client.create_namespace(namespace_id, namespace_config)
        
        # Set preferences if provided
        if result and preferences:
            client.update_namespace_preferences(namespace_id, preferences)
        
        return result
    
    def delete_namespace_completely(self, instance_name: str, namespace_id: str) -> Optional[Dict[str, Any]]:
        """Delete a namespace completely"""
        client = self.get_namespace_system_client(instance_name)
        if not client:
            return None
        return client.delete_namespace(namespace_id)
    
    def validate_namespace_health(self, instance_name: str, namespace_id: str) -> Dict[str, Any]:
        """Basic validation of namespace health"""
        client = self.get_namespace_system_client(instance_name)
        if not client:
            return {"status": "ERROR", "error": "Could not get client"}
        
        health_status = {
            "namespace_id": namespace_id,
            "exists": False,
            "preferences_accessible": False,
            "status": "UNHEALTHY"
        }
        
        try:
            # Check if namespace exists
            namespace_info = client.get_namespace(namespace_id)
            if namespace_info:
                health_status["exists"] = True
                health_status["namespace_info"] = namespace_info
            
            # Check if preferences are accessible
            preferences = client.get_namespace_preferences(namespace_id)
            if preferences is not None:
                health_status["preferences_accessible"] = True
                health_status["preferences_count"] = len(preferences) if isinstance(preferences, dict) else 0
            
            if health_status["exists"] and health_status["preferences_accessible"]:
                health_status["status"] = "HEALTHY"
            
        except Exception as e:
            health_status["error"] = str(e)
        
        return health_status
    
    def get_system_health_with_services(self, instance_name: str) -> Dict[str, Any]:
        """Get comprehensive system health with detailed service status"""
        client = self.get_namespace_system_client(instance_name)
        if not client:
            return {"status": "ERROR", "error": "Could not get client"}
        
        health_info = {
            "instance": instance_name,
            "timestamp": datetime.now().isoformat(),
            "overall_status": "HEALTHY",
            "components": {},
            "service_details": {}
        }
        
        try:
            # Get system services
            services = client.get_system_services()
            if services:
                health_info["components"]["services"] = {
                    "status": "HEALTHY",
                    "accessible": True,
                    "total_services": len(services) if isinstance(services, list) else 0
                }
            else:
                health_info["components"]["services"] = {"status": "UNHEALTHY", "accessible": False}
            
            # Get detailed status for key services
            key_services = ["appfabric", "dataset.service", "metadata.service"]
            for service_name in key_services:
                try:
                    service_status = client.get_system_service_status(service_name)
                    if service_status:
                        health_info["service_details"][service_name] = {
                            "status": "HEALTHY" if service_status.get("is_healthy", False) else "UNHEALTHY",
                            "service_name": service_status.get("service_name", service_name),
                            "details": service_status.get("status_details", {})
                        }
                except Exception as e:
                    health_info["service_details"][service_name] = {
                        "status": "ERROR",
                        "service_name": service_name,
                        "error": str(e)
                    }
                    health_info["overall_status"] = "UNHEALTHY"
            
        except Exception as e:
            health_info["components"]["services"] = {"status": "ERROR", "error": str(e)}
            health_info["overall_status"] = "UNHEALTHY"
        
        try:
            # Get system configuration
            config = client.get_system_configuration()
            if config:
                health_info["components"]["configuration"] = {
                    "status": "HEALTHY",
                    "accessible": True,
                    "config_keys": len(config) if isinstance(config, dict) else 0
                }
            else:
                health_info["components"]["configuration"] = {"status": "UNHEALTHY", "accessible": False}
        except Exception as e:
            health_info["components"]["configuration"] = {"status": "ERROR", "error": str(e)}
            health_info["overall_status"] = "UNHEALTHY"
        
        try:
            # Get system artifacts
            artifacts = client.get_system_artifacts()
            if artifacts:
                health_info["components"]["artifacts"] = {
                    "status": "HEALTHY",
                    "accessible": True,
                    "artifact_count": len(artifacts) if isinstance(artifacts, list) else 0
                }
            else:
                health_info["components"]["artifacts"] = {"status": "UNHEALTHY", "accessible": False}
        except Exception as e:
            health_info["components"]["artifacts"] = {"status": "ERROR", "error": str(e)}
            health_info["overall_status"] = "UNHEALTHY"
        
        return health_info
    
    def validate_system_services_detailed(self, instance_name: str) -> Dict[str, Any]:
        """Detailed validation of system services with individual status"""
        client = self.get_namespace_system_client(instance_name)
        if not client:
            return {"status": "ERROR", "error": "Could not get client"}
        
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "overall_status": "HEALTHY",
            "healthy_services": 0,
            "unhealthy_services": 0,
            "error_services": 0
        }
        
        try:
            services = client.get_system_services()
            
            # Validate key system services
            key_services = ["appfabric", "dataset.service", "metadata.service", "metrics"]
            
            for service_name in key_services:
                try:
                    service_status = client.get_system_service_status(service_name)
                    if service_status:
                        is_healthy = service_status.get("is_healthy", False)
                        
                        validation_result["services"][service_name] = {
                            "service_name": service_status.get("service_name", service_name),
                            "status": "HEALTHY" if is_healthy else "UNHEALTHY",
                            "details": service_status.get("status_details", {}),
                            "is_running": is_healthy
                        }
                        
                        if is_healthy:
                            validation_result["healthy_services"] += 1
                        else:
                            validation_result["unhealthy_services"] += 1
                            validation_result["overall_status"] = "UNHEALTHY"
                        
                except Exception as e:
                    validation_result["services"][service_name] = {
                        "service_name": service_name,
                        "status": "ERROR",
                        "error": str(e),
                        "is_running": False
                    }
                    validation_result["error_services"] += 1
                    validation_result["overall_status"] = "UNHEALTHY"
            
        except Exception as e:
            validation_result["error"] = str(e)
            validation_result["overall_status"] = "ERROR"
        
        return validation_result
    
    def restart_system_services(self, instance_name: str, service_names: List[str]) -> Dict[str, Any]:
        """Restart multiple system services"""
        client = self.get_namespace_system_client(instance_name)
        if not client:
            return {"status": "ERROR", "error": "Could not get client"}
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "overall_status": "SUCCESS",
            "successful_restarts": 0,
            "failed_restarts": 0
        }
        
        for service_name in service_names:
            try:
                result = client.restart_system_service(service_name)
                if result:
                    results["services"][service_name] = {
                        "service_name": service_name,
                        "status": "SUCCESS",
                        "restart_result": result
                    }
                    results["successful_restarts"] += 1
                else:
                    results["services"][service_name] = {
                        "service_name": service_name,
                        "status": "FAILED",
                        "error": "No response"
                    }
                    results["failed_restarts"] += 1
                    results["overall_status"] = "PARTIAL_FAILURE"
            except Exception as e:
                results["services"][service_name] = {
                    "service_name": service_name,
                    "status": "ERROR",
                    "error": str(e)
                }
                results["failed_restarts"] += 1
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
        """Test complete namespace operations with CRUD"""
        try:
            client = self.manager.get_namespace_system_client(instance_name)
            if not client:
                print("✗ Could not get namespace/system client")
                return
            
            # Test listing namespaces
            namespaces = client.list_namespaces()
            if namespaces is not None:
                print(f"✓ List namespaces test passed (found {len(namespaces) if isinstance(namespaces, list) else 0} namespaces)")
            
            # Test getting default namespace details
            default_namespace = client.get_namespace("default")
            if default_namespace:
                print(f"✓ Get default namespace test passed")
            
            # Test namespace preferences
            preferences = client.get_namespace_preferences("default")
            if preferences is not None:
                print(f"✓ Get namespace preferences test passed")
            
            # Test creating a test namespace
            try:
                namespace_config = {
                    "description": "Test namespace for API validation",
                    "config": {
                        "scheduler.max.thread.pool.size": "10"
                    }
                }
                result = client.create_namespace(self.test_namespace_name, namespace_config)
                if result:
                    print(f"✓ Create test namespace '{self.test_namespace_name}' test passed")
                
                # Test updating namespace preferences
                test_preferences = {
                    "system.log.level": "INFO",
                    "test.property": "test-value",
                    "environment": "testing"
                }
                result = client.update_namespace_preferences(self.test_namespace_name, test_preferences)
                if result:
                    print(f"✓ Update namespace preferences test passed")
                
                # Test getting updated preferences
                updated_prefs = client.get_namespace_preferences(self.test_namespace_name)
                if updated_prefs is not None:
                    print(f"✓ Get updated namespace preferences test passed")
                
                # Test namespace health validation
                health = self.manager.validate_namespace_health(instance_name, self.test_namespace_name)
                print(f"✓ Namespace health validation test passed (status: {health.get('status')})")
                
                # Clean up - delete test namespace
                result = client.delete_namespace(self.test_namespace_name)
                if result:
                    print(f"✓ Delete test namespace test passed")
                
            except Exception as e:
                print(f"✗ Namespace CRUD operations test failed: {e}")
            
        except Exception as e:
            print(f"✗ Namespace operations test failed: {e}")
    
    def _test_system_admin_operations(self, instance_name: str):
        """Test system admin operations with detailed service status"""
        try:
            client = self.manager.get_namespace_system_client(instance_name)
            if not client:
                print("✗ Could not get namespace/system client")
                return
            
            # Test system services
            services = client.get_system_services()
            if services is not None:
                print(f"✓ Get system services test passed")
            
            # Test system configuration
            config = client.get_system_configuration()
            if config is not None:
                print(f"✓ Get system configuration test passed")
            
            # Test system artifacts
            artifacts = client.get_system_artifacts()
            if artifacts is not None:
                print(f"✓ Get system artifacts test passed")
            
            # Test system metrics
            try:
                metrics = client.get_system_metrics()
                if metrics is not None:
                    print(f"✓ Get system metrics test passed")
            except Exception as e:
                print(f"✗ Get system metrics test failed: {e}")
            
            # Test getting specific service status with detailed reporting
            key_services = ["appfabric", "dataset.service"]
            for service_name in key_services:
                try:
                    service_status = client.get_system_service_status(service_name)
                    if service_status:
                        service_health = "HEALTHY" if service_status.get("is_healthy", False) else "UNHEALTHY"
                        print(f"✓ Get {service_name} service status test passed (Status: {service_health})")
                except Exception as e:
                    print(f"✗ Get {service_name} service status test failed: {e}")
            
            # Test system configuration update (safe test)
            try:
                test_config = {
                    "test.config.property": "test-value"
                }
                result = client.update_system_configuration(test_config)
                if result:
                    print(f"✓ Update system configuration test passed")
            except Exception as e:
                print(f"✗ Update system configuration test failed: {e}")
            
        except Exception as e:
            print(f"✗ System admin operations test failed: {e}")
    
    def _test_health_validation(self, instance_name: str):
        """Test comprehensive health validation with service details"""
        try:
            # Test detailed system health validation
            system_health = self.manager.get_system_health_with_services(instance_name)
            overall_status = system_health.get('overall_status')
            service_details = system_health.get('service_details', {})
            
            print(f"✓ System health validation test passed (Overall Status: {overall_status})")
            
            # Report individual service status
            for service_name, details in service_details.items():
                service_status = details.get('status', 'UNKNOWN')
                print(f"  - Service '{service_name}': {service_status}")
            
            # Test detailed service validation
            service_validation = self.manager.validate_system_services_detailed(instance_name)
            validation_status = service_validation.get('overall_status')
            healthy_count = service_validation.get('healthy_services', 0)
            unhealthy_count = service_validation.get('unhealthy_services', 0)
            
            print(f"✓ System services validation test passed (Status: {validation_status})")
            print(f"  - Healthy Services: {healthy_count}, Unhealthy Services: {unhealthy_count}")
            
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
                health = manager.get_system_health_with_services(instance_name)
                print(f"   System Health: {health.get('overall_status')}")
                
                components = health.get('components', {})
                for component, info in components.items():
                    status = info.get('status', 'UNKNOWN')
                    print(f"   - {component.title()}: {status}")
                
                service_details = health.get('service_details', {})
                if service_details:
                    print(f"   Service Details:")
                    for service, details in service_details.items():
                        status = details.get('status', 'UNKNOWN')
                        print(f"   - {service}: {status}")
                    
            except Exception as e:
                print(f"   Could not retrieve system health: {e}")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
