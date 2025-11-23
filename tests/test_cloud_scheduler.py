"""
Tests for Cloud Scheduler controller.

This module tests the CloudSchedulerController class with mocked GCP clients.
"""

from unittest.mock import MagicMock, Mock

import pytest
from google.api_core.exceptions import NotFound
from google.cloud.scheduler_v1.types import Job

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.cloud_scheduler import CloudSchedulerController
from gcp_utils.exceptions import ResourceNotFoundError


@pytest.fixture
def settings() -> GCPSettings:
    """Create test settings."""
    return GCPSettings(project_id="test-project")


@pytest.fixture
def mock_client() -> Mock:
    """Create a mock Cloud Scheduler client."""
    return MagicMock()


@pytest.fixture
def controller(settings: GCPSettings, mock_client: Mock) -> CloudSchedulerController:
    """Create a CloudSchedulerController with mocked client."""
    controller = CloudSchedulerController(settings=settings)
    controller._client = mock_client
    return controller


def test_create_job(controller: CloudSchedulerController, mock_client: Mock) -> None:
    """Test creating a Cloud Scheduler job."""
    # Setup mock
    mock_job = Job(
        name="projects/test-project/locations/us-central1/jobs/my-job",
        schedule="0 9 * * *",
        time_zone="America/Los_Angeles",
    )
    mock_client.create_job.return_value = mock_job

    # Execute
    result = controller.create_job(
        job_id="my-job",
        schedule="0 9 * * *",
        http_target={"uri": "https://example.com"},
    )

    # Assert
    assert result.schedule == "0 9 * * *"
    mock_client.create_job.assert_called_once()


def test_create_http_job(controller: CloudSchedulerController, mock_client: Mock) -> None:
    """Test creating an HTTP job with convenience method."""
    # Setup mock
    mock_job = Job(
        name="projects/test-project/locations/us-central1/jobs/http-job",
        schedule="*/15 * * * *",
    )
    mock_client.create_job.return_value = mock_job

    # Execute
    result = controller.create_http_job(
        job_id="http-job",
        schedule="*/15 * * * *",
        uri="https://example.com/api/task",
        http_method="POST",
    )

    # Assert
    assert result.name.endswith("http-job")
    mock_client.create_job.assert_called_once()


def test_create_pubsub_job(
    controller: CloudSchedulerController, mock_client: Mock
) -> None:
    """Test creating a Pub/Sub job with convenience method."""
    # Setup mock
    mock_job = Job(
        name="projects/test-project/locations/us-central1/jobs/pubsub-job",
        schedule="0 */6 * * *",
    )
    mock_client.create_job.return_value = mock_job

    # Execute
    result = controller.create_pubsub_job(
        job_id="pubsub-job",
        schedule="0 */6 * * *",
        topic_name="my-topic",
        data=b'{"action": "process"}',
    )

    # Assert
    assert result.name.endswith("pubsub-job")
    mock_client.create_job.assert_called_once()


def test_get_job(controller: CloudSchedulerController, mock_client: Mock) -> None:
    """Test getting a Cloud Scheduler job."""
    # Setup mock
    mock_job = Job(
        name="projects/test-project/locations/us-central1/jobs/my-job",
        schedule="0 9 * * *",
    )
    mock_client.get_job.return_value = mock_job

    # Execute
    result = controller.get_job("my-job")

    # Assert
    assert result.schedule == "0 9 * * *"
    mock_client.get_job.assert_called_once()


def test_get_job_not_found(
    controller: CloudSchedulerController, mock_client: Mock
) -> None:
    """Test getting a non-existent job raises ResourceNotFoundError."""
    # Setup mock
    mock_client.get_job.side_effect = NotFound("Job not found")

    # Execute and assert
    with pytest.raises(ResourceNotFoundError):
        controller.get_job("nonexistent")


def test_list_jobs(controller: CloudSchedulerController, mock_client: Mock) -> None:
    """Test listing Cloud Scheduler jobs."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.jobs = [
        Job(name="projects/test-project/locations/us-central1/jobs/job1"),
        Job(name="projects/test-project/locations/us-central1/jobs/job2"),
    ]
    mock_response.next_page_token = ""
    mock_client.list_jobs.return_value = mock_response

    # Execute
    result = controller.list_jobs()

    # Assert
    assert len(result.jobs) == 2
    mock_client.list_jobs.assert_called_once()


def test_update_job(controller: CloudSchedulerController, mock_client: Mock) -> None:
    """Test updating a Cloud Scheduler job."""
    # Setup mock
    mock_job = Job(
        name="projects/test-project/locations/us-central1/jobs/my-job",
        schedule="0 10 * * *",
    )
    mock_client.update_job.return_value = mock_job

    # Execute
    result = controller.update_job(
        job_id="my-job",
        schedule="0 10 * * *",
    )

    # Assert
    assert result.schedule == "0 10 * * *"
    mock_client.update_job.assert_called_once()


def test_delete_job(controller: CloudSchedulerController, mock_client: Mock) -> None:
    """Test deleting a Cloud Scheduler job."""
    # Execute
    controller.delete_job("my-job")

    # Assert
    mock_client.delete_job.assert_called_once()


def test_pause_job(controller: CloudSchedulerController, mock_client: Mock) -> None:
    """Test pausing a Cloud Scheduler job."""
    # Setup mock
    mock_job = Job(
        name="projects/test-project/locations/us-central1/jobs/my-job",
    )
    mock_job.state = 2  # PAUSED
    mock_client.pause_job.return_value = mock_job

    # Execute
    result = controller.pause_job("my-job")

    # Assert
    assert result.name.endswith("my-job")
    mock_client.pause_job.assert_called_once()


def test_resume_job(controller: CloudSchedulerController, mock_client: Mock) -> None:
    """Test resuming a Cloud Scheduler job."""
    # Setup mock
    mock_job = Job(
        name="projects/test-project/locations/us-central1/jobs/my-job",
    )
    mock_job.state = 1  # ENABLED
    mock_client.resume_job.return_value = mock_job

    # Execute
    result = controller.resume_job("my-job")

    # Assert
    assert result.name.endswith("my-job")
    mock_client.resume_job.assert_called_once()


def test_run_job(controller: CloudSchedulerController, mock_client: Mock) -> None:
    """Test manually running a Cloud Scheduler job."""
    # Setup mock
    from datetime import datetime
    mock_job = Job(
        name="projects/test-project/locations/us-central1/jobs/my-job",
    )
    mock_job.last_attempt_time = datetime.now()
    mock_client.run_job.return_value = mock_job

    # Execute
    result = controller.run_job("my-job")

    # Assert
    assert result.name.endswith("my-job")
    mock_client.run_job.assert_called_once()
