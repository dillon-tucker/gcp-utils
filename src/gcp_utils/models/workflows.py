"""Data models for Workflows operations."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_serializer


class ExecutionState(str, Enum):
    """Workflow execution states."""

    STATE_UNSPECIFIED = "STATE_UNSPECIFIED"
    ACTIVE = "ACTIVE"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowInfo(BaseModel):
    """Workflow information."""

    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    state: str = Field(..., description="Workflow state (ACTIVE, etc.)")
    created: Optional[datetime] = Field(None, description="Creation timestamp")
    updated: Optional[datetime] = Field(None, description="Last update timestamp")
    revision_id: Optional[str] = Field(None, description="Current revision ID")
    labels: dict[str, str] = Field(default_factory=dict, description="Workflow labels")

    @field_serializer("created", "updated")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None


class WorkflowExecution(BaseModel):
    """Workflow execution information."""

    name: str = Field(..., description="Execution name")
    workflow_name: str = Field(..., description="Workflow name")
    state: ExecutionState = Field(..., description="Execution state")
    argument: Optional[dict[str, Any]] = Field(
        None, description="Input arguments to the execution"
    )
    result: Optional[dict[str, Any]] = Field(None, description="Execution result")
    error: Optional[str] = Field(None, description="Error message if failed")
    start_time: Optional[datetime] = Field(None, description="Execution start time")
    end_time: Optional[datetime] = Field(None, description="Execution end time")

    @field_serializer("start_time", "end_time")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None
