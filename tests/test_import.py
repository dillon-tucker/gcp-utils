"""
Basic import tests to verify package structure.
"""


def test_import_package():
    """Test that the main package can be imported."""
    import gcp_utils

    assert gcp_utils.__version__ == "0.1.0"


def test_import_config():
    """Test that config module can be imported."""
    from gcp_utils.config import GCPSettings, get_settings

    assert GCPSettings is not None
    assert get_settings is not None


def test_import_controllers():
    """Test that all controllers can be imported."""
    from gcp_utils.controllers import (
        CloudRunController,
        CloudStorageController,
        CloudTasksController,
        FirebaseAuthController,
        FirestoreController,
        PubSubController,
        SecretManagerController,
        WorkflowsController,
    )

    assert CloudStorageController is not None
    assert FirestoreController is not None
    assert FirebaseAuthController is not None
    assert CloudRunController is not None
    assert WorkflowsController is not None
    assert CloudTasksController is not None
    assert PubSubController is not None
    assert SecretManagerController is not None


def test_import_exceptions():
    """Test that exceptions can be imported."""
    from gcp_utils.exceptions import (
        CloudRunError,
        CloudTasksError,
        ConfigurationError,
        FirebaseError,
        FirestoreError,
        GCPUtilitiesError,
        PubSubError,
        ResourceNotFoundError,
        SecretManagerError,
        StorageError,
        ValidationError,
        WorkflowsError,
    )

    assert GCPUtilitiesError is not None
    assert issubclass(ConfigurationError, GCPUtilitiesError)
    assert issubclass(StorageError, GCPUtilitiesError)
    assert issubclass(FirestoreError, GCPUtilitiesError)
    assert issubclass(FirebaseError, GCPUtilitiesError)
    assert issubclass(CloudRunError, GCPUtilitiesError)
    assert issubclass(WorkflowsError, GCPUtilitiesError)
    assert issubclass(CloudTasksError, GCPUtilitiesError)
    assert issubclass(PubSubError, GCPUtilitiesError)
    assert issubclass(SecretManagerError, GCPUtilitiesError)
    assert issubclass(ResourceNotFoundError, GCPUtilitiesError)
    assert issubclass(ValidationError, GCPUtilitiesError)


def test_import_models():
    """Test that models can be imported."""
    from gcp_utils.models import (
        BlobMetadata,
        BucketInfo,
        CloudRunService,
        CloudTask,
        FirestoreDocument,
        FirestoreQuery,
        QueryOperator,
        UploadResult,
        WorkflowExecution,
    )

    assert BlobMetadata is not None
    assert BucketInfo is not None
    assert UploadResult is not None
    assert FirestoreDocument is not None
    assert FirestoreQuery is not None
    assert QueryOperator is not None
    assert CloudRunService is not None
    assert WorkflowExecution is not None
    assert CloudTask is not None
