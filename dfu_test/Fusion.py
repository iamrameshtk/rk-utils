#!/usr/bin/env python3
"""
Google Cloud Data Fusion CRUD Operations Script with Test Cases

This script provides comprehensive CRUD operations for:
1. Cloud Data Fusion instances (Control Plane API)
2. CDAP pipelines and applications (Data Plane API)

Features:
- Complete CRUD operations for instances and pipelines
- Automated test case execution with Pass/Fail tracking
- CSV report generation with detailed test results
- Tabulated output display for easy reading

Requirements:
- Set GOOGLE_AUTH_TOKEN environment variable with your Google Cloud auth token
- Install required packages: requests, google-auth, tabulate

Usage:
    export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)
    python data_fusion_crud.py
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
    api_version: str = "v1beta1"  # or v1 for stable operations
    test_results: List[TestResult] = field(default_factory=list)

    def __post_init__(self):
        if not self.auth_token:
            raise ValueError("GOOGLE_AUTH_TOKEN environment variable must be set")


class CloudDataFusionClient:
    """Client for Google Cloud Data Fusion operations with test case tracking"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.auth_token}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, url: str, test_case: str, description: str, **kwargs) -> Tuple[requests.Response, TestResult]:
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

    # =====================================
    # INSTANCE LEVEL OPERATIONS (Control Plane)
    # =====================================
    
    def create_instance(self, instance_name: str, instance_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Data Fusion instance using POST"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances"
        
        payload = {
            "instanceId": instance_name,
            **instance_config
        }
        
        print(f"Creating Data Fusion instance: {instance_name}")
        response, _ = self._make_request(
            'POST', url, 
            f"CREATE_INSTANCE_{instance_name}", 
            f"Create Data Fusion instance '{instance_name}' with configuration",
            json=payload
        )
        return response.json()
    
    def get_instance(self, instance_name: str) -> Dict[str, Any]:
        """Get details of a Data Fusion instance"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances/{instance_name}"
        
        print(f"Getting Data Fusion instance: {instance_name}")
        response, _ = self._make_request(
            'GET', url,
            f"GET_INSTANCE_{instance_name}",
            f"Retrieve details for Data Fusion instance '{instance_name}'"
        )
        return response.json()
    
    def update_instance(self, instance_name: str, update_config: Dict[str, Any], update_mask: str = None) -> Dict[str, Any]:
        """Update a Data Fusion instance using PATCH"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances/{instance_name}"
        
        params = {}
        if update_mask:
            params['updateMask'] = update_mask
        
        print(f"Updating Data Fusion instance: {instance_name}")
        response, _ = self._make_request(
            'PATCH', url,
            f"UPDATE_INSTANCE_{instance_name}",
            f"Update Data Fusion instance '{instance_name}' configuration",
            json=update_config, params=params
        )
        return response.json()
    
    def delete_instance(self, instance_name: str) -> Dict[str, Any]:
        """Delete a Data Fusion instance"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances/{instance_name}"
        
        print(f"Deleting Data Fusion instance: {instance_name}")
        response, _ = self._make_request(
            'DELETE', url,
            f"DELETE_INSTANCE_{instance_name}",
            f"Delete Data Fusion instance '{instance_name}'"
        )
        return response.json() if response.text else {"status": "deleted"}
    
    def list_instances(self) -> List[Dict[str, Any]]:
        """List all Data Fusion instances in the project/location"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances"
        
        print("Listing Data Fusion instances")
        response, _ = self._make_request(
            'GET', url,
            "LIST_INSTANCES",
            f"List all Data Fusion instances in project '{self.config.project_id}' and location '{self.config.location}'"
        )
        result = response.json()
        return result.get('instances', [])
    
    def restart_instance(self, instance_name: str) -> Dict[str, Any]:
        """Restart a Data Fusion instance"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances/{instance_name}:restart"
        
        print(f"Restarting Data Fusion instance: {instance_name}")
        response, _ = self._make_request(
            'POST', url,
            f"RESTART_INSTANCE_{instance_name}",
            f"Restart Data Fusion instance '{instance_name}'",
            json={}
        )
        return response.json()
    
    def get_instance_api_endpoint(self, instance_name: str) -> str:
        """Get the CDAP API endpoint for an instance"""
        instance_details = self.get_instance(instance_name)
        api_endpoint = instance_details.get('apiEndpoint')
        if not api_endpoint:
            raise ValueError(f"No API endpoint found for instance {instance_name}")
        return api_endpoint


class CDAPClient:
    """Client for CDAP Data Plane operations with test case tracking"""
    
    def __init__(self, cdap_endpoint: str, auth_token: str, config: Config):
        self.cdap_endpoint = cdap_endpoint.rstrip('/')
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, test_case: str, description: str, **kwargs) -> Tuple[requests.Response, TestResult]:
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
    # PIPELINE LEVEL OPERATIONS (Data Plane)
    # =====================================
    
    def deploy_pipeline(self, namespace: str, pipeline_name: str, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy/Create a pipeline using PUT"""
        endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}"
        
        print(f"Deploying pipeline: {pipeline_name} in namespace: {namespace}")
        response, _ = self._make_request(
            'PUT', endpoint,
            f"DEPLOY_PIPELINE_{pipeline_name}",
            f"Deploy pipeline '{pipeline_name}' in namespace '{namespace}' using CDAP API",
            json=pipeline_config
        )
        return response.json() if response.text else {"status": "deployed"}
    
    def get_pipeline(self, namespace: str, pipeline_name: str) -> Dict[str, Any]:
        """Get pipeline details"""
        endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}"
        
        print(f"Getting pipeline: {pipeline_name} from namespace: {namespace}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_PIPELINE_{pipeline_name}",
            f"Retrieve pipeline details for '{pipeline_name}' from namespace '{namespace}'"
        )
        return response.json()
    
    def update_pipeline(self, namespace: str, pipeline_name: str, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update a pipeline using PUT (redeploy)"""
        return self.deploy_pipeline(namespace, pipeline_name, pipeline_config)
    
    def delete_pipeline(self, namespace: str, pipeline_name: str) -> Dict[str, Any]:
        """Delete a pipeline"""
        endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}"
        
        print(f"Deleting pipeline: {pipeline_name} from namespace: {namespace}")
        response, _ = self._make_request(
            'DELETE', endpoint,
            f"DELETE_PIPELINE_{pipeline_name}",
            f"Delete pipeline '{pipeline_name}' from namespace '{namespace}'"
        )
        return response.json() if response.text else {"status": "deleted"}
    
    def list_pipelines(self, namespace: str, artifact_name: str = None) -> List[Dict[str, Any]]:
        """List pipelines in a namespace"""
        endpoint = f"/v3/namespaces/{namespace}/apps"
        params = {}
        if artifact_name:
            params['artifactName'] = artifact_name
        
        print(f"Listing pipelines in namespace: {namespace}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"LIST_PIPELINES_{namespace}",
            f"List all pipelines in namespace '{namespace}'" + (f" with artifact '{artifact_name}'" if artifact_name else ""),
            params=params
        )
        return response.json()
    
    def list_batch_pipelines(self, namespace: str) -> List[Dict[str, Any]]:
        """List batch pipelines specifically"""
        return self.list_pipelines(namespace, artifact_name="cdap-data-pipeline")
    
    def list_realtime_pipelines(self, namespace: str) -> List[Dict[str, Any]]:
        """List real-time pipelines specifically"""
        return self.list_pipelines(namespace, artifact_name="cdap-data-streams")
    
    # =====================================
    # PIPELINE EXECUTION OPERATIONS
    # =====================================
    
    def start_batch_pipeline(self, namespace: str, pipeline_name: str, runtime_args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start a batch pipeline"""
        endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}/workflows/DataPipelineWorkflow/start"
        payload = runtime_args or {}
        
        print(f"Starting batch pipeline: {pipeline_name}")
        response, _ = self._make_request(
            'POST', endpoint,
            f"START_BATCH_PIPELINE_{pipeline_name}",
            f"Start execution of batch pipeline '{pipeline_name}' in namespace '{namespace}'",
            json=payload
        )
        return response.json() if response.text else {"status": "started"}
    
    def stop_batch_pipeline(self, namespace: str, pipeline_name: str) -> Dict[str, Any]:
        """Stop a batch pipeline"""
        endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}/workflows/DataPipelineWorkflow/stop"
        
        print(f"Stopping batch pipeline: {pipeline_name}")
        response, _ = self._make_request(
            'POST', endpoint,
            f"STOP_BATCH_PIPELINE_{pipeline_name}",
            f"Stop execution of batch pipeline '{pipeline_name}' in namespace '{namespace}'",
            json={}
        )
        return response.json() if response.text else {"status": "stopped"}
    
    def start_realtime_pipeline(self, namespace: str, pipeline_name: str, runtime_args: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start a real-time pipeline"""
        endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}/spark/DataStreamsSparkStreaming/start"
        payload = runtime_args or {}
        
        print(f"Starting real-time pipeline: {pipeline_name}")
        response, _ = self._make_request(
            'POST', endpoint,
            f"START_REALTIME_PIPELINE_{pipeline_name}",
            f"Start execution of real-time pipeline '{pipeline_name}' in namespace '{namespace}'",
            json=payload
        )
        return response.json() if response.text else {"status": "started"}
    
    def stop_realtime_pipeline(self, namespace: str, pipeline_name: str) -> Dict[str, Any]:
        """Stop a real-time pipeline"""
        endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}/spark/DataStreamsSparkStreaming/stop"
        
        print(f"Stopping real-time pipeline: {pipeline_name}")
        response, _ = self._make_request(
            'POST', endpoint,
            f"STOP_REALTIME_PIPELINE_{pipeline_name}",
            f"Stop execution of real-time pipeline '{pipeline_name}' in namespace '{namespace}'",
            json={}
        )
        return response.json() if response.text else {"status": "stopped"}
    
    def get_pipeline_runs(self, namespace: str, pipeline_name: str, pipeline_type: str = "batch") -> List[Dict[str, Any]]:
        """Get pipeline run history"""
        if pipeline_type == "batch":
            endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}/workflows/DataPipelineWorkflow/runs"
        else:  # realtime
            endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}/spark/DataStreamsSparkStreaming/runs"
        
        print(f"Getting {pipeline_type} pipeline runs for: {pipeline_name}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_PIPELINE_RUNS_{pipeline_name}_{pipeline_type.upper()}",
            f"Retrieve run history for {pipeline_type} pipeline '{pipeline_name}' in namespace '{namespace}'"
        )
        return response.json()

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
            "List all available namespaces in the CDAP instance"
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
            json=payload
        )
        return response.json() if response.text else {"status": "created"}


class DataFusionManager:
    """High-level manager for Data Fusion operations"""
    
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
        self.cdap_clients = {}  # Cache CDAP clients by instance
    
    def get_cdap_client(self, instance_name: str) -> CDAPClient:
        """Get or create CDAP client for an instance"""
        if instance_name not in self.cdap_clients:
            api_endpoint = self.instance_client.get_instance_api_endpoint(instance_name)
            self.cdap_clients[instance_name] = CDAPClient(api_endpoint, self.config.auth_token, self.config)
        return self.cdap_clients[instance_name]
    
    # Instance operations
    def create_instance(self, instance_name: str, instance_type: str = "BASIC", 
                       description: str = "Created via API") -> Dict[str, Any]:
        """Create a new Data Fusion instance with basic configuration"""
        instance_config = {
            "type": instance_type,
            "description": description,
            "enableStackdriverLogging": True,
            "enableStackdriverMonitoring": True
        }
        return self.instance_client.create_instance(instance_name, instance_config)
    
    def delete_instance(self, instance_name: str) -> Dict[str, Any]:
        """Delete a Data Fusion instance"""
        return self.instance_client.delete_instance(instance_name)
    
    def list_instances(self) -> List[Dict[str, Any]]:
        """List all instances"""
        return self.instance_client.list_instances()
    
    # Pipeline operations
    def deploy_batch_pipeline(self, instance_name: str, pipeline_name: str, 
                             source_config: Dict[str, Any], sink_config: Dict[str, Any],
                             namespace: str = "default") -> Dict[str, Any]:
        """Deploy a simple batch pipeline"""
        cdap_client = self.get_cdap_client(instance_name)
        
        pipeline_config = {
            "name": pipeline_name,
            "artifact": {
                "name": "cdap-data-pipeline",
                "version": "6.10.0",
                "scope": "system"
            },
            "config": {
                "stages": [
                    {
                        "name": "Source",
                        "plugin": source_config
                    },
                    {
                        "name": "Sink", 
                        "plugin": sink_config
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
        
        return cdap_client.deploy_pipeline(namespace, pipeline_name, pipeline_config)
    
    def delete_pipeline(self, instance_name: str, pipeline_name: str, namespace: str = "default") -> Dict[str, Any]:
        """Delete a pipeline"""
        cdap_client = self.get_cdap_client(instance_name)
        return cdap_client.delete_pipeline(namespace, pipeline_name)
    
    def start_pipeline(self, instance_name: str, pipeline_name: str, 
                      pipeline_type: str = "batch", namespace: str = "default") -> Dict[str, Any]:
        """Start a pipeline"""
        cdap_client = self.get_cdap_client(instance_name)
        if pipeline_type == "batch":
            return cdap_client.start_batch_pipeline(namespace, pipeline_name)
        else:
            return cdap_client.start_realtime_pipeline(namespace, pipeline_name)
    
    def stop_pipeline(self, instance_name: str, pipeline_name: str,
                     pipeline_type: str = "batch", namespace: str = "default") -> Dict[str, Any]:
        """Stop a pipeline"""
        cdap_client = self.get_cdap_client(instance_name)
        if pipeline_type == "batch":
            return cdap_client.stop_batch_pipeline(namespace, pipeline_name)
        else:
            return cdap_client.stop_realtime_pipeline(namespace, pipeline_name)


class TestRunner:
    """Test runner for comprehensive API testing"""
    
    def __init__(self, manager: DataFusionManager):
        self.manager = manager
        self.test_instance_name = f"test-instance-{int(time.time())}"
        self.test_pipeline_name = f"test-pipeline-{int(time.time())}"
    
    def run_comprehensive_tests(self) -> List[TestResult]:
        """Run comprehensive test suite"""
        print("=== Starting Comprehensive API Test Suite ===\n")
        
        # Test 1: List existing instances (should always work)
        self._test_list_instances()
        
        # Test 2: Test invalid instance operations (expected failures)
        self._test_invalid_operations()
        
        # Test 3: Test with existing instances (if any)
        instances = self.manager.list_instances()
        if instances:
            existing_instance = instances[0]['name'].split('/')[-1]
            self._test_existing_instance_operations(existing_instance)
        
        # Test 4: Test pipeline operations on existing instances
        if instances:
            existing_instance = instances[0]['name'].split('/')[-1]
            self._test_pipeline_operations(existing_instance)
        
        return self.manager.config.test_results
    
    def _test_list_instances(self):
        """Test listing instances"""
        try:
            self.manager.list_instances()
            print("✓ List instances test passed")
        except Exception as e:
            print(f"✗ List instances test failed: {e}")
    
    def _test_invalid_operations(self):
        """Test operations that should fail"""
        try:
            # Test getting non-existent instance
            self.manager.instance_client.get_instance("non-existent-instance-12345")
        except Exception:
            print("✓ Get non-existent instance test passed (expected failure)")
        
        try:
            # Test deleting non-existent instance
            self.manager.instance_client.delete_instance("non-existent-instance-12345")
        except Exception:
            print("✓ Delete non-existent instance test passed (expected failure)")
    
    def _test_existing_instance_operations(self, instance_name: str):
        """Test operations on existing instance"""
        try:
            # Test getting existing instance
            self.manager.instance_client.get_instance(instance_name)
            print(f"✓ Get existing instance '{instance_name}' test passed")
        except Exception as e:
            print(f"✗ Get existing instance test failed: {e}")
        
        try:
            # Test getting CDAP endpoint
            self.manager.get_cdap_client(instance_name)
            print(f"✓ Get CDAP client for '{instance_name}' test passed")
        except Exception as e:
            print(f"✗ Get CDAP client test failed: {e}")
    
    def _test_pipeline_operations(self, instance_name: str):
        """Test pipeline operations"""
        try:
            cdap_client = self.manager.get_cdap_client(instance_name)
            
            # Test listing namespaces
            cdap_client.list_namespaces()
            print(f"✓ List namespaces test passed")
            
            # Test listing pipelines
            cdap_client.list_pipelines("default")
            print(f"✓ List pipelines test passed")
            
            # Test listing batch pipelines
            cdap_client.list_batch_pipelines("default")
            print(f"✓ List batch pipelines test passed")
            
        except Exception as e:
            print(f"✗ Pipeline operations test failed: {e}")


class ReportGenerator:
    """Generate CSV reports and display results"""
    
    @staticmethod
    def generate_csv_report(test_results: List[TestResult], filename: str = None) -> str:
        """Generate CSV report of test results"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_fusion_api_test_results_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'test_case', 'api_endpoint', 'method', 'description', 'status',
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
                result.test_case[:30] + '...' if len(result.test_case) > 30 else result.test_case,
                result.method,
                result.status,
                result.response_code,
                f"{result.execution_time:.3f}s",
                result.description[:50] + '...' if len(result.description) > 50 else result.description
            ])
        
        headers = ['Test Case', 'Method', 'Status', 'Code', 'Time', 'Description']
        
        print("\n" + "="*120)
        print("API TEST RESULTS SUMMARY")
        print("="*120)
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
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in test_results:
                if result.status == "FAIL":
                    print(f"   - {result.test_case}: {result.response_code} {result.response_message}")
                    if result.error_details:
                        error_preview = result.error_details[:100] + '...' if len(result.error_details) > 100 else result.error_details
                        print(f"     Error: {error_preview}")


def main():
    """Enhanced main function with comprehensive testing"""
    # Configuration
    PROJECT_ID = "your-project-id"  # Replace with your actual project ID
    LOCATION = "us-central1"        # Replace with your preferred location
    
    try:
        print("=== Google Cloud Data Fusion API Testing Suite ===\n")
        
        # Initialize manager
        manager = DataFusionManager(PROJECT_ID, LOCATION)
        
        # Run comprehensive tests
        test_runner = TestRunner(manager)
        test_results = test_runner.run_comprehensive_tests()
        
        # Generate CSV report
        csv_filename = ReportGenerator.generate_csv_report(test_results)
        print(f"\n📄 CSV report generated: {csv_filename}")
        
        # Display results table
        ReportGenerator.display_results_table(test_results)
        
        print(f"\n✅ Testing completed. Check '{csv_filename}' for detailed results.")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
