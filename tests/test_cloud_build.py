"""
Tests for Cloud Build controller.

This module tests the CloudBuildController class with mocked GCP clients.
"""

from unittest.mock import MagicMock, Mock

import pytest
from google.api_core.exceptions import NotFound
from google.cloud.devtools.cloudbuild_v1.types import Build as GCPBuild
from google.cloud.devtools.cloudbuild_v1.types import BuildTrigger as GCPBuildTrigger

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.cloud_build import CloudBuildController
from gcp_utils.exceptions import ResourceNotFoundError


@pytest.fixture
def settings() -> GCPSettings:
    """Create test settings."""
    return GCPSettings(project_id="test-project")


@pytest.fixture
def mock_client() -> Mock:
    """Create a mock Cloud Build client."""
    return MagicMock()


@pytest.fixture
def controller(settings: GCPSettings, mock_client: Mock) -> CloudBuildController:
    """Create a CloudBuildController with mocked client."""
    controller = CloudBuildController(settings=settings)
    controller._client = mock_client
    return controller


def test_create_build(controller: CloudBuildController, mock_client: Mock) -> None:
    """Test creating a Cloud Build."""
    # Setup mock
    mock_operation = MagicMock()
    mock_metadata = MagicMock()
    mock_metadata.build.id = "build123"
    mock_operation.metadata = mock_metadata
    mock_client.create_build.return_value = mock_operation

    # Execute
    steps = [
        {"name": "gcr.io/cloud-builders/docker", "args": ["build", "-t", "image", "."]},
    ]
    result = controller.create_build(steps=steps)

    # Assert
    assert result.id == "build123"
    mock_client.create_build.assert_called_once()


def test_get_build(controller: CloudBuildController, mock_client: Mock) -> None:
    """Test getting a Cloud Build."""
    # Setup mock
    mock_build = GCPBuild(
        id="build123",
        project_id="test-project",
    )
    mock_client.get_build.return_value = mock_build

    # Execute
    result = controller.get_build("build123")

    # Assert
    assert result.id == "build123"
    mock_client.get_build.assert_called_once()


def test_get_build_not_found(
    controller: CloudBuildController, mock_client: Mock
) -> None:
    """Test getting a non-existent build raises ResourceNotFoundError."""
    # Setup mock
    mock_client.get_build.side_effect = NotFound("Build not found")

    # Execute and assert
    with pytest.raises(ResourceNotFoundError):
        controller.get_build("nonexistent")


def test_list_builds(controller: CloudBuildController, mock_client: Mock) -> None:
    """Test listing Cloud Builds."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.builds = [
        GCPBuild(id="build1", project_id="test-project"),
        GCPBuild(id="build2", project_id="test-project"),
    ]
    mock_response.next_page_token = ""
    mock_client.list_builds.return_value = mock_response

    # Execute
    result = controller.list_builds()

    # Assert
    assert len(result.builds) == 2
    mock_client.list_builds.assert_called_once()


def test_cancel_build(controller: CloudBuildController, mock_client: Mock) -> None:
    """Test cancelling a Cloud Build."""
    # Setup mock
    mock_build = GCPBuild(
        id="build123",
        project_id="test-project",
    )
    mock_client.cancel_build.return_value = mock_build

    # Execute
    result = controller.cancel_build("build123")

    # Assert
    assert result.id == "build123"
    mock_client.cancel_build.assert_called_once()


def test_create_build_trigger(
    controller: CloudBuildController, mock_client: Mock
) -> None:
    """Test creating a Cloud Build trigger."""
    # Setup mock
    mock_trigger = GCPBuildTrigger(
        id="trigger123",
        name="my-trigger",
        description="Test trigger",
    )
    mock_client.create_build_trigger.return_value = mock_trigger

    # Execute
    result = controller.create_build_trigger(
        name="my-trigger",
        description="Test trigger",
        filename="cloudbuild.yaml",
    )

    # Assert
    assert result.name == "my-trigger"
    mock_client.create_build_trigger.assert_called_once()


def test_get_build_trigger(controller: CloudBuildController, mock_client: Mock) -> None:
    """Test getting a Cloud Build trigger."""
    # Setup mock
    mock_trigger = GCPBuildTrigger(
        id="trigger123",
        name="my-trigger",
    )
    mock_client.get_build_trigger.return_value = mock_trigger

    # Execute
    result = controller.get_build_trigger("trigger123")

    # Assert
    assert result.name == "my-trigger"
    mock_client.get_build_trigger.assert_called_once()


def test_get_build_trigger_not_found(
    controller: CloudBuildController, mock_client: Mock
) -> None:
    """Test getting a non-existent trigger raises ResourceNotFoundError."""
    # Setup mock
    mock_client.get_build_trigger.side_effect = NotFound("Trigger not found")

    # Execute and assert
    with pytest.raises(ResourceNotFoundError):
        controller.get_build_trigger("nonexistent")


def test_list_build_triggers(
    controller: CloudBuildController, mock_client: Mock
) -> None:
    """Test listing Cloud Build triggers."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.triggers = [
        GCPBuildTrigger(id="trigger1", name="trigger-1"),
        GCPBuildTrigger(id="trigger2", name="trigger-2"),
    ]
    mock_response.next_page_token = ""
    mock_client.list_build_triggers.return_value = mock_response

    # Execute
    result = controller.list_build_triggers()

    # Assert
    assert len(result.triggers) == 2
    mock_client.list_build_triggers.assert_called_once()


def test_update_build_trigger(
    controller: CloudBuildController, mock_client: Mock
) -> None:
    """Test updating a Cloud Build trigger."""
    # Setup mock
    mock_get_trigger = GCPBuildTrigger(
        id="trigger123",
        name="my-trigger",
    )
    mock_updated_trigger = GCPBuildTrigger(
        id="trigger123",
        name="updated-trigger",
    )
    mock_client.get_build_trigger.return_value = mock_get_trigger
    mock_client.update_build_trigger.return_value = mock_updated_trigger

    # Execute
    result = controller.update_build_trigger(
        trigger_id="trigger123",
        name="updated-trigger",
    )

    # Assert
    assert result.name == "updated-trigger"
    mock_client.update_build_trigger.assert_called_once()


def test_delete_build_trigger(
    controller: CloudBuildController, mock_client: Mock
) -> None:
    """Test deleting a Cloud Build trigger."""
    # Execute
    controller.delete_build_trigger("trigger123")

    # Assert
    mock_client.delete_build_trigger.assert_called_once()


def test_run_build_trigger(controller: CloudBuildController, mock_client: Mock) -> None:
    """Test manually running a Cloud Build trigger."""
    # Setup mock
    mock_operation = MagicMock()
    mock_build = GCPBuild(id="build123", project_id="test-project")
    mock_operation.result.return_value = mock_build
    mock_client.run_build_trigger.return_value = mock_operation

    # Execute
    result = controller.run_build_trigger("trigger123")

    # Assert
    assert result.build_id == "build123"
    mock_client.run_build_trigger.assert_called_once()
