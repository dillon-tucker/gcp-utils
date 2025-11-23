"""
Tests for WorkflowsController.
"""

from unittest.mock import MagicMock, patch

import pytest

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.workflows import WorkflowsController
from gcp_utils.exceptions import ResourceNotFoundError


@pytest.fixture
def settings():
    """Fixture for GCPSettings."""
    return GCPSettings()


@pytest.fixture
def workflows_controller(settings):
    """Fixture for WorkflowsController with a mocked client."""
    with (
        patch("google.cloud.workflows.v1.WorkflowsClient") as mock_workflows_client,
        patch(
            "google.cloud.workflows.executions_v1.ExecutionsClient"
        ) as mock_executions_client,
    ):
        controller = WorkflowsController(settings)
        controller._workflows_client = mock_workflows_client.return_value
        controller._executions_client = mock_executions_client.return_value
        yield controller


def test_create_workflow_success(workflows_controller):
    """Test creating a workflow successfully."""
    mock_operation = MagicMock()
    mock_workflow = MagicMock()
    mock_workflow.name = (
        "projects/test-project/locations/us-central1/workflows/test-workflow"
    )

    mock_operation.result.return_value = mock_workflow
    workflows_controller._workflows_client.create_workflow.return_value = mock_operation

    workflow = workflows_controller.create_workflow(
        "test-workflow", "- step1:\n    return: 'hello'"
    )

    assert "test-workflow" in workflow.name


def test_get_workflow_success(workflows_controller):
    """Test getting a workflow successfully."""
    mock_workflow = MagicMock()
    mock_workflow.name = (
        "projects/test-project/locations/us-central1/workflows/test-workflow"
    )

    workflows_controller._workflows_client.get_workflow.return_value = mock_workflow

    workflow = workflows_controller.get_workflow("test-workflow")

    assert "test-workflow" in workflow.name


def test_get_workflow_not_found(workflows_controller):
    """Test getting a non-existent workflow."""
    workflows_controller._workflows_client.get_workflow.side_effect = Exception(
        "404 Not Found"
    )

    with pytest.raises(ResourceNotFoundError):
        workflows_controller.get_workflow("non-existent-workflow")


def test_execute_workflow_success(workflows_controller):
    """Test executing a workflow successfully."""
    mock_execution = MagicMock()
    mock_execution.name = "projects/test-project/locations/us-central1/workflows/test-workflow/executions/exec-123"

    workflows_controller._executions_client.create_execution.return_value = (
        mock_execution
    )

    execution = workflows_controller.execute_workflow(
        "test-workflow", argument={"key": "value"}
    )

    assert "exec-" in execution.name


def test_delete_workflow(workflows_controller):
    """Test deleting a workflow."""
    mock_operation = MagicMock()
    mock_operation.result.return_value = None
    workflows_controller._workflows_client.delete_workflow.return_value = mock_operation

    workflows_controller.delete_workflow("test-workflow")

    workflows_controller._workflows_client.delete_workflow.assert_called_once()


def test_list_workflows(workflows_controller):
    """Test listing workflows."""
    mock_workflow = MagicMock()
    mock_workflow.name = (
        "projects/test-project/locations/us-central1/workflows/test-workflow"
    )

    workflows_controller._workflows_client.list_workflows.return_value = [mock_workflow]

    workflows = workflows_controller.list_workflows()

    assert len(workflows) >= 1
