#!/usr/bin/env python3
"""
Import Dataproc Compute Profile to Cloud Data Fusion

This script imports a Dataproc compute profile configuration from a file into
a Cloud Data Fusion instance. It reads the configuration from a JSON file in the
specified directory and creates or updates the profile in Data Fusion.

Authentication:
    This script uses an access token from Harness secrets, which should be
    provided via the GOOGLE_ACCESS_TOKEN environment variable.

Usage:
    python import_compute_profile.py --profile-name PROFILE_NAME --project-id PROJECT_ID [options]

Arguments:
    --profile-name         Name of the Dataproc profile to import (required)
    --project-id           GCP Project ID (required)
    --config-dir           Directory containing profile configuration files (default: ./compute_profile)
    --datafusion-instance  Data Fusion instance name (default: auto-detect)
    --datafusion-location  Data Fusion instance location (default: us-central1)
    --namespace            Data Fusion namespace (default: default)
    --verbose              Enable verbose logging
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
import requests
from google.cloud import data_fusion_v1
from google.oauth2.credentials import Credentials

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('import_compute_profile')

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Import Dataproc compute profile to Data Fusion')
    parser.add_argument('--profile-name', required=True,
                      help='Name of the Dataproc profile to import')
    parser.add_argument('--project-id', required=True,
                      help='GCP Project ID')
    parser.add_argument('--config-dir', default='./compute_profile',
                      help='Directory containing profile configuration files (default: ./compute_profile)')
    parser.add_argument('--datafusion-instance', default=None,
                      help='Data Fusion instance name (default: auto-detect)')
    parser.add_argument('--datafusion-location', default='us-central1',
                      help='Data Fusion instance location (default: us-central1)')
    parser.add_argument('--namespace', default='default',
                      help='Data Fusion namespace (default: default)')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set log level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    return args

def get_access_token():
    """Get Google access token from Harness secret environment variable."""
    token = os.environ.get('GOOGLE_ACCESS_TOKEN')
    if not token:
        raise ValueError("GOOGLE_ACCESS_TOKEN environment variable not found. This should be set from Harness secrets.")
    
    logger.debug("Successfully retrieved Google access token from environment")
    return token

def get_credentials_from_token(token):
    """Create credentials object from access token."""
    try:
        credentials = Credentials(token=token)
        return credentials
    except Exception as e:
        logger.error(f"Failed to create credentials from token: {e}")
        raise ValueError(f"Invalid access token: {e}")

def load_profile_config(config_dir, profile_name):
    """Load the profile configuration from a file."""
    # Check if config_dir exists
    config_path = Path(config_dir)
    if not config_path.exists() or not config_path.is_dir():
        raise FileNotFoundError(f"Configuration directory not found: {config_dir}")
    
    # Try multiple possible file names/locations
    possible_paths = [
        config_path / f"{profile_name}.json",
        config_path / f"{profile_name}/config.json",
        config_path / "config.json",
        config_path / "profile.json"
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found profile configuration at: {path}")
            try:
                with open(path, 'r') as f:
                    config = json.load(f)
                return config
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON configuration: {e}")
                raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    raise FileNotFoundError(f"No profile configuration found for {profile_name} in {config_dir}")

def find_datafusion_instance(project_id, credentials, specified_instance=None, location=None):
    """Find Data Fusion instance or use the specified one."""
    if specified_instance:
        logger.info(f"Using specified Data Fusion instance: {specified_instance}")
        return specified_instance
    
    logger.info("No Data Fusion instance specified, attempting to find one")
    try:
        # Create a Data Fusion client with credentials
        client = data_fusion_v1.DataFusionClient(credentials=credentials)
        
        # List Data Fusion instances
        if location:
            parent = f"projects/{project_id}/locations/{location}"
            logger.debug(f"Looking for Data Fusion instances in: {parent}")
            
            # Create a proper request object
            request = data_fusion_v1.ListInstancesRequest(parent=parent)
            response = client.list_instances(request=request)
            instances = list(response)
            
            if instances:
                # Find the first running instance
                for instance in instances:
                    if instance.state == data_fusion_v1.Instance.State.RUNNING:
                        logger.info(f"Found running Data Fusion instance: {instance.name}")
                        # Extract instance name from the full resource name
                        return instance.name.split('/')[-1]
                
                # If no running instance, use the first one
                logger.warning(f"No running Data Fusion instances found in {location}, using: {instances[0].name}")
                return instances[0].name.split('/')[-1]
            else:
                logger.warning(f"No Data Fusion instances found in {location}")
        else:
            # Try multiple locations
            locations = ['us-central1', 'us-east1', 'us-west1', 'europe-west1', 'asia-east1']
            for loc in locations:
                parent = f"projects/{project_id}/locations/{loc}"
                logger.debug(f"Looking for Data Fusion instances in: {parent}")
                try:
                    # Create a proper request object
                    request = data_fusion_v1.ListInstancesRequest(parent=parent)
                    response = client.list_instances(request=request)
                    instances = list(response)
                    
                    if instances:
                        # Find running instance
                        for instance in instances:
                            if instance.state == data_fusion_v1.Instance.State.RUNNING:
                                logger.info(f"Found running Data Fusion instance in {loc}: {instance.name}")
                                return instance.name.split('/')[-1]
                        
                        # If no running instance, use the first one
                        logger.warning(f"No running Data Fusion instances found in {loc}, using: {instances[0].name}")
                        return instances[0].name.split('/')[-1]
                except Exception as e:
                    logger.debug(f"Error looking for instances in {loc}: {e}")
                    continue
        
        # If we get here, no instances were found
        raise ValueError(f"No Data Fusion instances found in project {project_id}")
        
    except Exception as e:
        logger.error(f"Error finding Data Fusion instance: {e}")
        raise ValueError(f"Failed to find Data Fusion instance: {e}")

def get_datafusion_api_endpoint(project_id, location, instance_name, credentials):
    """Get the API endpoint for the Data Fusion instance."""
    try:
        # Create a Data Fusion client
        client = data_fusion_v1.DataFusionClient(credentials=credentials)
        
        # Create a proper instance request
        instance_path = f"projects/{project_id}/locations/{location}/instances/{instance_name}"
        request = data_fusion_v1.GetInstanceRequest(
            name=instance_path
        )
        
        # Get instance details using the request object
        logger.debug(f"Getting Data Fusion instance details for: {instance_path}")
        instance = client.get_instance(request=request)
        
        # Extract and format API endpoint
        api_endpoint = instance.api_endpoint
        if api_endpoint.startswith('https://'):
            api_endpoint = api_endpoint[8:]
            
        logger.info(f"Data Fusion API endpoint: {api_endpoint}")
        return api_endpoint
    except Exception as e:
        logger.error(f"Error getting Data Fusion API endpoint: {e}")
        raise ValueError(f"Failed to get Data Fusion API endpoint: {e}")

def create_compute_profile(project_id, location, instance_name, namespace, profile_name, profile_config, access_token):
    """Create or update the compute profile in Data Fusion."""
    try:
        # Get the API endpoint
        credentials = get_credentials_from_token(access_token)
        api_endpoint = get_datafusion_api_endpoint(project_id, location, instance_name, credentials)
        
        # Set up the API request
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # API endpoint URL
        url = f"https://{api_endpoint}/v3/namespaces/{namespace}/profiles/{profile_name}"
        logger.info(f"API URL for profile creation: {url}")
        
        # Ensure profile has the correct name
        if 'name' not in profile_config:
            profile_config['name'] = profile_name
        elif profile_config['name'] != profile_name:
            logger.warning(f"Profile name in config ({profile_config['name']}) doesn't match specified name ({profile_name})")
            profile_config['name'] = profile_name
        
        # Ensure the profile has the correct structure
        if not profile_config.get('provisioner'):
            raise ValueError("Invalid profile configuration: missing 'provisioner' section")
            
        if profile_config.get('provisioner', {}).get('name') != 'gcp-dataproc':
            raise ValueError("Invalid profile configuration: provisioner is not 'gcp-dataproc'")
        
        # Make the API call
        logger.info(f"Creating/updating compute profile: {profile_name}")
        
        # Convert config to JSON and log a sample (not the full config for security/brevity)
        json_payload = json.dumps(profile_config)
        if logger.level <= logging.DEBUG:
            logger.debug(f"Profile configuration sample: {json.dumps(profile_config)[:200]}...")
        
        # Make the API request with error handling
        try:
            response = requests.put(url, headers=headers, data=json_payload, timeout=60)
            
            logger.debug(f"API response status code: {response.status_code}")
            logger.debug(f"API response headers: {dict(response.headers)}")
            
            # Handle the response based on status code
            if response.status_code in (200, 201):
                logger.info(f"Successfully created compute profile: {profile_name}")
                return True
            elif response.status_code == 409:
                logger.info(f"Compute profile {profile_name} already exists with the same configuration")
                return True
            else:
                # Log error details
                logger.error(f"Failed to create compute profile. Status: {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
                
                # Handle specific status codes
                if response.status_code == 401:
                    raise ValueError("Authentication failed: Invalid or expired token")
                elif response.status_code == 403:
                    raise ValueError("Permission denied: Insufficient privileges")
                elif response.status_code == 404:
                    raise ValueError(f"Not found: Check instance name, namespace, and location")
                else:
                    raise ValueError(f"Failed to create compute profile: {response.text[:200]}")
                    
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            raise ValueError("API request timed out. Check network connectivity and try again.")
        except requests.exceptions.ConnectionError:
            logger.error("Connection error")
            raise ValueError("Connection error. Check network connectivity and API endpoint.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise ValueError(f"API request failed: {e}")
    
    except ValueError as e:
        # Re-raise ValueError exceptions
        raise
    except Exception as e:
        # Log and convert other exceptions to ValueError
        logger.error(f"Error creating compute profile: {e}")
        raise ValueError(f"Error creating compute profile: {e}")

def main():
    """Main function to parse args and execute the import."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Set up variables
        profile_name = args.profile_name
        config_dir = args.config_dir
        project_id = args.project_id
        
        # Validate project ID
        if not project_id:
            raise ValueError("Project ID is required")
        
        logger.info(f"Starting import of compute profile '{profile_name}' for project '{project_id}'")
        
        # Get access token from environment (set by Harness)
        access_token = get_access_token()
        
        # Create credentials from token
        credentials = get_credentials_from_token(access_token)
        
        # Load profile configuration
        logger.info(f"Loading profile configuration from: {config_dir}")
        profile_config = load_profile_config(config_dir, profile_name)
        
        # Get Data Fusion instance
        logger.info("Finding Data Fusion instance")
        datafusion_instance = find_datafusion_instance(
            project_id, 
            credentials,
            args.datafusion_instance, 
            args.datafusion_location
        )
        
        # Create the compute profile
        logger.info(f"Creating compute profile in Data Fusion instance: {datafusion_instance}")
        create_compute_profile(
            project_id,
            args.datafusion_location,
            datafusion_instance,
            args.namespace,
            profile_name,
            profile_config,
            access_token
        )
        
        logger.info(f"Successfully imported compute profile: {profile_name}")
        return 0
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
