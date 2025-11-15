"""Data models for Cloud Storage operations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BlobMetadata(BaseModel):
    """Metadata for a Cloud Storage blob."""

    name: str = Field(..., description="Blob name/path")
    bucket: str = Field(..., description="Bucket name")
    size: int = Field(..., description="Size in bytes")
    content_type: Optional[str] = Field(None, description="Content type")
    md5_hash: Optional[str] = Field(None, description="MD5 hash")
    created: Optional[datetime] = Field(None, description="Creation timestamp")
    updated: Optional[datetime] = Field(None, description="Last update timestamp")
    generation: Optional[int] = Field(None, description="Object generation number")
    metageneration: Optional[int] = Field(None, description="Metadata generation number")
    public_url: Optional[str] = Field(None, description="Public URL if publicly accessible")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Custom metadata key-value pairs"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class BucketInfo(BaseModel):
    """Information about a Cloud Storage bucket."""

    name: str = Field(..., description="Bucket name")
    location: str = Field(..., description="Bucket location")
    storage_class: str = Field(..., description="Storage class (STANDARD, NEARLINE, etc.)")
    created: Optional[datetime] = Field(None, description="Creation timestamp")
    versioning_enabled: bool = Field(default=False, description="Whether versioning is enabled")
    labels: dict[str, str] = Field(default_factory=dict, description="Bucket labels")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UploadResult(BaseModel):
    """Result of a file upload operation."""

    blob_name: str = Field(..., description="Name of the uploaded blob")
    bucket: str = Field(..., description="Bucket name")
    size: int = Field(..., description="Size in bytes")
    public_url: Optional[str] = Field(None, description="Public URL if available")
    md5_hash: Optional[str] = Field(None, description="MD5 hash of uploaded content")
    generation: Optional[int] = Field(None, description="Object generation number")
