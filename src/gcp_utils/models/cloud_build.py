"""
Pydantic models for Google Cloud Build.

This module provides type-safe models for Cloud Build resources including
builds, build triggers, build steps, and source configurations.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BuildStatus(str, Enum):
    """Cloud Build status."""

    STATUS_UNKNOWN = "STATUS_UNKNOWN"
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    WORKING = "WORKING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class SubstitutionOption(str, Enum):
    """Substitution option for build configurations."""

    MUST_MATCH = "MUST_MATCH"
    ALLOW_LOOSE = "ALLOW_LOOSE"


class LogStreamingOption(str, Enum):
    """Log streaming option."""

    STREAM_DEFAULT = "STREAM_DEFAULT"
    STREAM_ON = "STREAM_ON"
    STREAM_OFF = "STREAM_OFF"


class LoggingMode(str, Enum):
    """Logging mode."""

    LOGGING_UNSPECIFIED = "LOGGING_UNSPECIFIED"
    LEGACY = "LEGACY"
    GCS_ONLY = "GCS_ONLY"
    STACKDRIVER_ONLY = "STACKDRIVER_ONLY"
    CLOUD_LOGGING_ONLY = "CLOUD_LOGGING_ONLY"
    NONE = "NONE"


class MachineType(str, Enum):
    """Machine type for build execution."""

    UNSPECIFIED = "UNSPECIFIED"
    N1_HIGHCPU_8 = "N1_HIGHCPU_8"
    N1_HIGHCPU_32 = "N1_HIGHCPU_32"
    E2_HIGHCPU_8 = "E2_HIGHCPU_8"
    E2_HIGHCPU_32 = "E2_HIGHCPU_32"
    E2_MEDIUM = "E2_MEDIUM"


class BuildStep(BaseModel):
    """A step in a Cloud Build."""

    name: str = Field(..., description="Docker image name (e.g., 'gcr.io/cloud-builders/docker')")
    args: list[str] | None = Field(
        default=None, description="Arguments to pass to the builder"
    )
    env: list[str] | None = Field(
        default=None, description="Environment variables (KEY=value format)"
    )
    dir: str | None = Field(
        default=None, description="Working directory for the step"
    )
    id: str | None = Field(
        default=None, description="Step ID (for dependencies)"
    )
    wait_for: list[str] | None = Field(
        default=None, description="Step IDs to wait for before running this step"
    )
    entrypoint: str | None = Field(
        default=None, description="Override entrypoint of the builder image"
    )
    secret_env: list[str] | None = Field(
        default=None, description="Secret environment variable names"
    )
    volumes: list[dict[str, str]] | None = Field(
        default=None, description="Volumes to mount"
    )
    timeout: str | None = Field(
        default=None, description="Step timeout (e.g., '300s')"
    )
    script: str | None = Field(
        default=None, description="Script to execute (alternative to args)"
    )


class StorageSource(BaseModel):
    """Source in Cloud Storage."""

    bucket: str = Field(..., description="GCS bucket name")
    object_: str = Field(..., description="GCS object path", alias="object")
    generation: int | None = Field(
        default=None, description="Object generation number"
    )


class RepoSource(BaseModel):
    """Source in Cloud Source Repositories."""

    project_id: str | None = Field(
        default=None, description="Project ID containing the repo"
    )
    repo_name: str = Field(..., description="Repository name")
    branch_name: str | None = Field(
        default=None, description="Branch name to build"
    )
    tag_name: str | None = Field(
        default=None, description="Tag name to build"
    )
    commit_sha: str | None = Field(
        default=None, description="Commit SHA to build"
    )
    dir: str | None = Field(
        default=None, description="Directory in the repository"
    )
    invert_regex: bool = Field(
        default=False, description="Invert the regex match"
    )


class GitHubEventsConfig(BaseModel):
    """GitHub events configuration for a trigger."""

    owner: str | None = Field(default=None, description="GitHub repository owner")
    name: str | None = Field(default=None, description="GitHub repository name")
    pull_request: dict[str, Any] | None = Field(
        default=None, description="Pull request trigger configuration"
    )
    push: dict[str, Any] | None = Field(
        default=None, description="Push trigger configuration"
    )


class Source(BaseModel):
    """Build source configuration."""

    storage_source: StorageSource | None = Field(
        default=None, description="Cloud Storage source"
    )
    repo_source: RepoSource | None = Field(
        default=None, description="Cloud Source Repository source"
    )


class BuildOptions(BaseModel):
    """Build execution options."""

    source_provenance_hash: list[str] | None = Field(
        default=None, description="Hash types to compute for source provenance"
    )
    requested_verify_option: str | None = Field(
        default=None, description="Verification option (VERIFIED, NOT_VERIFIED)"
    )
    machine_type: MachineType | None = Field(
        default=None, description="Machine type for build execution"
    )
    disk_size_gb: int | None = Field(
        default=None, description="Disk size in GB"
    )
    substitution_option: SubstitutionOption | None = Field(
        default=None, description="Substitution option"
    )
    dynamic_substitutions: bool | None = Field(
        default=None, description="Enable dynamic substitutions"
    )
    log_streaming_option: LogStreamingOption | None = Field(
        default=None, description="Log streaming option"
    )
    worker_pool: str | None = Field(
        default=None, description="Private worker pool resource name"
    )
    logging: LoggingMode | None = Field(
        default=None, description="Logging mode"
    )
    env: list[str] | None = Field(
        default=None, description="Global environment variables (KEY=value format)"
    )
    secret_env: list[str] | None = Field(
        default=None, description="Global secret environment variable names"
    )
    volumes: list[dict[str, str]] | None = Field(
        default=None, description="Global volumes to mount"
    )


class BuildResults(BaseModel):
    """Build execution results."""

    images: list[dict[str, str]] | None = Field(
        default=None, description="Container images that were built"
    )
    build_step_images: list[str] | None = Field(
        default=None, description="Digests of images built in each step"
    )
    artifact_manifest: str | None = Field(
        default=None, description="GCS path to artifact manifest"
    )
    num_artifacts: int | None = Field(
        default=None, description="Number of artifacts uploaded"
    )
    build_step_outputs: list[bytes] | None = Field(
        default=None, description="Output from build steps"
    )


class Build(BaseModel):
    """Cloud Build model."""

    id: str | None = Field(default=None, description="Build ID")
    project_id: str = Field(..., description="Project ID")
    status: BuildStatus | None = Field(default=None, description="Build status")
    source: Source | None = Field(default=None, description="Build source")
    steps: list[BuildStep] = Field(..., description="Build steps to execute")
    results: BuildResults | None = Field(
        default=None, description="Build results"
    )
    create_time: datetime | None = Field(
        default=None, description="Build creation time"
    )
    start_time: datetime | None = Field(
        default=None, description="Build start time"
    )
    finish_time: datetime | None = Field(
        default=None, description="Build finish time"
    )
    timeout: str | None = Field(
        default="600s", description="Build timeout (e.g., '600s')"
    )
    images: list[str] | None = Field(
        default=None, description="Container images to build and push"
    )
    queue_ttl: str | None = Field(
        default=None, description="Queue TTL (e.g., '3600s')"
    )
    artifacts: dict[str, Any] | None = Field(
        default=None, description="Artifacts configuration"
    )
    logs_bucket: str | None = Field(
        default=None, description="GCS bucket for logs"
    )
    source_provenance: dict[str, Any] | None = Field(
        default=None, description="Source provenance information"
    )
    build_trigger_id: str | None = Field(
        default=None, description="ID of trigger that created this build"
    )
    options: BuildOptions | None = Field(
        default=None, description="Build execution options"
    )
    log_url: str | None = Field(default=None, description="URL to build logs")
    substitutions: dict[str, str] | None = Field(
        default=None, description="Substitution variables"
    )
    tags: list[str] | None = Field(default=None, description="Build tags")
    secrets: list[dict[str, Any]] | None = Field(
        default=None, description="Secrets to make available"
    )
    timing: dict[str, Any] | None = Field(
        default=None, description="Timing information for build phases"
    )


class BuildTrigger(BaseModel):
    """Cloud Build trigger model."""

    id: str | None = Field(default=None, description="Trigger ID")
    name: str = Field(..., description="Trigger name")
    description: str | None = Field(default=None, description="Trigger description")
    tags: list[str] | None = Field(default=None, description="Trigger tags")
    trigger_template: RepoSource | None = Field(
        default=None, description="Cloud Source Repository trigger template"
    )
    github: GitHubEventsConfig | None = Field(
        default=None, description="GitHub events configuration"
    )
    build: Build | None = Field(
        default=None, description="Build configuration to execute"
    )
    filename: str | None = Field(
        default=None, description="Path to cloudbuild.yaml file in source repo"
    )
    create_time: datetime | None = Field(
        default=None, description="Trigger creation time"
    )
    disabled: bool = Field(default=False, description="Whether trigger is disabled")
    substitutions: dict[str, str] | None = Field(
        default=None, description="Substitution variables"
    )
    ignored_files: list[str] | None = Field(
        default=None, description="Glob patterns for files to ignore"
    )
    included_files: list[str] | None = Field(
        default=None, description="Glob patterns for files to include"
    )
    filter: str | None = Field(
        default=None, description="CEL expression filter"
    )


class BuildListResponse(BaseModel):
    """Response model for listing builds."""

    builds: list[Build] = Field(
        default_factory=list, description="List of builds"
    )
    next_page_token: str | None = Field(
        default=None, description="Token for fetching the next page"
    )


class TriggerListResponse(BaseModel):
    """Response model for listing build triggers."""

    triggers: list[BuildTrigger] = Field(
        default_factory=list, description="List of triggers"
    )
    next_page_token: str | None = Field(
        default=None, description="Token for fetching the next page"
    )


class RunBuildTriggerResponse(BaseModel):
    """Response model for running a build trigger."""

    build_id: str = Field(..., description="ID of the created build")
    project_id: str = Field(..., description="Project ID")
