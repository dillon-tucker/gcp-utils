"""
Tests for CloudTasksController.
"""
from unittest.mock import MagicMock, patch

import pytest

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.cloud_tasks import CloudTasksController
from gcp_utils.exceptions import ResourceNotFoundError, ValidationError


@pytest.fixture
def settings():
    """Fixture for GCPSettings."""
    return GCPSettings()


@pytest.fixture
def cloud_tasks_controller(settings):
    """Fixture for CloudTasksController with a mocked client."""
    with patch('google.cloud.tasks_v2.CloudTasksClient') as mock_client:
        controller = CloudTasksController(settings)
        controller._client = mock_client.return_value
        yield controller


def test_create_queue_success(cloud_tasks_controller):
    """Test creating a queue successfully."""
    mock_queue = MagicMock()
    mock_queue.name = "projects/test-project/locations/us-central1/queues/test-queue"

    cloud_tasks_controller._client.create_queue.return_value = mock_queue

    queue = cloud_tasks_controller.create_queue("test-queue")

    assert "test-queue" in queue.name


def test_get_queue_success(cloud_tasks_controller):
    """Test getting a queue successfully."""
    mock_queue = MagicMock()
    mock_queue.name = "projects/test-project/locations/us-central1/queues/test-queue"

    cloud_tasks_controller._client.get_queue.return_value = mock_queue

    queue = cloud_tasks_controller.get_queue("test-queue")

    assert "test-queue" in queue.name


def test_get_queue_not_found(cloud_tasks_controller):
    """Test getting a non-existent queue."""
    cloud_tasks_controller._client.get_queue.side_effect = Exception("404 Not Found")

    with pytest.raises(ResourceNotFoundError):
        cloud_tasks_controller.get_queue("non-existent-queue")


def test_create_http_task_success(cloud_tasks_controller):
    """Test creating an HTTP task successfully."""
    mock_task = MagicMock()
    mock_task.name = "projects/test-project/locations/us-central1/queues/test-queue/tasks/task-123"

    cloud_tasks_controller._client.create_task.return_value = mock_task

    task = cloud_tasks_controller.create_http_task(
        queue_name="test-queue",
        url="https://example.com/api/task",
        http_method="POST",
        payload={"key": "value"}
    )

    assert "task-123" in task.name


def test_create_http_task_validation_error(cloud_tasks_controller):
    """Test creating an HTTP task with invalid parameters."""
    with pytest.raises(ValidationError):
        cloud_tasks_controller.create_http_task(
            queue_name="",
            url="https://example.com/api/task"
        )


def test_delete_queue(cloud_tasks_controller):
    """Test deleting a queue."""
    cloud_tasks_controller._client.delete_queue.return_value = None

    cloud_tasks_controller.delete_queue("test-queue")

    cloud_tasks_controller._client.delete_queue.assert_called_once()


def test_list_tasks(cloud_tasks_controller):
    """Test listing tasks in a queue."""
    mock_task = MagicMock()
    mock_task.name = "projects/test-project/locations/us-central1/queues/test-queue/tasks/task-123"

    cloud_tasks_controller._client.list_tasks.return_value = [mock_task]

    tasks = cloud_tasks_controller.list_tasks("test-queue")

    assert len(tasks) >= 1
