"""Data models for Workflows operations."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_serializer

if TYPE_CHECKING:
    from google.cloud.workflows_v1 import Workflow
    from google.cloud.workflows.executions_v1 import Execution


class ExecutionState(str, Enum):
    """Workflow execution states."""

    STATE_UNSPECIFIED = "STATE_UNSPECIFIED"
    ACTIVE = "ACTIVE"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowInfo(BaseModel):
    """
    Workflow information with native object binding.

    This model wraps the Google Cloud Workflow object, providing both
    structured Pydantic data and access to the full Workflows API
    via `_workflow_object`.

    Example:
        >>> workflow = workflows_ctrl.get_workflow("my-workflow")
        >>>
        >>> # Use Pydantic fields
        >>> print(f"State: {workflow.state}")
        >>>
        >>> # Use convenience methods
        >>> execution = workflow.execute({"input": "value"})
        >>> workflow.update(new_source_contents="...")
    """

    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    state: str = Field(..., description="Workflow state (ACTIVE, etc.)")
    created: Optional[datetime] = Field(None, description="Creation timestamp")
    updated: Optional[datetime] = Field(None, description="Last update timestamp")
    revision_id: Optional[str] = Field(None, description="Current revision ID")
    labels: dict[str, str] = Field(default_factory=dict, description="Workflow labels")

    # The actual Workflow object (private attribute, not serialized)
    _workflow_object: Optional["Workflow"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("created", "updated")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None

    # Convenience methods that delegate to controller operations

    def execute(self, argument: Optional[dict[str, Any]] = None) -> "WorkflowExecution":
        """
        Execute this workflow.

        Args:
            argument: Optional input arguments

        Returns:
            WorkflowExecution object

        Raises:
            ValueError: If no Workflow object is bound

        Note:
            This requires access to the controller. Consider using
            WorkflowsController.execute_workflow() directly instead.
        """
        if not self._workflow_object:
            raise ValueError("No Workflow object bound to this WorkflowInfo")
        raise NotImplementedError(
            "Workflow execution must be performed via WorkflowsController.execute_workflow()"
        )

    def update(self, source_contents: Optional[str] = None, description: Optional[str] = None) -> None:
        """
        Update this workflow's source or description.

        Args:
            source_contents: New workflow definition
            description: New description

        Raises:
            ValueError: If no Workflow object is bound

        Note:
            This requires access to the controller. Consider using
            WorkflowsController.update_workflow() directly instead.
        """
        if not self._workflow_object:
            raise ValueError("No Workflow object bound to this WorkflowInfo")
        raise NotImplementedError(
            "Workflow updates must be performed via WorkflowsController.update_workflow()"
        )


class WorkflowExecution(BaseModel):
    """
    Workflow execution information with native object binding.

    This model wraps the Google Cloud Execution object, providing both
    structured Pydantic data and access to the full Workflows Executions API
    via `_execution_object`.

    Example:
        >>> execution = workflows_ctrl.execute_workflow("my-workflow", {"input": "data"})
        >>>
        >>> # Use Pydantic fields
        >>> print(f"State: {execution.state}")
        >>>
        >>> # Use convenience methods
        >>> execution.cancel()
        >>> current_state = execution.get_state()
    """

    name: str = Field(..., description="Execution name")
    workflow_name: str = Field(..., description="Workflow name")
    state: ExecutionState = Field(..., description="Execution state")
    argument: Optional[dict[str, Any]] = Field(
        None, description="Input arguments to the execution"
    )
    result: Optional[dict[str, Any]] = Field(None, description="Execution result")
    error: Optional[str] = Field(None, description="Error message if failed")
    start_time: Optional[datetime] = Field(None, description="Execution start time")
    end_time: Optional[datetime] = Field(None, description="Execution end time")

    # The actual Execution object (private attribute, not serialized)
    _execution_object: Optional["Execution"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("start_time", "end_time")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None

    # Convenience methods that delegate to controller operations

    def cancel(self) -> None:
        """
        Cancel this execution.

        Raises:
            ValueError: If no Execution object is bound

        Note:
            This requires access to the controller. Consider using
            WorkflowsController.cancel_execution() directly instead.
        """
        if not self._execution_object:
            raise ValueError("No Execution object bound to this WorkflowExecution")
        raise NotImplementedError(
            "Execution cancellation must be performed via WorkflowsController.cancel_execution()"
        )

    def get_state(self) -> ExecutionState:
        """
        Get the current state of this execution.

        Returns:
            Current execution state

        Raises:
            ValueError: If no Execution object is bound

        Note:
            This requires access to the controller. Consider using
            WorkflowsController.get_execution() directly instead.
        """
        if not self._execution_object:
            raise ValueError("No Execution object bound to this WorkflowExecution")
        raise NotImplementedError(
            "Execution state refresh must be performed via WorkflowsController.get_execution()"
        )
