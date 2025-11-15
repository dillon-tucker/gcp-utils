"""
Artifact Registry controller.

This module provides a high-level interface for Google Cloud Artifact Registry
operations including repository management, image operations, and Docker integration.
"""

from typing import Any, Optional
import subprocess
import json

from google.cloud import artifactregistry_v1
from google.api_core import exceptions as google_exceptions
from google.auth.credentials import Credentials

from ..config import GCPSettings, get_settings
from ..exceptions import (
    ArtifactRegistryError,
    ResourceNotFoundError,
    ValidationError,
)


class ArtifactRegistryController:
    """
    Controller for Artifact Registry operations.

    This controller provides methods for managing repositories, listing images,
    and integrating with Docker for image storage.

    Example:
        >>> from gcp_utils.controllers import ArtifactRegistryController
        >>>
        >>> # Automatically loads from .env file
        >>> registry = ArtifactRegistryController()
        >>>
        >>> # Create a Docker repository
        >>> repo = registry.create_repository(
        ...     repository_id="my-app",
        ...     location="us-central1",
        ...     format="DOCKER"
        ... )
    """

    def __init__(
        self,
        settings: Optional[GCPSettings] = None,
        credentials: Optional[Credentials] = None,
    ) -> None:
        """
        Initialize the Artifact Registry controller.

        Args:
            settings: GCP configuration settings. If not provided, loads from environment/.env file.
            credentials: Optional custom credentials object

        Raises:
            ArtifactRegistryError: If initialization fails
        """
        self._settings = settings or get_settings()
        self._credentials = credentials
        self._client: Optional[artifactregistry_v1.ArtifactRegistryClient] = None

    def _get_client(self) -> artifactregistry_v1.ArtifactRegistryClient:
        """
        Get or create Artifact Registry client.

        Returns:
            ArtifactRegistryClient instance

        Raises:
            ArtifactRegistryError: If client creation fails
        """
        if self._client is None:
            try:
                self._client = artifactregistry_v1.ArtifactRegistryClient(
                    credentials=self._credentials
                )
            except Exception as e:
                raise ArtifactRegistryError(
                    f"Failed to create Artifact Registry client: {e}",
                    details={"error": str(e)},
                ) from e

        return self._client

    def create_repository(
        self,
        repository_id: str,
        location: str,
        format: str = "DOCKER",
        description: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """
        Create an Artifact Registry repository.

        Args:
            repository_id: Repository ID (e.g., "my-app-images")
            location: GCP location (e.g., "us-central1")
            format: Repository format (DOCKER, MAVEN, NPM, PYTHON, APT, YUM, etc.)
            description: Optional repository description
            labels: Optional labels for the repository

        Returns:
            Dictionary containing repository information

        Raises:
            ArtifactRegistryError: If repository creation fails
            ValidationError: If inputs are invalid

        Example:
            >>> repo = registry.create_repository(
            ...     repository_id="my-docker-repo",
            ...     location="us-central1",
            ...     format="DOCKER",
            ...     description="Docker images for my application"
            ... )
        """
        if not repository_id or not repository_id.strip():
            raise ValidationError(
                "Repository ID cannot be empty",
                details={"repository_id": repository_id},
            )

        try:
            client = self._get_client()

            parent = f"projects/{self._settings.project_id}/locations/{location}"

            repository = artifactregistry_v1.Repository(
                format_=getattr(artifactregistry_v1.Repository.Format, format),
                description=description or "",
                labels=labels or {},
            )

            request = artifactregistry_v1.CreateRepositoryRequest(
                parent=parent,
                repository_id=repository_id,
                repository=repository,
            )

            operation = client.create_repository(request=request)
            result = operation.result()

            return {
                "name": result.name,
                "format": result.format_.name,
                "description": result.description,
                "create_time": result.create_time,
                "update_time": result.update_time,
                "labels": dict(result.labels),
            }

        except google_exceptions.AlreadyExists:
            raise ArtifactRegistryError(
                f"Repository '{repository_id}' already exists in {location}",
                details={"repository_id": repository_id, "location": location},
            )
        except Exception as e:
            if isinstance(e, (ArtifactRegistryError, ValidationError)):
                raise
            raise ArtifactRegistryError(
                f"Failed to create repository: {str(e)}",
                details={
                    "repository_id": repository_id,
                    "location": location,
                    "error": str(e),
                },
            ) from e

    def get_repository(
        self,
        repository_id: str,
        location: str,
    ) -> dict[str, Any]:
        """
        Get repository information.

        Args:
            repository_id: Repository ID
            location: GCP location

        Returns:
            Dictionary containing repository information

        Raises:
            ArtifactRegistryError: If request fails
            ResourceNotFoundError: If repository not found

        Example:
            >>> repo = registry.get_repository("my-docker-repo", "us-central1")
        """
        try:
            client = self._get_client()

            name = (
                f"projects/{self._settings.project_id}/locations/{location}/"
                f"repositories/{repository_id}"
            )

            request = artifactregistry_v1.GetRepositoryRequest(name=name)
            result = client.get_repository(request=request)

            return {
                "name": result.name,
                "format": result.format_.name,
                "description": result.description,
                "create_time": result.create_time,
                "update_time": result.update_time,
                "labels": dict(result.labels),
            }

        except google_exceptions.NotFound:
            raise ResourceNotFoundError(
                f"Repository '{repository_id}' not found in {location}",
                details={"repository_id": repository_id, "location": location},
            )
        except Exception as e:
            if isinstance(e, (ArtifactRegistryError, ResourceNotFoundError)):
                raise
            raise ArtifactRegistryError(
                f"Failed to get repository: {str(e)}",
                details={"repository_id": repository_id, "error": str(e)},
            ) from e

    def list_repositories(
        self,
        location: str,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List all repositories in a location.

        Args:
            location: GCP location
            page_size: Maximum number of repositories per page

        Returns:
            List of repository dictionaries

        Raises:
            ArtifactRegistryError: If request fails

        Example:
            >>> repos = registry.list_repositories("us-central1")
            >>> for repo in repos:
            ...     print(repo["name"])
        """
        try:
            client = self._get_client()

            parent = f"projects/{self._settings.project_id}/locations/{location}"

            request = artifactregistry_v1.ListRepositoriesRequest(
                parent=parent,
                page_size=page_size,
            )

            all_repos: list[dict[str, Any]] = []

            for repository in client.list_repositories(request=request):
                all_repos.append({
                    "name": repository.name,
                    "format": repository.format_.name,
                    "description": repository.description,
                    "create_time": repository.create_time,
                    "update_time": repository.update_time,
                    "labels": dict(repository.labels),
                })

            return all_repos

        except Exception as e:
            if isinstance(e, ArtifactRegistryError):
                raise
            raise ArtifactRegistryError(
                f"Failed to list repositories: {str(e)}",
                details={"location": location, "error": str(e)},
            ) from e

    def delete_repository(
        self,
        repository_id: str,
        location: str,
    ) -> None:
        """
        Delete a repository.

        Args:
            repository_id: Repository ID
            location: GCP location

        Raises:
            ArtifactRegistryError: If deletion fails
            ResourceNotFoundError: If repository not found

        Example:
            >>> registry.delete_repository("old-repo", "us-central1")
        """
        try:
            client = self._get_client()

            name = (
                f"projects/{self._settings.project_id}/locations/{location}/"
                f"repositories/{repository_id}"
            )

            request = artifactregistry_v1.DeleteRepositoryRequest(name=name)
            operation = client.delete_repository(request=request)
            operation.result()

        except google_exceptions.NotFound:
            raise ResourceNotFoundError(
                f"Repository '{repository_id}' not found in {location}",
                details={"repository_id": repository_id, "location": location},
            )
        except Exception as e:
            if isinstance(e, (ArtifactRegistryError, ResourceNotFoundError)):
                raise
            raise ArtifactRegistryError(
                f"Failed to delete repository: {str(e)}",
                details={"repository_id": repository_id, "error": str(e)},
            ) from e

    def get_docker_image_url(
        self,
        repository_id: str,
        location: str,
        image_name: str,
        tag: str = "latest",
    ) -> str:
        """
        Get the full Docker image URL for Artifact Registry.

        Args:
            repository_id: Repository ID
            location: GCP location
            image_name: Image name
            tag: Image tag (default: "latest")

        Returns:
            Full Docker image URL

        Example:
            >>> url = registry.get_docker_image_url(
            ...     "my-repo", "us-central1", "my-app", "v1.0.0"
            ... )
            >>> print(url)
            us-central1-docker.pkg.dev/my-project/my-repo/my-app:v1.0.0
        """
        return (
            f"{location}-docker.pkg.dev/"
            f"{self._settings.project_id}/"
            f"{repository_id}/"
            f"{image_name}:{tag}"
        )

    def configure_docker_auth(self, location: str) -> None:
        """
        Configure Docker to authenticate with Artifact Registry.

        This runs `gcloud auth configure-docker` for the specified location.

        Args:
            location: GCP location (e.g., "us-central1")

        Raises:
            ArtifactRegistryError: If authentication configuration fails

        Example:
            >>> registry.configure_docker_auth("us-central1")
        """
        try:
            registry_host = f"{location}-docker.pkg.dev"

            result = subprocess.run(
                ["gcloud", "auth", "configure-docker", registry_host, "--quiet"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise ArtifactRegistryError(
                    f"Failed to configure Docker auth: {result.stderr}",
                    details={"stderr": result.stderr, "stdout": result.stdout},
                )

        except subprocess.TimeoutExpired:
            raise ArtifactRegistryError(
                "Docker auth configuration timed out",
                details={"location": location},
            )
        except FileNotFoundError:
            raise ArtifactRegistryError(
                "gcloud CLI not found. Please install Google Cloud SDK.",
                details={"location": location},
            )
        except Exception as e:
            if isinstance(e, ArtifactRegistryError):
                raise
            raise ArtifactRegistryError(
                f"Failed to configure Docker auth: {str(e)}",
                details={"location": location, "error": str(e)},
            ) from e

    def list_docker_images(
        self,
        repository_id: str,
        location: str,
    ) -> list[dict[str, Any]]:
        """
        List Docker images in a repository using gcloud.

        Args:
            repository_id: Repository ID
            location: GCP location

        Returns:
            List of image dictionaries with tags and metadata

        Raises:
            ArtifactRegistryError: If listing fails

        Example:
            >>> images = registry.list_docker_images("my-repo", "us-central1")
            >>> for image in images:
            ...     print(f"{image['image']}:{image['tag']}")
        """
        try:
            repo_path = (
                f"{location}-docker.pkg.dev/"
                f"{self._settings.project_id}/"
                f"{repository_id}"
            )

            result = subprocess.run(
                [
                    "gcloud",
                    "artifacts",
                    "docker",
                    "images",
                    "list",
                    repo_path,
                    "--format=json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise ArtifactRegistryError(
                    f"Failed to list images: {result.stderr}",
                    details={"stderr": result.stderr},
                )

            images = json.loads(result.stdout) if result.stdout else []
            return images

        except json.JSONDecodeError as e:
            raise ArtifactRegistryError(
                f"Failed to parse gcloud output: {e}",
                details={"error": str(e)},
            ) from e
        except Exception as e:
            if isinstance(e, ArtifactRegistryError):
                raise
            raise ArtifactRegistryError(
                f"Failed to list Docker images: {str(e)}",
                details={"repository_id": repository_id, "error": str(e)},
            ) from e
