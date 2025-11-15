"""Data models for Cloud Tasks operations."""

from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field


class TaskSchedule(BaseModel):
    """Schedule configuration for a Cloud Task."""

    schedule_time: Optional[datetime] = Field(
        None, description="When to execute the task"
    )
    delay: Optional[timedelta] = Field(None, description="Delay before execution")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            timedelta: lambda v: v.total_seconds(),
        }


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

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TaskInfo(BaseModel):
    """Information about a created task."""

    name: str = Field(..., description="Full task name/path")
    task_id: str = Field(..., description="Task ID")
    queue_name: str = Field(..., description="Queue name")
    schedule_time: Optional[datetime] = Field(None, description="Scheduled execution time")
    dispatch_count: int = Field(default=0, description="Number of dispatch attempts")
    response_count: int = Field(default=0, description="Number of responses received")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
