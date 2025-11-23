"""
Workflows controller for orchestrating GCP services.

This module provides a high-level interface for creating, managing, and
executing Google Cloud Workflows.
"""

import json
from typing import Any

from google.auth.credentials import Credentials
from google.cloud import workflows_v1
from google.cloud.workflows import executions_v1

from ..config import GCPSettings, get_settings
from ..exceptions import ResourceNotFoundError, ValidationError, WorkflowsError
from ..models.workflows import ExecutionState, WorkflowExecution, WorkflowInfo


class WorkflowsController:
    """
    Controller for Google Cloud Workflows operations.

    This controller provides methods for managing workflows and executions.

    Example:
        >>> from gcp_utils.controllers import WorkflowsController
        >>>
        >>> # Automatically loads from .env file
        >>> wf_ctrl = WorkflowsController()
        >>>
        >>> # Execute a workflow
        >>> execution = wf_ctrl.execute_workflow(
        ...     "my-workflow",
        ...     {"input": "value"}
        ... )
    """

    def __init__(
        self,
        settings: GCPSettings | None = None,
        credentials: Credentials | None = None,
        location: str | None = None,
    ) -> None:
        """
        Initialize the Workflows controller.

        Args:
            settings: GCP configuration settings. If not provided, loads from environment/.env file.
            credentials: Optional custom credentials
            location: Workflows location (defaults to settings.workflows_location)

        Raises:
            WorkflowsError: If client initialization fails
        """
        self.settings = settings or get_settings()
        self.location = location or self.settings.workflows_location

        try:
            self.workflows_client = workflows_v1.WorkflowsClient(
                credentials=credentials
            )
            self.executions_client = executions_v1.ExecutionsClient(
                credentials=credentials
            )
        except Exception as e:
            raise WorkflowsError(
                f"Failed to initialize Workflows client: {e}",
                details={"error": str(e)},
            )

    def create_workflow(
        self,
        workflow_name: str,
        source_contents: str,
        description: str | None = None,
        labels: dict[str, str] | None = None,
        service_account: str | None = None,
    ) -> WorkflowInfo:
        """
        Create a new workflow.

        Args:
            workflow_name: Name of the workflow
            source_contents: Workflow definition in YAML or JSON format
            description: Optional workflow description
            labels: Optional labels
            service_account: Service account email for workflow execution

        Returns:
            WorkflowInfo object

        Raises:
            ValidationError: If parameters are invalid
            WorkflowsError: If creation fails
        """
        if not workflow_name:
            raise ValidationError("Workflow name cannot be empty")
        if not source_contents:
            raise ValidationError("Workflow source contents cannot be empty")

        try:
            parent = f"projects/{self.settings.project_id}/locations/{self.location}"

            workflow = workflows_v1.Workflow(
                description=description or "",
                source_contents=source_contents,
                labels=labels or {},
            )

            if service_account:
                workflow.service_account = service_account

            request = workflows_v1.CreateWorkflowRequest(
                parent=parent,
                workflow=workflow,
                workflow_id=workflow_name,
            )

            operation = self.workflows_client.create_workflow(request=request)
            created_workflow = operation.result()

            return self._workflow_to_info(created_workflow)

        except ValidationError:
            raise
        except Exception as e:
            raise WorkflowsError(
                f"Failed to create workflow '{workflow_name}': {e}",
                details={"workflow": workflow_name, "error": str(e)},
            )

    def get_workflow(self, workflow_name: str) -> WorkflowInfo:
        """
        Get workflow information.

        Args:
            workflow_name: Name of the workflow

        Returns:
            WorkflowInfo object

        Raises:
            ResourceNotFoundError: If workflow doesn't exist
            WorkflowsError: If operation fails
        """
        try:
            workflow_path = self._get_workflow_path(workflow_name)
            workflow = self.workflows_client.get_workflow(name=workflow_path)

            return self._workflow_to_info(workflow)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Workflow '{workflow_name}' not found",
                    details={"workflow": workflow_name},
                )
            raise WorkflowsError(
                f"Failed to get workflow '{workflow_name}': {e}",
                details={"workflow": workflow_name, "error": str(e)},
            )

    def list_workflows(self) -> list[WorkflowInfo]:
        """
        List all workflows.

        Returns:
            List of WorkflowInfo objects

        Raises:
            WorkflowsError: If listing fails
        """
        try:
            parent = f"projects/{self.settings.project_id}/locations/{self.location}"
            workflows = self.workflows_client.list_workflows(parent=parent)

            return [self._workflow_to_info(wf) for wf in workflows]

        except Exception as e:
            raise WorkflowsError(
                f"Failed to list workflows: {e}",
                details={"error": str(e)},
            )

    def update_workflow(
        self,
        workflow_name: str,
        source_contents: str | None = None,
        description: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> WorkflowInfo:
        """
        Update an existing workflow.

        Args:
            workflow_name: Name of the workflow
            source_contents: New workflow definition
            description: New description
            labels: New labels (merges with existing)

        Returns:
            Updated WorkflowInfo object

        Raises:
            ResourceNotFoundError: If workflow doesn't exist
            WorkflowsError: If update fails
        """
        try:
            workflow_path = self._get_workflow_path(workflow_name)
            workflow = self.workflows_client.get_workflow(name=workflow_path)

            if source_contents:
                workflow.source_contents = source_contents
            if description is not None:
                workflow.description = description
            if labels:
                workflow.labels.update(labels)

            request = workflows_v1.UpdateWorkflowRequest(workflow=workflow)
            operation = self.workflows_client.update_workflow(request=request)
            updated_workflow = operation.result()

            return self._workflow_to_info(updated_workflow)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Workflow '{workflow_name}' not found",
                    details={"workflow": workflow_name},
                )
            raise WorkflowsError(
                f"Failed to update workflow '{workflow_name}': {e}",
                details={"workflow": workflow_name, "error": str(e)},
            )

    def delete_workflow(self, workflow_name: str) -> None:
        """
        Delete a workflow.

        Args:
            workflow_name: Name of the workflow to delete

        Raises:
            WorkflowsError: If deletion fails
        """
        try:
            workflow_path = self._get_workflow_path(workflow_name)

            request = workflows_v1.DeleteWorkflowRequest(name=workflow_path)
            operation = self.workflows_client.delete_workflow(request=request)
            operation.result()

        except Exception as e:
            raise WorkflowsError(
                f"Failed to delete workflow '{workflow_name}': {e}",
                details={"workflow": workflow_name, "error": str(e)},
            )

    def execute_workflow(
        self,
        workflow_name: str,
        argument: dict[str, Any] | None = None,
    ) -> WorkflowExecution:
        """
        Execute a workflow.

        Args:
            workflow_name: Name of the workflow to execute
            argument: Optional input arguments as dictionary

        Returns:
            WorkflowExecution object

        Raises:
            ResourceNotFoundError: If workflow doesn't exist
            WorkflowsError: If execution fails
        """
        try:
            parent = self._get_workflow_path(workflow_name)

            execution = executions_v1.Execution()
            if argument:
                execution.argument = json.dumps(argument)

            request = executions_v1.CreateExecutionRequest(
                parent=parent,
                execution=execution,
            )

            execution_result = self.executions_client.create_execution(request=request)

            return self._execution_to_model(execution_result, workflow_name)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Workflow '{workflow_name}' not found",
                    details={"workflow": workflow_name},
                )
            raise WorkflowsError(
                f"Failed to execute workflow '{workflow_name}': {e}",
                details={"workflow": workflow_name, "error": str(e)},
            )

    def get_execution(
        self,
        workflow_name: str,
        execution_id: str,
    ) -> WorkflowExecution:
        """
        Get execution information.

        Args:
            workflow_name: Name of the workflow
            execution_id: Execution ID

        Returns:
            WorkflowExecution object

        Raises:
            ResourceNotFoundError: If execution doesn't exist
            WorkflowsError: If operation fails
        """
        try:
            execution_path = self._get_execution_path(workflow_name, execution_id)
            execution = self.executions_client.get_execution(name=execution_path)

            return self._execution_to_model(execution, workflow_name)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Execution '{execution_id}' not found for workflow '{workflow_name}'",
                    details={"workflow": workflow_name, "execution": execution_id},
                )
            raise WorkflowsError(
                f"Failed to get execution '{execution_id}': {e}",
                details={
                    "workflow": workflow_name,
                    "execution": execution_id,
                    "error": str(e),
                },
            )

    def list_executions(
        self,
        workflow_name: str,
        page_size: int = 100,
    ) -> list[WorkflowExecution]:
        """
        List executions for a workflow.

        Args:
            workflow_name: Name of the workflow
            page_size: Number of executions to return

        Returns:
            List of WorkflowExecution objects

        Raises:
            WorkflowsError: If listing fails
        """
        try:
            parent = self._get_workflow_path(workflow_name)

            request = executions_v1.ListExecutionsRequest(
                parent=parent,
                page_size=page_size,
            )

            executions = self.executions_client.list_executions(request=request)

            return [
                self._execution_to_model(execution, workflow_name)
                for execution in executions
            ]

        except Exception as e:
            raise WorkflowsError(
                f"Failed to list executions for workflow '{workflow_name}': {e}",
                details={"workflow": workflow_name, "error": str(e)},
            )

    def cancel_execution(
        self,
        workflow_name: str,
        execution_id: str,
    ) -> WorkflowExecution:
        """
        Cancel a running execution.

        Args:
            workflow_name: Name of the workflow
            execution_id: Execution ID to cancel

        Returns:
            Cancelled WorkflowExecution object

        Raises:
            WorkflowsError: If cancellation fails
        """
        try:
            execution_path = self._get_execution_path(workflow_name, execution_id)

            request = executions_v1.CancelExecutionRequest(name=execution_path)
            execution = self.executions_client.cancel_execution(request=request)

            return self._execution_to_model(execution, workflow_name)

        except Exception as e:
            raise WorkflowsError(
                f"Failed to cancel execution '{execution_id}': {e}",
                details={
                    "workflow": workflow_name,
                    "execution": execution_id,
                    "error": str(e),
                },
            )

    def _get_workflow_path(self, workflow_name: str) -> str:
        """Get the full resource path for a workflow."""
        return f"projects/{self.settings.project_id}/locations/{self.location}/workflows/{workflow_name}"

    def _get_execution_path(self, workflow_name: str, execution_id: str) -> str:
        """Get the full resource path for an execution."""
        return f"{self._get_workflow_path(workflow_name)}/executions/{execution_id}"

    def _workflow_to_info(self, workflow: Any) -> WorkflowInfo:
        """Convert Workflow to WorkflowInfo model with native object binding."""
        name = workflow.name.split("/")[-1]

        model = WorkflowInfo(
            name=name,
            description=workflow.description if hasattr(workflow, "description") else None,
            state=str(workflow.state) if hasattr(workflow, "state") else "UNKNOWN",
            created=workflow.create_time if hasattr(workflow, "create_time") else None,
            updated=workflow.update_time if hasattr(workflow, "update_time") else None,
            revision_id=(
                workflow.revision_id if hasattr(workflow, "revision_id") else None
            ),
            labels=dict(workflow.labels) if hasattr(workflow, "labels") else {},
        )
        # Bind the native object
        model._workflow_object = workflow
        return model

    def _execution_to_model(
        self, execution: Any, workflow_name: str
    ) -> WorkflowExecution:
        """Convert Execution to WorkflowExecution model with native object binding."""
        execution_id = execution.name.split("/")[-1]

        # Parse argument
        argument = None
        if hasattr(execution, "argument") and execution.argument:
            try:
                argument = json.loads(execution.argument)
            except json.JSONDecodeError:
                argument = {"raw": execution.argument}

        # Parse result
        result = None
        if hasattr(execution, "result") and execution.result:
            try:
                result = json.loads(execution.result)
            except json.JSONDecodeError:
                result = {"raw": execution.result}

        # Map state
        state = ExecutionState.STATE_UNSPECIFIED
        if hasattr(execution, "state"):
            state_str = str(execution.state)
            try:
                state = ExecutionState[state_str.split(".")[-1]]
            except (KeyError, AttributeError):
                pass

        model = WorkflowExecution(
            name=execution_id,
            workflow_name=workflow_name,
            state=state,
            argument=argument,
            result=result,
            error=execution.error if hasattr(execution, "error") else None,
            start_time=(
                execution.start_time if hasattr(execution, "start_time") else None
            ),
            end_time=execution.end_time if hasattr(execution, "end_time") else None,
        )
        # Bind the native object
        model._execution_object = execution
        return model
