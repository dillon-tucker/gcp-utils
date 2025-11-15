"""Data models for Secret Manager operations."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_serializer

if TYPE_CHECKING:
    from google.cloud.secretmanager_v1 import Secret, SecretVersion


class SecretState(str, Enum):
    """Secret version states."""

    STATE_UNSPECIFIED = "STATE_UNSPECIFIED"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    DESTROYED = "DESTROYED"


class SecretInfo(BaseModel):
    """
    Information about a Secret Manager secret.

    This model wraps the Google Cloud Secret object, providing both
    structured Pydantic data and access to the full Secret Manager API
    via `_secret_object`.

    Example:
        >>> secret = secrets_ctrl.get_secret("database-password")
        >>>
        >>> # Use Pydantic fields
        >>> print(f"Created: {secret.created}")
        >>>
        >>> # Access full Secret Manager API
        >>> secret.add_version("new-password")
        >>> secret.delete()
    """

    name: str = Field(..., description="Secret name (without prefix)")
    full_name: str = Field(..., description="Full resource name")
    labels: dict[str, str] = Field(default_factory=dict, description="Secret labels")
    created: Optional[datetime] = Field(None, description="Creation timestamp")

    # The actual Secret object (private attribute, not serialized)
    _secret_object: Optional["Secret"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("created")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None

    # Convenience methods that delegate to the Secret object

    def delete(self) -> None:
        """
        Delete this secret and all its versions.

        Raises:
            ValueError: If no Secret object is bound

        Example:
            ```python
            secret.delete()
            ```
        """
        if not self._secret_object:
            raise ValueError("No Secret object bound to this SecretInfo")
        # Note: Secret object doesn't have a delete method
        # This would need to be handled via the controller
        raise NotImplementedError(
            "Secret deletion must be performed via SecretManagerController.delete_secret()"
        )


class SecretVersionInfo(BaseModel):
    """
    Information about a Secret Manager secret version.

    This model wraps the Google Cloud SecretVersion object, providing both
    structured Pydantic data and access to the full Secret Manager API
    via `_version_object`.

    Example:
        >>> version = secrets_ctrl.add_secret_version("db-password", "secret123")
        >>>
        >>> # Use Pydantic fields
        >>> print(f"State: {version.state}")
        >>>
        >>> # Access full Secret Manager API
        >>> version.disable()
        >>> version.enable()
        >>> version.destroy()
        >>> data = version.access_version()
    """

    name: str = Field(..., description="Version ID")
    full_name: str = Field(..., description="Full resource name")
    state: str = Field(..., description="Version state (ENABLED, DISABLED, DESTROYED)")
    created: Optional[datetime] = Field(None, description="Creation timestamp")
    destroyed: Optional[datetime] = Field(None, description="Destruction timestamp")

    # The actual SecretVersion object (private attribute, not serialized)
    _version_object: Optional["SecretVersion"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("created", "destroyed")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None

    # Convenience methods that delegate to the SecretVersion object

    def access_version(self) -> bytes:
        """
        Access this secret version's value.

        Returns:
            Secret value as bytes

        Raises:
            ValueError: If no SecretVersion object is bound

        Example:
            ```python
            secret_data = version.access_version()
            secret_str = secret_data.decode('utf-8')
            ```
        """
        if not self._version_object:
            raise ValueError("No SecretVersion object bound to this SecretVersionInfo")
        # Note: SecretVersion object doesn't have access method
        # This would need to be handled via the controller
        raise NotImplementedError(
            "Secret version access must be performed via SecretManagerController.access_secret_version()"
        )

    def destroy(self) -> None:
        """
        Permanently destroy this secret version.

        Raises:
            ValueError: If no SecretVersion object is bound

        Example:
            ```python
            version.destroy()
            ```
        """
        if not self._version_object:
            raise ValueError("No SecretVersion object bound to this SecretVersionInfo")
        # Note: SecretVersion object doesn't have destroy method
        # This would need to be handled via the controller
        raise NotImplementedError(
            "Secret version destruction must be performed via SecretManagerController.destroy_secret_version()"
        )

    def enable(self) -> None:
        """
        Enable this secret version.

        Raises:
            ValueError: If no SecretVersion object is bound

        Example:
            ```python
            version.enable()
            ```
        """
        if not self._version_object:
            raise ValueError("No SecretVersion object bound to this SecretVersionInfo")
        # Note: SecretVersion object doesn't have enable method
        # This would need to be handled via the controller
        raise NotImplementedError(
            "Secret version enable must be performed via SecretManagerController.enable_secret_version()"
        )

    def disable(self) -> None:
        """
        Disable this secret version.

        Raises:
            ValueError: If no SecretVersion object is bound

        Example:
            ```python
            version.disable()
            ```
        """
        if not self._version_object:
            raise ValueError("No SecretVersion object bound to this SecretVersionInfo")
        # Note: SecretVersion object doesn't have disable method
        # This would need to be handled via the controller
        raise NotImplementedError(
            "Secret version disable must be performed via SecretManagerController.disable_secret_version()"
        )
