"""
Tests for ZipUtility module.

Tests cover:
- Directory zipping with exclusions
- ZIP content validation
- Upload integration
- Error handling
"""

import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from gcp_utils.utils import ZipUtility, zip_directory, zip_and_upload
from gcp_utils.exceptions import ValidationError, StorageError
from gcp_utils.models.storage import UploadResult


@pytest.fixture
def sample_directory(tmp_path: Path) -> Path:
    """
    Create a sample directory structure for testing.

    Structure:
        /test_dir
            /main.py
            /requirements.txt
            /.env
            /test_main.py
            /__pycache__
                /main.cpython-312.pyc
            /subdir
                /utils.py
    """
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # Create files
    (test_dir / "main.py").write_text("def main(): pass")
    (test_dir / "requirements.txt").write_text("flask==3.0.0")
    (test_dir / ".env").write_text("SECRET=should_be_excluded")
    (test_dir / "test_main.py").write_text("def test_main(): pass")

    # Create __pycache__
    pycache = test_dir / "__pycache__"
    pycache.mkdir()
    (pycache / "main.cpython-312.pyc").write_text("bytecode")

    # Create subdirectory
    subdir = test_dir / "subdir"
    subdir.mkdir()
    (subdir / "utils.py").write_text("def util(): pass")

    return test_dir


@pytest.fixture
def zip_util() -> ZipUtility:
    """Create a ZipUtility instance."""
    return ZipUtility()


class TestZipDirectory:
    """Tests for zip_directory method."""

    def test_zip_directory_basic(self, zip_util: ZipUtility, sample_directory: Path, tmp_path: Path) -> None:
        """Test basic directory zipping."""
        output_path = tmp_path / "output.zip"

        result = zip_util.zip_directory(
            source_dir=sample_directory,
            output_path=output_path,
            exclude_patterns=[],  # Don't exclude anything
        )

        assert result.exists()
        assert result == output_path
        assert zipfile.is_zipfile(result)

        # Check ZIP contents
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
            assert "main.py" in names
            assert "requirements.txt" in names
            assert "subdir/utils.py" in names

    def test_zip_directory_with_exclusions(self, zip_util: ZipUtility, sample_directory: Path, tmp_path: Path) -> None:
        """Test directory zipping with exclusion patterns."""
        output_path = tmp_path / "output.zip"

        result = zip_util.zip_directory(
            source_dir=sample_directory,
            output_path=output_path,
            exclude_patterns=["*.pyc", "__pycache__", ".env", "test_*.py"],
        )

        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()

            # Should include
            assert "main.py" in names
            assert "requirements.txt" in names
            assert "subdir/utils.py" in names

            # Should exclude
            assert ".env" not in names
            assert "test_main.py" not in names
            assert not any(".pyc" in name for name in names)
            assert not any("__pycache__" in name for name in names)

    def test_zip_directory_default_exclusions(self, zip_util: ZipUtility, sample_directory: Path, tmp_path: Path) -> None:
        """Test that default exclusions work correctly."""
        output_path = tmp_path / "output.zip"

        # Use default exclusions (exclude_patterns=None)
        result = zip_util.zip_directory(
            source_dir=sample_directory,
            output_path=output_path,
            exclude_patterns=None,
        )

        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()

            # Should include
            assert "main.py" in names
            assert "requirements.txt" in names

            # Should exclude (default patterns)
            assert ".env" not in names
            assert not any(".pyc" in name for name in names)
            assert not any("__pycache__" in name for name in names)

    def test_zip_directory_temp_file(self, zip_util: ZipUtility, sample_directory: Path) -> None:
        """Test zipping to a temporary file (no output_path specified)."""
        result = zip_util.zip_directory(
            source_dir=sample_directory,
            output_path=None,  # Should create temp file
        )

        assert result.exists()
        assert zipfile.is_zipfile(result)

        # Clean up
        result.unlink()

    def test_zip_directory_nonexistent_source(self, zip_util: ZipUtility, tmp_path: Path) -> None:
        """Test zipping a non-existent directory."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(ValidationError) as exc_info:
            zip_util.zip_directory(
                source_dir=nonexistent,
                output_path=tmp_path / "output.zip",
            )

        assert "does not exist" in str(exc_info.value)

    def test_zip_directory_source_is_file(self, zip_util: ZipUtility, tmp_path: Path) -> None:
        """Test zipping when source is a file, not a directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        with pytest.raises(ValidationError) as exc_info:
            zip_util.zip_directory(
                source_dir=file_path,
                output_path=tmp_path / "output.zip",
            )

        assert "not a directory" in str(exc_info.value)

    def test_zip_directory_creates_parent_dirs(self, zip_util: ZipUtility, sample_directory: Path, tmp_path: Path) -> None:
        """Test that parent directories are created if they don't exist."""
        output_path = tmp_path / "nested" / "dirs" / "output.zip"

        result = zip_util.zip_directory(
            source_dir=sample_directory,
            output_path=output_path,
        )

        assert result.exists()
        assert result.parent.exists()


