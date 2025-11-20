"""
Example: Zip and Deploy to Cloud Functions

This example demonstrates the complete workflow for deploying a Cloud Function
from source code:
1. Create/prepare source code directory
2. Zip the directory (excluding unnecessary files)
3. Upload ZIP to Cloud Storage
4. Deploy to Cloud Functions
5. Test the deployed function
6. Cleanup resources

This is the recommended workflow for CI/CD pipelines and automated deployments.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path for running without installation
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gcp_utils.controllers import CloudFunctionsController, CloudStorageController
from gcp_utils.utils import ZipUtility, zip_and_upload
from gcp_utils.config import get_settings


def create_sample_function_code(function_dir: Path) -> None:
    """
    Create a sample Cloud Function for testing.

    Args:
        function_dir: Directory to create the function code in
    """
    # Create main.py with a simple HTTP function
    main_py = function_dir / "main.py"
    main_py.write_text(
        '''"""Sample Cloud Function for deployment testing."""

import functions_framework
from flask import Request


@functions_framework.http
def hello_world(request: Request):
    """
    HTTP Cloud Function that returns a greeting.

    Args:
        request: The HTTP request object

    Returns:
        A greeting message
    """
    name = request.args.get("name", "World")
    return f"Hello, {name}! This function was deployed using gcp-utils."
'''
    )

    # Create requirements.txt
    requirements_txt = function_dir / "requirements.txt"
    requirements_txt.write_text("functions-framework==3.*\n")

    # Create .env file (should be excluded from ZIP)
    env_file = function_dir / ".env"
    env_file.write_text("SECRET_KEY=should_not_be_in_zip\n")

    # Create a test file (should be excluded)
    test_file = function_dir / "test_main.py"
    test_file.write_text("# Test file that should be excluded\n")

    # Create __pycache__ directory (should be excluded)
    pycache_dir = function_dir / "__pycache__"
    pycache_dir.mkdir(exist_ok=True)
    (pycache_dir / "main.cpython-312.pyc").write_text("compiled bytecode")

    print(f"Created sample function code in: {function_dir}")
    print("  Files:")
    for file in function_dir.rglob("*"):
        if file.is_file():
            print(f"    - {file.relative_to(function_dir)}")


def main() -> None:
    """Demonstrate complete Cloud Functions deployment workflow."""

    settings = get_settings()

    print("=" * 80)
    print("Cloud Functions Deployment Example - Zip and Deploy")
    print("=" * 80)

    # Configuration
    function_id = "example-hello-function"
    bucket_name = f"{settings.project_id}-functions-deployment"
    location = "us-central1"

    # Initialize controllers
    storage = CloudStorageController()
    functions = CloudFunctionsController()
    zip_util = ZipUtility(storage_controller=storage)

    # Step 1: Create sample function code
    print("\n" + "=" * 80)
    print("Step 1: Creating sample function code")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temp_dir:
        function_dir = Path(temp_dir) / "my-function"
        function_dir.mkdir()

        create_sample_function_code(function_dir)

        # Step 2: Create bucket for deployment artifacts
        print("\n" + "=" * 80)
        print("Step 2: Creating Cloud Storage bucket for deployments")
        print("=" * 80)

        try:
            bucket_info = storage.create_bucket(
                bucket_name=bucket_name,
                location=location,
            )
            print(f"[OK] Created bucket: {bucket_info.name}")
            print(f"  Location: {bucket_info.location}")
            print(f"  Storage class: {bucket_info.storage_class}")
        except Exception as e:
            if "409" in str(e) or "already exists" in str(e).lower():
                print(f"[INFO] Bucket already exists: {bucket_name}")
            else:
                print(f"[ERROR] Failed to create bucket: {e}")
                return

        # Step 3: Zip the function source code
        print("\n" + "=" * 80)
        print("Step 3: Creating ZIP archive of function source")
        print("=" * 80)

        # Option A: Zip to a specific file (for inspection)
        print("\nOption A: Zip to a specific file")
        zip_path = Path(temp_dir) / "function.zip"
        try:
            result_path = zip_util.zip_directory(
                source_dir=function_dir,
                output_path=zip_path,
                exclude_patterns=[
                    "*.pyc",
                    "__pycache__",
                    ".env",
                    ".git",
                    "test_*.py",
                    "venv",
                    ".venv",
                ],
            )
            print(f"[OK] Created ZIP: {result_path}")

            # Show ZIP contents
            contents = zip_util.list_zip_contents(result_path)
            print(f"  Files in ZIP ({len(contents)}):")
            for file in contents:
                print(f"    - {file}")

            # Show ZIP size
            size = zip_util.get_zip_size(result_path)
            print(f"  ZIP size: {size:,} bytes ({size / 1024:.2f} KB)")

            # Verify excluded files are not in ZIP
            excluded_found = [f for f in contents if ".env" in f or "test_" in f or ".pyc" in f]
            if excluded_found:
                print(f"  [WARNING] Found excluded files in ZIP: {excluded_found}")
            else:
                print(f"  [OK] Excluded files are not in ZIP")

        except Exception as e:
            print(f"[ERROR] Failed to create ZIP: {e}")
            return

        # Step 4: Upload ZIP to Cloud Storage
        print("\n" + "=" * 80)
        print("Step 4: Uploading ZIP to Cloud Storage")
        print("=" * 80)

        destination_blob = f"functions/{function_id}/source.zip"

        try:
            upload_result = storage.upload_file(
                bucket_name=bucket_name,
                source_path=zip_path,
                destination_blob_name=destination_blob,
                content_type="application/zip",
                metadata={
                    "function_id": function_id,
                    "created_by": "gcp-utils-example",
                },
            )
            print(f"[OK] Uploaded ZIP to Cloud Storage")
            print(f"  Bucket: {upload_result.bucket}")
            print(f"  Blob: {upload_result.blob_name}")
            print(f"  Size: {upload_result.size:,} bytes")
            print(f"  MD5: {upload_result.md5_hash}")
            print(f"  GCS URL: gs://{upload_result.bucket}/{upload_result.blob_name}")

        except Exception as e:
            print(f"[ERROR] Failed to upload ZIP: {e}")
            return

        # Alternative: Zip and upload in one step
        print("\n" + "=" * 80)
        print("Alternative: Zip and Upload in One Step")
        print("=" * 80)

        destination_blob_v2 = f"functions/{function_id}/source-v2.zip"

        try:
            print("Using zip_and_upload() convenience function...")
            upload_result = zip_and_upload(
                source_dir=function_dir,
                bucket_name=bucket_name,
                destination_blob_name=destination_blob_v2,
                exclude_patterns=["*.pyc", "__pycache__", ".env", "test_*.py"],
            )
            print(f"[OK] Zipped and uploaded in one step")
            print(f"  GCS URL: gs://{upload_result.bucket}/{upload_result.blob_name}")
            print(f"  Size: {upload_result.size:,} bytes")

        except Exception as e:
            print(f"[ERROR] Failed to zip and upload: {e}")
            # Continue with deployment using the first upload

        # Step 5: Deploy to Cloud Functions
        print("\n" + "=" * 80)
        print("Step 5: Deploying to Cloud Functions")
        print("=" * 80)

        try:
            # Build configuration
            build_config = {
                "runtime": "python312",
                "entry_point": "hello_world",
                "source": {
                    "storage_source": {
                        "bucket": bucket_name,
                        "object": destination_blob,
                    }
                },
            }

            # Service configuration
            service_config = {
                "available_memory": "256M",
                "timeout_seconds": 60,
                "environment_variables": {
                    "ENVIRONMENT": "production",
                    "DEPLOYED_BY": "gcp-utils",
                },
                "max_instance_count": 10,
                "min_instance_count": 0,  # Scale to zero
            }

            print(f"Deploying function '{function_id}'...")
            print(f"  Runtime: Python 3.12")
            print(f"  Entry point: hello_world")
            print(f"  Memory: 256M")
            print(f"  Source: gs://{bucket_name}/{destination_blob}")

            function = functions.create_function(
                function_id=function_id,
                location=location,
                build_config=build_config,
                service_config=service_config,
                description="Example function deployed using gcp-utils zip utility",
                wait_for_completion=True,
            )

            print(f"[OK] Function deployed successfully!")
            print(f"  Name: {function.name}")
            print(f"  State: {function.state}")
            print(f"  URL: {function.url}")

        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"[INFO] Function already exists, getting details...")
                try:
                    function = functions.get_function(function_id, location)
                    print(f"[OK] Function details retrieved")
                    print(f"  Name: {function.name}")
                    print(f"  State: {function.state}")
                    print(f"  URL: {function.url}")
                except Exception as get_error:
                    print(f"[ERROR] Failed to get function: {get_error}")
                    return
            else:
                print(f"[ERROR] Failed to deploy function: {e}")
                return

        # Step 6: Test the deployed function
        print("\n" + "=" * 80)
        print("Step 6: Testing the deployed function")
        print("=" * 80)

        if function.url:
            print(f"Function URL: {function.url}")
            print("\nYou can test the function with:")
            print(f"  curl {function.url}")
            print(f"  curl '{function.url}?name=Cloud'")
            print("\nOr open in browser:")
            print(f"  {function.url}")
        else:
            print("[WARNING] Function URL not available")

    # Step 7: Cleanup instructions
    print("\n" + "=" * 80)
    print("Step 7: Cleanup")
    print("=" * 80)

    print("\nTo clean up resources:")
    print(f"  1. Delete function: functions.delete_function('{function_id}', '{location}')")
    print(f"  2. Delete bucket: storage.delete_bucket('{bucket_name}', force=True)")

    print("\nOr run this code:")
    print("""
