"""
Tests for all Pydantic models.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from gcp_utils.models.artifact_registry import Repository
from gcp_utils.models.cloud_run import CloudRunService, ServiceRevision, TrafficTarget
from gcp_utils.models.firestore import FirestoreDocument, FirestoreQuery, QueryOperator
from gcp_utils.models.iam import (
    IAMBinding,
    IAMPolicy,
    ServiceAccount,
)
from gcp_utils.models.pubsub import SubscriptionInfo, TopicInfo
from gcp_utils.models.secret_manager import SecretInfo, SecretVersionInfo
from gcp_utils.models.storage import BlobMetadata, BucketInfo, UploadResult
from gcp_utils.models.tasks import CloudTask, TaskInfo
from gcp_utils.models.workflows import WorkflowExecution, WorkflowInfo


class TestCloudRunModels:
    """Tests for Cloud Run models."""

    def test_traffic_target_creation(self):
        """Test creating a TrafficTarget."""
        target = TrafficTarget(revision_name="rev-001", percent=100, tag="stable")
        assert target.revision_name == "rev-001"
        assert target.percent == 100
        assert target.tag == "stable"
        assert target.latest_revision is False

    def test_traffic_target_validation(self):
        """Test TrafficTarget validation."""
        with pytest.raises(ValidationError):
            TrafficTarget(percent=150)  # percent > 100

    def test_service_revision_creation(self):
        """Test creating a ServiceRevision."""
        revision = ServiceRevision(
            name="rev-001",
            service_name="test-service",
            image="gcr.io/test/image:latest",
            traffic_percent=100,
        )
        assert revision.name == "rev-001"
        assert revision.service_name == "test-service"
        assert revision.image == "gcr.io/test/image:latest"

    def test_cloud_run_service_creation(self):
        """Test creating a CloudRunService."""
        service = CloudRunService(
            name="test-service",
            region="us-central1",
            image="gcr.io/test/image:latest",
            url="https://test-service-abc123.run.app",
            traffic=[],
            labels={"env": "test"},
        )
        assert service.name == "test-service"
        assert service.region == "us-central1"
        assert service.url == "https://test-service-abc123.run.app"
        assert service.labels["env"] == "test"

    def test_cloud_run_service_serialization(self):
        """Test CloudRunService serialization."""
        service = CloudRunService(
            name="test-service",
            region="us-central1",
            image="gcr.io/test/image:latest",
            url="https://test-service-abc123.run.app",
            created=datetime.now(),
            updated=datetime.now(),
        )
        data = service.model_dump()
        assert data["name"] == "test-service"
        assert isinstance(data["created"], str)  # datetime serialized to string


class TestStorageModels:
    """Tests for Storage models."""

    def test_bucket_info_creation(self):
        """Test creating a BucketInfo."""
        bucket = BucketInfo(
            name="test-bucket", location="us-central1", storage_class="STANDARD"
        )
        assert bucket.name == "test-bucket"
        assert bucket.location == "us-central1"
        assert bucket.storage_class == "STANDARD"

    def test_blob_metadata_creation(self):
        """Test creating a BlobMetadata."""
        blob = BlobMetadata(
            name="test-blob.txt",
            size=1024,
            content_type="text/plain",
            bucket="test-bucket",
        )
        assert blob.name == "test-blob.txt"
        assert blob.size == 1024
        assert blob.content_type == "text/plain"

    def test_upload_result_creation(self):
        """Test creating an UploadResult."""
        result = UploadResult(
            bucket="test-bucket", blob_name="test-blob.txt", size=1024, public_url=None
        )
        assert result.bucket == "test-bucket"
        assert result.blob_name == "test-blob.txt"
        assert result.size == 1024


class TestFirestoreModels:
    """Tests for Firestore models."""

    def test_firestore_document_creation(self):
        """Test creating a FirestoreDocument."""
        doc = FirestoreDocument(
            id="doc123", collection="users", data={"name": "John", "age": 30}
        )
        assert doc.id == "doc123"
        assert doc.collection == "users"
        assert doc.data["name"] == "John"

    def test_firestore_query_creation(self):
        """Test creating a FirestoreQuery."""
        query = FirestoreQuery(
            field="age", operator=QueryOperator.GREATER_THAN, value=18
        )
        assert query.field == "age"
        assert query.operator == QueryOperator.GREATER_THAN
        assert query.value == 18

    def test_query_operator_enum(self):
        """Test QueryOperator enum values."""
        assert QueryOperator.EQUAL == "=="
        assert QueryOperator.GREATER_THAN == ">"
        assert QueryOperator.LESS_THAN == "<"


class TestIAMModels:
    """Tests for IAM models."""

    def test_service_account_creation(self):
        """Test creating a ServiceAccount."""
        account = ServiceAccount(
            name="projects/test-project/serviceAccounts/test-sa@test-project.iam.gserviceaccount.com",
            project_id="test-project",
            unique_id="123456789",
            email="test-sa@test-project.iam.gserviceaccount.com",
            display_name="Test Service Account",
        )
        assert account.email == "test-sa@test-project.iam.gserviceaccount.com"
        assert account.display_name == "Test Service Account"

    def test_iam_binding_creation(self):
        """Test creating an IAMBinding."""
        binding = IAMBinding(role="roles/viewer", members=["user:test@example.com"])
        assert binding.role == "roles/viewer"
        assert len(binding.members) == 1

    def test_iam_policy_creation(self):
        """Test creating an IAMPolicy."""
        policy = IAMPolicy(
            version=1,
            bindings=[
                IAMBinding(role="roles/viewer", members=["user:test@example.com"])
            ],
        )
        assert policy.version == 1
        assert len(policy.bindings) == 1


class TestPubSubModels:
    """Tests for PubSub models."""

    def test_topic_creation(self):
        """Test creating a TopicInfo."""
        topic = TopicInfo(
            name="test-topic",
            full_name="projects/test-project/topics/test-topic",
            labels={"env": "test"},
        )
        assert topic.name == "test-topic"
        assert topic.labels["env"] == "test"

    def test_subscription_creation(self):
        """Test creating a SubscriptionInfo."""
        subscription = SubscriptionInfo(
            name="test-subscription",
            full_name="projects/test-project/subscriptions/test-subscription",
            topic="test-topic",
            ack_deadline_seconds=10,
        )
        assert subscription.name == "test-subscription"
        assert subscription.topic == "test-topic"
        assert subscription.ack_deadline_seconds == 10


class TestTasksModels:
    """Tests for Cloud Tasks models."""

    def test_task_info_creation(self):
        """Test creating a TaskInfo."""
        task_info = TaskInfo(
            name="projects/test-project/locations/us-central1/queues/test-queue/tasks/task-123",
            task_id="task-123",
            queue_name="test-queue",
        )
        assert "task-123" in task_info.name

    def test_cloud_task_creation(self):
        """Test creating a CloudTask."""
        task = CloudTask(
            name="task-123", queue_name="test-queue", url="https://example.com/handler"
        )
        assert task.name == "task-123"


class TestWorkflowsModels:
    """Tests for Workflows models."""

    def test_workflow_creation(self):
        """Test creating a WorkflowInfo."""
        workflow = WorkflowInfo(name="test-workflow", state="ACTIVE")
        assert workflow.name == "test-workflow"

    def test_workflow_execution_creation(self):
        """Test creating a WorkflowExecution."""
        from gcp_utils.models.workflows import ExecutionState

        execution = WorkflowExecution(
            name="exec-123", workflow_name="test-workflow", state=ExecutionState.ACTIVE
        )
        assert execution.name == "exec-123"
        assert execution.state == ExecutionState.ACTIVE


class TestArtifactRegistryModels:
    """Tests for Artifact Registry models."""

    def test_repository_creation(self):
        """Test creating a Repository."""
        from gcp_utils.models.artifact_registry import RepositoryFormat

        repository = Repository(
            name="projects/test-project/locations/us-central1/repositories/test-repo",
            repository_id="test-repo",
            format=RepositoryFormat.DOCKER,
            location="us-central1",
        )
        assert "test-repo" in repository.name
        assert repository.format == RepositoryFormat.DOCKER


class TestSecretManagerModels:
    """Tests for Secret Manager models."""

    def test_secret_info_creation(self):
        """Test creating a SecretInfo."""
        secret = SecretInfo(
            name="test-secret",
            full_name="projects/test-project/secrets/test-secret",
            labels={"env": "test"},
        )
        assert secret.name == "test-secret"
        assert secret.labels["env"] == "test"

    def test_secret_version_creation(self):
        """Test creating a SecretVersionInfo."""
        from gcp_utils.models.secret_manager import SecretState

        version = SecretVersionInfo(
            name="1",
            full_name="projects/test-project/secrets/test-secret/versions/1",
            state=SecretState.ENABLED,
        )
        assert version.name == "1"
        assert version.state == SecretState.ENABLED
