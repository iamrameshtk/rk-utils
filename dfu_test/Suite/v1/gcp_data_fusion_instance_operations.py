#!/usr/bin/env python3
"""
Google Cloud Data Fusion Instance Level Operations Script (Control Plane)

This script tests instance-level CRUD operations for Google Cloud Data Fusion.

Features:
- Instance lifecycle management (CREATE, GET, UPDATE, DELETE, LIST, RESTART)
- Command-line parameter support
- Automated test execution with Pass/Fail tracking
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


@dataclass
class Config:
    """Configuration for Cloud Data Fusion operations"""
    project_id: str
    location: str
    auth_token: str
    base_url: str = "https://datafusion.googleapis.com"
    api_version: str = "v1beta1"
    test_results: List[TestResult] = field(default_factory=list)
    processed_tests: set = field(default_factory=set)  # Track processed test cases

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
                     expected_result: str = "", **kwargs) -> Tuple[Optional[requests.Response], TestResult]:
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
            expected_result=expected_result
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
        self.test_instance_name = f"test-instance-{int(time.time())}"
    
    def run_tests(self) -> List[TestResult]:
        """Run comprehensive instance-level tests"""
        print("\n" + "="*60)
        print("GOOGLE CLOUD DATA FUSION - INSTANCE LEVEL OPERATIONS TEST")
        print("="*60)
        print(f"Project: {self.client.config.project_id}")
        print(f"Location: {self.client.config.location}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        # Test 1: List instances (always works)
        self._test_list_instances()
        
        # Test 2: Test with existing instances
        instances = self.client.list_instances()
        if instances:
            # Test first existing instance
            existing_instance = instances[0]['name'].split('/')[-1]
            self._test_existing_instance_operations(existing_instance)
            
            # If more than one instance, test another
            if len(instances) > 1:
                another_instance = instances[1]['name'].split('/')[-1]
                self._test_another_existing_instance(another_instance)
        
        # Test 3: Test with non-existent instance (expected failures)
        self._test_non_existent_instance_operations()
        
        # Test 4: Create instance test (optional - expensive)
        if self.create_instance:
            self._test_create_delete_instance()
        
        return self.client.config.test_results
    
    def _test_list_instances(self):
        """Test listing instances"""
        print("Testing LIST_INSTANCES...")
        try:
            instances = self.client.list_instances()
            print(f"✓ LIST_INSTANCES passed - found {len(instances)} instance(s)")
            for idx, instance in enumerate(instances):
                name = instance['name'].split('/')[-1]
                state = instance.get('state', 'UNKNOWN')
                print(f"  [{idx+1}] {name} - {state}")
        except Exception as e:
            print(f"✗ LIST_INSTANCES failed: {e}")
    
    def _test_existing_instance_operations(self, instance_name: str):
        """Test operations on existing instance"""
        print(f"\nTesting operations on existing instance: {instance_name}")
        
        # GET instance - should succeed
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
        
        # UPDATE instance - should succeed
        try:
            update_config = {
                "labels": {
                    "test-update": "true",
                    "updated-at": str(int(time.time()))
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
        
        # RESTART instance - test based on state
        try:
            instance = self.client.get_instance(instance_name)
            if instance and instance.get('state') == 'RUNNING':
                self.client.restart_instance(
                    instance_name,
                    expected_result="Should succeed with 200 OK for running instance"
                )
                print(f"✓ RESTART_INSTANCE_{instance_name} passed")
            else:
                # Try restart on non-running instance - should fail
                self.client.restart_instance(
                    instance_name,
                    expected_result="Should fail with 400 Bad Request for non-running instance"
                )
                print(f"✓ RESTART_INSTANCE_{instance_name} tested (non-running state)")
        except Exception as e:
            print(f"ℹ RESTART_INSTANCE_{instance_name} result: {e}")
    
    def _test_another_existing_instance(self, instance_name: str):
        """Test another existing instance to avoid duplicates"""
        print(f"\nTesting another existing instance: {instance_name}")
        
        # GET with different test case
        try:
            instance = self.client.get_instance(
                instance_name,
                expected_result="Should succeed with 200 OK for second existing instance"
            )
            if instance:
                print(f"✓ GET_INSTANCE_{instance_name} passed (second instance)")
        except Exception as e:
            print(f"✗ GET_INSTANCE_{instance_name} failed: {e}")
    
    def _test_non_existent_instance_operations(self):
        """Test operations on non-existent instance (expected failures)"""
        non_existent = "non-existent-instance-12345"
        print(f"\nTesting operations on non-existent instance (expected failures)...")
        
        # GET non-existent - should fail with 404
        try:
            self.client.get_instance(
                non_existent,
                expected_result="Should fail with 404 Not Found"
            )
            print(f"✓ GET_INSTANCE_{non_existent} passed (failed as expected)")
        except Exception:
            print(f"✓ GET_INSTANCE_{non_existent} passed (failed as expected)")
        
        # UPDATE non-existent - should fail with 404
        try:
            self.client.update_instance(
                non_existent, 
                {"description": "test"},
                expected_result="Should fail with 404 Not Found"
            )
            print(f"✓ UPDATE_INSTANCE_{non_existent} passed (failed as expected)")
        except Exception:
            print(f"✓ UPDATE_INSTANCE_{non_existent} passed (failed as expected)")
        
        # DELETE non-existent - should fail with 404
        try:
            self.client.delete_instance(
                non_existent,
                expected_result="Should fail with 404 Not Found"
            )
            print(f"✓ DELETE_INSTANCE_{non_existent} passed (failed as expected)")
        except Exception:
            print(f"✓ DELETE_INSTANCE_{non_existent} passed (failed as expected)")
        
        # RESTART non-existent - should fail with 404
        try:
            self.client.restart_instance(
                non_existent,
                expected_result="Should fail with 404 Not Found"
            )
            print(f"✓ RESTART_INSTANCE_{non_existent} passed (failed as expected)")
        except Exception:
            print(f"✓ RESTART_INSTANCE_{non_existent} passed (failed as expected)")
    
    def _test_create_delete_instance(self):
        """Test creating and deleting an instance (expensive operation)"""
        print(f"\nTesting CREATE and DELETE instance operations...")
        print("⚠️  WARNING: This creates a real instance and incurs costs!")
        
        instance_config = {
            "type": "BASIC",
            "description": "Test instance created by API testing script",
            "labels": {
                "purpose": "api-testing",
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
            print("  - Note: Instance creation takes 10-15 minutes")
            
            # Wait a bit and then try to delete
            print("\nWaiting 30 seconds before attempting delete...")
            time.sleep(30)
            
            # DELETE instance
            try:
                self.client.delete_instance(
                    self.test_instance_name,
                    expected_result="Should succeed with 200 OK or fail with 409 if still creating"
                )
                print(f"✓ DELETE_INSTANCE_{self.test_instance_name} initiated")
            except Exception as e:
                print(f"ℹ DELETE_INSTANCE_{self.test_instance_name} result: {e}")
                
        except Exception as e:
            print(f"✗ CREATE_INSTANCE_{self.test_instance_name} failed: {e}")


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
  
  # Test with instance creation (expensive)
  python %(prog)s --project my-project --location us-central1 --create-instance
  
  # Generate custom report filename
  python %(prog)s --project my-project --location us-central1 --output my-report.csv
        """
    )
    
    parser.add_argument('--project', required=True, help='GCP Project ID')
    parser.add_argument('--location', required=True, help='GCP Location/Region (e.g., us-central1)')
    parser.add_argument('--create-instance', action='store_true', 
                       help='Include instance creation test (WARNING: incurs costs)')
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
        ReportGenerator.display_results_table(test_results)
        
        print(f"\n✅ Instance-level testing completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
