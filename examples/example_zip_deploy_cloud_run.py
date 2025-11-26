"""
Example: Zip and Deploy to Cloud Run via Cloud Build

This example demonstrates deploying to Cloud Run from source code using Cloud Build:
1. Create/prepare source code directory with Dockerfile
2. Zip the source code
3. Upload ZIP to Cloud Storage
4. Use Cloud Build to build container from source
5. Deploy container to Cloud Run
6. Test the deployed service
7. Cleanup resources

This workflow is ideal for:
- CI/CD pipelines that don't want to build Docker locally
- Teams without Docker installed
- Consistent builds across environments
- Automatic container registry management
"""

import sys
import tempfile
from pathlib import Path

# Add src to path for running without installation
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gcp_utils.controllers import (
    CloudBuildController,
    CloudRunController,
    CloudStorageController,
    ArtifactRegistryController,
)
from gcp_utils.utils import ZipUtility
from gcp_utils.config import get_settings


def create_sample_app(app_dir: Path) -> None:
    """
    Create a sample Cloud Run application.

    Creates a simple Flask app with Dockerfile.

    Args:
        app_dir: Directory to create the app in
    """
    # Create main.py with a simple Flask app
    main_py = app_dir / "main.py"
    main_py.write_text(
        '''"""Sample Cloud Run application."""

import os
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/", methods=["GET"])
def hello():
    """Simple hello endpoint."""
    name = request.args.get("name", "World")
    return jsonify({
        "message": f"Hello, {name}!",
        "service": "example-cloud-run-app",
        "deployed_with": "gcp-utils zip utility",
        "environment": os.environ.get("ENVIRONMENT", "unknown"),
    })


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
'''
    )

    # Create requirements.txt
    requirements_txt = app_dir / "requirements.txt"
    requirements_txt.write_text("flask==3.0.*\ngunicorn==21.*\n")

    # Create Dockerfile
    dockerfile = app_dir / "Dockerfile"
    dockerfile.write_text(
        """# Use official Python runtime
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run with gunicorn for production
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 0 main:app
"""
    )

    # Create .dockerignore (should be included in ZIP)
    dockerignore = app_dir / ".dockerignore"
    dockerignore.write_text(
        """# Ignore these files when building Docker image
__pycache__
*.pyc
.env
.git
.gitignore
venv
.venv
*.log
.DS_Store
README.md
"""
    )

    # Create .env (should be excluded from ZIP)
    env_file = app_dir / ".env"
    env_file.write_text("SECRET_KEY=should_not_be_in_zip\n")

    # Create test file (should be excluded)
    test_file = app_dir / "test_main.py"
    test_file.write_text("# Test file that should be excluded\n")

    print(f"Created sample Cloud Run app in: {app_dir}")
    print("  Files:")
    for file in app_dir.rglob("*"):
        if file.is_file():
            print(f"    - {file.relative_to(app_dir)}")


