"""
Firestore controller for NoSQL database operations.

This module provides a high-level interface for Firestore operations including
document CRUD, querying, batch operations, and transactions.
"""

from typing import Any, Optional

from google.cloud import firestore
from google.cloud.firestore_v1 import (
    Client,
    DocumentReference,
    CollectionReference,
    Transaction,
)
from google.auth.credentials import Credentials

from ..config import GCPSettings
from ..exceptions import FirestoreError, ResourceNotFoundError, ValidationError
from ..models.firestore import FirestoreDocument, FirestoreQuery, QueryOperator


class FirestoreController:
    """
    Controller for Google Cloud Firestore operations.

    This controller provides methods for document CRUD, querying,
    batch operations, and transactions.

    Example:
        >>> from gcp_utils.config import GCPSettings
        >>> from gcp_utils.controllers import FirestoreController
        >>>
        >>> settings = GCPSettings(project_id="my-project")
        >>> fs_ctrl = FirestoreController(settings)
        >>>
        >>> # Create a document
        >>> doc = fs_ctrl.create_document(
        ...     "users",
        ...     {"name": "John Doe", "email": "john@example.com"},
        ...     document_id="user123"
        ... )
    """

    def __init__(
        self,
        settings: GCPSettings,
        credentials: Optional[Credentials] = None,
        database: Optional[str] = None,
    ) -> None:
        """
        Initialize the Firestore controller.

        Args:
            settings: GCP configuration settings
            credentials: Optional custom credentials
            database: Database ID (defaults to settings.firestore_database)

        Raises:
            FirestoreError: If client initialization fails
        """
        self.settings = settings
        self.database = database or settings.firestore_database

        try:
            self.client: Client = firestore.Client(
                project=settings.project_id,
                credentials=credentials,
                database=self.database,
            )
        except Exception as e:
            raise FirestoreError(
                f"Failed to initialize Firestore client: {e}",
                details={"error": str(e)},
            )

    def create_document(
        self,
        collection: str,
        data: dict[str, Any],
        document_id: Optional[str] = None,
    ) -> FirestoreDocument:
        """
        Create a new document in a collection.

        Args:
            collection: Collection path
            data: Document data
            document_id: Optional document ID (auto-generated if not provided)

        Returns:
            FirestoreDocument with the created document details

        Raises:
            ValidationError: If data is invalid
            FirestoreError: If creation fails
        """
        if not data:
            raise ValidationError("Document data cannot be empty")

        try:
            col_ref = self.client.collection(collection)

            if document_id:
                doc_ref = col_ref.document(document_id)
                doc_ref.set(data)
            else:
                _, doc_ref = col_ref.add(data)
                document_id = doc_ref.id

            # Retrieve the created document
            return self.get_document(collection, document_id)

        except ValidationError:
            raise
        except Exception as e:
            raise FirestoreError(
                f"Failed to create document in '{collection}': {e}",
                details={
                    "collection": collection,
                    "document_id": document_id,
                    "error": str(e),
                },
            )

    def get_document(
        self,
        collection: str,
        document_id: str,
    ) -> FirestoreDocument:
        """
        Get a document by ID.

        Args:
            collection: Collection path
            document_id: Document ID

        Returns:
            FirestoreDocument with document data

        Raises:
            ResourceNotFoundError: If document doesn't exist
            FirestoreError: If retrieval fails
        """
        try:
            doc_ref = self.client.collection(collection).document(document_id)
            doc = doc_ref.get()

            if not doc.exists:
                raise ResourceNotFoundError(
                    f"Document '{document_id}' not found in collection '{collection}'",
                    details={"collection": collection, "document_id": document_id},
                )

            return FirestoreDocument(
                id=doc.id,
                collection=collection,
                data=doc.to_dict(),
                create_time=doc.create_time,
                update_time=doc.update_time,
            )

        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise FirestoreError(
                f"Failed to get document '{document_id}' from '{collection}': {e}",
                details={
                    "collection": collection,
                    "document_id": document_id,
                    "error": str(e),
                },
            )

    def update_document(
        self,
        collection: str,
        document_id: str,
        data: dict[str, Any],
        merge: bool = True,
    ) -> FirestoreDocument:
        """
        Update a document.

        Args:
            collection: Collection path
            document_id: Document ID
            data: Data to update
            merge: If True, merge with existing data. If False, replace entire document.

        Returns:
            Updated FirestoreDocument

        Raises:
            ValidationError: If data is invalid
            FirestoreError: If update fails
        """
        if not data:
            raise ValidationError("Update data cannot be empty")

        try:
            doc_ref = self.client.collection(collection).document(document_id)

            if merge:
                doc_ref.set(data, merge=True)
            else:
                doc_ref.set(data)

            return self.get_document(collection, document_id)

        except ValidationError:
            raise
        except Exception as e:
            raise FirestoreError(
                f"Failed to update document '{document_id}' in '{collection}': {e}",
                details={
                    "collection": collection,
                    "document_id": document_id,
                    "error": str(e),
                },
            )

    def delete_document(
        self,
        collection: str,
        document_id: str,
    ) -> None:
        """
        Delete a document.

        Args:
            collection: Collection path
            document_id: Document ID to delete

        Raises:
            FirestoreError: If deletion fails
        """
        try:
            doc_ref = self.client.collection(collection).document(document_id)
            doc_ref.delete()

        except Exception as e:
            raise FirestoreError(
                f"Failed to delete document '{document_id}' from '{collection}': {e}",
                details={
                    "collection": collection,
                    "document_id": document_id,
                    "error": str(e),
                },
            )

    def list_documents(
        self,
        collection: str,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        direction: str = "ASCENDING",
    ) -> list[FirestoreDocument]:
        """
        List all documents in a collection.

        Args:
            collection: Collection path
            limit: Maximum number of documents to return
            order_by: Field to order by
            direction: Sort direction (ASCENDING or DESCENDING)

        Returns:
            List of FirestoreDocument objects

        Raises:
            FirestoreError: If listing fails
        """
        try:
            query = self.client.collection(collection)

            if order_by:
                direction_enum = (
                    firestore.Query.DESCENDING
                    if direction == "DESCENDING"
                    else firestore.Query.ASCENDING
                )
                query = query.order_by(order_by, direction=direction_enum)

            if limit:
                query = query.limit(limit)

            docs = query.stream()

            return [
                FirestoreDocument(
                    id=doc.id,
                    collection=collection,
                    data=doc.to_dict(),
                    create_time=doc.create_time,
                    update_time=doc.update_time,
                )
                for doc in docs
            ]

        except Exception as e:
            raise FirestoreError(
                f"Failed to list documents in '{collection}': {e}",
                details={"collection": collection, "error": str(e)},
            )

    def query_documents(
        self,
        collection: str,
        queries: list[FirestoreQuery],
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        direction: str = "ASCENDING",
    ) -> list[FirestoreDocument]:
        """
        Query documents with filters.

        Args:
            collection: Collection path
            queries: List of FirestoreQuery objects
            limit: Maximum number of documents to return
            order_by: Field to order by
            direction: Sort direction (ASCENDING or DESCENDING)

        Returns:
            List of matching FirestoreDocument objects

        Raises:
            ValidationError: If queries are invalid
            FirestoreError: If query fails
        """
        if not queries:
            raise ValidationError("At least one query is required")

        try:
            query = self.client.collection(collection)

            # Apply filters
            for q in queries:
                query = query.where(
                    filter=firestore.FieldFilter(
                        q.field,
                        q.operator.value,
                        q.value,
                    )
                )

            # Apply ordering
            if order_by:
                direction_enum = (
                    firestore.Query.DESCENDING
                    if direction == "DESCENDING"
                    else firestore.Query.ASCENDING
                )
                query = query.order_by(order_by, direction=direction_enum)

            # Apply limit
            if limit:
                query = query.limit(limit)

            docs = query.stream()

            return [
                FirestoreDocument(
                    id=doc.id,
                    collection=collection,
                    data=doc.to_dict(),
                    create_time=doc.create_time,
                    update_time=doc.update_time,
                )
                for doc in docs
            ]

        except ValidationError:
            raise
        except Exception as e:
            raise FirestoreError(
                f"Failed to query documents in '{collection}': {e}",
                details={"collection": collection, "error": str(e)},
            )

    def batch_write(
        self,
        operations: list[dict[str, Any]],
    ) -> None:
        """
        Perform batch write operations.

        Args:
            operations: List of operations, each with:
                - operation: 'set', 'update', or 'delete'
                - collection: Collection path
                - document_id: Document ID
                - data: Data for set/update operations
                - merge: Whether to merge (for set operations)

        Raises:
            ValidationError: If operations are invalid
            FirestoreError: If batch write fails

        Example:
            >>> operations = [
            ...     {
            ...         "operation": "set",
            ...         "collection": "users",
            ...         "document_id": "user1",
            ...         "data": {"name": "John"},
            ...     },
            ...     {
            ...         "operation": "delete",
            ...         "collection": "users",
            ...         "document_id": "user2",
            ...     },
            ... ]
            >>> fs_ctrl.batch_write(operations)
        """
        if not operations:
            raise ValidationError("Operations list cannot be empty")

        try:
            batch = self.client.batch()

            for op in operations:
                operation_type = op.get("operation")
                collection = op.get("collection")
                document_id = op.get("document_id")

                if not all([operation_type, collection, document_id]):
                    raise ValidationError(
                        "Each operation must have 'operation', 'collection', and 'document_id'"
                    )

                doc_ref = self.client.collection(collection).document(document_id)

                if operation_type == "set":
                    data = op.get("data")
                    if not data:
                        raise ValidationError("'set' operation requires 'data'")
                    merge = op.get("merge", True)
                    batch.set(doc_ref, data, merge=merge)

                elif operation_type == "update":
                    data = op.get("data")
                    if not data:
                        raise ValidationError("'update' operation requires 'data'")
                    batch.update(doc_ref, data)

                elif operation_type == "delete":
                    batch.delete(doc_ref)

                else:
                    raise ValidationError(
                        f"Invalid operation type: {operation_type}. "
                        "Must be 'set', 'update', or 'delete'"
                    )

            batch.commit()

        except ValidationError:
            raise
        except Exception as e:
            raise FirestoreError(
                f"Batch write failed: {e}",
                details={"error": str(e)},
            )

    def run_transaction(
        self,
        transaction_func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Run a transaction.

        Args:
            transaction_func: Function to run in transaction.
                Must accept transaction as first argument.
            *args: Additional positional arguments for transaction_func
            **kwargs: Additional keyword arguments for transaction_func

        Returns:
            Result of transaction_func

        Raises:
            FirestoreError: If transaction fails

        Example:
            >>> def update_balance(transaction, user_id, amount):
            ...     doc_ref = fs_ctrl.client.collection('users').document(user_id)
            ...     snapshot = doc_ref.get(transaction=transaction)
            ...     new_balance = snapshot.get('balance') + amount
            ...     transaction.update(doc_ref, {'balance': new_balance})
            ...     return new_balance
            >>>
            >>> new_balance = fs_ctrl.run_transaction(update_balance, 'user123', 100)
        """
        try:
            transaction = self.client.transaction()
            return transaction_func(transaction, *args, **kwargs)

        except Exception as e:
            raise FirestoreError(
                f"Transaction failed: {e}",
                details={"error": str(e)},
            )

    def collection_exists(self, collection: str) -> bool:
        """
        Check if a collection has any documents.

        Args:
            collection: Collection path

        Returns:
            True if collection has documents, False otherwise

        Raises:
            FirestoreError: If check fails
        """
        try:
            docs = self.client.collection(collection).limit(1).stream()
            return len(list(docs)) > 0

        except Exception as e:
            raise FirestoreError(
                f"Failed to check collection '{collection}': {e}",
                details={"collection": collection, "error": str(e)},
            )

    def delete_collection(
        self,
        collection: str,
        batch_size: int = 100,
    ) -> int:
        """
        Delete all documents in a collection.

        Args:
            collection: Collection path
            batch_size: Number of documents to delete per batch

        Returns:
            Number of documents deleted

        Raises:
            FirestoreError: If deletion fails
        """
        try:
            col_ref = self.client.collection(collection)
            deleted = 0

            while True:
                docs = list(col_ref.limit(batch_size).stream())

                if not docs:
                    break

                batch = self.client.batch()
                for doc in docs:
                    batch.delete(doc.reference)

                batch.commit()
                deleted += len(docs)

            return deleted

        except Exception as e:
            raise FirestoreError(
                f"Failed to delete collection '{collection}': {e}",
                details={"collection": collection, "error": str(e)},
            )

    def get_subcollections(
        self,
        collection: str,
        document_id: str,
    ) -> list[str]:
        """
        Get all subcollections of a document.

        Args:
            collection: Parent collection path
            document_id: Parent document ID

        Returns:
            List of subcollection IDs

        Raises:
            FirestoreError: If operation fails
        """
        try:
            doc_ref = self.client.collection(collection).document(document_id)
            subcollections = doc_ref.collections()

            return [subcol.id for subcol in subcollections]

        except Exception as e:
            raise FirestoreError(
                f"Failed to get subcollections for '{collection}/{document_id}': {e}",
                details={
                    "collection": collection,
                    "document_id": document_id,
                    "error": str(e),
                },
            )
