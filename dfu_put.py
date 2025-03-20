#!/usr/bin/env python3
"""
Script to deploy Cloud Data Fusion pipelines from GitHub repository.

This script imports pipelines stored as JSON files in environment-specific 
folders (env_dev, env_pre, env_prd) of a GitHub repository into a Cloud 
Data Fusion instance using a Harness service account with OIDC token.

This version always uses PUT requests for importing pipelines, which has been 
found to be more reliable than POST requests for Data Fusion.
"""

import os
import sys
import json
import argparse
import requests
import logging
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFusionPipelineDeployer:
    """Class to handle deployment of pipelines from GitHub to Cloud Data Fusion."""
    
    def __init__(self, 
                 project_id: str, 
                 location: str, 
                 instance_name: str,
                 repo_path: str,
                 env_folder: str,
                 namespace: str = "default",
                 debug: bool = False,
                 timeout: int = 60,
                 retries: int = 3):
        """
        Initialize the deployer with configuration.
        
        Args:
            project_id: GCP project ID
            location: GCP region where Data Fusion instance is located
            instance_name: Name of the Data Fusion instance
            repo_path: Path to the local repository clone
            env_folder: Environment folder to use (env_dev, env_pre, env_prd)
            namespace: Data Fusion namespace (default: "default")
            debug: Enable debug mode for verbose logging
            timeout: Request timeout in seconds
            retries: Number of retries for failed requests
        """
        self.project_id = project_id
        self.location = location
        self.instance_name = instance_name
        self.repo_path = repo_path
        self.env_folder = env_folder
        self.namespace = namespace
        self.debug = debug
        self.timeout = timeout
        self.retries = retries
        
        # Set debug logging if requested
        if self.debug:
            logger.setLevel(logging.DEBUG)
            for handler in logger.handlers:
                handler.setLevel(logging.DEBUG)
        
        # Get the OIDC token which is already available in the pipeline
        self.token = os.environ.get("OIDC_TOKEN")
        if not self.token:
            raise ValueError("OIDC token not available in environment variable OIDC_TOKEN")
        
        # Basic headers that will be used for all requests
        self.base_headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Get Data Fusion API endpoint
        self.api_endpoint = self._get_data_fusion_endpoint()
        logger.info(f"Connected to Data Fusion API endpoint: {self.api_endpoint}")
        
        # Validate connection to the Data Fusion instance
        self._validate_connection()
    
    def _make_request(self, method: str, url: str, headers: Dict[str, str] = None, 
                     json_data: Any = None, retry_count: int = 0) -> Tuple[int, Any]:
        """
        Make an HTTP request with retry logic and proper error handling.
        
        Args:
            method: HTTP method (GET, PUT, POST, DELETE)
            url: Request URL
            headers: Request headers (will be combined with base_headers)
            json_data: JSON data to send
            retry_count: Current retry attempt
            
        Returns:
            Tuple of (status_code, response_data)
        """
        # Combine headers with base headers
        all_headers = self.base_headers.copy()
        if headers:
            all_headers.update(headers)
            
        # Log request details in debug mode
        if self.debug:
            logger.debug(f"Making {method} request to {url}")
            logger.debug(f"Headers: {all_headers}")
            if json_data:
                logger.debug(f"Request data: {json.dumps(json_data)[:500]}..." if json_data else "No data")
                
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=all_headers,
                json=json_data,
                timeout=self.timeout
            )
            
            # Log response details in debug mode
            if self.debug:
                logger.debug(f"Response status code: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                content_preview = response.text[:500] + "..." if len(response.text) > 500 else response.text
                logger.debug(f"Response content: {content_preview}" if response.text else "Empty response")
            
            # Parse response JSON if available
            response_data = None
            if response.text:
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    response_data = response.text
            
            return response.status_code, response_data
            
        except requests.exceptions.Timeout:
            logger.warning(f"Request timed out after {self.timeout} seconds")
            if retry_count < self.retries:
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds... (attempt {retry_count + 1}/{self.retries})")
                time.sleep(wait_time)
                return self._make_request(method, url, headers, json_data, retry_count + 1)
            else:
                logger.error("Maximum retry attempts reached. Giving up.")
                return 408, "Request timed out after multiple retries"
                
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                try:
                    error_data = e.response.json()
                    error_msg = f"Status {status_code}: {json.dumps(error_data)}"
                except (json.JSONDecodeError, ValueError):
                    error_msg = f"Status {status_code}: {e.response.text}"
            
            logger.error(f"Request error: {error_msg}")
            
            if retry_count < self.retries:
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds... (attempt {retry_count + 1}/{self.retries})")
                time.sleep(wait_time)
                return self._make_request(method, url, headers, json_data, retry_count + 1)
            else:
                logger.error("Maximum retry attempts reached. Giving up.")
                return 500, error_msg
    
    def _get_data_fusion_endpoint(self) -> str:
        """
        Get the API endpoint for the Data Fusion instance.
        
        Returns:
            Data Fusion API endpoint URL
        """
        url = f"https://datafusion.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/instances/{self.instance_name}"
        
        status_code, response_data = self._make_request("GET", url)
        
        if status_code != 200:
            error_msg = f"Failed to get Data Fusion instance details: {response_data}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        api_endpoint = response_data.get("apiEndpoint")
        if not api_endpoint:
            raise ValueError("Could not find API endpoint in Data Fusion instance details")
        
        return api_endpoint
    
    def _validate_connection(self) -> None:
        """
        Validate that we can connect to the Data Fusion instance.
        Raises an exception if connection fails.
        """
        # Check connection to Data Fusion
        url = f"{self.api_endpoint}/v3/namespaces"
        status_code, response_data = self._make_request("GET", url)
        
        if status_code != 200:
            error_msg = f"Failed to validate connection to Data Fusion: {response_data}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info("Successfully validated connection to Data Fusion instance")
        
        # Check if the namespace exists
        ns_url = f"{self.api_endpoint}/v3/namespaces/{self.namespace}"
        ns_status_code, ns_response = self._make_request("GET", ns_url)
        
        if ns_status_code == 404:
            logger.warning(f"Namespace '{self.namespace}' does not exist. Attempting to create it...")
            
            create_status_code, create_response = self._make_request("PUT", ns_url)
            
            if create_status_code < 200 or create_status_code >= 300:
                logger.warning(f"Failed to create namespace '{self.namespace}': {create_response}")
            else:
                logger.info(f"Successfully created namespace '{self.namespace}'")
        elif ns_status_code != 200:
            logger.warning(f"Unexpected status when checking namespace: {ns_status_code} - {ns_response}")
        else:
            logger.info(f"Namespace '{self.namespace}' exists")
    
    def get_pipelines_from_repo(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve pipeline JSON files from the specified environment folder.
        
        Returns:
            Dictionary mapping pipeline names to their JSON content
        """
        logger.info(f"Retrieving pipelines from environment folder: {self.env_folder}")
        
        env_folder_path = Path(self.repo_path) / self.env_folder
        
        if not env_folder_path.exists():
            error_msg = f"Environment folder '{self.env_folder}' not found in repository"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        pipelines = {}
        for json_file in env_folder_path.glob("*.json"):
            logger.info(f"Found pipeline file: {json_file.name}")
            pipeline_name = json_file.stem
            
            try:
                with open(json_file, 'r') as f:
                    pipeline_content = json.load(f)
                
                pipelines[pipeline_name] = pipeline_content
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from {json_file}: {str(e)}")
                continue
        
        if not pipelines:
            logger.warning(f"No pipeline JSON files found in {env_folder_path}")
        else:
            logger.info(f"Retrieved {len(pipelines)} pipelines from repository")
            
        return pipelines
    
    def check_pipeline_exists(self, pipeline_name: str) -> bool:
        """
        Check if a pipeline already exists in Data Fusion.
        
        Args:
            pipeline_name: Name of the pipeline to check
            
        Returns:
            True if the pipeline exists, False otherwise
        """
        url = f"{self.api_endpoint}/v3/namespaces/{self.namespace}/apps/{pipeline_name}"
        status_code, _ = self._make_request("GET", url)
        return status_code == 200
    
    def import_pipeline_to_data_fusion(self, pipeline_name: str, pipeline_json: Dict[str, Any]) -> bool:
        """
        Import a pipeline to Data Fusion using PUT request.
        
        Args:
            pipeline_name: Name of the pipeline
            pipeline_json: Pipeline configuration as JSON
            
        Returns:
            True if import was successful, False otherwise
        """
        logger.info(f"Importing pipeline: {pipeline_name}")
        
        # Check if pipeline exists (for logging purposes only)
        pipeline_exists = self.check_pipeline_exists(pipeline_name)
        operation = "Updating" if pipeline_exists else "Creating"
        logger.info(f"{operation} pipeline: {pipeline_name}")
        
        # Always use PUT request with the pipeline name in the URL
        # This works for both creating and updating pipelines in Data Fusion
        url = f"{self.api_endpoint}/v3/namespaces/{self.namespace}/apps/{pipeline_name}"
        
        try:
            status_code, response_data = self._make_request("PUT", url, json_data=pipeline_json)
            
            if 200 <= status_code < 300:
                logger.info(f"Successfully {operation.lower()}d pipeline: {pipeline_name}")
                return True
            else:
                logger.error(f"Failed to {operation.lower()} pipeline {pipeline_name}. Status: {status_code}, Response: {response_data}")
                return False
        except Exception as e:
            # Log the full exception traceback in debug mode
            if self.debug:
                logger.debug(f"Exception traceback: {traceback.format_exc()}")
            
            logger.error(f"Unexpected error {operation.lower()}ing pipeline {pipeline_name}: {str(e)}")
            return False
    
    def deploy_pipelines(self, pipeline_names: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Deploy pipelines from the repository to Data Fusion.
        
        Args:
            pipeline_names: Optional list of specific pipeline names to deploy.
                           If None, all pipelines in the environment folder will be deployed.
        
        Returns:
            Dictionary mapping pipeline names to deployment status (True for success, False for failure)
        """
        all_pipelines = self.get_pipelines_from_repo()
        
        if not all_pipelines:
            logger.warning("No pipelines found to deploy")
            return {}
        
        # Filter pipelines if specific names are provided
        if pipeline_names:
            logger.info(f"Filtering to deploy only specific pipelines: {', '.join(pipeline_names)}")
            pipelines_to_deploy = {name: all_pipelines[name] for name in pipeline_names if name in all_pipelines}
            
            # Check for missing pipelines
            missing_pipelines = [name for name in pipeline_names if name not in all_pipelines]
            if missing_pipelines:
                logger.warning(f"The following requested pipelines were not found: {', '.join(missing_pipelines)}")
        else:
            pipelines_to_deploy = all_pipelines
        
        if not pipelines_to_deploy:
            logger.warning("No pipelines to deploy after filtering")
            return {}
        
        logger.info(f"Deploying {len(pipelines_to_deploy)} pipelines to Data Fusion")
        
        # Record start time for overall deployment
        start_time = time.time()
        
        results = {}
        for i, (pipeline_name, pipeline_json) in enumerate(pipelines_to_deploy.items(), 1):
            logger.info(f"Processing pipeline {i}/{len(pipelines_to_deploy)}: {pipeline_name}")
            
            # Record start time for this pipeline
            pipeline_start_time = time.time()
            
            try:
                results[pipeline_name] = self.import_pipeline_to_data_fusion(pipeline_name, pipeline_json)
                
                # Calculate and log elapsed time
                elapsed = time.time() - pipeline_start_time
                logger.info(f"Pipeline {pipeline_name} processed in {elapsed:.2f} seconds")
                
                # Add a small delay between deployments to avoid rate limiting
                if i < len(pipelines_to_deploy):
                    time.sleep(1)
            except Exception as e:
                # Log the full exception traceback in debug mode
                if self.debug:
                    logger.debug(f"Exception traceback: {traceback.format_exc()}")
                    
                logger.error(f"Unexpected error deploying pipeline {pipeline_name}: {str(e)}")
                results[pipeline_name] = False
        
        # Calculate and log total elapsed time
        total_elapsed = time.time() - start_time
        logger.info(f"Total deployment time: {total_elapsed:.2f} seconds")
        
        return results

def main():
    """Main function to parse arguments and execute the script."""
    parser = argparse.ArgumentParser(description='Deploy Cloud Data Fusion pipelines from GitHub')
    
    parser.add_argument('--project-id', required=True, help='GCP project ID')
    parser.add_argument('--location', required=True, help='GCP region where Data Fusion instance is located')
    parser.add_argument('--instance-name', required=True, help='Name of the Data Fusion instance')
    parser.add_argument('--repo-path', 
                       default=os.environ.get('HARNESS_WORKSPACE_DIR', '.'),
                       help='Path to the local GitHub repository clone (defaults to Harness workspace)')
    parser.add_argument('--env-folder', required=True, 
                        choices=['env_dev', 'env_pre', 'env_prd'], 
                        help='Environment folder to use')
    parser.add_argument('--namespace', default='default', help='Data Fusion namespace (default: "default")')
    parser.add_argument('--pipelines', nargs='+', help='Optional: Specific pipeline names to deploy (deploy all if not specified)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging for detailed output')
    parser.add_argument('--timeout', type=int, default=60, help='Request timeout in seconds (default: 60)')
    parser.add_argument('--retries', type=int, default=3, help='Number of retries for failed requests (default: 3)')
    
    args = parser.parse_args()
    
    try:
        # Record script start time
        script_start_time = time.time()
        
        logger.info(f"Starting Data Fusion pipeline deployment script")
        logger.info(f"Project: {args.project_id}, Location: {args.location}, Instance: {args.instance_name}")
        logger.info(f"Environment folder: {args.env_folder}, Namespace: {args.namespace}")
        
        deployer = DataFusionPipelineDeployer(
            project_id=args.project_id,
            location=args.location,
            instance_name=args.instance_name,
            repo_path=args.repo_path,
            env_folder=args.env_folder,
            namespace=args.namespace,
            debug=args.debug,
            timeout=args.timeout,
            retries=args.retries
        )
        
        results = deployer.deploy_pipelines(args.pipelines)
        
        if not results:
            logger.warning("No pipelines were deployed")
            sys.exit(0)
        
        # Print summary
        success_count = sum(1 for status in results.values() if status)
        failure_count = sum(1 for status in results.values() if not status)
        
        logger.info(f"Deployment summary: {success_count} succeeded, {failure_count} failed")
        
        if success_count > 0:
            logger.info("Successfully deployed pipelines:")
            for pipeline_name, status in results.items():
                if status:
                    logger.info(f"- {pipeline_name}")
        
        if failure_count > 0:
            logger.error("Failed pipeline deployments:")
            for pipeline_name, status in results.items():
                if not status:
                    logger.error(f"- {pipeline_name}")
        
        # Log total script execution time
        total_script_time = time.time() - script_start_time
        logger.info(f"Total script execution time: {total_script_time:.2f} seconds")
            
        # Exit with non-zero code if any deployments failed
        if failure_count > 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        # Log the full exception traceback
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
