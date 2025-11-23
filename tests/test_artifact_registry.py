"""
Tests for ArtifactRegistryController.
"""

from unittest.mock import MagicMock, patch

import pytest

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.artifact_registry import ArtifactRegistryController
from gcp_utils.exceptions import ResourceNotFoundError


@pytest.fixture
def settings():
    """Fixture for GCPSettings."""
    return GCPSettings()


@pytest.fixture
def artifact_registry_controller(settings):
    """Fixture for ArtifactRegistryController with a mocked client."""
    with patch(
        "google.cloud.artifactregistry_v1.ArtifactRegistryClient"
    ) as mock_client:
        controller = ArtifactRegistryController(settings)
        controller._client = mock_client.return_value
        yield controller


def test_create_repository_success(artifact_registry_controller):
    """Test creating a repository successfully."""
    mock_operation = MagicMock()
    mock_repository = MagicMock()
    mock_repository.name = (
        "projects/test-project/locations/us-central1/repositories/test-repo"
    )

    mock_operation.result.return_value = mock_repository
    artifact_registry_controller._client.create_repository.return_value = mock_operation

    repository = artifact_registry_controller.create_repository(
        "test-repo", "us-central1", "DOCKER"
    )

    assert "test-repo" in repository.name


def test_get_repository_success(artifact_registry_controller):
    """Test getting a repository successfully."""
    mock_repository = MagicMock()
    mock_repository.name = (
        "projects/test-project/locations/us-central1/repositories/test-repo"
    )

    artifact_registry_controller._client.get_repository.return_value = mock_repository

    repository = artifact_registry_controller.get_repository("test-repo", "us-central1")

    assert "test-repo" in repository.name


def test_get_repository_not_found(artifact_registry_controller):
    """Test getting a non-existent repository."""
    artifact_registry_controller._client.get_repository.side_effect = Exception(
        "404 Not Found"
    )

    with pytest.raises(ResourceNotFoundError):
        artifact_registry_controller.get_repository("non-existent-repo", "us-central1")


def test_delete_repository(artifact_registry_controller):
    """Test deleting a repository."""
    mock_operation = MagicMock()
    mock_operation.result.return_value = None
    artifact_registry_controller._client.delete_repository.return_value = mock_operation

    artifact_registry_controller.delete_repository("test-repo", "us-central1")

    artifact_registry_controller._client.delete_repository.assert_called_once()


def test_get_docker_image_url(artifact_registry_controller):
    """Test generating a Docker image URL."""
    url = artifact_registry_controller.get_docker_image_url(
        "test-repo", "us-central1", "my-image", "v1.0.0"
    )

    expected = "us-central1-docker.pkg.dev/test-project/test-repo/my-image:v1.0.0"
    assert url == expected


def test_list_repositories(artifact_registry_controller):
    """Test listing repositories."""
    mock_repository = MagicMock()
    mock_repository.name = (
        "projects/test-project/locations/us-central1/repositories/test-repo"
    )

    artifact_registry_controller._client.list_repositories.return_value = [
        mock_repository
    ]

    repositories = artifact_registry_controller.list_repositories("us-central1")

    assert len(repositories) >= 1
