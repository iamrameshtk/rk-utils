import os
import requests
import glob

def upload_to_gcs_put(bucket_name, source_file_path, destination_blob_name=None):
    """
    Uploads a file to a private Google Cloud Storage bucket using PUT method.
    Uses auth token from environment variable.
    
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
    
    # Get auth token from environment variable
    auth_token = os.environ.get('GCP_AUTH_TOKEN')
    if not auth_token:
        raise ValueError("GCP_AUTH_TOKEN environment variable is not set")
    
    # Create authorized session using the token
    session = requests.Session()
    session.headers.update({
        'Authorization': f'Bearer {auth_token}'
    })
    
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
        '.joblib': 'application/octet-stream'  # For joblib model files
    }
    if file_extension in content_types:
        content_type = content_types[file_extension]
    
    # Make the PUT request
    headers = {
        'Content-Type': content_type
    }
    response = session.put(upload_url, data=file_content, headers=headers)
    
    # Check for success
    if response.status_code == 200:
        print(f"File {source_file_path} uploaded to gs://{bucket_name}/{destination_blob_name}")
        return f"gs://{bucket_name}/{destination_blob_name}"
    else:
        print(f"Error uploading file: {response.status_code}, {response.text}")
        return None

def upload_folder_to_gcs(bucket_name, folder_path="bucket_object"):
    """
    Uploads all files from a specific folder to GCS.
    
    Args:
        bucket_name: Name of the GCS bucket
        folder_path: Path to the folder containing files to upload (default: 'bucket_object')
    
    Returns:
        List of successful uploads
    """
    # Make sure folder path exists
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist.")
        return []
    
    # Normalize folder path (ensure it ends with separator)
    folder_path = os.path.normpath(folder_path)
    if not folder_path.endswith(os.sep):
        folder_path += os.sep
    
    # Get all files in the folder
    file_paths = glob.glob(os.path.join(folder_path, "*"))
    
    # Filter out directories
    file_paths = [f for f in file_paths if os.path.isfile(f)]
    
    if not file_paths:
        print(f"No files found in '{folder_path}'.")
        return []
    
    # Upload each file
    successful_uploads = []
    for file_path in file_paths:
        # Use just the filename for destination
        destination_blob_name = os.path.basename(file_path)
        
        # Upload the file
        gcs_path = upload_to_gcs_put(bucket_name, file_path, destination_blob_name)
        
        if gcs_path:
            successful_uploads.append(gcs_path)
    
    # Report summary
    print(f"\nUpload Summary:")
    print(f"Total files processed: {len(file_paths)}")
    print(f"Successfully uploaded: {len(successful_uploads)}")
    print(f"Failed uploads: {len(file_paths) - len(successful_uploads)}")
    
    return successful_uploads

def main():
    # Set your GCS bucket name
    bucket_name = "your-bucket-name"
    
    # Upload all files from the 'bucket_object' folder
    successful_uploads = upload_folder_to_gcs(bucket_name)
    
    if successful_uploads:
        print(f"\nSuccessfully uploaded {len(successful_uploads)} files to gs://{bucket_name}/")
    else:
        print("\nNo files were uploaded.")

if __name__ == "__main__":
    main()
