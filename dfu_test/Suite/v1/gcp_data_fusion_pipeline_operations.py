#!/usr/bin/env python3
"""
Google Cloud Data Fusion Pipeline Level Operations Script (Data Plane)

This script tests pipeline-level CRUD operations, execution, compute profiles, and security.

Features:
- Pipeline CRUD operations (CREATE, GET, UPDATE, DELETE, LIST)
- Pipeline execution operations (START, STOP, GET_RUNS)
- Compute profile management
- Security key management
- Command-line parameter support
- CSV report generation
- Tabulated output display
- Summary statistics

Usage:
    python gcp_data_fusion_pipeline_operations.py --project PROJECT_ID --location LOCATION --instance INSTANCE_NAME
    
Examples:
    # Test all pipeline operations
    python gcp_data_fusion_pipeline_operations.py --project my-project --location us-central1 --instance my-instance
    
    # Test in specific namespace
    python gcp_data_fusion_pipeline_operations.py --project my-project --location us-central1 --instance my-instance --namespace production
    
    # Skip cleanup (keep test resources)
    python gcp_data_fusion_pipeline_operations.py --project my-project --location us-central1 --instance my-instance --skip-cleanup

Requirements:
    export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)
"""

import os
import json
import time
import csv
import argparse
import requests
from typing import Dict, List, Optional, Any, Tuple
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
    type: str
    status: str
    response_code: int
    response_message: str
    execution_time: float
    timestamp: str
    error_details: str = ""
    expected_result: str = ""
    actual_result: str = ""
    test_passed: bool = False


@dataclass
class Config:
    """Configuration for Data Fusion operations"""
    project_id: str
    location: str
    instance_name: str
    namespace: str
    auth_token: str
    base_url: str = "https://datafusion.googleapis.com"
    api_version: str = "v1beta1"
    test_results: List[TestResult] = field(default_factory=list)
    processed_tests: set = field(default_factory=set)  # Track processed test cases

    def __post_init__(self):
        if not self.auth_token:
            raise ValueError("GOOGLE_AUTH_TOKEN environment variable must be set")


class DataFusionInstanceClient:
    """Client for getting instance details"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.auth_token}',
            'Content-Type': 'application/json'
        })
    
    def get_instance_api_endpoint(self) -> str:
        """Get the CDAP API endpoint for the instance"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances/{self.config.instance_name}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        instance_details = response.json()
        api_endpoint = instance_details.get('apiEndpoint')
        if not api_endpoint:
            raise ValueError(f"No API endpoint found for instance {self.config.instance_name}")
        
        return api_endpoint


