"""
Cloud Run controller for deploying and managing containerized applications.

This module provides a high-level interface for Cloud Run operations including
service deployment, management, traffic splitting, and job execution.
"""

from typing import Any

import httpx
from google.auth import default
from google.auth.credentials import Credentials
from google.auth.transport.requests import Request
from google.cloud import run_v2
from google.cloud.run_v2.services.jobs import JobsClient

from ..config import GCPSettings, get_settings
from ..exceptions import CloudRunError, ResourceNotFoundError, ValidationError
from ..models.cloud_run import (
    CloudRunJob,
    CloudRunService,
    ExecutionEnvironment,
    ExecutionStatus,
    JobExecution,
    LaunchStage,
    TrafficTarget,
)


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
        settings: GCPSettings | None = None,
        credentials: Credentials | None = None,
        region: str | None = None,
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
            self.jobs_client = JobsClient(credentials=credentials)
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
        max_instances: int | None = None,
        min_instances: int = 0,
        timeout: int = 300,
        env_vars: dict[str, str] | None = None,
        allow_unauthenticated: bool = False,
        labels: dict[str, str] | None = None,
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
        image: str | None = None,
        cpu: str | None = None,
        memory: str | None = None,
        max_instances: int | None = None,
        min_instances: int | None = None,
        timeout: int | None = None,
        env_vars: dict[str, str] | None = None,
        labels: dict[str, str] | None = None,
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
                service.template.containers[0].resources = run_v2.ResourceRequirements(
                    limits=limits
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
                    traffic.type_ = run_v2.TrafficTargetAllocationType.TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST  # type: ignore[assignment]
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
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
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
        if hasattr(service, "template") and service.template.containers:
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

    # Cloud Run Jobs methods

    def create_job(
        self,
        job_name: str,
        image: str,
        task_count: int = 1,
        parallelism: int = 1,
        max_retries: int = 3,
        timeout: int | None = None,
        cpu: str = "1000m",
        memory: str = "512Mi",
        env_vars: dict[str, str] | None = None,
        service_account: str | None = None,
        labels: dict[str, str] | None = None,
        execution_environment: ExecutionEnvironment = ExecutionEnvironment.EXECUTION_ENVIRONMENT_GEN2,
    ) -> CloudRunJob:
        """
        Create a new Cloud Run job.

        Args:
            job_name: Name of the job to create
            image: Container image URL (e.g., gcr.io/project/image:tag)
            task_count: Number of tasks to create per execution (default: 1)
            parallelism: Maximum number of tasks to run in parallel (default: 1)
            max_retries: Maximum number of retries per task (default: 3)
            timeout: Task timeout in seconds (default: 600)
            cpu: CPU allocation per task (e.g., '1000m' for 1 CPU)
            memory: Memory allocation per task (e.g., '512Mi')
            env_vars: Environment variables for tasks
            service_account: Service account email for tasks
            labels: Job labels
            execution_environment: Execution environment (GEN1 or GEN2)

        Returns:
            CloudRunJob object

        Raises:
            ValidationError: If parameters are invalid
            CloudRunError: If creation fails

        Example:
            >>> job = run_ctrl.create_job(
            ...     job_name="batch-processor",
            ...     image="gcr.io/my-project/batch-job:latest",
            ...     task_count=10,
            ...     parallelism=3,
            ...     env_vars={"BATCH_SIZE": "100"}
            ... )
        """
        if not job_name:
            raise ValidationError("Job name cannot be empty")
        if not image:
            raise ValidationError("Container image cannot be empty")

        try:
            parent = f"projects/{self.settings.project_id}/locations/{self.region}"

            # Build container spec
            container = run_v2.Container(
                image=image,
                resources=run_v2.ResourceRequirements(
                    limits={"cpu": cpu, "memory": memory}
                ),
            )

            # Add environment variables
            if env_vars:
                container.env = [
                    run_v2.EnvVar(name=k, value=v) for k, v in env_vars.items()
                ]

            # Build task template
            task_template = run_v2.TaskTemplate(
                containers=[container],
                max_retries=max_retries,
            )

            if timeout:
                task_template.timeout = f"{timeout}s"

            if service_account:
                task_template.service_account = service_account

            task_template.execution_environment = execution_environment.value  # type: ignore[assignment]

            # Build job template
            template = run_v2.ExecutionTemplate(
                template=task_template,
                task_count=task_count,
                parallelism=parallelism,
            )

            # Build job spec
            job = run_v2.Job(
                template=template,
                labels=labels or {},
                launch_stage=LaunchStage.GA.value,
            )

            # Create the job
            request = run_v2.CreateJobRequest(
                parent=parent,
                job=job,
                job_id=job_name,
            )

            operation_result = self.jobs_client.create_job(request=request)
            created_job = operation_result.result()

            return self._job_to_model(created_job)

        except ValidationError:
            raise
        except Exception as e:
            raise CloudRunError(
                f"Failed to create job '{job_name}': {e}",
                details={"job": job_name, "error": str(e)},
            ) from e

    def get_job(self, job_name: str) -> CloudRunJob:
        """
        Get information about a Cloud Run job.

        Args:
            job_name: Name of the job

        Returns:
            CloudRunJob object with job details

        Raises:
            ResourceNotFoundError: If job doesn't exist
            CloudRunError: If operation fails

        Example:
            >>> job = run_ctrl.get_job("my-batch-job")
            >>> print(f"Parallelism: {job.parallelism}")
        """
        try:
            job_path = self._get_job_path(job_name)
            job = self.jobs_client.get_job(name=job_path)

            return self._job_to_model(job)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Job '{job_name}' not found",
                    details={"job": job_name, "region": self.region},
                ) from e
            raise CloudRunError(
                f"Failed to get job '{job_name}': {e}",
                details={"job": job_name, "error": str(e)},
            ) from e

    def list_jobs(self) -> list[CloudRunJob]:
        """
        List all Cloud Run jobs in the region.

        Returns:
            List of CloudRunJob objects

        Raises:
            CloudRunError: If listing fails

        Example:
            >>> jobs = run_ctrl.list_jobs()
            >>> for job in jobs:
            ...     print(f"{job.name}: {job.task_count} tasks")
        """
        try:
            parent = f"projects/{self.settings.project_id}/locations/{self.region}"
            jobs = self.jobs_client.list_jobs(parent=parent)

            return [self._job_to_model(job) for job in jobs]

        except Exception as e:
            raise CloudRunError(
                f"Failed to list jobs: {e}",
                details={"error": str(e)},
            ) from e

    def update_job(
        self,
        job_name: str,
        image: str | None = None,
        task_count: int | None = None,
        parallelism: int | None = None,
        max_retries: int | None = None,
        timeout: int | None = None,
        cpu: str | None = None,
        memory: str | None = None,
        env_vars: dict[str, str] | None = None,
        labels: dict[str, str] | None = None,
    ) -> CloudRunJob:
        """
        Update an existing Cloud Run job.

        Args:
            job_name: Name of the job to update
            image: New container image URL
            task_count: New task count per execution
            parallelism: New parallelism setting
            max_retries: New max retries setting
            timeout: New timeout in seconds
            cpu: New CPU allocation
            memory: New memory allocation
            env_vars: New environment variables (replaces existing)
            labels: New labels (merges with existing)

        Returns:
            Updated CloudRunJob object

        Raises:
            ResourceNotFoundError: If job doesn't exist
            CloudRunError: If update fails

        Example:
            >>> job = run_ctrl.update_job(
            ...     "my-job",
            ...     parallelism=5,
            ...     env_vars={"BATCH_SIZE": "200"}
            ... )
        """
        try:
            job_path = self._get_job_path(job_name)
            job = self.jobs_client.get_job(name=job_path)

            # Update template configuration
            if task_count is not None:
                job.template.task_count = task_count

            if parallelism is not None:
                job.template.parallelism = parallelism

            # Update task template
            if image:
                job.template.template.containers[0].image = image

            if max_retries is not None:
                job.template.template.max_retries = max_retries

            if timeout is not None:
                job.template.template.timeout = f"{timeout}s"

            if cpu or memory:
                limits = {}
                if cpu:
                    limits["cpu"] = cpu
                if memory:
                    limits["memory"] = memory
                job.template.template.containers[0].resources = (
                    run_v2.ResourceRequirements(limits=limits)
                )

            if env_vars is not None:
                job.template.template.containers[0].env = [
                    run_v2.EnvVar(name=k, value=v) for k, v in env_vars.items()
                ]

            # Update labels
            if labels:
                job.labels.update(labels)

            # Update the job
            request = run_v2.UpdateJobRequest(job=job)
            operation_result = self.jobs_client.update_job(request=request)
            updated_job = operation_result.result()

            return self._job_to_model(updated_job)

        except ResourceNotFoundError:
            raise
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Job '{job_name}' not found",
                    details={"job": job_name},
                ) from e
            raise CloudRunError(
                f"Failed to update job '{job_name}': {e}",
                details={"job": job_name, "error": str(e)},
            ) from e

    def delete_job(self, job_name: str) -> None:
        """
        Delete a Cloud Run job.

        Args:
            job_name: Name of the job to delete

        Raises:
            CloudRunError: If deletion fails

        Example:
            >>> run_ctrl.delete_job("old-batch-job")
        """
        try:
            job_path = self._get_job_path(job_name)

            request = run_v2.DeleteJobRequest(name=job_path)
            operation_result = self.jobs_client.delete_job(request=request)
            operation_result.result()

        except Exception as e:
            raise CloudRunError(
                f"Failed to delete job '{job_name}': {e}",
                details={"job": job_name, "error": str(e)},
            ) from e

    def run_job(self, job_name: str) -> JobExecution:
        """
        Execute a Cloud Run job immediately.

        This method triggers a new execution of the specified job.
        The execution runs asynchronously - use get_execution() to monitor progress.

        Args:
            job_name: Name of the job to execute

        Returns:
            JobExecution object with execution details

        Raises:
            ResourceNotFoundError: If job doesn't exist
            CloudRunError: If execution fails to start

        Example:
            >>> execution = run_ctrl.run_job("my-batch-job")
            >>> print(f"Started execution: {execution.execution_id}")
            >>>
            >>> # Monitor execution status
            >>> import time
            >>> while execution.status == ExecutionStatus.RUNNING:
            ...     time.sleep(5)
            ...     execution = run_ctrl.get_execution(job_name, execution.execution_id)
            >>> print(f"Final status: {execution.status}")
        """
        try:
            job_path = self._get_job_path(job_name)

            request = run_v2.RunJobRequest(name=job_path)
            operation_result = self.jobs_client.run_job(request=request)
            execution = operation_result.result()

            return self._execution_to_model(execution, job_name)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Job '{job_name}' not found",
                    details={"job": job_name},
                ) from e
            raise CloudRunError(
                f"Failed to run job '{job_name}': {e}",
                details={"job": job_name, "error": str(e)},
            ) from e

    def get_execution(self, job_name: str, execution_id: str) -> JobExecution:
        """
        Get information about a job execution.

        Args:
            job_name: Name of the job
            execution_id: Execution ID (short ID or full resource path)

        Returns:
            JobExecution object with execution details

        Raises:
            ResourceNotFoundError: If execution doesn't exist
            CloudRunError: If operation fails

        Example:
            >>> execution = run_ctrl.get_execution("my-job", "my-execution-abc123")
            >>> print(f"Status: {execution.status}")
            >>> print(f"Succeeded tasks: {execution.succeeded_count}")
        """
        try:
            # If execution_id is not a full path, construct it
            if not execution_id.startswith("projects/"):
                execution_path = self._get_execution_path(job_name, execution_id)
            else:
                execution_path = execution_id

            execution = self.jobs_client.get_execution(name=execution_path)  # type: ignore[attr-defined]

            return self._execution_to_model(execution, job_name)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Execution '{execution_id}' not found for job '{job_name}'",
                    details={"job": job_name, "execution": execution_id},
                ) from e
            raise CloudRunError(
                f"Failed to get execution '{execution_id}': {e}",
                details={"job": job_name, "execution": execution_id, "error": str(e)},
            ) from e

    def list_executions(self, job_name: str) -> list[JobExecution]:
        """
        List all executions for a job.

        Args:
            job_name: Name of the job

        Returns:
            List of JobExecution objects, ordered by creation time (newest first)

        Raises:
            CloudRunError: If listing fails

        Example:
            >>> executions = run_ctrl.list_executions("my-job")
            >>> for exec in executions:
            ...     print(f"{exec.execution_id}: {exec.status} ({exec.succeeded_count}/{exec.task_count} tasks)")
        """
        try:
            job_path = self._get_job_path(job_name)
            executions = self.jobs_client.list_executions(parent=job_path)  # type: ignore[attr-defined]

            return [self._execution_to_model(exec, job_name) for exec in executions]

        except Exception as e:
            raise CloudRunError(
                f"Failed to list executions for job '{job_name}': {e}",
                details={"job": job_name, "error": str(e)},
            ) from e

    def cancel_execution(self, job_name: str, execution_id: str) -> JobExecution:
        """
        Cancel a running job execution.

        Args:
            job_name: Name of the job
            execution_id: Execution ID to cancel

        Returns:
            Updated JobExecution object

        Raises:
            ResourceNotFoundError: If execution doesn't exist
            CloudRunError: If cancellation fails

        Example:
            >>> execution = run_ctrl.cancel_execution("my-job", "execution-abc123")
            >>> print(f"Cancelled: {execution.status}")
        """
        try:
            # If execution_id is not a full path, construct it
            if not execution_id.startswith("projects/"):
                execution_path = self._get_execution_path(job_name, execution_id)
            else:
                execution_path = execution_id

            request = run_v2.CancelExecutionRequest(name=execution_path)
            operation_result = self.jobs_client.cancel_execution(request=request)  # type: ignore[attr-defined]
            execution = operation_result.result()

            return self._execution_to_model(execution, job_name)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Execution '{execution_id}' not found for job '{job_name}'",
                    details={"job": job_name, "execution": execution_id},
                ) from e
            raise CloudRunError(
                f"Failed to cancel execution '{execution_id}': {e}",
                details={"job": job_name, "execution": execution_id, "error": str(e)},
            ) from e

    def _get_job_path(self, job_name: str) -> str:
        """Get the full resource path for a job."""
        return f"projects/{self.settings.project_id}/locations/{self.region}/jobs/{job_name}"

    def _get_execution_path(self, job_name: str, execution_id: str) -> str:
        """Get the full resource path for a job execution."""
        return f"projects/{self.settings.project_id}/locations/{self.region}/jobs/{job_name}/executions/{execution_id}"

    def _job_to_model(self, job: Any) -> CloudRunJob:
        """Convert Cloud Run Job to CloudRunJob model with native object binding."""
        # Extract basic info
        name = job.name.split("/")[-1]

        # Extract container image
        image = ""
        if (
            hasattr(job, "template")
            and hasattr(job.template, "template")
            and job.template.template.containers
        ):
            image = job.template.template.containers[0].image

        # Extract execution configuration
        task_count = (
            job.template.task_count if hasattr(job.template, "task_count") else 1
        )
        parallelism = (
            job.template.parallelism if hasattr(job.template, "parallelism") else 1
        )
        max_retries = (
            job.template.template.max_retries
            if hasattr(job.template.template, "max_retries")
            else 3
        )

        # Extract timeout
        timeout = None
        if hasattr(job.template.template, "timeout"):
            timeout_value = job.template.template.timeout
            if timeout_value:
                # Handle both string format ("300s") and timedelta object
                if isinstance(timeout_value, str):
                    timeout = int(timeout_value.rstrip("s"))
                elif hasattr(timeout_value, "total_seconds"):
                    # datetime.timedelta object
                    timeout = int(timeout_value.total_seconds())
                else:
                    # Fallback: try to convert to int
                    timeout = int(timeout_value)

        # Extract resources
        cpu = None
        memory = None
        if (
            hasattr(job.template.template.containers[0], "resources")
            and job.template.template.containers[0].resources
        ):
            resources = job.template.template.containers[0].resources
            if hasattr(resources, "limits") and resources.limits:
                cpu = resources.limits.get("cpu")
                memory = resources.limits.get("memory")

        # Extract environment variables
        env_vars = {}
        if hasattr(job.template.template.containers[0], "env"):
            for env in job.template.template.containers[0].env:
                if hasattr(env, "name") and hasattr(env, "value"):
                    env_vars[env.name] = env.value

        # Extract service account
        service_account = (
            job.template.template.service_account
            if hasattr(job.template.template, "service_account")
            else None
        )

        # Extract execution environment
        execution_env = ExecutionEnvironment.EXECUTION_ENVIRONMENT_GEN2
        if hasattr(job.template.template, "execution_environment"):
            env_val = job.template.template.execution_environment
            if env_val:
                try:
                    execution_env = ExecutionEnvironment(str(env_val))
                except ValueError:
                    pass

        # Extract latest execution
        latest_execution = None
        if hasattr(job, "latest_created_execution") and job.latest_created_execution:
            if hasattr(job.latest_created_execution, "name"):
                latest_execution = job.latest_created_execution.name.split("/")[-1]

        # Extract execution count
        execution_count = job.execution_count if hasattr(job, "execution_count") else 0

        # Extract launch stage
        launch_stage = LaunchStage.GA
        if hasattr(job, "launch_stage"):
            try:
                launch_stage = LaunchStage(str(job.launch_stage))
            except ValueError:
                pass

        model = CloudRunJob(
            name=name,
            region=self.region,
            image=image,
            created=job.create_time if hasattr(job, "create_time") else None,
            updated=job.update_time if hasattr(job, "update_time") else None,
            labels=dict(job.labels) if hasattr(job, "labels") else {},
            task_count=task_count,
            parallelism=parallelism,
            max_retries=max_retries,
            timeout=timeout,
            cpu=cpu,
            memory=memory,
            env_vars=env_vars,
            service_account=service_account,
            execution_environment=execution_env,
            latest_execution=latest_execution,
            execution_count=execution_count,
            launch_stage=launch_stage,
        )
        # Bind the native object
        model._job_object = job
        return model

    def _execution_to_model(self, execution: Any, job_name: str) -> JobExecution:
        """Convert Cloud Run Execution to JobExecution model with native object binding."""
        # Extract basic info
        name = execution.name
        execution_id = name.split("/")[-1]

        # Extract status - check in priority order
        status = ExecutionStatus.STATUS_UNSPECIFIED
        if hasattr(execution, "task_count"):
            # Check cancelled first
            if hasattr(execution, "cancelled_count") and execution.cancelled_count > 0:
                status = ExecutionStatus.CANCELLED
            # Then check failed
            elif hasattr(execution, "failed_count") and execution.failed_count > 0:
                status = ExecutionStatus.FAILED
            # Then check succeeded
            elif (
                hasattr(execution, "succeeded_count")
                and execution.succeeded_count == execution.task_count
            ):
                status = ExecutionStatus.SUCCEEDED
            # Then check running
            elif hasattr(execution, "running_count") and execution.running_count > 0:
                status = ExecutionStatus.RUNNING
            # Otherwise pending
            else:
                status = ExecutionStatus.PENDING

        # Extract timing
        created = execution.create_time if hasattr(execution, "create_time") else None
        started = execution.start_time if hasattr(execution, "start_time") else None
        completed = (
            execution.completion_time if hasattr(execution, "completion_time") else None
        )

        # Calculate duration
        duration_seconds = None
        if started and completed:
            duration_seconds = int((completed - started).total_seconds())

        # Extract task counts
        task_count = execution.task_count if hasattr(execution, "task_count") else 1
        succeeded_count = (
            execution.succeeded_count if hasattr(execution, "succeeded_count") else 0
        )
        failed_count = (
            execution.failed_count if hasattr(execution, "failed_count") else 0
        )
        cancelled_count = (
            execution.cancelled_count if hasattr(execution, "cancelled_count") else 0
        )
        running_count = (
            execution.running_count if hasattr(execution, "running_count") else 0
        )
        pending_count = (
            task_count
            - succeeded_count
            - failed_count
            - cancelled_count
            - running_count
        )

        # Extract parallelism
        parallelism = execution.parallelism if hasattr(execution, "parallelism") else 1

        # Extract error message
        error_message = None
        if hasattr(execution, "log_uri") and failed_count > 0:
            error_message = f"Execution failed with {failed_count} failed task(s)"

        model = JobExecution(
            name=name,
            execution_id=execution_id,
            job_name=job_name,
            region=self.region,
            status=status,
            created=created,
            started=started,
            completed=completed,
            duration_seconds=duration_seconds,
            task_count=task_count,
            succeeded_count=succeeded_count,
            failed_count=failed_count,
            cancelled_count=cancelled_count,
            running_count=running_count,
            pending_count=pending_count,
            parallelism=parallelism,
            labels=dict(execution.labels) if hasattr(execution, "labels") else {},
            error_message=error_message,
        )
        # Bind the native object
        model._execution_object = execution
        return model
