"""Data models for Cloud Tasks operations."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_serializer

if TYPE_CHECKING:
    from google.cloud.tasks_v2 import Task


class TaskSchedule(BaseModel):
    """Schedule configuration for a Cloud Task."""

    schedule_time: Optional[datetime] = Field(
        None, description="When to execute the task"
    )
    delay: Optional[timedelta] = Field(None, description="Delay before execution")

    @field_serializer("schedule_time")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None

    @field_serializer("delay")
    def serialize_td(self, td: Optional[timedelta], _info: Any) -> Optional[float]:
        return td.total_seconds() if td else None


class CloudTask(BaseModel):
    """Cloud Task information."""

    name: str = Field(..., description="Task name")
    queue_name: str = Field(..., description="Queue name")
    http_method: str = Field(default="POST", description="HTTP method")
    url: str = Field(..., description="Target URL")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    body: Optional[bytes | str] = Field(None, description="Request body")
    schedule_time: Optional[datetime] = Field(None, description="Scheduled execution time")
    created: Optional[datetime] = Field(None, description="Task creation time")

    @field_serializer("schedule_time", "created")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None


class TaskInfo(BaseModel):
    """
    Information about a created task with native object binding.

    This model wraps the Google Cloud Task object, providing both
    structured Pydantic data and access to the full Cloud Tasks API
    via `_task_object`.

    Example:
        >>> task = tasks_ctrl.create_http_task("my-queue", "https://example.com/handler")
        >>>
        >>> # Use Pydantic fields
        >>> print(f"Task ID: {task.task_id}")
        >>>
        >>> # Use convenience methods
        >>> task.delete()
        >>> task.run()
    """

    name: str = Field(..., description="Full task name/path")
    task_id: str = Field(..., description="Task ID")
    queue_name: str = Field(..., description="Queue name")
    schedule_time: Optional[datetime] = Field(None, description="Scheduled execution time")
    dispatch_count: int = Field(default=0, description="Number of dispatch attempts")
    response_count: int = Field(default=0, description="Number of responses received")

    # The actual Task object (private attribute, not serialized)
    _task_object: Optional["Task"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("schedule_time")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None

    # Convenience methods that delegate to controller operations

    def delete(self) -> None:
        """
        Delete this task.

        Raises:
            ValueError: If no Task object is bound

        Note:
            This requires access to the controller. Consider using
            CloudTasksController.delete_task() directly instead.
        """
        if not self._task_object:
            raise ValueError("No Task object bound to this TaskInfo")
        raise NotImplementedError(
            "Task deletion must be performed via CloudTasksController.delete_task()"
        )

    def run(self) -> None:
        """
        Force this task to run immediately.

        Raises:
            ValueError: If no Task object is bound

        Note:
            This requires access to the controller. Consider using
            CloudTasksController.run_task() directly instead.
        """
        if not self._task_object:
            raise ValueError("No Task object bound to this TaskInfo")
        raise NotImplementedError(
            "Task immediate execution must be performed via CloudTasksController.run_task()"
        )
