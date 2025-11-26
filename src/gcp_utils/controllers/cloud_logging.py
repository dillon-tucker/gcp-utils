"""
Cloud Logging controller for centralized logging and monitoring.

This module provides a high-level interface for writing logs, querying log entries,
creating log-based metrics, and managing log sinks for export.
"""

from datetime import datetime, timedelta
from typing import Any

from google.auth.credentials import Credentials
from google.cloud import logging as cloud_logging

from ..config import GCPSettings, get_settings
from ..exceptions import CloudLoggingError, ResourceNotFoundError, ValidationError
from ..models.cloud_logging import (
    HttpRequestInfo,
    LogEntry,
    LogMetric,
    LogSeverity,
    LogSink,
    SourceLocation,
)


class CloudLoggingController:
    """
    Controller for Google Cloud Logging operations.

    This controller provides methods for writing logs, querying log entries,
    creating metrics, and managing log sinks for centralized logging.

    Example:
        >>> from gcp_utils.controllers import CloudLoggingController
        >>> import logging
        >>>
        >>> # Automatically loads from .env file
        >>> logging_ctrl = CloudLoggingController()
        >>>
        >>> # Recommended: Integrate with Python logging (Google's recommended pattern)
        >>> logging_ctrl.setup_logging()
        >>> logging.info("This goes to Cloud Logging")
        >>>
        >>> # Or write logs directly
        >>> logging_ctrl.write_log(
        ...     log_name="my-app-log",
        ...     message="Application started",
        ...     severity=LogSeverity.INFO
        ... )
        >>>
        >>> # Query logs
        >>> entries = logging_ctrl.list_entries(
        ...     filter='severity>="ERROR"',
        ...     max_results=100
        ... )
    """

    def __init__(
        self,
        settings: GCPSettings | None = None,
        credentials: Credentials | None = None,
    ) -> None:
        """
        Initialize the Cloud Logging controller.

        Args:
            settings: GCP configuration settings. If not provided, loads from environment/.env file.
            credentials: Optional custom credentials

        Raises:
            CloudLoggingError: If client initialization fails
        """
        self.settings = settings or get_settings()
        self._credentials = credentials
        self._client: cloud_logging.Client | None = None
        self._loggers: dict[str, cloud_logging.Logger] = {}

    def _get_client(self) -> cloud_logging.Client:
        """Lazy initialization of the Cloud Logging client."""
        if self._client is None:
            try:
                self._client = cloud_logging.Client(
                    project=self.settings.project_id,
                    credentials=self._credentials,
                )
            except Exception as e:
                raise CloudLoggingError(
                    message=f"Failed to initialize Cloud Logging client: {e}",
                    details={"error": str(e)},
                ) from e
        return self._client

    def _get_logger(self, log_name: str) -> cloud_logging.Logger:
        """
        Get or create a logger instance.

        Args:
            log_name: Name of the log

        Returns:
            Logger instance
        """
        if log_name not in self._loggers:
            client = self._get_client()
            self._loggers[log_name] = client.logger(log_name)
        return self._loggers[log_name]

    def setup_logging(
        self,
        log_level: int = 20,  # logging.INFO
        excluded_loggers: Optional[tuple[str, ...]] = None,
    ) -> None:
        """
        Integrate Google Cloud Logging with Python's standard logging module.

        This is the recommended pattern from Google Cloud documentation. It attaches
        a Cloud Logging handler to Python's root logger, allowing you to use standard
        Python logging (logging.info(), logging.error(), etc.) and have logs appear
        in Google Cloud Logging.

        Args:
            log_level: Minimum log level to capture (default: 20/INFO)
            excluded_loggers: Tuple of logger names to exclude from Cloud Logging

        Raises:
            CloudLoggingError: If setup fails

        Example:
            >>> from gcp_utils.controllers import CloudLoggingController
            >>> import logging
            >>>
            >>> # Setup integration
            >>> logging_ctrl = CloudLoggingController()
            >>> logging_ctrl.setup_logging()
            >>>
            >>> # Now use standard Python logging
            >>> logging.info("This goes to Cloud Logging")
            >>> logging.error("So does this")
            >>>
            >>> # With structured data
            >>> logging.info("User action", extra={"json_fields": {"user_id": "123"}})

        Note:
            This integrates with the Python logging standard library. For direct
            Cloud Logging writes without Python logging integration, use write_log().
        """
        try:
            client = self._get_client()
            client.setup_logging(log_level=log_level, excluded_loggers=excluded_loggers)
        except Exception as e:
            raise CloudLoggingError(
                message=f"Failed to setup Python logging integration: {e}",
                details={"error": str(e)},
            ) from e

    def write_log(
        self,
        log_name: str,
        message: str | dict[str, Any],
        severity: LogSeverity = LogSeverity.INFO,
        labels: dict[str, str] | None = None,
        resource: dict[str, Any] | None = None,
        http_request: HttpRequestInfo | None = None,
        source_location: SourceLocation | None = None,
        trace: str | None = None,
        span_id: str | None = None,
    ) -> None:
        """
        Write a log entry.

        Args:
            log_name: Name of the log (e.g., "my-app-log")
            message: Log message (string or structured dict)
            severity: Log severity level
            labels: Optional labels for the log entry
            resource: Optional monitored resource
            http_request: Optional HTTP request information
            source_location: Optional source code location
            trace: Optional trace ID for distributed tracing
            span_id: Optional span ID for distributed tracing

        Raises:
            ValidationError: If parameters are invalid
            CloudLoggingError: If log writing fails

        Example:
            >>> # Simple text log
            >>> logging_ctrl.write_log("my-app", "User logged in", severity=LogSeverity.INFO)
            >>>
            >>> # Structured JSON log
            >>> logging_ctrl.write_log(
            ...     "my-app",
            ...     {"event": "user_login", "user_id": "123", "ip": "1.2.3.4"},
            ...     severity=LogSeverity.INFO,
            ...     labels={"environment": "production"}
            ... )
        """
        if not log_name:
            raise ValidationError("Log name cannot be empty")

        try:
            logger = self._get_logger(log_name)

            # Build log entry kwargs
            log_kwargs: dict[str, Any] = {
                "severity": severity.value,
            }

            if labels:
                log_kwargs["labels"] = labels

            if resource:
                log_kwargs["resource"] = resource

            if http_request:
                log_kwargs["http_request"] = http_request.model_dump(exclude_none=True)

            if source_location:
                log_kwargs["source_location"] = source_location.model_dump(
                    exclude_none=True
                )

            if trace:
                log_kwargs["trace"] = trace

            if span_id:
                log_kwargs["span_id"] = span_id

            # Write the log
            if isinstance(message, dict):
                logger.log_struct(message, **log_kwargs)
            else:
                logger.log_text(message, **log_kwargs)

        except ValidationError:
            raise
        except Exception as e:
            raise CloudLoggingError(
                message=f"Failed to write log entry to '{log_name}': {e}",
                details={"log_name": log_name, "error": str(e)},
            ) from e

    def write_log_entry(self, entry: LogEntry) -> None:
        """
        Write a complete log entry object.

        Args:
            entry: LogEntry object with all metadata

        Raises:
            CloudLoggingError: If log writing fails

        Example:
            >>> entry = LogEntry(
            ...     log_name="projects/my-project/logs/my-log",
            ...     resource={"type": "global"},
            ...     severity=LogSeverity.INFO,
            ...     json_payload={"message": "Hello world"}
            ... )
            >>> logging_ctrl.write_log_entry(entry)
        """
        try:
            # Extract log name from full path
            log_name = entry.log_name.split("/logs/")[-1]
            logger = self._get_logger(log_name)

            # Determine payload
            payload: str | dict[str, Any]
            if entry.text_payload:
                payload = entry.text_payload
            elif entry.json_payload:
                payload = entry.json_payload
            elif entry.proto_payload:
                payload = entry.proto_payload
            else:
                raise ValidationError("Log entry must have a payload")

            # Build log kwargs
            log_kwargs: dict[str, Any] = {
                "severity": entry.severity.value,
            }

            if entry.labels:
                log_kwargs["labels"] = entry.labels

            if entry.resource:
                log_kwargs["resource"] = entry.resource

            if entry.http_request:
                log_kwargs["http_request"] = entry.http_request.model_dump(
                    exclude_none=True
                )

            if entry.source_location:
                log_kwargs["source_location"] = entry.source_location.model_dump(
                    exclude_none=True
                )

            if entry.trace:
                log_kwargs["trace"] = entry.trace

            if entry.span_id:
                log_kwargs["span_id"] = entry.span_id

            if entry.timestamp:
                log_kwargs["timestamp"] = entry.timestamp

            # Write the log
            if isinstance(payload, dict):
                logger.log_struct(payload, **log_kwargs)
            else:
                logger.log_text(str(payload), **log_kwargs)

        except ValidationError:
            raise
        except Exception as e:
            raise CloudLoggingError(
                message=f"Failed to write log entry: {e}",
                details={"log_name": entry.log_name, "error": str(e)},
            ) from e

    def list_entries(
        self,
        filter: str | None = None,
        order_by: str = "timestamp desc",
        max_results: int | None = None,
        page_size: int = 100,
    ) -> list[LogEntry]:
        """
        List log entries matching the filter.

        Args:
            filter: Advanced logs filter (e.g., 'severity>="ERROR"')
            order_by: Sort order (default: "timestamp desc")
            max_results: Maximum number of entries to return
            page_size: Number of entries per page

        Returns:
            List of LogEntry objects

        Raises:
            CloudLoggingError: If listing fails

        Example:
            >>> # Get recent errors
            >>> entries = logging_ctrl.list_entries(
            ...     filter='severity>="ERROR"',
            ...     max_results=50
            ... )
            >>>
            >>> # Get logs from specific resource
            >>> entries = logging_ctrl.list_entries(
            ...     filter='resource.type="gce_instance" AND resource.labels.instance_id="123"'
            ... )
            >>>
            >>> # Get logs from time range
            >>> entries = logging_ctrl.list_entries(
            ...     filter='timestamp>="2024-01-01T00:00:00Z" AND timestamp<"2024-01-02T00:00:00Z"'
            ... )
        """
        try:
            client = self._get_client()

            # Build filter
            project_filter = 'resource.type!=""'  # Basic filter
            if filter:
                project_filter = f"({filter})"

            # List entries
            iterator = client.list_entries(
                filter_=project_filter,
                order_by=order_by,
                page_size=page_size,
            )

            # Collect results
            results: list[LogEntry] = []
            for entry in iterator:
                log_entry = self._convert_entry(entry)
                results.append(log_entry)

                if max_results and len(results) >= max_results:
                    break

            return results

        except Exception as e:
            raise CloudLoggingError(
                message=f"Failed to list log entries: {e}",
                details={"filter": filter, "error": str(e)},
            ) from e

    def list_entries_for_log(
        self,
        log_name: str,
        hours: int = 24,
        severity: LogSeverity | None = None,
        max_results: int | None = None,
    ) -> list[LogEntry]:
        """
        List entries for a specific log.

        Args:
            log_name: Name of the log
            hours: Number of hours to look back (default: 24)
            severity: Optional minimum severity filter
            max_results: Maximum number of entries to return

        Returns:
            List of LogEntry objects

        Raises:
            CloudLoggingError: If listing fails

        Example:
            >>> # Get last 24 hours of logs
            >>> entries = logging_ctrl.list_entries_for_log("my-app-log")
            >>>
            >>> # Get errors from last hour
            >>> entries = logging_ctrl.list_entries_for_log(
            ...     "my-app-log",
            ...     hours=1,
            ...     severity=LogSeverity.ERROR
            ... )
        """
        try:
            # Build time filter
            from datetime import UTC

            start_time = datetime.now(UTC) - timedelta(hours=hours)
            time_filter = f'timestamp>="{start_time.isoformat()}Z"'

            # Build log name filter
            log_filter = (
                f'logName="projects/{self.settings.project_id}/logs/{log_name}"'
            )

            # Build severity filter
            filters = [log_filter, time_filter]
            if severity:
                filters.append(f'severity>="{severity.value}"')

            combined_filter = " AND ".join(filters)

            return self.list_entries(
                filter=combined_filter,
                max_results=max_results,
            )

        except Exception as e:
            raise CloudLoggingError(
                message=f"Failed to list entries for log '{log_name}': {e}",
                details={"log_name": log_name, "error": str(e)},
            ) from e

    def delete_log(self, log_name: str) -> None:
        """
        Delete all entries in a log.

        Args:
            log_name: Name of the log to delete

        Raises:
            CloudLoggingError: If deletion fails

        Example:
            >>> logging_ctrl.delete_log("my-app-log")
        """
        try:
            logger = self._get_logger(log_name)
            logger.delete()

            # Remove from cache
            if log_name in self._loggers:
                del self._loggers[log_name]

        except Exception as e:
            raise CloudLoggingError(
                message=f"Failed to delete log '{log_name}': {e}",
                details={"log_name": log_name, "error": str(e)},
            ) from e

    def create_metric(
        self,
        metric_name: str,
        filter: str,
        description: str | None = None,
        metric_kind: str | None = None,
        value_type: str | None = None,
        label_extractors: dict[str, str] | None = None,
    ) -> LogMetric:
        """
        Create a logs-based metric.

        Args:
            metric_name: Metric name
            filter: Log filter expression
            description: Metric description
            metric_kind: Metric kind (DELTA, GAUGE, CUMULATIVE)
            value_type: Value type (INT64, DOUBLE, DISTRIBUTION)
            label_extractors: Label value extraction patterns

        Returns:
            LogMetric object

        Raises:
            ValidationError: If parameters are invalid
            CloudLoggingError: If metric creation fails

        Example:
            >>> # Count error logs
            >>> metric = logging_ctrl.create_metric(
            ...     metric_name="error_count",
            ...     filter='severity="ERROR"',
            ...     description="Count of error-level log entries"
            ... )
            >>>
            >>> # Extract labels from logs
            >>> metric = logging_ctrl.create_metric(
            ...     metric_name="request_count_by_status",
            ...     filter='httpRequest.status>0',
            ...     label_extractors={"status": "EXTRACT(httpRequest.status)"}
            ... )
        """
        if not metric_name:
            raise ValidationError("Metric name cannot be empty")

        if not filter:
            raise ValidationError("Filter cannot be empty")

        try:
            client = self._get_client()

            # Build metric descriptor
            from google.cloud.logging_v2.types import LogMetric as GCPLogMetric

            metric_proto = GCPLogMetric(
                name=metric_name,
                filter=filter,
            )

            if description:
                metric_proto.description = description

            if metric_kind:
                metric_proto.metric_descriptor.metric_kind = metric_kind

            if value_type:
                metric_proto.metric_descriptor.value_type = value_type

            if label_extractors:
                metric_proto.label_extractors = label_extractors

            # Create the metric
            created_metric = client.metrics_api.create_log_metric(
                parent=f"projects/{self.settings.project_id}",
                metric=metric_proto,
            )

            return self._convert_metric(created_metric)

        except ValidationError:
            raise
        except Exception as e:
            raise CloudLoggingError(
                message=f"Failed to create metric '{metric_name}': {e}",
                details={"metric_name": metric_name, "error": str(e)},
            ) from e

    def get_metric(self, metric_name: str) -> LogMetric:
        """
        Get a logs-based metric.

        Args:
            metric_name: Metric name

        Returns:
            LogMetric object

        Raises:
            ResourceNotFoundError: If metric doesn't exist
            CloudLoggingError: If retrieval fails

        Example:
            >>> metric = logging_ctrl.get_metric("error_count")
            >>> print(f"Filter: {metric.filter}")
        """
        try:
            client = self._get_client()

            metric = client.metrics_api.get_log_metric(
                metric_name=f"projects/{self.settings.project_id}/metrics/{metric_name}"
            )

            return self._convert_metric(metric)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Metric '{metric_name}' not found",
                    details={"metric_name": metric_name},
                ) from e
            raise CloudLoggingError(
                message=f"Failed to get metric '{metric_name}': {e}",
                details={"metric_name": metric_name, "error": str(e)},
            ) from e

    def list_metrics(self) -> list[LogMetric]:
        """
        List all logs-based metrics.

        Returns:
            List of LogMetric objects

        Raises:
            CloudLoggingError: If listing fails

        Example:
            >>> metrics = logging_ctrl.list_metrics()
            >>> for metric in metrics:
            ...     print(f"{metric.name}: {metric.description}")
        """
        try:
            client = self._get_client()

            metrics = client.metrics_api.list_log_metrics(
                parent=f"projects/{self.settings.project_id}"
            )

            return [self._convert_metric(metric) for metric in metrics]

        except Exception as e:
            raise CloudLoggingError(
                message=f"Failed to list metrics: {e}",
                details={"error": str(e)},
            ) from e

    def delete_metric(self, metric_name: str) -> None:
        """
        Delete a logs-based metric.

        Args:
            metric_name: Metric name

        Raises:
            CloudLoggingError: If deletion fails

        Example:
            >>> logging_ctrl.delete_metric("error_count")
        """
        try:
            client = self._get_client()

            client.metrics_api.delete_log_metric(
                metric_name=f"projects/{self.settings.project_id}/metrics/{metric_name}"
            )

        except Exception as e:
            raise CloudLoggingError(
                message=f"Failed to delete metric '{metric_name}': {e}",
                details={"metric_name": metric_name, "error": str(e)},
            ) from e

    def create_sink(
        self,
        sink_name: str,
        destination: str,
        filter: str | None = None,
        include_children: bool = False,
    ) -> LogSink:
        """
        Create a log sink for exporting logs.

        Args:
            sink_name: Sink name
            destination: Destination URI (storage, bigquery, pubsub)
            filter: Optional log filter expression
            include_children: Include logs from child resources

        Returns:
            LogSink object

        Raises:
            ValidationError: If parameters are invalid
            CloudLoggingError: If sink creation fails

        Example:
            >>> # Export to Cloud Storage
            >>> sink = logging_ctrl.create_sink(
            ...     sink_name="error-logs-sink",
            ...     destination="storage.googleapis.com/my-logs-bucket",
            ...     filter='severity>="ERROR"'
            ... )
            >>>
            >>> # Export to BigQuery
            >>> sink = logging_ctrl.create_sink(
            ...     sink_name="all-logs-sink",
            ...     destination="bigquery.googleapis.com/projects/my-project/datasets/logs"
            ... )
            >>>
            >>> # Export to Pub/Sub
            >>> sink = logging_ctrl.create_sink(
            ...     sink_name="realtime-logs-sink",
            ...     destination="pubsub.googleapis.com/projects/my-project/topics/logs"
            ... )
        """
        if not sink_name:
            raise ValidationError("Sink name cannot be empty")

        if not destination:
            raise ValidationError("Destination cannot be empty")

        try:
            client = self._get_client()

            from google.cloud.logging_v2.types import LogSink as GCPLogSink

            sink_proto = GCPLogSink(
                name=sink_name,
                destination=destination,
                include_children=include_children,
            )

            if filter:
                sink_proto.filter = filter

            created_sink = client.sinks_api.create_sink(
                parent=f"projects/{self.settings.project_id}",
                sink=sink_proto,
            )

            return self._convert_sink(created_sink)

        except ValidationError:
            raise
        except Exception as e:
            raise CloudLoggingError(
                message=f"Failed to create sink '{sink_name}': {e}",
                details={"sink_name": sink_name, "error": str(e)},
            ) from e

    def get_sink(self, sink_name: str) -> LogSink:
        """
        Get a log sink.

        Args:
            sink_name: Sink name

        Returns:
            LogSink object

        Raises:
            ResourceNotFoundError: If sink doesn't exist
            CloudLoggingError: If retrieval fails

        Example:
            >>> sink = logging_ctrl.get_sink("error-logs-sink")
            >>> print(f"Destination: {sink.destination}")
        """
        try:
            client = self._get_client()

            sink = client.sinks_api.get_sink(
                sink_name=f"projects/{self.settings.project_id}/sinks/{sink_name}"
            )

            return self._convert_sink(sink)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Sink '{sink_name}' not found",
                    details={"sink_name": sink_name},
                ) from e
            raise CloudLoggingError(
                message=f"Failed to get sink '{sink_name}': {e}",
                details={"sink_name": sink_name, "error": str(e)},
            ) from e

    def list_sinks(self) -> list[LogSink]:
        """
        List all log sinks.

        Returns:
            List of LogSink objects

        Raises:
            CloudLoggingError: If listing fails

        Example:
            >>> sinks = logging_ctrl.list_sinks()
            >>> for sink in sinks:
            ...     print(f"{sink.name} -> {sink.destination}")
        """
        try:
            client = self._get_client()

            sinks = client.sinks_api.list_sinks(
                parent=f"projects/{self.settings.project_id}"
            )

            return [self._convert_sink(sink) for sink in sinks]

        except Exception as e:
            raise CloudLoggingError(
                message=f"Failed to list sinks: {e}",
                details={"error": str(e)},
            ) from e

    def update_sink(
        self,
        sink_name: str,
        destination: str | None = None,
        filter: str | None = None,
    ) -> LogSink:
        """
        Update a log sink.

        Args:
            sink_name: Sink name
            destination: New destination (optional)
            filter: New filter (optional)

        Returns:
            Updated LogSink object

        Raises:
            CloudLoggingError: If update fails

        Example:
            >>> sink = logging_ctrl.update_sink(
            ...     sink_name="error-logs-sink",
            ...     filter='severity>="WARNING"'
            ... )
        """
        try:
            client = self._get_client()

            # Get existing sink
            sink_path = f"projects/{self.settings.project_id}/sinks/{sink_name}"
            existing_sink = client.sinks_api.get_sink(sink_name=sink_path)

            # Update fields
            if destination:
                existing_sink.destination = destination

            if filter is not None:
                existing_sink.filter = filter

            # Update the sink
            updated_sink = client.sinks_api.update_sink(
                sink_name=sink_path,
                sink=existing_sink,
            )

            return self._convert_sink(updated_sink)

        except Exception as e:
            raise CloudLoggingError(
                message=f"Failed to update sink '{sink_name}': {e}",
                details={"sink_name": sink_name, "error": str(e)},
            ) from e

    def delete_sink(self, sink_name: str) -> None:
        """
        Delete a log sink.

        Args:
            sink_name: Sink name

        Raises:
            CloudLoggingError: If deletion fails

        Example:
            >>> logging_ctrl.delete_sink("error-logs-sink")
        """
        try:
            client = self._get_client()

            client.sinks_api.delete_sink(
                sink_name=f"projects/{self.settings.project_id}/sinks/{sink_name}"
            )

        except Exception as e:
            raise CloudLoggingError(
                message=f"Failed to delete sink '{sink_name}': {e}",
                details={"sink_name": sink_name, "error": str(e)},
            ) from e

    def _convert_entry(self, entry: Any) -> LogEntry:
        """Convert a Cloud Logging entry to LogEntry model."""
        # Extract payload
        text_payload = None
        json_payload = None
        proto_payload = None

        if hasattr(entry, "payload") and entry.payload:
            if isinstance(entry.payload, str):
                text_payload = entry.payload
            elif isinstance(entry.payload, dict):
                json_payload = entry.payload
            else:
                proto_payload = entry.payload

        # Extract resource
        resource = {}
        if hasattr(entry, "resource") and entry.resource:
            resource = {
                "type": entry.resource.type if hasattr(entry.resource, "type") else "",
                "labels": (
                    dict(entry.resource.labels)
                    if hasattr(entry.resource, "labels")
                    else {}
                ),
            }

        # Extract HTTP request
        http_request = None
        if hasattr(entry, "http_request") and entry.http_request:
            http_req = entry.http_request

            # Helper to safely extract string attributes
            def get_str_val(obj: Any, attr: str) -> str | None:
                val = getattr(obj, attr, None)
                return val if isinstance(val, str) else None

            # Helper to safely extract numeric attributes
            def get_num_val(obj: Any, attr: str) -> int | float | None:
                val = getattr(obj, attr, None)
                return val if isinstance(val, (int, float)) else None

            # Helper to safely extract int attributes
            def get_int_val(obj: Any, attr: str) -> int | None:
                val = getattr(obj, attr, None)
                if isinstance(val, int):
                    return val
                elif isinstance(val, float):
                    return int(val)
                return None

            # Helper to safely extract boolean attributes
            def get_bool_val(obj: Any, attr: str) -> bool | None:
                val = getattr(obj, attr, None)
                return val if isinstance(val, bool) else None

            http_request = HttpRequestInfo(
                request_method=get_str_val(http_req, "request_method"),
                request_url=get_str_val(http_req, "request_url"),
                request_size=get_int_val(http_req, "request_size"),
                status=get_int_val(http_req, "status"),
                response_size=get_int_val(http_req, "response_size"),
                user_agent=get_str_val(http_req, "user_agent"),
                remote_ip=get_str_val(http_req, "remote_ip"),
                server_ip=get_str_val(http_req, "server_ip"),
                referer=get_str_val(http_req, "referer"),
                latency=get_num_val(http_req, "latency"),
                cache_lookup=get_bool_val(http_req, "cache_lookup"),
                cache_hit=get_bool_val(http_req, "cache_hit"),
                cache_validated_with_origin_server=get_bool_val(
                    http_req, "cache_validated_with_origin_server"
                ),
            )

        # Extract source location
        source_location = None
        if hasattr(entry, "source_location") and entry.source_location:
            src_loc = entry.source_location

            # Helper to safely extract string attributes
            def get_str_val(obj: Any, attr: str) -> str | None:
                val = getattr(obj, attr, None)
                return val if isinstance(val, str) else None

            # Helper to safely extract int attributes
            def get_int_val(obj: Any, attr: str) -> int | None:
                val = getattr(obj, attr, None)
                return val if isinstance(val, int) else None

            source_location = SourceLocation(
                file=get_str_val(src_loc, "file"),
                line=get_int_val(src_loc, "line"),
                function=get_str_val(src_loc, "function"),
            )

        # Determine severity
        severity = LogSeverity.DEFAULT
        if hasattr(entry, "severity"):
            try:
                severity = LogSeverity(entry.severity)
            except ValueError:
                severity = LogSeverity.DEFAULT

        # Handle timestamps - keep as datetime objects
        timestamp_val = None
        if hasattr(entry, "timestamp") and entry.timestamp:
            if isinstance(entry.timestamp, datetime):
                timestamp_val = entry.timestamp
            elif hasattr(entry.timestamp, "isoformat"):
                # It's a protobuf timestamp, try to convert
                timestamp_val = entry.timestamp

        receive_timestamp_val = None
        if hasattr(entry, "receive_timestamp") and entry.receive_timestamp:
            if isinstance(entry.receive_timestamp, datetime):
                receive_timestamp_val = entry.receive_timestamp
            elif hasattr(entry.receive_timestamp, "isoformat"):
                # It's a protobuf timestamp, try to convert
                receive_timestamp_val = entry.receive_timestamp

        # Helper to safely get string attribute from entry
        def get_entry_str_attr(attr: str) -> str | None:
            if hasattr(entry, attr):
                val = getattr(entry, attr)
                return val if isinstance(val, str) else None
            return None

        # Helper to safely get bool attribute from entry
        def get_entry_bool_attr(attr: str) -> bool | None:
            if hasattr(entry, attr):
                val = getattr(entry, attr)
                return val if isinstance(val, bool) else None
            return None

        log_entry = LogEntry(
            log_name=entry.log_name if hasattr(entry, "log_name") else "",
            resource=resource,
            timestamp=timestamp_val,
            receive_timestamp=receive_timestamp_val,
            severity=severity,
            insert_id=get_entry_str_attr("insert_id"),
            labels=dict(entry.labels) if hasattr(entry, "labels") else {},
            text_payload=text_payload,
            json_payload=json_payload,
            proto_payload=proto_payload,
            http_request=http_request,
            source_location=source_location,
            operation_id=get_entry_str_attr("operation_id"),
            operation_producer=get_entry_str_attr("operation_producer"),
            operation_first=get_entry_bool_attr("operation_first"),
            operation_last=get_entry_bool_attr("operation_last"),
            trace=get_entry_str_attr("trace"),
            span_id=get_entry_str_attr("span_id"),
            trace_sampled=get_entry_bool_attr("trace_sampled"),
        )

        # Bind the native object
        log_entry._entry_object = entry

        return log_entry

    def _convert_metric(self, metric: Any) -> LogMetric:
        """Convert a GCP log metric to LogMetric model."""

        # Helper to safely get string attribute
        def get_str_attr(obj: Any, attr: str) -> str | None:
            if hasattr(obj, attr):
                val = getattr(obj, attr)
                return val if isinstance(val, str) else None
            return None

        return LogMetric(
            name=metric.name.split("/")[-1] if "/" in metric.name else metric.name,
            description=get_str_attr(metric, "description"),
            filter=metric.filter,
            metric_kind=(
                str(metric.metric_descriptor.metric_kind)
                if hasattr(metric, "metric_descriptor")
                and hasattr(metric.metric_descriptor, "metric_kind")
                else None
            ),
            value_type=(
                str(metric.metric_descriptor.value_type)
                if hasattr(metric, "metric_descriptor")
                and hasattr(metric.metric_descriptor, "value_type")
                else None
            ),
            label_extractors=(
                dict(metric.label_extractors)
                if hasattr(metric, "label_extractors")
                and isinstance(metric.label_extractors, dict)
                else {}
            ),
            bucket_options=(
                dict(metric.bucket_options)
                if hasattr(metric, "bucket_options") and metric.bucket_options
                else None
            ),
        )

    def _convert_sink(self, sink: Any) -> LogSink:
        """Convert a GCP log sink to LogSink model."""

        # Helper to safely get string attribute
        def get_str_attr(obj: Any, attr: str) -> str | None:
            if hasattr(obj, attr):
                val = getattr(obj, attr)
                return val if isinstance(val, str) else None
            return None

        # Helper to safely get datetime attribute
        def get_datetime_attr(obj: Any, attr: str) -> datetime | None:
            if hasattr(obj, attr):
                val = getattr(obj, attr)
                if isinstance(val, datetime):
                    return val
            return None

        return LogSink(
            name=sink.name.split("/")[-1] if "/" in sink.name else sink.name,
            destination=sink.destination,
            filter=get_str_attr(sink, "filter"),
            description=get_str_attr(sink, "description"),
            disabled=(
                sink.disabled
                if hasattr(sink, "disabled") and isinstance(sink.disabled, bool)
                else False
            ),
            include_children=(
                sink.include_children
                if hasattr(sink, "include_children")
                and isinstance(sink.include_children, bool)
                else False
            ),
            writer_identity=get_str_attr(sink, "writer_identity"),
            create_time=get_datetime_attr(sink, "create_time"),
            update_time=get_datetime_attr(sink, "update_time"),
        )
