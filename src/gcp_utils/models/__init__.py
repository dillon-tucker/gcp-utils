"""Data models and type definitions for GCP utilities."""

from .storage import BlobMetadata, BucketInfo, UploadResult
from .firestore import FirestoreDocument, FirestoreQuery, QueryOperator
from .cloud_run import CloudRunService, ServiceRevision, TrafficTarget
from .workflows import WorkflowExecution, WorkflowInfo, ExecutionState
from .tasks import CloudTask, TaskInfo, TaskSchedule
from .firebase_hosting import (
    HostingSite,
    CustomDomain,
    HostingVersion,
    HostingRelease,
    DeploymentInfo,
    FileUploadResult,
    DeploymentResult,
    DomainStatus,
    VersionStatus,
    RedirectRule,
    RewriteRule,
    HeaderRule,
    HostingConfig,
)
from .artifact_registry import (
    Repository,
    RepositoryFormat,
    DockerImage,
    BuildResult,
    DeploymentPipeline,
)
from .secret_manager import (
    SecretInfo,
    SecretVersionInfo,
    SecretState,
)
from .pubsub import (
    TopicInfo,
    SubscriptionInfo,
)
from .iam import (
    ServiceAccount,
    ServiceAccountKey,
    ServiceAccountKeyAlgorithm,
    ServiceAccountKeyType,
    IAMBinding,
    IAMPolicy,
    ServiceAccountInfo,
)

__all__ = [
    # Storage models
    "BlobMetadata",
    "BucketInfo",
    "UploadResult",
    # Firestore models
    "FirestoreDocument",
    "FirestoreQuery",
    "QueryOperator",
    # Cloud Run models
    "CloudRunService",
    "ServiceRevision",
    "TrafficTarget",
    # Workflows models
    "WorkflowExecution",
    "WorkflowInfo",
    "ExecutionState",
    # Cloud Tasks models
    "CloudTask",
    "TaskInfo",
    "TaskSchedule",
    # Firebase Hosting models
    "HostingSite",
    "CustomDomain",
    "HostingVersion",
    "HostingRelease",
    "DeploymentInfo",
    "FileUploadResult",
    "DeploymentResult",
    "DomainStatus",
    "VersionStatus",
    "RedirectRule",
    "RewriteRule",
    "HeaderRule",
    "HostingConfig",
    # Artifact Registry models
    "Repository",
    "RepositoryFormat",
    "DockerImage",
    "BuildResult",
    "DeploymentPipeline",
    # Secret Manager models
    "SecretInfo",
    "SecretVersionInfo",
    "SecretState",
    # Pub/Sub models
    "TopicInfo",
    "SubscriptionInfo",
    # IAM models
    "ServiceAccount",
    "ServiceAccountKey",
    "ServiceAccountKeyAlgorithm",
    "ServiceAccountKeyType",
    "IAMBinding",
    "IAMPolicy",
    "ServiceAccountInfo",
]
