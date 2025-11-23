"""
Tests for CloudLoggingController.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.cloud_logging import CloudLoggingController
from gcp_utils.exceptions import (
    CloudLoggingError,
    ResourceNotFoundError,
    ValidationError,
)
from gcp_utils.models.cloud_logging import LogSeverity


@pytest.fixture
def settings():
    """Fixture for GCPSettings."""
    return GCPSettings()


@pytest.fixture
def logging_controller(settings):
    """Fixture for CloudLoggingController with mocked client."""
    with patch("google.cloud.logging.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        controller = CloudLoggingController(settings)
        # Force client initialization
        controller._client = mock_client

        # Mock logger
        mock_logger = MagicMock()
        controller._loggers = {"test-log": mock_logger}

        yield controller


def test_write_log_text(logging_controller):
    """Test writing a simple text log."""
    mock_logger = logging_controller._loggers["test-log"]

    logging_controller.write_log(
        log_name="test-log", message="Test message", severity=LogSeverity.INFO
    )

    mock_logger.log_text.assert_called_once()
    call_args = mock_logger.log_text.call_args
    assert call_args[0][0] == "Test message"
    assert call_args[1]["severity"] == "INFO"


def test_write_log_structured(logging_controller):
    """Test writing a structured JSON log."""
    mock_logger = logging_controller._loggers["test-log"]

    logging_controller.write_log(
        log_name="test-log",
        message={"event": "user_login", "user_id": "123"},
        severity=LogSeverity.INFO,
    )

    mock_logger.log_struct.assert_called_once()
    call_args = mock_logger.log_struct.call_args
    assert call_args[0][0] == {"event": "user_login", "user_id": "123"}
    assert call_args[1]["severity"] == "INFO"


def test_write_log_with_labels(logging_controller):
    """Test writing a log with labels."""
    mock_logger = logging_controller._loggers["test-log"]

    logging_controller.write_log(
        log_name="test-log",
        message="Test message",
        severity=LogSeverity.WARNING,
        labels={"environment": "production", "version": "1.0.0"},
    )

    mock_logger.log_text.assert_called_once()
    call_args = mock_logger.log_text.call_args
    assert call_args[1]["labels"] == {"environment": "production", "version": "1.0.0"}


def test_write_log_with_trace(logging_controller):
    """Test writing a log with trace information."""
    mock_logger = logging_controller._loggers["test-log"]

    logging_controller.write_log(
        log_name="test-log",
        message="Test message",
        severity=LogSeverity.INFO,
        trace="projects/test-project/traces/123",
        span_id="456",
    )

    mock_logger.log_text.assert_called_once()
    call_args = mock_logger.log_text.call_args
    assert call_args[1]["trace"] == "projects/test-project/traces/123"
    assert call_args[1]["span_id"] == "456"


def test_write_log_empty_name(logging_controller):
    """Test writing a log with empty name raises ValidationError."""
    with pytest.raises(ValidationError):
        logging_controller.write_log(log_name="", message="Test message")


def test_write_log_failure(logging_controller):
    """Test write log failure raises CloudLoggingError."""
    mock_logger = logging_controller._loggers["test-log"]
    mock_logger.log_text.side_effect = Exception("Write failed")

    with pytest.raises(CloudLoggingError):
        logging_controller.write_log(log_name="test-log", message="Test message")


def test_list_entries_success(logging_controller):
    """Test listing log entries successfully."""
    mock_entry = MagicMock()
    mock_entry.log_name = "projects/test-project/logs/test-log"
    mock_entry.payload = "Test message"
    mock_entry.severity = "INFO"
    mock_entry.timestamp = datetime.now()
    mock_entry.resource = MagicMock()
    mock_entry.resource.type = "global"
    mock_entry.resource.labels = {}
    mock_entry.labels = {}
    # Remove http_request and source_location to avoid validation issues
    del mock_entry.http_request
    del mock_entry.source_location

    logging_controller._client.list_entries.return_value = [mock_entry]

    entries = logging_controller.list_entries(filter='severity="ERROR"')

    assert len(entries) == 1
    assert entries[0].log_name == "projects/test-project/logs/test-log"


def test_list_entries_with_max_results(logging_controller):
    """Test listing log entries with max_results."""
    mock_entries = []
    for i in range(10):
        mock_entry = MagicMock()
        mock_entry.log_name = f"projects/test-project/logs/test-log-{i}"
        mock_entry.payload = f"Message {i}"
        mock_entry.severity = "INFO"
        mock_entry.timestamp = datetime.now()
        mock_entry.resource = MagicMock()
        mock_entry.resource.type = "global"
        mock_entry.resource.labels = {}
        mock_entry.labels = {}
        # Remove http_request and source_location to avoid validation issues
        del mock_entry.http_request
        del mock_entry.source_location
        mock_entries.append(mock_entry)

    logging_controller._client.list_entries.return_value = iter(mock_entries)

    entries = logging_controller.list_entries(max_results=5)

    assert len(entries) == 5


def test_list_entries_failure(logging_controller):
    """Test list entries failure raises CloudLoggingError."""
    logging_controller._client.list_entries.side_effect = Exception("List failed")

    with pytest.raises(CloudLoggingError):
        logging_controller.list_entries()


def test_list_entries_for_log_success(logging_controller):
    """Test listing entries for a specific log."""
    mock_entry = MagicMock()
    mock_entry.log_name = "projects/test-project/logs/my-app-log"
    mock_entry.payload = "Test message"
    mock_entry.severity = "INFO"
    mock_entry.timestamp = datetime.now()
    mock_entry.resource = MagicMock()
    mock_entry.resource.type = "global"
    mock_entry.resource.labels = {}
    mock_entry.labels = {}
    # Remove http_request and source_location to avoid validation issues
    del mock_entry.http_request
    del mock_entry.source_location

    logging_controller._client.list_entries.return_value = [mock_entry]

    entries = logging_controller.list_entries_for_log("my-app-log", hours=1)

    assert len(entries) == 1
    logging_controller._client.list_entries.assert_called_once()


def test_list_entries_for_log_with_severity(logging_controller):
    """Test listing entries for a log with severity filter."""
    mock_entry = MagicMock()
    mock_entry.log_name = "projects/test-project/logs/my-app-log"
    mock_entry.payload = "Error message"
    mock_entry.severity = "ERROR"
    mock_entry.timestamp = datetime.now()
    mock_entry.resource = MagicMock()
    mock_entry.resource.type = "global"
    mock_entry.resource.labels = {}
    mock_entry.labels = {}
    # Remove http_request and source_location to avoid validation issues
    del mock_entry.http_request
    del mock_entry.source_location

    logging_controller._client.list_entries.return_value = [mock_entry]

    entries = logging_controller.list_entries_for_log(
        "my-app-log", hours=24, severity=LogSeverity.ERROR
    )

    assert len(entries) == 1


def test_delete_log_success(logging_controller):
    """Test deleting a log successfully."""
    mock_logger = logging_controller._loggers["test-log"]

    logging_controller.delete_log("test-log")

    mock_logger.delete.assert_called_once()
    assert "test-log" not in logging_controller._loggers


def test_delete_log_failure(logging_controller):
    """Test delete log failure raises CloudLoggingError."""
    mock_logger = logging_controller._loggers["test-log"]
    mock_logger.delete.side_effect = Exception("Delete failed")

    with pytest.raises(CloudLoggingError):
        logging_controller.delete_log("test-log")


def test_create_metric_success(logging_controller):
    """Test creating a log metric successfully."""
    mock_metric = MagicMock()
    mock_metric.name = "projects/test-project/metrics/error_count"
    mock_metric.filter = 'severity="ERROR"'
    mock_metric.description = "Error count metric"
    mock_metric.label_extractors = {}

    logging_controller._client.metrics_api.create_log_metric.return_value = mock_metric

    metric = logging_controller.create_metric(
        metric_name="error_count",
        filter='severity="ERROR"',
        description="Error count metric",
    )

    assert metric.name == "error_count"
    assert metric.filter == 'severity="ERROR"'


def test_create_metric_empty_name(logging_controller):
    """Test creating a metric with empty name raises ValidationError."""
    with pytest.raises(ValidationError):
        logging_controller.create_metric(metric_name="", filter='severity="ERROR"')


def test_create_metric_empty_filter(logging_controller):
    """Test creating a metric with empty filter raises ValidationError."""
    with pytest.raises(ValidationError):
        logging_controller.create_metric(metric_name="error_count", filter="")


def test_create_metric_with_label_extractors(logging_controller):
    """Test creating a metric with label extractors."""
    mock_metric = MagicMock()
    mock_metric.name = "projects/test-project/metrics/request_count"
    mock_metric.filter = "httpRequest.status>0"
    mock_metric.description = None
    mock_metric.label_extractors = {"status": "EXTRACT(httpRequest.status)"}
    # Mock metric_descriptor properly
    mock_metric.metric_descriptor = MagicMock()
    del mock_metric.metric_descriptor.metric_kind  # Remove to make hasattr return False
    del mock_metric.metric_descriptor.value_type

    logging_controller._client.metrics_api.create_log_metric.return_value = mock_metric

    metric = logging_controller.create_metric(
        metric_name="request_count",
        filter="httpRequest.status>0",
        label_extractors={"status": "EXTRACT(httpRequest.status)"},
    )

    assert metric.name == "request_count"


def test_create_metric_failure(logging_controller):
    """Test create metric failure raises CloudLoggingError."""
    logging_controller._client.metrics_api.create_log_metric.side_effect = Exception(
        "Create failed"
    )

    with pytest.raises(CloudLoggingError):
        logging_controller.create_metric(
            metric_name="error_count", filter='severity="ERROR"'
        )


def test_get_metric_success(logging_controller):
    """Test getting a metric successfully."""
    mock_metric = MagicMock()
    mock_metric.name = "projects/test-project/metrics/error_count"
    mock_metric.filter = 'severity="ERROR"'
    mock_metric.description = None
    mock_metric.label_extractors = {}
    # Mock metric_descriptor properly
    mock_metric.metric_descriptor = MagicMock()
    del mock_metric.metric_descriptor.metric_kind
    del mock_metric.metric_descriptor.value_type

    logging_controller._client.metrics_api.get_log_metric.return_value = mock_metric

    metric = logging_controller.get_metric("error_count")

    assert metric.name == "error_count"


def test_get_metric_not_found(logging_controller):
    """Test getting a non-existent metric."""
    logging_controller._client.metrics_api.get_log_metric.side_effect = Exception(
        "404 Not Found"
    )

    with pytest.raises(ResourceNotFoundError):
        logging_controller.get_metric("non-existent-metric")


def test_list_metrics_success(logging_controller):
    """Test listing metrics successfully."""
    mock_metric1 = MagicMock()
    mock_metric1.name = "projects/test-project/metrics/error_count"
    mock_metric1.filter = 'severity="ERROR"'
    mock_metric1.description = None
    mock_metric1.label_extractors = {}
    mock_metric1.metric_descriptor = MagicMock()
    del mock_metric1.metric_descriptor.metric_kind
    del mock_metric1.metric_descriptor.value_type

    mock_metric2 = MagicMock()
    mock_metric2.name = "projects/test-project/metrics/warning_count"
    mock_metric2.filter = 'severity="WARNING"'
    mock_metric2.description = None
    mock_metric2.label_extractors = {}
    mock_metric2.metric_descriptor = MagicMock()
    del mock_metric2.metric_descriptor.metric_kind
    del mock_metric2.metric_descriptor.value_type

    logging_controller._client.metrics_api.list_log_metrics.return_value = [
        mock_metric1,
        mock_metric2,
    ]

    metrics = logging_controller.list_metrics()

    assert len(metrics) == 2
    assert metrics[0].name == "error_count"
    assert metrics[1].name == "warning_count"


def test_delete_metric_success(logging_controller):
    """Test deleting a metric successfully."""
    logging_controller._client.metrics_api.delete_log_metric.return_value = None

    logging_controller.delete_metric("error_count")

    logging_controller._client.metrics_api.delete_log_metric.assert_called_once()


def test_delete_metric_failure(logging_controller):
    """Test delete metric failure raises CloudLoggingError."""
    logging_controller._client.metrics_api.delete_log_metric.side_effect = Exception(
        "Delete failed"
    )

    with pytest.raises(CloudLoggingError):
        logging_controller.delete_metric("error_count")


def test_create_sink_success(logging_controller):
    """Test creating a log sink successfully."""
    mock_sink = MagicMock()
    mock_sink.name = "projects/test-project/sinks/error-logs"
    mock_sink.destination = "storage.googleapis.com/my-bucket"
    mock_sink.filter = 'severity="ERROR"'
    mock_sink.description = None
    mock_sink.disabled = False
    mock_sink.include_children = False
    mock_sink.writer_identity = None

    logging_controller._client.sinks_api.create_sink.return_value = mock_sink

    sink = logging_controller.create_sink(
        sink_name="error-logs",
        destination="storage.googleapis.com/my-bucket",
        filter='severity="ERROR"',
    )

    assert sink.name == "error-logs"
    assert sink.destination == "storage.googleapis.com/my-bucket"


def test_create_sink_empty_name(logging_controller):
    """Test creating a sink with empty name raises ValidationError."""
    with pytest.raises(ValidationError):
        logging_controller.create_sink(
            sink_name="", destination="storage.googleapis.com/my-bucket"
        )


def test_create_sink_empty_destination(logging_controller):
    """Test creating a sink with empty destination raises ValidationError."""
    with pytest.raises(ValidationError):
        logging_controller.create_sink(sink_name="error-logs", destination="")


def test_create_sink_with_children(logging_controller):
    """Test creating a sink with include_children."""
    mock_sink = MagicMock()
    mock_sink.name = "projects/test-project/sinks/all-logs"
    mock_sink.destination = "bigquery.googleapis.com/projects/test/datasets/logs"
    mock_sink.filter = None
    mock_sink.description = None
    mock_sink.disabled = False
    mock_sink.include_children = True
    mock_sink.writer_identity = None

    logging_controller._client.sinks_api.create_sink.return_value = mock_sink

    sink = logging_controller.create_sink(
        sink_name="all-logs",
        destination="bigquery.googleapis.com/projects/test/datasets/logs",
        include_children=True,
    )

    assert sink.include_children is True


def test_create_sink_failure(logging_controller):
    """Test create sink failure raises CloudLoggingError."""
    logging_controller._client.sinks_api.create_sink.side_effect = Exception(
        "Create failed"
    )

    with pytest.raises(CloudLoggingError):
        logging_controller.create_sink(
            sink_name="error-logs", destination="storage.googleapis.com/my-bucket"
        )


def test_get_sink_success(logging_controller):
    """Test getting a sink successfully."""
    mock_sink = MagicMock()
    mock_sink.name = "projects/test-project/sinks/error-logs"
    mock_sink.destination = "storage.googleapis.com/my-bucket"
    mock_sink.filter = None
    mock_sink.description = None
    mock_sink.disabled = False
    mock_sink.include_children = False
    mock_sink.writer_identity = None

    logging_controller._client.sinks_api.get_sink.return_value = mock_sink

    sink = logging_controller.get_sink("error-logs")

    assert sink.name == "error-logs"


def test_get_sink_not_found(logging_controller):
    """Test getting a non-existent sink."""
    logging_controller._client.sinks_api.get_sink.side_effect = Exception(
        "404 Not Found"
    )

    with pytest.raises(ResourceNotFoundError):
        logging_controller.get_sink("non-existent-sink")


def test_list_sinks_success(logging_controller):
    """Test listing sinks successfully."""
    mock_sink1 = MagicMock()
    mock_sink1.name = "projects/test-project/sinks/error-logs"
    mock_sink1.destination = "storage.googleapis.com/my-bucket"
    mock_sink1.filter = None
    mock_sink1.description = None
    mock_sink1.disabled = False
    mock_sink1.include_children = False
    mock_sink1.writer_identity = None

    mock_sink2 = MagicMock()
    mock_sink2.name = "projects/test-project/sinks/all-logs"
    mock_sink2.destination = "bigquery.googleapis.com/projects/test/datasets/logs"
    mock_sink2.filter = None
    mock_sink2.description = None
    mock_sink2.disabled = False
    mock_sink2.include_children = True
    mock_sink2.writer_identity = None

    logging_controller._client.sinks_api.list_sinks.return_value = [
        mock_sink1,
        mock_sink2,
    ]

    sinks = logging_controller.list_sinks()

    assert len(sinks) == 2
    assert sinks[0].name == "error-logs"
    assert sinks[1].name == "all-logs"


def test_update_sink_success(logging_controller):
    """Test updating a sink successfully."""
    mock_existing_sink = MagicMock()
    mock_existing_sink.name = "projects/test-project/sinks/error-logs"
    mock_existing_sink.destination = "storage.googleapis.com/my-bucket"
    mock_existing_sink.filter = 'severity="ERROR"'

    mock_updated_sink = MagicMock()
    mock_updated_sink.name = "projects/test-project/sinks/error-logs"
    mock_updated_sink.destination = "storage.googleapis.com/my-bucket"
    mock_updated_sink.filter = 'severity>="WARNING"'
    mock_updated_sink.description = None
    mock_updated_sink.disabled = False
    mock_updated_sink.include_children = False
    mock_updated_sink.writer_identity = None

    logging_controller._client.sinks_api.get_sink.return_value = mock_existing_sink
    logging_controller._client.sinks_api.update_sink.return_value = mock_updated_sink

    sink = logging_controller.update_sink(
        sink_name="error-logs", filter='severity>="WARNING"'
    )

    assert sink.filter == 'severity>="WARNING"'


def test_delete_sink_success(logging_controller):
    """Test deleting a sink successfully."""
    logging_controller._client.sinks_api.delete_sink.return_value = None

    logging_controller.delete_sink("error-logs")

    logging_controller._client.sinks_api.delete_sink.assert_called_once()


def test_delete_sink_failure(logging_controller):
    """Test delete sink failure raises CloudLoggingError."""
    logging_controller._client.sinks_api.delete_sink.side_effect = Exception(
        "Delete failed"
    )

    with pytest.raises(CloudLoggingError):
        logging_controller.delete_sink("error-logs")


def test_controller_initialization_with_settings(settings):
    """Test controller initialization with explicit settings."""
    with patch("google.cloud.logging.Client"):
        controller = CloudLoggingController(settings)
        assert controller.settings.project_id == settings.project_id


def test_controller_initialization_without_settings():
    """Test controller initialization without settings (auto-load)."""
    with patch("google.cloud.logging.Client"):
        controller = CloudLoggingController()
        assert controller.settings is not None


def test_lazy_client_initialization():
    """Test that client is initialized lazily."""
    with patch("google.cloud.logging.Client") as mock_client_class:
        controller = CloudLoggingController()
        # Client should not be initialized yet
        assert controller._client is None

        # Force initialization
        controller._get_client()

        # Now client should be initialized
        assert controller._client is not None
        mock_client_class.assert_called_once()
