"""Data models for Cloud Storage operations."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_serializer

if TYPE_CHECKING:
    from google.cloud.storage import Blob, Bucket


class BlobMetadata(BaseModel):
    """
    Metadata for a Cloud Storage blob.

    This model wraps the Google Cloud Storage Blob object, providing both
    structured Pydantic data and access to the full GCS API via `_gcs_object`.

    Example:
        >>> blob_meta = storage.get_blob_metadata("my-bucket", "file.txt")
        >>>
        >>> # Use Pydantic fields
        >>> print(f"Size: {blob_meta.size}")
        >>>
        >>> # Access full GCS API
        >>> blob_meta._gcs_object.make_public()
        >>> blob_meta._gcs_object.download_to_filename("local.txt")
        >>>
        >>> # Or use convenience methods
        >>> blob_meta.make_public()
        >>> signed_url = blob_meta.generate_signed_url()
    """

    name: str = Field(..., description="Blob name/path")
    bucket: str = Field(..., description="Bucket name")
    size: int = Field(..., description="Size in bytes")
    content_type: str | None = Field(None, description="Content type")
    md5_hash: str | None = Field(None, description="MD5 hash")
    created: datetime | None = Field(None, description="Creation timestamp")
    updated: datetime | None = Field(None, description="Last update timestamp")
    generation: int | None = Field(None, description="Object generation number")
    metageneration: int | None = Field(None, description="Metadata generation number")
    public_url: str | None = Field(
        None, description="Public URL if publicly accessible"
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Custom metadata key-value pairs"
    )

    # The actual GCS Blob object (private attribute, not serialized)
    _gcs_object: Optional["Blob"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("created", "updated")
    def serialize_dt(self, dt: datetime | None, _info: Any) -> str | None:
        return dt.isoformat() if dt else None

    # Convenience methods that delegate to the GCS object

    def reload(self) -> None:
        """
        Reload blob metadata from GCS.

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this metadata")
        self._gcs_object.reload()
        # Update Pydantic fields with fresh data
        self.size = self._gcs_object.size or 0
        self.content_type = self._gcs_object.content_type
        self.md5_hash = self._gcs_object.md5_hash
        self.updated = self._gcs_object.updated

    def make_public(self) -> None:
        """
        Make the blob publicly accessible.

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this metadata")
        self._gcs_object.make_public()
        self.public_url = self._gcs_object.public_url

    def make_private(self) -> None:
        """
        Make the blob private (remove public access).

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this metadata")
        self._gcs_object.make_private()
        self.public_url = None

    def delete(self) -> None:
        """
        Delete the blob from GCS.

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this metadata")
        self._gcs_object.delete()

    def download_as_bytes(self) -> bytes:
        """
        Download blob content as bytes.

        Returns:
            Blob content as bytes

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this metadata")
        return self._gcs_object.download_as_bytes()

    def download_as_text(self, encoding: str = "utf-8") -> str:
        """
        Download blob content as text.

        Args:
            encoding: Text encoding (default: utf-8)

        Returns:
            Blob content as string

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this metadata")
        return self._gcs_object.download_as_text(encoding=encoding)

    def download_to_filename(self, filename: str) -> None:
        """
        Download blob to a local file.

        Args:
            filename: Destination file path

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this metadata")
        self._gcs_object.download_to_filename(filename)

    def upload_from_filename(
        self, filename: str, content_type: str | None = None
    ) -> None:
        """
        Upload content from a local file.

        Args:
            filename: Source file path
            content_type: Optional content type override

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this metadata")
        if content_type:
            self._gcs_object.content_type = content_type
        self._gcs_object.upload_from_filename(filename)
        self.reload()  # Update metadata after upload

    def upload_from_string(
        self, data: str | bytes, content_type: str | None = None
    ) -> None:
        """
        Upload content from a string or bytes.

        Args:
            data: Content to upload
            content_type: Optional content type override

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this metadata")
        if content_type:
            self._gcs_object.content_type = content_type
        self._gcs_object.upload_from_string(data)
        self.reload()  # Update metadata after upload

    def generate_signed_url(
        self,
        expiration: timedelta = timedelta(hours=1),
        method: str = "GET",
    ) -> str:
        """
        Generate a signed URL for temporary access.

        Args:
            expiration: URL expiration time (default: 1 hour)
            method: HTTP method (GET, PUT, DELETE, etc.)

        Returns:
            Signed URL string

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this metadata")
        return self._gcs_object.generate_signed_url(
            version="v4",
            expiration=expiration,
            method=method,
        )

    def update_metadata(self, metadata: dict[str, str]) -> None:
        """
        Update blob custom metadata.

        Args:
            metadata: New metadata key-value pairs

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this metadata")
        self._gcs_object.metadata = metadata
        self._gcs_object.patch()
        self.metadata = metadata


