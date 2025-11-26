"""
Tests for CloudRunController.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.cloud_run import CloudRunController
from gcp_utils.exceptions import CloudRunError, ResourceNotFoundError, ValidationError
from gcp_utils.models.cloud_run import TrafficTarget


def create_mock_service(
    name="test-service",
    image="gcr.io/test/image:latest",
    url="https://test-service-abc123.run.app",
):
    """Helper function to create a properly configured mock service."""
    mock_service = MagicMock()
    mock_service.name = f"projects/test-project/locations/us-central1/services/{name}"
    mock_service.uri = url
    mock_service.template.containers = [MagicMock(image=image)]
    mock_service.create_time = datetime.now()
    mock_service.update_time = datetime.now()
    mock_service.latest_ready_revision = f"{name}-001"
    mock_service.traffic = []
    mock_service.labels = {"env": "test"}
    return mock_service


@pytest.fixture
def settings():
    """Fixture for GCPSettings."""
    return GCPSettings()


@pytest.fixture
def cloud_run_controller(settings):
    """Fixture for CloudRunController with a mocked client."""
    with patch("google.cloud.run_v2.ServicesClient") as mock_client:
        controller = CloudRunController(settings)
        controller.client = mock_client.return_value
        yield controller


def test_init_success(settings):
    """Test successful initialization of CloudRunController."""
    with patch("google.cloud.run_v2.ServicesClient"):
        controller = CloudRunController(settings)
        assert controller.settings == settings
        assert controller.region == settings.cloud_run_region


def test_init_failure():
    """Test initialization failure handling."""
    with patch(
        "google.cloud.run_v2.ServicesClient", side_effect=Exception("Init failed")
    ):
        with pytest.raises(CloudRunError) as exc_info:
            CloudRunController()
        assert "Failed to initialize Cloud Run client" in str(exc_info.value)


def test_get_service_success(cloud_run_controller):
    """Test getting a service successfully."""
    mock_service = create_mock_service()
    cloud_run_controller.client.get_service.return_value = mock_service

    service = cloud_run_controller.get_service("test-service")

    assert service.name == "test-service"
    assert service.url == "https://test-service-abc123.run.app"
    assert service.image == "gcr.io/test/image:latest"
    assert service.latest_revision == "test-service-001"


def test_get_service_not_found(cloud_run_controller):
    """Test getting a non-existent service."""
    cloud_run_controller.client.get_service.side_effect = Exception("404 Not Found")

    with pytest.raises(ResourceNotFoundError) as exc_info:
        cloud_run_controller.get_service("non-existent-service")
    assert "Service 'non-existent-service' not found" in str(exc_info.value)


def test_list_services(cloud_run_controller):
    """Test listing services."""
    mock_service = create_mock_service()
    cloud_run_controller.client.list_services.return_value = [mock_service]

    services = cloud_run_controller.list_services()

    assert len(services) == 1
    assert services[0].name == "test-service"


def test_create_service_validation_error(cloud_run_controller):
    """Test creating a service with invalid parameters."""
    with pytest.raises(ValidationError) as exc_info:
        cloud_run_controller.create_service("", "gcr.io/test/image:latest")
    assert "Service name cannot be empty" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        cloud_run_controller.create_service("test-service", "")
    assert "Container image cannot be empty" in str(exc_info.value)


def test_create_service_success(cloud_run_controller):
    """Test creating a service successfully."""
    mock_operation = MagicMock()
    mock_service = create_mock_service()
    mock_operation.result.return_value = mock_service
    cloud_run_controller.client.create_service.return_value = mock_operation

    service = cloud_run_controller.create_service(
        "test-service", "gcr.io/test/image:latest", port=8080, env_vars={"KEY": "value"}
    )

    assert service.name == "test-service"
    cloud_run_controller.client.create_service.assert_called_once()


def test_update_service_success(cloud_run_controller):
    """Test updating a service successfully."""
    mock_service = create_mock_service(image="gcr.io/test/old-image:latest")
    cloud_run_controller.client.get_service.return_value = mock_service

    mock_operation = MagicMock()
    mock_updated_service = create_mock_service(image="gcr.io/test/new-image:latest")
    mock_operation.result.return_value = mock_updated_service
    cloud_run_controller.client.update_service.return_value = mock_operation

    # Patch the protobuf classes to avoid validation issues
    with (
        patch("gcp_utils.controllers.cloud_run.run_v2.UpdateServiceRequest"),
        patch("gcp_utils.controllers.cloud_run.run_v2.ResourceRequirements"),
        patch("gcp_utils.controllers.cloud_run.run_v2.EnvVar"),
        patch("gcp_utils.controllers.cloud_run.run_v2.RevisionScaling"),
    ):

        service = cloud_run_controller.update_service(
            "test-service", image="gcr.io/test/new-image:latest"
        )

        assert service.image == "gcr.io/test/new-image:latest"
        cloud_run_controller.client.update_service.assert_called_once()


def test_delete_service(cloud_run_controller):
    """Test deleting a service."""
    mock_operation = MagicMock()
    mock_operation.result.return_value = None
    cloud_run_controller.client.delete_service.return_value = mock_operation

    cloud_run_controller.delete_service("test-service")

    cloud_run_controller.client.delete_service.assert_called_once()


def test_update_traffic_validation_error(cloud_run_controller):
    """Test updating traffic with invalid percentages."""
    traffic_targets = [
        TrafficTarget(revision_name="rev-001", percent=50),
        TrafficTarget(revision_name="rev-002", percent=30),
    ]

    with pytest.raises(ValidationError) as exc_info:
        cloud_run_controller.update_traffic("test-service", traffic_targets)
    assert "must sum to 100" in str(exc_info.value)


def test_update_traffic_success(cloud_run_controller):
    """Test updating traffic successfully."""
    mock_service = create_mock_service()
    cloud_run_controller.client.get_service.return_value = mock_service

    # Return a fresh mock service to avoid MagicMock pollution in traffic list
    mock_updated_service = create_mock_service()
    mock_operation = MagicMock()
    mock_operation.result.return_value = mock_updated_service
    cloud_run_controller.client.update_service.return_value = mock_operation

    traffic_targets = [
        TrafficTarget(revision_name="rev-001", percent=50),
        TrafficTarget(revision_name="rev-002", percent=50),
    ]

    # Patch the protobuf classes to avoid validation issues
    with (
        patch("gcp_utils.controllers.cloud_run.run_v2.UpdateServiceRequest"),
        patch("gcp_utils.controllers.cloud_run.run_v2.TrafficTarget"),
        patch("gcp_utils.controllers.cloud_run.run_v2.TrafficTargetAllocationType"),
    ):

        service = cloud_run_controller.update_traffic("test-service", traffic_targets)

        assert service is not None
        cloud_run_controller.client.update_service.assert_called_once()


def test_get_service_url(cloud_run_controller):
    """Test getting service URL."""
    mock_service = create_mock_service()
    cloud_run_controller.client.get_service.return_value = mock_service

    url = cloud_run_controller.get_service_url("test-service")
    assert url == "https://test-service-abc123.run.app"


def test_invoke_service_success(cloud_run_controller):
    """Test invoking a service successfully."""
    mock_service = create_mock_service()
    cloud_run_controller.client.get_service.return_value = mock_service

    with (
        patch("gcp_utils.controllers.cloud_run.default") as mock_default,
        patch("gcp_utils.controllers.cloud_run.httpx.Client") as mock_httpx,
    ):

        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_credentials.token = "test-token"
        mock_default.return_value = (mock_credentials, None)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"message": "success"}'
        mock_response.json.return_value = {"message": "success"}

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value.get.return_value = mock_response
        mock_httpx.return_value = mock_client_instance

        result = cloud_run_controller.invoke_service("test-service", "/api/test")

        assert result["status_code"] == 200
        assert result["json"]["message"] == "success"


def test_invoke_service_post(cloud_run_controller):
    """Test invoking a service with POST method."""
    mock_service = create_mock_service()
    cloud_run_controller.client.get_service.return_value = mock_service

    with (
        patch("gcp_utils.controllers.cloud_run.default") as mock_default,
        patch("gcp_utils.controllers.cloud_run.httpx.Client") as mock_httpx,
    ):

        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_credentials.token = "test-token"
        mock_default.return_value = (mock_credentials, None)

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"id": "123"}'
        mock_response.json.return_value = {"id": "123"}

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__.return_value.post.return_value = mock_response
        mock_httpx.return_value = mock_client_instance

        result = cloud_run_controller.invoke_service(
            "test-service", "/api/create", method="POST", data={"name": "test"}
        )

        assert result["status_code"] == 201
        assert result["json"]["id"] == "123"


def test_invoke_service_invalid_method(cloud_run_controller):
    """Test invoking a service with invalid HTTP method."""
    mock_service = create_mock_service()
    cloud_run_controller.client.get_service.return_value = mock_service

    with (
        patch("gcp_utils.controllers.cloud_run.default") as mock_default,
        patch("gcp_utils.controllers.cloud_run.httpx.Client"),
    ):

        mock_credentials = MagicMock()
        mock_credentials.valid = True
        mock_credentials.token = "test-token"
        mock_default.return_value = (mock_credentials, None)

        with pytest.raises(ValidationError) as exc_info:
            cloud_run_controller.invoke_service(
                "test-service", "/api/test", method="INVALID"
            )
        assert "Unsupported HTTP method" in str(exc_info.value)
