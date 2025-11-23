"""
Utility for creating ZIP archives from directories.

This module provides functionality for zipping directories and optionally
uploading them to Cloud Storage, useful for deploying to Cloud Functions,
Cloud Run (via Cloud Build), and other GCP services.
"""

import tempfile
import zipfile
from pathlib import Path

from ..controllers.storage import CloudStorageController
from ..exceptions import StorageError, ValidationError
from ..models.storage import UploadResult


class ZipUtility:
    """
    Utility for creating ZIP archives and uploading to Cloud Storage.

    This utility simplifies the workflow of packaging source code directories
    into ZIP files and optionally uploading them to Cloud Storage for deployment.

    Example:
        ```python
        from gcp_utils.utils import ZipUtility

        # Create utility instance
        zip_util = ZipUtility()

        # Zip a directory
        zip_path = zip_util.zip_directory(
            source_dir="./my-app",
            output_path="./my-app.zip",
            exclude_patterns=["*.pyc", "__pycache__", ".git", "venv"],
        )
        print(f"Created: {zip_path}")

        # Zip and upload in one step
        upload_result = zip_util.zip_and_upload(
            source_dir="./my-app",
            bucket_name="my-deployment-bucket",
            destination_blob_name="functions/my-app.zip",
            exclude_patterns=["*.pyc", "__pycache__"],
        )
        print(f"Uploaded to: gs://{upload_result.bucket}/{upload_result.blob_name}")
        ```
    """

    def __init__(self, storage_controller: CloudStorageController | None = None):
        """
        Initialize the ZipUtility.

        Args:
            storage_controller: Optional CloudStorageController instance.
                If not provided, creates one with default settings when needed.
        """
        self._storage_controller = storage_controller

    def _get_storage_controller(self) -> CloudStorageController:
        """Lazy initialization of storage controller."""
        if self._storage_controller is None:
            self._storage_controller = CloudStorageController()
        return self._storage_controller

    def _should_exclude(self, file_path: Path, exclude_patterns: list[str]) -> bool:
        """
        Check if a file should be excluded based on patterns.

        Args:
            file_path: Path to check
            exclude_patterns: List of patterns to exclude (supports wildcards)

        Returns:
            True if file should be excluded, False otherwise
        """
        file_str = str(file_path)
        parts = file_path.parts

        for pattern in exclude_patterns:
            # Check if pattern is in any part of the path
            if pattern in parts:
                return True

            # Check wildcard patterns
            if "*" in pattern:
                import fnmatch

                if fnmatch.fnmatch(file_path.name, pattern):
                    return True

            # Check if pattern matches anywhere in path
            if pattern in file_str:
                return True

        return False

    def zip_directory(
        self,
        source_dir: str | Path,
        output_path: str | Path | None = None,
        exclude_patterns: list[str] | None = None,
        compression: int = zipfile.ZIP_DEFLATED,
        compression_level: int = 6,
    ) -> Path:
        """
        Create a ZIP archive from a directory.

        Args:
            source_dir: Directory to zip
            output_path: Output ZIP file path. If not provided, creates a temporary file.
            exclude_patterns: List of patterns to exclude (e.g., "*.pyc", "__pycache__", ".git")
            compression: Compression method (default: ZIP_DEFLATED)
            compression_level: Compression level 0-9 (default: 6)

        Returns:
            Path to the created ZIP file

        Raises:
            ValidationError: If source directory doesn't exist or is invalid
            StorageError: If ZIP creation fails

        Example:
            ```python
            zip_util = ZipUtility()

            # Zip with default exclusions
            zip_path = zip_util.zip_directory(
                source_dir="./my-app",
                output_path="./my-app.zip",
                exclude_patterns=[
                    "*.pyc",
                    "__pycache__",
                    ".git",
                    ".env",
                    "venv",
                    "node_modules",
                    ".DS_Store",
                ],
            )
            ```
        """
        source_dir = Path(source_dir)

        # Validate source directory
        if not source_dir.exists():
            raise ValidationError(
                f"Source directory does not exist: {source_dir}",
                details={"source_dir": str(source_dir)},
            )

        if not source_dir.is_dir():
            raise ValidationError(
                f"Source path is not a directory: {source_dir}",
                details={"source_dir": str(source_dir)},
            )

        # Use default exclusions if none provided
        if exclude_patterns is None:
            exclude_patterns = [
                "*.pyc",
                "__pycache__",
                ".git",
                ".gitignore",
                ".env",
                "venv",
                ".venv",
                "node_modules",
                ".DS_Store",
                "*.log",
            ]

        # Create output path
        if output_path is None:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".zip", delete=False, prefix=f"{source_dir.name}_"
            )
            output_path = Path(temp_file.name)
            temp_file.close()
        else:
            output_path = Path(output_path)
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Create ZIP file
            with zipfile.ZipFile(
                output_path,
                "w",
                compression=compression,
                compresslevel=compression_level,
            ) as zipf:
                # Walk through directory
                for file_path in source_dir.rglob("*"):
                    if file_path.is_file():
                        # Check if should be excluded
                        if self._should_exclude(file_path, exclude_patterns):
                            continue

                        # Add file to ZIP with relative path
                        arcname = file_path.relative_to(source_dir)
                        zipf.write(file_path, arcname)

            return output_path

        except Exception as e:
            # Clean up output file if it was created
            if output_path.exists():
                output_path.unlink()

            raise StorageError(
                f"Failed to create ZIP archive: {str(e)}",
                details={
                    "source_dir": str(source_dir),
                    "output_path": str(output_path),
                    "error": str(e),
                },
            ) from e

    def zip_and_upload(
        self,
        source_dir: str | Path,
        bucket_name: str,
        destination_blob_name: str,
        exclude_patterns: list[str] | None = None,
        cleanup: bool = True,
        public: bool = False,
        metadata: dict[str, str] | None = None,
    ) -> UploadResult:
        """
        Zip a directory and upload it to Cloud Storage in one step.

        Args:
            source_dir: Directory to zip
            bucket_name: Destination bucket name
            destination_blob_name: Destination blob name/path in the bucket
            exclude_patterns: List of patterns to exclude from ZIP
            cleanup: If True, delete the temporary ZIP file after upload (default: True)
            public: If True, make the uploaded blob publicly accessible
            metadata: Optional custom metadata for the blob

        Returns:
            UploadResult with upload details

        Raises:
            ValidationError: If source directory is invalid
            StorageError: If ZIP creation or upload fails

        Example:
            ```python
            zip_util = ZipUtility()

            # Zip and upload to Cloud Storage
            result = zip_util.zip_and_upload(
                source_dir="./my-function",
                bucket_name="my-deployment-bucket",
                destination_blob_name="functions/my-function-v1.zip",
                exclude_patterns=["*.pyc", "__pycache__", "tests"],
            )

            print(f"Uploaded to: gs://{result.bucket}/{result.blob_name}")
            print(f"Size: {result.size} bytes")
            print(f"MD5: {result.md5_hash}")
            ```
        """
        # Create ZIP file (temporary)
        zip_path = self.zip_directory(
            source_dir=source_dir,
            output_path=None,  # Use temporary file
            exclude_patterns=exclude_patterns,
        )

        try:
            # Upload to Cloud Storage
            storage = self._get_storage_controller()
            upload_result = storage.upload_file(
                bucket_name=bucket_name,
                source_path=zip_path,
                destination_blob_name=destination_blob_name,
                content_type="application/zip",
                metadata=metadata,
                public=public,
            )

            return upload_result

        finally:
            # Clean up temporary ZIP file
            if cleanup and zip_path.exists():
                zip_path.unlink()

    def get_zip_size(self, zip_path: str | Path) -> int:
        """
        Get the size of a ZIP file in bytes.

        Args:
            zip_path: Path to the ZIP file

        Returns:
            Size in bytes

        Raises:
            ValidationError: If ZIP file doesn't exist

        Example:
            ```python
            zip_util = ZipUtility()
            size = zip_util.get_zip_size("./my-app.zip")
            print(f"ZIP size: {size / (1024 * 1024):.2f} MB")
            ```
        """
        zip_path = Path(zip_path)

        if not zip_path.exists():
            raise ValidationError(
                f"ZIP file does not exist: {zip_path}",
                details={"zip_path": str(zip_path)},
            )

        return zip_path.stat().st_size

    def list_zip_contents(self, zip_path: str | Path) -> list[str]:
        """
        List the contents of a ZIP file.

        Args:
            zip_path: Path to the ZIP file

        Returns:
            List of file paths in the ZIP

        Raises:
            ValidationError: If ZIP file doesn't exist or is invalid

        Example:
            ```python
            zip_util = ZipUtility()
            contents = zip_util.list_zip_contents("./my-app.zip")
            print("ZIP contents:")
            for file in contents:
                print(f"  - {file}")
            ```
        """
        zip_path = Path(zip_path)

        if not zip_path.exists():
            raise ValidationError(
                f"ZIP file does not exist: {zip_path}",
                details={"zip_path": str(zip_path)},
            )

        try:
            with zipfile.ZipFile(zip_path, "r") as zipf:
                return zipf.namelist()
        except zipfile.BadZipFile as e:
            raise ValidationError(
                f"Invalid ZIP file: {zip_path}",
                details={"zip_path": str(zip_path), "error": str(e)},
            ) from e


