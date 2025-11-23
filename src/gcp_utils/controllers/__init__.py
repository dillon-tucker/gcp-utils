"""
GCP service controllers.

Controllers are conditionally imported based on installed dependencies.
Install specific services with: pip install gcp-utils[service-name]

Examples:
    pip install gcp-utils[storage]          # Cloud Storage only
    pip install gcp-utils[bigquery]         # BigQuery only
    pip install gcp-utils[storage,bigquery] # Multiple services
    pip install gcp-utils[all]              # All services
"""

from typing import TYPE_CHECKING

# Conditionally import controllers based on available dependencies
__all__: list[str] = []

# Cloud Storage
try:
    from .storage import CloudStorageController

    __all__.append("CloudStorageController")
except ImportError:
    if not TYPE_CHECKING:
        CloudStorageController = None  # type: ignore

# Firestore
try:
    from .firestore import FirestoreController

    __all__.append("FirestoreController")
except ImportError:
    if not TYPE_CHECKING:
        FirestoreController = None  # type: ignore

# BigQuery
try:
    from .bigquery import BigQueryController

    __all__.append("BigQueryController")
except ImportError:
    if not TYPE_CHECKING:
        BigQueryController = None  # type: ignore

# Firebase Auth
try:
    from .firebase_auth import FirebaseAuthController

    __all__.append("FirebaseAuthController")
except ImportError:
    if not TYPE_CHECKING:
        FirebaseAuthController = None  # type: ignore

# Firebase Hosting
try:
    from .firebase_hosting import FirebaseHostingController

    __all__.append("FirebaseHostingController")
except ImportError:
    if not TYPE_CHECKING:
        FirebaseHostingController = None  # type: ignore

# Artifact Registry
try:
    from .artifact_registry import ArtifactRegistryController

    __all__.append("ArtifactRegistryController")
except ImportError:
    if not TYPE_CHECKING:
        ArtifactRegistryController = None  # type: ignore

# Cloud Build
try:
    from .cloud_build import CloudBuildController

    __all__.append("CloudBuildController")
except ImportError:
    if not TYPE_CHECKING:
        CloudBuildController = None  # type: ignore

# Cloud Functions
try:
    from .cloud_functions import CloudFunctionsController

    __all__.append("CloudFunctionsController")
except ImportError:
    if not TYPE_CHECKING:
        CloudFunctionsController = None  # type: ignore

# Cloud Run
try:
    from .cloud_run import CloudRunController

    __all__.append("CloudRunController")
except ImportError:
    if not TYPE_CHECKING:
        CloudRunController = None  # type: ignore

# Cloud Scheduler
try:
    from .cloud_scheduler import CloudSchedulerController

    __all__.append("CloudSchedulerController")
except ImportError:
    if not TYPE_CHECKING:
        CloudSchedulerController = None  # type: ignore

# Cloud Tasks
try:
    from .cloud_tasks import CloudTasksController

    __all__.append("CloudTasksController")
except ImportError:
    if not TYPE_CHECKING:
        CloudTasksController = None  # type: ignore

# Workflows
try:
    from .workflows import WorkflowsController

    __all__.append("WorkflowsController")
except ImportError:
    if not TYPE_CHECKING:
        WorkflowsController = None  # type: ignore

# Pub/Sub
try:
    from .pubsub import PubSubController

    __all__.append("PubSubController")
except ImportError:
    if not TYPE_CHECKING:
        PubSubController = None  # type: ignore

# Secret Manager
try:
    from .secret_manager import SecretManagerController

    __all__.append("SecretManagerController")
except ImportError:
    if not TYPE_CHECKING:
        SecretManagerController = None  # type: ignore

# IAM
try:
    from .iam import IAMController

    __all__.append("IAMController")
except ImportError:
    if not TYPE_CHECKING:
        IAMController = None  # type: ignore

# Cloud Logging
try:
    from .cloud_logging import CloudLoggingController

    __all__.append("CloudLoggingController")
except ImportError:
    if not TYPE_CHECKING:
        CloudLoggingController = None  # type: ignore