class CDAPClient:
    """Client for CDAP Data Plane operations"""
    
    def __init__(self, cdap_endpoint: str, config: Config):
        self.cdap_endpoint = cdap_endpoint.rstrip('/')
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.auth_token}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, test_case: str, description: str, 
                     operation_type: str = "Pipeline Level Operation", 
                     expected_result: str = "", **kwargs) -> Tuple[Optional[requests.Response], TestResult]:
        """Make HTTP request with test case tracking"""
        # Create unique test identifier
        url = f"{self.cdap_endpoint}{endpoint}"
        test_id = f"{test_case}_{method}_{endpoint}"
        
        # Check if this exact test has been processed
        if test_id in self.config.processed_tests:
            print(f"Skipping duplicate test case: {test_case}")
            return None, None
        
        self.config.processed_tests.add(test_id)
        
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            response = self.session.request(method, url, **kwargs)
            execution_time = time.time() - start_time
            
            # Determine actual result
            if response.status_code < 300:
                actual_result = f"Success: {response.status_code} {response.reason}"
            elif response.status_code < 500:
                actual_result = f"Client Error: {response.status_code} {response.reason}"
            else:
                actual_result = f"Server Error: {response.status_code} {response.reason}"
            
            # Determine if test passed based on expected result
            test_passed = self._evaluate_test_result(response.status_code, expected_result)
            status = "PASS" if test_passed else "FAIL"
            
            error_details = "" if response.status_code < 400 else response.text[:200]
            
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
                error_details=error_details,
                expected_result=expected_result,
                actual_result=actual_result,
                test_passed=test_passed
            )
            
            self.config.test_results.append(test_result)
            
            # Only raise for status if test failed unexpectedly
            if not test_passed and "should fail" not in expected_result.lower():
                response.raise_for_status()
                
            return response, test_result
            
        except requests.exceptions.RequestException as e:
            execution_time = time.time() - start_time
            error_details = str(e)
            response_code = getattr(e.response, 'status_code', 0) if hasattr(e, 'response') else 0
            response_message = getattr(e.response, 'reason', 'Request Failed') if hasattr(e, 'response') else 'Request Failed'
            
            actual_result = f"Exception: {type(e).__name__} - {str(e)[:100]}"
            test_passed = self._evaluate_test_result(response_code, expected_result)
            status = "PASS" if test_passed else "FAIL"
            
            test_result = TestResult(
                test_case=test_case,
                api_endpoint=url,
                method=method,
                description=description,
                type=operation_type,
                status=status,
                response_code=response_code,
                response_message=response_message,
                execution_time=execution_time,
                timestamp=timestamp,
                error_details=error_details,
                expected_result=expected_result,
                actual_result=actual_result,
                test_passed=test_passed
            )
            
            self.config.test_results.append(test_result)
            
            # Only re-raise if test failed unexpectedly
            if not test_passed and "should fail" not in expected_result.lower():
                raise
            
            return None, test_result
    
    def _evaluate_test_result(self, status_code: int, expected_result: str) -> bool:
        """Evaluate if test passed based on expected result"""
        expected_lower = expected_result.lower()
        
        if "should fail" in expected_lower or "expected failure" in expected_lower:
            # Test should fail
            return status_code >= 400
        elif "should succeed" in expected_lower or "200" in expected_result:
            # Test should succeed
            return 200 <= status_code < 300
        elif "404" in expected_result:
            return status_code == 404
        elif "400" in expected_result:
            return status_code == 400
        else:
            # Default: success means 2xx status
            return 200 <= status_code < 300

    # Pipeline CRUD Operations
    def deploy_pipeline(self, pipeline_name: str, pipeline_config: Dict[str, Any], 
                       expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Deploy/Create a pipeline"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/apps/{pipeline_name}"
        
        print(f"Deploying pipeline: {pipeline_name}")
        response, _ = self._make_request(
            'PUT', endpoint,
            f"DEPLOY_PIPELINE_{pipeline_name}",
            f"Deploy pipeline '{pipeline_name}' in namespace '{self.config.namespace}'",
            "Pipeline Level Operation",
            expected_result=expected_result,
            json=pipeline_config
        )
        if response:
            return response.json() if response.text else {"status": "deployed"}
        return None
    
    def get_pipeline(self, pipeline_name: str, expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Get pipeline details"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/apps/{pipeline_name}"
        
        print(f"Getting pipeline: {pipeline_name}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_PIPELINE_{pipeline_name}",
            f"Retrieve pipeline '{pipeline_name}' from namespace '{self.config.namespace}'",
            "Pipeline Level Operation",
            expected_result=expected_result
        )
        return response.json() if response else None
    
    def update_pipeline(self, pipeline_name: str, pipeline_config: Dict[str, Any],
                       expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Update pipeline (redeploy)"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/apps/{pipeline_name}"
        
        print(f"Updating pipeline: {pipeline_name}")
        response, _ = self._make_request(
            'PUT', endpoint,
            f"UPDATE_PIPELINE_{pipeline_name}",
            f"Update pipeline '{pipeline_name}' in namespace '{self.config.namespace}'",
            "Pipeline Level Operation",
            expected_result=expected_result,
            json=pipeline_config
        )
        if response:
            return response.json() if response.text else {"status": "updated"}
        return None
    
    def delete_pipeline(self, pipeline_name: str, expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Delete a pipeline"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/apps/{pipeline_name}"
        
        print(f"Deleting pipeline: {pipeline_name}")
        response, _ = self._make_request(
            'DELETE', endpoint,
            f"DELETE_PIPELINE_{pipeline_name}",
            f"Delete pipeline '{pipeline_name}' from namespace '{self.config.namespace}'",
            "Pipeline Level Operation",
            expected_result=expected_result
        )
        if response:
            return response.json() if response.text else {"status": "deleted"}
        return None
    
    def list_pipelines(self, artifact_name: str = None) -> Optional[List[Dict[str, Any]]]:
        """List pipelines"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/apps"
        params = {}
        if artifact_name:
            params['artifactName'] = artifact_name
        
        test_case = f"LIST_PIPELINES_{self.config.namespace}"
        if artifact_name:
            test_case += f"_{artifact_name}"
            
        print(f"Listing pipelines in namespace: {self.config.namespace}")
        response, _ = self._make_request(
            'GET', endpoint,
            test_case,
            f"List all pipelines in namespace '{self.config.namespace}'" + (f" with artifact '{artifact_name}'" if artifact_name else ""),
            "Pipeline Level Operation",
            expected_result="Should succeed with 200 OK and return pipeline list",
            params=params
        )
        return response.json() if response else None
    
    # Pipeline Execution Operations
    def start_batch_pipeline(self, pipeline_name: str, runtime_args: Dict[str, Any] = None,
                           expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Start a batch pipeline"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/apps/{pipeline_name}/workflows/DataPipelineWorkflow/start"
        
        print(f"Starting batch pipeline: {pipeline_name}")
        response, _ = self._make_request(
            'POST', endpoint,
            f"START_BATCH_PIPELINE_{pipeline_name}",
            f"Start batch pipeline '{pipeline_name}' in namespace '{self.config.namespace}'",
            "Pipeline Level Execution",
            expected_result=expected_result,
            json=runtime_args or {}
        )
        if response:
            return response.json() if response.text else {"status": "started"}
        return None
    
    def stop_batch_pipeline(self, pipeline_name: str, expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Stop a batch pipeline"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/apps/{pipeline_name}/workflows/DataPipelineWorkflow/stop"
        
        print(f"Stopping batch pipeline: {pipeline_name}")
        response, _ = self._make_request(
            'POST', endpoint,
            f"STOP_BATCH_PIPELINE_{pipeline_name}",
            f"Stop batch pipeline '{pipeline_name}' in namespace '{self.config.namespace}'",
            "Pipeline Level Execution",
            expected_result=expected_result,
            json={}
        )
        if response:
            return response.json() if response.text else {"status": "stopped"}
        return None
    
    def get_pipeline_runs(self, pipeline_name: str, pipeline_type: str = "batch",
                         expected_result: str = "Should succeed with 200 OK") -> Optional[List[Dict[str, Any]]]:
        """Get pipeline run history"""
        if pipeline_type == "batch":
            endpoint = f"/v3/namespaces/{self.config.namespace}/apps/{pipeline_name}/workflows/DataPipelineWorkflow/runs"
        else:
            endpoint = f"/v3/namespaces/{self.config.namespace}/apps/{pipeline_name}/spark/DataStreamsSparkStreaming/runs"
        
        print(f"Getting {pipeline_type} pipeline runs for: {pipeline_name}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_PIPELINE_RUNS_{pipeline_name}_{pipeline_type.upper()}",
            f"Get run history for {pipeline_type} pipeline '{pipeline_name}'",
            "Pipeline Level Execution",
            expected_result=expected_result
        )
        return response.json() if response else None

    # Compute Profile Operations
    def list_compute_profiles(self) -> Optional[List[Dict[str, Any]]]:
        """List compute profiles"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/profiles"
        
        print(f"Listing compute profiles")
        response, _ = self._make_request(
            'GET', endpoint,
            f"LIST_COMPUTE_PROFILES_{self.config.namespace}",
            f"List compute profiles in namespace '{self.config.namespace}'",
            "Compute Profile Operation",
            expected_result="Should succeed with 200 OK and return profile list"
        )
        return response.json() if response else None
    
    def create_compute_profile(self, profile_name: str, profile_config: Dict[str, Any],
                             expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Create compute profile"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/profiles/{profile_name}"
        
        print(f"Creating compute profile: {profile_name}")
        response, _ = self._make_request(
            'PUT', endpoint,
            f"CREATE_COMPUTE_PROFILE_{profile_name}",
            f"Create compute profile '{profile_name}' in namespace '{self.config.namespace}'",
            "Compute Profile Operation",
            expected_result=expected_result,
            json=profile_config
        )
        if response:
            return response.json() if response.text else {"status": "created"}
        return None
    
    def get_compute_profile(self, profile_name: str, expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Get compute profile"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/profiles/{profile_name}"
        
        print(f"Getting compute profile: {profile_name}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_COMPUTE_PROFILE_{profile_name}",
            f"Get compute profile '{profile_name}' from namespace '{self.config.namespace}'",
            "Compute Profile Operation",
            expected_result=expected_result
        )
        return response.json() if response else None
    
    def update_compute_profile(self, profile_name: str, profile_config: Dict[str, Any],
                             expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Update compute profile"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/profiles/{profile_name}"
        
        print(f"Updating compute profile: {profile_name}")
        response, _ = self._make_request(
            'PUT', endpoint,
            f"UPDATE_COMPUTE_PROFILE_{profile_name}",
            f"Update compute profile '{profile_name}' in namespace '{self.config.namespace}'",
            "Compute Profile Operation",
            expected_result=expected_result,
            json=profile_config
        )
        if response:
            return response.json() if response.text else {"status": "updated"}
        return None
    
    def delete_compute_profile(self, profile_name: str, expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Delete compute profile"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/profiles/{profile_name}"
        
        print(f"Deleting compute profile: {profile_name}")
        response, _ = self._make_request(
            'DELETE', endpoint,
            f"DELETE_COMPUTE_PROFILE_{profile_name}",
            f"Delete compute profile '{profile_name}' from namespace '{self.config.namespace}'",
            "Compute Profile Operation",
            expected_result=expected_result
        )
        if response:
            return response.json() if response.text else {"status": "deleted"}
        return None

    # Security Operations
    def list_secure_keys(self) -> Optional[List[Dict[str, Any]]]:
        """List secure keys"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/securekeys"
        
        print(f"Listing secure keys")
        response, _ = self._make_request(
            'GET', endpoint,
            f"LIST_SECURE_KEYS_{self.config.namespace}",
            f"List secure keys in namespace '{self.config.namespace}'",
            "Security Operation",
            expected_result="Should succeed with 200 OK and return key list"
        )
        return response.json() if response else None
    
    def create_secure_key(self, key_name: str, key_data: Dict[str, Any],
                        expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Create secure key"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/securekeys/{key_name}"
        
        print(f"Creating secure key: {key_name}")
        response, _ = self._make_request(
            'PUT', endpoint,
            f"CREATE_SECURE_KEY_{key_name}",
            f"Create secure key '{key_name}' in namespace '{self.config.namespace}'",
            "Security Operation",
            expected_result=expected_result,
            json=key_data
        )
        if response:
            return response.json() if response.text else {"status": "created"}
        return None
    
    def get_secure_key_metadata(self, key_name: str, expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Get secure key metadata"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/securekeys/{key_name}/metadata"
        
        print(f"Getting secure key metadata: {key_name}")
        response, _ = self._make_request(
            'GET', endpoint,
            f"GET_SECURE_KEY_METADATA_{key_name}",
            f"Get metadata for secure key '{key_name}'",
            "Security Operation",
            expected_result=expected_result
        )
        return response.json() if response else None
    
    def delete_secure_key(self, key_name: str, expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Delete secure key"""
        endpoint = f"/v3/namespaces/{self.config.namespace}/securekeys/{key_name}"
        
        print(f"Deleting secure key: {key_name}")
        response, _ = self._make_request(
            'DELETE', endpoint,
            f"DELETE_SECURE_KEY_{key_name}",
            f"Delete secure key '{key_name}' from namespace '{self.config.namespace}'",
            "Security Operation",
            expected_result=expected_result
        )
        if response:
            return response.json() if response.text else {"status": "deleted"}
        return None


class PipelineTestRunner:
    """Test runner for pipeline-level operations"""
    
    def __init__(self, client: CDAPClient, skip_cleanup: bool = False):
        self.client = client
        self.skip_cleanup = skip_cleanup
        self.test_pipeline_name = f"test-pipeline-{int(time.time())}"
        self.test_profile_name = f"test-profile-{int(time.time())}"
        self.test_key_name = f"test-key-{int(time.time())}"
    
    def run_tests(self) -> List[TestResult]:
        """Run comprehensive pipeline-level tests"""
        print("\n" + "="*60)
        print("GOOGLE CLOUD DATA FUSION - PIPELINE LEVEL OPERATIONS TEST")
        print("="*60)
        print(f"Project: {self.client.config.project_id}")
        print(f"Location: {self.client.config.location}")
        print(f"Instance: {self.client.config.instance_name}")
        print(f"Namespace: {self.client.config.namespace}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        # Test 1: Pipeline CRUD operations
        self._test_pipeline_crud_operations()
        
        # Test 2: Pipeline execution operations
        self._test_pipeline_execution_operations()
        
        # Test 3: Compute profile operations
        self._test_compute_profile_operations()
        
        # Test 4: Security operations
        self._test_security_operations()
        
        # Test 5: Test with existing pipelines
        self._test_existing_pipeline_operations()
        
        return self.client.config.test_results
    
    def _test_pipeline_crud_operations(self):
        """Test pipeline CRUD operations"""
        print("=== Testing Pipeline CRUD Operations ===")
        
        # LIST all pipelines - should succeed
        try:
            pipelines = self.client.list_pipelines()
            print(f"✓ LIST_PIPELINES passed - found {len(pipelines) if pipelines else 0} pipeline(s)")
        except Exception as e:
            print(f"✗ LIST_PIPELINES failed: {e}")
        
        # LIST batch pipelines specifically - should succeed
        try:
            batch_pipelines = self.client.list_pipelines("cdap-data-pipeline")
            print(f"✓ LIST_BATCH_PIPELINES passed")
        except Exception as e:
            print(f"✗ LIST_BATCH_PIPELINES failed: {e}")
        
        # CREATE pipeline - should succeed
        pipeline_config = {
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
        
        try:
            self.client.deploy_pipeline(
                self.test_pipeline_name, 
                pipeline_config,
                expected_result="Should succeed with 200 OK for valid pipeline config"
            )
            print(f"✓ DEPLOY_PIPELINE_{self.test_pipeline_name} passed")
            
            # GET pipeline - should succeed
            try:
                pipeline = self.client.get_pipeline(
                    self.test_pipeline_name,
                    expected_result="Should succeed with 200 OK for existing pipeline"
                )
                print(f"✓ GET_PIPELINE_{self.test_pipeline_name} passed")
            except Exception as e:
                print(f"✗ GET_PIPELINE_{self.test_pipeline_name} failed: {e}")
            
            # UPDATE pipeline - should succeed
            try:
                pipeline_config["description"] = "Updated test pipeline"
                self.client.update_pipeline(
                    self.test_pipeline_name, 
                    pipeline_config,
                    expected_result="Should succeed with 200 OK for valid update"
                )
                print(f"✓ UPDATE_PIPELINE_{self.test_pipeline_name} passed")
            except Exception as e:
                print(f"✗ UPDATE_PIPELINE_{self.test_pipeline_name} failed: {e}")
            
            # DELETE pipeline - should succeed (unless skip_cleanup)
            if not self.skip_cleanup:
                try:
                    self.client.delete_pipeline(
                        self.test_pipeline_name,
                        expected_result="Should succeed with 200 OK for existing pipeline"
                    )
                    print(f"✓ DELETE_PIPELINE_{self.test_pipeline_name} passed")
                except Exception as e:
                    print(f"✗ DELETE_PIPELINE_{self.test_pipeline_name} failed: {e}")
            else:
                print(f"ℹ DELETE_PIPELINE_{self.test_pipeline_name} skipped (--skip-cleanup)")
                
        except Exception as e:
            print(f"✗ DEPLOY_PIPELINE_{self.test_pipeline_name} failed: {e}")
    
    def _test_pipeline_execution_operations(self):
        """Test pipeline execution operations"""
        print("\n=== Testing Pipeline Execution Operations ===")
        
        non_existent = "non-existent-pipeline-12345"
        
        # START batch pipeline on non-existent - should fail with 404
        try:
            self.client.start_batch_pipeline(
                non_existent,
                expected_result="Should fail with 404 Not Found"
            )
            print(f"✓ START_BATCH_PIPELINE_{non_existent} passed (failed as expected)")
        except Exception:
            print(f"✓ START_BATCH_PIPELINE_{non_existent} passed (failed as expected)")
        
        # STOP batch pipeline on non-existent - should fail with 404
        try:
            self.client.stop_batch_pipeline(
                non_existent,
                expected_result="Should fail with 404 Not Found"
            )
            print(f"✓ STOP_BATCH_PIPELINE_{non_existent} passed (failed as expected)")
        except Exception:
            print(f"✓ STOP_BATCH_PIPELINE_{non_existent} passed (failed as expected)")
        
        # GET pipeline runs on non-existent - should fail with 404
        try:
            runs = self.client.get_pipeline_runs(
                non_existent, 
                "batch",
                expected_result="Should fail with 404 Not Found"
            )
            print(f"✓ GET_PIPELINE_RUNS_{non_existent}_BATCH passed (failed as expected)")
        except Exception:
            print(f"✓ GET_PIPELINE_RUNS_{non_existent}_BATCH passed (failed as expected)")
    
    def _test_existing_pipeline_operations(self):
        """Test operations on existing pipelines"""
        print("\n=== Testing Existing Pipeline Operations ===")
        
        # Get list of existing pipelines
        try:
            pipelines = self.client.list_pipelines()
            if pipelines and len(pipelines) > 0:
                # Test with first existing pipeline
                existing_pipeline = pipelines[0]['name']
                
                # GET existing pipeline - should succeed
                try:
                    self.client.get_pipeline(
                        existing_pipeline,
                        expected_result="Should succeed with 200 OK for existing pipeline"
                    )
                    print(f"✓ GET_PIPELINE_{existing_pipeline} passed (existing pipeline)")
                except Exception as e:
                    print(f"✗ GET_PIPELINE_{existing_pipeline} failed: {e}")
                
                # GET runs for existing pipeline - should succeed
                try:
                    self.client.get_pipeline_runs(
                        existing_pipeline,
                        "batch",
                        expected_result="Should succeed with 200 OK for existing pipeline"
                    )
                    print(f"✓ GET_PIPELINE_RUNS_{existing_pipeline}_BATCH passed")
                except Exception as e:
                    print(f"ℹ GET_PIPELINE_RUNS_{existing_pipeline}_BATCH: {e}")
            else:
                print("ℹ No existing pipelines found to test")
        except Exception as e:
            print(f"ℹ Could not test existing pipelines: {e}")
    
    def _test_compute_profile_operations(self):
        """Test compute profile operations"""
        print("\n=== Testing Compute Profile Operations ===")
        
        # LIST compute profiles - should succeed
        try:
            profiles = self.client.list_compute_profiles()
            print(f"✓ LIST_COMPUTE_PROFILES passed - found {len(profiles) if profiles else 0} profile(s)")
        except Exception as e:
            print(f"✗ LIST_COMPUTE_PROFILES failed: {e}")
        
        # Test with non-existent profile first
        non_existent_profile = "non-existent-profile-12345"
        try:
            self.client.get_compute_profile(
                non_existent_profile,
                expected_result="Should fail with 404 Not Found"
            )
            print(f"✓ GET_COMPUTE_PROFILE_{non_existent_profile} passed (failed as expected)")
        except Exception:
            print(f"✓ GET_COMPUTE_PROFILE_{non_existent_profile} passed (failed as expected)")
        
        # CREATE compute profile - should succeed
        profile_config = {
            "label": "Test Compute Profile",
            "description": "Test profile for API validation",
            "provisioner": {
                "name": "gcp-dataproc",
                "properties": [
                    {"name": "projectId", "value": self.client.config.project_id},
                    {"name": "region", "value": self.client.config.location},
                    {"name": "masterInstanceType", "value": "n1-standard-2"},
                    {"name": "workerInstanceType", "value": "n1-standard-2"},
                    {"name": "numWorkers", "value": "2"}
                ]
            }
        }
        
        try:
            self.client.create_compute_profile(
                self.test_profile_name, 
                profile_config,
                expected_result="Should succeed with 200 OK for valid profile config"
            )
            print(f"✓ CREATE_COMPUTE_PROFILE_{self.test_profile_name} passed")
            
            # GET compute profile - should succeed
            try:
                profile = self.client.get_compute_profile(
                    self.test_profile_name,
                    expected_result="Should succeed with 200 OK for existing profile"
                )
                print(f"✓ GET_COMPUTE_PROFILE_{self.test_profile_name} passed")
            except Exception as e:
                print(f"✗ GET_COMPUTE_PROFILE_{self.test_profile_name} failed: {e}")
            
            # UPDATE compute profile - should succeed
            try:
                profile_config["description"] = "Updated test profile"
                self.client.update_compute_profile(
                    self.test_profile_name, 
                    profile_config,
                    expected_result="Should succeed with 200 OK for valid update"
                )
                print(f"✓ UPDATE_COMPUTE_PROFILE_{self.test_profile_name} passed")
            except Exception as e:
                print(f"✗ UPDATE_COMPUTE_PROFILE_{self.test_profile_name} failed: {e}")
            
            # DELETE compute profile - should succeed (unless skip_cleanup)
            if not self.skip_cleanup:
                try:
                    self.client.delete_compute_profile(
                        self.test_profile_name,
                        expected_result="Should succeed with 200 OK for existing profile"
                    )
                    print(f"✓ DELETE_COMPUTE_PROFILE_{self.test_profile_name} passed")
                except Exception as e:
                    print(f"✗ DELETE_COMPUTE_PROFILE_{self.test_profile_name} failed: {e}")
            else:
                print(f"ℹ DELETE_COMPUTE_PROFILE_{self.test_profile_name} skipped (--skip-cleanup)")
                
        except Exception as e:
            print(f"✗ CREATE_COMPUTE_PROFILE_{self.test_profile_name} failed: {e}")
    
    def _test_security_operations(self):
        """Test security operations"""
        print("\n=== Testing Security Operations ===")
        
        # LIST secure keys - should succeed
        try:
            keys = self.client.list_secure_keys()
            print(f"✓ LIST_SECURE_KEYS passed - found {len(keys) if keys else 0} key(s)")
        except Exception as e:
            print(f"✗ LIST_SECURE_KEYS failed: {e}")
        
        # Test with non-existent key first
        non_existent_key = "non-existent-key-12345"
        try:
            self.client.get_secure_key_metadata(
                non_existent_key,
                expected_result="Should fail with 404 Not Found"
            )
            print(f"✓ GET_SECURE_KEY_METADATA_{non_existent_key} passed (failed as expected)")
        except Exception:
            print(f"✓ GET_SECURE_KEY_METADATA_{non_existent_key} passed (failed as expected)")
        
        # CREATE secure key - should succeed
        key_data = {
            "description": "Test secure key for API validation",
            "data": "test-secret-value",
            "properties": {
                "test-property": "test-value"
            }
        }
        
        try:
            self.client.create_secure_key(
                self.test_key_name, 
                key_data,
                expected_result="Should succeed with 200 OK for valid key data"
            )
            print(f"✓ CREATE_SECURE_KEY_{self.test_key_name} passed")
            
            # GET secure key metadata - should succeed
            try:
                metadata = self.client.get_secure_key_metadata(
                    self.test_key_name,
                    expected_result="Should succeed with 200 OK for existing key"
                )
                print(f"✓ GET_SECURE_KEY_METADATA_{self.test_key_name} passed")
            except Exception as e:
                print(f"✗ GET_SECURE_KEY_METADATA_{self.test_key_name} failed: {e}")
            
            # DELETE secure key - should succeed (unless skip_cleanup)
            if not self.skip_cleanup:
                try:
                    self.client.delete_secure_key(
                        self.test_key_name,
                        expected_result="Should succeed with 200 OK for existing key"
                    )
                    print(f"✓ DELETE_SECURE_KEY_{self.test_key_name} passed")
                except Exception as e:
                    print(f"✗ DELETE_SECURE_KEY_{self.test_key_name} failed: {e}")
            else:
                print(f"ℹ DELETE_SECURE_KEY_{self.test_key_name} skipped (--skip-cleanup)")
                
        except Exception as e:
            print(f"✗ CREATE_SECURE_KEY_{self.test_key_name} failed: {e}")


class ReportGenerator:
    """Generate reports and display results"""
    
    @staticmethod
    def generate_csv_report(test_results: List[TestResult], filename: str = None) -> str:
        """Generate CSV report"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_fusion_pipeline_operations_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'test_case', 'api_endpoint', 'method', 'description', 'type', 'status',
                'response_code', 'response_message', 'execution_time', 'timestamp',
                'expected_result', 'actual_result', 'test_passed', 'error_details'
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
                    'expected_result': result.expected_result,
                    'actual_result': result.actual_result,
                    'test_passed': result.test_passed,
                    'error_details': result.error_details[:200] + '...' if len(result.error_details) > 200 else result.error_details
                })
        
        return filename
    
    @staticmethod
    def display_results_table(test_results: List[TestResult]):
        """Display results in tabulated format"""
        if not test_results:
            print("No test results to display.")
            return
        
        # Remove any duplicates based on test_case + method + endpoint
        unique_results = []
        seen = set()
        for result in test_results:
            key = f"{result.test_case}_{result.method}_{result.api_endpoint}"
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        # Prepare data for tabulation
        table_data = []
        for result in unique_results:
            table_data.append([
                result.test_case[:25] + '...' if len(result.test_case) > 25 else result.test_case,
                result.method,
                result.type[:20] + '...' if len(result.type) > 20 else result.type,
                result.status,
                result.response_code,
                f"{result.execution_time:.3f}s",
                result.expected_result[:30] + '...' if len(result.expected_result) > 30 else result.expected_result,
                result.actual_result[:30] + '...' if len(result.actual_result) > 30 else result.actual_result
            ])
        
        headers = ['Test Case', 'Method', 'Type', 'Status', 'Code', 'Time', 'Expected', 'Actual']
        
        print("\n" + "="*150)
        print("PIPELINE LEVEL OPERATIONS - TEST RESULTS")
        print("="*150)
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Summary statistics
        total_tests = len(unique_results)
        passed_tests = len([r for r in unique_results if r.status == "PASS"])
        failed_tests = total_tests - passed_tests
        avg_time = sum(r.execution_time for r in unique_results) / total_tests if total_tests > 0 else 0
        
        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✓")
        print(f"   Failed: {failed_tests} ✗")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"   Average Execution Time: {avg_time:.3f}s")
        
        # Operation type breakdown
        op_types = {}
        for result in unique_results:
            op_type = result.type
            op_types[op_type] = op_types.get(op_type, 0) + 1
        
        print(f"\n📋 OPERATION TYPE BREAKDOWN:")
        for op_type, count in sorted(op_types.items()):
            print(f"   {op_type}: {count}")
        
        # Operation breakdown
        operations = {}
        for result in unique_results:
            op = result.test_case.split('_')[0]
            operations[op] = operations.get(op, 0) + 1
        
        print(f"\n📋 OPERATION BREAKDOWN:")
        for op, count in sorted(operations.items()):
            print(f"   {op}: {count}")
        
        # Test validation summary
        print(f"\n✅ TEST VALIDATION SUMMARY:")
        expected_failures = [r for r in unique_results if "should fail" in r.expected_result.lower() and r.status == "PASS"]
        expected_successes = [r for r in unique_results if "should succeed" in r.expected_result.lower() and r.status == "PASS"]
        unexpected_failures = [r for r in unique_results if "should succeed" in r.expected_result.lower() and r.status == "FAIL"]
        
        print(f"   Expected Failures (passed): {len(expected_failures)}")
        print(f"   Expected Successes (passed): {len(expected_successes)}")
        print(f"   Unexpected Failures: {len(unexpected_failures)}")
        
        if unexpected_failures:
            print(f"\n❌ UNEXPECTED FAILURES:")
            for result in unexpected_failures:
                print(f"   - {result.test_case}: {result.actual_result}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Test Google Cloud Data Fusion Pipeline Level Operations (Data Plane)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all pipeline operations
  python %(prog)s --project my-project --location us-central1 --instance my-instance
  
  # Test in specific namespace
  python %(prog)s --project my-project --location us-central1 --instance my-instance --namespace production
  
  # Skip cleanup (keep test resources)
  python %(prog)s --project my-project --location us-central1 --instance my-instance --skip-cleanup
  
  # Generate custom report filename
  python %(prog)s --project my-project --location us-central1 --instance my-instance --output my-report.csv
        """
    )
    
    parser.add_argument('--project', required=True, help='GCP Project ID')
    parser.add_argument('--location', required=True, help='GCP Location/Region (e.g., us-central1)')
    parser.add_argument('--instance', required=True, help='Data Fusion instance name')
    parser.add_argument('--namespace', default='default', help='CDAP namespace (default: default)')
    parser.add_argument('--skip-cleanup', action='store_true', 
                       help='Skip cleanup of test resources')
    parser.add_argument('--output', help='Output CSV filename (optional)')
    
    args = parser.parse_args()
    
    try:
        # Get auth token
        auth_token = os.getenv('GOOGLE_AUTH_TOKEN')
        if not auth_token:
            print("ERROR: GOOGLE_AUTH_TOKEN environment variable not set")
            print("Run: export GOOGLE_AUTH_TOKEN=$(gcloud auth print-access-token)")
            return
        
        # Initialize configuration
        config = Config(
            project_id=args.project,
            location=args.location,
            instance_name=args.instance,
            namespace=args.namespace,
            auth_token=auth_token
        )
        
        # Get instance API endpoint
        print(f"Getting API endpoint for instance: {args.instance}...")
        instance_client = DataFusionInstanceClient(config)
        api_endpoint = instance_client.get_instance_api_endpoint()
        print(f"✓ API Endpoint: {api_endpoint}")
        
        # Create CDAP client and run tests
        cdap_client = CDAPClient(api_endpoint, config)
        runner = PipelineTestRunner(cdap_client, args.skip_cleanup)
        test_results = runner.run_tests()
        
        # Generate reports
        csv_filename = ReportGenerator.generate_csv_report(test_results, args.output)
        print(f"\n📄 CSV report generated: {csv_filename}")
        
        # Display results
        ReportGenerator.display_results_table(test_results)
        
        print(f"\n✅ Pipeline-level testing completed successfully!")
        
        if args.skip_cleanup:
            print(f"\n⚠️  Test resources were not cleaned up:")
            print(f"   - Pipeline: {runner.test_pipeline_name}")
            print(f"   - Compute Profile: {runner.test_profile_name}")
            print(f"   - Secure Key: {runner.test_key_name}")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
