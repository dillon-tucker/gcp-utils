"""
Tests for Cloud Functions controller.

This module tests the CloudFunctionsController class with mocked GCP clients.
"""

from unittest.mock import MagicMock, Mock

import pytest
from google.api_core.exceptions import NotFound
from google.cloud.functions_v2.types import Function

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.cloud_functions import CloudFunctionsController
from gcp_utils.exceptions import ResourceNotFoundError


@pytest.fixture
def settings() -> GCPSettings:
    """Create test settings."""
    return GCPSettings(project_id="test-project")


@pytest.fixture
def mock_client() -> Mock:
    """Create a mock Cloud Functions client."""
    return MagicMock()


@pytest.fixture
def controller(settings: GCPSettings, mock_client: Mock) -> CloudFunctionsController:
    """Create a CloudFunctionsController with mocked client."""
    controller = CloudFunctionsController(settings=settings)
    controller._client = mock_client
    return controller


def test_create_function(
    controller: CloudFunctionsController, mock_client: Mock
) -> None:
    """Test creating a Cloud Function."""
    # Setup mock
    mock_operation = MagicMock()
    mock_function = Function(
        name="projects/test-project/locations/us-central1/functions/my-function",
        description="Test function",
    )
    mock_operation.result.return_value = mock_function
    mock_client.create_function.return_value = mock_operation

    # Execute
    build_config = {"runtime": "python312", "entry_point": "main"}
    result = controller.create_function(
        function_id="my-function",
        build_config=build_config,
        wait_for_completion=True,
    )

    # Assert
    assert (
        result.name
        == "projects/test-project/locations/us-central1/functions/my-function"
    )
    mock_client.create_function.assert_called_once()


def test_get_function(controller: CloudFunctionsController, mock_client: Mock) -> None:
    """Test getting a Cloud Function."""
    # Setup mock
    mock_function = Function(
        name="projects/test-project/locations/us-central1/functions/my-function",
        description="Test function",
    )
    mock_client.get_function.return_value = mock_function

    # Execute
    result = controller.get_function("my-function")

    # Assert
    assert (
        result.name
        == "projects/test-project/locations/us-central1/functions/my-function"
    )
    mock_client.get_function.assert_called_once()


def test_get_function_not_found(
    controller: CloudFunctionsController, mock_client: Mock
) -> None:
    """Test getting a non-existent function raises ResourceNotFoundError."""
    # Setup mock
    mock_client.get_function.side_effect = NotFound("Function not found")

    # Execute and assert
    with pytest.raises(ResourceNotFoundError):
        controller.get_function("nonexistent")


def test_list_functions(
    controller: CloudFunctionsController, mock_client: Mock
) -> None:
    """Test listing Cloud Functions."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.functions = [
        Function(name="projects/test-project/locations/us-central1/functions/func1"),
        Function(name="projects/test-project/locations/us-central1/functions/func2"),
    ]
    mock_response.next_page_token = ""
    mock_response.unreachable = []
    mock_client.list_functions.return_value = mock_response

    # Execute
    result = controller.list_functions()

    # Assert
    assert len(result.functions) == 2
    mock_client.list_functions.assert_called_once()


def test_update_function(
    controller: CloudFunctionsController, mock_client: Mock
) -> None:
    """Test updating a Cloud Function."""
    # Setup mock
    mock_operation = MagicMock()
    mock_function = Function(
        name="projects/test-project/locations/us-central1/functions/my-function",
        description="Updated function",
    )
    mock_operation.result.return_value = mock_function
    mock_client.update_function.return_value = mock_operation

    # Execute
    result = controller.update_function(
        function_id="my-function",
        description="Updated function",
        wait_for_completion=True,
    )

    # Assert
    assert result.description == "Updated function"
    mock_client.update_function.assert_called_once()


def test_delete_function(
    controller: CloudFunctionsController, mock_client: Mock
) -> None:
    """Test deleting a Cloud Function."""
    # Setup mock
    mock_operation = MagicMock()
    mock_operation.result.return_value = None
    mock_client.delete_function.return_value = mock_operation

    # Execute
    controller.delete_function("my-function", wait_for_completion=True)

    # Assert
    mock_client.delete_function.assert_called_once()


def test_delete_function_not_found(
    controller: CloudFunctionsController, mock_client: Mock
) -> None:
    """Test deleting a non-existent function raises ResourceNotFoundError."""
    # Setup mock
    mock_client.delete_function.side_effect = NotFound("Function not found")

    # Execute and assert
    with pytest.raises(ResourceNotFoundError):
        controller.delete_function("nonexistent")


def test_generate_upload_url(
    controller: CloudFunctionsController, mock_client: Mock
) -> None:
    """Test generating an upload URL."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.upload_url = "https://storage.googleapis.com/upload/..."
    mock_response.storage_source.bucket = "test-bucket"
    mock_response.storage_source.object_ = "test-object"
    mock_response.storage_source.generation = 123
    mock_client.generate_upload_url.return_value = mock_response

    # Execute
    result = controller.generate_upload_url()

    # Assert
    assert result.upload_url.startswith("https://storage.googleapis.com")
    assert result.storage_source["bucket"] == "test-bucket"
    mock_client.generate_upload_url.assert_called_once()


def test_get_function_url(
    controller: CloudFunctionsController, mock_client: Mock
) -> None:
    """Test getting a function's HTTP URL."""
    # Setup mock
    mock_function = Function(
        name="projects/test-project/locations/us-central1/functions/my-function",
    )
    mock_function.service_config.uri = (
        "https://us-central1-test-project.cloudfunctions.net/my-function"
    )
    mock_client.get_function.return_value = mock_function

    # Execute
    result = controller.get_function_url("my-function")

    # Assert
    assert result.startswith("https://")
    assert "my-function" in result
