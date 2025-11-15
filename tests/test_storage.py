"""
Tests for CloudStorageController.
"""
import pytest
from unittest.mock import MagicMock, patch
from gcp_utils.controllers.storage import CloudStorageController
from gcp_utils.config import GCPSettings
from gcp_utils.exceptions import ResourceNotFoundError, ValidationError

@pytest.fixture
def settings():
    """Fixture for GCPSettings."""
    return GCPSettings()  # Reads from .env file

@pytest.fixture
def storage_controller(settings):
    """Fixture for CloudStorageController with a mocked client."""
    with patch('google.cloud.storage.Client') as mock_client:
        controller = CloudStorageController(settings)
        controller.client = mock_client.return_value
        yield controller

def test_get_bucket_not_found(storage_controller):
    """Test that get_bucket raises ResourceNotFoundError for a non-existent bucket."""
    storage_controller.client.get_bucket.side_effect = Exception("404 Not Found")
    with pytest.raises(ResourceNotFoundError):
        storage_controller.get_bucket("non-existent-bucket")

def test_upload_file_validation_error(storage_controller):
    """Test that upload_file raises ValidationError for a non-existent file."""
    with pytest.raises(ValidationError):
        storage_controller.upload_file("my-bucket", "non-existent-file.txt", "remote.txt")

def test_delete_blob(storage_controller):
    """Test deleting a blob."""
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    storage_controller.client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    storage_controller.delete_blob("my-bucket", "my-blob")

    mock_bucket.blob.assert_called_once_with("my-blob")
    mock_blob.delete.assert_called_once()

@pytest.mark.integration
def test_bucket_lifecycle(settings):
    """Integration test for the full lifecycle of a bucket."""
    controller = CloudStorageController(settings)
    bucket_name = f"test-bucket-lifecycle-{settings.project_id}"

    # Create bucket
    bucket_info = controller.create_bucket(bucket_name)
    assert bucket_info.name == bucket_name

    # Get bucket
    bucket_info = controller.get_bucket(bucket_name)
    assert bucket_info.name == bucket_name

    # Delete bucket
    controller.delete_bucket(bucket_name)

    with pytest.raises(ResourceNotFoundError):
        controller.get_bucket(bucket_name)

@pytest.mark.integration
def test_blob_lifecycle(settings):
    """Integration test for the full lifecycle of a blob."""
    controller = CloudStorageController(settings)
    bucket_name = f"test-blob-lifecycle-{settings.project_id}"
    blob_name = "test-blob.txt"
    file_content = "Hello, World!"
    local_file_path = "test_blob_lifecycle.txt"

    with open(local_file_path, "w") as f:
        f.write(file_content)

    # Create bucket
    controller.create_bucket(bucket_name)

    # Upload blob
    upload_result = controller.upload_file(bucket_name, local_file_path, blob_name)
    assert upload_result.blob_name == blob_name

    # Download and verify content
    downloaded_content = controller.download_as_text(bucket_name, blob_name)
    assert downloaded_content == file_content

    # List blobs
    blobs = controller.list_blobs(bucket_name)
    assert any(b.name == blob_name for b in blobs)

    # Delete blob
    controller.delete_blob(bucket_name, blob_name)

    # Verify blob is deleted
    with pytest.raises(ResourceNotFoundError):
        controller.get_blob_metadata(bucket_name, blob_name)

    # Cleanup
    controller.delete_bucket(bucket_name)
    import os
    os.remove(local_file_path)
