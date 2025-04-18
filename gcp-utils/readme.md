### GCP cleanup script to include authentication based on environment variables. The script now supports multiple authentication methods:

1. **Environment Variable Authentication**: The script can automatically detect and use authentication tokens from common environment variables:
   - `GCP_AUTH_TOKEN`: Direct authentication token 
   - `GOOGLE_APPLICATION_CREDENTIALS`: Path to a credentials file
   - `GCP_SERVICE_ACCOUNT_KEY`: Service account key content

2. **File-based Authentication**: Specify a token file with the `--auth-token-file` option

3. **Default Authentication**: If no specific authentication is provided, the script falls back to gcloud's default authentication

### Key Features Added:

- Temporary file handling for secure token storage
- Automatic cleanup of temporary authentication files
- Command-line option to use environment variables (`--use-env-auth` or `-e`)
- Command-line option to specify an auth token file (`--auth-token-file` or `-a`)
- Detailed logging of authentication steps

### Example Usage:

```bash
# Use authentication from environment variables
python gcp_cleanup.py --project-id=your-project-id --use-env-auth

# Use authentication from a specific file
python gcp_cleanup.py --project-id=your-project-id --auth-token-file=/path/to/credentials.json

# Use default authentication (gcloud auth)
python gcp_cleanup.py --project-id=your-project-id
```

The script checks for common environment variables used for GCP authentication and properly handles the different formats. This makes it easy to integrate with CI/CD pipelines or other automated systems that may have different authentication mechanisms.
