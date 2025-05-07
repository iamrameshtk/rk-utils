#!/usr/bin/env python3
"""
Import Dataproc Compute Profiles to Cloud Data Fusion

This script imports one or more Dataproc compute profile configurations from files into
a Cloud Data Fusion instance using the REST API. It reads configurations from 
JSON files in the specified directory and creates or updates profiles in Data Fusion.

Authentication:
    This script uses an access token from Harness secrets, which should be
    provided via the GOOGLE_ACCESS_TOKEN environment variable.

Usage:
    # Import a single profile
    python import_compute_profile.py --profile-name PROFILE_NAME --project-id PROJECT_ID [options]
    
    # Import multiple profiles
    python import_compute_profile.py --profile-dir PROFILE_DIR --project-id PROJECT_ID [options]

Arguments:
    --profile-name         Name of a single Dataproc profile to import
    --profile-dir          Directory containing multiple profile configurations to import
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
import requests
from pathlib import Path

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
    parser = argparse.ArgumentParser(description='Import Dataproc compute profiles to Data Fusion')
    profile_group = parser.add_mutually_exclusive_group(required=True)
    profile_group.add_argument('--profile-name',
                      help='Name of a single Dataproc profile to import')
    profile_group.add_argument('--profile-dir',
                      help='Directory containing multiple profile configurations to import')
    
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

def find_profile_configs(config_dir, profile_name=None, profile_dir=None):
    """
    Find one or multiple profile configurations.
    
    Args:
        config_dir: Base directory for configurations
        profile_name: Name of a single profile to import
        profile_dir: Directory containing multiple profiles to import
        
    Returns:
        Dictionary mapping profile names to their configurations
    """
    config_path = Path(config_dir)
    if not config_path.exists() or not config_path.is_dir():
        raise FileNotFoundError(f"Configuration directory not found: {config_dir}")
    
    profile_configs = {}
    
    # Single profile mode
    if profile_name:
        logger.info(f"Looking for single profile: {profile_name}")
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
                    profile_configs[profile_name] = config
                    return profile_configs
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON configuration: {e}")
                    raise ValueError(f"Invalid JSON in configuration file: {e}")
        
        raise FileNotFoundError(f"No profile configuration found for {profile_name} in {config_dir}")
    
    # Multiple profiles mode
    elif profile_dir:
        profiles_path = config_path / profile_dir if not Path(profile_dir).is_absolute() else Path(profile_dir)
        
        if not profiles_path.exists() or not profiles_path.is_dir():
            raise FileNotFoundError(f"Profiles directory not found: {profiles_path}")
        
        logger.info(f"Scanning for multiple profiles in: {profiles_path}")
        
        # Look for JSON files directly in the directory
        json_files = list(profiles_path.glob("*.json"))
        
        # Look for subdirectories with config.json files
        subdirs = [d for d in profiles_path.iterdir() if d.is_dir()]
        for subdir in subdirs:
            config_file = subdir / "config.json"
            if config_file.exists():
                json_files.append(config_file)
        
        if not json_files:
            raise FileNotFoundError(f"No profile configurations found in {profiles_path}")
        
        # Load each profile configuration
        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                
                # Determine profile name from file or config
                if file_path.name == "config.json":
                    # Use parent directory name
                    profile_name = file_path.parent.name
                else:
                    # Use file name without extension
                    profile_name = file_path.stem
                
                # If config contains a name field, use that instead
                if 'name' in config:
                    profile_name = config['name']
                
                logger.info(f"Found profile configuration for '{profile_name}' at: {file_path}")
                profile_configs[profile_name] = config
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON configuration in {file_path}: {e}")
                logger.error(f"Skipping this profile and continuing with others")
                continue
        
        if not profile_configs:
            raise ValueError("No valid profile configurations found")
        
        return profile_configs
    
    else:
        raise ValueError("Either profile_name or profile_dir must be specified")

def find_datafusion_instance(project_id, access_token, specified_instance=None, location=None):
    """Find Data Fusion instance or use the specified one."""
    if specified_instance:
        logger.info(f"Using specified Data Fusion instance: {specified_instance}")
        return specified_instance

    logger.info("No Data Fusion instance specified, attempting to find one")
    
    try:
        # Set up the API request
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # If location is specified, look in that location
        if location:
            url = f"https://datafusion.googleapis.com/v1/projects/{project_id}/locations/{location}/instances"
            logger.debug(f"Looking for Data Fusion instances in: {url}")
            
            response = requests.get(url, headers=headers, timeout=60)
            if response.status_code != 200:
                logger.error(f"Failed to list instances. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                raise ValueError(f"Failed to list Data Fusion instances: {response.text}")
            
            instances_data = response.json()
            instances = instances_data.get('instances', [])
            
            if instances:
                # Find the first running instance
                for instance in instances:
                    if instance.get('state') == 'RUNNING':
                        instance_name = instance.get('name', '').split('/')[-1]
                        logger.info(f"Found running Data Fusion instance: {instance_name}")
                        return instance_name
                
                # If no running instance, use the first one
                instance_name = instances[0].get('name', '').split('/')[-1]
                logger.warning(f"No running Data Fusion instances found, using: {instance_name}")
                return instance_name
            else:
                logger.warning(f"No Data Fusion instances found in {location}")
        else:
            # Try multiple locations
            locations = ['us-central1', 'us-east1', 'us-west1', 'europe-west1', 'asia-east1']
            for loc in locations:
                url = f"https://datafusion.googleapis.com/v1/projects/{project_id}/locations/{loc}/instances"
                logger.debug(f"Looking for Data Fusion instances in: {url}")
                
                try:
                    response = requests.get(url, headers=headers, timeout=60)
                    if response.status_code != 200:
                        continue
                    
                    instances_data = response.json()
                    instances = instances_data.get('instances', [])
                    
                    if instances:
                        # Find the first running instance
                        for instance in instances:
                            if instance.get('state') == 'RUNNING':
                                instance_name = instance.get('name', '').split('/')[-1]
                                logger.info(f"Found running Data Fusion instance in {loc}: {instance_name}")
                                return instance_name
                        
                        # If no running instance, use the first one
                        instance_name = instances[0].get('name', '').split('/')[-1]
                        logger.warning(f"No running Data Fusion instances found in {loc}, using: {instance_name}")
                        return instance_name
                except Exception as e:
                    logger.debug(f"Error looking for instances in {loc}: {e}")
                    continue
        
        # If we get here, no instances were found
        raise ValueError(f"No Data Fusion instances found in project {project_id}")
        
    except Exception as e:
        logger.error(f"Error finding Data Fusion instance: {e}")
        raise ValueError(f"Failed to find Data Fusion instance: {e}")

def get_datafusion_api_endpoint(project_id, location, instance_name, access_token):
    """Get the API endpoint for the Data Fusion instance using REST API."""
    try:
        # Set up the API request
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Get instance details
        url = f"https://datafusion.googleapis.com/v1/projects/{project_id}/locations/{location}/instances/{instance_name}"
        logger.debug(f"Getting Data Fusion instance details from: {url}")
        
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code != 200:
            logger.error(f"Failed to get instance. Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise ValueError(f"Failed to get Data Fusion instance: {response.text}")
        
        instance_data = response.json()
        
        # Extract the API endpoint
        api_endpoint = instance_data.get('apiEndpoint', '')
        if not api_endpoint:
            raise ValueError("API endpoint not found in Data Fusion instance response")
            
        # Remove https:// prefix if present
        if api_endpoint.startswith('https://'):
            api_endpoint = api_endpoint[8:]
            
        logger.info(f"Data Fusion API endpoint: {api_endpoint}")
        return api_endpoint
        
    except Exception as e:
        logger.error(f"Error getting Data Fusion API endpoint: {e}")
        raise ValueError(f"Failed to get Data Fusion API endpoint: {e}")

def create_compute_profile(project_id, location, instance_name, namespace, profile_name, profile_config, access_token):
    """Create or update the compute profile in Data Fusion using REST API."""
    try:
        # Get the API endpoint
        api_endpoint = get_datafusion_api_endpoint(project_id, location, instance_name, access_token)
        
        # Set up the API request
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # API endpoint URL (Using the CDAP API format)
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
            # Using PUT to create or update the profile
            response = requests.put(url, headers=headers, data=json_payload, timeout=60)
            
            logger.debug(f"API response status code: {response.status_code}")
            
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
        project_id = args.project_id
        
        # Validate project ID
        if not project_id:
            raise ValueError("Project ID is required")
        
        # Get access token from environment (set by Harness)
        access_token = get_access_token()
        
        # Find Data Fusion instance
        logger.info("Finding Data Fusion instance")
        datafusion_instance = find_datafusion_instance(
            project_id, 
            access_token,
            args.datafusion_instance, 
            args.datafusion_location
        )
        
        # Load profile configurations
        profile_configs = find_profile_configs(
            args.config_dir,
            args.profile_name,
            args.profile_dir
        )
        
        logger.info(f"Found {len(profile_configs)} profile(s) to import")
        
        # Import each profile
        success_count = 0
        failure_count = 0
        
        for profile_name, profile_config in profile_configs.items():
            try:
                logger.info(f"Processing profile: {profile_name}")
                create_compute_profile(
                    project_id,
                    args.datafusion_location,
                    datafusion_instance,
                    args.namespace,
                    profile_name,
                    profile_config,
                    access_token
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to import profile {profile_name}: {str(e)}")
                failure_count += 1
        
        # Summary report
        logger.info(f"Import complete. Successfully imported {success_count} profile(s), {failure_count} failed.")
        
        # Return appropriate exit code
        if failure_count > 0:
            return 1
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
