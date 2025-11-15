"""Data models for Cloud Tasks operations."""

from datetime import datetime, timedelta
from typing import Any, Optional

from pydantic import BaseModel, Field, field_serializer


class TaskSchedule(BaseModel):
    """Schedule configuration for a Cloud Task."""

    schedule_time: Optional[datetime] = Field(
        None, description="When to execute the task"
    )
    delay: Optional[timedelta] = Field(None, description="Delay before execution")

    @field_serializer("schedule_time")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None

    @field_serializer("delay")
    def serialize_td(self, td: Optional[timedelta], _info: Any) -> Optional[float]:
        return td.total_seconds() if td else None


class CloudTask(BaseModel):
    """Cloud Task information."""

    name: str = Field(..., description="Task name")
    queue_name: str = Field(..., description="Queue name")
    http_method: str = Field(default="POST", description="HTTP method")
    url: str = Field(..., description="Target URL")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    body: Optional[bytes | str] = Field(None, description="Request body")
    schedule_time: Optional[datetime] = Field(None, description="Scheduled execution time")
    created: Optional[datetime] = Field(None, description="Task creation time")

    @field_serializer("schedule_time", "created")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None


class TaskInfo(BaseModel):
    """Information about a created task."""

    name: str = Field(..., description="Full task name/path")
    task_id: str = Field(..., description="Task ID")
    queue_name: str = Field(..., description="Queue name")
    schedule_time: Optional[datetime] = Field(None, description="Scheduled execution time")
    dispatch_count: int = Field(default=0, description="Number of dispatch attempts")
    response_count: int = Field(default=0, description="Number of responses received")

    @field_serializer("schedule_time")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None