# Convenience functions for quick usage
def zip_directory(
    source_dir: str | Path,
    output_path: str | Path | None = None,
    exclude_patterns: list[str] | None = None,
) -> Path:
    """
    Convenience function to zip a directory.

    Args:
        source_dir: Directory to zip
        output_path: Output ZIP file path (optional)
        exclude_patterns: List of patterns to exclude

    Returns:
        Path to the created ZIP file

    Example:
        ```python
        from gcp_utils.utils import zip_directory

        zip_path = zip_directory(
            "./my-app",
            "./my-app.zip",
            exclude_patterns=["*.pyc", "__pycache__"],
        )
        ```
    """
    util = ZipUtility()
    return util.zip_directory(source_dir, output_path, exclude_patterns)


def zip_and_upload(
    source_dir: str | Path,
    bucket_name: str,
    destination_blob_name: str,
    exclude_patterns: list[str] | None = None,
) -> UploadResult:
    """
    Convenience function to zip a directory and upload to Cloud Storage.

    Args:
        source_dir: Directory to zip
        bucket_name: Destination bucket name
        destination_blob_name: Destination blob name/path
        exclude_patterns: List of patterns to exclude

    Returns:
        UploadResult with upload details

    Example:
        ```python
        from gcp_utils.utils import zip_and_upload

        result = zip_and_upload(
            "./my-function",
            "my-deployment-bucket",
            "functions/my-function.zip",
        )
        ```
    """
    util = ZipUtility()
    return util.zip_and_upload(
        source_dir, bucket_name, destination_blob_name, exclude_patterns
    )
