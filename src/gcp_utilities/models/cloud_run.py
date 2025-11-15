"""Data models for Cloud Run operations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TrafficTarget(BaseModel):
    """Traffic target for Cloud Run service."""

    revision_name: Optional[str] = Field(None, description="Revision name")
    percent: int = Field(..., description="Traffic percentage", ge=0, le=100)
    tag: Optional[str] = Field(None, description="Traffic tag")
    latest_revision: bool = Field(
        default=False, description="Whether to target latest revision"
    )


class ServiceRevision(BaseModel):
    """Cloud Run service revision information."""

    name: str = Field(..., description="Revision name")
    service_name: str = Field(..., description="Service name")
    image: str = Field(..., description="Container image")
    created: Optional[datetime] = Field(None, description="Creation timestamp")
    traffic_percent: int = Field(default=0, description="Percentage of traffic")
    max_instances: Optional[int] = Field(None, description="Maximum number of instances")
    min_instances: Optional[int] = Field(None, description="Minimum number of instances")
    timeout: Optional[int] = Field(None, description="Request timeout in seconds")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CloudRunService(BaseModel):
    """Cloud Run service information."""

    name: str = Field(..., description="Service name")
    region: str = Field(..., description="Service region")
    image: str = Field(..., description="Current container image")
    url: str = Field(..., description="Service URL")
    created: Optional[datetime] = Field(None, description="Creation timestamp")
    updated: Optional[datetime] = Field(None, description="Last update timestamp")
    latest_revision: Optional[str] = Field(None, description="Latest revision name")
    traffic: list[TrafficTarget] = Field(
        default_factory=list, description="Traffic split configuration"
    )
    labels: dict[str, str] = Field(default_factory=dict, description="Service labels")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
