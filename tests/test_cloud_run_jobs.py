"""
Tests for Cloud Run Jobs functionality in CloudRunController.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.cloud_run import CloudRunController
from gcp_utils.exceptions import CloudRunError, ResourceNotFoundError, ValidationError
from gcp_utils.models.cloud_run import ExecutionStatus


def create_mock_job(
    name="test-job",
    image="gcr.io/test/batch-job:latest",
    task_count=1,
    parallelism=1,
):
    """Helper function to create a properly configured mock job."""
    mock_job = MagicMock()
    mock_job.name = f"projects/test-project/locations/us-central1/jobs/{name}"

    # Template configuration
    mock_job.template.task_count = task_count
    mock_job.template.parallelism = parallelism

    # Task template
    mock_container = MagicMock()
    mock_container.image = image
    mock_container.resources.limits = {"cpu": "1000m", "memory": "512Mi"}
    mock_container.env = []

    mock_job.template.template.containers = [mock_container]
    mock_job.template.template.max_retries = 3
    mock_job.template.template.timeout = "600s"
    mock_job.template.template.service_account = None
    mock_job.template.template.execution_environment = "EXECUTION_ENVIRONMENT_GEN2"

    # Metadata
    mock_job.create_time = datetime.now()
    mock_job.update_time = datetime.now()
    mock_job.labels = {"env": "test"}
    mock_job.execution_count = 0
    mock_job.launch_stage = "GA"
    mock_job.latest_created_execution = None  # No latest execution

    return mock_job


def create_mock_execution(
    name="test-execution-abc123",
    job_name="test-job",
    task_count=5,
    succeeded_count=5,
    failed_count=0,
):
    """Helper function to create a properly configured mock execution."""
    mock_execution = MagicMock()
    mock_execution.name = (
        f"projects/test-project/locations/us-central1/jobs/{job_name}/executions/{name}"
    )

    # Task counts
    mock_execution.task_count = task_count
    mock_execution.succeeded_count = succeeded_count
    mock_execution.failed_count = failed_count
    mock_execution.cancelled_count = 0
    mock_execution.running_count = 0

    # Timing
    mock_execution.create_time = datetime.now() - timedelta(minutes=10)
    mock_execution.start_time = datetime.now() - timedelta(minutes=9)
    mock_execution.completion_time = datetime.now()

    # Configuration
    mock_execution.parallelism = 1
    mock_execution.labels = {"env": "test"}

    return mock_execution


@pytest.fixture
def settings():
    """Fixture for GCPSettings."""
    return GCPSettings()


@pytest.fixture
def cloud_run_controller(settings):
    """Fixture for CloudRunController with mocked clients."""
    with (
        patch("google.cloud.run_v2.ServicesClient"),
        patch("gcp_utils.controllers.cloud_run.JobsClient") as mock_jobs_client,
    ):
        controller = CloudRunController(settings)
        controller.jobs_client = mock_jobs_client.return_value
        yield controller


def test_init_with_jobs_client(settings):
    """Test successful initialization with jobs client."""
    with (
        patch("google.cloud.run_v2.ServicesClient"),
        patch("gcp_utils.controllers.cloud_run.JobsClient"),
    ):
        controller = CloudRunController(settings)
        assert controller.jobs_client is not None


def test_create_job_validation_error(cloud_run_controller):
    """Test creating a job with invalid parameters."""
    with pytest.raises(ValidationError) as exc_info:
        cloud_run_controller.create_job("", "gcr.io/test/image:latest")
    assert "Job name cannot be empty" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        cloud_run_controller.create_job("test-job", "")
    assert "Container image cannot be empty" in str(exc_info.value)


def test_create_job_success(cloud_run_controller):
    """Test creating a job successfully."""
    mock_operation = MagicMock()
    mock_job = create_mock_job()
    mock_operation.result.return_value = mock_job
    cloud_run_controller.jobs_client.create_job.return_value = mock_operation

    # Patch the protobuf classes
    with (
        patch("gcp_utils.controllers.cloud_run.run_v2.Container"),
        patch("gcp_utils.controllers.cloud_run.run_v2.ResourceRequirements"),
        patch("gcp_utils.controllers.cloud_run.run_v2.TaskTemplate"),
        patch("gcp_utils.controllers.cloud_run.run_v2.ExecutionTemplate"),
        patch("gcp_utils.controllers.cloud_run.run_v2.Job"),
        patch("gcp_utils.controllers.cloud_run.run_v2.CreateJobRequest"),
    ):
        job = cloud_run_controller.create_job(
            job_name="test-job",
            image="gcr.io/test/batch-job:latest",
            task_count=10,
            parallelism=3,
            env_vars={"BATCH_SIZE": "100"},
        )

        assert job.name == "test-job"
        assert job.task_count == 1
        cloud_run_controller.jobs_client.create_job.assert_called_once()


def test_get_job_success(cloud_run_controller):
    """Test getting a job successfully."""
    mock_job = create_mock_job()
    cloud_run_controller.jobs_client.get_job.return_value = mock_job

    job = cloud_run_controller.get_job("test-job")

    assert job.name == "test-job"
    assert job.image == "gcr.io/test/batch-job:latest"
    assert job.task_count == 1
    assert job.parallelism == 1


def test_get_job_not_found(cloud_run_controller):
    """Test getting a non-existent job."""
    cloud_run_controller.jobs_client.get_job.side_effect = Exception("404 Not Found")

    with pytest.raises(ResourceNotFoundError) as exc_info:
        cloud_run_controller.get_job("non-existent-job")
    assert "Job 'non-existent-job' not found" in str(exc_info.value)


def test_list_jobs(cloud_run_controller):
    """Test listing jobs."""
    mock_job = create_mock_job()
    cloud_run_controller.jobs_client.list_jobs.return_value = [mock_job]

    jobs = cloud_run_controller.list_jobs()

    assert len(jobs) == 1
    assert jobs[0].name == "test-job"
    assert jobs[0].image == "gcr.io/test/batch-job:latest"


def test_list_jobs_empty(cloud_run_controller):
    """Test listing jobs when none exist."""
    cloud_run_controller.jobs_client.list_jobs.return_value = []

    jobs = cloud_run_controller.list_jobs()

    assert len(jobs) == 0


def test_update_job_success(cloud_run_controller):
    """Test updating a job successfully."""
    mock_job = create_mock_job(image="gcr.io/test/old-image:latest")
    cloud_run_controller.jobs_client.get_job.return_value = mock_job

    mock_operation = MagicMock()
    mock_updated_job = create_mock_job(
        image="gcr.io/test/new-image:latest", parallelism=5
    )
    mock_operation.result.return_value = mock_updated_job
    cloud_run_controller.jobs_client.update_job.return_value = mock_operation

    # Patch protobuf classes
    with (
        patch("gcp_utils.controllers.cloud_run.run_v2.UpdateJobRequest"),
        patch("gcp_utils.controllers.cloud_run.run_v2.ResourceRequirements"),
        patch("gcp_utils.controllers.cloud_run.run_v2.EnvVar"),
    ):
        job = cloud_run_controller.update_job(
            "test-job",
            image="gcr.io/test/new-image:latest",
            parallelism=5,
        )

        assert job.image == "gcr.io/test/new-image:latest"
        assert job.parallelism == 5
        cloud_run_controller.jobs_client.update_job.assert_called_once()


def test_update_job_not_found(cloud_run_controller):
    """Test updating a non-existent job."""
    cloud_run_controller.jobs_client.get_job.side_effect = Exception("404 Not Found")

    with pytest.raises(ResourceNotFoundError) as exc_info:
        cloud_run_controller.update_job("non-existent-job", parallelism=5)
    assert "Job 'non-existent-job' not found" in str(exc_info.value)


def test_delete_job_success(cloud_run_controller):
    """Test deleting a job successfully."""
    mock_operation = MagicMock()
    mock_operation.result.return_value = None
    cloud_run_controller.jobs_client.delete_job.return_value = mock_operation

    # Patch protobuf classes
    with patch("gcp_utils.controllers.cloud_run.run_v2.DeleteJobRequest"):
        cloud_run_controller.delete_job("test-job")
        cloud_run_controller.jobs_client.delete_job.assert_called_once()


def test_delete_job_failure(cloud_run_controller):
    """Test deleting a job with failure."""
    cloud_run_controller.jobs_client.delete_job.side_effect = Exception("Delete failed")

    with pytest.raises(CloudRunError) as exc_info:
        cloud_run_controller.delete_job("test-job")
    assert "Failed to delete job 'test-job'" in str(exc_info.value)


def test_run_job_success(cloud_run_controller):
    """Test running a job successfully."""
    mock_operation = MagicMock()
    mock_execution = create_mock_execution()
    mock_operation.result.return_value = mock_execution
    cloud_run_controller.jobs_client.run_job.return_value = mock_operation

    # Patch protobuf classes
    with patch("gcp_utils.controllers.cloud_run.run_v2.RunJobRequest"):
        execution = cloud_run_controller.run_job("test-job")

        assert execution.execution_id == "test-execution-abc123"
        assert execution.job_name == "test-job"
        assert execution.status == ExecutionStatus.SUCCEEDED
        cloud_run_controller.jobs_client.run_job.assert_called_once()


def test_run_job_not_found(cloud_run_controller):
    """Test running a non-existent job."""
    cloud_run_controller.jobs_client.run_job.side_effect = Exception("404 Not Found")

    with pytest.raises(ResourceNotFoundError) as exc_info:
        cloud_run_controller.run_job("non-existent-job")
    assert "Job 'non-existent-job' not found" in str(exc_info.value)


def test_get_execution_success(cloud_run_controller):
    """Test getting an execution successfully."""
    mock_execution = create_mock_execution()
    cloud_run_controller.jobs_client.get_execution.return_value = mock_execution

    execution = cloud_run_controller.get_execution("test-job", "test-execution-abc123")

    assert execution.execution_id == "test-execution-abc123"
    assert execution.job_name == "test-job"
    assert execution.task_count == 5
    assert execution.succeeded_count == 5
    assert execution.failed_count == 0


def test_get_execution_with_full_path(cloud_run_controller):
    """Test getting an execution with full resource path."""
    mock_execution = create_mock_execution()
    cloud_run_controller.jobs_client.get_execution.return_value = mock_execution

    full_path = "projects/test-project/locations/us-central1/jobs/test-job/executions/test-execution-abc123"
    execution = cloud_run_controller.get_execution("test-job", full_path)

    assert execution.execution_id == "test-execution-abc123"


def test_get_execution_not_found(cloud_run_controller):
    """Test getting a non-existent execution."""
    cloud_run_controller.jobs_client.get_execution.side_effect = Exception(
        "404 Not Found"
    )

    with pytest.raises(ResourceNotFoundError) as exc_info:
        cloud_run_controller.get_execution("test-job", "non-existent-execution")
    assert "Execution 'non-existent-execution' not found" in str(exc_info.value)


def test_list_executions(cloud_run_controller):
    """Test listing executions for a job."""
    mock_execution1 = create_mock_execution(name="execution-1", succeeded_count=5)
    mock_execution2 = create_mock_execution(
        name="execution-2", succeeded_count=3, failed_count=2
    )
    cloud_run_controller.jobs_client.list_executions.return_value = [
        mock_execution1,
        mock_execution2,
    ]

    executions = cloud_run_controller.list_executions("test-job")

    assert len(executions) == 2
    assert executions[0].execution_id == "execution-1"
    assert executions[0].succeeded_count == 5
    assert executions[1].execution_id == "execution-2"
    assert executions[1].failed_count == 2


def test_list_executions_empty(cloud_run_controller):
    """Test listing executions when none exist."""
    cloud_run_controller.jobs_client.list_executions.return_value = []

    executions = cloud_run_controller.list_executions("test-job")

    assert len(executions) == 0


def test_cancel_execution_success(cloud_run_controller):
    """Test cancelling an execution successfully."""
    mock_operation = MagicMock()
    mock_execution = create_mock_execution()
    mock_execution.cancelled_count = 5
    mock_operation.result.return_value = mock_execution
    cloud_run_controller.jobs_client.cancel_execution.return_value = mock_operation

    # Patch protobuf classes
    with patch("gcp_utils.controllers.cloud_run.run_v2.CancelExecutionRequest"):
        execution = cloud_run_controller.cancel_execution(
            "test-job", "test-execution-abc123"
        )

        assert execution.execution_id == "test-execution-abc123"
        assert execution.status == ExecutionStatus.CANCELLED
        cloud_run_controller.jobs_client.cancel_execution.assert_called_once()


def test_cancel_execution_not_found(cloud_run_controller):
    """Test cancelling a non-existent execution."""
    cloud_run_controller.jobs_client.cancel_execution.side_effect = Exception(
        "404 Not Found"
    )

    with pytest.raises(ResourceNotFoundError) as exc_info:
        cloud_run_controller.cancel_execution("test-job", "non-existent-execution")
    assert "Execution 'non-existent-execution' not found" in str(exc_info.value)


def test_execution_status_determination():
    """Test execution status is correctly determined from task counts."""
    # Test SUCCEEDED status
    exec_succeeded = create_mock_execution(
        task_count=5, succeeded_count=5, failed_count=0
    )
    assert exec_succeeded.succeeded_count == exec_succeeded.task_count

    # Test FAILED status
    exec_failed = create_mock_execution(task_count=5, succeeded_count=3, failed_count=2)
    assert exec_failed.failed_count > 0

    # Test RUNNING status
    exec_running = create_mock_execution(
        task_count=5, succeeded_count=2, failed_count=0
    )
    exec_running.running_count = 3
    assert exec_running.running_count > 0


def test_job_path_construction(cloud_run_controller):
    """Test job resource path construction."""
    path = cloud_run_controller._get_job_path("my-job")
    expected = "projects/test-project/locations/us-central1/jobs/my-job"
    assert path == expected


def test_execution_path_construction(cloud_run_controller):
    """Test execution resource path construction."""
    path = cloud_run_controller._get_execution_path("my-job", "execution-123")
    expected = "projects/test-project/locations/us-central1/jobs/my-job/executions/execution-123"
    assert path == expected
