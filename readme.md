# Data Fusion Pipeline Deployment Tool

## Overview

This tool automates the deployment of Google Cloud Data Fusion pipelines from a GitHub repository to a Data Fusion instance. The script is designed to work within a Harness CI/CD pipeline, leveraging the existing GitHub integration and service account authentication.

## Key Features

- Deploys pipelines from GitHub repository environment folders (env_dev, env_pre, env_prd)
- Authenticates using existing Harness OIDC token
- Supports selective deployment of specific pipelines
- Handles both new pipeline creation and updates to existing pipelines
- Provides detailed logging and deployment status reporting

## Prerequisites

- Python 3.6 or higher
- Access to a Google Cloud Project with Data Fusion enabled
- Harness CI/CD pipeline with:
  - GitHub repository integration configured
  - Service account with appropriate Data Fusion permissions
  - OIDC token generation enabled

## Required Permissions

The service account used by Harness requires the following roles:
- `roles/datafusion.admin` or `roles/datafusion.editor` on the Data Fusion instance
- `roles/datafusion.runner` for deploying pipelines

## Installation

1. Add this script to your GitHub repository
2. Include the script execution as a step in your Harness pipeline

## Harness Pipeline Configuration

### Basic Pipeline Configuration

Configure your Harness pipeline with the following structure:

```yaml
pipeline:
  name: Deploy Data Fusion Pipelines
  identifier: deploy_data_fusion_pipelines
  projectIdentifier: your_project_id
  orgIdentifier: your_org_id
  tags: {}
  stages:
    - stage:
        name: Deploy Pipelines
        identifier: deploy_pipelines
        description: Deploy pipelines to Data Fusion
        type: Deployment
        spec:
          deploymentType: Kubernetes
          service:
            serviceRef: data_fusion_service
          environment:
            environmentRef: target_environment
            deployToAll: false
            infrastructureDefinitions:
              - identifier: gcp_infrastructure
          execution:
            steps:
              - step:
                  name: Clone Repository
                  identifier: clone_repository
                  type: GitClone
                  spec:
                    connectorRef: github_connector
                    repo: your-org/your-repo
                    branch: main
                    baseBranch: main
                    gitFetchType: Branch
                    buildOnCommit: <+input>
                
              - step:
                  name: Deploy Data Fusion Pipelines
                  identifier: deploy_data_fusion_pipelines
                  type: Run
                  spec:
                    connectorRef: gcp_connector
                    image: python:3.9-slim
                    shell: Bash
                    command: |
                      pip install requests
                      python deploy_data_fusion_pipelines.py \
                        --project-id ${GCP_PROJECT_ID} \
                        --location ${GCP_REGION} \
                        --instance-name ${DATAFUSION_INSTANCE} \
                        --env-folder ${TARGET_ENV} \
                        --namespace ${DATAFUSION_NAMESPACE}
```

### Environment Variables and Secrets

Set up environment variables in your Harness pipeline:

```yaml
  variables:
    - name: GCP_PROJECT_ID
      type: String
      description: GCP Project ID
      required: true
      value: your-gcp-project-id
    
    - name: GCP_REGION
      type: String
      description: GCP Region
      required: true
      value: us-central1
    
    - name: DATAFUSION_INSTANCE
      type: String
      description: Data Fusion Instance Name
      required: true
      value: your-datafusion-instance
    
    - name: TARGET_ENV
      type: String
      description: Target Environment Folder
      required: true
      value: env_dev
    
    - name: DATAFUSION_NAMESPACE
      type: String
      description: Data Fusion Namespace
      required: false
      value: default
```

For secure values like service account keys, use Harness secrets:

```yaml
  secrets:
    - name: GCP_SERVICE_ACCOUNT_KEY
      type: SecretText
      description: GCP Service Account Key (JSON)
```

### Service Account Authentication

To configure service account authentication with OIDC:

```yaml
  serviceAccount:
    spec:
      connectorRef: gcp_connector
      serviceAccountType: WIF
      audience: https://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID
      serviceAccountEmail: your-service-account@your-project.iam.gserviceaccount.com
```

