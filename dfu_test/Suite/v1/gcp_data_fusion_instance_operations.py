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
    
    def _make_request(self, method: str, url: str, test_case: str, description: str, 
                     operation_type: str = "Instance Level Operation", **kwargs) -> Tuple[Optional[requests.Response], TestResult]:
        """Make HTTP request with test case tracking"""
        existing_test = next((r for r in self.config.test_results if r.test_case == test_case), None)
        if existing_test:
            print(f"Skipping duplicate test case: {test_case}")
            return None, existing_test
        
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            response = self.session.request(method, url, **kwargs)
            execution_time = time.time() - start_time
            
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
            raise

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
            params=params,
            json=instance_config
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
            json=update_config,
            params=params
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
        """List all Data Fusion instances"""
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
            existing_instance = instances[0]['name'].split('/')[-1]
            self._test_existing_instance_operations(existing_instance)
        
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
        
        # GET instance
        try:
            instance = self.client.get_instance(instance_name)
            print(f"✓ GET_INSTANCE_{instance_name} passed")
            print(f"  - State: {instance.get('state', 'UNKNOWN')}")
            print(f"  - Type: {instance.get('type', 'UNKNOWN')}")
            print(f"  - Version: {instance.get('version', 'UNKNOWN')}")
        except Exception as e:
            print(f"✗ GET_INSTANCE_{instance_name} failed: {e}")
        
        # UPDATE instance (minimal update)
        try:
            update_config = {
                "labels": {
                    "updated": "true",
                    "test-timestamp": str(int(time.time()))
                }
            }
            self.client.update_instance(instance_name, update_config, "labels")
            print(f"✓ UPDATE_INSTANCE_{instance_name} passed")
        except Exception as e:
            print(f"✗ UPDATE_INSTANCE_{instance_name} failed: {e}")
        
        # RESTART instance (only if instance is RUNNING)
        try:
            instance = self.client.get_instance(instance_name)
            if instance and instance.get('state') == 'RUNNING':
                self.client.restart_instance(instance_name)
                print(f"✓ RESTART_INSTANCE_{instance_name} passed")
            else:
                print(f"ℹ RESTART_INSTANCE_{instance_name} skipped (instance not RUNNING)")
        except Exception as e:
            print(f"✗ RESTART_INSTANCE_{instance_name} failed: {e}")
    
    def _test_non_existent_instance_operations(self):
        """Test operations on non-existent instance (expected failures)"""
        non_existent = "non-existent-instance-12345"
        print(f"\nTesting operations on non-existent instance (expected failures)...")
        
        # GET non-existent
        try:
            self.client.get_instance(non_existent)
            print(f"✗ GET_INSTANCE_{non_existent} should have failed")
        except Exception:
            print(f"✓ GET_INSTANCE_{non_existent} failed as expected")
        
        # UPDATE non-existent
        try:
            self.client.update_instance(non_existent, {"description": "test"})
            print(f"✗ UPDATE_INSTANCE_{non_existent} should have failed")
        except Exception:
            print(f"✓ UPDATE_INSTANCE_{non_existent} failed as expected")
        
        # DELETE non-existent
        try:
            self.client.delete_instance(non_existent)
            print(f"✗ DELETE_INSTANCE_{non_existent} should have failed")
        except Exception:
            print(f"✓ DELETE_INSTANCE_{non_existent} failed as expected")
        
        # RESTART non-existent
        try:
            self.client.restart_instance(non_existent)
            print(f"✗ RESTART_INSTANCE_{non_existent} should have failed")
        except Exception:
            print(f"✓ RESTART_INSTANCE_{non_existent} failed as expected")
    
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
                self.client.delete_instance(self.test_instance_name)
                print(f"✓ DELETE_INSTANCE_{self.test_instance_name} initiated")
            except Exception as e:
                print(f"✗ DELETE_INSTANCE_{self.test_instance_name} failed: {e}")
                
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
        """Display results in tabulated format"""
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
        print("INSTANCE LEVEL OPERATIONS - TEST RESULTS")
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
        
        # Operation breakdown
        operations = {}
        for result in test_results:
            op = result.test_case.split('_')[0]
            operations[op] = operations.get(op, 0) + 1
        
        print(f"\n📋 OPERATION BREAKDOWN:")
        for op, count in sorted(operations.items()):
            print(f"   {op}: {count}")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in test_results:
                if result.status == "FAIL":
                    print(f"   - {result.test_case}: {result.response_code} {result.response_message}")


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
