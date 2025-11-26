"""
Example: Complete Docker build, push, and Cloud Run deployment workflow.

This example demonstrates the complete CI/CD pipeline for containerized applications:
1. Create Artifact Registry repository
2. Build Docker image
3. Push to Artifact Registry
4. Deploy to Cloud Run

This is the typical workflow for deploying containerized applications to GCP.
"""

from gcp_utils.config import GCPSettings
from gcp_utils.controllers import (
    ArtifactRegistryController,
    CloudRunController,
)
from gcp_utils.utils import DockerBuilder
from gcp_utils.exceptions import (
    ArtifactRegistryError,
    CloudRunError,
)


def main():
    # Initialize settings
    settings = GCPSettings(
        project_id="my-gcp-project",
        location="us-central1",
    )

    # Initialize controllers
    registry = ArtifactRegistryController(settings)
    cloud_run = CloudRunController(settings)
    docker_builder = DockerBuilder()

    # Configuration
    location = "us-central1"
    repository_id = "my-app-images"
    image_name = "my-web-app"
    image_tag = "v1.0.0"
    service_name = "my-web-app"

    # Example 1: Create Artifact Registry repository
    print("=" * 60)
    print("Creating Artifact Registry repository...")
    print("=" * 60)
    try:
        repo = registry.create_repository(
            repository_id=repository_id,
            location=location,
            format="DOCKER",
            description="Docker images for my web application",
            labels={"environment": "production", "app": "web"},
        )
        print(f"✓ Created repository: {repo['name']}")
        print(f"  Format: {repo['format']}")
        print(f"  Location: {location}")
    except ArtifactRegistryError as e:
        if "already exists" in str(e):
            print(f"✓ Repository '{repository_id}' already exists")
        else:
            print(f"✗ Failed to create repository: {e.message}")
            return

    # Example 2: Configure Docker authentication
    print("\n" + "=" * 60)
    print("Configuring Docker authentication...")
    print("=" * 60)
    try:
        registry.configure_docker_auth(location)
        print(f"✓ Docker configured for {location}-docker.pkg.dev")
    except ArtifactRegistryError as e:
        print(f"✗ Failed to configure Docker auth: {e.message}")
        print("  You may need to run: gcloud auth configure-docker manually")

    # Example 3: Build Docker image
    print("\n" + "=" * 60)
    print("Building Docker image...")
    print("=" * 60)

    # Get the full image URL
    image_url = registry.get_docker_image_url(
        repository_id=repository_id,
        location=location,
        image_name=image_name,
        tag=image_tag,
    )
    print(f"Image URL: {image_url}")

    try:
        build_result = docker_builder.build_image(
            dockerfile_path="./Dockerfile",
            context_path=".",
            image_url=image_url,
            build_args={
                "VERSION": image_tag,
                "BUILD_DATE": "2025-11-14",
            },
            platform="linux/amd64",  # Important for Cloud Run
        )
        print(f"✓ Image built: {build_result['image_url']}")
    except ArtifactRegistryError as e:
        print(f"✗ Build failed: {e.message}")
        return

    # Example 4: Push Docker image to Artifact Registry
    print("\n" + "=" * 60)
    print("Pushing image to Artifact Registry...")
    print("=" * 60)
    try:
        push_result = docker_builder.push_image(image_url)
        print(f"✓ Image pushed: {push_result['image_url']}")
    except ArtifactRegistryError as e:
        print(f"✗ Push failed: {e.message}")
        return

    # Example 5: Deploy to Cloud Run
    print("\n" + "=" * 60)
    print("Deploying to Cloud Run...")
    print("=" * 60)
    try:
        cloud_run.create_service(
            service_name=service_name,
            image=image_url,
            region=location,
            cpu="1000m",
            memory="512Mi",
            max_instances=10,
            min_instances=0,
            env_vars={
                "VERSION": image_tag,
                "ENVIRONMENT": "production",
            },
            allow_unauthenticated=True,  # Make publicly accessible
        )

        service_url = cloud_run.get_service_url(service_name, location)
        print("✓ Service deployed!")
        print(f"  Service URL: {service_url}")
        print(f"  Image: {image_url}")
    except CloudRunError as e:
        print(f"✗ Deployment failed: {e.message}")
        return

    # Example 6: List images in repository
    print("\n" + "=" * 60)
    print("Listing images in repository...")
    print("=" * 60)
    try:
        images = registry.list_docker_images(repository_id, location)
        print(f"Found {len(images)} image(s):")
        for img in images[:5]:  # Show first 5
            print(f"  - {img.get('image', 'N/A')}:{img.get('tag', 'N/A')}")
    except ArtifactRegistryError as e:
        print(f"✗ Failed to list images: {e.message}")

    # Example 7: Complete workflow using build_and_push
    print("\n" + "=" * 60)
    print("Alternative: One-step build and push...")
    print("=" * 60)
    print(
        """
    You can also use the build_and_push method for a simpler workflow:

    image_url = registry.get_docker_image_url(
        repository_id="my-app",
        location="us-central1",
        image_name="app",
        tag="v2.0.0",
    )

    result = docker_builder.build_and_push(
        dockerfile_path="./Dockerfile",
        context_path=".",
        image_url=image_url,
        platform="linux/amd64",
    )

    # Then deploy
    cloud_run.create_service(
        service_name="my-app",
        image=image_url,
        region="us-central1",
        allow_unauthenticated=True,
    )
    """
    )

    # Example 8: Update existing Cloud Run service
    print("\n" + "=" * 60)
    print("Updating Cloud Run service with new image...")
    print("=" * 60)
    print(
        """
    To update an existing service with a new image:

    # Build and push new version
    new_image_url = registry.get_docker_image_url(
        repository_id="my-app",
        location="us-central1",
        image_name="app",
        tag="v2.0.0",
    )

    docker_builder.build_and_push(
        dockerfile_path="./Dockerfile",
        context_path=".",
        image_url=new_image_url,
    )

    # Update the service
    cloud_run.update_service(
        service_name="my-app",
        region="us-central1",
        image=new_image_url,
    )
    """
    )

    # Example 9: CI/CD Integration
    print("\n" + "=" * 60)
    print("CI/CD Integration Pattern...")
    print("=" * 60)
    print(
        """
    Typical CI/CD workflow:

    1. Developer pushes code to Git
    2. CI system triggers build:
       - Runs tests
       - Builds Docker image
       - Pushes to Artifact Registry
       - Deploys to Cloud Run (staging)

    3. After approval:
       - Promote to production

    Example CI script:

    import os
    from gcp_utils.config import GCPSettings
    from gcp_utils.controllers import ArtifactRegistryController, CloudRunController
    from gcp_utils.utils import DockerBuilder

    # Get version from Git
    git_sha = os.getenv('GITHUB_SHA', 'latest')[:7]

    settings = GCPSettings(project_id=os.getenv('GCP_PROJECT'))
    registry = ArtifactRegistryController(settings)
    builder = DockerBuilder()
    cloud_run = CloudRunController(settings)

    # Build and push
    image_url = registry.get_docker_image_url(
        "my-repo", "us-central1", "app", git_sha
    )
    builder.build_and_push("./Dockerfile", ".", image_url)

    # Deploy to staging
    cloud_run.create_service("app-staging", image_url, "us-central1")
    """
    )

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)
    print(f"\nYour app is now running at: {service_url}")
    print("\nNext steps:")
    print("  1. Test the deployed application")
    print("  2. Set up custom domain (optional)")
    print("  3. Configure CI/CD pipeline")
    print("  4. Set up monitoring and logging")


if __name__ == "__main__":
    main()
