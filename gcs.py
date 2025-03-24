import os
import requests
from google.cloud import storage
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

def upload_to_gcs_put(bucket_name, source_file_path, destination_blob_name=None):
    """
    Uploads a file to a private Google Cloud Storage bucket using PUT method.
    
    Args:
        bucket_name: Name of the GCS bucket
        source_file_path: Path to the local file to upload
        destination_blob_name: Name to give the file in GCS (if None, uses the filename)
    
    Returns:
        The GCS path to the uploaded file
    """
    # If no destination blob name is provided, use the source filename
    if destination_blob_name is None:
        destination_blob_name = os.path.basename(source_file_path)
    
    # Get credentials and create authorized session
    credentials = service_account.Credentials.from_service_account_file(
        os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    )
    scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/cloud-platform'])
    authed_session = AuthorizedSession(scoped_credentials)
    
    # Build the PUT request URL
    upload_url = f"https://storage.googleapis.com/upload/storage/v1/b/{bucket_name}/o?uploadType=media&name={destination_blob_name}"
    
    # Read the file
    with open(source_file_path, 'rb') as file_obj:
        file_content = file_obj.read()
    
    # Get content type (basic detection based on extension)
    content_type = 'application/octet-stream'  # Default
    file_extension = os.path.splitext(source_file_path)[1].lower()
    content_types = {
        '.txt': 'text/plain',
        '.csv': 'text/csv',
        '.json': 'application/json',
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.xml': 'application/xml',
        '.html': 'text/html',
        '.joblib': 'application/octet-stream'  # Added joblib file type
    }
    if file_extension in content_types:
        content_type = content_types[file_extension]
    
    # Make the PUT request
    headers = {
        'Content-Type': content_type
    }
    response = authed_session.put(upload_url, data=file_content, headers=headers)
    
    # Check for success
    if response.status_code == 200:
        print(f"File {source_file_path} uploaded to gs://{bucket_name}/{destination_blob_name}")
        return f"gs://{bucket_name}/{destination_blob_name}"
    else:
        print(f"Error uploading file: {response.text}")
        return None

def main():
    # Set your GCS bucket name
    bucket_name = "your-bucket-name"
    
    # Set the local file path you want to upload
    local_file_path = "path/to/your/model.joblib"
    
    # Optional: Set a custom name for the file in GCS
    # destination_blob_name = "custom_model_name.joblib"
    
    # Upload the file using PUT method
    gcs_path = upload_to_gcs_put(bucket_name, local_file_path)
    
    if gcs_path:
        print(f"File uploaded successfully to: {gcs_path}")
    else:
        print("File upload failed.")

if __name__ == "__main__":
    main()