class TestZipUtilityHelpers:
    """Tests for helper methods."""

    def test_get_zip_size(self, zip_util: ZipUtility, sample_directory: Path, tmp_path: Path) -> None:
        """Test getting ZIP file size."""
        zip_path = tmp_path / "test.zip"
        zip_util.zip_directory(sample_directory, zip_path)

        size = zip_util.get_zip_size(zip_path)

        assert size > 0
        assert size == zip_path.stat().st_size

    def test_get_zip_size_nonexistent(self, zip_util: ZipUtility, tmp_path: Path) -> None:
        """Test getting size of non-existent ZIP."""
        with pytest.raises(ValidationError) as exc_info:
            zip_util.get_zip_size(tmp_path / "nonexistent.zip")

        assert "does not exist" in str(exc_info.value)

    def test_list_zip_contents(self, zip_util: ZipUtility, sample_directory: Path, tmp_path: Path) -> None:
        """Test listing ZIP contents."""
        zip_path = tmp_path / "test.zip"
        zip_util.zip_directory(sample_directory, zip_path, exclude_patterns=[])

        contents = zip_util.list_zip_contents(zip_path)

        assert isinstance(contents, list)
        assert len(contents) > 0
        assert "main.py" in contents
        assert "requirements.txt" in contents

    def test_list_zip_contents_nonexistent(self, zip_util: ZipUtility, tmp_path: Path) -> None:
        """Test listing contents of non-existent ZIP."""
        with pytest.raises(ValidationError) as exc_info:
            zip_util.list_zip_contents(tmp_path / "nonexistent.zip")

        assert "does not exist" in str(exc_info.value)

    def test_list_zip_contents_invalid_zip(self, zip_util: ZipUtility, tmp_path: Path) -> None:
        """Test listing contents of invalid ZIP file."""
        invalid_zip = tmp_path / "invalid.zip"
        invalid_zip.write_text("not a zip file")

        with pytest.raises(ValidationError) as exc_info:
            zip_util.list_zip_contents(invalid_zip)

        assert "Invalid ZIP file" in str(exc_info.value)


class TestZipAndUpload:
    """Tests for zip_and_upload method."""

    def test_zip_and_upload_success(self, sample_directory: Path) -> None:
        """Test successful zip and upload."""
        # Mock storage controller
        mock_storage = Mock()
        mock_storage.upload_file.return_value = UploadResult(
            blob_name="functions/test.zip",
            bucket="test-bucket",
            size=1024,
            public_url=None,
            md5_hash="abc123",
            generation=1,
        )

        zip_util = ZipUtility(storage_controller=mock_storage)

        result = zip_util.zip_and_upload(
            source_dir=sample_directory,
            bucket_name="test-bucket",
            destination_blob_name="functions/test.zip",
            cleanup=True,
        )

        # Verify upload was called
        assert mock_storage.upload_file.called
        call_args = mock_storage.upload_file.call_args

        # Check arguments
        assert call_args.kwargs["bucket_name"] == "test-bucket"
        assert call_args.kwargs["destination_blob_name"] == "functions/test.zip"
        assert call_args.kwargs["content_type"] == "application/zip"

        # Check result
        assert result.bucket == "test-bucket"
        assert result.blob_name == "functions/test.zip"
        assert result.size == 1024

    def test_zip_and_upload_with_metadata(self, sample_directory: Path) -> None:
        """Test zip and upload with custom metadata."""
        mock_storage = Mock()
        mock_storage.upload_file.return_value = UploadResult(
            blob_name="test.zip",
            bucket="test-bucket",
            size=1024,
            public_url=None,
            md5_hash="abc123",
            generation=1,
        )

        zip_util = ZipUtility(storage_controller=mock_storage)

        metadata = {"version": "1.0.0", "environment": "production"}

        zip_util.zip_and_upload(
            source_dir=sample_directory,
            bucket_name="test-bucket",
            destination_blob_name="test.zip",
            metadata=metadata,
        )

        call_args = mock_storage.upload_file.call_args
        assert call_args.kwargs["metadata"] == metadata

    def test_zip_and_upload_public(self, sample_directory: Path) -> None:
        """Test zip and upload with public access."""
        mock_storage = Mock()
        mock_storage.upload_file.return_value = UploadResult(
            blob_name="test.zip",
            bucket="test-bucket",
            size=1024,
            public_url="https://storage.googleapis.com/test-bucket/test.zip",
            md5_hash="abc123",
            generation=1,
        )

        zip_util = ZipUtility(storage_controller=mock_storage)

        result = zip_util.zip_and_upload(
            source_dir=sample_directory,
            bucket_name="test-bucket",
            destination_blob_name="test.zip",
            public=True,
        )

        call_args = mock_storage.upload_file.call_args
        assert call_args.kwargs["public"] is True
        assert result.public_url is not None


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_zip_directory_function(self, sample_directory: Path, tmp_path: Path) -> None:
        """Test zip_directory convenience function."""
        output_path = tmp_path / "output.zip"

        result = zip_directory(
            source_dir=sample_directory,
            output_path=output_path,
            exclude_patterns=["*.pyc", ".env"],
        )

        assert result.exists()
        assert zipfile.is_zipfile(result)

    def test_zip_and_upload_function(self, sample_directory: Path) -> None:
        """Test zip_and_upload convenience function."""
        with patch("gcp_utils.utils.zip_utils.CloudStorageController") as mock_controller_class:
            mock_storage = Mock()
            mock_storage.upload_file.return_value = UploadResult(
                blob_name="test.zip",
                bucket="test-bucket",
                size=1024,
                public_url=None,
                md5_hash="abc123",
                generation=1,
            )
            mock_controller_class.return_value = mock_storage

            result = zip_and_upload(
                source_dir=sample_directory,
                bucket_name="test-bucket",
                destination_blob_name="test.zip",
            )

            assert result.bucket == "test-bucket"
            assert mock_storage.upload_file.called


