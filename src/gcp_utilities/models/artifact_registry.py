"""Data models for Artifact Registry operations."""

from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field


class RepositoryFormat(str, Enum):
    """Repository format types."""

    DOCKER = "DOCKER"
    MAVEN = "MAVEN"
    NPM = "NPM"
    PYTHON = "PYTHON"
    APT = "APT"
    YUM = "YUM"
    GENERIC = "GENERIC"


class Repository(BaseModel):
    """Information about an Artifact Registry repository."""

    name: str = Field(..., description="Full resource name of the repository")
    repository_id: str = Field(..., description="Repository identifier")
    format: RepositoryFormat = Field(..., description="Repository format")
    description: Optional[str] = Field(None, description="Repository description")
    location: str = Field(..., description="GCP location")
    create_time: Optional[datetime] = Field(None, description="Creation timestamp")
    update_time: Optional[datetime] = Field(None, description="Last update timestamp")
    labels: dict[str, str] = Field(
        default_factory=dict, description="Resource labels"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        use_enum_values = True


class DockerImage(BaseModel):
    """Information about a Docker image in Artifact Registry."""

    image_name: str = Field(..., description="Image name")
    tag: str = Field(..., description="Image tag")
    digest: str = Field(..., description="Image digest (SHA256)")
    upload_time: Optional[datetime] = Field(None, description="Upload timestamp")
    size_bytes: Optional[int] = Field(None, description="Image size in bytes")
    media_type: Optional[str] = Field(None, description="Media type")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class BuildResult(BaseModel):
    """Result of a Docker image build operation."""

    image_url: str = Field(..., description="Full image URL")
    success: bool = Field(..., description="Whether build succeeded")
    build_time: Optional[float] = Field(None, description="Build time in seconds")
    size_bytes: Optional[int] = Field(None, description="Image size in bytes")

    class Config:
        use_enum_values = True


class DeploymentPipeline(BaseModel):
    """Complete build-push-deploy pipeline result."""

    image_url: str = Field(..., description="Deployed image URL")
    repository: str = Field(..., description="Artifact Registry repository")
    service_url: str = Field(..., description="Cloud Run service URL")
    build_success: bool = Field(..., description="Whether build succeeded")
    push_success: bool = Field(..., description="Whether push succeeded")
    deploy_success: bool = Field(..., description="Whether deployment succeeded")
    total_time: Optional[float] = Field(None, description="Total pipeline time in seconds")

    class Config:
        use_enum_values = True
