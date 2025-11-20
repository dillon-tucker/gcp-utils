"""
Example usage of Cloud Build controller.

This example demonstrates:
- Creating and executing builds
- Creating build triggers for CI/CD
- Managing build lifecycle
- Integrating with GitHub and Cloud Source Repositories
- Building and deploying containers

Requirements:
- Valid GCP project with Cloud Build API enabled
- .env file with GCP_PROJECT_ID set
- Docker images or source code repositories
"""

from gcp_utils.controllers import CloudBuildController

# Initialize controller (auto-loads from .env)
cloud_build = CloudBuildController()


def example_simple_build() -> None:
    """
    Create and execute a simple build with custom steps.

    This example builds a Docker image and pushes it to GCR.
    """
    print("\n=== Creating Simple Build ===")

    steps = [
        {
            "name": "gcr.io/cloud-builders/docker",
            "args": [
                "build",
                "-t",
                "gcr.io/my-project/my-app:latest",
                "-t",
                "gcr.io/my-project/my-app:$BUILD_ID",
                ".",
            ],
        },
        {
            "name": "gcr.io/cloud-builders/docker",
            "args": ["push", "gcr.io/my-project/my-app:latest"],
        },
        {
            "name": "gcr.io/cloud-builders/docker",
            "args": ["push", "gcr.io/my-project/my-app:$BUILD_ID"],
        },
    ]

    try:
        build = cloud_build.create_build(
            steps=steps,
            images=[
                "gcr.io/my-project/my-app:latest",
                "gcr.io/my-project/my-app:$BUILD_ID",
            ],
            timeout="600s",
            tags=["manual-build", "my-app"],
            wait_for_completion=False,
        )

        print(f"✓ Build created: {build.id}")
        print(f"  Project: {build.project_id}")
        print(f"  Check build status: gcloud builds describe {build.id}")

    except Exception as e:
        print(f"✗ Error creating build: {e}")


def example_build_with_source() -> None:
    """
    Create a build with source code from Cloud Storage.

    This is useful for building from ZIP archives.
    """
    print("\n=== Creating Build with Source ===")

    source = {
        "storage_source": {
            "bucket": "my-source-bucket",
            "object": "my-app-source.zip",
        }
    }

    steps = [
        {
            "name": "gcr.io/cloud-builders/docker",
            "args": ["build", "-t", "gcr.io/my-project/my-app:$SHORT_SHA", "."],
        },
    ]

    try:
        build = cloud_build.create_build(
            steps=steps,
            source=source,
            images=["gcr.io/my-project/my-app:$SHORT_SHA"],
            substitutions={
                "SHORT_SHA": "abc123",
                "BRANCH_NAME": "main",
            },
        )

        print(f"✓ Build with source created: {build.id}")

    except Exception as e:
        print(f"✗ Error creating build: {e}")


def example_create_github_trigger() -> None:
    """
    Create a build trigger for GitHub repository.

    This trigger runs builds automatically when code is pushed to GitHub.
    """
    print("\n=== Creating GitHub Build Trigger ===")

    github_config = {
        "owner": "my-org",
        "name": "my-repo",
        "push": {
            "branch": "^main$",  # Trigger on pushes to main branch
        },
    }

    try:
        trigger = cloud_build.create_build_trigger(
            name="deploy-on-push",
            description="Deploy when pushing to main branch",
            github=github_config,
            filename="cloudbuild.yaml",  # Use cloudbuild.yaml from repo
            substitutions={
                "_DEPLOY_ENV": "production",
                "_REGION": "us-central1",
            },
            tags=["github", "auto-deploy"],
        )

        print(f"✓ GitHub trigger created: {trigger.name}")
        print(f"  ID: {trigger.id}")
        print(f"  Description: {trigger.description}")

    except Exception as e:
        print(f"✗ Error creating trigger: {e}")


