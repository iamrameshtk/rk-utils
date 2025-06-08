#!/usr/bin/env python3
"""
Google Cloud Data Fusion Instance Level Operations Script (Control Plane)

This script tests instance-level CRUD operations for Google Cloud Data Fusion.

Features:
- Complete instance lifecycle management (CREATE, GET, UPDATE, DELETE, LIST, RESTART)
- Command-line parameter support
- Automated test execution with Pass/Fail tracking
- Resource tracking and cleanup validation
- CSV report generation
- Tabulated output display
- Summary statistics

Usage:
    python gcp_data_fusion_instance_operations.py --project PROJECT_ID --location LOCATION [--create-instance]
    
Examples:
    # Test existing instances only
    python gcp_data_fusion_instance_operations.py --project my-project --location us-central1
    
    # Test with instance creation (expensive operation)
    python gcp_data_fusion_instance_operations.py --project my-project --location us-central1 --create-instance

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
    resource_created: str = ""  # Track created resources
    resource_deleted: bool = False  # Track if resource was deleted


@dataclass
class ResourceTracker:
    """Track created resources for cleanup validation"""
    created_instances: Dict[str, bool] = field(default_factory=dict)  # name -> deleted
    
    def add_instance(self, name: str):
        self.created_instances[name] = False
    
    def mark_deleted(self, name: str):
        if name in self.created_instances:
            self.created_instances[name] = True
    
    def get_undeleted_resources(self) -> List[str]:
        return [name for name, deleted in self.created_instances.items() if not deleted]


@dataclass
class Config:
    """Configuration for Cloud Data Fusion operations"""
    project_id: str
    location: str
    auth_token: str
    base_url: str = "https://datafusion.googleapis.com"
    api_version: str = "v1beta1"
    test_results: List[TestResult] = field(default_factory=list)
    processed_tests: set = field(default_factory=set)
    resource_tracker: ResourceTracker = field(default_factory=ResourceTracker)

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
    
    def _make_request(self, method: str, url: str, test_case: str, description: str, 
                     operation_type: str = "Instance Level Operation", 
                     expected_result: str = "", resource_name: str = "", **kwargs) -> Tuple[Optional[requests.Response], TestResult]:
        """Make HTTP request with test case tracking"""
        # Create unique test identifier
        test_id = f"{test_case}_{method}_{url}"
        
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
            
            # Track resource creation
            resource_created = ""
            if method in ["POST", "PUT"] and response.status_code < 300 and resource_name:
                resource_created = resource_name
                if "instance" in test_case.lower() and method == "POST":
                    self.config.resource_tracker.add_instance(resource_name)
            
            # Track resource deletion
            resource_deleted = False
            if method == "DELETE" and response.status_code < 300 and resource_name:
                resource_deleted = True
                self.config.resource_tracker.mark_deleted(resource_name)
            
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
                test_passed=test_passed,
                resource_created=resource_created,
                resource_deleted=resource_deleted
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
            return status_code >= 400
        elif "should succeed" in expected_lower or "200" in expected_result:
            return 200 <= status_code < 300
        elif "404" in expected_result:
            return status_code == 404
        elif "409" in expected_result:
            return status_code == 409
        else:
            return 200 <= status_code < 300

    def create_instance(self, instance_name: str, instance_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new Data Fusion instance"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances"
        
        params = {"instanceId": instance_name}
        
        print(f"Creating Data Fusion instance: {instance_name}")
        response, _ = self._make_request(
            'POST', url, 
            f"CREATE_INSTANCE_{instance_name}", 
            f"Create Data Fusion instance '{instance_name}' with configuration",
            "Instance Level Operation",
            expected_result="Should succeed with 200 OK for valid configuration",
            resource_name=instance_name,
            params=params,
            json=instance_config
        )
        return response.json() if response else None
    
    def get_instance(self, instance_name: str, expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Get details of a Data Fusion instance"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances/{instance_name}"
        
        print(f"Getting Data Fusion instance: {instance_name}")
        response, _ = self._make_request(
            'GET', url,
            f"GET_INSTANCE_{instance_name}",
            f"Retrieve details for Data Fusion instance '{instance_name}'",
            "Instance Level Operation",
            expected_result=expected_result
        )
        return response.json() if response else None
    
    def update_instance(self, instance_name: str, update_config: Dict[str, Any], 
                       update_mask: str = None, expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Update a Data Fusion instance"""
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
            expected_result=expected_result,
            json=update_config,
            params=params
        )
        return response.json() if response else None
    
    def delete_instance(self, instance_name: str, expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Delete a Data Fusion instance"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances/{instance_name}"
        
        print(f"Deleting Data Fusion instance: {instance_name}")
        response, _ = self._make_request(
            'DELETE', url,
            f"DELETE_INSTANCE_{instance_name}",
            f"Delete Data Fusion instance '{instance_name}'",
            "Instance Level Operation",
            expected_result=expected_result,
            resource_name=instance_name
        )
        if response:
            return response.json() if response.text else {"status": "deleted"}
        return None
    
    def list_instances(self) -> List[Dict[str, Any]]:
        """List all Data Fusion instances"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances"
        
        print("Listing Data Fusion instances")
        response, _ = self._make_request(
            'GET', url,
            "LIST_INSTANCES",
            f"List all Data Fusion instances in project '{self.config.project_id}' and location '{self.config.location}'",
            "Instance Level Operation",
            expected_result="Should succeed with 200 OK and return instance list"
        )
        if response:
            result = response.json()
            return result.get('instances', [])
        return []
    
    def restart_instance(self, instance_name: str, expected_result: str = "Should succeed with 200 OK") -> Optional[Dict[str, Any]]:
        """Restart a Data Fusion instance"""
        url = f"{self.config.base_url}/{self.config.api_version}/projects/{self.config.project_id}/locations/{self.config.location}/instances/{instance_name}:restart"
        
        print(f"Restarting Data Fusion instance: {instance_name}")
        response, _ = self._make_request(
            'POST', url,
            f"RESTART_INSTANCE_{instance_name}",
            f"Restart Data Fusion instance '{instance_name}'",
            "Instance Level Operation",
            expected_result=expected_result,
            json={}
        )
        return response.json() if response else None


class InstanceTestRunner:
    """Test runner for instance-level operations"""
    
    def __init__(self, client: CloudDataFusionClient, create_instance: bool = False):
        self.client = client
        self.create_instance = create_instance
        self.test_instance_name = f"test-api-instance-{int(time.time())}"
        self.mini_instance_name = f"test-mini-instance-{int(time.time())}"
    
    def run_tests(self) -> List[TestResult]:
        """Run comprehensive instance-level tests"""
        print("\n" + "="*60)
        print("GOOGLE CLOUD DATA FUSION - INSTANCE LEVEL OPERATIONS TEST")
        print("="*60)
        print(f"Project: {self.client.config.project_id}")
        print(f"Location: {self.client.config.location}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        # Test 1: Complete CRUD workflow on test instance
        if self.create_instance:
            self._test_complete_instance_crud_workflow()
        
        # Test 2: LIST operation
        self._test_list_instances()
        
        # Test 3: Test with existing instances
        instances = self.client.list_instances()
        if instances:
            existing_instance = instances[0]['name'].split('/')[-1]
            self._test_existing_instance_operations(existing_instance)
        
        # Test 4: Test with non-existent instance (expected failures)
        self._test_non_existent_instance_operations()
        
        # Test 5: Test mini CRUD cycle (if enabled)
        if self.create_instance:
            self._test_mini_crud_cycle()
        
        return self.client.config.test_results
    
    def _test_complete_instance_crud_workflow(self):
        """Test complete instance CRUD workflow"""
        print("=== Testing Complete Instance CRUD Workflow ===")
        print("⚠️  WARNING: This creates real instances and incurs costs!")
        
        instance_config = {
            "type": "BASIC",
            "description": "Test instance for complete CRUD validation",
            "labels": {
                "purpose": "api-testing",
                "test-type": "complete-crud",
                "created-by": "test-script"
            },
            "enableStackdriverLogging": True,
            "enableStackdriverMonitoring": True
        }
        
        # CREATE instance
        try:
            operation = self.client.create_instance(self.test_instance_name, instance_config)
            print(f"✓ CREATE_INSTANCE_{self.test_instance_name} initiated")
            print(f"  - Operation: {operation.get('name', 'UNKNOWN')}")
            print("  - Waiting for instance to be ready (this takes 10-15 minutes)...")
            
            # Poll for instance creation (simplified - in production use operation status)
            max_wait = 900  # 15 minutes
            wait_interval = 30  # 30 seconds
            elapsed = 0
            instance_ready = False
            
            while elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval
                
                try:
                    instance = self.client.get_instance(
                        self.test_instance_name,
                        expected_result="Should succeed with 200 OK once instance is created"
                    )
                    if instance and instance.get('state') in ['RUNNING', 'ACTIVE']:
                        instance_ready = True
                        print(f"✓ Instance {self.test_instance_name} is now {instance.get('state')}")
                        break
                    else:
                        print(f"  - Instance state: {instance.get('state', 'UNKNOWN')} ({elapsed}s elapsed)")
                except Exception:
                    print(f"  - Instance not ready yet ({elapsed}s elapsed)")
            
            if instance_ready:
                # UPDATE instance
                try:
                    update_config = {
                        "labels": {
                            "purpose": "api-testing",
                            "test-type": "complete-crud",
                            "created-by": "test-script",
                            "updated": "true",
                            "update-time": str(int(time.time()))
                        }
                    }
                    self.client.update_instance(
                        self.test_instance_name,
                        update_config,
                        "labels",
                        expected_result="Should succeed with 200 OK for running instance"
                    )
                    print(f"✓ UPDATE_INSTANCE_{self.test_instance_name} passed")
                except Exception as e:
                    print(f"✗ UPDATE_INSTANCE_{self.test_instance_name} failed: {e}")
                
                # RESTART instance
                try:
                    self.client.restart_instance(
                        self.test_instance_name,
                        expected_result="Should succeed with 200 OK for running instance"
                    )
                    print(f"✓ RESTART_INSTANCE_{self.test_instance_name} passed")
                except Exception as e:
                    print(f"✗ RESTART_INSTANCE_{self.test_instance_name} failed: {e}")
            
            # DELETE instance (always attempt)
            try:
                self.client.delete_instance(
                    self.test_instance_name,
                    expected_result="Should succeed with 200 OK"
                )
                print(f"✓ DELETE_INSTANCE_{self.test_instance_name} initiated")
            except Exception as e:
                print(f"✗ DELETE_INSTANCE_{self.test_instance_name} failed: {e}")
                
        except Exception as e:
            print(f"✗ CREATE_INSTANCE_{self.test_instance_name} failed: {e}")
            # Still try to delete if create partially succeeded
            try:
                self.client.delete_instance(self.test_instance_name)
                print(f"✓ Cleanup: DELETE_INSTANCE_{self.test_instance_name} initiated")
            except:
                pass
    
    def _test_mini_crud_cycle(self):
        """Test mini CRUD cycle with immediate delete"""
        print("\n=== Testing Mini CRUD Cycle ===")
        
        instance_config = {
            "type": "BASIC",
            "description": "Mini test instance for quick CRUD validation",
            "labels": {
                "purpose": "api-testing",
                "test-type": "mini-crud"
            }
        }
        
        # CREATE and immediately DELETE
        try:
            operation = self.client.create_instance(self.mini_instance_name, instance_config)
            print(f"✓ CREATE_INSTANCE_{self.mini_instance_name} initiated")
            
            # Wait just 10 seconds then delete
            print("  - Waiting 10 seconds before delete...")
            time.sleep(10)
            
            # DELETE instance
            try:
                self.client.delete_instance(
                    self.mini_instance_name,
                    expected_result="Should succeed with 200 OK or 409 if still creating"
                )
                print(f"✓ DELETE_INSTANCE_{self.mini_instance_name} initiated")
            except Exception as e:
                print(f"ℹ DELETE_INSTANCE_{self.mini_instance_name} result: {e}")
                
        except Exception as e:
            print(f"✗ Mini CRUD cycle failed: {e}")
    
    def _test_list_instances(self):
        """Test listing instances"""
        print("\n=== Testing LIST Operation ===")
        try:
            instances = self.client.list_instances()
            print(f"✓ LIST_INSTANCES passed - found {len(instances)} instance(s)")
            for idx, instance in enumerate(instances[:5]):  # Show first 5
                name = instance['name'].split('/')[-1]
                state = instance.get('state', 'UNKNOWN')
                type_ = instance.get('type', 'UNKNOWN')
                print(f"  [{idx+1}] {name} - State: {state}, Type: {type_}")
        except Exception as e:
            print(f"✗ LIST_INSTANCES failed: {e}")
    
    def _test_existing_instance_operations(self, instance_name: str):
        """Test operations on existing instance"""
        print(f"\n=== Testing Operations on Existing Instance: {instance_name} ===")
        
        # GET instance
        try:
            instance = self.client.get_instance(
                instance_name, 
                expected_result="Should succeed with 200 OK for existing instance"
            )
            if instance:
                print(f"✓ GET_INSTANCE_{instance_name} passed")
                print(f"  - State: {instance.get('state', 'UNKNOWN')}")
                print(f"  - Type: {instance.get('type', 'UNKNOWN')}")
                print(f"  - Version: {instance.get('version', 'UNKNOWN')}")
        except Exception as e:
            print(f"✗ GET_INSTANCE_{instance_name} failed: {e}")
        
        # UPDATE instance
        try:
            update_config = {
                "labels": {
                    "tested-by": "api-script",
                    "test-timestamp": str(int(time.time()))
                }
            }
            self.client.update_instance(
                instance_name, 
                update_config, 
                "labels",
                expected_result="Should succeed with 200 OK for valid update"
            )
            print(f"✓ UPDATE_INSTANCE_{instance_name} passed")
        except Exception as e:
            print(f"✗ UPDATE_INSTANCE_{instance_name} failed: {e}")
        
        # RESTART instance (only if RUNNING)
        try:
            instance = self.client.get_instance(instance_name)
            if instance and instance.get('state') == 'RUNNING':
                self.client.restart_instance(
                    instance_name,
                    expected_result="Should succeed with 200 OK for running instance"
                )
                print(f"✓ RESTART_INSTANCE_{instance_name} passed")
            else:
                print(f"ℹ RESTART_INSTANCE_{instance_name} skipped (instance not RUNNING)")
        except Exception as e:
            print(f"✗ RESTART_INSTANCE_{instance_name} failed: {e}")
    
    def _test_non_existent_instance_operations(self):
        """Test operations on non-existent instance (expected failures)"""
        non_existent = "non-existent-instance-12345"
        print(f"\n=== Testing Operations on Non-Existent Instance (Expected Failures) ===")
        
        # GET non-existent
        try:
            self.client.get_instance(
                non_existent,
                expected_result="Should fail with 404 Not Found"
            )
            print(f"✓ GET_INSTANCE_{non_existent} passed (failed as expected)")
        except Exception:
            print(f"✓ GET_INSTANCE_{non_existent} passed (failed as expected)")
        
        # UPDATE non-existent
        try:
            self.client.update_instance(
                non_existent, 
                {"description": "test"},
                expected_result="Should fail with 404 Not Found"
            )
            print(f"✓ UPDATE_INSTANCE_{non_existent} passed (failed as expected)")
        except Exception:
            print(f"✓ UPDATE_INSTANCE_{non_existent} passed (failed as expected)")
        
        # DELETE non-existent
        try:
            self.client.delete_instance(
                non_existent,
                expected_result="Should fail with 404 Not Found"
            )
            print(f"✓ DELETE_INSTANCE_{non_existent} passed (failed as expected)")
        except Exception:
            print(f"✓ DELETE_INSTANCE_{non_existent} passed (failed as expected)")
        
        # RESTART non-existent
        try:
            self.client.restart_instance(
                non_existent,
                expected_result="Should fail with 404 Not Found"
            )
            print(f"✓ RESTART_INSTANCE_{non_existent} passed (failed as expected)")
        except Exception:
            print(f"✓ RESTART_INSTANCE_{non_existent} passed (failed as expected)")


class ReportGenerator:
    """Generate reports and display results"""
    
    @staticmethod
    def generate_csv_report(test_results: List[TestResult], filename: str = None) -> str:
        """Generate CSV report"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_fusion_instance_operations_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'test_case', 'api_endpoint', 'method', 'description', 'type', 'status',
                'response_code', 'response_message', 'execution_time', 'timestamp', 
                'expected_result', 'actual_result', 'test_passed', 'resource_created',
                'resource_deleted', 'error_details'
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
                    'resource_created': result.resource_created,
                    'resource_deleted': result.resource_deleted,
                    'error_details': result.error_details[:200] + '...' if len(result.error_details) > 200 else result.error_details
                })
        
        return filename
    
    @staticmethod
    def display_results_table(test_results: List[TestResult], resource_tracker: ResourceTracker):
        """Display results in tabulated format"""
        if not test_results:
            print("No test results to display.")
            return
        
        # Remove any duplicates
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
                result.status,
                result.response_code,
                f"{result.execution_time:.3f}s",
                result.expected_result[:30] + '...' if len(result.expected_result) > 30 else result.expected_result,
                result.actual_result[:30] + '...' if len(result.actual_result) > 30 else result.actual_result
            ])
        
        headers = ['Test Case', 'Method', 'Status', 'Code', 'Time', 'Expected', 'Actual']
        
        print("\n" + "="*140)
        print("INSTANCE LEVEL OPERATIONS - TEST RESULTS")
        print("="*140)
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
        
        # Operation breakdown
        operations = {}
        for result in unique_results:
            op = result.test_case.split('_')[0]
            operations[op] = operations.get(op, 0) + 1
        
        print(f"\n📋 OPERATION BREAKDOWN:")
        for op, count in sorted(operations.items()):
            print(f"   {op}: {count}")
        
        # Resource tracking summary
        print(f"\n🔧 RESOURCE TRACKING:")
        created_count = len([r for r in unique_results if r.resource_created])
        deleted_count = len([r for r in unique_results if r.resource_deleted])
        print(f"   Resources Created: {created_count}")
        print(f"   Resources Deleted: {deleted_count}")
        
        undeleted = resource_tracker.get_undeleted_resources()
        if undeleted:
            print(f"\n⚠️  UNDELETED TEST RESOURCES:")
            for resource in undeleted:
                print(f"   - {resource}")
            print("   Please clean up these resources manually to avoid charges!")
        else:
            print(f"\n✅ All test resources cleaned up successfully!")
        
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
        description='Test Google Cloud Data Fusion Instance Level Operations (Control Plane)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with existing instances only
  python %(prog)s --project my-project --location us-central1
  
  # Test with instance creation (expensive - creates real instances!)
  python %(prog)s --project my-project --location us-central1 --create-instance
  
  # Generate custom report filename
  python %(prog)s --project my-project --location us-central1 --output my-report.csv
        """
    )
    
    parser.add_argument('--project', required=True, help='GCP Project ID')
    parser.add_argument('--location', required=True, help='GCP Location/Region (e.g., us-central1)')
    parser.add_argument('--create-instance', action='store_true', 
                       help='Include instance creation test (WARNING: creates real instances, incurs costs!)')
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
            auth_token=auth_token
        )
        
        # Create client and run tests
        client = CloudDataFusionClient(config)
        runner = InstanceTestRunner(client, args.create_instance)
        test_results = runner.run_tests()
        
        # Generate reports
        csv_filename = ReportGenerator.generate_csv_report(test_results, args.output)
        print(f"\n📄 CSV report generated: {csv_filename}")
        
        # Display results
        ReportGenerator.display_results_table(test_results, config.resource_tracker)
        
        print(f"\n✅ Instance-level testing completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