class BucketInfo(BaseModel):
    """
    Information about a Cloud Storage bucket.

    This model wraps the Google Cloud Storage Bucket object, providing both
    structured Pydantic data and access to the full GCS API via `_gcs_object`.

    Example:
        >>> bucket_info = storage.get_bucket("my-bucket")
        >>>
        >>> # Use Pydantic fields
        >>> print(f"Location: {bucket_info.location}")
        >>>
        >>> # Access full GCS API
        >>> bucket_info._gcs_object.enable_versioning()
        >>> bucket_info._gcs_object.make_public()
        >>>
        >>> # Or use convenience methods
        >>> bucket_info.enable_versioning()
        >>> blobs = bucket_info.list_blobs(prefix="uploads/")
    """

    name: str = Field(..., description="Bucket name")
    location: str = Field(..., description="Bucket location")
    storage_class: str = Field(
        ..., description="Storage class (STANDARD, NEARLINE, etc.)"
    )
    created: datetime | None = Field(None, description="Creation timestamp")
    versioning_enabled: bool = Field(
        default=False, description="Whether versioning is enabled"
    )
    labels: dict[str, str] = Field(default_factory=dict, description="Bucket labels")

    # The actual GCS Bucket object (private attribute, not serialized)
    _gcs_object: Optional["Bucket"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("created")
    def serialize_dt(self, dt: datetime | None, _info: Any) -> str | None:
        return dt.isoformat() if dt else None

    # Convenience methods that delegate to the GCS object

    def reload(self) -> None:
        """
        Reload bucket metadata from GCS.

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this bucket info")
        self._gcs_object.reload()
        # Update Pydantic fields with fresh data
        self.versioning_enabled = self._gcs_object.versioning_enabled or False
        self.labels = self._gcs_object.labels or {}
        self.storage_class = self._gcs_object.storage_class

    def enable_versioning(self) -> None:
        """
        Enable versioning for the bucket.

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this bucket info")
        self._gcs_object.versioning_enabled = True
        self._gcs_object.patch()
        self.versioning_enabled = True

    def disable_versioning(self) -> None:
        """
        Disable versioning for the bucket.

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this bucket info")
        self._gcs_object.versioning_enabled = False
        self._gcs_object.patch()
        self.versioning_enabled = False

    def update_labels(self, labels: dict[str, str]) -> None:
        """
        Update bucket labels.

        Args:
            labels: New labels to set

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this bucket info")
        self._gcs_object.labels = labels
        self._gcs_object.patch()
        self.labels = labels

    def delete(self, force: bool = False) -> None:
        """
        Delete the bucket.

        Args:
            force: If True, delete all blobs in the bucket first

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this bucket info")

        if force:
            # Delete all blobs first
            blobs = self._gcs_object.list_blobs()
            for blob in blobs:
                blob.delete()

        self._gcs_object.delete()

    def list_blobs(
        self,
        prefix: str | None = None,
        delimiter: str | None = None,
        max_results: int | None = None,
    ) -> list["Blob"]:
        """
        List blobs in the bucket.

        Args:
            prefix: Filter to blobs with this prefix
            delimiter: Delimiter for hierarchical listing
            max_results: Maximum number of results

        Returns:
            List of Blob objects

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this bucket info")

        return list(
            self._gcs_object.list_blobs(
                prefix=prefix,
                delimiter=delimiter,
                max_results=max_results,
            )
        )

    def get_blob(self, blob_name: str) -> Optional["Blob"]:
        """
        Get a blob by name.

        Args:
            blob_name: Name of the blob

        Returns:
            Blob object if exists, None otherwise

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this bucket info")
        return self._gcs_object.get_blob(blob_name)

    def blob(self, blob_name: str) -> "Blob":
        """
        Get a blob reference (doesn't check if it exists).

        Args:
            blob_name: Name of the blob

        Returns:
            Blob object

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this bucket info")
        return self._gcs_object.blob(blob_name)


class UploadResult(BaseModel):
    """
    Result of a file upload operation.

    This model wraps the uploaded Blob object, providing both structured
    data and access to the full GCS API via `_gcs_object`.

    Example:
        >>> result = storage.upload_file("bucket", "local.txt", "remote.txt")
        >>>
        >>> # Use Pydantic fields
        >>> print(f"Uploaded {result.size} bytes")
        >>>
        >>> # Access the uploaded blob directly
        >>> result._gcs_object.make_public()
        >>> signed_url = result.generate_signed_url()
    """

    blob_name: str = Field(..., description="Name of the uploaded blob")
    bucket: str = Field(..., description="Bucket name")
    size: int = Field(..., description="Size in bytes")
    public_url: str | None = Field(None, description="Public URL if available")
    md5_hash: str | None = Field(None, description="MD5 hash of uploaded content")
    generation: int | None = Field(None, description="Object generation number")

    # The actual GCS Blob object (private attribute, not serialized)
    _gcs_object: Optional["Blob"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Convenience methods that delegate to the GCS object

    def make_public(self) -> None:
        """
        Make the uploaded blob publicly accessible.

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this upload result")
        self._gcs_object.make_public()
        self.public_url = self._gcs_object.public_url

    def generate_signed_url(
        self,
        expiration: timedelta = timedelta(hours=1),
        method: str = "GET",
    ) -> str:
        """
        Generate a signed URL for the uploaded blob.

        Args:
            expiration: URL expiration time (default: 1 hour)
            method: HTTP method (GET, PUT, DELETE, etc.)

        Returns:
            Signed URL string

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this upload result")
        return self._gcs_object.generate_signed_url(
            version="v4",
            expiration=expiration,
            method=method,
        )

    def delete(self) -> None:
        """
        Delete the uploaded blob.

        Raises:
            ValueError: If no GCS object is bound
        """
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this upload result")
        self._gcs_object.delete()
