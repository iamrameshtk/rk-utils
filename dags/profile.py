"""
Airflow DAG to create a Dataproc Compute Profile configuration in an existing Data Fusion instance.
This DAG configures the compute profile at the namespace level without creating a Dataproc cluster.
Simplified, focused implementation with essential error handling.
"""

import json
import requests
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.google.cloud.hooks.datafusion import DataFusionHook
from airflow.providers.google.common.hooks.base_google import GoogleBaseHook
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.exceptions import AirflowException

# Set up logger
logger = logging.getLogger(__name__)

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
    'workerNumNodes': Variable.get('worker_num_nodes', '2'),
    'workerMachineType': Variable.get('worker_machine_type', 'n1-standard-4'),
    'imageVersion': Variable.get('image_version', '2.0-debian10'),
    'subnet': SUBNET,
    'serviceAccount': SERVICE_ACCOUNT,
    'idleTTL': Variable.get('idle_ttl', '3600'),  # Seconds before auto-deletion when idle
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

    def create_datafusion_compute_profile(**kwargs):
        """
        Create a compute profile in Data Fusion using the DataFusion REST API
        """
        try:
            # Get Data Fusion Hook and API client
            datafusion_hook = DataFusionHook(gcp_conn_id='google_cloud_default')
            api_client = datafusion_hook.get_conn()
            
            # Get Data Fusion instance details
            instance_path = f"projects/{PROJECT_ID}/locations/{DATAFUSION_LOCATION}/instances/{DATAFUSION_INSTANCE}"
            instance = api_client.projects().locations().instances().get(name=instance_path).execute()
            
            # Get API endpoint
            api_endpoint = instance.get('apiEndpoint', '')
            if not api_endpoint:
                raise AirflowException("API endpoint not found in Data Fusion instance response")
                
            # Remove https:// prefix if present
            if api_endpoint.startswith('https://'):
                api_endpoint = api_endpoint[8:]
            
            # Get authentication token
            google_hook = GoogleBaseHook(gcp_conn_id='google_cloud_default')
            credentials, _ = google_hook.get_credentials_and_project_id()
            request = google_hook._get_request()
            credentials.refresh(request)
            token = credentials.token
            
            # Create profile configuration
            profile_config = {
                'name': COMPUTE_PROFILE_NAME,
                'label': 'Ephemeral Dataproc Cluster Profile',
                'provisioner': {
                    'name': 'gcp-dataproc',
                    'properties': [
                        {'name': 'projectId', 'value': PROJECT_ID},
                        {'name': 'region', 'value': REGION},
                        {'name': 'zone', 'value': ZONE},
                        {'name': 'subnet', 'value': DATAPROC_CONFIG['subnet']},
                        {'name': 'serviceAccount', 'value': DATAPROC_CONFIG['serviceAccount']},
                        {'name': 'masterNumNodes', 'value': DATAPROC_CONFIG['masterNumNodes']},
                        {'name': 'masterMachineType', 'value': DATAPROC_CONFIG['masterMachineType']},
                        {'name': 'workerNumNodes', 'value': DATAPROC_CONFIG['workerNumNodes']},
                        {'name': 'workerMachineType', 'value': DATAPROC_CONFIG['workerMachineType']},
                        {'name': 'imageVersion', 'value': DATAPROC_CONFIG['imageVersion']},
                        {'name': 'idleTTL', 'value': DATAPROC_CONFIG['idleTTL']},
                        {'name': 'enableStackdriverLogging', 'value': 'true'},
                        {'name': 'enableStackdriverMonitoring', 'value': 'true'},
                    ]
                }
            }
            
            # Set up request
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # API endpoint URL
            url = f"https://{api_endpoint}/v3/namespaces/{DATAFUSION_NAMESPACE}/profiles/{COMPUTE_PROFILE_NAME}"
            
            # Make the API call
            response = requests.put(url, headers=headers, data=json.dumps(profile_config), timeout=60)
            
            # Log response status
            logger.info(f"API response status code: {response.status_code}")
            
            # Handle response
            if response.status_code in (200, 201, 409):  # 409 means it already exists
                logger.info(f"Successfully created/updated compute profile: {COMPUTE_PROFILE_NAME}")
                return {'status': 'success', 'code': response.status_code}
            else:
                logger.error(f"Failed to create compute profile. Status: {response.status_code}")
                logger.error(f"Response: {response.text[:200]}")
                raise AirflowException(f"Failed to create compute profile. Status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error creating compute profile: {str(e)}")
            raise AirflowException(f"Error creating compute profile: {str(e)}")
    
    # Task to create the compute profile in Data Fusion
    create_profile = PythonOperator(
        task_id='create_compute_profile',
        python_callable=create_datafusion_compute_profile,
    )
    
    # Set simple task flow
    create_profile