def example_create_cloud_source_trigger() -> None:
    """
    Create a build trigger for Cloud Source Repositories.

    This trigger runs builds for changes in Cloud Source Repositories.
    """
    print("\n=== Creating Cloud Source Repository Trigger ===")

    trigger_template = {
        "project_id": "my-project",
        "repo_name": "my-repo",
        "branch_name": "main",
    }

    try:
        trigger = cloud_build.create_build_trigger(
            name="build-on-commit",
            description="Build on every commit to main",
            trigger_template=trigger_template,
            filename="cloudbuild.yaml",
        )

        print(f"✓ Cloud Source Repository trigger created: {trigger.name}")
        print(f"  ID: {trigger.id}")

    except Exception as e:
        print(f"✗ Error creating trigger: {e}")


def example_create_trigger_with_inline_build() -> None:
    """
    Create a trigger with inline build configuration.

    Instead of using cloudbuild.yaml, define the build steps in the trigger.
    """
    print("\n=== Creating Trigger with Inline Build ===")

    build_config = {
        "steps": [
            {
                "name": "gcr.io/cloud-builders/docker",
                "args": ["build", "-t", "gcr.io/$PROJECT_ID/app:$COMMIT_SHA", "."],
            },
            {
                "name": "gcr.io/cloud-builders/docker",
                "args": ["push", "gcr.io/$PROJECT_ID/app:$COMMIT_SHA"],
            },
            {
                "name": "gcr.io/cloud-builders/gcloud",
                "args": [
                    "run",
                    "deploy",
                    "my-service",
                    "--image",
                    "gcr.io/$PROJECT_ID/app:$COMMIT_SHA",
                    "--region",
                    "us-central1",
                ],
            },
        ],
        "images": ["gcr.io/$PROJECT_ID/app:$COMMIT_SHA"],
    }

    trigger_template = {
        "project_id": "my-project",
        "repo_name": "my-repo",
        "branch_name": "main",
    }

    try:
        trigger = cloud_build.create_build_trigger(
            name="build-and-deploy",
            description="Build Docker image and deploy to Cloud Run",
            trigger_template=trigger_template,
            build=build_config,
        )

        print(f"✓ Trigger with inline build created: {trigger.name}")

    except Exception as e:
        print(f"✗ Error creating trigger: {e}")


def example_list_and_get_builds() -> None:
    """
    List builds and get details for specific ones.
    """
    print("\n=== Listing Recent Builds ===")

    try:
        # List recent builds
        response = cloud_build.list_builds(page_size=10)

        print(f"Found {len(response.builds)} recent builds:")
        for build in response.builds[:5]:  # Show first 5
            print(f"\n  Build ID: {build.id}")
            print(f"    Status: {build.status}")
            print(f"    Created: {build.create_time}")
            if build.log_url:
                print(f"    Logs: {build.log_url}")

        # Get details for a specific build
        if response.builds:
            build_id = response.builds[0].id
            print(f"\n=== Getting Details for Build {build_id} ===")

            build = cloud_build.get_build(build_id)
            print(f"  Status: {build.status}")
            print(f"  Created: {build.create_time}")
            print(f"  Started: {build.start_time}")
            print(f"  Finished: {build.finish_time}")

    except Exception as e:
        print(f"✗ Error: {e}")


def example_list_triggers() -> None:
    """
    List all build triggers.
    """
    print("\n=== Listing Build Triggers ===")

    try:
        response = cloud_build.list_build_triggers()

        print(f"Found {len(response.triggers)} triggers:")
        for trigger in response.triggers:
            print(f"\n  Trigger: {trigger.name}")
            print(f"    ID: {trigger.id}")
            print(f"    Description: {trigger.description}")
            print(f"    Disabled: {trigger.disabled}")
            if trigger.filename:
                print(f"    Config file: {trigger.filename}")

    except Exception as e:
        print(f"✗ Error listing triggers: {e}")


def example_run_trigger_manually() -> None:
    """
    Manually run a build trigger.

    This is useful for testing triggers without pushing code.
    """
    print("\n=== Running Trigger Manually ===")

    try:
        response = cloud_build.run_build_trigger(
            trigger_id="trigger123",
            branch_name="main",
        )

        print(f"✓ Trigger executed")
        print(f"  Build ID: {response.build_id}")
        print(f"  Check status: gcloud builds describe {response.build_id}")

    except Exception as e:
        print(f"✗ Error running trigger: {e}")


