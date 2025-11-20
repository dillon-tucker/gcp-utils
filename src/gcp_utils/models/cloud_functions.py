"""
Pydantic models for Google Cloud Functions.

This module provides type-safe models for Cloud Functions resources including
functions, event triggers, build configurations, and runtime settings.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class FunctionState(str, Enum):
    """Cloud Function lifecycle state."""

    STATE_UNSPECIFIED = "STATE_UNSPECIFIED"
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"
    DEPLOYING = "DEPLOYING"
    DELETING = "DELETING"
    UNKNOWN = "UNKNOWN"


class Runtime(str, Enum):
    """Supported Cloud Functions runtimes."""

    PYTHON_38 = "python38"
    PYTHON_39 = "python39"
    PYTHON_310 = "python310"
    PYTHON_311 = "python311"
    PYTHON_312 = "python312"
    PYTHON_313 = "python313"
    NODEJS_16 = "nodejs16"
    NODEJS_18 = "nodejs18"
    NODEJS_20 = "nodejs20"
    NODEJS_22 = "nodejs22"
    GO_119 = "go119"
    GO_121 = "go121"
    GO_122 = "go122"
    JAVA_11 = "java11"
    JAVA_17 = "java17"
    JAVA_21 = "java21"
    DOTNET_3 = "dotnet3"
    DOTNET_6 = "dotnet6"
    DOTNET_8 = "dotnet8"
    RUBY_30 = "ruby30"
    RUBY_32 = "ruby32"
    RUBY_33 = "ruby33"
    PHP_81 = "php81"
    PHP_82 = "php82"
    PHP_83 = "php83"


class IngressSettings(str, Enum):
    """Ingress settings for controlling network access to the function."""

    ALLOW_ALL = "ALLOW_ALL"
    ALLOW_INTERNAL_ONLY = "ALLOW_INTERNAL_ONLY"
    ALLOW_INTERNAL_AND_GCLB = "ALLOW_INTERNAL_AND_GCLB"


class VpcConnectorEgressSettings(str, Enum):
    """VPC connector egress settings."""

    VPC_CONNECTOR_EGRESS_SETTINGS_UNSPECIFIED = (
        "VPC_CONNECTOR_EGRESS_SETTINGS_UNSPECIFIED"
    )
    PRIVATE_RANGES_ONLY = "PRIVATE_RANGES_ONLY"
    ALL_TRAFFIC = "ALL_TRAFFIC"


class EventType(str, Enum):
    """Common Cloud Functions event types."""

    # Cloud Storage
    STORAGE_OBJECT_FINALIZE = "google.cloud.storage.object.v1.finalized"
    STORAGE_OBJECT_DELETE = "google.cloud.storage.object.v1.deleted"
    STORAGE_OBJECT_ARCHIVE = "google.cloud.storage.object.v1.archived"
    STORAGE_OBJECT_METADATA_UPDATE = "google.cloud.storage.object.v1.metadataUpdated"

    # Pub/Sub
    PUBSUB_TOPIC_PUBLISH = "google.cloud.pubsub.topic.v1.messagePublished"

    # Firestore
    FIRESTORE_DOCUMENT_CREATE = "google.cloud.firestore.document.v1.created"
    FIRESTORE_DOCUMENT_UPDATE = "google.cloud.firestore.document.v1.updated"
    FIRESTORE_DOCUMENT_DELETE = "google.cloud.firestore.document.v1.deleted"
    FIRESTORE_DOCUMENT_WRITE = "google.cloud.firestore.document.v1.written"

    # Firebase Auth
    FIREBASE_AUTH_USER_CREATE = "google.firebase.auth.user.v1.created"
    FIREBASE_AUTH_USER_DELETE = "google.firebase.auth.user.v1.deleted"

    # Firebase Realtime Database
    FIREBASE_DATABASE_REF_CREATE = "google.firebase.database.ref.v1.created"
    FIREBASE_DATABASE_REF_UPDATE = "google.firebase.database.ref.v1.updated"
    FIREBASE_DATABASE_REF_DELETE = "google.firebase.database.ref.v1.deleted"
    FIREBASE_DATABASE_REF_WRITE = "google.firebase.database.ref.v1.written"


class SecretEnvVar(BaseModel):
    """Environment variable from Secret Manager."""

    key: str = Field(..., description="Environment variable name")
    project_id: str = Field(..., description="Project ID containing the secret")
    secret: str = Field(..., description="Secret name")
    version: str = Field(default="latest", description="Secret version")


class SecretVolume(BaseModel):
    """Secret mounted as a volume."""

    mount_path: str = Field(..., description="Path to mount the secret")
    project_id: str = Field(..., description="Project ID containing the secret")
    secret: str = Field(..., description="Secret name")
    versions: list[dict[str, str]] = Field(
        default_factory=list, description="Secret versions to mount"
    )


class ServiceConfig(BaseModel):
    """Configuration for the function service."""

    available_memory: Optional[str] = Field(
        default="256M", description="Memory allocated to the function (e.g., '256M', '1G')"
    )
    timeout_seconds: Optional[int] = Field(
        default=60,
        description="Maximum execution time in seconds",
        ge=1,
        le=3600,
    )
    max_instance_count: Optional[int] = Field(
        default=None,
        description="Maximum number of instances",
        ge=0,
        le=3000,
    )
    min_instance_count: Optional[int] = Field(
        default=None,
        description="Minimum number of instances (for warm starts)",
        ge=0,
        le=3000,
    )
    max_instance_request_concurrency: Optional[int] = Field(
        default=1,
        description="Maximum concurrent requests per instance",
        ge=1,
        le=1000,
    )
    available_cpu: Optional[str] = Field(
        default=None,
        description="CPU allocated to the function (e.g., '1', '2')",
    )
    environment_variables: Optional[dict[str, str]] = Field(
        default=None, description="Environment variables for the function"
    )
    secret_environment_variables: Optional[list[SecretEnvVar]] = Field(
        default=None, description="Secret environment variables from Secret Manager"
    )
    secret_volumes: Optional[list[SecretVolume]] = Field(
        default=None, description="Secrets mounted as volumes"
    )
    service_account_email: Optional[str] = Field(
        default=None, description="Service account email for the function"
    )
    ingress_settings: Optional[IngressSettings] = Field(
        default=IngressSettings.ALLOW_ALL, description="Ingress settings"
    )
    vpc_connector: Optional[str] = Field(
        default=None, description="VPC connector name"
    )
    vpc_connector_egress_settings: Optional[VpcConnectorEgressSettings] = Field(
        default=None, description="VPC connector egress settings"
    )
    all_traffic_on_latest_revision: bool = Field(
        default=True, description="Route all traffic to the latest revision"
    )


class BuildConfig(BaseModel):
    """Build configuration for the function."""

    runtime: Runtime = Field(..., description="Runtime for the function")
    entry_point: str = Field(..., description="Function entry point name")
    source_archive_url: Optional[str] = Field(
        default=None, description="GCS URL to source archive (gs://bucket/path)"
    )
    source_repository_url: Optional[str] = Field(
        default=None, description="Cloud Source Repositories URL"
    )
    build_environment_variables: Optional[dict[str, str]] = Field(
        default=None, description="Build-time environment variables"
    )
    docker_repository: Optional[str] = Field(
        default=None, description="Docker repository for storing function images"
    )
    worker_pool: Optional[str] = Field(
        default=None, description="Cloud Build worker pool"
    )


class EventFilter(BaseModel):
    """Event filter for event-driven functions."""

    attribute: str = Field(..., description="Filter attribute name")
    value: str = Field(..., description="Filter value")
    operator: Optional[str] = Field(
        default=None, description="Filter operator (e.g., 'match-path-pattern')"
    )


class EventTrigger(BaseModel):
    """Event trigger configuration."""

    trigger_region: Optional[str] = Field(
        default=None, description="Region where events are received"
    )
    event_type: str = Field(..., description="Event type that triggers the function")
    event_filters: Optional[list[EventFilter]] = Field(
        default=None, description="Event filters for selective triggering"
    )
    pubsub_topic: Optional[str] = Field(
        default=None, description="Pub/Sub topic name for Pub/Sub triggers"
    )
    service_account_email: Optional[str] = Field(
        default=None, description="Service account for invoking the function"
    )
    retry_policy: Optional[str] = Field(
        default=None,
        description="Retry policy: 'RETRY_POLICY_UNSPECIFIED', 'RETRY_POLICY_DO_NOT_RETRY', 'RETRY_POLICY_RETRY'",
    )
    channel: Optional[str] = Field(
        default=None, description="Eventarc channel name"
    )


class CloudFunction(BaseModel):
    """Cloud Function resource model."""

    name: str = Field(..., description="Function resource name")
    description: Optional[str] = Field(default=None, description="Function description")
    build_config: Optional[BuildConfig] = Field(
        default=None, description="Build configuration"
    )
    service_config: Optional[ServiceConfig] = Field(
        default=None, description="Service configuration"
    )
    event_trigger: Optional[EventTrigger] = Field(
        default=None, description="Event trigger configuration"
    )
    state: Optional[FunctionState] = Field(
        default=None, description="Function lifecycle state"
    )
    update_time: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )
    labels: Optional[dict[str, str]] = Field(
        default=None, description="Resource labels"
    )
    url: Optional[str] = Field(default=None, description="HTTP trigger URL")
    kms_key_name: Optional[str] = Field(
        default=None, description="Cloud KMS key for encryption"
    )


class FunctionListResponse(BaseModel):
    """Response model for listing functions."""

    functions: list[CloudFunction] = Field(
        default_factory=list, description="List of functions"
    )
    next_page_token: Optional[str] = Field(
        default=None, description="Token for fetching the next page"
    )
    unreachable: Optional[list[str]] = Field(
        default_factory=list, description="Locations that could not be reached"
    )


class GenerateUploadUrlResponse(BaseModel):
    """Response from generating an upload URL."""

    upload_url: str = Field(..., description="Signed URL for uploading source code")
    storage_source: dict[str, Any] = Field(
        ..., description="Storage source location details"
    )