def main() -> None:
    """Demonstrate complete Cloud Run deployment workflow via Cloud Build."""

    settings = get_settings()

    print("=" * 80)
    print("Cloud Run Deployment Example - Zip, Build, and Deploy")
    print("=" * 80)

    # Configuration
    service_name = "example-zip-app"
    bucket_name = f"{settings.project_id}-cloudrun-deployments"
    repository_id = "cloudrun-apps"
    location = "us-central1"

    # Initialize controllers
    storage = CloudStorageController()
    cloud_build = CloudBuildController()
    cloud_run = CloudRunController()
    artifact_registry = ArtifactRegistryController()
    zip_util = ZipUtility(storage_controller=storage)

    # Step 1: Create sample application code
    print("\n" + "=" * 80)
    print("Step 1: Creating sample Cloud Run application")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temp_dir:
        app_dir = Path(temp_dir) / "my-app"
        app_dir.mkdir()

        create_sample_app(app_dir)

        # Step 2: Create Cloud Storage bucket
        print("\n" + "=" * 80)
        print("Step 2: Creating Cloud Storage bucket")
        print("=" * 80)

        try:
            bucket_info = storage.create_bucket(
                bucket_name=bucket_name,
                location=location,
            )
            print(f"[OK] Created bucket: {bucket_info.name}")
        except Exception as e:
            if "409" in str(e) or "already exists" in str(e).lower():
                print(f"[INFO] Bucket already exists: {bucket_name}")
            else:
                print(f"[ERROR] Failed to create bucket: {e}")
                return

        # Step 3: Create Artifact Registry repository (if needed)
        print("\n" + "=" * 80)
        print("Step 3: Creating Artifact Registry repository")
        print("=" * 80)

        try:
            repo = artifact_registry.create_repository(
                repository_id=repository_id,
                location=location,
                format="DOCKER",
                description="Repository for Cloud Run applications",
            )
            print(f"[OK] Created repository: {repo['name']}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"[INFO] Repository already exists: {repository_id}")
            else:
                print(f"[ERROR] Failed to create repository: {e}")
                return

        # Step 4: Zip the application source
        print("\n" + "=" * 80)
        print("Step 4: Creating ZIP archive of application source")
        print("=" * 80)

        destination_blob = f"cloud-run/{service_name}/source.zip"

        try:
            print("Zipping and uploading source code...")
            upload_result = zip_util.zip_and_upload(
                source_dir=app_dir,
                bucket_name=bucket_name,
                destination_blob_name=destination_blob,
                exclude_patterns=[
                    "*.pyc",
                    "__pycache__",
                    ".env",
                    "test_*.py",
                    ".git",
                    "venv",
                    ".venv",
                ],
                metadata={
                    "service": service_name,
                    "type": "cloud-run-source",
                },
            )

            print("[OK] Uploaded source ZIP")
            print(f"  Bucket: {upload_result.bucket}")
            print(f"  Blob: {upload_result.blob_name}")
            print(
                f"  Size: {upload_result.size:,} bytes ({upload_result.size / 1024:.2f} KB)"
            )
            print(f"  GCS URL: gs://{upload_result.bucket}/{upload_result.blob_name}")

        except Exception as e:
            print(f"[ERROR] Failed to zip and upload: {e}")
            return

        # Step 5: Use Cloud Build to build container from source
        print("\n" + "=" * 80)
        print("Step 5: Building container with Cloud Build")
        print("=" * 80)

        # Generate image URL
        image_url = artifact_registry.get_docker_image_url(
            repository_id=repository_id,
            location=location,
            image_name=service_name,
            tag="latest",
        )

        print(f"Target image: {image_url}")

        try:
            # Create Cloud Build configuration
            # This will:
            # 1. Extract source from GCS
            # 2. Build Docker image
            # 3. Push to Artifact Registry
            build_steps = [
                {
                    "name": "gcr.io/cloud-builders/gsutil",
                    "args": [
                        "cp",
                        f"gs://{bucket_name}/{destination_blob}",
                        "source.zip",
                    ],
                },
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": [
                        "run",
                        "--rm",
                        "-v",
                        "/workspace:/workspace",
                        "busybox",
                        "unzip",
                        "source.zip",
                    ],
                },
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": [
                        "build",
                        "-t",
                        image_url,
                        "-f",
                        "Dockerfile",
                        ".",
                    ],
                },
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": ["push", image_url],
                },
            ]

            print("Starting Cloud Build...")
            print("  Steps:")
            print("    1. Download source ZIP from Cloud Storage")
            print("    2. Extract ZIP")
            print("    3. Build Docker image")
            print("    4. Push to Artifact Registry")

            build = cloud_build.create_build(
                steps=build_steps,
                images=[image_url],
                timeout="600s",
                tags=["cloud-run", service_name],
                wait_for_completion=True,
            )

            print("[OK] Build completed successfully!")
            print(f"  Build ID: {build.id}")
            print(f"  Status: {build.status}")
            if build.log_url:
                print(f"  Logs: {build.log_url}")

        except Exception as e:
            print(f"[ERROR] Build failed: {e}")
            print("\nNote: Make sure Cloud Build API is enabled and has permissions:")
            print("  - Cloud Build Service Account")
            print("  - Artifact Registry Writer")
            return

        # Step 6: Deploy to Cloud Run
        print("\n" + "=" * 80)
        print("Step 6: Deploying to Cloud Run")
        print("=" * 80)

        try:
            print(f"Deploying service '{service_name}'...")
            print(f"  Image: {image_url}")
            print(f"  Region: {location}")
            print("  CPU: 1 vCPU")
            print("  Memory: 512 MB")

            service = cloud_run.create_service(
                service_name=service_name,
                image=image_url,
                port=8080,
                cpu="1000m",
                memory="512Mi",
                max_instances=10,
                min_instances=0,
                env_vars={
                    "ENVIRONMENT": "production",
                    "DEPLOYED_BY": "gcp-utils",
                },
                allow_unauthenticated=True,
                labels={
                    "deployed-by": "gcp-utils",
                    "deployment-method": "zip-cloud-build",
                },
            )

            print("[OK] Service deployed successfully!")
            print(f"  Name: {service.name}")
            print(f"  URL: {service.url}")
            print(f"  Region: {service.region}")
            print(f"  Image: {service.image}")

        except Exception as e:
            if "already exists" in str(e).lower():
                print("[INFO] Service already exists, getting details...")
                try:
                    service = cloud_run.get_service(service_name)
                    print("[OK] Service details:")
                    print(f"  Name: {service.name}")
                    print(f"  URL: {service.url}")
                    print(f"  Region: {service.region}")
                except Exception as get_error:
                    print(f"[ERROR] Failed to get service: {get_error}")
                    return
            else:
                print(f"[ERROR] Failed to deploy service: {e}")
                return

        # Step 7: Test the deployed service
        print("\n" + "=" * 80)
        print("Step 7: Testing the deployed service")
        print("=" * 80)

        if service.url:
            print(f"Service URL: {service.url}")
            print("\nYou can test the service with:")
            print(f"  curl {service.url}")
            print(f"  curl '{service.url}?name=Cloud'")
            print(f"  curl {service.url}/health")
            print("\nOr open in browser:")
            print(f"  {service.url}")

            # Try to invoke the service
            print("\nInvoking service programmatically...")
            try:
                response = cloud_run.invoke_service(
                    service_name=service_name,
                    path="/",
                    method="GET",
                )
                print("[OK] Service responded!")
                print(f"  Status: {response['status_code']}")
                if response.get("json"):
                    print(f"  Response: {response['json']}")
                else:
                    print(f"  Content: {response['content'][:200]}...")
            except Exception as e:
                print(f"[WARNING] Failed to invoke service: {e}")
                print("  (This is expected if the service requires authentication)")
        else:
            print("[WARNING] Service URL not available")

    # Step 8: Cleanup instructions
    print("\n" + "=" * 80)
    print("Step 8: Cleanup")
    print("=" * 80)

    print("\nTo clean up all resources:")
    print("  1. Delete Cloud Run service")
    print("  2. Delete Docker image from Artifact Registry")
    print("  3. Delete source ZIP from Cloud Storage")
    print("  4. Delete bucket (optional)")

    print("\nRun this code:")
    print(
        f"""
# Delete Cloud Run service
try:
    cloud_run.delete_service('{service_name}')
    print('[OK] Deleted Cloud Run service')
except Exception as e:
    print(f'[ERROR] Failed to delete service: {{e}}')

# Delete storage bucket
try:
    storage.delete_bucket('{bucket_name}', force=True)
    print('[OK] Deleted bucket')
except Exception as e:
    print(f'[ERROR] Failed to delete bucket: {{e}}')

# Note: Image in Artifact Registry can be deleted manually or left for reuse
print('\\nArtifact Registry image: {image_url}')
print('Delete manually if needed via gcloud or Console')
"""
    )

    # Summary
    print("\n" + "=" * 80)
    print("Summary: Complete Cloud Run Deployment Workflow")
    print("=" * 80)

    print(
        """
This example demonstrated a complete Cloud Run deployment from source code:

1. ✓ Created sample Flask application with Dockerfile
2. ✓ Created Cloud Storage bucket for source artifacts
3. ✓ Created Artifact Registry repository for images
4. ✓ Zipped source code with smart exclusions
5. ✓ Uploaded ZIP to Cloud Storage
6. ✓ Used Cloud Build to build Docker image from source
7. ✓ Deployed container to Cloud Run
8. ✓ Service is now accessible via HTTPS URL

Key Advantages of This Workflow:

1. No Local Docker Required:
   - Build happens in the cloud
   - Consistent across all environments
   - No "works on my machine" issues

2. Automatic Container Registry:
   - Images stored in Artifact Registry
   - Version control with tags
   - Vulnerability scanning

3. CI/CD Friendly:
   - Zip source in CI pipeline
   - Upload to Cloud Storage
   - Trigger Cloud Build
   - Deploy to Cloud Run
   - All programmatic, no manual steps

4. Build Reproducibility:
   - Cloud Build provides consistent environment
   - Build logs are preserved
   - Easy to debug build issues

Comparison with Other Deployment Methods:

Method 1: Docker + Artifact Registry + Cloud Run
  Pros: Full control, test locally
  Cons: Requires Docker, manual build steps

Method 2: Source + Cloud Build + Cloud Run (This Example)
  Pros: No Docker needed, CI/CD friendly
  Cons: Slight overhead for build step

Method 3: Cloud Functions
  Pros: Simpler, no Dockerfile needed
  Cons: Limited to function patterns, 540s timeout

Method 4: Buildpacks (gcloud run deploy --source)
  Pros: Automatic Dockerfile generation
  Cons: Less control over build

Example Integration in CI/CD:

```python
# In your CI/CD pipeline (e.g., GitHub Actions, GitLab CI)
from gcp_utils.utils import zip_and_upload
from gcp_utils.controllers import CloudBuildController, CloudRunController

# 1. Zip and upload source
result = zip_and_upload(
    source_dir="./app",
    bucket_name="my-deployments",
    destination_blob_name=f"cloud-run/my-app/{{git_commit}}.zip",
)

# 2. Build with Cloud Build
cloud_build = CloudBuildController()
image_url = f"us-central1-docker.pkg.dev/my-project/apps/my-app:{{git_commit}}"

build = cloud_build.create_build(
    steps=[
        # Extract source
        {{
            "name": "gcr.io/cloud-builders/gsutil",
            "args": ["cp", f"gs://{{result.bucket}}/{{result.blob_name}}", "source.zip"],
        }},
        # Build and push
        {{
            "name": "gcr.io/cloud-builders/docker",
            "args": ["build", "-t", image_url, "."],
        }},
        {{
            "name": "gcr.io/cloud-builders/docker",
            "args": ["push", image_url],
        }},
    ],
    images=[image_url],
    wait_for_completion=True,
)

# 3. Deploy to Cloud Run
cloud_run = CloudRunController()
service = cloud_run.create_service(
    service_name="my-app",
    image=image_url,
    env_vars={{"GIT_COMMIT": git_commit}},
)

print(f"Deployed: {{service.url}}")
```

Best Practices:

1. Source Code Management:
   - Always exclude .env files
   - Exclude test files and __pycache__
   - Keep ZIP size reasonable (<500MB)
   - Use .dockerignore in your app

2. Image Tagging:
   - Use semantic versioning (v1.0.0)
   - Tag with git commit hash
   - Tag with environment (staging, production)
   - Keep 'latest' tag for most recent

3. Build Configuration:
   - Set reasonable timeout (default 10min)
   - Use build substitutions for variables
   - Cache dependencies when possible
   - Log build metrics

4. Cloud Run Configuration:
   - Set appropriate CPU/memory
   - Configure autoscaling (min/max instances)
   - Use health checks
   - Set proper timeout values
   - Use secrets for sensitive data

5. Security:
   - Never commit secrets to source
   - Use Secret Manager for sensitive config
   - Limit service account permissions
   - Use VPC connector for private resources
   - Enable authentication for internal services

Troubleshooting:

1. Build Fails:
   - Check Cloud Build logs (URL in output)
   - Verify Dockerfile syntax
   - Check file permissions
   - Ensure all dependencies in requirements.txt

2. Deployment Fails:
   - Check Cloud Build completed successfully
   - Verify image exists in Artifact Registry
   - Check Cloud Run service logs
   - Verify IAM permissions

3. Service Not Responding:
   - Check container listens on PORT env var
   - Verify health check endpoint
   - Check service logs for errors
   - Test locally with Docker first

Next Steps:

- Customize the Flask app for your needs
- Add database connections (Cloud SQL, Firestore)
- Implement health checks and monitoring
- Set up Cloud Logging and Error Reporting
- Create staging and production environments
- Implement blue-green or canary deployments
- Add automated testing in Cloud Build
"""
    )

    print("=" * 80)
    print("Example completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
