"""
GCP Utilities - Comprehensive Google Cloud Platform utilities for Python backend applications.

This package provides high-level controllers for common GCP services including:
- Cloud Storage
- Firestore
- Firebase Authentication
- Firebase Hosting
- Artifact Registry (Docker images)
- Cloud Run
- Workflows
- Cloud Tasks
- Pub/Sub
- Secret Manager

Example:
    >>> from gcp_utilities.config import GCPSettings
    >>> from gcp_utilities.controllers import CloudStorageController
    >>>
    >>> settings = GCPSettings(project_id="my-project")
    >>> storage = CloudStorageController(settings)
    >>> result = storage.upload_file("my-bucket", "local.txt", "remote.txt")
"""

__version__ = "0.1.0"

from . import config, controllers, exceptions, models, utils

__all__ = [
    "config",
    "controllers",
    "exceptions",
    "models",
    "utils",
    "__version__",
]
