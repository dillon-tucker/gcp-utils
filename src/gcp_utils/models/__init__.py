"""Data models and type definitions for GCP utilities."""

from .artifact_registry import (
    BuildResult,
    DeploymentPipeline,
    DockerImage,
    Repository,
    RepositoryFormat,
)
from .bigquery import (
    Dataset,
    FieldType,
    Job,
)
from .bigquery import JobState as BigQueryJobState
from .bigquery import (
    QueryResult,
    SchemaField,
    Table,
)
from .cloud_build import (
    Build,
    BuildStatus,
    BuildStep,
    BuildTrigger,
)
from .cloud_functions import (
    BuildConfig,
    CloudFunction,
    EventTrigger,
    EventType,
    FunctionState,
    Runtime,
    ServiceConfig,
)
from .cloud_logging import (
    HttpRequestInfo,
    LogEntry,
    LoggerInfo,
    LogMetric,
    LogSeverity,
    LogSink,
    SourceLocation,
)
from .cloud_run import (
    CloudRunJob,
    CloudRunService,
    ExecutionEnvironment,
    ExecutionStatus,
    JobExecution,
    LaunchStage,
    ServiceRevision,
    TaskAttemptResult,
    TrafficTarget,
)
from .cloud_scheduler import (
    HttpMethod,
    HttpTarget,
    JobState,
    PubsubTarget,
    SchedulerJob,
)
from .firebase_hosting import (
    CustomDomain,
    DeploymentInfo,
    DeploymentResult,
    DomainStatus,
    FileUploadResult,
    HeaderRule,
    HostingConfig,
    HostingRelease,
    HostingSite,
    HostingVersion,
    RedirectRule,
    RewriteRule,
    VersionStatus,
)
from .firestore import FirestoreDocument, FirestoreQuery, QueryOperator
from .iam import (
    IAMBinding,
    IAMPolicy,
    ServiceAccount,
    ServiceAccountInfo,
    ServiceAccountKey,
    ServiceAccountKeyAlgorithm,
    ServiceAccountKeyType,
)
from .pubsub import (
    SubscriptionInfo,
    TopicInfo,
)
from .secret_manager import (
    SecretInfo,
    SecretState,
    SecretVersionInfo,
)
from .storage import BlobMetadata, BucketInfo, UploadResult
from .tasks import CloudTask, TaskInfo, TaskSchedule
from .workflows import ExecutionState, WorkflowExecution, WorkflowInfo

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
    "CloudRunJob",
    "JobExecution",
    "ExecutionEnvironment",
    "ExecutionStatus",
    "LaunchStage",
    "TaskAttemptResult",
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
    # Cloud Functions models
    "CloudFunction",
    "Runtime",
    "FunctionState",
    "EventType",
    "BuildConfig",
    "ServiceConfig",
    "EventTrigger",
    # Cloud Scheduler models
    "SchedulerJob",
    "HttpTarget",
    "PubsubTarget",
    "JobState",
    "HttpMethod",
    # BigQuery models
    "Dataset",
    "Table",
    "QueryResult",
    "Job",
    "SchemaField",
    "FieldType",
    "BigQueryJobState",
    # Cloud Build models
    "Build",
    "BuildTrigger",
    "BuildStep",
    "BuildStatus",
    # Cloud Logging models
    "LogEntry",
    "LogSeverity",
    "LogMetric",
    "LogSink",
    "LoggerInfo",
    "HttpRequestInfo",
    "SourceLocation",
]
