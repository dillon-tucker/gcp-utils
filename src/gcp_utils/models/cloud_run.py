"""Data models for Cloud Run operations."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_serializer

if TYPE_CHECKING:
    from google.cloud.run_v2 import Service


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
