"""
Tests for BigQuery controller.

This module tests the BigQueryController class with mocked GCP clients.
"""

from unittest.mock import MagicMock, Mock

import pytest
from google.api_core.exceptions import NotFound
from google.cloud import bigquery

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.bigquery import BigQueryController
from gcp_utils.exceptions import BigQueryError, ResourceNotFoundError
from gcp_utils.models.bigquery import SchemaField


@pytest.fixture
def settings() -> GCPSettings:
    """Create test settings."""
    return GCPSettings(project_id="test-project")


@pytest.fixture
def mock_client() -> Mock:
    """Create a mock BigQuery client."""
    return MagicMock()


@pytest.fixture
def controller(settings: GCPSettings, mock_client: Mock) -> BigQueryController:
    """Create a BigQueryController with mocked client."""
    controller = BigQueryController(settings=settings)
    controller._client = mock_client
    return controller


def test_create_dataset(controller: BigQueryController, mock_client: Mock) -> None:
    """Test creating a BigQuery dataset."""
    # Setup mock
    mock_dataset = MagicMock()
    mock_dataset.dataset_id = "my_dataset"
    mock_dataset.project = "test-project"
    mock_dataset.location = "US"
    mock_dataset.description = "Test dataset"
    mock_dataset.friendly_name = None
    mock_dataset.labels = {}
    mock_dataset.default_table_expiration_ms = None
    mock_dataset.created = None
    mock_dataset.modified = None
    mock_client.create_dataset.return_value = mock_dataset

    # Execute
    result = controller.create_dataset(
        dataset_id="my_dataset",
        location="US",
        description="Test dataset",
    )

    # Assert
    assert result.dataset_id == "my_dataset"
    assert result.location == "US"
    mock_client.create_dataset.assert_called_once()


def test_get_dataset(controller: BigQueryController, mock_client: Mock) -> None:
    """Test getting a BigQuery dataset."""
    # Setup mock
    mock_dataset = MagicMock()
    mock_dataset.dataset_id = "my_dataset"
    mock_dataset.project = "test-project"
    mock_dataset.location = "US"
    mock_dataset.description = None
    mock_dataset.friendly_name = None
    mock_dataset.labels = None
    mock_dataset.default_table_expiration_ms = None
    mock_dataset.created = None
    mock_dataset.modified = None
    mock_client.get_dataset.return_value = mock_dataset

    # Execute
    result = controller.get_dataset("my_dataset")

    # Assert
    assert result.dataset_id == "my_dataset"
    mock_client.get_dataset.assert_called_once()


def test_get_dataset_not_found(
    controller: BigQueryController, mock_client: Mock
) -> None:
    """Test getting a non-existent dataset raises ResourceNotFoundError."""
    # Setup mock
    mock_client.get_dataset.side_effect = NotFound("Dataset not found")

    # Execute and assert
    with pytest.raises(ResourceNotFoundError):
        controller.get_dataset("nonexistent")


def test_list_datasets(controller: BigQueryController, mock_client: Mock) -> None:
    """Test listing BigQuery datasets."""
    # Setup mock
    mock_datasets = [
        MagicMock(dataset_id="dataset1", project="test-project"),
        MagicMock(dataset_id="dataset2", project="test-project"),
    ]
    mock_client.list_datasets.return_value = mock_datasets

    # Execute
    result = controller.list_datasets()

    # Assert
    assert len(result.datasets) == 2
    mock_client.list_datasets.assert_called_once()


def test_delete_dataset(controller: BigQueryController, mock_client: Mock) -> None:
    """Test deleting a BigQuery dataset."""
    # Execute
    controller.delete_dataset("my_dataset")

    # Assert
    mock_client.delete_dataset.assert_called_once()


