"""
Tests for FirebaseHostingController.
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.firebase_hosting import FirebaseHostingController
from gcp_utils.exceptions import (
    FirebaseHostingError,
    ResourceNotFoundError,
    ValidationError,
)


@pytest.fixture
def settings():
    """Fixture for GCPSettings."""
    return GCPSettings()


@pytest.fixture
def firebase_hosting_controller(settings):
    """Fixture for FirebaseHostingController with mocked HTTP client."""
    with (
        patch("firebase_admin.get_app") as mock_get_app,
        patch("firebase_admin.initialize_app"),
        patch("google.auth.default") as mock_default,
    ):

        # Simulate Firebase already initialized
        mock_get_app.return_value = Mock()

        # Mock credentials
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.token = "mock-token"
        mock_default.return_value = (mock_creds, None)

        controller = FirebaseHostingController(settings)

        # Mock the HTTP client
        mock_client = MagicMock(spec=httpx.Client)
        controller._client = mock_client

        yield controller, mock_client


def test_create_site_success(firebase_hosting_controller):
    """Test creating a site successfully."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "projects/test-project/sites/my-site",
        "siteId": "my-site",
        "type": "DEFAULT_SITE",
    }
    mock_response.content = b'{"name": "..."}'

    mock_client.request.return_value = mock_response

    site = controller.create_site("my-site")

    assert site["siteId"] == "my-site"
    mock_client.request.assert_called_once()


def test_get_site_success(firebase_hosting_controller):
    """Test getting a site successfully."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "projects/test-project/sites/my-site",
        "siteId": "my-site",
        "defaultUrl": "https://my-site.web.app",
    }
    mock_response.content = b'{"name": "..."}'

    mock_client.request.return_value = mock_response

    site = controller.get_site("my-site")

    assert site["siteId"] == "my-site"
    assert site["defaultUrl"] == "https://my-site.web.app"


def test_get_site_not_found(firebase_hosting_controller):
    """Test getting a non-existent site."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 404

    mock_client.request.return_value = mock_response

    with pytest.raises(ResourceNotFoundError):
        controller.get_site("nonexistent-site")


def test_list_sites_success(firebase_hosting_controller):
    """Test listing sites successfully."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "sites": [
            {"siteId": "site1", "name": "projects/test-project/sites/site1"},
            {"siteId": "site2", "name": "projects/test-project/sites/site2"},
        ]
    }
    mock_response.content = b'{"sites": [...]}'

    mock_client.request.return_value = mock_response

    sites = controller.list_sites()

    assert len(sites) == 2
    assert sites[0]["siteId"] == "site1"
    assert sites[1]["siteId"] == "site2"


def test_delete_site_success(firebase_hosting_controller):
    """Test deleting a site successfully."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b""

    mock_client.request.return_value = mock_response

    controller.delete_site("my-site")

    mock_client.request.assert_called_once()
    call_args = mock_client.request.call_args
    assert call_args[1]["method"] == "DELETE"


def test_add_custom_domain_success(firebase_hosting_controller):
    """Test adding a custom domain successfully."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "domainName": "example.com",
        "status": "PENDING",
        "updateTime": "2025-01-01T00:00:00Z",
    }
    mock_response.content = b'{"domainName": "..."}'

    mock_client.request.return_value = mock_response

    domain = controller.add_custom_domain("my-site", "example.com")

    assert domain["domainName"] == "example.com"
    assert domain["status"] == "PENDING"


def test_get_domain_success(firebase_hosting_controller):
    """Test getting a domain successfully."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "domainName": "example.com",
        "status": "ACTIVE",
        "updateTime": "2025-01-01T00:00:00Z",
    }
    mock_response.content = b'{"domainName": "..."}'

    mock_client.request.return_value = mock_response

    domain = controller.get_domain("my-site", "example.com")

    assert domain["domainName"] == "example.com"
    assert domain["status"] == "ACTIVE"


def test_list_domains_success(firebase_hosting_controller):
    """Test listing domains successfully."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "domains": [
            {"domainName": "example.com", "status": "ACTIVE"},
            {"domainName": "test.com", "status": "PENDING"},
        ]
    }
    mock_response.content = b'{"domains": [...]}'

    mock_client.request.return_value = mock_response

    domains = controller.list_domains("my-site")

    assert len(domains) == 2
    assert domains[0]["domainName"] == "example.com"
    assert domains[1]["domainName"] == "test.com"


def test_delete_domain_success(firebase_hosting_controller):
    """Test deleting a domain successfully."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b""

    mock_client.request.return_value = mock_response

    controller.delete_domain("my-site", "example.com")

    mock_client.request.assert_called_once()


