"""
Google Cloud Functions controller for managing serverless functions.

This module provides a type-safe controller for deploying and managing
Cloud Functions (2nd gen) including HTTP functions and event-driven functions.
"""

from google.api_core.exceptions import GoogleAPIError
from google.auth.credentials import Credentials
from google.cloud import functions_v2
from google.cloud.functions_v2.types import (
    CreateFunctionRequest,
    DeleteFunctionRequest,
    Function,
    GenerateUploadUrlRequest,
    GetFunctionRequest,
    ListFunctionsRequest,
    UpdateFunctionRequest,
)

from ..config import GCPSettings, get_settings
from ..exceptions import CloudFunctionsError, ResourceNotFoundError
from ..models.cloud_functions import (
    CloudFunction,
    FunctionListResponse,
    GenerateUploadUrlResponse,
)


class CloudFunctionsController:
    """
    Controller for managing Google Cloud Functions.

    Provides methods for deploying, updating, deleting, and managing Cloud Functions.
    Supports both HTTP-triggered and event-driven functions with comprehensive
    configuration options.

    Example:
        ```python
        from gcp_utils.controllers import CloudFunctionsController
        from gcp_utils.models.cloud_functions import (
            BuildConfig,
            Runtime,
            ServiceConfig,
        )

        # Controller auto-loads settings from .env file
        functions = CloudFunctionsController()

        # Deploy a simple HTTP function
        build_config = BuildConfig(
            runtime=Runtime.PYTHON_312,
            entry_point="hello_world",
            source_archive_url="gs://my-bucket/function-source.zip",
        )

        service_config = ServiceConfig(
            available_memory="256M",
            timeout_seconds=60,
            environment_variables={"ENV": "production"},
        )

        function = functions.create_function(
            function_id="my-function",
            location="us-central1",
            build_config=build_config,
            service_config=service_config,
        )
        ```
    """

    def __init__(
        self,
        settings: GCPSettings | None = None,
        credentials: Credentials | None = None,
    ) -> None:
        """
        Initialize the Cloud Functions controller.

        Args:
            settings: GCP configuration. If not provided, loads from environment/.env file.
            credentials: Optional custom credentials.
        """
        self._settings = settings or get_settings()
        self._credentials = credentials
        self._client: functions_v2.FunctionServiceClient | None = None

    def _get_client(self) -> functions_v2.FunctionServiceClient:
        """Lazy initialization of the Cloud Functions client."""
        if self._client is None:
            self._client = functions_v2.FunctionServiceClient(
                credentials=self._credentials
            )
        return self._client

    def _function_to_model(self, function: Function) -> CloudFunction:
        """Convert a Function proto to CloudFunction model."""
        return CloudFunction(
            name=function.name,
            description=function.description or None,
            state=function.state.name if function.state else None,
            url=function.service_config.uri if function.service_config else None,
            update_time=function.update_time,
            labels=dict(function.labels) if function.labels else None,
            kms_key_name=function.kms_key_name or None,
        )

    def create_function(
        self,
        function_id: str,
        location: str | None = None,
        build_config: dict | None = None,
        service_config: dict | None = None,
        event_trigger: dict | None = None,
        description: str | None = None,
        labels: dict[str, str] | None = None,
        wait_for_completion: bool = True,
    ) -> CloudFunction:
        """
        Create a new Cloud Function.

        Args:
            function_id: Function ID (name)
            location: GCP region (defaults to settings.cloud_functions_region)
            build_config: Build configuration dictionary
            service_config: Service configuration dictionary
            event_trigger: Event trigger configuration dictionary (optional, for event-driven functions)
            description: Function description
            labels: Resource labels
            wait_for_completion: Wait for the deployment to complete

        Returns:
            CloudFunction model containing the created function details

        Raises:
            CloudFunctionsError: If function creation fails

        Example:
            ```python
            from gcp_utils.models.cloud_functions import BuildConfig, Runtime

            build_config = {
                "runtime": "python312",
                "entry_point": "main",
                "source": {
                    "storage_source": {
                        "bucket": "my-bucket",
                        "object": "function.zip",
                    }
                },
            }

            service_config = {
                "available_memory": "256M",
                "timeout_seconds": 60,
                "environment_variables": {"KEY": "value"},
            }

            function = functions.create_function(
                function_id="my-function",
                build_config=build_config,
                service_config=service_config,
            )
            ```
        """
        try:
            client = self._get_client()
            region = location or self._settings.cloud_functions_region
            parent = f"projects/{self._settings.project_id}/locations/{region}"
            function_name = f"{parent}/functions/{function_id}"

            function = Function(
                name=function_name,
                description=description or "",
                labels=labels or {},
            )

            if build_config:
                function.build_config = build_config  # type: ignore[assignment]

            if service_config:
                function.service_config = service_config  # type: ignore[assignment]

            if event_trigger:
                function.event_trigger = event_trigger  # type: ignore[assignment]

            request = CreateFunctionRequest(
                parent=parent,
                function=function,
                function_id=function_id,
            )

            operation = client.create_function(request=request)

            if wait_for_completion:
                result = operation.result(timeout=self._settings.operation_timeout)
                return self._function_to_model(result)

            return CloudFunction(
                name=function_name,
                description=description,
                labels=labels,
            )

        except GoogleAPIError as e:
            raise CloudFunctionsError(
                message=f"Failed to create function '{function_id}': {str(e)}",
                details={
                    "function_id": function_id,
                    "location": location,
                    "error": str(e),
                },
            ) from e

    def get_function(
        self, function_id: str, location: str | None = None
    ) -> CloudFunction:
        """
        Get details about a Cloud Function.

        Args:
            function_id: Function ID
            location: GCP region (defaults to settings.cloud_functions_region)

        Returns:
            CloudFunction model with function details

        Raises:
            ResourceNotFoundError: If function doesn't exist
            CloudFunctionsError: If retrieval fails

        Example:
            ```python
            function = functions.get_function("my-function")
            print(f"State: {function.state}")
            print(f"URL: {function.url}")
            ```
        """
        try:
            client = self._get_client()
            region = location or self._settings.cloud_functions_region
            name = f"projects/{self._settings.project_id}/locations/{region}/functions/{function_id}"

            request = GetFunctionRequest(name=name)
            function = client.get_function(request=request)

            return self._function_to_model(function)

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Function '{function_id}' not found",
                    details={"function_id": function_id, "location": location},
                ) from e

            raise CloudFunctionsError(
                message=f"Failed to get function '{function_id}': {str(e)}",
                details={"function_id": function_id, "error": str(e)},
            ) from e

    def list_functions(
        self,
        location: str | None = None,
        page_size: int = 100,
        page_token: str | None = None,
    ) -> FunctionListResponse:
        """
        List Cloud Functions in a location.

        Args:
            location: GCP region (defaults to settings.cloud_functions_region)
            page_size: Maximum number of functions to return
            page_token: Token from previous list call for pagination

        Returns:
            FunctionListResponse with list of functions and pagination token

        Raises:
            CloudFunctionsError: If listing fails

        Example:
            ```python
            response = functions.list_functions()
            for func in response.functions:
                print(f"{func.name}: {func.state}")
            ```
        """
        try:
            client = self._get_client()
            region = location or self._settings.cloud_functions_region
            parent = f"projects/{self._settings.project_id}/locations/{region}"

            request = ListFunctionsRequest(
                parent=parent,
                page_size=page_size,
                page_token=page_token or "",
            )

            response = client.list_functions(request=request)

            functions = [self._function_to_model(func) for func in response.functions]

            return FunctionListResponse(
                functions=functions,
                next_page_token=response.next_page_token or None,
                unreachable=list(response.unreachable) if response.unreachable else [],
            )

        except GoogleAPIError as e:
            raise CloudFunctionsError(
                message=f"Failed to list functions: {str(e)}",
                details={"location": location, "error": str(e)},
            ) from e

    def update_function(
        self,
        function_id: str,
        location: str | None = None,
        build_config: dict | None = None,
        service_config: dict | None = None,
        event_trigger: dict | None = None,
        description: str | None = None,
        labels: dict[str, str] | None = None,
        update_mask: list[str] | None = None,
        wait_for_completion: bool = True,
    ) -> CloudFunction:
        """
        Update an existing Cloud Function.

        Args:
            function_id: Function ID
            location: GCP region (defaults to settings.cloud_functions_region)
            build_config: Updated build configuration
            service_config: Updated service configuration
            event_trigger: Updated event trigger configuration
            description: Updated description
            labels: Updated labels
            update_mask: Fields to update (if None, updates all provided fields)
            wait_for_completion: Wait for the update to complete

        Returns:
            CloudFunction model with updated function details

        Raises:
            ResourceNotFoundError: If function doesn't exist
            CloudFunctionsError: If update fails

        Example:
            ```python
            # Update memory and timeout
            service_config = {
                "available_memory": "512M",
                "timeout_seconds": 120,
            }

            function = functions.update_function(
                function_id="my-function",
                service_config=service_config,
                update_mask=["service_config.available_memory", "service_config.timeout_seconds"],
            )
            ```
        """
        try:
            client = self._get_client()
            region = location or self._settings.cloud_functions_region
            name = f"projects/{self._settings.project_id}/locations/{region}/functions/{function_id}"

            function = Function(name=name)

            if description is not None:
                function.description = description

            if labels is not None:
                function.labels = labels

            if build_config:
                function.build_config = build_config  # type: ignore[assignment]

            if service_config:
                function.service_config = service_config  # type: ignore[assignment]

            if event_trigger:
                function.event_trigger = event_trigger  # type: ignore[assignment]

            request = UpdateFunctionRequest(function=function)

            if update_mask:
                from google.protobuf import field_mask_pb2

                request.update_mask = field_mask_pb2.FieldMask(paths=update_mask)

            operation = client.update_function(request=request)

            if wait_for_completion:
                result = operation.result(timeout=self._settings.operation_timeout)
                return self._function_to_model(result)

            return CloudFunction(
                name=name,
                description=description,
                labels=labels,
            )

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Function '{function_id}' not found",
                    details={"function_id": function_id, "location": location},
                ) from e

            raise CloudFunctionsError(
                message=f"Failed to update function '{function_id}': {str(e)}",
                details={"function_id": function_id, "error": str(e)},
            ) from e

    def delete_function(
        self,
        function_id: str,
        location: str | None = None,
        wait_for_completion: bool = True,
    ) -> None:
        """
        Delete a Cloud Function.

        Args:
            function_id: Function ID
            location: GCP region (defaults to settings.cloud_functions_region)
            wait_for_completion: Wait for deletion to complete

        Raises:
            ResourceNotFoundError: If function doesn't exist
            CloudFunctionsError: If deletion fails

        Example:
            ```python
            functions.delete_function("my-function")
            ```
        """
        try:
            client = self._get_client()
            region = location or self._settings.cloud_functions_region
            name = f"projects/{self._settings.project_id}/locations/{region}/functions/{function_id}"

            request = DeleteFunctionRequest(name=name)
            operation = client.delete_function(request=request)

            if wait_for_completion:
                operation.result(timeout=self._settings.operation_timeout)

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Function '{function_id}' not found",
                    details={"function_id": function_id, "location": location},
                ) from e

            raise CloudFunctionsError(
                message=f"Failed to delete function '{function_id}': {str(e)}",
                details={"function_id": function_id, "error": str(e)},
            ) from e

    def generate_upload_url(
        self, location: str | None = None
    ) -> GenerateUploadUrlResponse:
        """
        Generate a signed URL for uploading function source code.

        This URL can be used to upload a ZIP archive containing the function source code.
        After uploading, use the returned storage_source in the BuildConfig.

        Args:
            location: GCP region (defaults to settings.cloud_functions_region)

        Returns:
            GenerateUploadUrlResponse with upload URL and storage source details

        Raises:
            CloudFunctionsError: If URL generation fails

        Example:
            ```python
            # Generate upload URL
            upload_info = functions.generate_upload_url()

            # Upload your source code ZIP to upload_info.upload_url
            # Then use upload_info.storage_source in your BuildConfig

            build_config = {
                "runtime": "python312",
                "entry_point": "main",
                "source": {"storage_source": upload_info.storage_source},
            }
            ```
        """
        try:
            client = self._get_client()
            region = location or self._settings.cloud_functions_region
            parent = f"projects/{self._settings.project_id}/locations/{region}"

            request = GenerateUploadUrlRequest(parent=parent)
            response = client.generate_upload_url(request=request)

            return GenerateUploadUrlResponse(
                upload_url=response.upload_url,
                storage_source={
                    "bucket": response.storage_source.bucket,
                    "object": response.storage_source.object_,
                    "generation": response.storage_source.generation,
                },
            )

        except GoogleAPIError as e:
            raise CloudFunctionsError(
                message=f"Failed to generate upload URL: {str(e)}",
                details={"location": location, "error": str(e)},
            ) from e

    def get_function_url(self, function_id: str, location: str | None = None) -> str:
        """
        Get the HTTP URL for a Cloud Function.

        Args:
            function_id: Function ID
            location: GCP region (defaults to settings.cloud_functions_region)

        Returns:
            HTTP URL string

        Raises:
            ResourceNotFoundError: If function doesn't exist
            CloudFunctionsError: If retrieval fails

        Example:
            ```python
            url = functions.get_function_url("my-function")
            print(f"Function URL: {url}")
            ```
        """
        function = self.get_function(function_id, location)

        if not function.url:
            raise CloudFunctionsError(
                message=f"Function '{function_id}' does not have an HTTP URL",
                details={
                    "function_id": function_id,
                    "state": function.state,
                },
            )

        return function.url
