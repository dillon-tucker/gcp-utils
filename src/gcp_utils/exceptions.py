"""
Custom exceptions for GCP utilities module.

This module defines custom exception classes for better error handling
and debugging across all GCP service controllers.
"""

from typing import Any, Optional


class GCPUtilitiesError(Exception):
    """Base exception for all GCP utilities errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """
        Initialize the base exception.

        Args:
            message: Human-readable error message
            details: Optional dictionary containing additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(GCPUtilitiesError):
    """Raised when there is a configuration-related error."""

    pass


class AuthenticationError(GCPUtilitiesError):
    """Raised when authentication fails."""

    pass


class StorageError(GCPUtilitiesError):
    """Raised when Cloud Storage operations fail."""

    pass


class FirestoreError(GCPUtilitiesError):
    """Raised when Firestore operations fail."""

    pass


class FirebaseError(GCPUtilitiesError):
    """Raised when Firebase operations fail."""

    pass


class FirebaseHostingError(GCPUtilitiesError):
    """Raised when Firebase Hosting operations fail."""

    pass


class ArtifactRegistryError(GCPUtilitiesError):
    """Raised when Artifact Registry operations fail."""

    pass


class CloudRunError(GCPUtilitiesError):
    """Raised when Cloud Run operations fail."""

    pass


class WorkflowsError(GCPUtilitiesError):
    """Raised when Workflows operations fail."""

    pass


class CloudTasksError(GCPUtilitiesError):
    """Raised when Cloud Tasks operations fail."""

    pass


class PubSubError(GCPUtilitiesError):
    """Raised when Pub/Sub operations fail."""

    pass


class SecretManagerError(GCPUtilitiesError):
    """Raised when Secret Manager operations fail."""

    pass


class CloudLoggingError(GCPUtilitiesError):
    """Raised when Cloud Logging operations fail."""

    pass


class ResourceNotFoundError(GCPUtilitiesError):
    """Raised when a requested GCP resource is not found."""

    pass


class OperationTimeoutError(GCPUtilitiesError):
    """Raised when a GCP operation times out."""

    pass


class ValidationError(GCPUtilitiesError):
    """Raised when input validation fails."""

    pass