try:
    functions.delete_function('{function_id}', '{location}')
    print('[OK] Deleted function')
except Exception as e:
    print(f'[ERROR] Failed to delete function: {{e}}')

try:
    storage.delete_bucket('{bucket_name}', force=True)
    print('[OK] Deleted bucket')
except Exception as e:
    print(f'[ERROR] Failed to delete bucket: {{e}}')
""".format(function_id=function_id, location=location, bucket_name=bucket_name))

    # Summary
    print("\n" + "=" * 80)
    print("Summary: Complete Deployment Workflow")
    print("=" * 80)

    print("""
This example demonstrated the complete Cloud Functions deployment workflow:

1. ✓ Created sample function source code
2. ✓ Created Cloud Storage bucket for deployments
3. ✓ Zipped source code with smart exclusions (.env, tests, cache files)
4. ✓ Uploaded ZIP to Cloud Storage
5. ✓ Deployed function to Cloud Functions from the uploaded ZIP
6. ✓ Function is now accessible via HTTPS URL

Key Features Demonstrated:

• ZipUtility Class:
  - Automatic exclusion of common unwanted files (*.pyc, .env, __pycache__)
  - Custom exclusion patterns
  - Temporary file handling
  - ZIP inspection (list contents, get size)

• Integrated Workflow:
  - CloudStorageController for uploads
  - CloudFunctionsController for deployment
  - All operations with comprehensive error handling

