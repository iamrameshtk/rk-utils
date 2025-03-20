#!/usr/bin/env python3
"""
Script to deploy Cloud Data Fusion pipelines from GitHub repository.

This script imports pipelines stored as JSON files in environment-specific 
folders (env_dev, env_pre, env_prd) of a GitHub repository into a Cloud 
Data Fusion instance using a Harness service account with OIDC token.
"""

import os
import sys
import json
import argparse
import requests
import logging
import time
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
                 timeout: int = 60):
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
        """
        self.project_id = project_id
        self.location = location
        self.instance_name = instance_name
        self.repo_path = repo_path
        self.env_folder = env_folder
        self.namespace = namespace
        self.debug = debug
        self.timeout = timeout
        
        # Set debug logging if requested
        if self.debug:
            logger.setLevel(logging.DEBUG)
            for handler in logger.handlers:
                handler.setLevel(logging.DEBUG)
        
        # Get the OIDC token which is already available in the pipeline
        self.token = os.environ.get("OIDC_TOKEN")
        if not self.token:
            raise ValueError("OIDC token not available in environment variable OIDC_TOKEN")
        
        # Get Data Fusion API endpoint
        self.api_endpoint = self._get_data_fusion_endpoint()
        logger.info(f"Connected to Data Fusion API endpoint: {self.api_endpoint}")
        
        # Validate connection to the Data Fusion instance
        self._validate_connection()
    
    def _get_data_fusion_endpoint(self) -> str:
        """
        Get the API endpoint for the Data Fusion instance.
        
        Returns:
            Data Fusion API endpoint URL
        """
        url = f"https://datafusion.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/instances/{self.instance_name}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            instance_details = response.json()
            api_endpoint = instance_details.get("apiEndpoint")
            
            if not api_endpoint:
                raise ValueError("Could not find API endpoint in Data Fusion instance details")
            
            return api_endpoint
            
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Failed to get Data Fusion instance details: {e.response.text}")
            else:
                logger.error(f"Failed to get Data Fusion instance details: {str(e)}")
            raise
    
    def _validate_connection(self) -> None:
        """
        Validate that we can connect to the Data Fusion instance.
        Raises an exception if connection fails.
        """
        test_url = f"{self.api_endpoint}/v3/namespaces"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        try:
            response = requests.get(test_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            logger.info("Successfully validated connection to Data Fusion instance")
            
            if self.debug:
                namespaces = response.json()
                logger.debug(f"Available namespaces: {namespaces}")
                
            # Verify the specified namespace exists
            namespace_url = f"{self.api_endpoint}/v3/namespaces/{self.namespace}"
            ns_response = requests.get(namespace_url, headers=headers, timeout=self.timeout)
            
            if ns_response.status_code == 404:
                logger.warning(f"Namespace '{self.namespace}' does not exist. Creating it...")
                create_response = requests.put(namespace_url, headers=headers, timeout=self.timeout)
                create_response.raise_for_status()
                logger.info(f"Successfully created namespace '{self.namespace}'")
            elif ns_response.status_code != 200:
                logger.warning(f"Unexpected status when checking namespace: {ns_response.status_code}")
            else:
                logger.info(f"Namespace '{self.namespace}' exists")
                
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Failed to validate connection to Data Fusion: {e.response.text}")
            else:
                logger.error(f"Failed to validate connection to Data Fusion: {str(e)}")
            raise
    
    def get_pipelines_from_repo(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve pipeline JSON files from the specified environment folder.
        
        Returns:
            Dictionary mapping pipeline names to their JSON content
        """
        logger.info(f"Retrieving pipelines from environment folder: {self.env_folder}")
        
        env_folder_path = Path(self.repo_path) / self.env_folder
        
        if not env_folder_path.exists():
            raise Exception(f"Environment folder '{self.env_folder}' not found in repository")
        
        pipelines = {}
        for json_file in env_folder_path.glob("*.json"):
            logger.info(f"Found pipeline file: {json_file.name}")
            pipeline_name = json_file.stem
            
            try:
                with open(json_file, 'r') as f:
                    pipeline_content = json.load(f)
                
                pipelines[pipeline_name] = pipeline_content
                
            except json.JSONDecodeError:
                logger.error(f"Error parsing JSON from {json_file}")
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
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def import_pipeline_to_data_fusion(self, pipeline_name: str, pipeline_json: Dict[str, Any]) -> bool:
        """
        Import a pipeline to Data Fusion using the import API.
        
        Args:
            pipeline_name: Name of the pipeline
            pipeline_json: Pipeline configuration as JSON
            
        Returns:
            True if import was successful, False otherwise
        """
        logger.info(f"Importing pipeline: {pipeline_name}")
        
        # Check if we need to create or update
        pipeline_exists = self.check_pipeline_exists(pipeline_name)
        operation = "Updating" if pipeline_exists else "Creating"
        logger.info(f"{operation} pipeline: {pipeline_name}")
        
        # Set the endpoint URL based on whether the pipeline exists
        if pipeline_exists:
            url = f"{self.api_endpoint}/v3/namespaces/{self.namespace}/apps/{pipeline_name}"
            http_method = requests.put
        else:
            url = f"{self.api_endpoint}/v3/namespaces/{self.namespace}/apps"
            http_method = requests.post
        
        # Set up the headers
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # For debugging
        if self.debug:
            logger.debug(f"Request URL: {url}")
            logger.debug(f"Request method: {http_method.__name__}")
            logger.debug(f"Request headers: {headers}")
            logger.debug(f"Pipeline JSON excerpt: {str(pipeline_json)[:200]}...")
        
        try:
            # Send the request to import the pipeline
            response = http_method(url, headers=headers, json=pipeline_json, timeout=self.timeout)
            
            # For debugging
            if self.debug:
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                logger.debug(f"Response content: {response.text[:500]}..." if response.text else "Empty response")
            
            # Check if the request was successful
            if response.status_code in [200, 201, 202]:
                logger.info(f"Successfully {operation.lower()}d pipeline: {pipeline_name}")
                return True
            else:
                logger.error(f"Failed to {operation.lower()} pipeline {pipeline_name}. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                error_msg = f"{error_msg} - {e.response.text}"
            logger.error(f"Error {operation.lower()}ing pipeline {pipeline_name}: {error_msg}")
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
        
        results = {}
        for pipeline_name, pipeline_json in pipelines_to_deploy.items():
            try:
                results[pipeline_name] = self.import_pipeline_to_data_fusion(pipeline_name, pipeline_json)
                # Add a small delay between deployments to avoid rate limiting
                if len(pipelines_to_deploy) > 1:
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Unexpected error deploying pipeline {pipeline_name}: {str(e)}")
                results[pipeline_name] = False
        
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
    
    args = parser.parse_args()
    
    try:
        deployer = DataFusionPipelineDeployer(
            project_id=args.project_id,
            location=args.location,
            instance_name=args.instance_name,
            repo_path=args.repo_path,
            env_folder=args.env_folder,
            namespace=args.namespace,
            debug=args.debug,
            timeout=args.timeout
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
            
            # Exit with non-zero code if any deployments failed
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error in execution: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
