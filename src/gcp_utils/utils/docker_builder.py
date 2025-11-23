"""
Docker builder utility.

This module provides utilities for building Docker images and pushing them
to Google Artifact Registry for use with Cloud Run and other services.
"""

import json
import subprocess
from pathlib import Path
from typing import Any

from ..exceptions import ArtifactRegistryError, ValidationError


class DockerBuilder:
    """
    Utility for building and pushing Docker images.

    This class provides methods for building Docker images from Dockerfiles
    and pushing them to Artifact Registry.

    Example:
        >>> from gcp_utils.utils import DockerBuilder
        >>>
        >>> builder = DockerBuilder()
        >>> image_url = builder.build_and_push(
        ...     dockerfile_path="./Dockerfile",
        ...     context_path=".",
        ...     image_url="us-central1-docker.pkg.dev/my-project/my-repo/my-app:v1"
        ... )
    """

    def __init__(self) -> None:
        """Initialize Docker builder."""
        self._check_docker_available()

    def _check_docker_available(self) -> None:
        """
        Check if Docker is available.

        Raises:
            ArtifactRegistryError: If Docker is not available
        """
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise ArtifactRegistryError(
                    "Docker is not available or not working correctly",
                    details={"error": result.stderr},
                )
        except FileNotFoundError:
            raise ArtifactRegistryError(
                "Docker not found. Please install Docker Desktop or Docker Engine.",
                details={},
            )
        except subprocess.TimeoutExpired:
            raise ArtifactRegistryError(
                "Docker command timed out",
                details={},
            )

    def build_image(
        self,
        dockerfile_path: str,
        context_path: str,
        image_url: str,
        build_args: dict[str, str] | None = None,
        no_cache: bool = False,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """
        Build a Docker image.

        Args:
            dockerfile_path: Path to Dockerfile
            context_path: Build context directory path
            image_url: Full image URL (e.g., "us-central1-docker.pkg.dev/project/repo/image:tag")
            build_args: Optional build arguments
            no_cache: If True, build without using cache
            platform: Optional platform specification (e.g., "linux/amd64")

        Returns:
            Dictionary with build information

        Raises:
            ValidationError: If inputs are invalid
            ArtifactRegistryError: If build fails

        Example:
            >>> result = builder.build_image(
            ...     dockerfile_path="./Dockerfile",
            ...     context_path=".",
            ...     image_url="us-central1-docker.pkg.dev/my-project/my-repo/app:v1",
            ...     build_args={"VERSION": "1.0.0"}
            ... )
        """
        # Validate inputs
        dockerfile = Path(dockerfile_path)
        if not dockerfile.exists():
            raise ValidationError(
                f"Dockerfile not found: {dockerfile_path}",
                details={"dockerfile_path": dockerfile_path},
            )

        context = Path(context_path)
        if not context.exists() or not context.is_dir():
            raise ValidationError(
                f"Context path must be a directory: {context_path}",
                details={"context_path": context_path},
            )

        try:
            # Build docker command
            cmd = [
                "docker",
                "build",
                "-f",
                str(dockerfile),
                "-t",
                image_url,
            ]

            # Add build args
            if build_args:
                for key, value in build_args.items():
                    cmd.extend(["--build-arg", f"{key}={value}"])

            # Add options
            if no_cache:
                cmd.append("--no-cache")

            if platform:
                cmd.extend(["--platform", platform])

            # Add context (must be last)
            cmd.append(str(context))

            print(f"Building Docker image: {image_url}")
            print(f"Command: {' '.join(cmd)}")

            # Run build
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            if result.returncode != 0:
                raise ArtifactRegistryError(
                    f"Docker build failed: {result.stderr}",
                    details={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                    },
                )

            print("✓ Docker image built successfully")

            return {
                "image_url": image_url,
                "success": True,
                "stdout": result.stdout,
            }

        except subprocess.TimeoutExpired:
            raise ArtifactRegistryError(
                "Docker build timed out (exceeded 10 minutes)",
                details={"image_url": image_url},
            )
        except Exception as e:
            if isinstance(e, (ArtifactRegistryError, ValidationError)):
                raise
            raise ArtifactRegistryError(
                f"Docker build failed: {str(e)}",
                details={"image_url": image_url, "error": str(e)},
            ) from e

    def push_image(self, image_url: str) -> dict[str, Any]:
        """
        Push a Docker image to Artifact Registry.

        Args:
            image_url: Full image URL

        Returns:
            Dictionary with push information

        Raises:
            ArtifactRegistryError: If push fails

        Example:
            >>> result = builder.push_image(
            ...     "us-central1-docker.pkg.dev/my-project/my-repo/app:v1"
            ... )
        """
        try:
            print(f"Pushing Docker image: {image_url}")

            result = subprocess.run(
                ["docker", "push", image_url],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            if result.returncode != 0:
                raise ArtifactRegistryError(
                    f"Docker push failed: {result.stderr}",
                    details={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode,
                    },
                )

            print("✓ Docker image pushed successfully")

            return {
                "image_url": image_url,
                "success": True,
                "stdout": result.stdout,
            }

        except subprocess.TimeoutExpired:
            raise ArtifactRegistryError(
                "Docker push timed out (exceeded 10 minutes)",
                details={"image_url": image_url},
            )
        except Exception as e:
            if isinstance(e, ArtifactRegistryError):
                raise
            raise ArtifactRegistryError(
                f"Docker push failed: {str(e)}",
                details={"image_url": image_url, "error": str(e)},
            ) from e

    def build_and_push(
        self,
        dockerfile_path: str,
        context_path: str,
        image_url: str,
        build_args: dict[str, str] | None = None,
        no_cache: bool = False,
        platform: str | None = None,
    ) -> dict[str, Any]:
        """
        Build and push a Docker image in one step.

        Args:
            dockerfile_path: Path to Dockerfile
            context_path: Build context directory path
            image_url: Full image URL
            build_args: Optional build arguments
            no_cache: If True, build without using cache
            platform: Optional platform specification

        Returns:
            Dictionary with build and push information

        Raises:
            ValidationError: If inputs are invalid
            ArtifactRegistryError: If build or push fails

        Example:
            >>> result = builder.build_and_push(
            ...     dockerfile_path="./Dockerfile",
            ...     context_path=".",
            ...     image_url="us-central1-docker.pkg.dev/my-project/my-repo/app:v1"
            ... )
            >>> print(f"Image ready: {result['image_url']}")
        """
        # Build the image
        build_result = self.build_image(
            dockerfile_path=dockerfile_path,
            context_path=context_path,
            image_url=image_url,
            build_args=build_args,
            no_cache=no_cache,
            platform=platform,
        )

        # Push the image
        push_result = self.push_image(image_url)

        return {
            "image_url": image_url,
            "build": build_result,
            "push": push_result,
            "success": True,
        }

    def tag_image(self, source_image: str, target_image: str) -> None:
        """
        Tag an existing image with a new name/tag.

        Args:
            source_image: Existing image URL or ID
            target_image: New image URL

        Raises:
            ArtifactRegistryError: If tagging fails

        Example:
            >>> builder.tag_image(
            ...     "my-app:latest",
            ...     "us-central1-docker.pkg.dev/my-project/my-repo/my-app:v1.0.0"
            ... )
        """
        try:
            result = subprocess.run(
                ["docker", "tag", source_image, target_image],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise ArtifactRegistryError(
                    f"Docker tag failed: {result.stderr}",
                    details={"stderr": result.stderr},
                )

        except subprocess.TimeoutExpired:
            raise ArtifactRegistryError(
                "Docker tag command timed out",
                details={"source": source_image, "target": target_image},
            )
        except Exception as e:
            if isinstance(e, ArtifactRegistryError):
                raise
            raise ArtifactRegistryError(
                f"Docker tag failed: {str(e)}",
                details={
                    "source": source_image,
                    "target": target_image,
                    "error": str(e),
                },
            ) from e

    def get_image_info(self, image_url: str) -> dict[str, Any]:
        """
        Get information about a Docker image.

        Args:
            image_url: Image URL or ID

        Returns:
            Dictionary with image information

        Raises:
            ArtifactRegistryError: If inspection fails

        Example:
            >>> info = builder.get_image_info("my-app:latest")
            >>> print(info["Id"])
        """
        try:
            result = subprocess.run(
                ["docker", "inspect", image_url],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise ArtifactRegistryError(
                    f"Docker inspect failed: {result.stderr}",
                    details={"stderr": result.stderr},
                )

            info = json.loads(result.stdout)
            return info[0] if info else {}

        except json.JSONDecodeError as e:
            raise ArtifactRegistryError(
                f"Failed to parse docker inspect output: {e}",
                details={"error": str(e)},
            ) from e
        except Exception as e:
            if isinstance(e, ArtifactRegistryError):
                raise
            raise ArtifactRegistryError(
                f"Failed to get image info: {str(e)}",
                details={"image_url": image_url, "error": str(e)},
            ) from e
