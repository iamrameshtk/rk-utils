#!/usr/bin/env python3
"""
Script to deploy Cloud Data Fusion pipelines from GitHub repository.

This script imports pipelines stored as JSON files in environment-specific 
folders (env_dev, env_pre, env_prd) of a GitHub repository into a Cloud 
Data Fusion instance using a Harness service account with OIDC token.

This implementation uses curl commands for the actual API interactions to 
ensure compatibility and exact behavior matching manual curl commands.
"""

import os
import sys
import json
import argparse
import logging
import time
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFusionPipelineDeployer:
    """Class to handle deployment of pipelines from GitHub to Cloud Data Fusion using curl."""
    
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
            timeout: Command timeout in seconds
        """
        self.project_id = project_id
        self.location = location
        self.instance_name = instance_name
        self.repo_path = repo_path
        self.env_folder = env_folder
        self.namespace = namespace
        self.debug = debug
        self.timeout = timeout
        self.curl_timeout = timeout
        
        # Set debug logging if requested
        if self.debug:
            logger.setLevel(logging.DEBUG)
            for handler in logger.handlers:
                handler.setLevel(logging.DEBUG)
        
        # Get the OIDC token which is already available in the pipeline
        self.token = os.environ.get("OIDC_TOKEN")
        if not self.token:
            raise ValueError("OIDC token not available in environment variable OIDC_TOKEN")
        
        # Verify curl is available
        self._verify_curl()
        
        # Get Data Fusion API endpoint
        self.api_endpoint = self._get_data_fusion_endpoint()
        logger.info(f"Connected to Data Fusion API endpoint: {self.api_endpoint}")
        
        # Validate connection to the Data Fusion instance
        self._validate_connection()
    
    def _verify_curl(self) -> None:
        """Verify that curl is available on the system."""
        try:
            subprocess.run(["curl", "--version"], check=True, capture_output=True)
            logger.info("curl is available on the system")
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("curl is not available on the system")
            raise RuntimeError("curl command is required for this script but was not found")
    
    def _run_curl_command(self, curl_args: List[str], input_data: Any = None) -> Tuple[int, str]:
        """
        Run a curl command and return the result.
        
        Args:
            curl_args: Arguments to pass to curl
            input_data: Optional JSON data to send
            
        Returns:
            Tuple of (exit_code, output)
        """
        command = ["curl", "--silent", "--fail-with-body"]
        
        # Add timeout
        command.extend(["--max-time", str(self.curl_timeout)])
        
        # Add debug flag if requested
        if self.debug:
            command.append("--verbose")
        
        # Add the rest of the arguments
        command.extend(curl_args)
        
        # For debugging
        if self.debug:
            logger.debug(f"Running curl command: {' '.join(command)}")
            if input_data:
                logger.debug(f"Input data: {json.dumps(input_data)[:200]}...")
        
        # Create a temporary file for input data if needed
        input_file = None
        if input_data is not None:
            input_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
            json.dump(input_data, input_file)
            input_file.close()
            command.extend(["--data", f"@{input_file.name}"])
        
        try:
            # Run the command
            result = subprocess.run(
                command,
                check=False,  # Don't raise an exception on non-zero exit
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # For debugging
            if self.debug:
                logger.debug(f"curl exit code: {result.returncode}")
                logger.debug(f"curl stdout: {result.stdout[:500]}..." if result.stdout else "Empty stdout")
                logger.debug(f"curl stderr: {result.stderr[:500]}..." if result.stderr else "Empty stderr")
                
            return result.returncode, result.stdout or result.stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"curl command timed out after {self.timeout} seconds")
            return 124, "Command timed out"
        except Exception as e:
            logger.error(f"Error running curl command: {str(e)}")
            return 1, str(e)
        finally:
            # Clean up the temporary file if it was created
            if input_file and os.path.exists(input_file.name):
                os.unlink(input_file.name)
    
    def _get_data_fusion_endpoint(self) -> str:
        """
        Get the API endpoint for the Data Fusion instance.
        
        Returns:
            Data Fusion API endpoint URL
        """
        curl_args = [
            "-X", "GET",
            "-H", f"Authorization: Bearer {self.token}",
            f"https://datafusion.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/instances/{self.instance_name}"
        ]
        
        exit_code, output = self._run_curl_command(curl_args)
        
        if exit_code != 0:
            raise RuntimeError(f"Failed to get Data Fusion instance details: {output}")
        
        try:
            instance_details = json.loads(output)
            api_endpoint = instance_details.get("apiEndpoint")
            
            if not api_endpoint:
                raise ValueError("Could not find API endpoint in Data Fusion instance details")
            
            return api_endpoint
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response from Data Fusion API: {output}")
            raise
    
    def _validate_connection(self) -> None:
        """
        Validate that we can connect to the Data Fusion instance.
        Raises an exception if connection fails.
        """
        curl_args = [
            "-X", "GET",
            "-H", f"Authorization: Bearer {self.token}",
            f"{self.api_endpoint}/v3/namespaces"
        ]
        
        exit_code, output = self._run_curl_command(curl_args)
        
        if exit_code != 0:
            raise RuntimeError(f"Failed to validate connection to Data Fusion: {output}")
        
        logger.info("Successfully validated connection to Data Fusion instance")
        
        # Check if the namespace exists
        ns_curl_args = [
            "-X", "GET",
            "-H", f"Authorization: Bearer {self.token}",
            f"{self.api_endpoint}/v3/namespaces/{self.namespace}"
        ]
        
        ns_exit_code, ns_output = self._run_curl_command(ns_curl_args)
        
        if ns_exit_code != 0:
            logger.warning(f"Namespace '{self.namespace}' may not exist. Attempting to create it...")
            
            create_ns_curl_args = [
                "-X", "PUT",
                "-H", f"Authorization: Bearer {self.token}",
                f"{self.api_endpoint}/v3/namespaces/{self.namespace}"
            ]
            
            create_exit_code, create_output = self._run_curl_command(create_ns_curl_args)
            
            if create_exit_code != 0:
                logger.warning(f"Failed to create namespace '{self.namespace}': {create_output}")
            else:
                logger.info(f"Successfully created namespace '{self.namespace}'")
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
        curl_args = [
            "-X", "GET",
            "-H", f"Authorization: Bearer {self.token}",
            f"{self.api_endpoint}/v3/namespaces/{self.namespace}/apps/{pipeline_name}"
        ]
        
        exit_code, _ = self._run_curl_command(curl_args)
        return exit_code == 0
    
    def import_pipeline_to_data_fusion(self, pipeline_name: str, pipeline_json: Dict[str, Any]) -> bool:
        """
        Import a pipeline to Data Fusion using curl.
        
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
        
        # Build the curl command for import
        if pipeline_exists:
            # Update existing pipeline
            curl_args = [
                "-X", "PUT",
                "-H", f"Authorization: Bearer {self.token}",
                "-H", "Content-Type: application/json",
                f"{self.api_endpoint}/v3/namespaces/{self.namespace}/apps/{pipeline_name}"
            ]
        else:
            # Create new pipeline
            curl_args = [
                "-X", "POST",
                "-H", f"Authorization: Bearer {self.token}",
                "-H", "Content-Type: application/json",
                f"{self.api_endpoint}/v3/namespaces/{self.namespace}/apps"
            ]
        
        # Run the curl command
        exit_code, output = self._run_curl_command(curl_args, pipeline_json)
        
        if exit_code == 0:
            logger.info(f"Successfully {operation.lower()}d pipeline: {pipeline_name}")
            return True
        else:
            logger.error(f"Failed to {operation.lower()} pipeline {pipeline_name}: {output}")
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
    parser.add_argument('--timeout', type=int, default=60, help='Command timeout in seconds (default: 60)')
    
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
