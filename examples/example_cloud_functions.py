"""
Example usage of Cloud Functions controller.

This example demonstrates:
- Creating HTTP-triggered functions
- Creating event-driven functions
- Updating function configuration
- Managing function lifecycle
- Generating upload URLs for source code

Requirements:
- Valid GCP project with Cloud Functions API enabled
- .env file with GCP_PROJECT_ID set
- Cloud Storage bucket for function source code
"""

from gcp_utils.controllers import CloudFunctionsController

# Initialize controller (auto-loads from .env)
functions = CloudFunctionsController()


def example_create_http_function() -> None:
    """
    Create a simple HTTP-triggered Cloud Function.

    This example creates a function that responds to HTTP requests.
    """
    print("\n=== Creating HTTP Function ===")

    # Define build configuration
    build_config = {
        "runtime": "python312",
        "entry_point": "hello_world",
        "source": {
            "storage_source": {
                "bucket": "my-source-bucket",
                "object": "function-source.zip",
            }
        },
    }

    # Define service configuration
    service_config = {
        "available_memory": "256M",
        "timeout_seconds": 60,
        "max_instance_count": 10,
        "environment_variables": {
            "ENV": "production",
            "LOG_LEVEL": "info",
        },
    }

    try:
        function = functions.create_function(
            function_id="hello-http",
            location="us-central1",
            build_config=build_config,
            service_config=service_config,
            description="HTTP endpoint that returns Hello World",
            labels={"environment": "production", "team": "backend"},
            wait_for_completion=True,
        )

        print(f"✓ Function created: {function.name}")
        print(f"  State: {function.state}")
        print(f"  URL: {function.url}")

    except Exception as e:
        print(f"✗ Error creating function: {e}")


def example_create_event_driven_function() -> None:
    """
    Create an event-driven Cloud Function triggered by Cloud Storage.

    This function runs automatically when files are uploaded to a bucket.
    """
    print("\n=== Creating Event-Driven Function ===")

    build_config = {
        "runtime": "python312",
        "entry_point": "process_file",
        "source": {
            "storage_source": {
                "bucket": "my-source-bucket",
                "object": "function-source.zip",
            }
        },
    }

    service_config = {
        "available_memory": "512M",
        "timeout_seconds": 300,
    }

    # Configure event trigger for Cloud Storage
    event_trigger = {
        "trigger_region": "us-central1",
        "event_type": "google.cloud.storage.object.v1.finalized",
        "event_filters": [
            {
                "attribute": "bucket",
                "value": "my-data-bucket",
            }
        ],
        "retry_policy": "RETRY_POLICY_RETRY",
    }

    try:
        function = functions.create_function(
            function_id="process-uploads",
            location="us-central1",
            build_config=build_config,
            service_config=service_config,
            event_trigger=event_trigger,
            description="Process files uploaded to Cloud Storage",
            wait_for_completion=True,
        )

        print(f"✓ Event-driven function created: {function.name}")
        print("  Triggers on: Storage object finalized in my-data-bucket")

    except Exception as e:
        print(f"✗ Error creating function: {e}")


def example_upload_source_code() -> None:
    """
    Generate a signed URL for uploading function source code.

    Use this workflow to upload your function code before deployment.
    """
    print("\n=== Generating Source Upload URL ===")

    try:
        upload_info = functions.generate_upload_url(location="us-central1")

        print("✓ Upload URL generated")
        print(f"  URL: {upload_info.upload_url[:50]}...")
        print(f"  Bucket: {upload_info.storage_source['bucket']}")
        print(f"  Object: {upload_info.storage_source['object']}")

        # You would then upload your ZIP file to this URL using httpx or requests:
        # import httpx
        # with open("function-source.zip", "rb") as f:
        #     response = httpx.put(upload_info.upload_url, content=f.read())

        # After uploading, use the storage_source in your BuildConfig:
        build_config = {
            "runtime": "python312",
            "entry_point": "main",
            "source": {"storage_source": upload_info.storage_source},
        }
        print("\n  Use this in BuildConfig:")
        print(f"  {build_config}")

    except Exception as e:
        print(f"✗ Error generating upload URL: {e}")


def example_update_function() -> None:
    """
    Update an existing Cloud Function's configuration.

    This example shows how to update memory, timeout, and environment variables.
    """
    print("\n=== Updating Function Configuration ===")

    # New service configuration
    service_config = {
        "available_memory": "512M",  # Increase memory
        "timeout_seconds": 120,  # Increase timeout
        "environment_variables": {
            "ENV": "production",
            "LOG_LEVEL": "debug",  # Change log level
            "NEW_FEATURE_FLAG": "enabled",  # Add new variable
        },
    }

    try:
        function = functions.update_function(
            function_id="hello-http",
            location="us-central1",
            service_config=service_config,
            description="Updated HTTP endpoint with more resources",
            update_mask=[
                "service_config.available_memory",
                "service_config.timeout_seconds",
                "service_config.environment_variables",
                "description",
            ],
            wait_for_completion=True,
        )

        print(f"✓ Function updated: {function.name}")
        print(f"  Description: {function.description}")

    except Exception as e:
        print(f"✗ Error updating function: {e}")


def example_list_and_get_functions() -> None:
    """
    List all functions and get details for specific ones.
    """
    print("\n=== Listing Functions ===")

    try:
        # List all functions
        response = functions.list_functions(location="us-central1")

        print(f"Found {len(response.functions)} functions:")
        for func in response.functions:
            print(f"  - {func.name}")
            print(f"    State: {func.state}")
            if func.url:
                print(f"    URL: {func.url}")

        # Get details for a specific function
        if response.functions:
            function_id = response.functions[0].name.split("/")[-1]
            print(f"\n=== Getting Details for {function_id} ===")

            function = functions.get_function(function_id, location="us-central1")
            print(f"  Name: {function.name}")
            print(f"  State: {function.state}")
            print(f"  Labels: {function.labels}")

    except Exception as e:
        print(f"✗ Error: {e}")


def example_get_function_url() -> None:
    """
    Get the HTTP URL for a deployed function.
    """
    print("\n=== Getting Function URL ===")

    try:
        url = functions.get_function_url("hello-http", location="us-central1")

        print(f"✓ Function URL: {url}")
        print("\n  You can now call this function:")
        print(f"  curl {url}")

    except Exception as e:
        print(f"✗ Error getting function URL: {e}")


def example_delete_function() -> None:
    """
    Delete a Cloud Function.

    CAUTION: This permanently deletes the function.
    """
    print("\n=== Deleting Function ===")

    try:
        functions.delete_function(
            function_id="hello-http",
            location="us-central1",
            wait_for_completion=True,
        )

        print("✓ Function deleted successfully")

    except Exception as e:
        print(f"✗ Error deleting function: {e}")


if __name__ == "__main__":
    print("Cloud Functions Controller Example")
    print("=" * 50)

    # Run examples
    # example_create_http_function()
    # example_create_event_driven_function()
    example_upload_source_code()
    # example_update_function()
    example_list_and_get_functions()
    # example_get_function_url()
    # example_delete_function()  # Uncomment to test deletion

    print("\n" + "=" * 50)
    print("Example completed!")
