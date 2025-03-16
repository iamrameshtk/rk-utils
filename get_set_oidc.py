import json
import requests
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Path to Workload Identity Provider JSON file
WIP_JSON_PATH = "/harness/.config/gcloud/application_default_credentials.json"

def load_wip_json():
    """Load the Workload Identity Provider JSON file."""
    try:
        with open(WIP_JSON_PATH, "r") as f:
            wip_data = json.load(f)
        logging.info("Successfully loaded Workload Identity Provider JSON.")
        return wip_data
    except FileNotFoundError:
        logging.error(f"File not found: {WIP_JSON_PATH}")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in {WIP_JSON_PATH}")
        sys.exit(1)

def get_subject_token(credential_source_path):
    """Retrieve the OIDC subject token from the credential source file."""
    try:
        with open(credential_source_path, "r") as f:
            subject_token = f.read().strip()
        if not subject_token:
            logging.error("Subject token file is empty.")
            sys.exit(1)
        logging.info("Successfully retrieved the subject token.")
        return subject_token
    except FileNotFoundError:
        logging.error(f"Credential source file not found: {credential_source_path}")
        sys.exit(1)

def get_access_token():
    """Generate the OIDC token using the JSON configuration."""
    wip_data = load_wip_json()
    token_url = wip_data.get("token_url")
    credential_source_path = wip_data.get("credential_source", {}).get("file")
    subject_token_type = wip_data.get("subject_token_type")
    impersonation_url = wip_data.get("service_account_impersonation_url")
    audience = wip_data.get("audience")

    if not token_url or not credential_source_path or not subject_token_type or not impersonation_url or not audience:
        logging.error("Missing required fields in the JSON file.")
        sys.exit(1)

    subject_token = get_subject_token(credential_source_path)

    payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "subject_token": subject_token,
        "subject_token_type": subject_token_type,
        "audience": audience
    }

    try:
        response = requests.post(token_url, json=payload, timeout=10)
        response.raise_for_status()
        access_token = response.json().get("access_token")

        if not access_token:
            logging.error("Access token not found in response.")
            sys.exit(1)

        logging.info("Successfully retrieved the access token.")
        return access_token
    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving access token: {e}")
        sys.exit(1)

def main():
    """Main function to retrieve and print the OIDC token."""
    logging.info("Starting the OIDC token retrieval process...")

    # Retrieve OIDC token
    access_token = get_access_token()

    # Print the OIDC token (useful for setting in CI/CD environment variables)
    print(access_token)

if __name__ == "__main__":
    main()
