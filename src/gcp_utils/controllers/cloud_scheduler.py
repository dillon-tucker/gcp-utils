"""
Google Cloud Scheduler controller for managing cron jobs.

This module provides a type-safe controller for creating and managing
Cloud Scheduler jobs with HTTP, Pub/Sub, and App Engine targets.
"""


from google.api_core.exceptions import GoogleAPIError
from google.auth.credentials import Credentials
from google.cloud import scheduler_v1  # type: ignore[attr-defined]
from google.cloud.scheduler_v1.types import (
    CreateJobRequest,
    DeleteJobRequest,
    GetJobRequest,
    Job,
    ListJobsRequest,
    PauseJobRequest,
    ResumeJobRequest,
    RunJobRequest,
    UpdateJobRequest,
)

from ..config import GCPSettings, get_settings
from ..exceptions import CloudSchedulerError, ResourceNotFoundError
from ..models.cloud_scheduler import (
    JobListResponse,
    JobState,
    PauseJobResponse,
    ResumeJobResponse,
    RunJobResponse,
    SchedulerJob,
)


class CloudSchedulerController:
    """
    Controller for managing Google Cloud Scheduler jobs.

    Provides methods for creating, updating, deleting, and managing scheduled jobs
    with support for HTTP, Pub/Sub, and App Engine targets.

    Example:
        ```python
        from gcp_utils.controllers import CloudSchedulerController

        # Controller auto-loads settings from .env file
        scheduler = CloudSchedulerController()

        # Create an HTTP job that runs every day at 9 AM
        job = scheduler.create_http_job(
            job_id="daily-backup",
            schedule="0 9 * * *",
            uri="https://example.com/api/backup",
            http_method="POST",
            time_zone="America/New_York",
        )

        # Run a job immediately (for testing)
        scheduler.run_job("daily-backup")
        ```
    """

    def __init__(
        self,
        settings: GCPSettings | None = None,
        credentials: Credentials | None = None,
    ) -> None:
        """
        Initialize the Cloud Scheduler controller.

        Args:
            settings: GCP configuration. If not provided, loads from environment/.env file.
            credentials: Optional custom credentials.
        """
        self._settings = settings or get_settings()
        self._credentials = credentials
        self._client: scheduler_v1.CloudSchedulerClient | None = None

    def _get_client(self) -> scheduler_v1.CloudSchedulerClient:
        """Lazy initialization of the Cloud Scheduler client."""
        if self._client is None:
            self._client = scheduler_v1.CloudSchedulerClient(
                credentials=self._credentials
            )
        return self._client

    def _job_to_model(self, job: Job) -> SchedulerJob:
        """Convert a Job proto to SchedulerJob model."""
        return SchedulerJob(
            name=job.name,
            description=job.description or None,
            schedule=job.schedule,
            time_zone=job.time_zone,
            state=job.state.name if job.state else None,
            schedule_time=job.schedule_time,
            last_attempt_time=job.last_attempt_time,
            user_update_time=job.user_update_time,
        )

    def create_job(
        self,
        job_id: str,
        schedule: str,
        location: str | None = None,
        time_zone: str | None = None,
        http_target: dict | None = None,
        pubsub_target: dict | None = None,
        app_engine_http_target: dict | None = None,
        retry_config: dict | None = None,
        description: str | None = None,
        attempt_deadline: str | None = None,
    ) -> SchedulerJob:
        """
        Create a new Cloud Scheduler job.

        Args:
            job_id: Job ID (name)
            schedule: Cron schedule (e.g., '0 9 * * *' for 9 AM daily)
            location: GCP region (defaults to settings.cloud_scheduler_location)
            time_zone: IANA time zone (defaults to settings.cloud_scheduler_timezone)
            http_target: HTTP target configuration dictionary
            pubsub_target: Pub/Sub target configuration dictionary
            app_engine_http_target: App Engine HTTP target configuration dictionary
            retry_config: Retry configuration dictionary
            description: Job description
            attempt_deadline: Maximum execution time (e.g., '180s')

        Returns:
            SchedulerJob model containing the created job details

        Raises:
            CloudSchedulerError: If job creation fails

        Example:
            ```python
            # Create HTTP job
            http_target = {
                "uri": "https://example.com/api/task",
                "http_method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": b'{"key": "value"}',
            }

            job = scheduler.create_job(
                job_id="my-job",
                schedule="*/15 * * * *",  # Every 15 minutes
                http_target=http_target,
                time_zone="UTC",
            )
            ```
        """
        try:
            client = self._get_client()
            region = location or self._settings.cloud_scheduler_location
            parent = f"projects/{self._settings.project_id}/locations/{region}"
            job_name = f"{parent}/jobs/{job_id}"

            job = Job(
                name=job_name,
                schedule=schedule,
                time_zone=time_zone or self._settings.cloud_scheduler_timezone,
                description=description or "",
            )

            if http_target:
                job.http_target = http_target

            if pubsub_target:
                job.pubsub_target = pubsub_target

            if app_engine_http_target:
                job.app_engine_http_target = app_engine_http_target

            if retry_config:
                job.retry_config = retry_config

            if attempt_deadline:
                from google.protobuf import duration_pb2

                # Parse duration string (e.g., "180s")
                seconds = int(attempt_deadline.rstrip("s"))
                job.attempt_deadline = duration_pb2.Duration(seconds=seconds)

            request = CreateJobRequest(parent=parent, job=job)
            result = client.create_job(request=request)

            return self._job_to_model(result)

        except GoogleAPIError as e:
            raise CloudSchedulerError(
                message=f"Failed to create job '{job_id}': {str(e)}",
                details={
                    "job_id": job_id,
                    "location": location,
                    "schedule": schedule,
                    "error": str(e),
                },
            ) from e

    def create_http_job(
        self,
        job_id: str,
        schedule: str,
        uri: str,
        http_method: str = "POST",
        location: str | None = None,
        time_zone: str | None = None,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
        oauth_service_account: str | None = None,
        oidc_service_account: str | None = None,
        description: str | None = None,
    ) -> SchedulerJob:
        """
        Create a Cloud Scheduler job with an HTTP target.

        This is a convenience method for creating HTTP-triggered jobs.

        Args:
            job_id: Job ID
            schedule: Cron schedule
            uri: HTTP URI to invoke
            http_method: HTTP method (default: POST)
            location: GCP region
            time_zone: IANA time zone
            headers: HTTP headers
            body: Request body (for POST/PUT/PATCH)
            oauth_service_account: Service account email for OAuth token auth
            oidc_service_account: Service account email for OIDC token auth
            description: Job description

        Returns:
            SchedulerJob model

        Raises:
            CloudSchedulerError: If job creation fails

        Example:
            ```python
            job = scheduler.create_http_job(
                job_id="notify-users",
                schedule="0 9 * * *",  # 9 AM daily
                uri="https://api.example.com/notify",
                http_method="POST",
                headers={"Authorization": "Bearer token"},
                time_zone="America/New_York",
            )
            ```
        """
        http_target: dict = {
            "uri": uri,
            "http_method": http_method,
        }

        if headers:
            http_target["headers"] = headers

        if body:
            http_target["body"] = body

        if oauth_service_account:
            http_target["oauth_token"] = {
                "service_account_email": oauth_service_account
            }

        if oidc_service_account:
            http_target["oidc_token"] = {
                "service_account_email": oidc_service_account
            }

        return self.create_job(
            job_id=job_id,
            schedule=schedule,
            location=location,
            time_zone=time_zone,
            http_target=http_target,
            description=description,
        )

    def create_pubsub_job(
        self,
        job_id: str,
        schedule: str,
        topic_name: str,
        location: str | None = None,
        time_zone: str | None = None,
        data: bytes | None = None,
        attributes: dict[str, str] | None = None,
        description: str | None = None,
    ) -> SchedulerJob:
        """
        Create a Cloud Scheduler job with a Pub/Sub target.

        This is a convenience method for creating Pub/Sub-triggered jobs.

        Args:
            job_id: Job ID
            schedule: Cron schedule
            topic_name: Pub/Sub topic name (projects/{project}/topics/{topic})
            location: GCP region
            time_zone: IANA time zone
            data: Message data as bytes
            attributes: Message attributes
            description: Job description

        Returns:
            SchedulerJob model

        Raises:
            CloudSchedulerError: If job creation fails

        Example:
            ```python
            job = scheduler.create_pubsub_job(
                job_id="process-data",
                schedule="0 */6 * * *",  # Every 6 hours
                topic_name=f"projects/{project_id}/topics/data-processing",
                data=b'{"action": "process"}',
                attributes={"priority": "high"},
            )
            ```
        """
        # Ensure topic name is fully qualified
        if not topic_name.startswith("projects/"):
            topic_name = f"projects/{self._settings.project_id}/topics/{topic_name}"

        pubsub_target: dict = {"topic_name": topic_name}

        if data:
            pubsub_target["data"] = data

        if attributes:
            pubsub_target["attributes"] = attributes

        return self.create_job(
            job_id=job_id,
            schedule=schedule,
            location=location,
            time_zone=time_zone,
            pubsub_target=pubsub_target,
            description=description,
        )

    def get_job(self, job_id: str, location: str | None = None) -> SchedulerJob:
        """
        Get details about a Cloud Scheduler job.

        Args:
            job_id: Job ID
            location: GCP region (defaults to settings.cloud_scheduler_location)

        Returns:
            SchedulerJob model with job details

        Raises:
            ResourceNotFoundError: If job doesn't exist
            CloudSchedulerError: If retrieval fails

        Example:
            ```python
            job = scheduler.get_job("my-job")
            print(f"Schedule: {job.schedule}")
            print(f"State: {job.state}")
            ```
        """
        try:
            client = self._get_client()
            region = location or self._settings.cloud_scheduler_location
            name = f"projects/{self._settings.project_id}/locations/{region}/jobs/{job_id}"

            request = GetJobRequest(name=name)
            job = client.get_job(request=request)

            return self._job_to_model(job)

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Job '{job_id}' not found",
                    details={"job_id": job_id, "location": location},
                ) from e

            raise CloudSchedulerError(
                message=f"Failed to get job '{job_id}': {str(e)}",
                details={"job_id": job_id, "error": str(e)},
            ) from e

    def list_jobs(
        self,
        location: str | None = None,
        page_size: int = 100,
        page_token: str | None = None,
    ) -> JobListResponse:
        """
        List Cloud Scheduler jobs in a location.

        Args:
            location: GCP region (defaults to settings.cloud_scheduler_location)
            page_size: Maximum number of jobs to return
            page_token: Token from previous list call for pagination

        Returns:
            JobListResponse with list of jobs and pagination token

        Raises:
            CloudSchedulerError: If listing fails

        Example:
            ```python
            response = scheduler.list_jobs()
            for job in response.jobs:
                print(f"{job.name}: {job.schedule} ({job.state})")
            ```
        """
        try:
            client = self._get_client()
            region = location or self._settings.cloud_scheduler_location
            parent = f"projects/{self._settings.project_id}/locations/{region}"

            request = ListJobsRequest(
                parent=parent,
                page_size=page_size,
                page_token=page_token or "",
            )

            response = client.list_jobs(request=request)

            jobs = [self._job_to_model(job) for job in response.jobs]

            return JobListResponse(
                jobs=jobs,
                next_page_token=response.next_page_token or None,
            )

        except GoogleAPIError as e:
            raise CloudSchedulerError(
                message=f"Failed to list jobs: {str(e)}",
                details={"location": location, "error": str(e)},
            ) from e

    def update_job(
        self,
        job_id: str,
        location: str | None = None,
        schedule: str | None = None,
        time_zone: str | None = None,
        http_target: dict | None = None,
        pubsub_target: dict | None = None,
        description: str | None = None,
        update_mask: list[str] | None = None,
    ) -> SchedulerJob:
        """
        Update an existing Cloud Scheduler job.

        Args:
            job_id: Job ID
            location: GCP region
            schedule: Updated cron schedule
            time_zone: Updated time zone
            http_target: Updated HTTP target configuration
            pubsub_target: Updated Pub/Sub target configuration
            description: Updated description
            update_mask: Fields to update (if None, updates all provided fields)

        Returns:
            SchedulerJob model with updated job details

        Raises:
            ResourceNotFoundError: If job doesn't exist
            CloudSchedulerError: If update fails

        Example:
            ```python
            # Update schedule only
            job = scheduler.update_job(
                job_id="my-job",
                schedule="0 10 * * *",  # Change to 10 AM
                update_mask=["schedule"],
            )
            ```
        """
        try:
            client = self._get_client()
            region = location or self._settings.cloud_scheduler_location
            name = f"projects/{self._settings.project_id}/locations/{region}/jobs/{job_id}"

            job = Job(name=name)

            if schedule is not None:
                job.schedule = schedule

            if time_zone is not None:
                job.time_zone = time_zone

            if description is not None:
                job.description = description

            if http_target:
                job.http_target = http_target

            if pubsub_target:
                job.pubsub_target = pubsub_target

            request = UpdateJobRequest(job=job)

            if update_mask:
                from google.protobuf import field_mask_pb2

                request.update_mask = field_mask_pb2.FieldMask(paths=update_mask)

            result = client.update_job(request=request)

            return self._job_to_model(result)

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Job '{job_id}' not found",
                    details={"job_id": job_id, "location": location},
                ) from e

            raise CloudSchedulerError(
                message=f"Failed to update job '{job_id}': {str(e)}",
                details={"job_id": job_id, "error": str(e)},
            ) from e

    def delete_job(self, job_id: str, location: str | None = None) -> None:
        """
        Delete a Cloud Scheduler job.

        Args:
            job_id: Job ID
            location: GCP region (defaults to settings.cloud_scheduler_location)

        Raises:
            ResourceNotFoundError: If job doesn't exist
            CloudSchedulerError: If deletion fails

        Example:
            ```python
            scheduler.delete_job("my-job")
            ```
        """
        try:
            client = self._get_client()
            region = location or self._settings.cloud_scheduler_location
            name = f"projects/{self._settings.project_id}/locations/{region}/jobs/{job_id}"

            request = DeleteJobRequest(name=name)
            client.delete_job(request=request)

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Job '{job_id}' not found",
                    details={"job_id": job_id, "location": location},
                ) from e

            raise CloudSchedulerError(
                message=f"Failed to delete job '{job_id}': {str(e)}",
                details={"job_id": job_id, "error": str(e)},
            ) from e

    def pause_job(self, job_id: str, location: str | None = None) -> PauseJobResponse:
        """
        Pause a Cloud Scheduler job.

        Args:
            job_id: Job ID
            location: GCP region

        Returns:
            PauseJobResponse with job name and state

        Raises:
            ResourceNotFoundError: If job doesn't exist
            CloudSchedulerError: If pause operation fails

        Example:
            ```python
            response = scheduler.pause_job("my-job")
            print(f"Job paused: {response.state}")
            ```
        """
        try:
            client = self._get_client()
            region = location or self._settings.cloud_scheduler_location
            name = f"projects/{self._settings.project_id}/locations/{region}/jobs/{job_id}"

            request = PauseJobRequest(name=name)
            job = client.pause_job(request=request)

            return PauseJobResponse(
                name=job.name,
                state=JobState(job.state.name),
            )

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Job '{job_id}' not found",
                    details={"job_id": job_id, "location": location},
                ) from e

            raise CloudSchedulerError(
                message=f"Failed to pause job '{job_id}': {str(e)}",
                details={"job_id": job_id, "error": str(e)},
            ) from e

    def resume_job(self, job_id: str, location: str | None = None) -> ResumeJobResponse:
        """
        Resume a paused Cloud Scheduler job.

        Args:
            job_id: Job ID
            location: GCP region

        Returns:
            ResumeJobResponse with job name and state

        Raises:
            ResourceNotFoundError: If job doesn't exist
            CloudSchedulerError: If resume operation fails

        Example:
            ```python
            response = scheduler.resume_job("my-job")
            print(f"Job resumed: {response.state}")
            ```
        """
        try:
            client = self._get_client()
            region = location or self._settings.cloud_scheduler_location
            name = f"projects/{self._settings.project_id}/locations/{region}/jobs/{job_id}"

            request = ResumeJobRequest(name=name)
            job = client.resume_job(request=request)

            return ResumeJobResponse(
                name=job.name,
                state=JobState(job.state.name),
            )

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Job '{job_id}' not found",
                    details={"job_id": job_id, "location": location},
                ) from e

            raise CloudSchedulerError(
                message=f"Failed to resume job '{job_id}': {str(e)}",
                details={"job_id": job_id, "error": str(e)},
            ) from e

    def run_job(self, job_id: str, location: str | None = None) -> RunJobResponse:
        """
        Manually trigger a Cloud Scheduler job to run immediately.

        This is useful for testing jobs without waiting for the scheduled time.

        Args:
            job_id: Job ID
            location: GCP region

        Returns:
            RunJobResponse with job name and attempt time

        Raises:
            ResourceNotFoundError: If job doesn't exist
            CloudSchedulerError: If run operation fails

        Example:
            ```python
            response = scheduler.run_job("my-job")
            print(f"Job triggered at: {response.attempt_time}")
            ```
        """
        try:
            client = self._get_client()
            region = location or self._settings.cloud_scheduler_location
            name = f"projects/{self._settings.project_id}/locations/{region}/jobs/{job_id}"

            request = RunJobRequest(name=name)
            job = client.run_job(request=request)

            return RunJobResponse(
                name=job.name,
                attempt_time=job.last_attempt_time,
            )

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Job '{job_id}' not found",
                    details={"job_id": job_id, "location": location},
                ) from e

            raise CloudSchedulerError(
                message=f"Failed to run job '{job_id}': {str(e)}",
                details={"job_id": job_id, "error": str(e)},
            ) from e
