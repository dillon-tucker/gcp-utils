"""
Cloud Tasks controller for task queue management.

This module provides a high-level interface for creating and managing
Cloud Tasks queues and tasks for asynchronous workloads.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Optional

from google.cloud import tasks_v2
from google.auth.credentials import Credentials
from google.protobuf import timestamp_pb2

from ..config import GCPSettings, get_settings
from ..exceptions import CloudTasksError, ResourceNotFoundError, ValidationError
from ..models.tasks import CloudTask, TaskInfo, TaskSchedule


class CloudTasksController:
    """
    Controller for Google Cloud Tasks operations.

    This controller provides methods for managing task queues and creating tasks.

    Example:
        >>> from gcp_utils.controllers import CloudTasksController
        >>>
        >>> # Automatically loads from .env file
        >>> tasks_ctrl = CloudTasksController()
        >>>
        >>> # Create a task
        >>> task = tasks_ctrl.create_http_task(
        ...     queue="my-queue",
        ...     url="https://myservice.com/task-handler",
        ...     payload={"data": "value"},
        ...     delay_seconds=60
        ... )
    """

    def __init__(
        self,
        settings: Optional[GCPSettings] = None,
        credentials: Optional[Credentials] = None,
        location: Optional[str] = None,
    ) -> None:
        """
        Initialize the Cloud Tasks controller.

        Args:
            settings: GCP configuration settings. If not provided, loads from environment/.env file.
            credentials: Optional custom credentials
            location: Cloud Tasks location (defaults to settings.cloud_tasks_location)

        Raises:
            CloudTasksError: If client initialization fails
        """
        self.settings = settings or get_settings()
        self.location = location or self.settings.cloud_tasks_location

        try:
            self.client = tasks_v2.CloudTasksClient(credentials=credentials)
        except Exception as e:
            raise CloudTasksError(
                f"Failed to initialize Cloud Tasks client: {e}",
                details={"error": str(e)},
            )

    def create_queue(
        self,
        queue_name: str,
        max_concurrent_dispatches: Optional[int] = None,
        max_dispatches_per_second: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Create a new task queue.

        Args:
            queue_name: Name of the queue
            max_concurrent_dispatches: Maximum concurrent task dispatches
            max_dispatches_per_second: Maximum dispatches per second

        Returns:
            Dictionary with queue information

        Raises:
            ValidationError: If parameters are invalid
            CloudTasksError: If creation fails
        """
        if not queue_name:
            raise ValidationError("Queue name cannot be empty")

        try:
            parent = f"projects/{self.settings.project_id}/locations/{self.location}"

            queue = tasks_v2.Queue(name=f"{parent}/queues/{queue_name}")

            # Configure rate limits
            if max_concurrent_dispatches or max_dispatches_per_second:
                rate_limits = tasks_v2.RateLimits()
                if max_concurrent_dispatches:
                    rate_limits.max_concurrent_dispatches = max_concurrent_dispatches
                if max_dispatches_per_second:
                    rate_limits.max_dispatches_per_second = max_dispatches_per_second
                queue.rate_limits = rate_limits

            request = tasks_v2.CreateQueueRequest(
                parent=parent,
                queue=queue,
            )

            created_queue = self.client.create_queue(request=request)

            return self._queue_to_dict(created_queue)

        except ValidationError:
            raise
        except Exception as e:
            raise CloudTasksError(
                f"Failed to create queue '{queue_name}': {e}",
                details={"queue": queue_name, "error": str(e)},
            )

    def get_queue(self, queue_name: str) -> dict[str, Any]:
        """
        Get queue information.

        Args:
            queue_name: Name of the queue

        Returns:
            Dictionary with queue information

        Raises:
            ResourceNotFoundError: If queue doesn't exist
            CloudTasksError: If operation fails
        """
        try:
            queue_path = self._get_queue_path(queue_name)
            queue = self.client.get_queue(name=queue_path)

            return self._queue_to_dict(queue)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Queue '{queue_name}' not found",
                    details={"queue": queue_name},
                )
            raise CloudTasksError(
                f"Failed to get queue '{queue_name}': {e}",
                details={"queue": queue_name, "error": str(e)},
            )

    def list_queues(self) -> list[dict[str, Any]]:
        """
        List all queues in the location.

        Returns:
            List of queue dictionaries

        Raises:
            CloudTasksError: If listing fails
        """
        try:
            parent = f"projects/{self.settings.project_id}/locations/{self.location}"
            queues = self.client.list_queues(parent=parent)

            return [self._queue_to_dict(queue) for queue in queues]

        except Exception as e:
            raise CloudTasksError(
                f"Failed to list queues: {e}",
                details={"error": str(e)},
            )

    def delete_queue(self, queue_name: str) -> None:
        """
        Delete a queue.

        Args:
            queue_name: Name of the queue to delete

        Raises:
            CloudTasksError: If deletion fails
        """
        try:
            queue_path = self._get_queue_path(queue_name)
            self.client.delete_queue(name=queue_path)

        except Exception as e:
            raise CloudTasksError(
                f"Failed to delete queue '{queue_name}': {e}",
                details={"queue": queue_name, "error": str(e)},
            )

    def pause_queue(self, queue_name: str) -> dict[str, Any]:
        """
        Pause a queue (stop dispatching tasks).

        Args:
            queue_name: Name of the queue to pause

        Returns:
            Updated queue information

        Raises:
            CloudTasksError: If operation fails
        """
        try:
            queue_path = self._get_queue_path(queue_name)
            queue = self.client.pause_queue(name=queue_path)

            return self._queue_to_dict(queue)

        except Exception as e:
            raise CloudTasksError(
                f"Failed to pause queue '{queue_name}': {e}",
                details={"queue": queue_name, "error": str(e)},
            )

    def resume_queue(self, queue_name: str) -> dict[str, Any]:
        """
        Resume a paused queue.

        Args:
            queue_name: Name of the queue to resume

        Returns:
            Updated queue information

        Raises:
            CloudTasksError: If operation fails
        """
        try:
            queue_path = self._get_queue_path(queue_name)
            queue = self.client.resume_queue(name=queue_path)

            return self._queue_to_dict(queue)

        except Exception as e:
            raise CloudTasksError(
                f"Failed to resume queue '{queue_name}': {e}",
                details={"queue": queue_name, "error": str(e)},
            )

    def create_http_task(
        self,
        queue: str,
        url: str,
        payload: Optional[dict[str, Any] | str | bytes] = None,
        method: str = "POST",
        headers: Optional[dict[str, str]] = None,
        schedule_time: Optional[datetime] = None,
        delay_seconds: Optional[int] = None,
        task_name: Optional[str] = None,
        oidc_token: Optional[dict[str, str]] = None,
    ) -> TaskInfo:
        """
        Create an HTTP task.

        Args:
            queue: Queue name
            url: Target URL for the task
            payload: Task payload (dict, string, or bytes)
            method: HTTP method (POST, GET, etc.)
            headers: HTTP headers
            schedule_time: Specific time to execute the task
            delay_seconds: Delay in seconds before executing (alternative to schedule_time)
            task_name: Optional task name (auto-generated if not provided)
            oidc_token: Optional OIDC token configuration with 'service_account_email' and optional 'audience'

        Returns:
            TaskInfo object

        Raises:
            ValidationError: If parameters are invalid
            CloudTasksError: If task creation fails
        """
        if not url:
            raise ValidationError("URL cannot be empty")

        if schedule_time and delay_seconds:
            raise ValidationError(
                "Cannot specify both schedule_time and delay_seconds"
            )

        try:
            queue_path = self._get_queue_path(queue)

            # Build HTTP request
            http_request = tasks_v2.HttpRequest(
                url=url,
                http_method=method,
                headers=headers or {},
            )

            # Add OIDC token if provided
            if oidc_token:
                service_account_email = oidc_token.get("service_account_email")
                if not service_account_email:
                    raise ValidationError(
                        "oidc_token must include 'service_account_email'"
                    )
                http_request.oidc_token = tasks_v2.OidcToken(
                    service_account_email=service_account_email,
                    audience=oidc_token.get("audience", url),
                )

            # Set payload
            if payload is not None:
                if isinstance(payload, dict):
                    http_request.body = json.dumps(payload).encode()
                    if "Content-Type" not in http_request.headers:
                        http_request.headers["Content-Type"] = "application/json"
                elif isinstance(payload, str):
                    http_request.body = payload.encode()
                elif isinstance(payload, bytes):
                    http_request.body = payload

            # Build task
            task = tasks_v2.Task(http_request=http_request)

            # Set schedule time
            if schedule_time:
                timestamp = timestamp_pb2.Timestamp()
                timestamp.FromDatetime(schedule_time)
                task.schedule_time = timestamp
            elif delay_seconds:
                schedule_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
                timestamp = timestamp_pb2.Timestamp()
                timestamp.FromDatetime(schedule_time)
                task.schedule_time = timestamp

            # Set task name if provided
            if task_name:
                task.name = f"{queue_path}/tasks/{task_name}"

            # Create the task
            request = tasks_v2.CreateTaskRequest(
                parent=queue_path,
                task=task,
            )

            created_task = self.client.create_task(request=request)

            return self._task_to_info(created_task)

        except ValidationError:
            raise
        except Exception as e:
            raise CloudTasksError(
                f"Failed to create task in queue '{queue}': {e}",
                details={"queue": queue, "url": url, "error": str(e)},
            )

    def get_task(self, queue: str, task_name: str) -> TaskInfo:
        """
        Get task information.

        Args:
            queue: Queue name
            task_name: Task name/ID

        Returns:
            TaskInfo object

        Raises:
            ResourceNotFoundError: If task doesn't exist
            CloudTasksError: If operation fails
        """
        try:
            task_path = f"{self._get_queue_path(queue)}/tasks/{task_name}"
            task = self.client.get_task(name=task_path)

            return self._task_to_info(task)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Task '{task_name}' not found in queue '{queue}'",
                    details={"queue": queue, "task": task_name},
                )
            raise CloudTasksError(
                f"Failed to get task '{task_name}': {e}",
                details={"queue": queue, "task": task_name, "error": str(e)},
            )

    def list_tasks(
        self,
        queue: str,
        page_size: int = 100,
    ) -> list[TaskInfo]:
        """
        List tasks in a queue.

        Args:
            queue: Queue name
            page_size: Number of tasks to return

        Returns:
            List of TaskInfo objects

        Raises:
            CloudTasksError: If listing fails
        """
        try:
            queue_path = self._get_queue_path(queue)

            request = tasks_v2.ListTasksRequest(
                parent=queue_path,
                page_size=page_size,
            )

            tasks = self.client.list_tasks(request=request)

            return [self._task_to_info(task) for task in tasks]

        except Exception as e:
            raise CloudTasksError(
                f"Failed to list tasks in queue '{queue}': {e}",
                details={"queue": queue, "error": str(e)},
            )

    def delete_task(self, queue: str, task_name: str) -> None:
        """
        Delete a task.

        Args:
            queue: Queue name
            task_name: Task name/ID to delete

        Raises:
            CloudTasksError: If deletion fails
        """
        try:
            task_path = f"{self._get_queue_path(queue)}/tasks/{task_name}"
            self.client.delete_task(name=task_path)

        except Exception as e:
            raise CloudTasksError(
                f"Failed to delete task '{task_name}': {e}",
                details={"queue": queue, "task": task_name, "error": str(e)},
            )

    def purge_queue(self, queue_name: str) -> dict[str, Any]:
        """
        Purge all tasks from a queue.

        Args:
            queue_name: Name of the queue to purge

        Returns:
            Purged queue information

        Raises:
            CloudTasksError: If purge fails
        """
        try:
            queue_path = self._get_queue_path(queue_name)
            queue = self.client.purge_queue(name=queue_path)

            return self._queue_to_dict(queue)

        except Exception as e:
            raise CloudTasksError(
                f"Failed to purge queue '{queue_name}': {e}",
                details={"queue": queue_name, "error": str(e)},
            )

    def _get_queue_path(self, queue_name: str) -> str:
        """Get the full resource path for a queue."""
        return f"projects/{self.settings.project_id}/locations/{self.location}/queues/{queue_name}"

    def _queue_to_dict(self, queue: Any) -> dict[str, Any]:
        """Convert Queue to dictionary."""
        queue_name = queue.name.split("/")[-1]

        return {
            "name": queue_name,
            "full_name": queue.name,
            "state": str(queue.state) if hasattr(queue, "state") else "UNKNOWN",
            "rate_limits": {
                "max_dispatches_per_second": (
                    queue.rate_limits.max_dispatches_per_second
                    if hasattr(queue, "rate_limits")
                    and hasattr(queue.rate_limits, "max_dispatches_per_second")
                    else None
                ),
                "max_concurrent_dispatches": (
                    queue.rate_limits.max_concurrent_dispatches
                    if hasattr(queue, "rate_limits")
                    and hasattr(queue.rate_limits, "max_concurrent_dispatches")
                    else None
                ),
            }
            if hasattr(queue, "rate_limits")
            else {},
        }

    def _task_to_info(self, task: Any) -> TaskInfo:
        """Convert Task to TaskInfo model."""
        task_id = task.name.split("/")[-1]
        queue_name = task.name.split("/")[-3]

        schedule_time = None
        if hasattr(task, "schedule_time") and task.schedule_time:
            schedule_time = task.schedule_time.ToDatetime()

        return TaskInfo(
            name=task.name,
            task_id=task_id,
            queue_name=queue_name,
            schedule_time=schedule_time,
            dispatch_count=(
                task.dispatch_count if hasattr(task, "dispatch_count") else 0
            ),
            response_count=(
                task.response_count if hasattr(task, "response_count") else 0
            ),
        )