• Convenience Functions:
  - zip_directory() - Quick function to zip a directory
  - zip_and_upload() - One-step zip and upload to Cloud Storage

Use Cases:

1. CI/CD Pipelines:
   - Zip source code in build step
   - Upload to Cloud Storage
   - Deploy to Cloud Functions
   - Zero downtime deployments

2. Local Development:
   - Test function locally
   - Deploy with one command
   - Iterate quickly

3. Multi-Environment Deployments:
   - Zip once, deploy to multiple environments
   - Version control with bucket prefixes
   - Rollback support

Best Practices:

1. Exclusion Patterns:
   - Always exclude .env files (secrets)
   - Exclude test files and __pycache__
   - Exclude venv/node_modules
   - Keep ZIP small for faster deployments

2. Bucket Organization:
   - Use project-specific buckets
   - Organize by function: functions/{function_id}/source.zip
   - Version artifacts: functions/{function_id}/v{version}.zip

3. Metadata:
   - Add custom metadata to blobs (version, commit hash, etc.)
   - Track deployment history
   - Enable debugging

4. Error Handling:
   - Check if bucket exists before creating
   - Handle "already exists" errors gracefully
   - Clean up temporary files
   - Validate ZIP contents

Example Integration in Your Project:

```python
from gcp_utils.utils import zip_and_upload
from gcp_utils.controllers import CloudFunctionsController

# 1. Zip and upload in one line
result = zip_and_upload(
    source_dir="./my-function",
    bucket_name="my-deployment-bucket",
    destination_blob_name="functions/my-func/source.zip",
)

# 2. Deploy to Cloud Functions
functions = CloudFunctionsController()
function = functions.create_function(
    function_id="my-func",
    location="us-central1",
    build_config={{
        "runtime": "python312",
        "entry_point": "main",
        "source": {{
            "storage_source": {{
                "bucket": result.bucket,
                "object": result.blob_name,
            }}
        }},
    }},
    service_config={{
        "available_memory": "256M",
        "timeout_seconds": 60,
    }},
)

print(f"Deployed! URL: {{function.url}}")
```

Next Steps:

- Try deploying your own function
- Customize exclusion patterns for your needs
- Integrate into your CI/CD pipeline
- Add versioning and rollback support
- Monitor function performance in Cloud Console
""")

    print("=" * 80)
    print("Example completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
