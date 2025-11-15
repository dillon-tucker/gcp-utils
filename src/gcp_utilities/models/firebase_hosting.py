"""Data models for Firebase Hosting operations."""

from datetime import datetime
from typing import Optional, Any
from enum import Enum

from pydantic import BaseModel, Field


class DomainStatus(str, Enum):
    """Status of a custom domain."""

    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    PENDING_DEPLOYMENT = "PENDING_DEPLOYMENT"
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"


class VersionStatus(str, Enum):
    """Status of a hosting version."""

    CREATED = "CREATED"
    FINALIZED = "FINALIZED"
    DELETED = "DELETED"


class HostingSite(BaseModel):
    """Information about a Firebase Hosting site."""

    name: str = Field(..., description="Full resource name of the site")
    site_id: str = Field(..., description="Site identifier")
    default_url: str = Field(..., description="Default Firebase Hosting URL")
    app_id: Optional[str] = Field(None, description="Associated Firebase app ID")
    type: Optional[str] = Field(None, description="Site type")

    class Config:
        use_enum_values = True


class CustomDomain(BaseModel):
    """Information about a custom domain."""

    domain_name: str = Field(..., description="The custom domain name")
    status: DomainStatus = Field(..., description="Current status of the domain")
    provisioning: Optional[dict[str, Any]] = Field(
        None, description="DNS provisioning information"
    )
    update_time: Optional[datetime] = Field(None, description="Last update timestamp")
    cert: Optional[dict[str, Any]] = Field(None, description="SSL certificate information")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        use_enum_values = True


class HostingVersion(BaseModel):
    """Information about a hosting version."""

    name: str = Field(..., description="Full resource name of the version")
    version_id: str = Field(..., description="Version identifier")
    status: VersionStatus = Field(..., description="Version status")
    config: Optional[dict[str, Any]] = Field(None, description="Version configuration")
    create_time: Optional[datetime] = Field(None, description="Creation timestamp")
    finalize_time: Optional[datetime] = Field(None, description="Finalization timestamp")
    file_count: Optional[int] = Field(None, description="Number of files in version")
    version_bytes: Optional[int] = Field(None, description="Total size in bytes")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        use_enum_values = True


class HostingRelease(BaseModel):
    """Information about a hosting release."""

    name: str = Field(..., description="Full resource name of the release")
    version_name: str = Field(..., description="Version being released")
    message: Optional[str] = Field(None, description="Release message")
    release_time: Optional[datetime] = Field(None, description="Release timestamp")
    release_user: Optional[dict[str, str]] = Field(
        None, description="User who created the release"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class RedirectRule(BaseModel):
    """Configuration for a redirect rule."""

    source: str = Field(..., description="Source URL pattern")
    destination: str = Field(..., description="Destination URL")
    redirect_type: int = Field(
        301, description="HTTP redirect type (301 permanent, 302 temporary)"
    )


class RewriteRule(BaseModel):
    """Configuration for a rewrite rule."""

    source: str = Field(..., description="Source URL pattern to match")
    destination: Optional[str] = Field(None, description="Destination path")
    function: Optional[str] = Field(None, description="Cloud Function to invoke")
    run: Optional[dict[str, str]] = Field(None, description="Cloud Run service to invoke")


class HeaderRule(BaseModel):
    """Configuration for custom headers."""

    source: str = Field(..., description="URL pattern to match")
    headers: dict[str, str] = Field(..., description="Headers to set")


class HostingConfig(BaseModel):
    """Configuration for a hosting version."""

    redirects: list[RedirectRule] = Field(
        default_factory=list, description="Redirect rules"
    )
    rewrites: list[RewriteRule] = Field(
        default_factory=list, description="Rewrite rules"
    )
    headers: list[HeaderRule] = Field(
        default_factory=list, description="Custom header rules"
    )
    clean_urls: bool = Field(
        default=False, description="Whether to use clean URLs (remove .html extension)"
    )
    trailing_slash_behavior: Optional[str] = Field(
        None, description="How to handle trailing slashes (ADD, REMOVE)"
    )

    class Config:
        use_enum_values = True


class DeploymentInfo(BaseModel):
    """Information about a complete deployment."""

    site_id: str = Field(..., description="Site identifier")
    version_name: str = Field(..., description="Deployed version name")
    release_name: str = Field(..., description="Release name")
    default_url: str = Field(..., description="Default hosting URL")
    custom_domains: list[str] = Field(
        default_factory=list, description="Associated custom domains"
    )
    deployed_at: datetime = Field(..., description="Deployment timestamp")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class FileUploadResult(BaseModel):
    """Result of file upload operation."""

    total_file_count: int = Field(..., description="Total number of files")
    uploaded_file_count: int = Field(..., description="Number of files uploaded")
    cached_file_count: int = Field(..., description="Number of files already cached")
    upload_url: Optional[str] = Field(None, description="Upload URL used")


class DeploymentResult(BaseModel):
    """Result of a complete site deployment."""

    version_name: str = Field(..., description="Deployed version name")
    release_name: str = Field(..., description="Created release name")
    site_url: str = Field(..., description="Site URL")
    total_files: int = Field(..., description="Total files deployed")
    uploaded_files: int = Field(..., description="Newly uploaded files")
    cached_files: int = Field(..., description="Cached files")
    version_status: str = Field(..., description="Version status (should be FINALIZED)")
    success: bool = Field(default=True, description="Whether deployment succeeded")