class TestExclusionPatterns:
    """Tests for exclusion pattern matching."""

    def test_should_exclude_exact_match(self, zip_util: ZipUtility) -> None:
        """Test exact pattern matching."""
        file_path = Path("test_dir") / "__pycache__" / "file.pyc"

        result = zip_util._should_exclude(file_path, ["__pycache__"])

        assert result is True

    def test_should_exclude_wildcard(self, zip_util: ZipUtility) -> None:
        """Test wildcard pattern matching."""
        file_path = Path("test_dir") / "main.pyc"

        result = zip_util._should_exclude(file_path, ["*.pyc"])

        assert result is True

    def test_should_not_exclude(self, zip_util: ZipUtility) -> None:
        """Test that non-matching patterns don't exclude."""
        file_path = Path("test_dir") / "main.py"

        result = zip_util._should_exclude(file_path, ["*.pyc", "__pycache__"])

        assert result is False

    def test_should_exclude_in_path(self, zip_util: ZipUtility) -> None:
        """Test pattern matching anywhere in path."""
        file_path = Path("test_dir") / ".git" / "config"

        result = zip_util._should_exclude(file_path, [".git"])

        assert result is True


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_zip_directory_cleans_up_on_error(self, tmp_path: Path) -> None:
        """Test that output file is cleaned up if an error occurs during zipping."""
        # Create a directory that will cause an error
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        output_path = tmp_path / "output.zip"

        zip_util = ZipUtility()

        # Mock zipfile.ZipFile to raise an error
        with patch("zipfile.ZipFile") as mock_zipfile:
            mock_zipfile.side_effect = Exception("Simulated error")

            with pytest.raises(StorageError):
                zip_util.zip_directory(test_dir, output_path)

            # Output file should not exist (cleaned up)
            assert not output_path.exists()

    def test_lazy_storage_controller_initialization(self, sample_directory: Path) -> None:
        """Test that storage controller is lazily initialized."""
        zip_util = ZipUtility()  # No storage controller provided

        # Storage controller should be None initially
        assert zip_util._storage_controller is None

        # Mock the storage controller creation
        with patch("gcp_utils.utils.zip_utils.CloudStorageController") as mock_controller_class:
            mock_storage = Mock()
            mock_storage.upload_file.return_value = UploadResult(
                blob_name="test.zip",
                bucket="test-bucket",
                size=1024,
                public_url=None,
                md5_hash="abc123",
                generation=1,
            )
            mock_controller_class.return_value = mock_storage

            # This should trigger lazy initialization
            zip_util.zip_and_upload(
                source_dir=sample_directory,
                bucket_name="test-bucket",
                destination_blob_name="test.zip",
            )

            # Controller should be created
            assert mock_controller_class.called
            assert zip_util._storage_controller is not None
