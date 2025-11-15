"""
Firebase Hosting controller.

This module provides a high-level interface for Firebase Hosting operations
including site management, deployments, and custom domain configuration.
"""

from typing import Any, Optional
import json
import time
import hashlib
from pathlib import Path

import firebase_admin
from firebase_admin import credentials
from google.auth.credentials import Credentials
from google.auth import default
import httpx

from ..config import GCPSettings, get_settings
from ..exceptions import (
    FirebaseHostingError,
    ResourceNotFoundError,
    ValidationError,
    OperationTimeoutError,
)


class FirebaseHostingController:
    """
    Controller for Firebase Hosting operations.

    This controller provides methods for managing Firebase Hosting sites,
    deploying websites, and configuring custom domains.

    Example:
        >>> from gcp_utils.controllers import FirebaseHostingController
        >>>
        >>> # Automatically loads from .env file
        >>> hosting = FirebaseHostingController()
        >>>
        >>> # Create a site
        >>> site = hosting.create_site(site_id="my-site")
        >>>
        >>> # Add custom domain
        >>> domain = hosting.add_custom_domain(
        ...     site_id="my-site",
        ...     domain_name="example.com"
        ... )
    """

    def __init__(
        self,
        settings: Optional[GCPSettings] = None,
        credentials_obj: Optional[Credentials] = None,
    ) -> None:
        """
        Initialize the Firebase Hosting controller.

        Args:
            settings: GCP configuration settings. If not provided, loads from environment/.env file.
            credentials_obj: Optional custom credentials object.
                If not provided, uses settings.credentials_path or default credentials.

        Raises:
            FirebaseHostingError: If Firebase initialization fails
        """
        self._settings = settings or get_settings()
        self._credentials = credentials_obj
        self._api_base_url = "https://firebasehosting.googleapis.com/v1beta1"
        self._client: Optional[httpx.Client] = None

        try:
            # Check if Firebase is already initialized
            try:
                firebase_admin.get_app()
            except ValueError:
                # Firebase not initialized yet
                cred_path = (
                    str(self._settings.credentials_path) if self._settings.credentials_path else None
                )

                if cred_path:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(
                        cred,
                        {"projectId": self._settings.project_id},
                    )
                else:
                    # Use application default credentials
                    firebase_admin.initialize_app(
                        options={"projectId": self._settings.project_id}
                    )

        except Exception as e:
            raise FirebaseHostingError(
                f"Failed to initialize Firebase: {e}",
                details={"error": str(e)},
            ) from e

    def _get_client(self) -> httpx.Client:
        """
        Get or create HTTP client with authentication.

        Returns:
            Authenticated httpx.Client instance

        Raises:
            FirebaseHostingError: If client creation fails
        """
        if self._client is None:
            try:
                if self._credentials:
                    creds = self._credentials
                else:
                    creds, _ = default()

                # Refresh credentials if needed
                if not creds.valid:
                    from google.auth.transport.requests import Request
                    creds.refresh(Request())

                self._client = httpx.Client(
                    headers={
                        "Authorization": f"Bearer {creds.token}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
            except Exception as e:
                raise FirebaseHostingError(
                    f"Failed to create HTTP client: {e}",
                    details={"error": str(e)},
                ) from e

        return self._client

    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """
        Make an authenticated request to Firebase Hosting API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint path
            json_data: Optional JSON payload
            params: Optional query parameters

        Returns:
            Response data as dictionary

        Raises:
            FirebaseHostingError: If request fails
            ResourceNotFoundError: If resource not found (404)
        """
        try:
            client = self._get_client()
            url = f"{self._api_base_url}/{endpoint}"

            response = client.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
            )

            if response.status_code == 404:
                raise ResourceNotFoundError(
                    f"Resource not found: {endpoint}",
                    details={"endpoint": endpoint, "status": 404},
                )

            response.raise_for_status()

            if response.content:
                return response.json()
            return {}

        except httpx.HTTPStatusError as e:
            raise FirebaseHostingError(
                f"HTTP error: {e.response.status_code} - {e.response.text}",
                details={
                    "status_code": e.response.status_code,
                    "response": e.response.text,
                },
            ) from e
        except Exception as e:
            if isinstance(e, (FirebaseHostingError, ResourceNotFoundError)):
                raise
            raise FirebaseHostingError(
                f"Request failed: {str(e)}",
                details={"error": str(e)},
            ) from e

    def create_site(
        self,
        site_id: str,
        app_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a new Firebase Hosting site.

        Args:
            site_id: Unique identifier for the site
            app_id: Optional Firebase app ID to associate with the site

        Returns:
            Dictionary containing site information

        Raises:
            FirebaseHostingError: If site creation fails
            ValidationError: If site_id is invalid

        Example:
            >>> site = hosting.create_site(site_id="my-awesome-site")
            >>> print(site["name"])
        """
        if not site_id or not site_id.strip():
            raise ValidationError(
                "Site ID cannot be empty",
                details={"site_id": site_id},
            )

        try:
            endpoint = f"projects/{self._settings.project_id}/sites"
            payload: dict[str, Any] = {"siteId": site_id}

            if app_id:
                payload["appId"] = app_id

            result = self._make_request("POST", endpoint, json_data=payload)
            return result

        except Exception as e:
            if isinstance(e, (FirebaseHostingError, ValidationError)):
                raise
            raise FirebaseHostingError(
                f"Failed to create site: {str(e)}",
                details={"site_id": site_id, "error": str(e)},
            ) from e

    def get_site(self, site_id: str) -> dict[str, Any]:
        """
        Get information about a Firebase Hosting site.

        Args:
            site_id: The site identifier

        Returns:
            Dictionary containing site information

        Raises:
            FirebaseHostingError: If request fails
            ResourceNotFoundError: If site not found

        Example:
            >>> site = hosting.get_site("my-site")
            >>> print(site["defaultUrl"])
        """
        try:
            endpoint = f"projects/{self._settings.project_id}/sites/{site_id}"
            return self._make_request("GET", endpoint)

        except Exception as e:
            if isinstance(e, (FirebaseHostingError, ResourceNotFoundError)):
                raise
            raise FirebaseHostingError(
                f"Failed to get site: {str(e)}",
                details={"site_id": site_id, "error": str(e)},
            ) from e

    def list_sites(self, page_size: int = 100) -> list[dict[str, Any]]:
        """
        List all Firebase Hosting sites in the project.

        Args:
            page_size: Maximum number of sites to return per page

        Returns:
            List of site dictionaries

        Raises:
            FirebaseHostingError: If request fails

        Example:
            >>> sites = hosting.list_sites()
            >>> for site in sites:
            ...     print(site["name"])
        """
        try:
            endpoint = f"projects/{self._settings.project_id}/sites"
            params = {"pageSize": str(page_size)}

            all_sites: list[dict[str, Any]] = []
            next_page_token: Optional[str] = None

            while True:
                if next_page_token:
                    params["pageToken"] = next_page_token

                response = self._make_request("GET", endpoint, params=params)

                sites = response.get("sites", [])
                all_sites.extend(sites)

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

            return all_sites

        except Exception as e:
            if isinstance(e, FirebaseHostingError):
                raise
            raise FirebaseHostingError(
                f"Failed to list sites: {str(e)}",
                details={"error": str(e)},
            ) from e

    def delete_site(self, site_id: str) -> None:
        """
        Delete a Firebase Hosting site.

        Args:
            site_id: The site identifier

        Raises:
            FirebaseHostingError: If deletion fails
            ResourceNotFoundError: If site not found

        Example:
            >>> hosting.delete_site("my-old-site")
        """
        try:
            endpoint = f"projects/{self._settings.project_id}/sites/{site_id}"
            self._make_request("DELETE", endpoint)

        except Exception as e:
            if isinstance(e, (FirebaseHostingError, ResourceNotFoundError)):
                raise
            raise FirebaseHostingError(
                f"Failed to delete site: {str(e)}",
                details={"site_id": site_id, "error": str(e)},
            ) from e

    def add_custom_domain(
        self,
        site_id: str,
        domain_name: str,
    ) -> dict[str, Any]:
        """
        Add a custom domain to a Firebase Hosting site.

        Args:
            site_id: The site identifier
            domain_name: The custom domain name (e.g., "example.com")

        Returns:
            Dictionary containing domain information

        Raises:
            FirebaseHostingError: If adding domain fails
            ValidationError: If domain_name is invalid

        Example:
            >>> domain = hosting.add_custom_domain(
            ...     site_id="my-site",
            ...     domain_name="example.com"
            ... )
            >>> print(domain["domainName"])
        """
        if not domain_name or not domain_name.strip():
            raise ValidationError(
                "Domain name cannot be empty",
                details={"domain_name": domain_name},
            )

        try:
            endpoint = f"projects/{self._settings.project_id}/sites/{site_id}/domains"
            payload = {"domainName": domain_name}

            result = self._make_request("POST", endpoint, json_data=payload)
            return result

        except Exception as e:
            if isinstance(e, (FirebaseHostingError, ValidationError)):
                raise
            raise FirebaseHostingError(
                f"Failed to add custom domain: {str(e)}",
                details={
                    "site_id": site_id,
                    "domain_name": domain_name,
                    "error": str(e),
                },
            ) from e

    def get_domain(self, site_id: str, domain_name: str) -> dict[str, Any]:
        """
        Get information about a custom domain.

        Args:
            site_id: The site identifier
            domain_name: The domain name

        Returns:
            Dictionary containing domain information including status and DNS records

        Raises:
            FirebaseHostingError: If request fails
            ResourceNotFoundError: If domain not found

        Example:
            >>> domain = hosting.get_domain("my-site", "example.com")
            >>> print(domain["status"])
        """
        try:
            endpoint = (
                f"projects/{self._settings.project_id}/sites/{site_id}/"
                f"domains/{domain_name}"
            )
            return self._make_request("GET", endpoint)

        except Exception as e:
            if isinstance(e, (FirebaseHostingError, ResourceNotFoundError)):
                raise
            raise FirebaseHostingError(
                f"Failed to get domain: {str(e)}",
                details={
                    "site_id": site_id,
                    "domain_name": domain_name,
                    "error": str(e),
                },
            ) from e

    def list_domains(self, site_id: str) -> list[dict[str, Any]]:
        """
        List all custom domains for a site.

        Args:
            site_id: The site identifier

        Returns:
            List of domain dictionaries

        Raises:
            FirebaseHostingError: If request fails

        Example:
            >>> domains = hosting.list_domains("my-site")
            >>> for domain in domains:
            ...     print(f"{domain['domainName']}: {domain['status']}")
        """
        try:
            endpoint = f"projects/{self._settings.project_id}/sites/{site_id}/domains"

            all_domains: list[dict[str, Any]] = []
            next_page_token: Optional[str] = None
            params: dict[str, str] = {}

            while True:
                if next_page_token:
                    params["pageToken"] = next_page_token

                response = self._make_request("GET", endpoint, params=params)

                domains = response.get("domains", [])
                all_domains.extend(domains)

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

            return all_domains

        except Exception as e:
            if isinstance(e, FirebaseHostingError):
                raise
            raise FirebaseHostingError(
                f"Failed to list domains: {str(e)}",
                details={"site_id": site_id, "error": str(e)},
            ) from e

    def delete_domain(self, site_id: str, domain_name: str) -> None:
        """
        Delete a custom domain from a site.

        Args:
            site_id: The site identifier
            domain_name: The domain name to delete

        Raises:
            FirebaseHostingError: If deletion fails
            ResourceNotFoundError: If domain not found

        Example:
            >>> hosting.delete_domain("my-site", "old-domain.com")
        """
        try:
            endpoint = (
                f"projects/{self._settings.project_id}/sites/{site_id}/"
                f"domains/{domain_name}"
            )
            self._make_request("DELETE", endpoint)

        except Exception as e:
            if isinstance(e, (FirebaseHostingError, ResourceNotFoundError)):
                raise
            raise FirebaseHostingError(
                f"Failed to delete domain: {str(e)}",
                details={
                    "site_id": site_id,
                    "domain_name": domain_name,
                    "error": str(e),
                },
            ) from e

    def create_version(
        self,
        site_id: str,
        config: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create a new version for deployment.

        Args:
            site_id: The site identifier
            config: Optional version configuration (redirects, headers, rewrites, etc.)

        Returns:
            Dictionary containing version information

        Raises:
            FirebaseHostingError: If version creation fails

        Example:
            >>> config = {
            ...     "redirects": [{
            ...         "source": "/old-page",
            ...         "destination": "/new-page",
            ...         "type": 301
            ...     }]
            ... }
            >>> version = hosting.create_version("my-site", config=config)
        """
        try:
            endpoint = f"projects/{self._settings.project_id}/sites/{site_id}/versions"
            payload = {"config": config} if config else {}

            result = self._make_request("POST", endpoint, json_data=payload)
            return result

        except Exception as e:
            if isinstance(e, FirebaseHostingError):
                raise
            raise FirebaseHostingError(
                f"Failed to create version: {str(e)}",
                details={"site_id": site_id, "error": str(e)},
            ) from e

    def get_version(self, version_name: str) -> dict[str, Any]:
        """
        Get information about a specific version.

        Args:
            version_name: Full version name (e.g., "projects/PROJECT/sites/SITE/versions/VERSION")

        Returns:
            Dictionary containing version information

        Raises:
            FirebaseHostingError: If request fails
            ResourceNotFoundError: If version not found

        Example:
            >>> version = hosting.get_version(
            ...     "projects/my-project/sites/my-site/versions/abc123"
            ... )
        """
        try:
            # Remove the base URL part if present
            if version_name.startswith("projects/"):
                endpoint = version_name
            else:
                endpoint = f"projects/{self._settings.project_id}/{version_name}"

            return self._make_request("GET", endpoint)

        except Exception as e:
            if isinstance(e, (FirebaseHostingError, ResourceNotFoundError)):
                raise
            raise FirebaseHostingError(
                f"Failed to get version: {str(e)}",
                details={"version_name": version_name, "error": str(e)},
            ) from e

    def create_release(
        self,
        site_id: str,
        version_name: str,
        message: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a release to deploy a version to the live site.

        Args:
            site_id: The site identifier
            version_name: The version to release
            message: Optional release message

        Returns:
            Dictionary containing release information

        Raises:
            FirebaseHostingError: If release creation fails

        Example:
            >>> release = hosting.create_release(
            ...     site_id="my-site",
            ...     version_name="projects/my-project/sites/my-site/versions/abc123",
            ...     message="Production deployment"
            ... )
        """
        try:
            endpoint = f"projects/{self._settings.project_id}/sites/{site_id}/releases"
            params = {"versionName": version_name}

            payload: dict[str, Any] = {}
            if message:
                payload["message"] = message

            result = self._make_request("POST", endpoint, json_data=payload, params=params)
            return result

        except Exception as e:
            if isinstance(e, FirebaseHostingError):
                raise
            raise FirebaseHostingError(
                f"Failed to create release: {str(e)}",
                details={
                    "site_id": site_id,
                    "version_name": version_name,
                    "error": str(e),
                },
            ) from e

    def list_releases(
        self,
        site_id: str,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List releases for a site.

        Args:
            site_id: The site identifier
            page_size: Maximum number of releases to return per page

        Returns:
            List of release dictionaries

        Raises:
            FirebaseHostingError: If request fails

        Example:
            >>> releases = hosting.list_releases("my-site")
            >>> for release in releases[:5]:  # Show last 5 releases
            ...     print(f"{release['name']}: {release.get('message', 'No message')}")
        """
        try:
            endpoint = f"projects/{self._settings.project_id}/sites/{site_id}/releases"
            params = {"pageSize": str(page_size)}

            all_releases: list[dict[str, Any]] = []
            next_page_token: Optional[str] = None

            while True:
                if next_page_token:
                    params["pageToken"] = next_page_token

                response = self._make_request("GET", endpoint, params=params)

                releases = response.get("releases", [])
                all_releases.extend(releases)

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

            return all_releases

        except Exception as e:
            if isinstance(e, FirebaseHostingError):
                raise
            raise FirebaseHostingError(
                f"Failed to list releases: {str(e)}",
                details={"site_id": site_id, "error": str(e)},
            ) from e

    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            Hex string of SHA256 hash

        Raises:
            FirebaseHostingError: If file cannot be read
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            raise FirebaseHostingError(
                f"Failed to hash file: {str(e)}",
                details={"file_path": str(file_path), "error": str(e)},
            ) from e

    def populate_files(
        self,
        version_name: str,
        files: dict[str, str],
    ) -> dict[str, Any]:
        """
        Upload files to a version.

        This method implements the Firebase Hosting file upload workflow:
        1. Hash all files
        2. Send hashes to API to check which files are needed
        3. Upload only the missing files
        4. Finalize the file population

        Args:
            version_name: Full version name (e.g., "projects/PROJECT/sites/SITE/versions/VERSION")
            files: Dictionary mapping destination paths to local file paths
                   Example: {"/index.html": "/path/to/index.html", "/app.js": "/path/to/app.js"}

        Returns:
            Dictionary containing upload results

        Raises:
            FirebaseHostingError: If file upload fails
            ValidationError: If files dictionary is invalid

        Example:
            >>> files = {
            ...     "/index.html": "./public/index.html",
            ...     "/css/style.css": "./public/css/style.css",
            ...     "/js/app.js": "./public/js/app.js"
            ... }
            >>> result = hosting.populate_files(version_name, files)
            >>> print(f"Uploaded {result.get('uploadedFileCount', 0)} files")
        """
        if not files:
            raise ValidationError(
                "Files dictionary cannot be empty",
                details={"files": files},
            )

        try:
            # Step 1: Hash all files and prepare file manifest
            file_hashes: dict[str, str] = {}
            hash_to_path: dict[str, str] = {}

            for dest_path, source_path in files.items():
                source = Path(source_path)
                if not source.exists():
                    raise ValidationError(
                        f"Source file does not exist: {source_path}",
                        details={"source_path": source_path},
                    )
                if not source.is_file():
                    raise ValidationError(
                        f"Source path is not a file: {source_path}",
                        details={"source_path": source_path},
                    )

                file_hash = self._calculate_file_hash(source)
                file_hashes[dest_path] = file_hash
                hash_to_path[file_hash] = source_path

            # Step 2: Populate files endpoint - tell API about all files
            endpoint = f"{version_name}:populateFiles"
            payload = {
                "files": {
                    path: hash_val for path, hash_val in file_hashes.items()
                }
            }

            response = self._make_request("POST", endpoint, json_data=payload)

            # Step 3: Upload files that the API doesn't have
            upload_required_hashes = response.get("uploadRequiredHashes", [])

            if upload_required_hashes:
                # Get upload URL
                upload_url = response.get("uploadUrl")
                if not upload_url:
                    raise FirebaseHostingError(
                        "API did not provide upload URL",
                        details={"response": response},
                    )

                # Upload each required file
                for hash_val in upload_required_hashes:
                    if hash_val not in hash_to_path:
                        continue

                    source_path = hash_to_path[hash_val]
                    file_upload_url = f"{upload_url}/{hash_val}"

                    with open(source_path, "rb") as f:
                        file_content = f.read()

                    # Upload file using PUT request
                    client = self._get_client()
                    upload_response = client.put(
                        file_upload_url,
                        content=file_content,
                        headers={
                            "Content-Type": "application/octet-stream",
                        },
                    )
                    upload_response.raise_for_status()

            return {
                "totalFileCount": len(files),
                "uploadedFileCount": len(upload_required_hashes),
                "cachedFileCount": len(files) - len(upload_required_hashes),
                "uploadUrl": response.get("uploadUrl"),
            }

        except Exception as e:
            if isinstance(e, (FirebaseHostingError, ValidationError)):
                raise
            raise FirebaseHostingError(
                f"Failed to populate files: {str(e)}",
                details={"version_name": version_name, "error": str(e)},
            ) from e

    def finalize_version(
        self,
        version_name: str,
    ) -> dict[str, Any]:
        """
        Finalize a version to make it ready for release.

        A version must be finalized before it can be released. Finalization
        processes the uploaded files and makes the version immutable.

        Args:
            version_name: Full version name (e.g., "projects/PROJECT/sites/SITE/versions/VERSION")

        Returns:
            Dictionary containing finalized version information

        Raises:
            FirebaseHostingError: If finalization fails

        Example:
            >>> version = hosting.finalize_version(
            ...     "projects/my-project/sites/my-site/versions/abc123"
            ... )
            >>> print(f"Status: {version['status']}")
        """
        try:
            endpoint = f"{version_name}?updateMask=status"
            payload = {"status": "FINALIZED"}

            result = self._make_request("PATCH", endpoint, json_data=payload)
            return result

        except Exception as e:
            if isinstance(e, FirebaseHostingError):
                raise
            raise FirebaseHostingError(
                f"Failed to finalize version: {str(e)}",
                details={"version_name": version_name, "error": str(e)},
            ) from e

    def deploy_site(
        self,
        site_id: str,
        files: dict[str, str],
        config: Optional[dict[str, Any]] = None,
        message: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Complete deployment workflow: create version, upload files, and release.

        This is a convenience method that performs the entire deployment process:
        1. Create a new version with optional configuration
        2. Upload all files to the version
        3. Finalize the version
        4. Create a release to deploy the version

        Args:
            site_id: The site identifier
            files: Dictionary mapping destination paths to local file paths
                   Example: {"/index.html": "./public/index.html"}
            config: Optional hosting configuration (redirects, headers, rewrites)
            message: Optional release message

        Returns:
            Dictionary containing deployment information including:
            - version: The created version
            - upload_result: File upload results
            - release: The created release

        Raises:
            FirebaseHostingError: If any step of deployment fails
            ValidationError: If inputs are invalid

        Example:
            >>> # Deploy a simple site
            >>> result = hosting.deploy_site(
            ...     site_id="my-site",
            ...     files={
            ...         "/index.html": "./public/index.html",
            ...         "/style.css": "./public/style.css",
            ...         "/app.js": "./public/app.js"
            ...     },
            ...     config={
            ...         "redirects": [{
            ...             "source": "/old",
            ...             "destination": "/new",
            ...             "type": 301
            ...         }]
            ...     },
            ...     message="Production v1.0.0"
            ... )
            >>> print(f"Deployed {result['upload_result']['totalFileCount']} files")
            >>> print(f"Release: {result['release']['name']}")
        """
        try:
            # Step 1: Create version
            print(f"Creating version for site '{site_id}'...")
            version = self.create_version(site_id, config=config)
            version_name = version["name"]
            print(f"✓ Created version: {version_name}")

            # Step 2: Upload files
            print(f"Uploading {len(files)} file(s)...")
            upload_result = self.populate_files(version_name, files)
            print(
                f"✓ Uploaded {upload_result['uploadedFileCount']} new file(s), "
                f"{upload_result['cachedFileCount']} cached"
            )

            # Step 3: Finalize version
            print("Finalizing version...")
            finalized_version = self.finalize_version(version_name)
            print(f"✓ Version finalized: {finalized_version.get('status', 'FINALIZED')}")

            # Step 4: Create release
            print("Creating release...")
            release = self.create_release(
                site_id=site_id,
                version_name=version_name,
                message=message,
            )
            print(f"✓ Release created: {release['name']}")

            # Get site info for URL
            site = self.get_site(site_id)
            default_url = site.get("defaultUrl", "")

            return {
                "version": finalized_version,
                "upload_result": upload_result,
                "release": release,
                "site_url": default_url,
                "success": True,
            }

        except Exception as e:
            if isinstance(e, (FirebaseHostingError, ValidationError)):
                raise
            raise FirebaseHostingError(
                f"Failed to deploy site: {str(e)}",
                details={
                    "site_id": site_id,
                    "file_count": len(files),
                    "error": str(e),
                },
            ) from e

    def __del__(self) -> None:
        """Clean up HTTP client on deletion."""
        if self._client:
            self._client.close()
