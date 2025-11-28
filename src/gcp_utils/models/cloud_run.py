"""Data models for Cloud Run operations."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_serializer

if TYPE_CHECKING:
    from google.cloud.run_v2 import Execution, Job, Service


class TrafficTarget(BaseModel):
    """Traffic target for Cloud Run service."""

    revision_name: str | None = Field(None, description="Revision name")
    percent: int = Field(..., description="Traffic percentage", ge=0, le=100)
    tag: str | None = Field(None, description="Traffic tag")
    latest_revision: bool = Field(
        default=False, description="Whether to target latest revision"
    )


class ServiceRevision(BaseModel):
    """Cloud Run service revision information."""

    name: str = Field(..., description="Revision name")
    service_name: str = Field(..., description="Service name")
    image: str = Field(..., description="Container image")
    created: datetime | None = Field(None, description="Creation timestamp")
    traffic_percent: int = Field(default=0, description="Percentage of traffic")
    max_instances: int | None = Field(None, description="Maximum number of instances")
    min_instances: int | None = Field(None, description="Minimum number of instances")
    timeout: int | None = Field(None, description="Request timeout in seconds")

    @field_serializer("created")
    def serialize_dt(self, dt: datetime | None, _info: Any) -> str | None:
        return dt.isoformat() if dt else None


class CloudRunService(BaseModel):
    """
    Cloud Run service information with native object binding.

    This model wraps the Google Cloud Run Service object, providing both
    structured Pydantic data and access to the full Cloud Run API
    via `_service_object`.

    Example:
        >>> service = run_ctrl.get_service("my-service")
        >>>
        >>> # Use Pydantic fields
        >>> print(f"URL: {service.url}")
        >>>
        >>> # Use convenience methods
        >>> service.delete()
        >>> url = service.get_url()
    """

    name: str = Field(..., description="Service name")
    region: str = Field(..., description="Service region")
    image: str = Field(..., description="Current container image")
    url: str = Field(..., description="Service URL")
    created: datetime | None = Field(None, description="Creation timestamp")
    updated: datetime | None = Field(None, description="Last update timestamp")
    latest_revision: str | None = Field(None, description="Latest revision name")
    traffic: list[TrafficTarget] = Field(
        default_factory=list, description="Traffic split configuration"
    )
    labels: dict[str, str] = Field(default_factory=dict, description="Service labels")

    # The actual Service object (private attribute, not serialized)
    _service_object: Optional["Service"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("created", "updated")
    def serialize_dt(self, dt: datetime | None, _info: Any) -> str | None:
        return dt.isoformat() if dt else None

    # Convenience methods that delegate to controller operations

    def delete(self) -> None:
        """
        Delete this Cloud Run service.

        Raises:
            ValueError: If no Service object is bound

        Note:
            This requires access to the controller. Consider using
            CloudRunController.delete_service() directly instead.
        """
        if not self._service_object:
            raise ValueError("No Service object bound to this CloudRunService")
        raise NotImplementedError(
            "Service deletion must be performed via CloudRunController.delete_service()"
        )

    def get_url(self) -> str:
        """
        Get the service URL.

        Returns:
            Service URL

        Raises:
            ValueError: If no Service object is bound
        """
        if not self._service_object:
            raise ValueError("No Service object bound to this CloudRunService")
        return self.url


# Cloud Run Jobs Models


class ExecutionEnvironment(str, Enum):
    """Execution environment for Cloud Run jobs."""

    EXECUTION_ENVIRONMENT_UNSPECIFIED = "EXECUTION_ENVIRONMENT_UNSPECIFIED"
    EXECUTION_ENVIRONMENT_GEN1 = "EXECUTION_ENVIRONMENT_GEN1"
    EXECUTION_ENVIRONMENT_GEN2 = "EXECUTION_ENVIRONMENT_GEN2"


class ExecutionStatus(str, Enum):
    """Status of a Cloud Run job execution."""

    STATUS_UNSPECIFIED = "STATUS_UNSPECIFIED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"


class LaunchStage(str, Enum):
    """Launch stage for Cloud Run jobs."""

    LAUNCH_STAGE_UNSPECIFIED = "LAUNCH_STAGE_UNSPECIFIED"
    UNIMPLEMENTED = "UNIMPLEMENTED"
    PRELAUNCH = "PRELAUNCH"
    EARLY_ACCESS = "EARLY_ACCESS"
    ALPHA = "ALPHA"
    BETA = "BETA"
    GA = "GA"
    DEPRECATED = "DEPRECATED"


class TaskAttemptResult(BaseModel):
    """Result of a task attempt in a job execution."""

    status: ExecutionStatus = Field(..., description="Status of the task attempt")
    exit_code: int | None = Field(None, description="Exit code of the task")
    error_message: str | None = Field(None, description="Error message if failed")


class CloudRunJob(BaseModel):
    """
    Cloud Run job information with native object binding.

    This model wraps the Google Cloud Run Job object, providing both
    structured Pydantic data and access to the full Cloud Run API
    via `_job_object`.

    Example:
        >>> job = run_ctrl.get_job("my-batch-job")
        >>>
        >>> # Use Pydantic fields
        >>> print(f"Parallelism: {job.parallelism}")
        >>>
        >>> # Access native object
        >>> print(job._job_object.uid)
    """

    name: str = Field(..., description="Job name")
    region: str = Field(..., description="Job region")
    image: str = Field(..., description="Container image")
    created: datetime | None = Field(None, description="Creation timestamp")
    updated: datetime | None = Field(None, description="Last update timestamp")
    labels: dict[str, str] = Field(default_factory=dict, description="Job labels")

    # Execution configuration
    task_count: int = Field(default=1, description="Number of tasks to create")
    parallelism: int = Field(
        default=1, description="Number of tasks to run in parallel"
    )
    max_retries: int = Field(
        default=3, description="Maximum number of retries per task"
    )
    timeout: int | None = Field(None, description="Task timeout in seconds")

    # Resource configuration
    cpu: str | None = Field(None, description="CPU allocation (e.g., '1000m')")
    memory: str | None = Field(None, description="Memory allocation (e.g., '512Mi')")

    # Environment configuration
    env_vars: dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    service_account: str | None = Field(None, description="Service account email")
    execution_environment: ExecutionEnvironment = Field(
        default=ExecutionEnvironment.EXECUTION_ENVIRONMENT_GEN2,
        description="Execution environment",
    )

    # Status
    latest_execution: str | None = Field(
        None, description="Name of the latest execution"
    )
    execution_count: int = Field(default=0, description="Total number of executions")
    launch_stage: LaunchStage = Field(
        default=LaunchStage.GA, description="Launch stage"
    )

    # The actual Job object (private attribute, not serialized)
    _job_object: Optional["Job"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("created", "updated")
    def serialize_dt(self, dt: datetime | None, _info: Any) -> str | None:
        return dt.isoformat() if dt else None


class JobExecution(BaseModel):
    """
    Cloud Run job execution information.

    Represents a single execution of a Cloud Run job, including its
    status, timing, and task-level details.

    Example:
        >>> execution = run_ctrl.get_execution("my-job", "my-execution-abc123")
        >>>
        >>> # Check execution status
        >>> if execution.status == ExecutionStatus.SUCCEEDED:
        >>>     print(f"Completed in {execution.duration_seconds}s")
    """

    name: str = Field(..., description="Execution name (full resource path)")
    execution_id: str = Field(..., description="Short execution ID")
    job_name: str = Field(..., description="Parent job name")
    region: str = Field(..., description="Execution region")

    # Status and timing
    status: ExecutionStatus = Field(..., description="Current execution status")
    created: datetime | None = Field(None, description="Creation timestamp")
    started: datetime | None = Field(None, description="Start timestamp")
    completed: datetime | None = Field(None, description="Completion timestamp")
    duration_seconds: int | None = Field(
        None, description="Execution duration in seconds"
    )

    # Task information
    task_count: int = Field(default=1, description="Total number of tasks")
    succeeded_count: int = Field(default=0, description="Number of succeeded tasks")
    failed_count: int = Field(default=0, description="Number of failed tasks")
    cancelled_count: int = Field(default=0, description="Number of cancelled tasks")
    running_count: int = Field(default=0, description="Number of running tasks")
    pending_count: int = Field(default=0, description="Number of pending tasks")

    # Configuration
    parallelism: int = Field(default=1, description="Maximum parallel tasks")
    labels: dict[str, str] = Field(default_factory=dict, description="Execution labels")

    # Error information
    error_message: str | None = Field(None, description="Error message if failed")

    # The actual Execution object (private attribute, not serialized)
    _execution_object: Optional["Execution"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("created", "started", "completed")
    def serialize_dt(self, dt: datetime | None, _info: Any) -> str | None:
        return dt.isoformat() if dt else None
