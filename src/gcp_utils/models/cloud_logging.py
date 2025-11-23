"""Data models for Cloud Logging operations."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

if TYPE_CHECKING:
    from google.cloud.logging_v2 import entries


class LogSeverity(str, Enum):
    """
    Log entry severity levels.

    Follows the RFC 5424 syslog severity levels.
    """

    DEFAULT = "DEFAULT"
    DEBUG = "DEBUG"
    INFO = "INFO"
    NOTICE = "NOTICE"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    ALERT = "ALERT"
    EMERGENCY = "EMERGENCY"


class HttpRequestInfo(BaseModel):
    """HTTP request information for structured logs."""

    request_method: str | None = Field(None, description="HTTP request method")
    request_url: str | None = Field(None, description="Request URL")
    request_size: int | None = Field(None, description="Request size in bytes")
    status: int | None = Field(None, description="HTTP status code")
    response_size: int | None = Field(None, description="Response size in bytes")
    user_agent: str | None = Field(None, description="User agent string")
    remote_ip: str | None = Field(None, description="Client IP address")
    server_ip: str | None = Field(None, description="Server IP address")
    referer: str | None = Field(None, description="Referer URL")
    latency: float | None = Field(None, description="Request latency in seconds")
    cache_lookup: bool | None = Field(None, description="Whether a cache lookup was made")
    cache_hit: bool | None = Field(None, description="Whether a cache hit occurred")
    cache_validated_with_origin_server: bool | None = Field(
        None, description="Whether cache was validated with origin"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SourceLocation(BaseModel):
    """Source code location information."""

    file: str | None = Field(None, description="Source file name")
    line: int | None = Field(None, description="Line number")
    function: str | None = Field(None, description="Function name")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class LogEntry(BaseModel):
    """
    A log entry with structured metadata.

    This model represents a Cloud Logging entry with all associated
    metadata, labels, and payload information.

    Example:
        >>> entry = LogEntry(
        ...     log_name="projects/my-project/logs/my-log",
        ...     resource={"type": "gce_instance", "labels": {"instance_id": "123"}},
        ...     severity=LogSeverity.INFO,
        ...     text_payload="Application started"
        ... )
    """

    log_name: str = Field(..., description="Full log name path")
    resource: dict[str, Any] = Field(..., description="Monitored resource")
    timestamp: datetime | None = Field(None, description="Log entry timestamp")
    receive_timestamp: datetime | None = Field(None, description="Time entry was received")
    severity: LogSeverity = Field(LogSeverity.DEFAULT, description="Entry severity")
    insert_id: str | None = Field(None, description="Unique entry ID")
    labels: dict[str, str] = Field(default_factory=dict, description="User-defined labels")

    # Payload - exactly one should be set
    text_payload: str | None = Field(None, description="Text log entry")
    json_payload: dict[str, Any] | None = Field(None, description="Structured JSON log")
    proto_payload: dict[str, Any] | None = Field(None, description="Protocol buffer payload")

    # HTTP request information
    http_request: HttpRequestInfo | None = Field(None, description="HTTP request metadata")

    # Source location
    source_location: SourceLocation | None = Field(None, description="Source code location")

    # Operation information
    operation_id: str | None = Field(None, description="Operation ID")
    operation_producer: str | None = Field(None, description="Operation producer")
    operation_first: bool | None = Field(None, description="First entry in operation")
    operation_last: bool | None = Field(None, description="Last entry in operation")

    # Trace and span information
    trace: str | None = Field(None, description="Trace ID")
    span_id: str | None = Field(None, description="Span ID")
    trace_sampled: bool | None = Field(None, description="Whether trace is sampled")

    # The actual log entry object (private attribute, not serialized)
    _entry_object: Optional["entries.StructEntry"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the log entry to a dictionary suitable for API calls.

        Returns:
            Dictionary representation of the log entry
        """
        entry_dict: dict[str, Any] = {
            "log_name": self.log_name,
            "resource": self.resource,
            "severity": self.severity.value,
        }

        if self.timestamp:
            entry_dict["timestamp"] = self.timestamp.isoformat()

        if self.labels:
            entry_dict["labels"] = self.labels

        if self.text_payload:
            entry_dict["text_payload"] = self.text_payload
        elif self.json_payload:
            entry_dict["json_payload"] = self.json_payload
        elif self.proto_payload:
            entry_dict["proto_payload"] = self.proto_payload

        if self.http_request:
            entry_dict["http_request"] = self.http_request.model_dump(exclude_none=True)

        if self.source_location:
            entry_dict["source_location"] = self.source_location.model_dump(exclude_none=True)

        if self.trace:
            entry_dict["trace"] = self.trace

        if self.span_id:
            entry_dict["span_id"] = self.span_id

        return entry_dict


class LogMetric(BaseModel):
    """
    A logs-based metric definition.

    Log metrics extract data from logs to create custom metrics
    that can be used for monitoring and alerting.

    Example:
        >>> metric = LogMetric(
        ...     name="error_count",
        ...     filter='severity="ERROR"',
        ...     description="Count of error-level log entries"
        ... )
    """

    name: str = Field(..., description="Metric name")
    description: str | None = Field(None, description="Metric description")
    filter: str = Field(..., description="Log filter expression")
    metric_kind: str | None = Field(None, description="Metric kind (DELTA, GAUGE, CUMULATIVE)")
    value_type: str | None = Field(None, description="Value type (INT64, DOUBLE, DISTRIBUTION)")
    labels: dict[str, str] = Field(default_factory=dict, description="Metric labels")
    label_extractors: dict[str, str] = Field(
        default_factory=dict,
        description="Label value extraction patterns"
    )
    bucket_options: dict[str, Any] | None = Field(None, description="Distribution bucket options")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class LogSink(BaseModel):
    """
    A log sink for exporting logs to external destinations.

    Sinks export logs to Cloud Storage, BigQuery, Pub/Sub, or
    other supported destinations.

    Example:
        >>> sink = LogSink(
        ...     name="my-sink",
        ...     destination="storage.googleapis.com/my-bucket",
        ...     filter='severity>="ERROR"'
        ... )
    """

    name: str = Field(..., description="Sink name")
    destination: str = Field(..., description="Destination (storage, bigquery, pubsub)")
    filter: str | None = Field(None, description="Log filter expression")
    description: str | None = Field(None, description="Sink description")
    disabled: bool = Field(default=False, description="Whether sink is disabled")
    include_children: bool = Field(
        default=False,
        description="Include logs from child resources"
    )
    writer_identity: str | None = Field(None, description="Service account for writing")
    create_time: datetime | None = Field(None, description="Sink creation time")
    update_time: datetime | None = Field(None, description="Last update time")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class LoggerInfo(BaseModel):
    """
    Information about a logger.

    Represents a named logger that writes to Cloud Logging.
    """

    name: str = Field(..., description="Logger name")
    resource: dict[str, Any] | None = Field(None, description="Default monitored resource")
    labels: dict[str, str] = Field(default_factory=dict, description="Default labels")

    model_config = ConfigDict(arbitrary_types_allowed=True)
