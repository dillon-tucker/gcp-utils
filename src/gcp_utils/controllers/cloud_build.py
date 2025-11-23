"""
Google Cloud Build controller for CI/CD automation.

This module provides a type-safe controller for managing Cloud Build triggers
and executing builds for continuous integration and deployment workflows.
"""


from google.api_core.exceptions import GoogleAPIError
from google.auth.credentials import Credentials
from google.cloud.devtools import cloudbuild_v1
from google.cloud.devtools.cloudbuild_v1.types import (
    Build as GCPBuild,
)
from google.cloud.devtools.cloudbuild_v1.types import (
    BuildTrigger as GCPBuildTrigger,
)
from google.cloud.devtools.cloudbuild_v1.types import (
    CancelBuildRequest,
    CreateBuildRequest,
    CreateBuildTriggerRequest,
    DeleteBuildTriggerRequest,
    GetBuildRequest,
    GetBuildTriggerRequest,
    ListBuildsRequest,
    ListBuildTriggersRequest,
    RunBuildTriggerRequest,
    UpdateBuildTriggerRequest,
)

from ..config import GCPSettings, get_settings
from ..exceptions import CloudBuildError, ResourceNotFoundError
from ..models.cloud_build import (
    Build,
    BuildListResponse,
    BuildTrigger,
    RunBuildTriggerResponse,
    TriggerListResponse,
)


