"""Data models for Artifact Registry operations."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_serializer

if TYPE_CHECKING:
    from google.cloud.artifactregistry_v1 import Repository as GCPRepository
    from google.cloud.artifactregistry_v1.types import DockerImage as GCPDockerImage


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
    """
    Information about an Artifact Registry repository with native object binding.

    This model wraps the Google Cloud Repository object, providing both
    structured Pydantic data and access to the full Artifact Registry API
    via `_repository_object`.

    Example:
        >>> repo = registry.create_repository("my-app", "us-central1", "DOCKER")
        >>>
        >>> # Use Pydantic fields
        >>> print(f"Format: {repo.format}")
        >>>
        >>> # Use convenience methods
        >>> repo.delete()
    """

    name: str = Field(..., description="Full resource name of the repository")
    repository_id: str = Field(..., description="Repository identifier")
    format: RepositoryFormat = Field(..., description="Repository format")
    description: str | None = Field(None, description="Repository description")
    location: str = Field(..., description="GCP location")
    create_time: datetime | None = Field(None, description="Creation timestamp")
    update_time: datetime | None = Field(None, description="Last update timestamp")
    labels: dict[str, str] = Field(default_factory=dict, description="Resource labels")

    # The actual Repository object (private attribute, not serialized)
    _repository_object: Optional["GCPRepository"] = PrivateAttr(default=None)

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)

    @field_serializer("create_time", "update_time")
    def serialize_dt(self, dt: datetime | None, _info: Any) -> str | None:
        return dt.isoformat() if dt else None

    # Convenience methods that delegate to controller operations

    def delete(self) -> None:
        """
        Delete this repository.

        Raises:
            ValueError: If no Repository object is bound

        Note:
            This requires access to the controller. Consider using
            ArtifactRegistryController.delete_repository() directly instead.
        """
        if not self._repository_object:
            raise ValueError("No Repository object bound to this Repository")
        raise NotImplementedError(
            "Repository deletion must be performed via ArtifactRegistryController.delete_repository()"
        )


class DockerImage(BaseModel):
    """
    Information about a Docker image in Artifact Registry with native object binding.

    This model wraps the Google Cloud DockerImage object, providing both
    structured Pydantic data and access to the full Artifact Registry API
    via `_image_object`.

    Example:
        >>> images = registry.list_docker_images("my-app", "us-central1")
        >>> for image in images:
        ...     print(f"{image.image_name}:{image.tag}")
        ...     image.delete()
    """

    image_name: str = Field(..., description="Image name")
    tag: str = Field(..., description="Image tag")
    digest: str = Field(..., description="Image digest (SHA256)")
    upload_time: datetime | None = Field(None, description="Upload timestamp")
    size_bytes: int | None = Field(None, description="Image size in bytes")
    media_type: str | None = Field(None, description="Media type")

    # The actual DockerImage object (private attribute, not serialized)
    _image_object: Optional["GCPDockerImage"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("upload_time")
    def serialize_dt(self, dt: datetime | None, _info: Any) -> str | None:
        return dt.isoformat() if dt else None

    # Convenience methods that delegate to controller operations

    def delete(self) -> None:
        """
        Delete this Docker image.

        Raises:
            ValueError: If no DockerImage object is bound

        Note:
            This requires access to the controller. Consider using
            ArtifactRegistryController.delete_docker_image() directly instead.
        """
        if not self._image_object:
            raise ValueError("No DockerImage object bound to this DockerImage")
        raise NotImplementedError(
            "Docker image deletion must be performed via ArtifactRegistryController.delete_docker_image()"
        )


class BuildResult(BaseModel):
    """Result of a Docker image build operation."""

    image_url: str = Field(..., description="Full image URL")
    success: bool = Field(..., description="Whether build succeeded")
    build_time: float | None = Field(None, description="Build time in seconds")
    size_bytes: int | None = Field(None, description="Image size in bytes")

    model_config = ConfigDict(use_enum_values=True)


class DeploymentPipeline(BaseModel):
    """Complete build-push-deploy pipeline result."""

    image_url: str = Field(..., description="Deployed image URL")
    repository: str = Field(..., description="Artifact Registry repository")
    service_url: str = Field(..., description="Cloud Run service URL")
    build_success: bool = Field(..., description="Whether build succeeded")
    push_success: bool = Field(..., description="Whether push succeeded")
    deploy_success: bool = Field(..., description="Whether deployment succeeded")
    total_time: float | None = Field(None, description="Total pipeline time in seconds")

    model_config = ConfigDict(use_enum_values=True)
