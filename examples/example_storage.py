"""
Example usage of CloudStorageController.

This example demonstrates common Cloud Storage operations including
bucket management, file uploads/downloads, and blob operations.
"""

from gcp_utilities.config import GCPSettings
from gcp_utilities.controllers import CloudStorageController


def main():
    # Initialize settings (reads from environment variables or .env file)
    settings = GCPSettings(
        project_id="my-gcp-project",
        storage_bucket="my-default-bucket",
    )

    # Create controller
    storage = CloudStorageController(settings)

    # Create a bucket
    print("Creating bucket...")
    bucket_info = storage.create_bucket(
        bucket_name="my-new-bucket",
        location="us-central1",
        storage_class="STANDARD",
        labels={"environment": "development"},
    )
    print(f"Created bucket: {bucket_info.name}")

    # Upload a file
    print("\nUploading file...")
    upload_result = storage.upload_file(
        bucket_name="my-new-bucket",
        source_path="local_file.txt",
        destination_blob_name="uploads/remote_file.txt",
        metadata={"uploaded_by": "example_script"},
    )
    print(f"Uploaded: {upload_result.blob_name} ({upload_result.size} bytes)")

    # Upload from string
    print("\nUploading from string...")
    storage.upload_from_string(
        bucket_name="my-new-bucket",
        destination_blob_name="data/config.json",
        content='{"key": "value"}',
        content_type="application/json",
    )

    # List blobs
    print("\nListing blobs...")
    blobs = storage.list_blobs(
        bucket_name="my-new-bucket",
        prefix="uploads/",
    )
    for blob in blobs:
        print(f"  - {blob.name} ({blob.size} bytes)")

    # Download file
    print("\nDownloading file...")
    storage.download_file(
        bucket_name="my-new-bucket",
        blob_name="uploads/remote_file.txt",
        destination_path="downloaded_file.txt",
    )

    # Download as text
    print("\nDownloading as text...")
    content = storage.download_as_text(
        bucket_name="my-new-bucket",
        blob_name="data/config.json",
    )
    print(f"Content: {content}")

    # Generate signed URL
    print("\nGenerating signed URL...")
    from datetime import timedelta

    signed_url = storage.generate_signed_url(
        bucket_name="my-new-bucket",
        blob_name="uploads/remote_file.txt",
        expiration=timedelta(hours=1),
    )
    print(f"Signed URL: {signed_url[:50]}...")

    # Copy blob
    print("\nCopying blob...")
    copied_blob = storage.copy_blob(
        source_bucket="my-new-bucket",
        source_blob="uploads/remote_file.txt",
        destination_bucket="my-new-bucket",
        destination_blob="backups/remote_file_backup.txt",
    )
    print(f"Copied to: {copied_blob.name}")

    # Get blob metadata
    print("\nGetting blob metadata...")
    metadata = storage.get_blob_metadata(
        bucket_name="my-new-bucket",
        blob_name="uploads/remote_file.txt",
    )
    print(f"Metadata: Created {metadata.created}, Size: {metadata.size}")

    # Delete blob
    print("\nDeleting blob...")
    storage.delete_blob(
        bucket_name="my-new-bucket",
        blob_name="backups/remote_file_backup.txt",
    )
    print("Blob deleted")

    # List buckets
    print("\nListing all buckets...")
    buckets = storage.list_buckets()
    for bucket in buckets:
        print(f"  - {bucket.name} ({bucket.location})")

    # Clean up - delete bucket (with force to delete all contents)
    print("\nDeleting bucket (with contents)...")
    storage.delete_bucket("my-new-bucket", force=True)
    print("Bucket deleted")


if __name__ == "__main__":
    main()
