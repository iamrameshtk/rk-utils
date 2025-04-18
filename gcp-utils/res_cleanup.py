#!/usr/bin/env python3
import subprocess
import json
import logging
import argparse
import sys
import os
import tempfile
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
            auth_token: Authentication token for GCP. If None, uses default authentication.
        """
        self.project_id = project_id
        self.dry_run = dry_run
        self.max_workers = max_workers
        self.auth_token = auth_token
        self.deleted_resources = []
        self.failed_resources = []
        self.missing_permissions = []
        self.temp_files = []
        
        # Authenticate with GCP if token is provided
        if self.auth_token:
            self._authenticate()
        
        # Configure GCloud project
        self._run_command(f"gcloud config set project {self.project_id}")
        logger.info(f"GCP Resource Cleaner initialized for project: {self.project_id}")
        if self.dry_run:
            logger.info("DRY RUN MODE: Resources will be listed but not deleted")
            
    def _authenticate(self):
        """Authenticate with GCP using provided auth token"""
        try:
            logger.info("Authenticating with GCP using provided token...")
            
            # Create a temporary file to store the token
            fd, temp_path = tempfile.mkstemp(prefix='gcp_token_', suffix='.json')
            with os.fdopen(fd, 'w') as temp_file:
                temp_file.write(self.auth_token)
            
            self.temp_files.append(temp_path)
            
            # Set GOOGLE_APPLICATION_CREDENTIALS environment variable
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_path
            
            # Test authentication
            success, output, error = self._run_command("gcloud auth list")
            if success:
                logger.info("Successfully authenticated with GCP")
            else:
                logger.error(f"Authentication failed: {error}")
                raise Exception("GCP authentication failed")
                
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            self._cleanup_temp_files()
            raise

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
            
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            executor.map(
                lambda resource: self._delete_resource(resource_type, resource, delete_command),
                resources
            )

    def cleanup_compute_instances(self) -> None:
        """Clean up Compute Engine instances"""
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
        resources = self._list_resources(
            "Cloud Functions",
            "gcloud functions list --format=json"
        )
        self._delete_resources(
            "Cloud Function", 
            resources,
            "gcloud functions delete {name} --region={region} --quiet"
        )

    def cleanup_cloud_run(self) -> None:
        """Clean up Cloud Run services"""
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
        resources = self._list_resources(
            "VPC networks",
            "gcloud compute networks list --filter='name!=default' --format=json"
        )
        self._delete_resources(
            "VPC Network", 
            resources,
            "gcloud compute networks delete {name} --quiet"
        )

    def run_cleanup(self) -> None:
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
        
        # Print summary
        self.print_summary()

    def _cleanup_temp_files(self):
        """Clean up any temporary files created during the process"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"Removed temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_file}: {str(e)}")
                
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
        print(f"Total failed deletions: {len(self.failed_resources)}")
        print(f"Resource types with missing permissions: {len(self.missing_permissions)}")
        
        if self.dry_run:
            print("\n⚠️  THIS WAS A DRY RUN. NO ACTUAL DELETIONS WERE PERFORMED.")
            
        print("="*80)
        
        # Clean up temporary files
        self._cleanup_temp_files()

def get_auth_token_from_env():
    """
    Get GCP authentication token from environment variables.
    Checks for common GCP auth environment variables.
    
    Returns:
        str or None: The authentication token if found, None otherwise
    """
    # Check for direct token environment variable
    if 'GCP_AUTH_TOKEN' in os.environ:
        logger.info("Found GCP_AUTH_TOKEN environment variable")
        return os.environ['GCP_AUTH_TOKEN']
        
    # Check for JSON key file path
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        cred_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        logger.info(f"Found GOOGLE_APPLICATION_CREDENTIALS environment variable: {cred_path}")
        try:
            with open(cred_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not read credentials file: {str(e)}")
    
    # Check for other common GCP environment variables
    if 'GCP_SERVICE_ACCOUNT_KEY' in os.environ:
        logger.info("Found GCP_SERVICE_ACCOUNT_KEY environment variable")
        return os.environ['GCP_SERVICE_ACCOUNT_KEY']
    
    logger.info("No GCP authentication token found in environment variables")
    return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Clean up resources in a GCP project")
    parser.add_argument("--project-id", "-p", required=True, help="GCP project ID")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Dry run mode (list only, no deletion)")
    parser.add_argument("--workers", "-w", type=int, default=5, help="Maximum number of concurrent deletions")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--auth-token-file", "-a", help="Path to GCP authentication token JSON file")
    parser.add_argument("--use-env-auth", "-e", action="store_true", help="Use authentication token from environment variables")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Handle authentication
    auth_token = None
    if args.auth_token_file:
        try:
            with open(args.auth_token_file, 'r') as f:
                auth_token = f.read()
                logger.info(f"Read authentication token from file: {args.auth_token_file}")
        except Exception as e:
            logger.error(f"Failed to read authentication token file: {str(e)}")
            sys.exit(1)
    elif args.use_env_auth:
        auth_token = get_auth_token_from_env()
        if not auth_token:
            logger.warning("No authentication token found in environment variables")
        
    try:
        cleaner = GCPResourceCleaner(
            project_id=args.project_id,
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
    main()
