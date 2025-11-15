"""
Cloud Run controller for deploying and managing containerized applications.

This module provides a high-level interface for Cloud Run operations including
service deployment, management, and traffic splitting.
"""

from typing import Any, Optional

from google.cloud import run_v2
from google.auth.credentials import Credentials
from google.api_core import operation
from google.auth.transport.requests import Request
from google.auth import default
import httpx

from ..config import GCPSettings, get_settings
from ..exceptions import CloudRunError, ResourceNotFoundError, ValidationError
from ..models.cloud_run import CloudRunService, ServiceRevision, TrafficTarget


class CloudRunController:
    """
    Controller for Google Cloud Run operations.

    This controller provides methods for deploying and managing
    Cloud Run services, revisions, and traffic management.

    Example:
        >>> from gcp_utils.controllers import CloudRunController
        >>>
        >>> # Automatically loads from .env file
        >>> run_ctrl = CloudRunController()
        >>>
        >>> # Get service information
        >>> service = run_ctrl.get_service("my-service")
    """

    def __init__(
        self,
        settings: Optional[GCPSettings] = None,
        credentials: Optional[Credentials] = None,
        region: Optional[str] = None,
    ) -> None:
        """
        Initialize the Cloud Run controller.

        Args:
            settings: GCP configuration settings. If not provided, loads from environment/.env file.
            credentials: Optional custom credentials
            region: Cloud Run region (defaults to settings.cloud_run_region)

        Raises:
            CloudRunError: If client initialization fails
        """
        self.settings = settings or get_settings()
        self.region = region or self.settings.cloud_run_region

        try:
            self.client = run_v2.ServicesClient(credentials=credentials)
        except Exception as e:
            raise CloudRunError(
                f"Failed to initialize Cloud Run client: {e}",
                details={"error": str(e)},
            )

    def get_service(self, service_name: str) -> CloudRunService:
        """
        Get information about a Cloud Run service.

        Args:
            service_name: Name of the service

        Returns:
            CloudRunService object with service details

        Raises:
            ResourceNotFoundError: If service doesn't exist
            CloudRunError: If operation fails
        """
        try:
            service_path = self._get_service_path(service_name)
            service = self.client.get_service(name=service_path)

            return self._service_to_model(service)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Service '{service_name}' not found",
                    details={"service": service_name, "region": self.region},
                )
            raise CloudRunError(
                f"Failed to get service '{service_name}': {e}",
                details={"service": service_name, "error": str(e)},
            )

    def list_services(self) -> list[CloudRunService]:
        """
        List all Cloud Run services in the region.

        Returns:
            List of CloudRunService objects

        Raises:
            CloudRunError: If listing fails
        """
        try:
            parent = f"projects/{self.settings.project_id}/locations/{self.region}"
            services = self.client.list_services(parent=parent)

            return [self._service_to_model(service) for service in services]

        except Exception as e:
            raise CloudRunError(
                f"Failed to list services: {e}",
                details={"error": str(e)},
            )

    def create_service(
        self,
        service_name: str,
        image: str,
        port: int = 8080,
        cpu: str = "1000m",
        memory: str = "512Mi",
        max_instances: Optional[int] = None,
        min_instances: int = 0,
        timeout: int = 300,
        env_vars: Optional[dict[str, str]] = None,
        allow_unauthenticated: bool = False,
        labels: Optional[dict[str, str]] = None,
    ) -> CloudRunService:
        """
        Create a new Cloud Run service.

        Args:
            service_name: Name of the service to create
            image: Container image URL (e.g., gcr.io/project/image:tag)
            port: Container port (default: 8080)
            cpu: CPU allocation (e.g., '1000m' for 1 CPU)
            memory: Memory allocation (e.g., '512Mi')
            max_instances: Maximum number of instances
            min_instances: Minimum number of instances (default: 0)
            timeout: Request timeout in seconds (default: 300)
            env_vars: Environment variables
            allow_unauthenticated: Allow unauthenticated access
            labels: Service labels

        Returns:
            CloudRunService object

        Raises:
            ValidationError: If parameters are invalid
            CloudRunError: If creation fails
        """
        if not service_name:
            raise ValidationError("Service name cannot be empty")
        if not image:
            raise ValidationError("Container image cannot be empty")

        try:
            parent = f"projects/{self.settings.project_id}/locations/{self.region}"

            # Build container spec
            container = run_v2.Container(
                image=image,
                ports=[run_v2.ContainerPort(container_port=port)],
                resources=run_v2.ResourceRequirements(
                    limits={"cpu": cpu, "memory": memory}
                ),
            )

            # Add environment variables
            if env_vars:
                container.env = [
                    run_v2.EnvVar(name=k, value=v) for k, v in env_vars.items()
                ]

            # Build template spec
            template = run_v2.RevisionTemplate(
                containers=[container],
                timeout=f"{timeout}s",
                max_instance_request_concurrency=80,
                scaling=run_v2.RevisionScaling(
                    min_instance_count=min_instances,
                    max_instance_count=max_instances,
                ),
            )

            # Build service spec
            service = run_v2.Service(
                template=template,
                labels=labels or {},
            )

            # Create the service
            request = run_v2.CreateServiceRequest(
                parent=parent,
                service=service,
                service_id=service_name,
            )

            operation_result = self.client.create_service(request=request)
            created_service = operation_result.result()

            # Set IAM policy for unauthenticated access if requested
            if allow_unauthenticated:
                self._set_iam_policy_unauthenticated(service_name)

            return self._service_to_model(created_service)

        except ValidationError:
            raise
        except Exception as e:
            raise CloudRunError(
                f"Failed to create service '{service_name}': {e}",
                details={"service": service_name, "error": str(e)},
            )

    def update_service(
        self,
        service_name: str,
        image: Optional[str] = None,
        cpu: Optional[str] = None,
        memory: Optional[str] = None,
        max_instances: Optional[int] = None,
        min_instances: Optional[int] = None,
        timeout: Optional[int] = None,
        env_vars: Optional[dict[str, str]] = None,
        labels: Optional[dict[str, str]] = None,
    ) -> CloudRunService:
        """
        Update an existing Cloud Run service.

        Args:
            service_name: Name of the service to update
            image: New container image URL
            cpu: New CPU allocation
            memory: New memory allocation
            max_instances: New maximum instance count
            min_instances: New minimum instance count
            timeout: New request timeout in seconds
            env_vars: New environment variables (replaces existing)
            labels: New labels (merges with existing)

        Returns:
            Updated CloudRunService object

        Raises:
            ResourceNotFoundError: If service doesn't exist
            CloudRunError: If update fails
        """
        try:
            service_path = self._get_service_path(service_name)
            service = self.client.get_service(name=service_path)

            # Update container configuration
            if image:
                service.template.containers[0].image = image

            if cpu or memory:
                limits = {}
                if cpu:
                    limits["cpu"] = cpu
                if memory:
                    limits["memory"] = memory
                service.template.containers[0].resources = (
                    run_v2.ResourceRequirements(limits=limits)
                )

            if env_vars is not None:
                service.template.containers[0].env = [
                    run_v2.EnvVar(name=k, value=v) for k, v in env_vars.items()
                ]

            if timeout is not None:
                service.template.timeout = f"{timeout}s"

            # Update scaling configuration
            if min_instances is not None or max_instances is not None:
                scaling = run_v2.RevisionScaling()
                if min_instances is not None:
                    scaling.min_instance_count = min_instances
                if max_instances is not None:
                    scaling.max_instance_count = max_instances
                service.template.scaling = scaling

            # Update labels
            if labels:
                service.labels.update(labels)

            # Update the service
            request = run_v2.UpdateServiceRequest(service=service)
            operation_result = self.client.update_service(request=request)
            updated_service = operation_result.result()

            return self._service_to_model(updated_service)

        except ResourceNotFoundError:
            raise
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Service '{service_name}' not found",
                    details={"service": service_name},
                )
            raise CloudRunError(
                f"Failed to update service '{service_name}': {e}",
                details={"service": service_name, "error": str(e)},
            )

    def delete_service(self, service_name: str) -> None:
        """
        Delete a Cloud Run service.

        Args:
            service_name: Name of the service to delete

        Raises:
            CloudRunError: If deletion fails
        """
        try:
            service_path = self._get_service_path(service_name)

            request = run_v2.DeleteServiceRequest(name=service_path)
            operation_result = self.client.delete_service(request=request)
            operation_result.result()

        except Exception as e:
            raise CloudRunError(
                f"Failed to delete service '{service_name}': {e}",
                details={"service": service_name, "error": str(e)},
            )

    def update_traffic(
        self,
        service_name: str,
        traffic_targets: list[TrafficTarget],
    ) -> CloudRunService:
        """
        Update traffic split for a service.

        Args:
            service_name: Name of the service
            traffic_targets: List of TrafficTarget objects defining traffic split

        Returns:
            Updated CloudRunService object

        Raises:
            ValidationError: If traffic targets are invalid
            CloudRunError: If update fails
        """
        # Validate traffic percentages sum to 100
        total_percent = sum(target.percent for target in traffic_targets)
        if total_percent != 100:
            raise ValidationError(
                f"Traffic percentages must sum to 100, got {total_percent}"
            )

        try:
            service_path = self._get_service_path(service_name)
            service = self.client.get_service(name=service_path)

            # Build traffic targets
            service.traffic = []
            for target in traffic_targets:
                traffic = run_v2.TrafficTarget(
                    percent=target.percent,
                )
                if target.revision_name:
                    traffic.revision = target.revision_name
                elif target.latest_revision:
                    traffic.type_ = run_v2.TrafficTargetAllocationType.TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST
                if target.tag:
                    traffic.tag = target.tag

                service.traffic.append(traffic)

            # Update the service
            request = run_v2.UpdateServiceRequest(service=service)
            operation_result = self.client.update_service(request=request)
            updated_service = operation_result.result()

            return self._service_to_model(updated_service)

        except ValidationError:
            raise
        except Exception as e:
            raise CloudRunError(
                f"Failed to update traffic for service '{service_name}': {e}",
                details={"service": service_name, "error": str(e)},
            )

    def get_service_url(self, service_name: str) -> str:
        """
        Get the URL of a Cloud Run service.

        Args:
            service_name: Name of the service

        Returns:
            Service URL

        Raises:
            ResourceNotFoundError: If service doesn't exist
            CloudRunError: If operation fails
        """
        service = self.get_service(service_name)
        return service.url

    def invoke_service(
        self,
        service_name: str,
        path: str = "/",
        method: str = "GET",
        data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: int = 60,
    ) -> dict[str, Any]:
        """
        Invoke a Cloud Run service with authentication.

        This method makes an authenticated HTTP request to a Cloud Run service
        using the service account credentials or application default credentials.

        Args:
            service_name: Name of the Cloud Run service to invoke
            path: URL path to request (default: "/")
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            data: Optional JSON data to send in request body
            headers: Optional additional headers to include
            timeout: Request timeout in seconds (default: 60)

        Returns:
            Dictionary containing:
                - status_code: HTTP status code
                - headers: Response headers as dict
                - content: Response body as string
                - json: Response body as dict (if JSON response)

        Raises:
            ResourceNotFoundError: If service doesn't exist
            CloudRunError: If invocation fails

        Example:
            >>> run_ctrl = CloudRunController()
            >>>
            >>> # GET request
            >>> response = run_ctrl.invoke_service("my-service", "/api/users")
            >>> print(response["status_code"])
            >>> print(response["json"])
            >>>
            >>> # POST request
            >>> response = run_ctrl.invoke_service(
            ...     "my-service",
            ...     "/api/users",
            ...     method="POST",
            ...     data={"name": "John", "email": "john@example.com"}
            ... )
        """
        try:
            # Get service URL
            service_url = self.get_service_url(service_name)
            full_url = f"{service_url.rstrip('/')}/{path.lstrip('/')}"

            # Get credentials and generate auth token
            credentials, _ = default()
            if not credentials.valid:
                credentials.refresh(Request())

            # Prepare headers with authentication
            auth_headers = {
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json",
            }
            if headers:
                auth_headers.update(headers)

            # Make the request
            with httpx.Client(timeout=timeout) as client:
                if method.upper() == "GET":
                    response = client.get(full_url, headers=auth_headers)
                elif method.upper() == "POST":
                    response = client.post(full_url, headers=auth_headers, json=data)
                elif method.upper() == "PUT":
                    response = client.put(full_url, headers=auth_headers, json=data)
                elif method.upper() == "DELETE":
                    response = client.delete(full_url, headers=auth_headers)
                elif method.upper() == "PATCH":
                    response = client.patch(full_url, headers=auth_headers, json=data)
                else:
                    raise ValidationError(f"Unsupported HTTP method: {method}")

            # Build response dictionary
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text,
            }

            # Try to parse JSON response
            try:
                result["json"] = response.json()
            except Exception:
                result["json"] = None

            return result

        except ResourceNotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            raise CloudRunError(
                f"Failed to invoke service '{service_name}': {e}",
                details={
                    "service": service_name,
                    "path": path,
                    "method": method,
                    "error": str(e),
                },
            ) from e

    def _get_service_path(self, service_name: str) -> str:
        """Get the full resource path for a service."""
        return f"projects/{self.settings.project_id}/locations/{self.region}/services/{service_name}"

    def _set_iam_policy_unauthenticated(self, service_name: str) -> None:
        """Set IAM policy to allow unauthenticated access."""
        try:
            from google.cloud.run_v2 import ServicesClient
            from google.iam.v1 import iam_policy_pb2, policy_pb2

            service_path = self._get_service_path(service_name)

            policy_request = iam_policy_pb2.GetIamPolicyRequest(resource=service_path)
            policy = self.client.get_iam_policy(request=policy_request)

            # Add allUsers as invoker
            binding = policy_pb2.Binding(
                role="roles/run.invoker",
                members=["allUsers"],
            )

            # Add or update binding
            policy.bindings.append(binding)

            set_policy_request = iam_policy_pb2.SetIamPolicyRequest(
                resource=service_path,
                policy=policy,
            )
            self.client.set_iam_policy(request=set_policy_request)

        except Exception as e:
            # Log but don't fail the deployment
            if self.settings.enable_request_logging:
                print(f"Warning: Failed to set IAM policy: {e}")

    def _service_to_model(self, service: Any) -> CloudRunService:
        """Convert Cloud Run Service to CloudRunService model with native object binding."""
        # Extract basic info
        name = service.name.split("/")[-1]
        url = service.uri if hasattr(service, "uri") else ""

        # Extract container image
        image = ""
        if (
            hasattr(service, "template")
            and service.template.containers
        ):
            image = service.template.containers[0].image

        # Extract traffic configuration
        traffic = []
        if hasattr(service, "traffic"):
            for t in service.traffic:
                traffic.append(
                    TrafficTarget(
                        revision_name=t.revision if hasattr(t, "revision") else None,
                        percent=t.percent if hasattr(t, "percent") else 0,
                        tag=t.tag if hasattr(t, "tag") else None,
                        latest_revision=(
                            t.type_
                            == run_v2.TrafficTargetAllocationType.TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST
                            if hasattr(t, "type_")
                            else False
                        ),
                    )
                )

        # Extract latest revision
        latest_revision = None
        if hasattr(service, "latest_ready_revision"):
            latest_revision = service.latest_ready_revision

        model = CloudRunService(
            name=name,
            region=self.region,
            image=image,
            url=url,
            created=service.create_time if hasattr(service, "create_time") else None,
            updated=service.update_time if hasattr(service, "update_time") else None,
            latest_revision=latest_revision,
            traffic=traffic,
            labels=dict(service.labels) if hasattr(service, "labels") else {},
        )
        # Bind the native object
        model._service_object = service
        return model