def test_create_version_success(firebase_hosting_controller):
    """Test creating a version successfully."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "projects/test-project/sites/my-site/versions/version123",
        "status": "CREATED",
        "config": {},
    }
    mock_response.content = b'{"name": "..."}'

    mock_client.request.return_value = mock_response

    version = controller.create_version("my-site")

    assert "version123" in version["name"]
    assert version["status"] == "CREATED"


def test_create_version_with_config(firebase_hosting_controller):
    """Test creating a version with custom config."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "projects/test-project/sites/my-site/versions/version123",
        "status": "CREATED",
        "config": {
            "redirects": [{"source": "/old", "destination": "/new", "type": 301}]
        },
    }
    mock_response.content = b'{"name": "..."}'

    mock_client.request.return_value = mock_response

    config = {"redirects": [{"source": "/old", "destination": "/new", "type": 301}]}

    version = controller.create_version("my-site", config=config)

    assert version["config"]["redirects"][0]["source"] == "/old"


def test_get_version_success(firebase_hosting_controller):
    """Test getting a version successfully."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "projects/test-project/sites/my-site/versions/version123",
        "status": "FINALIZED",
        "config": {},
    }
    mock_response.content = b'{"name": "..."}'

    mock_client.request.return_value = mock_response

    version_name = "projects/test-project/sites/my-site/versions/version123"
    version = controller.get_version(version_name)

    assert version["status"] == "FINALIZED"


def test_create_release_success(firebase_hosting_controller):
    """Test creating a release successfully."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "projects/test-project/sites/my-site/releases/release123",
        "version": {"name": "projects/test-project/sites/my-site/versions/version123"},
        "type": "DEPLOY",
        "releaseTime": "2025-01-01T00:00:00Z",
    }
    mock_response.content = b'{"name": "..."}'

    mock_client.request.return_value = mock_response

    version_name = "projects/test-project/sites/my-site/versions/version123"
    release = controller.create_release("my-site", version_name, message="Deploy v1.0")

    assert "release123" in release["name"]
    assert release["type"] == "DEPLOY"


def test_list_releases_success(firebase_hosting_controller):
    """Test listing releases successfully."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "releases": [
            {
                "name": "projects/test-project/sites/my-site/releases/release1",
                "type": "DEPLOY",
                "releaseTime": "2025-01-01T00:00:00Z",
            },
            {
                "name": "projects/test-project/sites/my-site/releases/release2",
                "type": "DEPLOY",
                "releaseTime": "2025-01-02T00:00:00Z",
            },
        ]
    }
    mock_response.content = b'{"releases": [...]}'

    mock_client.request.return_value = mock_response

    releases = controller.list_releases("my-site", page_size=10)

    assert len(releases) == 2
    assert "release1" in releases[0]["name"]


def test_finalize_version_success(firebase_hosting_controller):
    """Test finalizing a version successfully."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "projects/test-project/sites/my-site/versions/version123",
        "status": "FINALIZED",
    }
    mock_response.content = b'{"name": "..."}'

    mock_client.request.return_value = mock_response

    version_name = "projects/test-project/sites/my-site/versions/version123"
    version = controller.finalize_version(version_name)

    assert version["status"] == "FINALIZED"


def test_calculate_file_hash(firebase_hosting_controller):
    """Test calculating file hash."""
    controller, mock_client = firebase_hosting_controller

    # Create a temporary file
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("test content")
        temp_path = Path(f.name)

    try:
        file_hash = controller._calculate_file_hash(temp_path)
        assert len(file_hash) == 64  # SHA256 hash length
    finally:
        temp_path.unlink()


def test_http_error_handling(firebase_hosting_controller):
    """Test handling of HTTP errors."""
    controller, mock_client = firebase_hosting_controller

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Server Error", request=Mock(), response=mock_response
    )

    mock_client.request.return_value = mock_response

    with pytest.raises(FirebaseHostingError) as exc_info:
        controller.get_site("my-site")

    assert "500" in str(exc_info.value.message)


def test_populate_files_validation_error(firebase_hosting_controller):
    """Test populate_files with empty files dict."""
    controller, mock_client = firebase_hosting_controller

    version_name = "projects/test-project/sites/my-site/versions/version123"

    with pytest.raises(ValidationError) as exc_info:
        controller.populate_files(version_name, {})

    assert "cannot be empty" in str(exc_info.value.message).lower()


def test_populate_files_success(firebase_hosting_controller):
    """Test populating files successfully."""
    controller, mock_client = firebase_hosting_controller

    # Create temporary files
    import tempfile

    temp_dir = Path(tempfile.mkdtemp())

    try:
        index_file = temp_dir / "index.html"
        index_file.write_text("<html>Test</html>")

        css_file = temp_dir / "style.css"
        css_file.write_text("body { margin: 0; }")

        files = {"/index.html": str(index_file), "/style.css": str(css_file)}

        # Mock the populate response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "uploadRequiredHashes": [],
            "uploadUrl": "https://upload.example.com",
        }
        mock_response.content = b'{"uploadRequiredHashes": []}'

        mock_client.request.return_value = mock_response

        version_name = "projects/test-project/sites/my-site/versions/version123"
        result = controller.populate_files(version_name, files)

        assert "uploadRequiredHashes" in result

    finally:
        # Cleanup
        import shutil

        shutil.rmtree(temp_dir)
