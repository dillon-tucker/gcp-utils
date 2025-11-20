"""
Pydantic models for Google Cloud Build.

This module provides type-safe models for Cloud Build resources including
builds, build triggers, build steps, and source configurations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

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
    args: Optional[list[str]] = Field(
        default=None, description="Arguments to pass to the builder"
    )
    env: Optional[list[str]] = Field(
        default=None, description="Environment variables (KEY=value format)"
    )
    dir: Optional[str] = Field(
        default=None, description="Working directory for the step"
    )
    id: Optional[str] = Field(
        default=None, description="Step ID (for dependencies)"
    )
    wait_for: Optional[list[str]] = Field(
        default=None, description="Step IDs to wait for before running this step"
    )
    entrypoint: Optional[str] = Field(
        default=None, description="Override entrypoint of the builder image"
    )
    secret_env: Optional[list[str]] = Field(
        default=None, description="Secret environment variable names"
    )
    volumes: Optional[list[dict[str, str]]] = Field(
        default=None, description="Volumes to mount"
    )
    timeout: Optional[str] = Field(
        default=None, description="Step timeout (e.g., '300s')"
    )
    script: Optional[str] = Field(
        default=None, description="Script to execute (alternative to args)"
    )


class StorageSource(BaseModel):
    """Source in Cloud Storage."""

    bucket: str = Field(..., description="GCS bucket name")
    object_: str = Field(..., description="GCS object path", alias="object")
    generation: Optional[int] = Field(
        default=None, description="Object generation number"
    )


class RepoSource(BaseModel):
    """Source in Cloud Source Repositories."""

    project_id: Optional[str] = Field(
        default=None, description="Project ID containing the repo"
    )
    repo_name: str = Field(..., description="Repository name")
    branch_name: Optional[str] = Field(
        default=None, description="Branch name to build"
    )
    tag_name: Optional[str] = Field(
        default=None, description="Tag name to build"
    )
    commit_sha: Optional[str] = Field(
        default=None, description="Commit SHA to build"
    )
    dir: Optional[str] = Field(
        default=None, description="Directory in the repository"
    )
    invert_regex: bool = Field(
        default=False, description="Invert the regex match"
    )


class GitHubEventsConfig(BaseModel):
    """GitHub events configuration for a trigger."""

    owner: Optional[str] = Field(default=None, description="GitHub repository owner")
    name: Optional[str] = Field(default=None, description="GitHub repository name")
    pull_request: Optional[dict[str, Any]] = Field(
        default=None, description="Pull request trigger configuration"
    )
    push: Optional[dict[str, Any]] = Field(
        default=None, description="Push trigger configuration"
    )


class Source(BaseModel):
    """Build source configuration."""

    storage_source: Optional[StorageSource] = Field(
        default=None, description="Cloud Storage source"
    )
    repo_source: Optional[RepoSource] = Field(
        default=None, description="Cloud Source Repository source"
    )


class BuildOptions(BaseModel):
    """Build execution options."""

    source_provenance_hash: Optional[list[str]] = Field(
        default=None, description="Hash types to compute for source provenance"
    )
    requested_verify_option: Optional[str] = Field(
        default=None, description="Verification option (VERIFIED, NOT_VERIFIED)"
    )
    machine_type: Optional[MachineType] = Field(
        default=None, description="Machine type for build execution"
    )
    disk_size_gb: Optional[int] = Field(
        default=None, description="Disk size in GB"
    )
    substitution_option: Optional[SubstitutionOption] = Field(
        default=None, description="Substitution option"
    )
    dynamic_substitutions: Optional[bool] = Field(
        default=None, description="Enable dynamic substitutions"
    )
    log_streaming_option: Optional[LogStreamingOption] = Field(
        default=None, description="Log streaming option"
    )
    worker_pool: Optional[str] = Field(
        default=None, description="Private worker pool resource name"
    )
    logging: Optional[LoggingMode] = Field(
        default=None, description="Logging mode"
    )
    env: Optional[list[str]] = Field(
        default=None, description="Global environment variables (KEY=value format)"
    )
    secret_env: Optional[list[str]] = Field(
        default=None, description="Global secret environment variable names"
    )
    volumes: Optional[list[dict[str, str]]] = Field(
        default=None, description="Global volumes to mount"
    )


class BuildResults(BaseModel):
    """Build execution results."""

    images: Optional[list[dict[str, str]]] = Field(
        default=None, description="Container images that were built"
    )
    build_step_images: Optional[list[str]] = Field(
        default=None, description="Digests of images built in each step"
    )
    artifact_manifest: Optional[str] = Field(
        default=None, description="GCS path to artifact manifest"
    )
    num_artifacts: Optional[int] = Field(
        default=None, description="Number of artifacts uploaded"
    )
    build_step_outputs: Optional[list[bytes]] = Field(
        default=None, description="Output from build steps"
    )


class Build(BaseModel):
    """Cloud Build model."""

    id: Optional[str] = Field(default=None, description="Build ID")
    project_id: str = Field(..., description="Project ID")
    status: Optional[BuildStatus] = Field(default=None, description="Build status")
    source: Optional[Source] = Field(default=None, description="Build source")
    steps: list[BuildStep] = Field(..., description="Build steps to execute")
    results: Optional[BuildResults] = Field(
        default=None, description="Build results"
    )
    create_time: Optional[datetime] = Field(
        default=None, description="Build creation time"
    )
    start_time: Optional[datetime] = Field(
        default=None, description="Build start time"
    )
    finish_time: Optional[datetime] = Field(
        default=None, description="Build finish time"
    )
    timeout: Optional[str] = Field(
        default="600s", description="Build timeout (e.g., '600s')"
    )
    images: Optional[list[str]] = Field(
        default=None, description="Container images to build and push"
    )
    queue_ttl: Optional[str] = Field(
        default=None, description="Queue TTL (e.g., '3600s')"
    )
    artifacts: Optional[dict[str, Any]] = Field(
        default=None, description="Artifacts configuration"
    )
    logs_bucket: Optional[str] = Field(
        default=None, description="GCS bucket for logs"
    )
    source_provenance: Optional[dict[str, Any]] = Field(
        default=None, description="Source provenance information"
    )
    build_trigger_id: Optional[str] = Field(
        default=None, description="ID of trigger that created this build"
    )
    options: Optional[BuildOptions] = Field(
        default=None, description="Build execution options"
    )
    log_url: Optional[str] = Field(default=None, description="URL to build logs")
    substitutions: Optional[dict[str, str]] = Field(
        default=None, description="Substitution variables"
    )
    tags: Optional[list[str]] = Field(default=None, description="Build tags")
    secrets: Optional[list[dict[str, Any]]] = Field(
        default=None, description="Secrets to make available"
    )
    timing: Optional[dict[str, Any]] = Field(
        default=None, description="Timing information for build phases"
    )


class BuildTrigger(BaseModel):
    """Cloud Build trigger model."""

    id: Optional[str] = Field(default=None, description="Trigger ID")
    name: str = Field(..., description="Trigger name")
    description: Optional[str] = Field(default=None, description="Trigger description")
    tags: Optional[list[str]] = Field(default=None, description="Trigger tags")
    trigger_template: Optional[RepoSource] = Field(
        default=None, description="Cloud Source Repository trigger template"
    )
    github: Optional[GitHubEventsConfig] = Field(
        default=None, description="GitHub events configuration"
    )
    build: Optional[Build] = Field(
        default=None, description="Build configuration to execute"
    )
    filename: Optional[str] = Field(
        default=None, description="Path to cloudbuild.yaml file in source repo"
    )
    create_time: Optional[datetime] = Field(
        default=None, description="Trigger creation time"
    )
    disabled: bool = Field(default=False, description="Whether trigger is disabled")
    substitutions: Optional[dict[str, str]] = Field(
        default=None, description="Substitution variables"
    )
    ignored_files: Optional[list[str]] = Field(
        default=None, description="Glob patterns for files to ignore"
    )
    included_files: Optional[list[str]] = Field(
        default=None, description="Glob patterns for files to include"
    )
    filter: Optional[str] = Field(
        default=None, description="CEL expression filter"
    )


class BuildListResponse(BaseModel):
    """Response model for listing builds."""

    builds: list[Build] = Field(
        default_factory=list, description="List of builds"
    )
    next_page_token: Optional[str] = Field(
        default=None, description="Token for fetching the next page"
    )


class TriggerListResponse(BaseModel):
    """Response model for listing build triggers."""

    triggers: list[BuildTrigger] = Field(
        default_factory=list, description="List of triggers"
    )
    next_page_token: Optional[str] = Field(
        default=None, description="Token for fetching the next page"
    )


class RunBuildTriggerResponse(BaseModel):
    """Response model for running a build trigger."""

    build_id: str = Field(..., description="ID of the created build")
    project_id: str = Field(..., description="Project ID")
