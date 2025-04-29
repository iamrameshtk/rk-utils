"""
Airflow DAG to create a Dataproc Compute Profile configuration in an existing Data Fusion instance.
This DAG configures the compute profile at the namespace level without actually creating a Dataproc cluster.
Includes enhanced error handling and comprehensive logging.
"""

import json
import requests
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.google.cloud.hooks.datafusion import DataFusionHook
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.exceptions import AirflowException

# Set up logger
logger = logging.getLogger(__name__)

# Define custom exceptions for clearer error handling
class DataFusionProfileException(AirflowException):
    """Exception raised for errors in the Data Fusion Profile operations."""
    pass

class DataFusionAPIException(AirflowException):
    """Exception raised for errors in the Data Fusion API calls."""
    pass

class DataFusionAuthException(AirflowException):
    """Exception raised for authentication errors with Data Fusion."""
    pass

# Define default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
    'start_date': datetime(2025, 4, 29),
}

# Environment configuration - adjust these variables as needed
PROJECT_ID = Variable.get('project_id', 'your-gcp-project-id')
REGION = Variable.get('region', 'us-central1')
ZONE = Variable.get('zone', 'us-central1-a')
DATAFUSION_INSTANCE = Variable.get('datafusion_instance', 'datafusion-instance')
DATAFUSION_LOCATION = Variable.get('datafusion_location', 'us-central1')
DATAFUSION_NAMESPACE = Variable.get('datafusion_namespace', 'default')
COMPUTE_PROFILE_NAME = Variable.get('compute_profile_name', 'dataproc-ephemeral-profile')
SUBNET = Variable.get('subnet', 'default')
SERVICE_ACCOUNT = Variable.get('service_account', 'default')

# Dataproc cluster configuration parameters
DATAPROC_CONFIG = {
    'masterNumNodes': Variable.get('master_num_nodes', '1'),
    'masterMachineType': Variable.get('master_machine_type', 'n1-standard-4'),
    'masterDiskType': Variable.get('master_disk_type', 'pd-standard'),
    'masterDiskSize': Variable.get('master_disk_size', '500'),
    'workerNumNodes': Variable.get('worker_num_nodes', '2'),
    'workerMachineType': Variable.get('worker_machine_type', 'n1-standard-4'),
    'workerDiskType': Variable.get('worker_disk_type', 'pd-standard'),
    'workerDiskSize': Variable.get('worker_disk_size', '500'),
    'imageVersion': Variable.get('image_version', '2.0-debian10'),
    'network': Variable.get('network', 'default'),
    'subnet': SUBNET,
    'serviceAccount': SERVICE_ACCOUNT,
    'idleTTL': Variable.get('idle_ttl', '3600'),  # Seconds before auto-deletion when idle
    'enableStackdriverLogging': Variable.get('enable_stackdriver_logging', 'true'),
    'enableStackdriverMonitoring': Variable.get('enable_stackdriver_monitoring', 'true'),
    'initActions': Variable.get('init_actions', ''),
}

