"""
Tests for IAMController.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.iam import IAMController
from gcp_utils.exceptions import ResourceNotFoundError


def create_mock_service_account(
    account_id: str = "test-sa", project_id: str = "test-project"
):
    """Helper function to create a properly configured mock service account."""
    mock = MagicMock()
    mock.name = f"projects/{project_id}/serviceAccounts/{account_id}@{project_id}.iam.gserviceaccount.com"
    mock.email = f"{account_id}@{project_id}.iam.gserviceaccount.com"
    mock.display_name = "Test Service Account"
    mock.unique_id = "123456789"
    mock.project_id = project_id
    mock.description = "Test service account description"
    mock.oauth2_client_id = "987654321"
    mock.disabled = False
    return mock


@pytest.fixture
def settings():
    """Fixture for GCPSettings."""
    return GCPSettings()


@pytest.fixture
def iam_controller(settings):
    """Fixture for IAMController with a mocked client."""
    with patch("google.cloud.iam_admin_v1.IAMClient") as mock_client:
        controller = IAMController(settings)
        controller._client = mock_client.return_value
        yield controller


def test_create_service_account_success(iam_controller):
    """Test creating a service account successfully."""
    mock_account = create_mock_service_account("test-sa", "test-project")

    iam_controller._client.create_service_account.return_value = mock_account

    account = iam_controller.create_service_account(
        "test-sa", display_name="Test Service Account"
    )

    assert account.email == "test-sa@test-project.iam.gserviceaccount.com"
    assert account.display_name == "Test Service Account"
    assert account.description == "Test service account description"


def test_get_service_account_success(iam_controller):
    """Test getting a service account successfully."""
    mock_account = create_mock_service_account("test-sa", "test-project")

    iam_controller._client.get_service_account.return_value = mock_account

    account = iam_controller.get_service_account(
        "test-sa@test-project.iam.gserviceaccount.com"
    )

    assert account.email == "test-sa@test-project.iam.gserviceaccount.com"
    assert account.description == "Test service account description"


def test_get_service_account_not_found(iam_controller):
    """Test getting a non-existent service account."""
    from google.api_core.exceptions import NotFound

    iam_controller._client.get_service_account.side_effect = NotFound("404 Not Found")

    with pytest.raises(ResourceNotFoundError):
        iam_controller.get_service_account(
            "nonexistent@test-project.iam.gserviceaccount.com"
        )


def test_list_service_accounts(iam_controller):
    """Test listing service accounts."""
    mock_account = create_mock_service_account("test-sa", "test-project")

    iam_controller._client.list_service_accounts.return_value = [mock_account]

    accounts = iam_controller.list_service_accounts()

    assert len(accounts) == 1
    assert accounts[0].email == "test-sa@test-project.iam.gserviceaccount.com"


def test_delete_service_account(iam_controller):
    """Test deleting a service account."""
    iam_controller._client.delete_service_account.return_value = None

    iam_controller.delete_service_account(
        "test-sa@test-project.iam.gserviceaccount.com"
    )

    iam_controller._client.delete_service_account.assert_called_once()


def test_create_service_account_key(iam_controller):
    """Test creating a service account key."""

    mock_key = MagicMock()
    mock_key.name = "projects/test-project/serviceAccounts/test-sa@test-project.iam.gserviceaccount.com/keys/key123"
    mock_key.private_key_data = b"base64encodeddata"
    mock_key.key_algorithm = "KEY_ALG_RSA_2048"
    mock_key.key_type = "USER_MANAGED"
    mock_key.valid_after_time = datetime.now()
    mock_key.valid_before_time = datetime.now()

    iam_controller._client.create_service_account_key.return_value = mock_key

    key = iam_controller.create_service_account_key(
        "test-sa@test-project.iam.gserviceaccount.com"
    )

    assert key.private_key_data is not None
    assert "key123" in key.name