### Triggers

Set up automated triggers based on Git events:

```yaml
triggers:
  - trigger:
      name: On Pipeline Push
      identifier: on_pipeline_push
      enabled: true
      description: Trigger deployment when pipelines are pushed
      tags: {}
      type: Webhook
      spec:
        type: Github
        spec:
          connectorRef: github_connector
          payloadConditions:
            - key: pushedFiles
              operator: Matches
              value: "(env_dev|env_pre|env_prd)/.+\\.json"
          headerConditions: []
          webhookToken: ""
          actions: []
      eventConditions:
        - key: action
          operator: Equals
          value: push
        - key: target_branch
          operator: Equals
          value: main
      pipelineIdentifier: deploy_data_fusion_pipelines
```

## Configuration

### Environment Variables

The script requires the `OIDC_TOKEN` environment variable to be present. This token is automatically generated by Harness and should be available in the pipeline environment.

### GitHub Repository Structure

The script expects your GitHub repository to follow this structure:

```
repository-root/
├── env_dev/
│   ├── pipeline1.json
│   ├── pipeline2.json
│   └── ...
├── env_pre/
│   ├── pipeline1.json
│   ├── pipeline2.json
│   └── ...
└── env_prd/
    ├── pipeline1.json
    ├── pipeline2.json
    └── ...
```

## Usage

The script can be executed as follows:

```bash
python deploy_data_fusion_pipelines.py \
  --project-id YOUR_GCP_PROJECT_ID \
  --location REGION \
  --instance-name DATAFUSION_INSTANCE_NAME \
  --env-folder TARGET_ENVIRONMENT \
  [--namespace NAMESPACE] \
  [--pipelines PIPELINE1 PIPELINE2 ...]
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--project-id` | Yes | Google Cloud Project ID where the Data Fusion instance is located |
| `--location` | Yes | GCP region of the Data Fusion instance (e.g., us-central1) |
| `--instance-name` | Yes | Name of the Data Fusion instance |
| `--env-folder` | Yes | Environment folder to use (env_dev, env_pre, or env_prd) |
| `--namespace` | No | Data Fusion namespace (defaults to "default") |
| `--pipelines` | No | Space-separated list of pipeline names to deploy (deploys all if not specified) |

### Harness Integration

The script automatically detects the repository clone in the Harness workspace environment. No additional configuration is required as Harness clones the repository as part of its execution pipeline.

#### Repository Integration

For the GitHub repository integration in Harness:

1. Navigate to **Resources → Connectors → New Connector**
2. Select **GitHub** as the connector type
3. Configure the connection with:
   - **Connection Name**: A descriptive name like `github-data-fusion-repo`
   - **GitHub URL**: URL of your GitHub instance
   - **Connection Type**: Select "HTTP" for GitHub.com or "SSH" for GitHub Enterprise
   - **Authentication**: Choose between "Username and Token" or "SSH Key"
   - **Repository Permissions**: Ensure read access to repositories is enabled

#### Service Account Configuration

To set up the GCP service account with proper permissions:

1. Navigate to **Resources → Connectors → New Connector**
2. Select **Google Cloud Platform** as the connector type
3. Configure with:
   - **Connector Name**: A descriptive name like `gcp-data-fusion-connector`
   - **Authentication**: Choose "Workload Identity Federation"
   - **Project ID**: Your GCP project ID
   - **Service Account Email**: The service account email with Data Fusion permissions
   - **Workload Identity Provider**: The full resource path of your Workload Identity Provider

#### Workflow Variables

Define pipeline variables under **Pipeline Settings → Variables**:

