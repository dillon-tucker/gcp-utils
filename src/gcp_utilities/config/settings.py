"""
Configuration settings for GCP utilities.

This module handles configuration management for GCP credentials and project settings
using Pydantic settings with support for environment variables and .env files.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..exceptions import ConfigurationError


class GCPSettings(BaseSettings):
    """
    GCP configuration settings with automatic environment variable loading.

    Attributes:
        project_id: GCP project ID
        credentials_path: Path to service account JSON key file
        location: Default GCP location/region (e.g., 'us-central1')
        storage_bucket: Default Cloud Storage bucket name
        firestore_database: Firestore database ID (default: '(default)')
        cloud_run_region: Cloud Run deployment region
        workflows_location: Workflows location
        cloud_tasks_location: Cloud Tasks location
        pubsub_topic_prefix: Prefix for Pub/Sub topics
        firebase_hosting_default_site: Default Firebase Hosting site ID
        enable_request_logging: Enable detailed request logging
        operation_timeout: Default timeout for long-running operations (seconds)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="GCP_",
        case_sensitive=False,
        extra="ignore",
    )

    # Required settings
    project_id: str = Field(
        ...,
        description="GCP project ID",
        examples=["my-gcp-project-123456"],
    )

    # Optional settings with defaults
    credentials_path: Optional[Path] = Field(
        default=None,
        description="Path to service account JSON key file. If not provided, uses Application Default Credentials.",
    )

    location: str = Field(
        default="us-central1",
        description="Default GCP location/region",
    )

    storage_bucket: Optional[str] = Field(
        default=None,
        description="Default Cloud Storage bucket name",
    )

    firestore_database: str = Field(
        default="(default)",
        description="Firestore database ID",
    )

    cloud_run_region: str = Field(
        default="us-central1",
        description="Cloud Run deployment region",
    )

    workflows_location: str = Field(
        default="us-central1",
        description="Workflows location",
    )

    cloud_tasks_location: str = Field(
        default="us-central1",
        description="Cloud Tasks location",
    )

    pubsub_topic_prefix: str = Field(
        default="",
        description="Prefix for Pub/Sub topics",
    )

    firebase_hosting_default_site: Optional[str] = Field(
        default=None,
        description="Default Firebase Hosting site ID",
    )

    enable_request_logging: bool = Field(
        default=False,
        description="Enable detailed request logging",
    )

    operation_timeout: int = Field(
        default=300,
        description="Default timeout for long-running operations (seconds)",
        ge=1,
        le=3600,
    )

    @field_validator("credentials_path", mode="before")
    @classmethod
    def validate_credentials_path(cls, v: Optional[str | Path]) -> Optional[Path]:
        """Validate that credentials file exists if provided."""
        if v is None:
            return None

        path = Path(v) if isinstance(v, str) else v

        if not path.exists():
            raise ConfigurationError(
                f"Credentials file not found: {path}",
                details={"path": str(path)},
            )

        if not path.is_file():
            raise ConfigurationError(
                f"Credentials path is not a file: {path}",
                details={"path": str(path)},
            )

        return path

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        """Validate project ID format."""
        if not v or not v.strip():
            raise ConfigurationError("Project ID cannot be empty")

        # Basic GCP project ID validation (lowercase letters, digits, hyphens)
        if not all(c.islower() or c.isdigit() or c == "-" for c in v):
            raise ConfigurationError(
                f"Invalid project ID format: {v}. Must contain only lowercase letters, digits, and hyphens.",
                details={"project_id": v},
            )

        return v.strip()

    def get_credentials_dict(self) -> Optional[dict]:
        """
        Load and return credentials as a dictionary.

        Returns:
            Dictionary containing credentials if path is set, None otherwise

        Raises:
            ConfigurationError: If credentials file cannot be read or parsed
        """
        if self.credentials_path is None:
            return None

        try:
            import json
            from typing import cast

            with open(self.credentials_path, "r", encoding="utf-8") as f:
                return cast(dict[str, str], json.load(f))
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in credentials file: {e}",
                details={"path": str(self.credentials_path), "error": str(e)},
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to read credentials file: {e}",
                details={"path": str(self.credentials_path), "error": str(e)},
            )


# Global settings instance
_settings: Optional[GCPSettings] = None


def get_settings() -> GCPSettings:
    """
    Get or create the global settings instance.

    Returns:
        GCPSettings instance

    Example:
        >>> settings = get_settings()
        >>> print(settings.project_id)
    """
    global _settings
    if _settings is None:
        _settings = GCPSettings()  # type: ignore[call-arg]
    return _settings


def reload_settings() -> GCPSettings:
    """
    Reload settings from environment variables and .env file.

    Returns:
        New GCPSettings instance

    Example:
        >>> settings = reload_settings()
    """
    global _settings
    _settings = GCPSettings()  # type: ignore[call-arg]
    return _settings
