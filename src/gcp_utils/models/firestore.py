"""Data models for Firestore operations."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_serializer

if TYPE_CHECKING:
    from google.cloud.firestore_v1.document import DocumentReference


class QueryOperator(str, Enum):
    """Firestore query operators."""

    EQUAL = "=="
    NOT_EQUAL = "!="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    ARRAY_CONTAINS = "array_contains"
    ARRAY_CONTAINS_ANY = "array_contains_any"
    IN = "in"
    NOT_IN = "not_in"


class FirestoreQuery(BaseModel):
    """Query parameters for Firestore."""

    field: str = Field(..., description="Field name to query")
    operator: QueryOperator = Field(..., description="Query operator")
    value: Any = Field(..., description="Value to compare against")


class FirestoreDocument(BaseModel):
    """
    Represents a Firestore document with native object binding.

    The document exposes convenience methods that delegate to the native
    Firestore DocumentReference for operations like update, delete, etc.
    """

    id: str = Field(..., description="Document ID")
    collection: str = Field(..., description="Collection path")
    data: dict[str, Any] = Field(..., description="Document data")
    create_time: Optional[datetime] = Field(None, description="Document creation time")
    update_time: Optional[datetime] = Field(None, description="Last update time")

    # Private attribute for native Firestore DocumentReference
    _firestore_ref: Optional["DocumentReference"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("create_time", "update_time")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None

    def update(self, updates: dict[str, Any]) -> None:
        """
        Update document fields.

        Args:
            updates: Dictionary of field updates

        Raises:
            ValueError: If no Firestore reference is bound

        Example:
            ```python
            doc.update({"status": "active", "count": 10})
            ```
        """
        if not self._firestore_ref:
            raise ValueError("No Firestore reference bound to this document")
        self._firestore_ref.update(updates)
        # Update local data
        self.data.update(updates)

    def delete(self) -> None:
        """
        Delete this document from Firestore.

        Raises:
            ValueError: If no Firestore reference is bound

        Example:
            ```python
            doc.delete()
            ```
        """
        if not self._firestore_ref:
            raise ValueError("No Firestore reference bound to this document")
        self._firestore_ref.delete()

    def get(self) -> dict[str, Any]:
        """
        Refresh document data from Firestore.

        Returns:
            Updated document data

        Raises:
            ValueError: If no Firestore reference is bound

        Example:
            ```python
            fresh_data = doc.get()
            ```
        """
        if not self._firestore_ref:
            raise ValueError("No Firestore reference bound to this document")
        snapshot = self._firestore_ref.get()
        if snapshot.exists:
            self.data = snapshot.to_dict() or {}
            self.update_time = snapshot.update_time
            self.create_time = snapshot.create_time
        return self.data

    def set(self, data: dict[str, Any], merge: bool = False) -> None:
        """
        Set document data (replaces or merges).

        Args:
            data: Document data to set
            merge: If True, merge with existing data; if False, replace

        Raises:
            ValueError: If no Firestore reference is bound

        Example:
            ```python
            doc.set({"name": "John", "age": 30}, merge=True)
            ```
        """
        if not self._firestore_ref:
            raise ValueError("No Firestore reference bound to this document")
        self._firestore_ref.set(data, merge=merge)
        if merge:
            self.data.update(data)
        else:
            self.data = data

    @property
    def path(self) -> str:
        """Get the full document path."""
        if self._firestore_ref:
            return self._firestore_ref.path
        return f"{self.collection}/{self.id}"

    @property
    def parent(self) -> Optional[Any]:
        """Get the parent collection reference."""
        if self._firestore_ref:
            return self._firestore_ref.parent
        return None
