"""
Tests for SecretManagerController.
"""
from unittest.mock import patch

import pytest
from google.api_core import exceptions as google_exceptions

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.secret_manager import SecretManagerController
from gcp_utils.exceptions import ResourceNotFoundError


@pytest.fixture
def settings():
    """Fixture for GCPSettings."""
    return GCPSettings()  # Reads from .env file

@pytest.fixture
def secret_manager_controller(settings):
    """Fixture for SecretManagerController with a mocked client."""
    with patch('google.cloud.secretmanager.SecretManagerServiceClient') as mock_client:
        controller = SecretManagerController(settings)
        controller.client = mock_client.return_value
        yield controller

def test_access_secret_version_not_found(secret_manager_controller):
    """Test that access_secret_version raises ResourceNotFoundError."""
    secret_manager_controller.client.access_secret_version.side_effect = google_exceptions.NotFound("404")

    with pytest.raises(ResourceNotFoundError):
        secret_manager_controller.access_secret_version("non-existent-secret")

def test_create_secret(secret_manager_controller):
    """Test creating a secret."""
    secret_id = "my-secret"
    secret_manager_controller.create_secret(secret_id)

    parent = f"projects/{secret_manager_controller.settings.project_id}"
    secret_manager_controller.client.create_secret.assert_called_once()
    call_args = secret_manager_controller.client.create_secret.call_args
    assert call_args.kwargs['request'].parent == parent
    assert call_args.kwargs['request'].secret_id == secret_id
@pytest.mark.integration
def test_secret_lifecycle(settings):
    """Integration test for the full lifecycle of a secret."""
    controller = SecretManagerController(settings)
    secret_id = "test-secret-lifecycle"
    payload = "my-super-secret-payload"

    # Clean up any existing secret from previous test runs
    try:
        controller.delete_secret(secret_id)
    except Exception:
        pass  # Secret doesn't exist or can't be deleted, which is fine

    # Create secret with a value
    version = controller.create_secret_with_value(secret_id, payload)
    assert secret_id in version["full_name"]

    # Access the secret
    retrieved_payload = controller.access_secret_version(secret_id)
    assert retrieved_payload == payload

    # Add a new version
    new_payload = "new-super-secret-payload"
    new_version = controller.add_secret_version(secret_id, new_payload)
    assert new_version["name"] == "2"

    # Access the new version
    retrieved_new_payload = controller.access_secret_version(secret_id, version="latest")
    assert retrieved_new_payload == new_payload

    # Delete the secret
    controller.delete_secret(secret_id)

    # Verify the secret is deleted
    with pytest.raises(ResourceNotFoundError):
        controller.access_secret_version(secret_id)
