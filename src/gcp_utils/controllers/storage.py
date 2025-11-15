"""
Cloud Storage controller for managing GCS buckets and blobs.

This module provides a high-level interface for common Cloud Storage operations
including bucket management, file uploads/downloads, and blob operations.
"""

import mimetypes
from datetime import timedelta
from pathlib import Path
from typing import Any, BinaryIO, Optional

import aiofiles
from google.cloud import storage
from google.cloud.storage import Blob, Bucket
from google.auth.credentials import Credentials

from ..config import GCPSettings
from ..exceptions import StorageError, ResourceNotFoundError, ValidationError
from ..models.storage import BlobMetadata, BucketInfo, UploadResult


class CloudStorageController:
    """
    Controller for Google Cloud Storage operations.

    This controller provides methods for managing buckets and blobs,
    including uploads, downloads, listing, and metadata operations.

    Example:
        >>> from gcp_utils.config import GCPSettings
        >>> from gcp_utils.controllers import CloudStorageController
        >>>
        >>> settings = GCPSettings(project_id="my-project")
        >>> storage_ctrl = CloudStorageController(settings)
        >>>
        >>> # Upload a file
        >>> result = storage_ctrl.upload_file(
        ...     "my-bucket",
        ...     "path/to/local/file.txt",
        ...     "destination/file.txt"
        ... )
    """

    def __init__(
        self,
        settings: GCPSettings,
        credentials: Optional[Credentials] = None,
    ) -> None:
        """
        Initialize the Cloud Storage controller.

        Args:
            settings: GCP configuration settings
            credentials: Optional custom credentials. If not provided, uses default credentials.

        Raises:
            StorageError: If client initialization fails
        """
        self.settings = settings
        try:
            self.client = storage.Client(
                project=settings.project_id,
                credentials=credentials,
            )
        except Exception as e:
            raise StorageError(
                f"Failed to initialize Storage client: {e}",
                details={"error": str(e)},
            )

    def create_bucket(
        self,
        bucket_name: str,
        location: Optional[str] = None,
        storage_class: str = "STANDARD",
        labels: Optional[dict[str, str]] = None,
    ) -> BucketInfo:
        """
        Create a new Cloud Storage bucket.

        Args:
            bucket_name: Name of the bucket to create
            location: Bucket location (defaults to settings.location)
            storage_class: Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
            labels: Optional labels for the bucket

        Returns:
            BucketInfo object with bucket details

        Raises:
            StorageError: If bucket creation fails
            ValidationError: If bucket name is invalid
        """
        if not bucket_name:
            raise ValidationError("Bucket name cannot be empty")

        try:
            bucket = self.client.bucket(bucket_name)
            bucket.storage_class = storage_class

            if labels:
                bucket.labels = labels

            created_bucket = self.client.create_bucket(
                bucket,
                location=location or self.settings.location,
            )

            return self._bucket_to_info(created_bucket)

        except Exception as e:
            raise StorageError(
                f"Failed to create bucket '{bucket_name}': {e}",
                details={"bucket": bucket_name, "error": str(e)},
            )

    def get_bucket(self, bucket_name: str) -> BucketInfo:
        """
        Get information about a bucket.

        Args:
            bucket_name: Name of the bucket

        Returns:
            BucketInfo object

        Raises:
            ResourceNotFoundError: If bucket doesn't exist
            StorageError: If operation fails
        """
        try:
            bucket = self.client.get_bucket(bucket_name)
            return self._bucket_to_info(bucket)
        except Exception as e:
            if "404" in str(e):
                raise ResourceNotFoundError(
                    f"Bucket '{bucket_name}' not found",
                    details={"bucket": bucket_name},
                )
            raise StorageError(
                f"Failed to get bucket '{bucket_name}': {e}",
                details={"bucket": bucket_name, "error": str(e)},
            )

    def list_buckets(self, prefix: Optional[str] = None) -> list[BucketInfo]:
        """
        List all buckets in the project.

        Args:
            prefix: Optional prefix to filter bucket names

        Returns:
            List of BucketInfo objects

        Raises:
            StorageError: If listing fails
        """
        try:
            buckets = self.client.list_buckets(prefix=prefix)
            return [self._bucket_to_info(bucket) for bucket in buckets]
        except Exception as e:
            raise StorageError(
                f"Failed to list buckets: {e}",
                details={"error": str(e)},
            )

    def delete_bucket(self, bucket_name: str, force: bool = False) -> None:
        """
        Delete a bucket.

        Args:
            bucket_name: Name of the bucket to delete
            force: If True, delete all blobs in the bucket first

        Raises:
            StorageError: If deletion fails
        """
        try:
            bucket = self.client.bucket(bucket_name)

            if force:
                # Delete all blobs first
                blobs = bucket.list_blobs()
                for blob in blobs:
                    blob.delete()

            bucket.delete()

        except Exception as e:
            raise StorageError(
                f"Failed to delete bucket '{bucket_name}': {e}",
                details={"bucket": bucket_name, "error": str(e)},
            )

    def upload_file(
        self,
        bucket_name: str,
        source_path: str | Path,
        destination_blob_name: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
        public: bool = False,
    ) -> UploadResult:
        """
        Upload a file to Cloud Storage.

        Args:
            bucket_name: Name of the destination bucket
            source_path: Path to the local file
            destination_blob_name: Destination blob name/path
            content_type: Optional content type (auto-detected if not provided)
            metadata: Optional custom metadata
            public: If True, make the blob publicly accessible

        Returns:
            UploadResult with upload details

        Raises:
            ValidationError: If source file doesn't exist
            StorageError: If upload fails
        """
        source_path = Path(source_path)

        if not source_path.exists():
            raise ValidationError(
                f"Source file not found: {source_path}",
                details={"path": str(source_path)},
            )

        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)

            # Set content type
            if content_type:
                blob.content_type = content_type
            else:
                guessed_type, _ = mimetypes.guess_type(str(source_path))
                if guessed_type:
                    blob.content_type = guessed_type

            # Set metadata
            if metadata:
                blob.metadata = metadata

            # Upload file
            blob.upload_from_filename(str(source_path))

            # Make public if requested
            if public:
                blob.make_public()

            return UploadResult(
                blob_name=destination_blob_name,
                bucket=bucket_name,
                size=blob.size,
                public_url=blob.public_url if public else None,
                md5_hash=blob.md5_hash,
                generation=blob.generation,
            )

        except Exception as e:
            raise StorageError(
                f"Failed to upload file to '{bucket_name}/{destination_blob_name}': {e}",
                details={
                    "bucket": bucket_name,
                    "blob": destination_blob_name,
                    "error": str(e),
                },
            )

    def upload_from_string(
        self,
        bucket_name: str,
        destination_blob_name: str,
        content: str | bytes,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
        public: bool = False,
    ) -> UploadResult:
        """
        Upload content from a string or bytes to Cloud Storage.

        Args:
            bucket_name: Name of the destination bucket
            destination_blob_name: Destination blob name/path
            content: Content to upload (string or bytes)
            content_type: Content type
            metadata: Optional custom metadata
            public: If True, make the blob publicly accessible

        Returns:
            UploadResult with upload details

        Raises:
            StorageError: If upload fails
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)

            if content_type:
                blob.content_type = content_type

            if metadata:
                blob.metadata = metadata

            blob.upload_from_string(content)

            if public:
                blob.make_public()

            return UploadResult(
                blob_name=destination_blob_name,
                bucket=bucket_name,
                size=blob.size,
                public_url=blob.public_url if public else None,
                md5_hash=blob.md5_hash,
                generation=blob.generation,
            )

        except Exception as e:
            raise StorageError(
                f"Failed to upload content to '{bucket_name}/{destination_blob_name}': {e}",
                details={
                    "bucket": bucket_name,
                    "blob": destination_blob_name,
                    "error": str(e),
                },
            )

    def download_file(
        self,
        bucket_name: str,
        blob_name: str,
        destination_path: str | Path,
    ) -> Path:
        """
        Download a blob to a local file.

        Args:
            bucket_name: Source bucket name
            blob_name: Source blob name/path
            destination_path: Local destination path

        Returns:
            Path to the downloaded file

        Raises:
            ResourceNotFoundError: If blob doesn't exist
            StorageError: If download fails
        """
        destination_path = Path(destination_path)

        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            if not blob.exists():
                raise ResourceNotFoundError(
                    f"Blob '{blob_name}' not found in bucket '{bucket_name}'",
                    details={"bucket": bucket_name, "blob": blob_name},
                )

            # Create parent directories if they don't exist
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            blob.download_to_filename(str(destination_path))

            return destination_path

        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to download '{bucket_name}/{blob_name}': {e}",
                details={
                    "bucket": bucket_name,
                    "blob": blob_name,
                    "error": str(e),
                },
            )

    def download_as_bytes(
        self,
        bucket_name: str,
        blob_name: str,
    ) -> bytes:
        """
        Download a blob as bytes.

        Args:
            bucket_name: Source bucket name
            blob_name: Source blob name/path

        Returns:
            Blob content as bytes

        Raises:
            ResourceNotFoundError: If blob doesn't exist
            StorageError: If download fails
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            if not blob.exists():
                raise ResourceNotFoundError(
                    f"Blob '{blob_name}' not found in bucket '{bucket_name}'",
                    details={"bucket": bucket_name, "blob": blob_name},
                )

            return blob.download_as_bytes()

        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to download '{bucket_name}/{blob_name}': {e}",
                details={
                    "bucket": bucket_name,
                    "blob": blob_name,
                    "error": str(e),
                },
            )

    def download_as_text(
        self,
        bucket_name: str,
        blob_name: str,
        encoding: str = "utf-8",
    ) -> str:
        """
        Download a blob as text.

        Args:
            bucket_name: Source bucket name
            blob_name: Source blob name/path
            encoding: Text encoding (default: utf-8)

        Returns:
            Blob content as string

        Raises:
            ResourceNotFoundError: If blob doesn't exist
            StorageError: If download fails
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            if not blob.exists():
                raise ResourceNotFoundError(
                    f"Blob '{blob_name}' not found in bucket '{bucket_name}'",
                    details={"bucket": bucket_name, "blob": blob_name},
                )

            return blob.download_as_text(encoding=encoding)

        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to download '{bucket_name}/{blob_name}': {e}",
                details={
                    "bucket": bucket_name,
                    "blob": blob_name,
                    "error": str(e),
                },
            )

    def list_blobs(
        self,
        bucket_name: str,
        prefix: Optional[str] = None,
        delimiter: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> list[BlobMetadata]:
        """
        List blobs in a bucket.

        Args:
            bucket_name: Bucket name
            prefix: Filter to blobs with this prefix
            delimiter: Delimiter for hierarchical listing (e.g., '/')
            max_results: Maximum number of results

        Returns:
            List of BlobMetadata objects

        Raises:
            StorageError: If listing fails
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blobs = bucket.list_blobs(
                prefix=prefix,
                delimiter=delimiter,
                max_results=max_results,
            )

            return [self._blob_to_metadata(blob) for blob in blobs]

        except Exception as e:
            raise StorageError(
                f"Failed to list blobs in '{bucket_name}': {e}",
                details={"bucket": bucket_name, "error": str(e)},
            )

    def get_blob_metadata(
        self,
        bucket_name: str,
        blob_name: str,
    ) -> BlobMetadata:
        """
        Get metadata for a specific blob.

        Args:
            bucket_name: Bucket name
            blob_name: Blob name/path

        Returns:
            BlobMetadata object

        Raises:
            ResourceNotFoundError: If blob doesn't exist
            StorageError: If operation fails
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            if not blob.exists():
                raise ResourceNotFoundError(
                    f"Blob '{blob_name}' not found in bucket '{bucket_name}'",
                    details={"bucket": bucket_name, "blob": blob_name},
                )

            blob.reload()
            return self._blob_to_metadata(blob)

        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to get metadata for '{bucket_name}/{blob_name}': {e}",
                details={
                    "bucket": bucket_name,
                    "blob": blob_name,
                    "error": str(e),
                },
            )

    def delete_blob(
        self,
        bucket_name: str,
        blob_name: str,
    ) -> None:
        """
        Delete a blob.

        Args:
            bucket_name: Bucket name
            blob_name: Blob name/path to delete

        Raises:
            StorageError: If deletion fails
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()

        except Exception as e:
            raise StorageError(
                f"Failed to delete '{bucket_name}/{blob_name}': {e}",
                details={
                    "bucket": bucket_name,
                    "blob": blob_name,
                    "error": str(e),
                },
            )

    def copy_blob(
        self,
        source_bucket: str,
        source_blob: str,
        destination_bucket: str,
        destination_blob: str,
    ) -> BlobMetadata:
        """
        Copy a blob to another location.

        Args:
            source_bucket: Source bucket name
            source_blob: Source blob name
            destination_bucket: Destination bucket name
            destination_blob: Destination blob name

        Returns:
            BlobMetadata of the new blob

        Raises:
            ResourceNotFoundError: If source blob doesn't exist
            StorageError: If copy fails
        """
        try:
            src_bucket = self.client.bucket(source_bucket)
            src_blob = src_bucket.blob(source_blob)

            if not src_blob.exists():
                raise ResourceNotFoundError(
                    f"Source blob '{source_blob}' not found in bucket '{source_bucket}'",
                    details={"bucket": source_bucket, "blob": source_blob},
                )

            dst_bucket = self.client.bucket(destination_bucket)

            new_blob = src_bucket.copy_blob(
                src_blob,
                dst_bucket,
                destination_blob,
            )

            return self._blob_to_metadata(new_blob)

        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to copy blob: {e}",
                details={
                    "source_bucket": source_bucket,
                    "source_blob": source_blob,
                    "destination_bucket": destination_bucket,
                    "destination_blob": destination_blob,
                    "error": str(e),
                },
            )

    def generate_signed_url(
        self,
        bucket_name: str,
        blob_name: str,
        expiration: timedelta = timedelta(hours=1),
        method: str = "GET",
    ) -> str:
        """
        Generate a signed URL for temporary blob access.

        Args:
            bucket_name: Bucket name
            blob_name: Blob name/path
            expiration: URL expiration time (default: 1 hour)
            method: HTTP method (GET, PUT, DELETE, etc.)

        Returns:
            Signed URL string

        Raises:
            StorageError: If URL generation fails
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            url = blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method=method,
            )

            return url

        except Exception as e:
            raise StorageError(
                f"Failed to generate signed URL for '{bucket_name}/{blob_name}': {e}",
                details={
                    "bucket": bucket_name,
                    "blob": blob_name,
                    "error": str(e),
                },
            )

    def _bucket_to_info(self, bucket: Bucket) -> BucketInfo:
        """Convert a Bucket object to BucketInfo model."""
        return BucketInfo(
            name=bucket.name,
            location=bucket.location,
            storage_class=bucket.storage_class,
            created=bucket.time_created,
            versioning_enabled=bucket.versioning_enabled or False,
            labels=bucket.labels or {},
        )

    def _blob_to_metadata(self, blob: Blob) -> BlobMetadata:
        """Convert a Blob object to BlobMetadata model."""
        return BlobMetadata(
            name=blob.name,
            bucket=blob.bucket.name,
            size=blob.size or 0,
            content_type=blob.content_type,
            md5_hash=blob.md5_hash,
            created=blob.time_created,
            updated=blob.updated,
            generation=blob.generation,
            metageneration=blob.metageneration,
            public_url=blob.public_url if blob.public_url else None,
            metadata=blob.metadata or {},
        )
