"""Data models for Firestore operations."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_serializer


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
    """Represents a Firestore document."""

    id: str = Field(..., description="Document ID")
    collection: str = Field(..., description="Collection path")
    data: dict[str, Any] = Field(..., description="Document data")
    create_time: Optional[datetime] = Field(None, description="Document creation time")
    update_time: Optional[datetime] = Field(None, description="Last update time")

    @field_serializer("create_time", "update_time")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None