class CloudBuildController:
    """
    Controller for managing Google Cloud Build.

    Provides methods for creating and managing build triggers, executing builds,
    and implementing CI/CD pipelines.

    Example:
        ```python
        from gcp_utils.controllers import CloudBuildController
        from gcp_utils.models.cloud_build import BuildStep

        # Controller auto-loads settings from .env file
        build = CloudBuildController()

        # Create a simple build with steps
        steps = [
            BuildStep(
                name="gcr.io/cloud-builders/docker",
                args=["build", "-t", "gcr.io/my-project/my-image", "."],
            ),
            BuildStep(
                name="gcr.io/cloud-builders/docker",
                args=["push", "gcr.io/my-project/my-image"],
            ),
        ]

        # Execute build
        result = build.create_build(steps=steps)
        ```
    """

    def __init__(
        self,
        settings: GCPSettings | None = None,
        credentials: Credentials | None = None,
    ) -> None:
        """
        Initialize the Cloud Build controller.

        Args:
            settings: GCP configuration. If not provided, loads from environment/.env file.
            credentials: Optional custom credentials.
        """
        self._settings = settings or get_settings()
        self._credentials = credentials
        self._client: cloudbuild_v1.CloudBuildClient | None = None

    def _get_client(self) -> cloudbuild_v1.CloudBuildClient:
        """Lazy initialization of the Cloud Build client."""
        if self._client is None:
            self._client = cloudbuild_v1.CloudBuildClient(
                credentials=self._credentials
            )
        return self._client

    def _build_to_model(self, build: GCPBuild) -> Build:
        """Convert a Build proto to Build model."""
        return Build(
            id=build.id,
            project_id=build.project_id or self._settings.project_id,
            status=build.status.name if build.status else None,
            create_time=build.create_time,
            start_time=build.start_time,
            finish_time=build.finish_time,
            log_url=build.log_url or None,
            timeout=str(build.timeout.seconds) + "s" if build.timeout else None,
            steps=[],  # Simplified for now
        )

    def _trigger_to_model(self, trigger: GCPBuildTrigger) -> BuildTrigger:
        """Convert a BuildTrigger proto to BuildTrigger model."""
        return BuildTrigger(
            id=trigger.id,
            name=trigger.name,
            description=trigger.description or None,
            tags=list(trigger.tags) if trigger.tags else None,
            create_time=trigger.create_time,
            disabled=trigger.disabled,
            substitutions=dict(trigger.substitutions) if trigger.substitutions else None,
            filename=trigger.filename or None,
            filter=trigger.filter or None,
        )

    def create_build(
        self,
        steps: list[dict],
        source: dict | None = None,
        images: list[str] | None = None,
        timeout: str | None = None,
        substitutions: dict[str, str] | None = None,
        tags: list[str] | None = None,
        wait_for_completion: bool = False,
    ) -> Build:
        """
        Create and execute a Cloud Build.

        Args:
            steps: Build steps to execute (list of BuildStep dictionaries)
            source: Build source configuration (optional)
            images: Container images to build and push
            timeout: Build timeout (e.g., '600s')
            substitutions: Substitution variables
            tags: Build tags
            wait_for_completion: Wait for the build to complete

        Returns:
            Build model with build details

        Raises:
            CloudBuildError: If build creation fails

        Example:
            ```python
            steps = [
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": ["build", "-t", "gcr.io/my-project/image", "."],
                },
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": ["push", "gcr.io/my-project/image"],
                },
            ]

            build = cloud_build.create_build(
                steps=steps,
                images=["gcr.io/my-project/image"],
                tags=["latest", "v1.0"],
            )
            ```
        """
        try:
            client = self._get_client()

            build = GCPBuild(
                project_id=self._settings.project_id,
                steps=steps,
            )

            if source:
                build.source = source

            if images:
                build.images = images

            if timeout:
                from google.protobuf import duration_pb2

                seconds = int(timeout.rstrip("s"))
                build.timeout = duration_pb2.Duration(seconds=seconds)

            if substitutions:
                build.substitutions = substitutions

            if tags:
                build.tags = tags

            request = CreateBuildRequest(
                project_id=self._settings.project_id,
                build=build,
            )

            operation = client.create_build(request=request)

            if wait_for_completion:
                result = operation.result()
                return self._build_to_model(result)

            # Get metadata from operation
            metadata = operation.metadata
            return Build(
                id=metadata.build.id if metadata else None,
                project_id=self._settings.project_id,
                steps=[],
            )

        except GoogleAPIError as e:
            raise CloudBuildError(
                message=f"Failed to create build: {str(e)}",
                details={"error": str(e)},
            ) from e

    def get_build(self, build_id: str) -> Build:
        """
        Get details about a Cloud Build.

        Args:
            build_id: Build ID

        Returns:
            Build model with build details

        Raises:
            ResourceNotFoundError: If build doesn't exist
            CloudBuildError: If retrieval fails

        Example:
            ```python
            build = cloud_build.get_build("abc123")
            print(f"Status: {build.status}")
            print(f"Log URL: {build.log_url}")
            ```
        """
        try:
            client = self._get_client()

            request = GetBuildRequest(
                project_id=self._settings.project_id,
                id=build_id,
            )

            build = client.get_build(request=request)

            return self._build_to_model(build)

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Build '{build_id}' not found",
                    details={"build_id": build_id},
                ) from e

            raise CloudBuildError(
                message=f"Failed to get build '{build_id}': {str(e)}",
                details={"build_id": build_id, "error": str(e)},
            ) from e

    def list_builds(
        self,
        page_size: int = 100,
        page_token: str | None = None,
        filter_: str | None = None,
    ) -> BuildListResponse:
        """
        List Cloud Builds in the project.

        Args:
            page_size: Maximum number of builds to return
            page_token: Token from previous list call for pagination
            filter_: Filter expression (e.g., 'status="SUCCESS"')

        Returns:
            BuildListResponse with list of builds and pagination token

        Raises:
            CloudBuildError: If listing fails

        Example:
            ```python
            # List all builds
            response = cloud_build.list_builds()
            for build in response.builds:
                print(f"{build.id}: {build.status}")

            # List only successful builds
            response = cloud_build.list_builds(filter_='status="SUCCESS"')
            ```
        """
        try:
            client = self._get_client()

            request = ListBuildsRequest(
                project_id=self._settings.project_id,
                page_size=page_size,
                page_token=page_token or "",
                filter=filter_ or "",
            )

            response = client.list_builds(request=request)

            builds = [self._build_to_model(build) for build in response.builds]

            return BuildListResponse(
                builds=builds,
                next_page_token=response.next_page_token or None,
            )

        except GoogleAPIError as e:
            raise CloudBuildError(
                message=f"Failed to list builds: {str(e)}",
                details={"error": str(e)},
            ) from e

    def cancel_build(self, build_id: str) -> Build:
        """
        Cancel a running Cloud Build.

        Args:
            build_id: Build ID

        Returns:
            Build model with updated status

        Raises:
            ResourceNotFoundError: If build doesn't exist
            CloudBuildError: If cancellation fails

        Example:
            ```python
            build = cloud_build.cancel_build("abc123")
            print(f"Build cancelled: {build.status}")
            ```
        """
        try:
            client = self._get_client()

            request = CancelBuildRequest(
                project_id=self._settings.project_id,
                id=build_id,
            )

            build = client.cancel_build(request=request)

            return self._build_to_model(build)

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Build '{build_id}' not found",
                    details={"build_id": build_id},
                ) from e

            raise CloudBuildError(
                message=f"Failed to cancel build '{build_id}': {str(e)}",
                details={"build_id": build_id, "error": str(e)},
            ) from e

    def create_build_trigger(
        self,
        name: str,
        description: str | None = None,
        trigger_template: dict | None = None,
        github: dict | None = None,
        build: dict | None = None,
        filename: str | None = None,
        substitutions: dict[str, str] | None = None,
        tags: list[str] | None = None,
    ) -> BuildTrigger:
        """
        Create a Cloud Build trigger.

        Args:
            name: Trigger name
            description: Trigger description
            trigger_template: Cloud Source Repository trigger configuration
            github: GitHub events configuration
            build: Build configuration to execute
            filename: Path to cloudbuild.yaml file in source repo
            substitutions: Substitution variables
            tags: Trigger tags

        Returns:
            BuildTrigger model

        Raises:
            CloudBuildError: If trigger creation fails

        Example:
            ```python
            # Create a trigger for Cloud Source Repositories
            trigger_template = {
                "project_id": project_id,
                "repo_name": "my-repo",
                "branch_name": "main",
            }

            trigger = cloud_build.create_build_trigger(
                name="deploy-on-push",
                description="Deploy on push to main",
                trigger_template=trigger_template,
                filename="cloudbuild.yaml",
            )
            ```
        """
        try:
            client = self._get_client()

            trigger = GCPBuildTrigger(name=name)

            if description:
                trigger.description = description

            if trigger_template:
                trigger.trigger_template = trigger_template

            if github:
                trigger.github = github

            if build:
                trigger.build = build

            if filename:
                trigger.filename = filename

            if substitutions:
                trigger.substitutions = substitutions

            if tags:
                trigger.tags = tags

            request = CreateBuildTriggerRequest(
                project_id=self._settings.project_id,
                trigger=trigger,
            )

            result = client.create_build_trigger(request=request)

            return self._trigger_to_model(result)

        except GoogleAPIError as e:
            raise CloudBuildError(
                message=f"Failed to create build trigger '{name}': {str(e)}",
                details={"name": name, "error": str(e)},
            ) from e

    def get_build_trigger(self, trigger_id: str) -> BuildTrigger:
        """
        Get a Cloud Build trigger.

        Args:
            trigger_id: Trigger ID

        Returns:
            BuildTrigger model

        Raises:
            ResourceNotFoundError: If trigger doesn't exist
            CloudBuildError: If retrieval fails

        Example:
            ```python
            trigger = cloud_build.get_build_trigger("abc123")
            print(f"Name: {trigger.name}")
            print(f"Disabled: {trigger.disabled}")
            ```
        """
        try:
            client = self._get_client()

            request = GetBuildTriggerRequest(
                project_id=self._settings.project_id,
                trigger_id=trigger_id,
            )

            trigger = client.get_build_trigger(request=request)

            return self._trigger_to_model(trigger)

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Build trigger '{trigger_id}' not found",
                    details={"trigger_id": trigger_id},
                ) from e

            raise CloudBuildError(
                message=f"Failed to get build trigger '{trigger_id}': {str(e)}",
                details={"trigger_id": trigger_id, "error": str(e)},
            ) from e

    def list_build_triggers(
        self, page_size: int = 100, page_token: str | None = None
    ) -> TriggerListResponse:
        """
        List Cloud Build triggers in the project.

        Args:
            page_size: Maximum number of triggers to return
            page_token: Token from previous list call for pagination

        Returns:
            TriggerListResponse with list of triggers and pagination token

        Raises:
            CloudBuildError: If listing fails

        Example:
            ```python
            response = cloud_build.list_build_triggers()
            for trigger in response.triggers:
                print(f"{trigger.name}: {trigger.description}")
            ```
        """
        try:
            client = self._get_client()

            request = ListBuildTriggersRequest(
                project_id=self._settings.project_id,
                page_size=page_size,
                page_token=page_token or "",
            )

            response = client.list_build_triggers(request=request)

            triggers = [self._trigger_to_model(trigger) for trigger in response.triggers]

            return TriggerListResponse(
                triggers=triggers,
                next_page_token=response.next_page_token or None,
            )

        except GoogleAPIError as e:
            raise CloudBuildError(
                message=f"Failed to list build triggers: {str(e)}",
                details={"error": str(e)},
            ) from e

    def update_build_trigger(
        self,
        trigger_id: str,
        name: str | None = None,
        description: str | None = None,
        disabled: bool | None = None,
        substitutions: dict[str, str] | None = None,
    ) -> BuildTrigger:
        """
        Update a Cloud Build trigger.

        Args:
            trigger_id: Trigger ID
            name: Updated trigger name
            description: Updated description
            disabled: Whether to disable the trigger
            substitutions: Updated substitution variables

        Returns:
            BuildTrigger model with updated details

        Raises:
            ResourceNotFoundError: If trigger doesn't exist
            CloudBuildError: If update fails

        Example:
            ```python
            # Disable a trigger
            trigger = cloud_build.update_build_trigger(
                trigger_id="abc123",
                disabled=True,
            )
            ```
        """
        try:
            client = self._get_client()

            # Get existing trigger
            get_request = GetBuildTriggerRequest(
                project_id=self._settings.project_id,
                trigger_id=trigger_id,
            )
            trigger = client.get_build_trigger(request=get_request)

            # Update fields
            if name is not None:
                trigger.name = name

            if description is not None:
                trigger.description = description

            if disabled is not None:
                trigger.disabled = disabled

            if substitutions is not None:
                trigger.substitutions = substitutions

            request = UpdateBuildTriggerRequest(
                project_id=self._settings.project_id,
                trigger_id=trigger_id,
                trigger=trigger,
            )

            result = client.update_build_trigger(request=request)

            return self._trigger_to_model(result)

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Build trigger '{trigger_id}' not found",
                    details={"trigger_id": trigger_id},
                ) from e

            raise CloudBuildError(
                message=f"Failed to update build trigger '{trigger_id}': {str(e)}",
                details={"trigger_id": trigger_id, "error": str(e)},
            ) from e

    def delete_build_trigger(self, trigger_id: str) -> None:
        """
        Delete a Cloud Build trigger.

        Args:
            trigger_id: Trigger ID

        Raises:
            ResourceNotFoundError: If trigger doesn't exist
            CloudBuildError: If deletion fails

        Example:
            ```python
            cloud_build.delete_build_trigger("abc123")
            ```
        """
        try:
            client = self._get_client()

            request = DeleteBuildTriggerRequest(
                project_id=self._settings.project_id,
                trigger_id=trigger_id,
            )

            client.delete_build_trigger(request=request)

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Build trigger '{trigger_id}' not found",
                    details={"trigger_id": trigger_id},
                ) from e

            raise CloudBuildError(
                message=f"Failed to delete build trigger '{trigger_id}': {str(e)}",
                details={"trigger_id": trigger_id, "error": str(e)},
            ) from e

    def run_build_trigger(
        self, trigger_id: str, branch_name: str | None = None
    ) -> RunBuildTriggerResponse:
        """
        Manually run a Cloud Build trigger.

        Args:
            trigger_id: Trigger ID
            branch_name: Branch name to build (optional, uses trigger default)

        Returns:
            RunBuildTriggerResponse with created build ID

        Raises:
            ResourceNotFoundError: If trigger doesn't exist
            CloudBuildError: If run operation fails

        Example:
            ```python
            response = cloud_build.run_build_trigger("abc123", branch_name="main")
            print(f"Build ID: {response.build_id}")
            ```
        """
        try:
            client = self._get_client()

            request = RunBuildTriggerRequest(
                project_id=self._settings.project_id,
                trigger_id=trigger_id,
            )

            if branch_name:
                from google.cloud.devtools.cloudbuild_v1.types import RepoSource

                request.source = RepoSource(branch_name=branch_name)

            operation = client.run_build_trigger(request=request)

            # Wait for operation to complete to get build ID
            result = operation.result()

            return RunBuildTriggerResponse(
                build_id=result.id,
                project_id=self._settings.project_id,
            )

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Build trigger '{trigger_id}' not found",
                    details={"trigger_id": trigger_id},
                ) from e

            raise CloudBuildError(
                message=f"Failed to run build trigger '{trigger_id}': {str(e)}",
                details={"trigger_id": trigger_id, "error": str(e)},
            ) from e