def example_update_trigger() -> None:
    """
    Update an existing build trigger.

    This example disables a trigger.
    """
    print("\n=== Updating Build Trigger ===")

    try:
        trigger = cloud_build.update_build_trigger(
            trigger_id="trigger123",
            disabled=True,
            description="Updated: Temporarily disabled",
        )

        print(f"✓ Trigger updated: {trigger.name}")
        print(f"  Disabled: {trigger.disabled}")

    except Exception as e:
        print(f"✗ Error updating trigger: {e}")


def example_cancel_build() -> None:
    """
    Cancel a running build.
    """
    print("\n=== Cancelling Build ===")

    try:
        build = cloud_build.cancel_build("build123")

        print(f"✓ Build cancelled: {build.id}")
        print(f"  Status: {build.status}")

    except Exception as e:
        print(f"✗ Error cancelling build: {e}")


def example_delete_trigger() -> None:
    """
    Delete a build trigger.

    CAUTION: This permanently deletes the trigger.
    """
    print("\n=== Deleting Build Trigger ===")

    try:
        cloud_build.delete_build_trigger("trigger123")
        print("✓ Trigger deleted successfully")

    except Exception as e:
        print(f"✗ Error deleting trigger: {e}")


def example_complete_ci_cd_workflow() -> None:
    """
    Example of a complete CI/CD workflow.

    This creates a trigger that:
    1. Builds a Docker image
    2. Pushes to Artifact Registry
    3. Deploys to Cloud Run
    """
    print("\n=== Complete CI/CD Workflow ===")

    build_config = {
        "steps": [
            # Run tests
            {
                "name": "python:3.12",
                "entrypoint": "bash",
                "args": ["-c", "pip install -r requirements.txt && pytest"],
            },
            # Build Docker image
            {
                "name": "gcr.io/cloud-builders/docker",
                "args": [
                    "build",
                    "-t",
                    "us-central1-docker.pkg.dev/$PROJECT_ID/my-app/api:$SHORT_SHA",
                    "-t",
                    "us-central1-docker.pkg.dev/$PROJECT_ID/my-app/api:latest",
                    ".",
                ],
            },
            # Push to Artifact Registry
            {
                "name": "gcr.io/cloud-builders/docker",
                "args": ["push", "--all-tags", "us-central1-docker.pkg.dev/$PROJECT_ID/my-app/api"],
            },
            # Deploy to Cloud Run
            {
                "name": "gcr.io/cloud-builders/gcloud",
                "args": [
                    "run",
                    "deploy",
                    "my-api",
                    "--image",
                    "us-central1-docker.pkg.dev/$PROJECT_ID/my-app/api:$SHORT_SHA",
                    "--region",
                    "us-central1",
                    "--platform",
                    "managed",
                ],
            },
        ],
        "images": [
            "us-central1-docker.pkg.dev/$PROJECT_ID/my-app/api:$SHORT_SHA",
            "us-central1-docker.pkg.dev/$PROJECT_ID/my-app/api:latest",
        ],
    }

    trigger_template = {
        "project_id": "my-project",
        "repo_name": "my-api",
        "branch_name": "main",
    }

    try:
        trigger = cloud_build.create_build_trigger(
            name="ci-cd-pipeline",
            description="Complete CI/CD: Test, Build, Push, Deploy",
            trigger_template=trigger_template,
            build=build_config,
            tags=["ci-cd", "production"],
        )

        print(f"✓ CI/CD pipeline trigger created: {trigger.name}")
        print(f"  On every push to main:")
        print(f"    1. Run tests")
        print(f"    2. Build Docker image")
        print(f"    3. Push to Artifact Registry")
        print(f"    4. Deploy to Cloud Run")

    except Exception as e:
        print(f"✗ Error creating CI/CD trigger: {e}")


if __name__ == "__main__":
    print("Cloud Build Controller Example")
    print("=" * 50)

    # Run examples
    # example_simple_build()
    # example_build_with_source()
    # example_create_github_trigger()
    # example_create_cloud_source_trigger()
    # example_create_trigger_with_inline_build()
    example_list_and_get_builds()
    example_list_triggers()
    # example_run_trigger_manually()
    # example_update_trigger()
    # example_cancel_build()
    # example_delete_trigger()  # Uncomment to test deletion
    # example_complete_ci_cd_workflow()

    print("\n" + "=" * 50)
    print("Example completed!")