1. **Basic Variables**:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_REGION`: Region where your Data Fusion instance is located
   - `DATAFUSION_INSTANCE`: Name of your Data Fusion instance
   - `TARGET_ENV`: Environment folder to use (env_dev, env_pre, env_prd)

2. **Advanced Configuration**:
   - `DEPLOYMENT_TIMEOUT`: Maximum time allowed for deployment (default: 600 seconds)
   - `MAX_CONCURRENT`: Maximum number of concurrent pipeline deployments (default: 5)

#### Pipeline Step Configuration

Configure the execution step with proper settings:

1. **Resource Requirements**:
   - Set appropriate CPU and memory limits for the deployment container
   - Example: `cpu: 1`, `memory: 2Gi`

2. **Failure Strategy**:
   - Set retry count: `retryCount: 2`
   - Configure timeout in seconds: `timeout: 600`

3. **Conditional Execution**:
   - Add conditions based on branch, environment, or manual approval requirements

### Deployment Process

1. The script scans the specified environment folder for JSON pipeline files
2. For each pipeline:
   - Validates the pipeline JSON format
   - Checks if the pipeline already exists in Data Fusion
   - Creates new or updates existing pipelines as appropriate
3. Provides a summary of successful and failed deployments

## Exit Codes

- **0**: All pipelines deployed successfully or no pipelines to deploy
- **1**: One or more pipeline deployments failed or an error occurred during execution

## Logging

The script provides detailed logging with timestamps at the INFO level, which will be captured in the Harness pipeline execution logs. Critical errors and warnings are clearly marked in the log output.

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure the Harness service account has the necessary Data Fusion permissions
   - Verify the OIDC token is being generated correctly
   - Check the GCP connector configuration in Harness
   - Validate that the Workload Identity Federation is properly configured

2. **Pipeline Not Found**
   - Check that the pipeline JSON files exist in the specified environment folder
   - Ensure pipeline names are specified correctly when using the `--pipelines` parameter
   - Verify the Git Clone step completed successfully in the Harness execution logs

3. **Invalid Pipeline JSON**
   - Validate that the pipeline JSON format meets Data Fusion requirements
   - Export a fresh copy of the pipeline from Data Fusion UI if needed
   - Check for JSON formatting issues using a validator

4. **Harness-Specific Issues**
   - **Variable Substitution Failure**: Ensure all variables referenced with `${VAR_NAME}` are defined in the pipeline
   - **Connector Issues**: Verify the GCP connector has been successfully tested in Harness
   - **Permission Errors**: Check that the Harness service account has been assigned the correct IAM roles
   - **Execution Environment**: Make sure the execution environment has sufficient resources allocated

5. **Execution Timeouts**
   - Increase the step timeout setting in Harness if deploying many pipelines
   - Consider using the `--pipelines` parameter to deploy subsets of pipelines in separate steps

### Harness Pipeline Debugging

To troubleshoot issues within the Harness pipeline:

1. Check the **Execution Details** in the Harness UI
2. Review the **Logs** tab for each step in the pipeline
3. Use the **Diagnose** feature in Harness to get more detailed error information
4. Add debugging output to the script by modifying the logging level:
   ```bash
   python deploy_data_fusion_pipelines.py \
     --project-id ${GCP_PROJECT_ID} \
     --location ${GCP_REGION} \
     --instance-name ${DATAFUSION_INSTANCE} \
     --env-folder ${TARGET_ENV} \
     --debug
   ```

### Resolving Pipeline Conflicts

If a pipeline deployment fails due to conflicts with an existing pipeline:
1. Review the logs to identify the specific error
2. Consider deleting the conflicting pipeline in Data Fusion before redeploying
3. Ensure pipeline versions are compatible with your Data Fusion instance

## Best Practices

1. **Pipeline Validation**
   - Always validate pipelines in Data Fusion UI before committing to GitHub
   - Use consistent naming conventions for pipeline files

2. **Deployment Strategy**
   - Deploy to dev environment first, then promote to pre-production and production
   - Use the `--pipelines` parameter for targeted deployments during testing

3. **Security**
   - Regularly rotate service account credentials
   - Implement appropriate access controls on your GitHub repository

## Support

For issues related to this script, please contact your organization's Data Engineering team.

For Data Fusion specific issues, refer to the [Google Cloud Data Fusion documentation](https://cloud.google.com/data-fusion/docs).
