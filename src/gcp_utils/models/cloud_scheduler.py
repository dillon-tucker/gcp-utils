"""
Pydantic models for Google Cloud Scheduler.

This module provides type-safe models for Cloud Scheduler resources including
jobs, schedules, HTTP targets, Pub/Sub targets, and App Engine targets.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class JobState(str, Enum):
    """Cloud Scheduler job state."""

    STATE_UNSPECIFIED = "STATE_UNSPECIFIED"
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"
    UPDATE_FAILED = "UPDATE_FAILED"


class HttpMethod(str, Enum):
    """HTTP methods for HTTP targets."""

    HTTP_METHOD_UNSPECIFIED = "HTTP_METHOD_UNSPECIFIED"
    POST = "POST"
    GET = "GET"
    HEAD = "HEAD"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"


class OAuthToken(BaseModel):
    """OAuth token configuration for HTTP target authentication."""

    service_account_email: str = Field(
        ..., description="Service account email for generating OAuth token"
    )
    scope: Optional[str] = Field(
        default=None, description="OAuth scope (optional)"
    )


class OidcToken(BaseModel):
    """OIDC token configuration for HTTP target authentication."""

    service_account_email: str = Field(
        ..., description="Service account email for generating OIDC token"
    )
    audience: Optional[str] = Field(
        default=None, description="OIDC audience claim (optional)"
    )


class HttpTarget(BaseModel):
    """HTTP target configuration for a Cloud Scheduler job."""

    uri: str = Field(..., description="HTTP URI to invoke")
    http_method: HttpMethod = Field(
        default=HttpMethod.POST, description="HTTP method to use"
    )
    headers: Optional[dict[str, str]] = Field(
        default=None, description="HTTP headers to include"
    )
    body: Optional[bytes] = Field(
        default=None, description="HTTP request body (for POST/PUT/PATCH)"
    )
    oauth_token: Optional[OAuthToken] = Field(
        default=None, description="OAuth token authentication (mutually exclusive with oidc_token)"
    )
    oidc_token: Optional[OidcToken] = Field(
        default=None, description="OIDC token authentication (mutually exclusive with oauth_token)"
    )


class PubsubTarget(BaseModel):
    """Pub/Sub target configuration for a Cloud Scheduler job."""

    topic_name: str = Field(..., description="Pub/Sub topic name (projects/{project}/topics/{topic})")
    data: Optional[bytes] = Field(
        default=None, description="Message data as bytes"
    )
    attributes: Optional[dict[str, str]] = Field(
        default=None, description="Message attributes"
    )


class AppEngineHttpTarget(BaseModel):
    """App Engine HTTP target configuration."""

    http_method: HttpMethod = Field(
        default=HttpMethod.POST, description="HTTP method to use"
    )
    app_engine_routing: Optional[dict[str, str]] = Field(
        default=None, description="App Engine routing configuration"
    )
    relative_uri: str = Field(..., description="Relative URI for App Engine app")
    headers: Optional[dict[str, str]] = Field(
        default=None, description="HTTP headers"
    )
    body: Optional[bytes] = Field(
        default=None, description="HTTP request body"
    )


class RetryConfig(BaseModel):
    """Retry configuration for a Cloud Scheduler job."""

    retry_count: Optional[int] = Field(
        default=None,
        description="Maximum number of retry attempts",
        ge=0,
        le=10,
    )
    max_retry_duration: Optional[str] = Field(
        default=None,
        description="Maximum retry duration (e.g., '3600s')",
    )
    min_backoff_duration: Optional[str] = Field(
        default=None,
        description="Minimum backoff duration between retries (e.g., '5s')",
    )
    max_backoff_duration: Optional[str] = Field(
        default=None,
        description="Maximum backoff duration between retries (e.g., '3600s')",
    )
    max_doublings: Optional[int] = Field(
        default=None,
        description="Maximum number of times to double the backoff",
        ge=0,
        le=16,
    )


class SchedulerJob(BaseModel):
    """Cloud Scheduler job model."""

    name: str = Field(..., description="Job resource name")
    description: Optional[str] = Field(
        default=None, description="Job description"
    )
    schedule: str = Field(
        ...,
        description="Job schedule in cron format (e.g., '0 9 * * 1' for 9 AM every Monday)",
    )
    time_zone: str = Field(
        default="America/Los_Angeles",
        description="IANA time zone (e.g., 'America/New_York', 'UTC')",
    )
    state: Optional[JobState] = Field(
        default=None, description="Job state"
    )
    http_target: Optional[HttpTarget] = Field(
        default=None, description="HTTP target configuration"
    )
    pubsub_target: Optional[PubsubTarget] = Field(
        default=None, description="Pub/Sub target configuration"
    )
    app_engine_http_target: Optional[AppEngineHttpTarget] = Field(
        default=None, description="App Engine HTTP target configuration"
    )
    retry_config: Optional[RetryConfig] = Field(
        default=None, description="Retry configuration"
    )
    attempt_deadline: Optional[str] = Field(
        default=None,
        description="Maximum time allowed for a single job execution (e.g., '180s')",
    )
    schedule_time: Optional[datetime] = Field(
        default=None, description="Time when the job is scheduled to run next"
    )
    last_attempt_time: Optional[datetime] = Field(
        default=None, description="Time of last job attempt"
    )
    user_update_time: Optional[datetime] = Field(
        default=None, description="Time when the job was last modified by a user"
    )


class JobListResponse(BaseModel):
    """Response model for listing Cloud Scheduler jobs."""

    jobs: list[SchedulerJob] = Field(
        default_factory=list, description="List of jobs"
    )
    next_page_token: Optional[str] = Field(
        default=None, description="Token for fetching the next page"
    )


class PauseJobResponse(BaseModel):
    """Response model for pausing a job."""

    name: str = Field(..., description="Job resource name")
    state: JobState = Field(..., description="Job state after pausing")


class ResumeJobResponse(BaseModel):
    """Response model for resuming a job."""

    name: str = Field(..., description="Job resource name")
    state: JobState = Field(..., description="Job state after resuming")


class RunJobResponse(BaseModel):
    """Response model for manually running a job."""

    name: str = Field(..., description="Job resource name")
    attempt_time: datetime = Field(..., description="Time when the job attempt started")