def test_create_table(controller: BigQueryController, mock_client: Mock) -> None:
    """Test creating a BigQuery table."""
    # Setup mock
    mock_table = MagicMock()
    mock_table.table_id = "my_table"
    mock_table.dataset_id = "my_dataset"
    mock_table.project = "test-project"
    mock_table.description = "Test table"
    mock_table.friendly_name = None
    mock_table.labels = None
    mock_table.num_rows = None
    mock_table.num_bytes = None
    mock_table.created = None
    mock_table.modified = None
    mock_table.expires = None
    mock_client.create_table.return_value = mock_table

    # Execute
    schema = [
        SchemaField(name="id", field_type="INTEGER", mode="REQUIRED"),
        SchemaField(name="name", field_type="STRING", mode="REQUIRED"),
    ]
    result = controller.create_table(
        dataset_id="my_dataset",
        table_id="my_table",
        schema=schema,
        description="Test table",
    )

    # Assert
    assert result.table_id == "my_table"
    assert result.dataset_id == "my_dataset"
    mock_client.create_table.assert_called_once()


def test_get_table(controller: BigQueryController, mock_client: Mock) -> None:
    """Test getting a BigQuery table."""
    # Setup mock
    mock_table = MagicMock()
    mock_table.table_id = "my_table"
    mock_table.dataset_id = "my_dataset"
    mock_table.project = "test-project"
    mock_table.description = None
    mock_table.friendly_name = None
    mock_table.labels = None
    mock_table.num_rows = 100
    mock_table.num_bytes = 1024
    mock_table.created = None
    mock_table.modified = None
    mock_table.expires = None
    mock_client.get_table.return_value = mock_table

    # Execute
    result = controller.get_table("my_dataset", "my_table")

    # Assert
    assert result.table_id == "my_table"
    assert result.num_rows == 100
    mock_client.get_table.assert_called_once()


def test_list_tables(controller: BigQueryController, mock_client: Mock) -> None:
    """Test listing tables in a BigQuery dataset."""
    # Setup mock
    mock_tables = [
        MagicMock(table_id="table1", dataset_id="my_dataset", project="test-project"),
        MagicMock(table_id="table2", dataset_id="my_dataset", project="test-project"),
    ]
    mock_client.list_tables.return_value = mock_tables

    # Execute
    result = controller.list_tables("my_dataset")

    # Assert
    assert len(result.tables) == 2
    mock_client.list_tables.assert_called_once()


def test_delete_table(controller: BigQueryController, mock_client: Mock) -> None:
    """Test deleting a BigQuery table."""
    # Execute
    controller.delete_table("my_dataset", "my_table")

    # Assert
    mock_client.delete_table.assert_called_once()


def test_query(controller: BigQueryController, mock_client: Mock) -> None:
    """Test executing a BigQuery query."""
    # Setup mock
    mock_job = MagicMock()
    mock_job.job_id = "job123"
    mock_job.total_bytes_processed = 1024
    mock_job.total_bytes_billed = 1024
    mock_job.cache_hit = False

    mock_result = MagicMock()
    mock_result.total_rows = 2
    mock_result.schema = [
        bigquery.SchemaField("name", "STRING"),
        bigquery.SchemaField("count", "INTEGER"),
    ]
    mock_result.__iter__ = Mock(
        return_value=iter([
            {"name": "Alice", "count": 10},
            {"name": "Bob", "count": 20},
        ])
    )

    mock_job.result.return_value = mock_result
    mock_client.query.return_value = mock_job

    # Execute
    result = controller.query("SELECT name, COUNT(*) as count FROM users GROUP BY name")

    # Assert
    assert result.total_rows == 2
    assert len(result.rows) == 2
    assert result.rows[0].values["name"] == "Alice"
    mock_client.query.assert_called_once()


def test_insert_rows(controller: BigQueryController, mock_client: Mock) -> None:
    """Test inserting rows into a BigQuery table."""
    # Setup mock
    mock_table = MagicMock()
    mock_client.get_table.return_value = mock_table
    mock_client.insert_rows.return_value = []  # No errors

    # Execute
    rows = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]
    controller.insert_rows("my_dataset", "my_table", rows)

    # Assert
    mock_client.insert_rows.assert_called_once()


def test_insert_rows_with_errors(
    controller: BigQueryController, mock_client: Mock
) -> None:
    """Test inserting rows with errors raises BigQueryError."""
    # Setup mock
    mock_table = MagicMock()
    mock_client.get_table.return_value = mock_table
    mock_client.insert_rows.return_value = [{"error": "Invalid row"}]

    # Execute and assert
    rows = [{"id": 1, "name": "Alice"}]
    with pytest.raises(BigQueryError):
        controller.insert_rows("my_dataset", "my_table", rows)
