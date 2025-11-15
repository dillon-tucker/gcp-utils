"""
Secret Manager controller for secure secrets management.

This module provides a high-level interface for Google Cloud Secret Manager
operations including secret creation, access, and version management.
"""

from typing import Any, Optional

from google.cloud import secretmanager_v1
from google.auth.credentials import Credentials

from ..config import GCPSettings, get_settings
from ..exceptions import SecretManagerError, ResourceNotFoundError, ValidationError
from ..models.secret_manager import SecretInfo, SecretVersionInfo


class SecretManagerController:
    """
    Controller for Google Cloud Secret Manager operations.

    This controller provides methods for managing secrets and their versions.

    Example:
        >>> from gcp_utils.controllers import SecretManagerController
        >>>
        >>> # Automatically loads from .env file
        >>> secrets_ctrl = SecretManagerController()
        >>>
        >>> # Create and add a secret
        >>> secrets_ctrl.create_secret("database-password")
        >>> secrets_ctrl.add_secret_version("database-password", "my-secure-password")
    """

    def __init__(
        self,
        settings: Optional[GCPSettings] = None,
        credentials: Optional[Credentials] = None,
    ) -> None:
        """
        Initialize the Secret Manager controller.

        Args:
            settings: GCP configuration settings. If not provided, loads from environment/.env file.
            credentials: Optional custom credentials

        Raises:
            SecretManagerError: If client initialization fails
        """
        self.settings = settings or get_settings()

        try:
            self.client = secretmanager_v1.SecretManagerServiceClient(
                credentials=credentials
            )
        except Exception as e:
            raise SecretManagerError(
                f"Failed to initialize Secret Manager client: {e}",
                details={"error": str(e)},
            )

    def create_secret(
        self,
        secret_id: str,
        labels: Optional[dict[str, str]] = None,
        replication_policy: str = "automatic",
        locations: Optional[list[str]] = None,
    ) -> SecretInfo:
        """
        Create a new secret (without version/value).

        Args:
            secret_id: Secret ID
            labels: Optional labels for the secret
            replication_policy: 'automatic' or 'user-managed'
            locations: Required if replication_policy is 'user-managed'

        Returns:
            SecretInfo object with native object binding

        Raises:
            ValidationError: If parameters are invalid
            SecretManagerError: If creation fails
        """
        if not secret_id:
            raise ValidationError("Secret ID cannot be empty")

        try:
            parent = f"projects/{self.settings.project_id}"

            # Configure replication policy
            if replication_policy == "automatic":
                replication = secretmanager_v1.Replication(
                    automatic=secretmanager_v1.Replication.Automatic()
                )
            elif replication_policy == "user-managed":
                if not locations:
                    raise ValidationError(
                        "Locations required for user-managed replication"
                    )
                replicas = [
                    secretmanager_v1.Replication.UserManaged.Replica(location=loc)
                    for loc in locations
                ]
                replication = secretmanager_v1.Replication(
                    user_managed=secretmanager_v1.Replication.UserManaged(
                        replicas=replicas
                    )
                )
            else:
                raise ValidationError(
                    f"Invalid replication policy: {replication_policy}"
                )

            secret = secretmanager_v1.Secret(
                replication=replication,
                labels=labels or {},
            )

            request = secretmanager_v1.CreateSecretRequest(
                parent=parent,
                secret_id=secret_id,
                secret=secret,
            )

            created_secret = self.client.create_secret(request=request)

            return self._secret_to_model(created_secret)

        except ValidationError:
            raise
        except Exception as e:
            raise SecretManagerError(
                f"Failed to create secret '{secret_id}': {e}",
                details={"secret_id": secret_id, "error": str(e)},
            )

    def get_secret(self, secret_id: str) -> SecretInfo:
        """
        Get secret metadata (not the secret value).

        Args:
            secret_id: Secret ID

        Returns:
            SecretInfo object with native object binding

        Raises:
            ResourceNotFoundError: If secret doesn't exist
            SecretManagerError: If operation fails
        """
        try:
            secret_path = self._get_secret_path(secret_id)
            secret = self.client.get_secret(name=secret_path)

            return self._secret_to_model(secret)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Secret '{secret_id}' not found",
                    details={"secret_id": secret_id},
                )
            raise SecretManagerError(
                f"Failed to get secret '{secret_id}': {e}",
                details={"secret_id": secret_id, "error": str(e)},
            )

    def list_secrets(self) -> list[SecretInfo]:
        """
        List all secrets in the project.

        Returns:
            List of SecretInfo objects with native object binding

        Raises:
            SecretManagerError: If listing fails
        """
        try:
            parent = f"projects/{self.settings.project_id}"
            secrets = self.client.list_secrets(parent=parent)

            return [self._secret_to_model(secret) for secret in secrets]

        except Exception as e:
            raise SecretManagerError(
                f"Failed to list secrets: {e}",
                details={"error": str(e)},
            )

    def delete_secret(self, secret_id: str) -> None:
        """
        Delete a secret and all its versions.

        Args:
            secret_id: Secret ID to delete

        Raises:
            SecretManagerError: If deletion fails
        """
        try:
            secret_path = self._get_secret_path(secret_id)
            self.client.delete_secret(name=secret_path)

        except Exception as e:
            raise SecretManagerError(
                f"Failed to delete secret '{secret_id}': {e}",
                details={"secret_id": secret_id, "error": str(e)},
            )

    def add_secret_version(
        self,
        secret_id: str,
        payload: str | bytes,
    ) -> SecretVersionInfo:
        """
        Add a new version to an existing secret.

        Args:
            secret_id: Secret ID
            payload: Secret value as string or bytes

        Returns:
            SecretVersionInfo object with native object binding

        Raises:
            ValidationError: If payload is invalid
            SecretManagerError: If operation fails
        """
        if not payload:
            raise ValidationError("Secret payload cannot be empty")

        try:
            parent = self._get_secret_path(secret_id)

            # Convert payload to bytes
            if isinstance(payload, str):
                payload_bytes = payload.encode("utf-8")
            else:
                payload_bytes = payload

            version = self.client.add_secret_version(
                request={
                    "parent": parent,
                    "payload": {"data": payload_bytes},
                }
            )

            return self._version_to_model(version)

        except ValidationError:
            raise
        except Exception as e:
            raise SecretManagerError(
                f"Failed to add version to secret '{secret_id}': {e}",
                details={"secret_id": secret_id, "error": str(e)},
            )

    def access_secret_version(
        self,
        secret_id: str,
        version: str = "latest",
    ) -> str:
        """
        Access a secret version's value.

        Args:
            secret_id: Secret ID
            version: Version ID or 'latest' (default)

        Returns:
            Secret value as string

        Raises:
            ResourceNotFoundError: If secret or version doesn't exist
            SecretManagerError: If access fails
        """
        try:
            version_path = self._get_version_path(secret_id, version)
            response = self.client.access_secret_version(name=version_path)

            return response.payload.data.decode("utf-8")

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Secret '{secret_id}' version '{version}' not found",
                    details={"secret_id": secret_id, "version": version},
                )
            raise SecretManagerError(
                f"Failed to access secret '{secret_id}' version '{version}': {e}",
                details={"secret_id": secret_id, "version": version, "error": str(e)},
            )

    def access_secret_version_bytes(
        self,
        secret_id: str,
        version: str = "latest",
    ) -> bytes:
        """
        Access a secret version's value as bytes.

        Args:
            secret_id: Secret ID
            version: Version ID or 'latest' (default)

        Returns:
            Secret value as bytes

        Raises:
            ResourceNotFoundError: If secret or version doesn't exist
            SecretManagerError: If access fails
        """
        try:
            version_path = self._get_version_path(secret_id, version)
            response = self.client.access_secret_version(name=version_path)

            return response.payload.data

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Secret '{secret_id}' version '{version}' not found",
                    details={"secret_id": secret_id, "version": version},
                )
            raise SecretManagerError(
                f"Failed to access secret '{secret_id}' version '{version}': {e}",
                details={"secret_id": secret_id, "version": version, "error": str(e)},
            )

    def list_secret_versions(
        self,
        secret_id: str,
    ) -> list[SecretVersionInfo]:
        """
        List all versions of a secret.

        Args:
            secret_id: Secret ID

        Returns:
            List of SecretVersionInfo objects with native object binding

        Raises:
            SecretManagerError: If listing fails
        """
        try:
            parent = self._get_secret_path(secret_id)
            versions = self.client.list_secret_versions(parent=parent)

            return [self._version_to_model(version) for version in versions]

        except Exception as e:
            raise SecretManagerError(
                f"Failed to list versions for secret '{secret_id}': {e}",
                details={"secret_id": secret_id, "error": str(e)},
            )

    def disable_secret_version(
        self,
        secret_id: str,
        version: str,
    ) -> SecretVersionInfo:
        """
        Disable a secret version.

        Args:
            secret_id: Secret ID
            version: Version ID to disable

        Returns:
            SecretVersionInfo object with updated state and native object binding

        Raises:
            SecretManagerError: If operation fails
        """
        try:
            version_path = self._get_version_path(secret_id, version)
            disabled_version = self.client.disable_secret_version(name=version_path)

            return self._version_to_model(disabled_version)

        except Exception as e:
            raise SecretManagerError(
                f"Failed to disable secret '{secret_id}' version '{version}': {e}",
                details={"secret_id": secret_id, "version": version, "error": str(e)},
            )

    def enable_secret_version(
        self,
        secret_id: str,
        version: str,
    ) -> SecretVersionInfo:
        """
        Enable a previously disabled secret version.

        Args:
            secret_id: Secret ID
            version: Version ID to enable

        Returns:
            SecretVersionInfo object with updated state and native object binding

        Raises:
            SecretManagerError: If operation fails
        """
        try:
            version_path = self._get_version_path(secret_id, version)
            enabled_version = self.client.enable_secret_version(name=version_path)

            return self._version_to_model(enabled_version)

        except Exception as e:
            raise SecretManagerError(
                f"Failed to enable secret '{secret_id}' version '{version}': {e}",
                details={"secret_id": secret_id, "version": version, "error": str(e)},
            )

    def destroy_secret_version(
        self,
        secret_id: str,
        version: str,
    ) -> SecretVersionInfo:
        """
        Permanently destroy a secret version.

        Args:
            secret_id: Secret ID
            version: Version ID to destroy

        Returns:
            SecretVersionInfo object with destroyed state and native object binding

        Raises:
            SecretManagerError: If operation fails
        """
        try:
            version_path = self._get_version_path(secret_id, version)
            destroyed_version = self.client.destroy_secret_version(name=version_path)

            return self._version_to_model(destroyed_version)

        except Exception as e:
            raise SecretManagerError(
                f"Failed to destroy secret '{secret_id}' version '{version}': {e}",
                details={"secret_id": secret_id, "version": version, "error": str(e)},
            )

    def create_secret_with_value(
        self,
        secret_id: str,
        payload: str | bytes,
        labels: Optional[dict[str, str]] = None,
    ) -> SecretVersionInfo:
        """
        Convenience method to create a secret and add its first version.

        Args:
            secret_id: Secret ID
            payload: Secret value
            labels: Optional labels

        Returns:
            SecretVersionInfo object for the first version with native object binding

        Raises:
            ValidationError: If parameters are invalid
            SecretManagerError: If operation fails
        """
        try:
            # Create the secret
            self.create_secret(secret_id, labels=labels)

            # Add the first version
            return self.add_secret_version(secret_id, payload)

        except Exception as e:
            # Try to clean up if secret was created but version failed
            try:
                self.delete_secret(secret_id)
            except Exception:
                pass

            if isinstance(e, (ValidationError, SecretManagerError)):
                raise
            raise SecretManagerError(
                f"Failed to create secret with value '{secret_id}': {e}",
                details={"secret_id": secret_id, "error": str(e)},
            )

    def _get_secret_path(self, secret_id: str) -> str:
        """Get the full secret path."""
        return f"projects/{self.settings.project_id}/secrets/{secret_id}"

    def _get_version_path(self, secret_id: str, version: str) -> str:
        """Get the full version path."""
        return f"{self._get_secret_path(secret_id)}/versions/{version}"

    def _secret_to_model(self, secret: Any) -> SecretInfo:
        """Convert Secret to SecretInfo model with native object binding."""
        model = SecretInfo(
            name=secret.name.split("/")[-1],
            full_name=secret.name,
            labels=dict(secret.labels) if hasattr(secret, "labels") else {},
            created=secret.create_time if hasattr(secret, "create_time") else None,
        )
        # Bind the native object
        model._secret_object = secret
        return model

    def _version_to_model(self, version: Any) -> SecretVersionInfo:
        """Convert SecretVersion to SecretVersionInfo model with native object binding."""
        version_id = version.name.split("/")[-1]

        model = SecretVersionInfo(
            name=version_id,
            full_name=version.name,
            state=str(version.state) if hasattr(version, "state") else "UNKNOWN",
            created=version.create_time if hasattr(version, "create_time") else None,
            destroyed=(
                version.destroy_time if hasattr(version, "destroy_time") else None
            ),
        )
        # Bind the native object
        model._version_object = version
        return model
