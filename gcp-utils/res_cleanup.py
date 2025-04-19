def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Clean up resources in a GCP project")
    parser.add_argument("--project-id", "-p", help="GCP Project ID (optional, will prompt if not provided)")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Dry run mode (list only, no deletion)")
    parser.add_argument("--workers", "-w", type=int, default=5, help="Maximum number of concurrent deletions")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    print("="*80)
    print("GCP RESOURCE CLEANUP UTILITY")
    print("="*80)
    print("\nThis script will delete resources in a specified GCP project.")
    
    # Get project ID from command line or prompt
    project_id = args.project_id
    if not project_id:
        project_id = input("\nEnter GCP Project ID: ").strip()
        while not project_id:
            print("Project ID cannot be empty.")
            project_id = input("Enter GCP Project ID: ").strip()
    
    # Check for GCP_AUTH_TOKEN environment variable
    auth_token = os.environ.get('GCP_AUTH_TOKEN')
    if not auth_token:
        print("\n⚠️  Environment variable GCP_AUTH_TOKEN not found.")
        print("Please set the GCP_AUTH_TOKEN environment variable with your access token.")
        print("Example: export GCP_AUTH_TOKEN=your_access_token")
        sys.exit(1)
    else:
        logger.info("Found GCP_AUTH_TOKEN environment variable")
    
    # Display information about what will be done
    print("\n" + "="*80)
    print(f"READY TO CLEAN UP PROJECT: {project_id}")
    print("="*80)
    print("\nThis will scan for and delete the following resource types:")
    print("- Compute Engine instances and disks")
    print("- GKE clusters")
    print("- Cloud SQL instances")
    print("- Cloud Functions")
    print("- Cloud Run services")
    print("- Pub/Sub topics")
    print("- Firestore indexes")
    print("- Storage buckets")
    print("- BigQuery datasets")
    print("- VPC networks (excluding default)")
    print("- Spanner instances and databases")
    print("- Cloud Composer environments")
    print("- Memorystore instances (Redis and Memcached)")
    print("- Log Buckets and Log Sinks")
    print("- Data Catalog entries and tag templates")
    print("- Dataproc clusters")
    print("- Dataproc Serverless batches and sessions")
    print("- AI Platform resources (models, datasets, endpoints)")
    print("- API Gateway resources")
    print("- IoT Core registries and devices")
    print("- Filestore instances")
    
    if args.dry_run:
        print("\n⚠️  DRY RUN MODE: Resources will only be listed, not deleted.")
    else:
        print("\n⚠️  WARNING: THIS OPERATION WILL DELETE RESOURCES! IT CANNOT BE UNDONE!")
    
    # Get confirmation
    confirm = input("\nAre you sure you want to proceed? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("Operation cancelled by user.")
        return
    
    try:
        cleaner = GCPResourceCleaner(
            project_id=project_id,
            dry_run=args.dry_run,
            max_workers=args.workers,
            auth_token=auth_token
        )
        cleaner.run_cleanup()
    except KeyboardInterrupt:
        logger.warning("Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()    def run_cleanup(self) -> None:
        """Run the full cleanup process"""
        logger.info(f"Starting resource cleanup for project: {self.project_id}")
        
        # Call all cleanup methods
        self.cleanup_compute_instances()
        self.cleanup_compute_disks()
        self.cleanup_gke_clusters()
        self.cleanup_cloud_sql()
        self.cleanup_cloud_functions()
        self.cleanup_cloud_run()
        self.cleanup_pubsub()
        self.cleanup_firestore_indexes()
        self.cleanup_storage_buckets()
        self.cleanup_bigquery_datasets()
        self.cleanup_vpc_networks()
        
        # Additional services
        self.cleanup_spanner()
        self.cleanup_composer()
        self.cleanup_memorystore()
        self.cleanup_logging()
        self.cleanup_data_catalog()
        self.cleanup_dataproc()
        self.cleanup_dataproc_serverless()
        self.cleanup_ai_platform()
        self.cleanup_api_gateway()
        self.cleanup_iot()
        self.cleanup_filestore()
        
        # Print summary
        self.print_summary()

    def print_summary(self) -> None:
        """Print a summary of the cleanup operation"""
        print("\n" + "="*80)
        print(f"GCP RESOURCE CLEANUP SUMMARY FOR PROJECT: {self.project_id}")
        print("="*80)
        
        # Successful deletions
        if self.deleted_resources:
            print("\nSUCCESSFULLY DELETED RESOURCES:")
            table_data = []
            for resource_type, name, status in self.deleted_resources:
                table_data.append([resource_type, name, "✅ " + status])
            print(tabulate(table_data, headers=["Resource Type", "Name", "Status"], tablefmt="grid"))
        else:
            print("\nNo resources were deleted.")
            
        # Skipped resources
        if self.skipped_resources:
            print("\nSKIPPED RESOURCES:")
            table_data = []
            for resource_type, name, reason in self.skipped_resources:
                table_data.append([resource_type, name, "⏭️ " + reason])
            print(tabulate(table_data, headers=["Resource Type", "Name", "Reason"], tablefmt="grid"))
            
        # Failed deletions
        if self.failed_resources:
            print("\nFAILED DELETIONS:")
            table_data = []
            for resource_type, name, error in self.failed_resources:
                error_msg = (error[:47] + '...') if len(error) > 50 else error
                table_data.append([resource_type, name, "❌ " + error_msg])
            print(tabulate(table_data, headers=["Resource Type", "Name", "Error"], tablefmt="grid"))
            
        # Missing permissions
        if self.missing_permissions:
            print("\nMISSING PERMISSIONS:")
            for resource_type in self.missing_permissions:
                print(f"⚠️  {resource_type}")
                
        print("\nSUMMARY STATISTICS:")
        print(f"Total resources deleted: {len(self.deleted_resources)}")
        print(f"Total resources skipped: {len(self.skipped_resources)}")
        print(f"Total failed deletions: {len(self.failed_resources)}")
        print(f"Resource types with missing permissions: {len(self.missing_permissions)}")
        
        if self.dry_run:
            print("\n⚠️  THIS WAS A DRY RUN. NO ACTUAL DELETIONS WERE PERFORMED.")
            
        print("="*80)
        
        # Clean up temporary files
        self._cleanup_temp_files()    def cleanup_iot(self) -> None:
        """Clean up IoT Core resources"""
        if not self._is_service_enabled("cloudiot.googleapis.com"):
            logger.info("IoT Core API is not enabled. Skipping IoT Core cleanup.")
            return
            
        # Get regions where IoT Core is available
        regions = ['us-central1', 'europe-west1', 'asia-east1']
        
        for region in regions:
            # List registries first
            registry_resources = self._list_resources(
                f"IoT Core registries in {region}",
                f"gcloud iot registries list --region={region} --format=json"
            )
            
            for registry in registry_resources:
                registry_id = registry.get('id')
                if not registry_id:
                    continue
                
                # For each registry, list and delete devices first
                device_resources = self._list_resources(
                    f"IoT Core devices in registry {registry_id}",
                    f"gcloud iot devices list --registry={registry_id} --region={region} --format=json"
                )
                
                # Add registry and region to device resources for deletion
                for device in device_resources:
                    device['registry'] = registry_id
                    device['region'] = region
                
                self._delete_resources(
                    "IoT Core Device",
                    device_resources,
                    "gcloud iot devices delete {id} --registry={registry} --region={region} --quiet"
                )
                
                # Then delete the registry
                registry['region'] = region
                self._delete_resource(
                    "IoT Core Registry",
                    registry,
                    "gcloud iot registries delete {id} --region={region} --quiet"
                )

    def cleanup_filestore(self) -> None:
        """Clean up Filestore instances"""
        if not self._is_service_enabled("file.googleapis.com"):
            logger.info("Filestore API is not enabled. Skipping Filestore cleanup.")
            return
            
        # List all zones for Filestore instances
        zone_cmd = "gcloud filestore instances list --format='value(zone)' | sort | uniq"
        success, output, error = self._run_command(zone_cmd)
        
        if not success or not output:
            logger.info("No Filestore zones found or unable to list zones")
            return
            
        zones = output.strip().split('\n')
        
        for zone in zones:
            zone = zone.strip()
            if not zone:
                continue
                
            instance_resources = self._list_resources(
                f"Filestore instances in zone {zone}",
                f"gcloud filestore instances list --filter='zone:{zone}' --format=json"
            )
            
            # Add zone to resources for deletion
            for resource in instance_resources:
                resource['zone'] = zone
                
            self._delete_resources(
                "Filestore Instance",
                instance_resources,
                "gcloud filestore instances delete {name} --zone={zone} --quiet"
            )    def cleanup_ai_platform(self) -> None:
        """Clean up AI Platform resources (models, datasets, etc.)"""
        if not self._is_service_enabled("aiplatform.googleapis.com"):
            logger.info("AI Platform API is not enabled. Skipping AI Platform cleanup.")
            return
            
        # Get regions where AI Platform is available
        regions = ['us-central1', 'europe-west4', 'asia-east1', 'global']
        
        for region in regions:
            logger.info(f"Checking for AI Platform resources in {region}")
            
            # Clean up models
            model_resources = self._list_resources(
                f"AI Platform models in {region}",
                f"gcloud ai models list --region={region} --format=json"
            )
            
            # Add region to resources for deletion
            for resource in model_resources:
                resource['region'] = region
                
            self._delete_resources(
                "AI Platform Model",
                model_resources,
                "gcloud ai models delete {name} --region={region} --quiet"
            )
            
            # Clean up datasets
            dataset_resources = self._list_resources(
                f"AI Platform datasets in {region}",
                f"gcloud ai datasets list --region={region} --format=json"
            )
            
            # Add region to resources for deletion
            for resource in dataset_resources:
                resource['region'] = region
                
            self._delete_resources(
                "AI Platform Dataset",
                dataset_resources,
                "gcloud ai datasets delete {name} --region={region} --quiet"
            )
            
            # Clean up endpoints
            endpoint_resources = self._list_resources(
                f"AI Platform endpoints in {region}",
                f"gcloud ai endpoints list --region={region} --format=json"
            )
            
            # Add region to resources for deletion
            for resource in endpoint_resources:
                resource['region'] = region
                
            self._delete_resources(
                "AI Platform Endpoint",
                endpoint_resources,
                "gcloud ai endpoints delete {name} --region={region} --quiet"
            )

    def cleanup_api_gateway(self) -> None:
        """Clean up API Gateway resources"""
        if not self._is_service_enabled("apigateway.googleapis.com"):
            logger.info("API Gateway API is not enabled. Skipping API Gateway cleanup.")
            return
            
        # Clean up gateways
        gateway_resources = self._list_resources(
            "API Gateways",
            "gcloud api-gateway gateways list --format=json"
        )
        
        for resource in gateway_resources:
            # Format may be projects/*/locations/*/gateways/*
            if 'name' in resource:
                parts = resource['name'].split('/')
                if len(parts) >= 6:
                    resource['location'] = parts[3]
                    resource['gateway_id'] = parts[5]
        
        self._delete_resources(
            "API Gateway",
            gateway_resources,
            "gcloud api-gateway gateways delete {gateway_id} --location={location} --quiet"
        )
        
        # Clean up APIs
        api_resources = self._list_resources(
            "API Gateway APIs",
            "gcloud api-gateway apis list --format=json"
        )
        
        self._delete_resources(
            "API Gateway API",
            api_resources,
            "gcloud api-gateway apis delete {name} --quiet"
        )#!/usr/bin/env python3
import subprocess
import json
import logging
import argparse
import sys
import os
import tempfile
import getpass
from datetime import datetime
from tabulate import tabulate
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"gcp_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

class GCPResourceCleaner:
    def __init__(self, project_id: str, dry_run: bool = False, max_workers: int = 5, auth_token: str = None):
        """
        Initialize the GCP Resource Cleaner.
        
        Args:
            project_id: The GCP project ID
            dry_run: If True, only list resources without deleting
            max_workers: Maximum number of concurrent deletion operations
            auth_token: Authentication token for GCP from GCP_AUTH_TOKEN environment variable
        """
        self.project_id = project_id
        self.dry_run = dry_run
        self.max_workers = max_workers
        self.auth_token = auth_token
        self.deleted_resources = []
        self.failed_resources = []
        self.skipped_resources = []
        self.missing_permissions = []
        self.temp_files = []
        self.skip_confirmation = False
        
        # Authenticate with GCP if token is provided
        if self.auth_token:
            self._authenticate()
        
        # Configure GCloud project
        self._run_command(f"gcloud config set project {self.project_id}")
        logger.info(f"GCP Resource Cleaner initialized for project: {self.project_id}")
        if self.dry_run:
            logger.info("DRY RUN MODE: Resources will be listed but not deleted")

    def _authenticate(self):
        """Authenticate with GCP using access token from GCP_AUTH_TOKEN"""
        try:
            logger.info("Authenticating with GCP using access token from GCP_AUTH_TOKEN...")
            
            # Set the access token directly using gcloud config
            command = f"gcloud auth print-access-token"
            success, output, error = self._run_command(command)
            
            if not success:
                logger.error(f"Access token authentication failed: {error}")
                raise Exception("GCP authentication failed with token from GCP_AUTH_TOKEN")
            else:
                logger.info("Successfully authenticated with GCP_AUTH_TOKEN")
                
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            sys.exit(1)

    def _cleanup_temp_files(self):
        """Clean up any temporary files created during the process"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"Removed temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_file}: {str(e)}")

    def _run_command(self, command: str) -> Tuple[bool, str, str]:
        """
        Run a shell command and return the result.
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        logger.debug(f"Running command: {command}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return (result.returncode == 0, result.stdout.strip(), result.stderr.strip())
        except Exception as e:
            logger.error(f"Command execution error: {str(e)}")
            return (False, "", str(e))

    def _is_service_enabled(self, service_name: str) -> bool:
        """
        Check if a specific GCP service is enabled for the project.
        
        Args:
            service_name: The service name to check (e.g., compute.googleapis.com)
            
        Returns:
            bool: True if the service is enabled, False otherwise
        """
        logger.info(f"Checking if {service_name} is enabled...")
        check_cmd = f"gcloud services list --enabled --filter={service_name} --format=json --project={self.project_id}"
        success, output, error = self._run_command(check_cmd)
        
        if not success:
            logger.warning(f"Failed to check if {service_name} is enabled: {error}")
            return False
            
        try:
            services = json.loads(output) if output else []
            is_enabled = len(services) > 0
            
            if is_enabled:
                logger.info(f"Service {service_name} is enabled for this project")
            else:
                logger.info(f"Service {service_name} is not enabled for this project")
                
            return is_enabled
        except json.JSONDecodeError:
            logger.error(f"Failed to parse service check result for {service_name}")
            return False

    def _parse_resources(self, output: str, format_type: str) -> List[Dict[str, str]]:
        """
        Parse command output into a list of resource dictionaries.
        
        Args:
            output: Command output
            format_type: Format of the output ('json' or 'table')
            
        Returns:
            List of resource dictionaries
        """
        if not output:
            return []
            
        if format_type == 'json':
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON: {output}")
                return []
        else:
            # Parse table format (assuming lines with fields separated by spaces)
            lines = [line for line in output.splitlines() if line.strip()]
            if len(lines) <= 1:  # No data or only header
                return []
                
            # Simple parsing for table format
            result = []
            for line in lines[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 2:
                    result.append({"name": parts[0], "zone": parts[1] if len(parts) > 1 else "global"})
            return result

    def _list_resources(self, resource_type: str, list_command: str, format_type: str = 'json') -> List[Dict[str, Any]]:
        """
        List resources of a specific type.
        
        Args:
            resource_type: Type of resource (for logging)
            list_command: Command to list resources
            format_type: Format of the output ('json' or 'table')
            
        Returns:
            List of resources
        """
        logger.info(f"Scanning for {resource_type}...")
        success, output, error = self._run_command(list_command)
        
        if not success:
            if "Required 'compute.instances.list' permission" in error or "permission denied" in error.lower():
                logger.warning(f"Missing permissions to list {resource_type}: {error}")
                self.missing_permissions.append(resource_type)
                return []
            elif "not found" in error.lower() or "not installed" in error.lower():
                logger.info(f"Service {resource_type} is not enabled or installed")
                return []
            else:
                logger.error(f"Error listing {resource_type}: {error}")
                return []
                
        resources = self._parse_resources(output, format_type)
        resource_count = len(resources)
        
        if resource_count > 0:
            logger.info(f"Found {resource_count} {resource_type}")
        else:
            logger.info(f"No {resource_type} found")
            
        return resources

    def _delete_resource(self, resource_type: str, resource: Dict[str, Any], delete_command: str) -> bool:
        """
        Delete a specific resource.
        
        Args:
            resource_type: Type of resource
            resource: Resource details
            delete_command: Command template for deletion
            
        Returns:
            True if deletion was successful, False otherwise
        """
        resource_name = resource.get('name', '')
        resource_zone = resource.get('zone', 'global')
        resource_region = resource.get('region', '')
        
        # Format the command with resource details
        formatted_command = delete_command.format(
            name=resource_name,
            zone=resource_zone,
            region=resource_region,
            project=self.project_id
        )
        
        resource_identifier = f"{resource_type}/{resource_name}"
        if resource_zone and resource_zone != 'global':
            resource_identifier += f" (zone: {resource_zone})"
        elif resource_region:
            resource_identifier += f" (region: {resource_region})"
            
        if self.dry_run:
            logger.info(f"Would delete: {resource_identifier}")
            self.deleted_resources.append((resource_type, resource_name, "dry-run"))
            return True
            
        # Get interactive approval for this specific resource
        print(f"\nReady to delete: {resource_identifier}")
        confirm = input("Delete this resource? (yes/no/all/quit): ").strip().lower()
        
        if confirm == "quit":
            logger.info("User chose to quit. Stopping deletion process.")
            print("\nDeletion process stopped by user.")
            sys.exit(0)
        elif confirm == "all":
            # Set a flag to skip future confirmations
            self.skip_confirmation = True
            logger.info("User chose to delete all resources without further confirmation.")
        elif confirm != "yes":
            logger.info(f"User skipped deletion of {resource_identifier}")
            self.skipped_resources.append((resource_type, resource_name, "user-skipped"))
            return False
            
        logger.info(f"Deleting {resource_identifier}...")
        success, output, error = self._run_command(formatted_command)
        
        if success:
            logger.info(f"Successfully deleted {resource_identifier}")
            self.deleted_resources.append((resource_type, resource_name, "success"))
            return True
        else:
            logger.error(f"Failed to delete {resource_identifier}: {error}")
            self.failed_resources.append((resource_type, resource_name, error))
            return False

    def _delete_resources(self, resource_type: str, resources: List[Dict[str, Any]], delete_command: str) -> None:
        """
        Delete multiple resources of the same type.
        
        Args:
            resource_type: Type of resource
            resources: List of resources
            delete_command: Command template for deletion
        """
        if not resources:
            return
        
        # Since we need interactive confirmation, we can't use ThreadPoolExecutor here
        # Instead, process resources sequentially
        for resource in resources:
            if hasattr(self, 'skip_confirmation') and self.skip_confirmation:
                # User has chosen to delete all without confirmation
                self._delete_resource(resource_type, resource, delete_command)
            else:
                # Get confirmation for each resource
                self._delete_resource(resource_type, resource, delete_command)

    def cleanup_compute_instances(self) -> None:
        """Clean up Compute Engine instances"""
        if not self._is_service_enabled("compute.googleapis.com"):
            logger.info("Compute Engine API is not enabled. Skipping compute instances cleanup.")
            return

        resources = self._list_resources(
            "Compute Engine instances",
            "gcloud compute instances list --format=json"
        )
        self._delete_resources(
            "Compute Instance", 
            resources,
            "gcloud compute instances delete {name} --zone={zone} --quiet"
        )

    def cleanup_compute_disks(self) -> None:
        """Clean up Compute Engine disks"""
        if not self._is_service_enabled("compute.googleapis.com"):
            logger.info("Compute Engine API is not enabled. Skipping compute disks cleanup.")
            return

        resources = self._list_resources(
            "Compute Engine disks",
            "gcloud compute disks list --format=json"
        )
        self._delete_resources(
            "Compute Disk", 
            resources,
            "gcloud compute disks delete {name} --zone={zone} --quiet"
        )

    def cleanup_gke_clusters(self) -> None:
        """Clean up GKE clusters"""
        if not self._is_service_enabled("container.googleapis.com"):
            logger.info("GKE API is not enabled. Skipping GKE clusters cleanup.")
            return

        resources = self._list_resources(
            "GKE clusters",
            "gcloud container clusters list --format=json"
        )
        self._delete_resources(
            "GKE Cluster", 
            resources,
            "gcloud container clusters delete {name} --zone={zone} --quiet"
        )

    def cleanup_cloud_sql(self) -> None:
        """Clean up Cloud SQL instances"""
        if not self._is_service_enabled("sqladmin.googleapis.com"):
            logger.info("Cloud SQL Admin API is not enabled. Skipping Cloud SQL cleanup.")
            return

        resources = self._list_resources(
            "Cloud SQL instances",
            "gcloud sql instances list --format=json"
        )
        self._delete_resources(
            "Cloud SQL", 
            resources,
            "gcloud sql instances delete {name} --quiet"
        )

    def cleanup_cloud_functions(self) -> None:
        """Clean up Cloud Functions"""
        if not self._is_service_enabled("cloudfunctions.googleapis.com"):
            logger.info("Cloud Functions API is not enabled. Skipping Cloud Functions cleanup.")
            return
        
        # Use a timeout for the command in case it hangs
        list_cmd = f"timeout 30 gcloud functions list --format=json --project={self.project_id}"
        success, output, error = self._run_command(list_cmd)
        
        if not success:
            if "timeout" in error:
                logger.warning(f"Command timed out while listing Cloud Functions. Skipping this resource type.")
                return
            elif "Required 'cloudfunctions.functions.list' permission" in error or "permission denied" in error.lower():
                logger.warning(f"Missing permissions to list Cloud Functions: {error}")
                self.missing_permissions.append("Cloud Functions")
                return
            else:
                logger.error(f"Error listing Cloud Functions: {error}")
                return
                
        try:
            resources = json.loads(output) if output else []
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from Cloud Functions list output")
            return
            
        resource_count = len(resources)
        
        if resource_count > 0:
            logger.info(f"Found {resource_count} Cloud Functions")
            self._delete_resources(
                "Cloud Function", 
                resources,
                "gcloud functions delete {name} --region={region} --quiet"
            )
        else:
            logger.info("No Cloud Functions found")

    def cleanup_cloud_run(self) -> None:
        """Clean up Cloud Run services"""
        if not self._is_service_enabled("run.googleapis.com"):
            logger.info("Cloud Run API is not enabled. Skipping Cloud Run cleanup.")
            return
            
        resources = self._list_resources(
            "Cloud Run services",
            "gcloud run services list --format=json"
        )
        self._delete_resources(
            "Cloud Run Service", 
            resources,
            "gcloud run services delete {name} --region={region} --quiet"
        )

    def cleanup_pubsub(self) -> None:
        """Clean up Pub/Sub topics"""
        if not self._is_service_enabled("pubsub.googleapis.com"):
            logger.info("Pub/Sub API is not enabled. Skipping Pub/Sub cleanup.")
            return
            
        resources = self._list_resources(
            "Pub/Sub topics",
            "gcloud pubsub topics list --format=json"
        )
        
        # Extract only the topic name from the full path
        for resource in resources:
            if 'name' in resource:
                resource['short_name'] = resource['name'].split('/')[-1]
        
        self._delete_resources(
            "Pub/Sub Topic", 
            resources,
            "gcloud pubsub topics delete {short_name} --quiet"
        )

    def cleanup_firestore_indexes(self) -> None:
        """Clean up Firestore indexes"""
        if not self._is_service_enabled("firestore.googleapis.com"):
            logger.info("Firestore API is not enabled. Skipping Firestore indexes cleanup.")
            return
            
        resources = self._list_resources(
            "Firestore indexes",
            "gcloud firestore indexes composite list --format=json"
        )
        self._delete_resources(
            "Firestore Index", 
            resources,
            "gcloud firestore indexes composite delete {name} --quiet"
        )

    def cleanup_storage_buckets(self) -> None:
        """Clean up Storage buckets"""
        if not self._is_service_enabled("storage.googleapis.com"):
            logger.info("Storage API is not enabled. Skipping Storage buckets cleanup.")
            return
            
        resources = self._list_resources(
            "Storage buckets",
            "gsutil ls -p {project} | grep 'gs://'".format(project=self.project_id),
            format_type='table'
        )
        
        # Convert the bucket URLs to resource dictionaries
        bucket_resources = []
        for bucket_url in resources:
            bucket_resources.append({"name": bucket_url.get('name')})
        
        self._delete_resources(
            "Storage Bucket", 
            bucket_resources,
            "gsutil -m rm -r {name}"
        )

    def cleanup_bigquery_datasets(self) -> None:
        """Clean up BigQuery datasets"""
        if not self._is_service_enabled("bigquery.googleapis.com"):
            logger.info("BigQuery API is not enabled. Skipping BigQuery datasets cleanup.")
            return
            
        resources = self._list_resources(
            "BigQuery datasets",
            "bq ls --format=json --project_id={project}".format(project=self.project_id)
        )
        self._delete_resources(
            "BigQuery Dataset", 
            resources,
            "bq rm -r -f {project}:{name}"
        )

    def cleanup_vpc_networks(self) -> None:
        """Clean up VPC networks (excluding default)"""
        if not self._is_service_enabled("compute.googleapis.com"):
            logger.info("Compute Engine API is not enabled. Skipping VPC networks cleanup.")
            return
            
        resources = self._list_resources(
            "VPC networks",
            "gcloud compute networks list --filter='name!=default' --format=json"
        )
        self._delete_resources(
            "VPC Network", 
            resources,
            "gcloud compute networks delete {name} --quiet"
        )

    def cleanup_spanner(self) -> None:
        """Clean up Spanner instances and databases"""
        if not self._is_service_enabled("spanner.googleapis.com"):
            logger.info("Spanner API is not enabled. Skipping Spanner cleanup.")
            return

        # First list all instances
        instances = self._list_resources(
            "Spanner instances",
            "gcloud spanner instances list --format=json"
        )
        
        if not instances:
            logger.info("No Spanner instances found")
            return

        for instance in instances:
            instance_id = instance.get('name', '').split('/')[-1]
            if not instance_id:
                continue
                
            # For each instance, list its databases first
            databases = self._list_resources(
                f"Spanner databases in instance {instance_id}",
                f"gcloud spanner databases list --instance={instance_id} --format=json"
            )
            
            # Delete each database first
            for db in databases:
                db_id = db.get('name', '').split('/')[-1]
                if not db_id:
                    continue
                    
                db_resource = {
                    "name": db_id,
                    "instance": instance_id
                }
                self._delete_resource(
                    "Spanner Database",
                    db_resource,
                    "gcloud spanner databases delete {name} --instance={instance} --quiet"
                )
            
            # Then delete the instance itself
            self._delete_resource(
                "Spanner Instance",
                instance,
                "gcloud spanner instances delete {name} --quiet"
            )

    def cleanup_composer(self) -> None:
        """Clean up Cloud Composer environments"""
        if not self._is_service_enabled("composer.googleapis.com"):
            logger.info("Cloud Composer API is not enabled. Skipping Composer cleanup.")
            return
            
        resources = self._list_resources(
            "Cloud Composer environments",
            "gcloud composer environments list --format=json"
        )
        
        for resource in resources:
            # Extract location and name from the full path
            if 'name' in resource:
                parts = resource['name'].split('/')
                if len(parts) >= 6:  # Format: projects/PROJECT/locations/LOCATION/environments/NAME
                    resource['location'] = parts[3]
                    resource['env_name'] = parts[5]
        
        self._delete_resources(
            "Cloud Composer Environment",
            resources,
            "gcloud composer environments delete {env_name} --location={location} --quiet"
        )

    def cleanup_memorystore(self) -> None:
        """Clean up Memorystore instances (Redis and Memcached)"""
        # Check for Redis API
        redis_enabled = self._is_service_enabled("redis.googleapis.com")
        memcached_enabled = self._is_service_enabled("memcache.googleapis.com")
        
        if not redis_enabled and not memcached_enabled:
            logger.info("Neither Redis nor Memcached APIs are enabled. Skipping Memorystore cleanup.")
            return
            
        # Clean up Redis instances
        if redis_enabled:
            redis_resources = self._list_resources(
                "Memorystore Redis instances",
                "gcloud redis instances list --format=json"
            )
            
            for resource in redis_resources:
                # Extract location and name from the full path
                if 'name' in resource:
                    parts = resource['name'].split('/')
                    if len(parts) >= 6:  # Format: projects/PROJECT/locations/LOCATION/instances/NAME
                        resource['location'] = parts[3]
                        resource['instance_id'] = parts[5]
            
            self._delete_resources(
                "Memorystore Redis Instance",
                redis_resources,
                "gcloud redis instances delete {instance_id} --region={location} --quiet"
            )
            
        # Clean up Memcached instances
        if memcached_enabled:
            memcached_resources = self._list_resources(
                "Memorystore Memcached instances",
                "gcloud memcache instances list --format=json"
            )
            
            for resource in memcached_resources:
                # Extract location and name from the full path
                if 'name' in resource:
                    parts = resource['name'].split('/')
                    if len(parts) >= 6:  # Format: projects/PROJECT/locations/LOCATION/instances/NAME
                        resource['location'] = parts[3]
                        resource['instance_id'] = parts[5]
            
            self._delete_resources(
                "Memorystore Memcached Instance",
                memcached_resources,
                "gcloud memcache instances delete {instance_id} --region={location} --quiet"
            )

    def cleanup_logging(self) -> None:
        """Clean up Log Buckets and Log Sinks"""
        if not self._is_service_enabled("logging.googleapis.com"):
            logger.info("Logging API is not enabled. Skipping Logging cleanup.")
            return
            
        # First clean up log sinks
        sink_resources = self._list_resources(
            "Log Sinks",
            "gcloud logging sinks list --format=json"
        )
        
        # Skip _Default sink which cannot be deleted
        filtered_sinks = [sink for sink in sink_resources if sink.get('name') != '_Default']
        
        self._delete_resources(
            "Log Sink",
            filtered_sinks,
            "gcloud logging sinks delete {name} --quiet"
        )
        
        # Then clean up log buckets (only user-created ones, not _Default or _Required)
        bucket_resources = self._list_resources(
            "Log Buckets",
            "gcloud logging buckets list --format=json"
        )
        
        # Filter out default and required buckets
        filtered_buckets = []
        for bucket in bucket_resources:
            bucket_name = bucket.get('name', '')
            # Skip default and required buckets
            if bucket_name.endswith('_Default') or bucket_name.endswith('_Required'):
                continue
                
            # Extract location and bucket name from the full path
            # Format is typically "projects/PROJECT_ID/locations/LOCATION/buckets/BUCKET_ID"
            parts = bucket_name.split('/')
            if len(parts) >= 6:
                bucket['location'] = parts[3]
                bucket['bucket_id'] = parts[5]
                filtered_buckets.append(bucket)
        
        self._delete_resources(
            "Log Bucket",
            filtered_buckets,
            "gcloud logging buckets delete {bucket_id} --location={location} --quiet"
        )

    def cleanup_data_catalog(self) -> None:
        """Clean up Data Catalog entries and tag templates"""
        if not self._is_service_enabled("datacatalog.googleapis.com"):
            logger.info("Data Catalog API is not enabled. Skipping Data Catalog cleanup.")
            return
            
        # First clean up entries
        entry_resources = self._list_resources(
            "Data Catalog entries",
            "gcloud data-catalog entries list --format=json"
        )
        
        # Format entry resources for deletion
        formatted_entries = []
        for entry in entry_resources:
            if 'name' in entry:
                formatted_entries.append(entry)
        
        self._delete_resources(
            "Data Catalog Entry",
            formatted_entries,
            "gcloud data-catalog entries delete {name} --quiet"
        )
        
        # Then clean up tag templates
        template_resources = self._list_resources(
            "Data Catalog tag templates",
            "gcloud data-catalog tag-templates list --format=json"
        )
        
        # Format template resources for deletion
        formatted_templates = []
        for template in template_resources:
            if 'name' in template:
                # Extract location and template ID
                parts = template['name'].split('/')
                if len(parts) >= 6:  # Format: projects/PROJECT/locations/LOCATION/tagTemplates/TEMPLATE_ID
                    template['location'] = parts[3]
                    template['template_id'] = parts[5]
                    formatted_templates.append(template)
        
        self._delete_resources(
            "Data Catalog Tag Template",
            formatted_templates,
            "gcloud data-catalog tag-templates delete {template_id} --location={location} --force --quiet"
        )

    def cleanup_dataproc(self) -> None:
        """Clean up Dataproc clusters"""
        if not self._is_service_enabled("dataproc.googleapis.com"):
            logger.info("Dataproc API is not enabled. Skipping Dataproc cleanup.")
            return
            
        # Get regions where Dataproc is available for this project
        regions_cmd = "gcloud dataproc regions list --format=json"
        success, output, error = self._run_command(regions_cmd)
        
        if not success or not output:
            logger.warning(f"Failed to list Dataproc regions: {error}")
            return
            
        try:
            regions = json.loads(output)
            region_names = [region.get('name') for region in regions if 'name' in region]
        except json.JSONDecodeError:
            logger.error("Failed to parse Dataproc regions output")
            region_names = ['global', 'us-central1', 'us-east1', 'us-east4', 'us-west1', 'us-west2', 'us-west3', 'us-west4']  # Default regions
        
        # Check each region for clusters
        for region in region_names:
            logger.info(f"Checking for Dataproc clusters in region: {region}")
            
            cluster_resources = self._list_resources(
                f"Dataproc clusters in {region}",
                f"gcloud dataproc clusters list --region={region} --format=json"
            )
            
            # Add region to each resource for deletion command
            for resource in cluster_resources:
                resource['region'] = region
                
            self._delete_resources(
                "Dataproc Cluster",
                cluster_resources,
                "gcloud dataproc clusters delete {name} --region={region} --quiet"
            )
            
    def cleanup_dataproc_serverless(self) -> None:
        """Clean up Dataproc Serverless batches and sessions"""
        if not self._is_service_enabled("dataproc.googleapis.com"):
            logger.info("Dataproc API is not enabled. Skipping Dataproc Serverless cleanup.")
            return
            
        # Get regions where Dataproc is available
        regions_cmd = "gcloud dataproc regions list --format=json"
        success, output, error = self._run_command(regions_cmd)
        
        if not success or not output:
            logger.warning(f"Failed to list Dataproc regions: {error}")
            return
            
        try:
            regions = json.loads(output)
            region_names = [region.get('name') for region in regions if 'name' in region]
        except json.JSONDecodeError:
            logger.error("Failed to parse Dataproc regions output")
            region_names = ['global', 'us-central1', 'us-east1', 'us-east4', 'us-west1', 'us-west2', 'us-west3', 'us-west4']  # Default regions
        
        # For each region, delete batches and sessions
        for region in region_names:
            # Clean up batches
            batch_resources = self._list_resources(
                f"Dataproc Serverless batches in {region}",
                f"gcloud dataproc batches list --region={region} --format=json"
            )
            
            # Add region to each resource for deletion command
            for resource in batch_resources:
                resource['region'] = region
                
            self._delete_resources(
                "Dataproc Serverless Batch",
                batch_resources,
                "gcloud dataproc batches delete {name} --region={region} --quiet"
            )
            
            # Clean up sessions
            session_resources = self._list_resources(
                f"Dataproc Serverless sessions in {region}",
                f"gcloud dataproc sessions list --region={region} --format=json"
            )
            
            # Add region to each resource for deletion command
            for resource in session_resources:
                resource['region'] = region
                
            self._delete_resources(
                "Dataproc Serverless Session",
                session_resources,
                "gcloud dataproc sessions delete {name} --region={region} --quiet"
            )