# Create the DAG
with DAG(
    'datafusion_dataproc_compute_profile',
    default_args=default_args,
    description='Create a Dataproc Compute Profile configuration in Data Fusion',
    schedule_interval=None,  # Run manually
    catchup=False,
    tags=['datafusion', 'dataproc', 'profile'],
) as dag:

    def get_datafusion_api_info():
        """
        Helper function to get Data Fusion API info and credentials
        Returns a tuple of (api_client, api_endpoint, token)
        """
        logger.info(f"Initializing Data Fusion connection for instance: {DATAFUSION_INSTANCE}")
        
        try:
            # Get the Data Fusion Hook
            datafusion_hook = DataFusionHook(
                gcp_conn_id='google_cloud_default',
            )
            
            # Construct API client
            api_client = datafusion_hook.get_conn()
            
            # Get location-specific URI path for Data Fusion instance
            parent = f"projects/{PROJECT_ID}/locations/{DATAFUSION_LOCATION}/instances/{DATAFUSION_INSTANCE}"
            logger.info(f"Fetching Data Fusion instance details from: {parent}")
            
            # Make REST API call to get the Data Fusion instance info
            try:
                instance = api_client.projects().locations().instances().get(
                    name=parent
                ).execute()
            except Exception as e:
                logger.error(f"Failed to get Data Fusion instance: {str(e)}")
                raise DataFusionAPIException(f"Error retrieving Data Fusion instance: {str(e)}")
            
            # Extract the API endpoint from the instance info
            api_endpoint = instance.get('apiEndpoint')
            if not api_endpoint:
                raise DataFusionAPIException("API endpoint not found in Data Fusion instance response")
                
            # Remove https:// prefix if present
            if api_endpoint.startswith('https://'):
                api_endpoint = api_endpoint[8:]
            
            logger.info(f"Successfully retrieved API endpoint: {api_endpoint}")
            
            # Get auth token from the hook
            try:
                credentials = datafusion_hook._get_credentials()
                token = credentials.token
                if not token:
                    raise DataFusionAuthException("Authentication token is empty")
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                raise DataFusionAuthException(f"Failed to get authentication token: {str(e)}")
            
            logger.info("Successfully obtained authentication credentials")
            return api_client, api_endpoint, token
            
        except Exception as e:
            logger.error(f"Unexpected error getting Data Fusion API info: {str(e)}")
            raise
    
    def create_datafusion_compute_profile(**kwargs):
        """
        Create a compute profile in Data Fusion using the DataFusion REST API
        """
        logger.info(f"Starting creation of compute profile: {COMPUTE_PROFILE_NAME}")
        logger.info(f"Project: {PROJECT_ID}, Region: {REGION}, Zone: {ZONE}")
        
        try:
            # Get API info
            api_client, api_endpoint, token = get_datafusion_api_info()
            
            # Build the compute profile configuration
            logger.info("Building compute profile configuration")
            profile_config = {
                'name': COMPUTE_PROFILE_NAME,
                'label': 'Ephemeral Dataproc Cluster Profile',
                'provisioner': {
                    'name': 'gcp-dataproc',
                    'properties': [
                        {'name': 'projectId', 'value': PROJECT_ID},
                        {'name': 'region', 'value': REGION},
                        {'name': 'zone', 'value': ZONE},
                        {'name': 'network', 'value': DATAPROC_CONFIG['network']},
                        {'name': 'subnet', 'value': DATAPROC_CONFIG['subnet']},
                        {'name': 'serviceAccount', 'value': DATAPROC_CONFIG['serviceAccount']},
                        {'name': 'masterNumNodes', 'value': DATAPROC_CONFIG['masterNumNodes']},
                        {'name': 'masterMachineType', 'value': DATAPROC_CONFIG['masterMachineType']},
                        {'name': 'masterDiskType', 'value': DATAPROC_CONFIG['masterDiskType']},
                        {'name': 'masterDiskSize', 'value': DATAPROC_CONFIG['masterDiskSize']},
                        {'name': 'workerNumNodes', 'value': DATAPROC_CONFIG['workerNumNodes']},
                        {'name': 'workerMachineType', 'value': DATAPROC_CONFIG['workerMachineType']},
                        {'name': 'workerDiskType', 'value': DATAPROC_CONFIG['workerDiskType']},
                        {'name': 'workerDiskSize', 'value': DATAPROC_CONFIG['workerDiskSize']},
                        {'name': 'imageVersion', 'value': DATAPROC_CONFIG['imageVersion']},
                        {'name': 'initActions', 'value': DATAPROC_CONFIG['initActions']},
                        {'name': 'idleTTL', 'value': DATAPROC_CONFIG['idleTTL']},
                        {'name': 'enableStackdriverLogging', 'value': DATAPROC_CONFIG['enableStackdriverLogging']},
                        {'name': 'enableStackdriverMonitoring', 'value': DATAPROC_CONFIG['enableStackdriverMonitoring']},
                        {'name': 'securityGroup', 'value': ''},
                        {'name': 'coreAutoscaling', 'value': 'false'},
                        {'name': 'encrypted', 'value': 'false'},
                        {'name': 'encryptionKeyName', 'value': ''},
                    ]
                }
            }
            
            # Log configuration details (excluding sensitive information)
            logger.info(f"Compute profile configuration prepared for {COMPUTE_PROFILE_NAME}")
            logger.info(f"Master nodes: {DATAPROC_CONFIG['masterNumNodes']}, Worker nodes: {DATAPROC_CONFIG['workerNumNodes']}")
            logger.info(f"Master type: {DATAPROC_CONFIG['masterMachineType']}, Worker type: {DATAPROC_CONFIG['workerMachineType']}")
            logger.info(f"Dataproc image version: {DATAPROC_CONFIG['imageVersion']}")
            logger.info(f"Idle TTL: {DATAPROC_CONFIG['idleTTL']} seconds")
            
            # Set up headers for API request
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Data Fusion API endpoint for creating a compute profile in the specified namespace
            url = f"https://{api_endpoint}/v3/namespaces/{DATAFUSION_NAMESPACE}/profiles/{COMPUTE_PROFILE_NAME}"
            logger.info(f"Making API request to: {url}")
            
            # Make the API call to create the compute profile
            try:
                response = requests.put(url, headers=headers, data=json.dumps(profile_config), timeout=60)
                
                # Log response status and content if not successful
                if response.status_code not in (200, 201):
                    logger.error(f"API call failed with status code: {response.status_code}")
                    logger.error(f"Response content: {response.text}")
                    raise DataFusionProfileException(
                        f"Failed to create compute profile. Status: {response.status_code}, Error: {response.text}"
                    )
                    
                logger.info(f"Successfully created compute profile: {COMPUTE_PROFILE_NAME}")
                # Log success response (limited to avoid excessive logs)
                response_data = response.json()
                logger.info(f"Profile created with name: {response_data.get('name', 'Unknown')}")
                
                return response_data
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {str(e)}")
                raise DataFusionAPIException(f"API request failed: {str(e)}")
                
        except (DataFusionProfileException, DataFusionAPIException, DataFusionAuthException) as e:
            # Re-raise known exceptions
            raise e
        except Exception as e:
            # Handle unexpected exceptions
            logger.error(f"Unexpected error creating compute profile: {str(e)}")
            raise DataFusionProfileException(f"Unexpected error creating compute profile: {str(e)}")
    
    # Task to create the compute profile in Data Fusion
    create_compute_profile = PythonOperator(
        task_id='create_compute_profile',
        python_callable=create_datafusion_compute_profile,
    )
    
    # Task to verify the compute profile was created
    def verify_compute_profile(**kwargs):
        """
        Verify that the compute profile was created successfully
        """
        logger.info(f"Verifying compute profile: {COMPUTE_PROFILE_NAME}")
        
        try:
            # Get API info
            api_client, api_endpoint, token = get_datafusion_api_info()
            
            # Set up headers for API request
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Data Fusion API endpoint to get the compute profile
            url = f"https://{api_endpoint}/v3/namespaces/{DATAFUSION_NAMESPACE}/profiles"
            logger.info(f"Making API request to get all profiles: {url}")
            
            # Make the API call to get all profiles
            try:
                response = requests.get(url, headers=headers, timeout=60)
                
                # Check response and handle errors
                if response.status_code != 200:
                    logger.error(f"API call failed with status code: {response.status_code}")
                    logger.error(f"Response content: {response.text}")
                    raise DataFusionAPIException(
                        f"Failed to get compute profiles. Status: {response.status_code}, Error: {response.text}"
                    )
                
                # Check if our profile is in the list
                profiles = response.json()
                logger.info(f"Found {len(profiles)} compute profiles in namespace {DATAFUSION_NAMESPACE}")
                
                profile_found = False
                for profile in profiles:
                    if profile.get('name') == COMPUTE_PROFILE_NAME:
                        profile_found = True
                        logger.info(f"Profile verified: {COMPUTE_PROFILE_NAME}")
                        logger.info(f"Profile label: {profile.get('label', 'No label')}")
                        logger.info(f"Provisioner: {profile.get('provisioner', {}).get('name', 'Unknown')}")
                        break
                        
                if profile_found:
                    logger.info(f"Successfully verified compute profile: {COMPUTE_PROFILE_NAME}")
                    return True
                else:
                    logger.error(f"Compute profile {COMPUTE_PROFILE_NAME} was not found")
                    raise DataFusionProfileException(f"Compute profile {COMPUTE_PROFILE_NAME} was not found in the list of profiles")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error during verification: {str(e)}")
                raise DataFusionAPIException(f"API request failed during verification: {str(e)}")
                
        except (DataFusionProfileException, DataFusionAPIException, DataFusionAuthException) as e:
            # Re-raise known exceptions
            raise e
        except Exception as e:
            # Handle unexpected exceptions
            logger.error(f"Unexpected error verifying compute profile: {str(e)}")
            raise DataFusionProfileException(f"Unexpected error verifying compute profile: {str(e)}")
    
    # Task for profile verification
    verify_profile = PythonOperator(
        task_id='verify_compute_profile',
        python_callable=verify_compute_profile,
    )

    # Task to check if profile already exists before creating
    def check_profile_exists(**kwargs):
        """
        Check if the compute profile already exists to determine if we should create or update
        """
        logger.info(f"Checking if compute profile already exists: {COMPUTE_PROFILE_NAME}")
        
        try:
            # Get API info
            api_client, api_endpoint, token = get_datafusion_api_info()
            
            # Set up headers for API request
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Data Fusion API endpoint to get the specific compute profile
            url = f"https://{api_endpoint}/v3/namespaces/{DATAFUSION_NAMESPACE}/profiles/{COMPUTE_PROFILE_NAME}"
            logger.info(f"Making API request to check profile: {url}")
            
            # Make the API call to check if the profile exists
            try:
                response = requests.get(url, headers=headers, timeout=60)
                
                # If status is 200, profile exists
                if response.status_code == 200:
                    logger.info(f"Compute profile {COMPUTE_PROFILE_NAME} already exists")
                    return True
                # If status is 404, profile doesn't exist
                elif response.status_code == 404:
                    logger.info(f"Compute profile {COMPUTE_PROFILE_NAME} does not exist yet")
                    return False
                # Any other status is an error
                else:
                    logger.error(f"API call failed with status code: {response.status_code}")
                    logger.error(f"Response content: {response.text}")
                    raise DataFusionAPIException(
                        f"Failed to check compute profile. Status: {response.status_code}, Error: {response.text}"
                    )
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error checking profile existence: {str(e)}")
                raise DataFusionAPIException(f"API request failed when checking profile: {str(e)}")
                
        except (DataFusionProfileException, DataFusionAPIException, DataFusionAuthException) as e:
            # Re-raise known exceptions
            raise e
        except Exception as e:
            # Handle unexpected exceptions
            logger.error(f"Unexpected error checking profile existence: {str(e)}")
            raise DataFusionProfileException(f"Unexpected error checking profile: {str(e)}")
    
    # Task for checking if profile exists
    check_profile = PythonOperator(
        task_id='check_profile_exists',
        python_callable=check_profile_exists,
    )
    
    # Set task dependencies to run in sequence
    check_profile >> create_compute_profile >> verify_profile
