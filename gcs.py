from google.cloud import storage
import os

def upload_to_gcs(bucket_name, source_file_path, destination_blob_name=None):
    """
    Uploads a file to a Google Cloud Storage bucket.
    
    Args:
        bucket_name: Name of the GCS bucket
        source_file_path: Path to the local file to upload
        destination_blob_name: Name to give the file in GCS (if None, uses the filename)
    
    Returns:
        The public URL of the uploaded file
    """
    # If no destination blob name is provided, use the source filename
    if destination_blob_name is None:
        destination_blob_name = os.path.basename(source_file_path)
    
    # Initialize the GCS client
    storage_client = storage.Client()
    
    # Get the bucket
    bucket = storage_client.bucket(bucket_name)
    
    # Create a blob object and upload the file
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_path)
    
    print(f"File {source_file_path} uploaded to gs://{bucket_name}/{destination_blob_name}")
    
    # Return the public URL
    return blob.public_url

def main():
    # Set your GCS bucket name
    bucket_name = "your-bucket-name"
    
    # Set the local file path you want to upload
    local_file_path = "path/to/your/file.txt"
    
    # Optional: Set a custom name for the file in GCS
    # destination_blob_name = "custom_filename.txt"
    
    # Upload the file
    upload_to_gcs(bucket_name, local_file_path)
    # Or with custom destination name: upload_to_gcs(bucket_name, local_file_path, "custom_filename.txt")

if __name__ == "__main__":
    main()
