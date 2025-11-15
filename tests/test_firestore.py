"""
Tests for FirestoreController.
"""
import pytest
from unittest.mock import MagicMock, patch
from gcp_utilities.controllers.firestore import FirestoreController
from gcp_utilities.config import GCPSettings
from gcp_utilities.exceptions import ResourceNotFoundError
from gcp_utilities.models.firestore import FirestoreQuery, QueryOperator

@pytest.fixture
def settings():
    """Fixture for GCPSettings."""
    return GCPSettings()  # Reads from .env file

@pytest.fixture
def firestore_controller(settings):
    """Fixture for FirestoreController with a mocked client."""
    with patch('google.cloud.firestore.Client') as mock_client:
        controller = FirestoreController(settings)
        controller.client = mock_client.return_value
        yield controller

def test_get_document_not_found(firestore_controller):
    """Test that get_document raises ResourceNotFoundError for a non-existent document."""
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value.exists = False
    firestore_controller.client.collection.return_value.document.return_value = mock_doc_ref

    with pytest.raises(ResourceNotFoundError):
        firestore_controller.get_document("my-collection", "non-existent-doc")

def test_create_document(firestore_controller):
    """Test creating a document."""
    collection_id = "users"
    document_id = "user123"
    data = {"name": "Test User"}

    # Mock the client and its methods
    mock_collection = MagicMock()
    mock_doc_ref = MagicMock()
    
    # Configure the return value for the document snapshot
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True
    mock_doc_snapshot.id = document_id
    mock_doc_snapshot.to_dict.return_value = data
    mock_doc_snapshot.create_time = "2025-01-01T00:00:00Z"
    mock_doc_snapshot.update_time = "2025-01-01T00:00:00Z"

    # Set up the mock call chain
    firestore_controller.client.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_doc_ref
    mock_doc_ref.get.return_value = mock_doc_snapshot
    mock_doc_ref.set.return_value = None


    # Call the method under test
    created_doc = firestore_controller.create_document(collection_id, data, document_id=document_id)

    # Assertions
    mock_collection.document.assert_called_with(document_id)
    mock_doc_ref.set.assert_called_once_with(data)
    assert created_doc.id == document_id
    assert created_doc.data["name"] == "Test User"

@pytest.mark.integration
def test_document_lifecycle(settings):
    """Integration test for the full lifecycle of a Firestore document."""
    controller = FirestoreController(settings)
    collection_id = "test-collection"
    document_id = "test-doc"
    doc_data = {"name": "Test", "value": 123}

    # Create document
    created_doc = controller.create_document(collection_id, doc_data, document_id=document_id)
    assert created_doc.id == document_id

    # Get document
    retrieved_doc = controller.get_document(collection_id, document_id)
    assert retrieved_doc.data["name"] == "Test"

    # Query for the document
    query = [FirestoreQuery(field="name", operator=QueryOperator.EQUAL, value="Test")]
    results = controller.query_documents(collection_id, query)
    assert len(results) > 0
    assert results[0].data["name"] == "Test"

    # Delete document
    controller.delete_document(collection_id, document_id)

    # Verify document is deleted
    with pytest.raises(ResourceNotFoundError):
        controller.get_document(collection_id, document_id)
