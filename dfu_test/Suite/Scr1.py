#!/usr/bin/env python3
"""
Google Cloud Data Fusion Main CRUD Operations Script

This script provides CRUD operations for:
1. Cloud Data Fusion instances (Control Plane API)
2. CDAP pipelines and applications (Data Plane API)
3. Compute profiles and security management

Features:
- Instance-level CRUD operations
- Pipeline deployment and management
- Compute profile management
- Security key management
- Automated test case execution with Pass/Fail tracking
- CSV report generation with detailed test results
- Tabulated output display for easy reading

Requirements:
- Set GOOGLE_AUTH_TOKEN environment variable with your Google Cloud auth token
- Install required packages: requests, google-auth, tabulate

Usage:
    export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)
    python gcp_data_fusion_cp_and_dp.py
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
    type: str  # Operation type (Instance Level, Pipeline Level, etc.)
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

    # =====================================
    # INSTANCE LEVEL OPERATIONS (Control Plane)
    # =====================================
    
    def create_instance(self, instance_name: str, instance_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
            "Instance Level Operation",
            json=payload
        )
        return response.json() if response else None
    
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
    
    def update_instance(self, instance_name: str, update_config: Dict[str, Any], update_mask: str = None) -> Optional[Dict[str, Any]]:
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
            "Instance Level Operation",
            json=update_config, params=params
        )
        return response.json() if response else None
    
    def delete_instance(self, instance_name: str) -> Optional[Dict[str, Any]]:
        """Delete a Data Fusion instance"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances/{instance_name}"
        
        print(f"Deleting Data Fusion instance: {instance_name}")
        response, _ = self._make_request(
            'DELETE', url,
            f"DELETE_INSTANCE_{instance_name}",
            f"Delete Data Fusion instance '{instance_name}'",
            "Instance Level Operation"
        )
        if response:
            return response.json() if response.text else {"status": "deleted"}
        return None
    
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
    
    def restart_instance(self, instance_name: str) -> Optional[Dict[str, Any]]:
        """Restart a Data Fusion instance"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances/{instance_name}:restart"
        
        print(f"Restarting Data Fusion instance: {instance_name}")
        response, _ = self._make_request(
            'POST', url,
            f"RESTART_INSTANCE_{instance_name}",
            f"Restart Data Fusion instance '{instance_name}'",
            "Instance Level Operation",
            json={}
        )
        return response.json() if response else None
    
    def get_instance_api_endpoint(self, instance_name: str) -> Optional[str]:
        """Get the CDAP API endpoint for an instance"""
        instance_details = self.get_instance(instance_name)
        if instance_details:
            api_endpoint = instance_details.get('apiEndpoint')
            if not api_endpoint:
                raise ValueError(f"No API endpoint found for instance {instance_name}")
            return api_endpoint
        return None


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
    
    def _make_request(self, method: str, endpoint: str, test_case: str, description: str, operation_type: str = "Pipeline Level Operation", **kwargs) -> Tuple[Optional[requests.Response], TestResult]:
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
    # PIPELINE LEVEL OPERATIONS (Data Plane)
    # =====================================
    
    def deploy_pipeline(self, namespace: str, pipeline_name: str, pipeline_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Deploy/Create a pipeline using PUT"""
        endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}"
        
        print(f"Deploying pipeline: {pipeline_name} in namespace: {namespace}")
        response, _ = self._make_request(
            'PUT', endpoint,
            f"DEPLOY_PIPELINE_{pipeline_name}",
            f"Deploy pipeline '{pipeline_name}' in namespace '{namespace}' using CDAP API",
            "Pipeline Level Operation",
            json=pipeline_config
        )
        if response:
            return response.json() if response.text else {"status": "deployed"}
        return None
    
    def get_pipeline(self, namespace: str, pipeline_name: str) -> Optional[Dict[str, Any]]:
        """Get pipeline details"""
        endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}"
        
        print(f"Getting pipeline: {pipeline_name} from namespace: {namespace}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_PIPELINE_{pipeline_name}",
            f"Retrieve pipeline details for '{pipeline_name}' from namespace '{namespace}'",
            "Pipeline Level Operation"
        )
        return response.json() if response else None
    
    def update_pipeline(self, namespace: str, pipeline_name: str, pipeline_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a pipeline using PUT (redeploy)"""
        return self.deploy_pipeline(namespace, pipeline_name, pipeline_config)
    
    def delete_pipeline(self, namespace: str, pipeline_name: str) -> Optional[Dict[str, Any]]:
        """Delete a pipeline"""
        endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}"
        
        print(f"Deleting pipeline: {pipeline_name} from namespace: {namespace}")
        response, _ = self._make_request(
            'DELETE', endpoint,
            f"DELETE_PIPELINE_{pipeline_name}",
            f"Delete pipeline '{pipeline_name}' from namespace '{namespace}'",
            "Pipeline Level Operation"
        )
        if response:
            return response.json() if response.text else {"status": "deleted"}
        return None
    
    def list_pipelines(self, namespace: str, artifact_name: str = None) -> Optional[List[Dict[str, Any]]]:
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
            "Pipeline Level Operation",
            params=params
        )
        return response.json() if response else None
    
    def list_batch_pipelines(self, namespace: str) -> Optional[List[Dict[str, Any]]]:
        """List batch pipelines specifically"""
        return self.list_pipelines(namespace, artifact_name="cdap-data-pipeline")
    
    def list_realtime_pipelines(self, namespace: str) -> Optional[List[Dict[str, Any]]]:
        """List real-time pipelines specifically"""
        return self.list_pipelines(namespace, artifact_name="cdap-data-streams")
    
    # =====================================
    # PIPELINE EXECUTION OPERATIONS
    # =====================================
    
    def start_batch_pipeline(self, namespace: str, pipeline_name: str, runtime_args: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Start a batch pipeline"""
        endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}/workflows/DataPipelineWorkflow/start"
        payload = runtime_args or {}
        
        print(f"Starting batch pipeline: {pipeline_name}")
        response, _ = self._make_request(
            'POST', endpoint,
            f"START_BATCH_PIPELINE_{pipeline_name}",
            f"Start execution of batch pipeline '{pipeline_name}' in namespace '{namespace}'",
            "Pipeline Level Execution",
            json=payload
        )
        if response:
            return response.json() if response.text else {"status": "started"}
        return None
    
    def stop_batch_pipeline(self, namespace: str, pipeline_name: str) -> Optional[Dict[str, Any]]:
        """Stop a batch pipeline"""
        endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}/workflows/DataPipelineWorkflow/stop"
        
        print(f"Stopping batch pipeline: {pipeline_name}")
        response, _ = self._make_request(
            'POST', endpoint,
            f"STOP_BATCH_PIPELINE_{pipeline_name}",
            f"Stop execution of batch pipeline '{pipeline_name}' in namespace '{namespace}'",
            "Pipeline Level Execution",
            json={}
        )
        if response:
            return response.json() if response.text else {"status": "stopped"}
        return None
    
    def start_realtime_pipeline(self, namespace: str, pipeline_name: str, runtime_args: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Start a real-time pipeline"""
        endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}/spark/DataStreamsSparkStreaming/start"
        payload = runtime_args or {}
        
        print(f"Starting real-time pipeline: {pipeline_name}")
        response, _ = self._make_request(
            'POST', endpoint,
            f"START_REALTIME_PIPELINE_{pipeline_name}",
            f"Start execution of real-time pipeline '{pipeline_name}' in namespace '{namespace}'",
            "Pipeline Level Execution",
            json=payload
        )
        if response:
            return response.json() if response.text else {"status": "started"}
        return None
    
    def stop_realtime_pipeline(self, namespace: str, pipeline_name: str) -> Optional[Dict[str, Any]]:
        """Stop a real-time pipeline"""
        endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}/spark/DataStreamsSparkStreaming/stop"
        
        print(f"Stopping real-time pipeline: {pipeline_name}")
        response, _ = self._make_request(
            'POST', endpoint,
            f"STOP_REALTIME_PIPELINE_{pipeline_name}",
            f"Stop execution of real-time pipeline '{pipeline_name}' in namespace '{namespace}'",
            "Pipeline Level Execution",
            json={}
        )
        if response:
            return response.json() if response.text else {"status": "stopped"}
        return None
    
    def get_pipeline_runs(self, namespace: str, pipeline_name: str, pipeline_type: str = "batch") -> Optional[List[Dict[str, Any]]]:
        """Get pipeline run history"""
        if pipeline_type == "batch":
            endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}/workflows/DataPipelineWorkflow/runs"
        else:  # realtime
            endpoint = f"/v3/namespaces/{namespace}/apps/{pipeline_name}/spark/DataStreamsSparkStreaming/runs"
        
        print(f"Getting {pipeline_type} pipeline runs for: {pipeline_name}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_PIPELINE_RUNS_{pipeline_name}_{pipeline_type.upper()}",
            f"Retrieve run history for {pipeline_type} pipeline '{pipeline_name}' in namespace '{namespace}'",
            "Pipeline Level Execution"
        )
        return response.json() if response else None

    # =====================================
    # COMPUTE PROFILE OPERATIONS
    # =====================================
    
    def list_compute_profiles(self, namespace: str) -> Optional[List[Dict[str, Any]]]:
        """List compute profiles in a namespace"""
        endpoint = f"/v3/namespaces/{namespace}/profiles"
        
        print(f"Listing compute profiles in namespace: {namespace}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"LIST_COMPUTE_PROFILES_{namespace}",
            f"List all compute profiles available in namespace '{namespace}'",
            "Compute Profile Operation"
        )
        return response.json() if response else None
    
    def create_compute_profile(self, namespace: str, profile_name: str, profile_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a compute profile using PUT"""
        endpoint = f"/v3/namespaces/{namespace}/profiles/{profile_name}"
        
        print(f"Creating compute profile: {profile_name} in namespace: {namespace}")
        response, _ = self._make_request(
            'PUT', endpoint,
            f"CREATE_COMPUTE_PROFILE_{namespace}_{profile_name}",
            f"Create compute profile '{profile_name}' in namespace '{namespace}' with specified configuration",
            "Compute Profile Operation",
            json=profile_config
        )
        if response:
            return response.json() if response.text else {"status": "created"}
        return None
    
    def get_compute_profile(self, namespace: str, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get compute profile details"""
        endpoint = f"/v3/namespaces/{namespace}/profiles/{profile_name}"
        
        print(f"Getting compute profile: {profile_name} from namespace: {namespace}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_COMPUTE_PROFILE_{namespace}_{profile_name}",
            f"Retrieve details for compute profile '{profile_name}' in namespace '{namespace}'",
            "Compute Profile Operation"
        )
        return response.json() if response else None
    
    def update_compute_profile(self, namespace: str, profile_name: str, profile_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a compute profile using PUT"""
        endpoint = f"/v3/namespaces/{namespace}/profiles/{profile_name}"
        
        print(f"Updating compute profile: {profile_name} in namespace: {namespace}")
        response, _ = self._make_request(
            'PUT', endpoint,
            f"UPDATE_COMPUTE_PROFILE_{namespace}_{profile_name}",
            f"Update compute profile '{profile_name}' in namespace '{namespace}' with new configuration",
            "Compute Profile Operation",
            json=profile_config
        )
        if response:
            return response.json() if response.text else {"status": "updated"}
        return None
    
    def delete_compute_profile(self, namespace: str, profile_name: str) -> Optional[Dict[str, Any]]:
        """Delete a compute profile"""
        endpoint = f"/v3/namespaces/{namespace}/profiles/{profile_name}"
        
        print(f"Deleting compute profile: {profile_name} from namespace: {namespace}")
        response, _ = self._make_request(
            'DELETE', endpoint,
            f"DELETE_COMPUTE_PROFILE_{namespace}_{profile_name}",
            f"Delete compute profile '{profile_name}' from namespace '{namespace}'",
            "Compute Profile Operation"
        )
        if response:
            return response.json() if response.text else {"status": "deleted"}
        return None
    
    # =====================================
    # SECURITY AND ACCESS CONTROL
    # =====================================
    
    def list_secure_keys(self, namespace: str) -> Optional[List[Dict[str, Any]]]:
        """List secure keys in a namespace"""
        endpoint = f"/v3/namespaces/{namespace}/securekeys"
        
        print(f"Listing secure keys in namespace: {namespace}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"LIST_SECURE_KEYS_{namespace}",
            f"List all secure keys in namespace '{namespace}'",
            "Security Operation"
        )
        return response.json() if response else None
    
    def create_secure_key(self, namespace: str, key_name: str, key_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a secure key using PUT"""
        endpoint = f"/v3/namespaces/{namespace}/securekeys/{key_name}"
        
        print(f"Creating secure key: {key_name} in namespace: {namespace}")
        response, _ = self._make_request(
            'PUT', endpoint,
            f"CREATE_SECURE_KEY_{namespace}_{key_name}",
            f"Create secure key '{key_name}' in namespace '{namespace}'",
            "Security Operation",
            json=key_data
        )
        if response:
            return response.json() if response.text else {"status": "created"}
        return None
    
    def get_secure_key_metadata(self, namespace: str, key_name: str) -> Optional[Dict[str, Any]]:
        """Get secure key metadata"""
        endpoint = f"/v3/namespaces/{namespace}/securekeys/{key_name}/metadata"
        
        print(f"Getting secure key metadata: {key_name} from namespace: {namespace}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_SECURE_KEY_METADATA_{namespace}_{key_name}",
            f"Retrieve metadata for secure key '{key_name}' in namespace '{namespace}'",
            "Security Operation"
        )
        return response.json() if response else None
    
    def delete_secure_key(self, namespace: str, key_name: str) -> Optional[Dict[str, Any]]:
        """Delete a secure key"""
        endpoint = f"/v3/namespaces/{namespace}/securekeys/{key_name}"
        
        print(f"Deleting secure key: {key_name} from namespace: {namespace}")
        response, _ = self._make_request(
            'DELETE', endpoint,
            f"DELETE_SECURE_KEY_{namespace}_{key_name}",
            f"Delete secure key '{key_name}' from namespace '{namespace}'",
            "Security Operation"
        )
        if response:
            return response.json() if response.text else {"status": "deleted"}
        return None


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
    
    def get_cdap_client(self, instance_name: str) -> Optional[CDAPClient]:
        """Get or create CDAP client for an instance"""
        if instance_name not in self.cdap_clients:
            api_endpoint = self.instance_client.get_instance_api_endpoint(instance_name)
            if api_endpoint:
                self.cdap_clients[instance_name] = CDAPClient(api_endpoint, self.config.auth_token, self.config)
            else:
                return None
        return self.cdap_clients[instance_name]
    
    # Instance operations
    def create_instance(self, instance_name: str, instance_type: str = "BASIC", 
                       description: str = "Created via API") -> Optional[Dict[str, Any]]:
        """Create a new Data Fusion instance with basic configuration"""
        instance_config = {
            "type": instance_type,
            "description": description,
            "enableStackdriverLogging": True,
            "enableStackdriverMonitoring": True
        }
        return self.instance_client.create_instance(instance_name, instance_config)
    
    def delete_instance(self, instance_name: str) -> Optional[Dict[str, Any]]:
        """Delete a Data Fusion instance"""
        return self.instance_client.delete_instance(instance_name)
    
    def list_instances(self) -> List[Dict[str, Any]]:
        """List all instances"""
        return self.instance_client.list_instances()
    
    # Pipeline operations
    def deploy_batch_pipeline(self, instance_name: str, pipeline_name: str, 
                             source_config: Dict[str, Any], sink_config: Dict[str, Any],
                             namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Deploy a simple batch pipeline"""
        cdap_client = self.get_cdap_client(instance_name)
        if not cdap_client:
            return None
        
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
    
    def delete_pipeline(self, instance_name: str, pipeline_name: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Delete a pipeline"""
        cdap_client = self.get_cdap_client(instance_name)
        if not cdap_client:
            return None
        return cdap_client.delete_pipeline(namespace, pipeline_name)
    
    def start_pipeline(self, instance_name: str, pipeline_name: str, 
                      pipeline_type: str = "batch", namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Start a pipeline"""
        cdap_client = self.get_cdap_client(instance_name)
        if not cdap_client:
            return None
        if pipeline_type == "batch":
            return cdap_client.start_batch_pipeline(namespace, pipeline_name)
        else:
            return cdap_client.start_realtime_pipeline(namespace, pipeline_name)
    
    def stop_pipeline(self, instance_name: str, pipeline_name: str,
                     pipeline_type: str = "batch", namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Stop a pipeline"""
        cdap_client = self.get_cdap_client(instance_name)
        if not cdap_client:
            return None
        if pipeline_type == "batch":
            return cdap_client.stop_batch_pipeline(namespace, pipeline_name)
        else:
            return cdap_client.stop_realtime_pipeline(namespace, pipeline_name)
    
    # Compute profile management
    def create_dataproc_compute_profile(self, instance_name: str, namespace: str, 
                                      profile_name: str, project_id: str, region: str,
                                      machine_type: str = "n1-standard-4",
                                      num_workers: int = 2) -> Optional[Dict[str, Any]]:
        """Create a Dataproc compute profile with common configurations"""
        cdap_client = self.get_cdap_client(instance_name)
        if not cdap_client:
            return None
        
        profile_config = {
            "label": f"Dataproc Profile - {profile_name}",
            "description": f"Dataproc compute profile for {namespace} namespace",
            "provisioner": {
                "name": "gcp-dataproc",
                "properties": [
                    {"name": "projectId", "value": project_id},
                    {"name": "region", "value": region},
                    {"name": "zone", "value": f"{region}-a"},
                    {"name": "masterInstanceType", "value": machine_type},
                    {"name": "workerInstanceType", "value": machine_type},
                    {"name": "numWorkers", "value": str(num_workers)},
                    {"name": "network", "value": "default"},
                    {"name": "diskSizeGb", "value": "100"},
                    {"name": "stackdriverLoggingEnabled", "value": "true"},
                    {"name": "stackdriverMonitoringEnabled", "value": "true"}
                ]
            }
        }
        
        return cdap_client.create_compute_profile(namespace, profile_name, profile_config)
    
    def create_secure_key_for_database(self, instance_name: str, namespace: str, 
                                     key_name: str, connection_string: str, 
                                     username: str, password: str) -> Optional[Dict[str, Any]]:
        """Create a secure key for database connections"""
        cdap_client = self.get_cdap_client(instance_name)
        if not cdap_client:
            return None
        
        key_data = {
            "description": f"Database connection credentials for {key_name}",
            "data": json.dumps({
                "connectionString": connection_string,
                "username": username,
                "password": password
            }),
            "properties": {
                "type": "database-credentials",
                "database": key_name
            }
        }
        
        return cdap_client.create_secure_key(namespace, key_name, key_data)


class TestRunner:
    """Test runner for main API testing"""
    
    def __init__(self, manager: DataFusionManager):
        self.manager = manager
        self.test_instance_name = f"test-instance-{int(time.time())}"
        self.test_pipeline_name = f"test-pipeline-{int(time.time())}"
        self.test_profile_name = f"test-profile-{int(time.time())}"
        self.test_key_name = f"test-key-{int(time.time())}"
    
    def run_comprehensive_tests(self) -> List[TestResult]:
        """Run comprehensive test suite"""
        print("=== Starting Main Data Fusion API Test Suite ===\n")
        
        # Test 1: Instance Level Operations (Control Plane)
        self._test_instance_operations()
        
        # Test 2: Pipeline Level Operations (Data Plane) - if instances exist
        instances = self.manager.list_instances()
        if instances:
            existing_instance = instances[0]['name'].split('/')[-1]
            print(f"\n--- Testing on instance: {existing_instance} ---\n")
            
            # Pipeline CRUD operations
            self._test_pipeline_crud_operations(existing_instance)
            
            # Pipeline execution operations
            self._test_pipeline_execution_operations(existing_instance)
            
            # Compute profile operations
            self._test_compute_profile_operations(existing_instance)
            
            # Security operations
            self._test_security_operations(existing_instance)
        else:
            print("No instances found for testing pipeline operations")
        
        return self.manager.config.test_results
    
    def _test_instance_operations(self):
        """Test all instance level operations"""
        print("=== Testing Instance Level Operations ===")
        
        # LIST instances (should always work)
        try:
            instances = self.manager.list_instances()
            print(f"✓ LIST_INSTANCES test passed (found {len(instances)} instances)")
        except Exception as e:
            print(f"✗ LIST_INSTANCES test failed: {e}")
        
        # Test instance CRUD with a non-existent instance (expected failures)
        non_existent = "non-existent-instance-12345"
        
        # GET non-existent instance (expected failure)
        try:
            self.manager.instance_client.get_instance(non_existent)
            print(f"✗ GET_INSTANCE_{non_existent} should have failed")
        except Exception:
            print(f"✓ GET_INSTANCE_{non_existent} test passed (expected failure)")
        
        # UPDATE non-existent instance (expected failure)
        try:
            self.manager.instance_client.update_instance(non_existent, {"description": "Updated"})
            print(f"✗ UPDATE_INSTANCE_{non_existent} should have failed")
        except Exception:
            print(f"✓ UPDATE_INSTANCE_{non_existent} test passed (expected failure)")
        
        # DELETE non-existent instance (expected failure)
        try:
            self.manager.instance_client.delete_instance(non_existent)
            print(f"✗ DELETE_INSTANCE_{non_existent} should have failed")
        except Exception:
            print(f"✓ DELETE_INSTANCE_{non_existent} test passed (expected failure)")
        
        # RESTART non-existent instance (expected failure)
        try:
            self.manager.instance_client.restart_instance(non_existent)
            print(f"✗ RESTART_INSTANCE_{non_existent} should have failed")
        except Exception:
            print(f"✓ RESTART_INSTANCE_{non_existent} test passed (expected failure)")
        
        # Note: CREATE_INSTANCE is expensive and long-running, so we skip it in tests
        print("ℹ CREATE_INSTANCE test skipped (expensive operation)")
    
    def _test_pipeline_crud_operations(self, instance_name: str):
        """Test complete pipeline CRUD operations"""
        print("\n=== Testing Pipeline Level CRUD Operations ===")
        
        cdap_client = self.manager.get_cdap_client(instance_name)
        if not cdap_client:
            print("✗ Could not get CDAP client for pipeline operations")
            return
        
        namespace = "default"
        
        # LIST all pipelines
        try:
            pipelines = cdap_client.list_pipelines(namespace)
            print(f"✓ LIST_PIPELINES_{namespace} test passed")
        except Exception as e:
            print(f"✗ LIST_PIPELINES_{namespace} test failed: {e}")
        
        # LIST batch pipelines specifically
        try:
            batch_pipelines = cdap_client.list_batch_pipelines(namespace)
            print(f"✓ LIST_BATCH_PIPELINES_{namespace} test passed")
        except Exception as e:
            print(f"✗ LIST_BATCH_PIPELINES_{namespace} test failed: {e}")
        
        # LIST realtime pipelines specifically
        try:
            realtime_pipelines = cdap_client.list_realtime_pipelines(namespace)
            print(f"✓ LIST_REALTIME_PIPELINES_{namespace} test passed")
        except Exception as e:
            print(f"✗ LIST_REALTIME_PIPELINES_{namespace} test failed: {e}")
        
        # Test pipeline CRUD with test pipeline
        test_pipeline_config = {
            "name": self.test_pipeline_name,
            "description": "Test pipeline for API validation",
            "artifact": {
                "name": "cdap-data-pipeline",
                "version": "6.10.0",
                "scope": "system"
            },
            "config": {
                "stages": [
                    {
                        "name": "MockSource",
                        "plugin": {
                            "name": "Mock",
                            "type": "batchsource",
                            "label": "Mock Source",
                            "artifact": {
                                "name": "core-plugins",
                                "version": "2.11.0",
                                "scope": "system"
                            },
                            "properties": {}
                        }
                    },
                    {
                        "name": "MockSink",
                        "plugin": {
                            "name": "Mock",
                            "type": "batchsink",
                            "label": "Mock Sink",
                            "artifact": {
                                "name": "core-plugins",
                                "version": "2.11.0",
                                "scope": "system"
                            },
                            "properties": {}
                        }
                    }
                ],
                "connections": [
                    {
                        "from": "MockSource",
                        "to": "MockSink"
                    }
                ],
                "engine": "spark"
            }
        }
        
        # CREATE/DEPLOY pipeline
        try:
            cdap_client.deploy_pipeline(namespace, self.test_pipeline_name, test_pipeline_config)
            print(f"✓ DEPLOY_PIPELINE_{self.test_pipeline_name} test passed")
            
            # GET pipeline
            try:
                pipeline_details = cdap_client.get_pipeline(namespace, self.test_pipeline_name)
                print(f"✓ GET_PIPELINE_{self.test_pipeline_name} test passed")
            except Exception as e:
                print(f"✗ GET_PIPELINE_{self.test_pipeline_name} test failed: {e}")
            
            # UPDATE pipeline (redeploy with changes)
            try:
                test_pipeline_config["description"] = "Updated test pipeline"
                cdap_client.update_pipeline(namespace, self.test_pipeline_name, test_pipeline_config)
                print(f"✓ UPDATE_PIPELINE_{self.test_pipeline_name} test passed")
            except Exception as e:
                print(f"✗ UPDATE_PIPELINE_{self.test_pipeline_name} test failed: {e}")
            
            # DELETE pipeline
            try:
                cdap_client.delete_pipeline(namespace, self.test_pipeline_name)
                print(f"✓ DELETE_PIPELINE_{self.test_pipeline_name} test passed")
            except Exception as e:
                print(f"✗ DELETE_PIPELINE_{self.test_pipeline_name} test failed: {e}")
                
        except Exception as e:
            print(f"✗ DEPLOY_PIPELINE_{self.test_pipeline_name} test failed: {e}")
    
    def _test_pipeline_execution_operations(self, instance_name: str):
        """Test pipeline execution operations"""
        print("\n=== Testing Pipeline Level Execution Operations ===")
        
        cdap_client = self.manager.get_cdap_client(instance_name)
        if not cdap_client:
            print("✗ Could not get CDAP client for pipeline execution")
            return
        
        namespace = "default"
        
        # Test with non-existent pipeline (expected failures)
        non_existent_pipeline = "non-existent-pipeline-12345"
        
        # START batch pipeline (expected failure)
        try:
            cdap_client.start_batch_pipeline(namespace, non_existent_pipeline)
            print(f"✗ START_BATCH_PIPELINE_{non_existent_pipeline} should have failed")
        except Exception:
            print(f"✓ START_BATCH_PIPELINE_{non_existent_pipeline} test passed (expected failure)")
        
        # STOP batch pipeline (expected failure)
        try:
            cdap_client.stop_batch_pipeline(namespace, non_existent_pipeline)
            print(f"✗ STOP_BATCH_PIPELINE_{non_existent_pipeline} should have failed")
        except Exception:
            print(f"✓ STOP_BATCH_PIPELINE_{non_existent_pipeline} test passed (expected failure)")
        
        # START realtime pipeline (expected failure)
        try:
            cdap_client.start_realtime_pipeline(namespace, non_existent_pipeline)
            print(f"✗ START_REALTIME_PIPELINE_{non_existent_pipeline} should have failed")
        except Exception:
            print(f"✓ START_REALTIME_PIPELINE_{non_existent_pipeline} test passed (expected failure)")
        
        # STOP realtime pipeline (expected failure)
        try:
            cdap_client.stop_realtime_pipeline(namespace, non_existent_pipeline)
            print(f"✗ STOP_REALTIME_PIPELINE_{non_existent_pipeline} should have failed")
        except Exception:
            print(f"✓ STOP_REALTIME_PIPELINE_{non_existent_pipeline} test passed (expected failure)")
        
        # GET pipeline runs
        try:
            cdap_client.get_pipeline_runs(namespace, non_existent_pipeline, "batch")
            print(f"✗ GET_PIPELINE_RUNS_{non_existent_pipeline}_BATCH should have failed")
        except Exception:
            print(f"✓ GET_PIPELINE_RUNS_{non_existent_pipeline}_BATCH test passed (expected failure)")
    
    def _test_compute_profile_operations(self, instance_name: str):
        """Test compute profile operations"""
        print("\n=== Testing Compute Profile Operations ===")
        
        cdap_client = self.manager.get_cdap_client(instance_name)
        if not cdap_client:
            print("✗ Could not get CDAP client for compute profile operations")
            return
        
        namespace = "default"
        
        # LIST compute profiles
        try:
            profiles = cdap_client.list_compute_profiles(namespace)
            print(f"✓ LIST_COMPUTE_PROFILES_{namespace} test passed")
        except Exception as e:
            print(f"✗ LIST_COMPUTE_PROFILES_{namespace} test failed: {e}")
        
        # Test compute profile CRUD
        test_profile_config = {
            "label": "Test Compute Profile",
            "description": "Test compute profile for API testing",
            "provisioner": {
                "name": "gcp-dataproc",
                "properties": [
                    {"name": "projectId", "value": self.manager.config.project_id},
                    {"name": "region", "value": self.manager.config.location},
                    {"name": "masterInstanceType", "value": "n1-standard-2"},
                    {"name": "workerInstanceType", "value": "n1-standard-2"},
                    {"name": "numWorkers", "value": "2"}
                ]
            }
        }
        
        # CREATE compute profile
        try:
            cdap_client.create_compute_profile(namespace, self.test_profile_name, test_profile_config)
            print(f"✓ CREATE_COMPUTE_PROFILE_{namespace}_{self.test_profile_name} test passed")
            
            # GET compute profile
            try:
                profile = cdap_client.get_compute_profile(namespace, self.test_profile_name)
                print(f"✓ GET_COMPUTE_PROFILE_{namespace}_{self.test_profile_name} test passed")
            except Exception as e:
                print(f"✗ GET_COMPUTE_PROFILE_{namespace}_{self.test_profile_name} test failed: {e}")
            
            # UPDATE compute profile
            try:
                test_profile_config["description"] = "Updated compute profile"
                cdap_client.update_compute_profile(namespace, self.test_profile_name, test_profile_config)
                print(f"✓ UPDATE_COMPUTE_PROFILE_{namespace}_{self.test_profile_name} test passed")
            except Exception as e:
                print(f"✗ UPDATE_COMPUTE_PROFILE_{namespace}_{self.test_profile_name} test failed: {e}")
            
            # DELETE compute profile
            try:
                cdap_client.delete_compute_profile(namespace, self.test_profile_name)
                print(f"✓ DELETE_COMPUTE_PROFILE_{namespace}_{self.test_profile_name} test passed")
            except Exception as e:
                print(f"✗ DELETE_COMPUTE_PROFILE_{namespace}_{self.test_profile_name} test failed: {e}")
                
        except Exception as e:
            print(f"✗ CREATE_COMPUTE_PROFILE_{namespace}_{self.test_profile_name} test failed: {e}")
    
    def _test_security_operations(self, instance_name: str):
        """Test security and access control operations"""
        print("\n=== Testing Security Operations ===")
        
        cdap_client = self.manager.get_cdap_client(instance_name)
        if not cdap_client:
            print("✗ Could not get CDAP client for security operations")
            return
        
        namespace = "default"
        
        # LIST secure keys
        try:
            keys = cdap_client.list_secure_keys(namespace)
            print(f"✓ LIST_SECURE_KEYS_{namespace} test passed")
        except Exception as e:
            print(f"✗ LIST_SECURE_KEYS_{namespace} test failed: {e}")
        
        # Test secure key CRUD
        test_key_data = {
            "description": "Test secure key for API testing",
            "data": "test-secret-value",
            "properties": {
                "test-property": "test-value"
            }
        }
        
        # CREATE secure key
        try:
            cdap_client.create_secure_key(namespace, self.test_key_name, test_key_data)
            print(f"✓ CREATE_SECURE_KEY_{namespace}_{self.test_key_name} test passed")
            
            # GET secure key metadata
            try:
                metadata = cdap_client.get_secure_key_metadata(namespace, self.test_key_name)
                print(f"✓ GET_SECURE_KEY_METADATA_{namespace}_{self.test_key_name} test passed")
            except Exception as e:
                print(f"✗ GET_SECURE_KEY_METADATA_{namespace}_{self.test_key_name} test failed: {e}")
            
            # DELETE secure key
            try:
                cdap_client.delete_secure_key(namespace, self.test_key_name)
                print(f"✓ DELETE_SECURE_KEY_{namespace}_{self.test_key_name} test passed")
            except Exception as e:
                print(f"✗ DELETE_SECURE_KEY_{namespace}_{self.test_key_name} test failed: {e}")
                
        except Exception as e:
            print(f"✗ CREATE_SECURE_KEY_{namespace}_{self.test_key_name} test failed: {e}")


class ReportGenerator:
    """Generate CSV reports and display results"""
    
    @staticmethod
    def generate_csv_report(test_results: List[TestResult], filename: str = None) -> str:
        """Generate CSV report of test results"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_fusion_main_test_results_{timestamp}.csv"
        
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
        
        print("\n" + "="*120)
        print("MAIN DATA FUSION API TEST RESULTS SUMMARY")
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
    """Main function with comprehensive testing"""
    # Configuration
    PROJECT_ID = "your-project-id"  # Replace with your actual project ID
    LOCATION = "us-central1"        # Replace with your preferred location
    
    try:
        print("=== Google Cloud Data Fusion Main API Testing Suite ===\n")
        
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
        
        print(f"\n✅ Main testing completed. Check '{csv_filename}' for detailed results.")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
