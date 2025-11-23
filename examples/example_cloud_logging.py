"""
Example usage of CloudLoggingController.

This example demonstrates how to use the Cloud Logging controller for:
- Writing simple and structured logs
- Querying and filtering log entries
- Creating logs-based metrics
- Managing log sinks for export
- Working with distributed tracing

Prerequisites:
- Valid GCP project with Cloud Logging API enabled
- Proper authentication (service account or application default credentials)
- .env file with GCP_PROJECT_ID set

Installation:
    pip install gcp-utils[logging]
"""

from datetime import datetime

from gcp_utils.controllers import CloudLoggingController
from gcp_utils.models.cloud_logging import (
    HttpRequestInfo,
    LogEntry,
    LogSeverity,
    SourceLocation,
)


def main() -> None:
    """Demonstrate Cloud Logging operations."""

    # Initialize the controller (automatically loads from .env)
    logging_ctrl = CloudLoggingController()

    print("=" * 80)
    print("Cloud Logging Controller Example")
    print("=" * 80)

    # ========================================================================
    # 1. WRITING LOGS
    # ========================================================================
    print("\n1. WRITING LOGS")
    print("-" * 80)

    # Simple text log
    print("\n→ Writing simple text log...")
    logging_ctrl.write_log(
        log_name="example-app-log",
        message="Application started successfully",
        severity=LogSeverity.INFO,
    )
    print("✓ Text log written")

    # Structured JSON log
    print("\n→ Writing structured JSON log...")
    logging_ctrl.write_log(
        log_name="example-app-log",
        message={
            "event": "user_login",
            "user_id": "user-123",
            "ip_address": "192.168.1.1",
            "timestamp": datetime.utcnow().isoformat(),
        },
        severity=LogSeverity.INFO,
        labels={"environment": "production", "version": "1.0.0"},
    )
    print("✓ Structured log written")

    # Log with HTTP request information
    print("\n→ Writing log with HTTP request metadata...")
    http_request = HttpRequestInfo(
        request_method="GET",
        request_url="https://example.com/api/users",
        status=200,
        response_size=1024,
        user_agent="Mozilla/5.0",
        remote_ip="192.168.1.1",
        latency=0.125,
    )

    logging_ctrl.write_log(
        log_name="example-app-log",
        message="API request completed",
        severity=LogSeverity.INFO,
        http_request=http_request,
    )
    print("✓ HTTP request log written")

    # Log with source location
    print("\n→ Writing log with source code location...")
    source_location = SourceLocation(
        file="example_cloud_logging.py", line=85, function="main"
    )

    logging_ctrl.write_log(
        log_name="example-app-log",
        message="Debug checkpoint reached",
        severity=LogSeverity.DEBUG,
        source_location=source_location,
    )
    print("✓ Log with source location written")

    # Log with distributed tracing
    print("\n→ Writing log with trace information...")
    logging_ctrl.write_log(
        log_name="example-app-log",
        message="Processing request in microservice",
        severity=LogSeverity.INFO,
        trace="projects/my-project/traces/abc123",
        span_id="span456",
    )
    print("✓ Log with trace info written")

    # Error log
    print("\n→ Writing error log...")
    logging_ctrl.write_log(
        log_name="example-app-log",
        message={
            "error": "Database connection failed",
            "error_code": "DB_CONN_001",
            "details": "Connection timeout after 30 seconds",
        },
        severity=LogSeverity.ERROR,
        labels={"component": "database", "severity": "high"},
    )
    print("✓ Error log written")

    # ========================================================================
    # 2. QUERYING LOGS
    # ========================================================================
    print("\n2. QUERYING LOGS")
    print("-" * 80)

    # Query recent error logs
    print("\n→ Querying error logs from last 24 hours...")
    try:
        error_entries = logging_ctrl.list_entries(
            filter='severity>="ERROR"', max_results=10
        )
        print(f"✓ Found {len(error_entries)} error entries")
        for entry in error_entries[:3]:  # Show first 3
            print(f"  • {entry.severity.value}: {entry.log_name}")
    except Exception as e:
        print(f"✗ Query failed: {e}")

    # Query logs for specific application
    print("\n→ Querying logs for example-app-log (last hour)...")
    try:
        app_entries = logging_ctrl.list_entries_for_log(
            log_name="example-app-log", hours=1, max_results=5
        )
        print(f"✓ Found {len(app_entries)} entries for example-app-log")
        for entry in app_entries:
            print(
                f"  • {entry.severity.value}: "
                f"{entry.text_payload or entry.json_payload}"
            )
    except Exception as e:
        print(f"✗ Query failed: {e}")

    # Query logs with advanced filter
    print("\n→ Querying logs with advanced filter...")
    try:
        # Filter for logs from specific resource and severity
        advanced_filter = (
            'resource.type="gce_instance" '
            'AND severity>="WARNING" '
            'AND labels.environment="production"'
        )
        filtered_entries = logging_ctrl.list_entries(
            filter=advanced_filter, max_results=10
        )
        print(f"✓ Found {len(filtered_entries)} entries matching advanced filter")
    except Exception as e:
        print(f"✗ Query failed: {e}")

    # ========================================================================
    # 3. LOGS-BASED METRICS
    # ========================================================================
    print("\n3. LOGS-BASED METRICS")
    print("-" * 80)

    # Create error count metric
    print("\n→ Creating error count metric...")
    try:
        error_metric = logging_ctrl.create_metric(
            metric_name="example_error_count",
            filter='severity>="ERROR"',
            description="Count of error-level log entries",
        )
        print(f"✓ Created metric: {error_metric.name}")
        print(f"  Filter: {error_metric.filter}")
    except Exception as e:
        print(f"✗ Metric already exists or creation failed: {e}")

    # Create metric with label extractors
    print("\n→ Creating metric with label extractors...")
    try:
        request_metric = logging_ctrl.create_metric(
            metric_name="example_http_requests_by_status",
            filter="httpRequest.status>0",
            description="HTTP requests by status code",
            label_extractors={"status": "EXTRACT(httpRequest.status)"},
        )
        print(f"✓ Created metric: {request_metric.name}")
        print(f"  Label extractors: {request_metric.label_extractors}")
    except Exception as e:
        print(f"✗ Metric already exists or creation failed: {e}")

    # List all metrics
    print("\n→ Listing all metrics...")
    try:
        metrics = logging_ctrl.list_metrics()
        print(f"✓ Found {len(metrics)} metrics:")
        for metric in metrics:
            print(f"  • {metric.name}: {metric.description or 'No description'}")
    except Exception as e:
        print(f"✗ Failed to list metrics: {e}")

    # Get specific metric
    print("\n→ Getting specific metric...")
    try:
        metric = logging_ctrl.get_metric("example_error_count")
        print(f"✓ Retrieved metric: {metric.name}")
        print(f"  Filter: {metric.filter}")
        print(f"  Description: {metric.description}")
    except Exception as e:
        print(f"✗ Failed to get metric: {e}")

    # ========================================================================
    # 4. LOG SINKS (EXPORT)
    # ========================================================================
    print("\n4. LOG SINKS (EXPORT)")
    print("-" * 80)

    # Create sink to Cloud Storage
    print("\n→ Creating sink to export errors to Cloud Storage...")
    try:
        storage_sink = logging_ctrl.create_sink(
            sink_name="example-error-logs-sink",
            destination="storage.googleapis.com/my-logs-bucket",
            filter='severity>="ERROR"',
        )
        print(f"✓ Created sink: {storage_sink.name}")
        print(f"  Destination: {storage_sink.destination}")
        print(f"  Filter: {storage_sink.filter}")
        print(
            f"  Writer identity: {storage_sink.writer_identity or 'Not yet assigned'}"
        )
    except Exception as e:
        print(f"✗ Sink already exists or creation failed: {e}")

    # Create sink to BigQuery
    print("\n→ Creating sink to export all logs to BigQuery...")
    try:
        bigquery_sink = logging_ctrl.create_sink(
            sink_name="example-all-logs-bigquery",
            destination="bigquery.googleapis.com/projects/my-project/datasets/logs",
            include_children=True,
        )
        print(f"✓ Created sink: {bigquery_sink.name}")
        print(f"  Destination: {bigquery_sink.destination}")
        print(f"  Includes children: {bigquery_sink.include_children}")
    except Exception as e:
        print(f"✗ Sink already exists or creation failed: {e}")

    # Create sink to Pub/Sub
    print("\n→ Creating sink to stream logs to Pub/Sub...")
    try:
        pubsub_sink = logging_ctrl.create_sink(
            sink_name="example-realtime-logs-pubsub",
            destination="pubsub.googleapis.com/projects/my-project/topics/logs",
            filter='severity>="INFO"',
        )
        print(f"✓ Created sink: {pubsub_sink.name}")
        print(f"  Destination: {pubsub_sink.destination}")
    except Exception as e:
        print(f"✗ Sink already exists or creation failed: {e}")

    # List all sinks
    print("\n→ Listing all sinks...")
    try:
        sinks = logging_ctrl.list_sinks()
        print(f"✓ Found {len(sinks)} sinks:")
        for sink in sinks:
            print(f"  • {sink.name} → {sink.destination}")
            if sink.filter:
                print(f"    Filter: {sink.filter}")
    except Exception as e:
        print(f"✗ Failed to list sinks: {e}")

    # Update sink
    print("\n→ Updating sink filter...")
    try:
        updated_sink = logging_ctrl.update_sink(
            sink_name="example-error-logs-sink", filter='severity>="WARNING"'
        )
        print(f"✓ Updated sink: {updated_sink.name}")
        print(f"  New filter: {updated_sink.filter}")
    except Exception as e:
        print(f"✗ Failed to update sink: {e}")

    # ========================================================================
    # 5. CLEANUP (OPTIONAL)
    # ========================================================================
    print("\n5. CLEANUP (OPTIONAL)")
    print("-" * 80)
    print("\nTo clean up example resources, uncomment the following:")
    print("  # Delete metrics")
    print('  # logging_ctrl.delete_metric("example_error_count")')
    print('  # logging_ctrl.delete_metric("example_http_requests_by_status")')
    print("\n  # Delete sinks")
    print('  # logging_ctrl.delete_sink("example-error-logs-sink")')
    print('  # logging_ctrl.delete_sink("example-all-logs-bigquery")')
    print('  # logging_ctrl.delete_sink("example-realtime-logs-pubsub")')
    print("\n  # Delete logs")
    print('  # logging_ctrl.delete_log("example-app-log")')

    # Uncomment to perform cleanup:
    # try:
    #     print("\n→ Cleaning up metrics...")
    #     logging_ctrl.delete_metric("example_error_count")
    #     logging_ctrl.delete_metric("example_http_requests_by_status")
    #     print("✓ Metrics deleted")
    # except Exception as e:
    #     print(f"✗ Failed to delete metrics: {e}")
    #
    # try:
    #     print("\n→ Cleaning up sinks...")
    #     logging_ctrl.delete_sink("example-error-logs-sink")
    #     logging_ctrl.delete_sink("example-all-logs-bigquery")
    #     logging_ctrl.delete_sink("example-realtime-logs-pubsub")
    #     print("✓ Sinks deleted")
    # except Exception as e:
    #     print(f"✗ Failed to delete sinks: {e}")
    #
    # try:
    #     print("\n→ Cleaning up logs...")
    #     logging_ctrl.delete_log("example-app-log")
    #     print("✓ Logs deleted")
    # except Exception as e:
    #     print(f"✗ Failed to delete logs: {e}")

    # ========================================================================
    # 6. ADVANCED USAGE
    # ========================================================================
    print("\n6. ADVANCED USAGE EXAMPLES")
    print("-" * 80)

    print("\n→ Writing complete LogEntry object...")
    log_entry = LogEntry(
        log_name=f"projects/{logging_ctrl.settings.project_id}/logs/advanced-log",
        resource={"type": "global"},
        severity=LogSeverity.INFO,
        json_payload={
            "message": "Advanced logging example",
            "custom_field": "custom_value",
            "nested": {"data": "nested_value"},
        },
        labels={"source": "example", "type": "advanced"},
        trace=f"projects/{logging_ctrl.settings.project_id}/traces/trace-123",
    )

    try:
        logging_ctrl.write_log_entry(log_entry)
        print("✓ Complete LogEntry written")
    except Exception as e:
        print(f"✗ Failed to write LogEntry: {e}")

    print("\n" + "=" * 80)
    print("Example completed successfully!")
    print("=" * 80)

    # ========================================================================
    # BEST PRACTICES
    # ========================================================================
    print("\n📚 BEST PRACTICES:")
    print("-" * 80)
    print("1. Use structured logging (JSON) for better searchability")
    print("2. Add consistent labels for filtering and aggregation")
    print("3. Use appropriate severity levels (DEBUG, INFO, WARNING, ERROR, etc.)")
    print("4. Include trace IDs for distributed tracing")
    print("5. Export important logs to Cloud Storage or BigQuery for long-term storage")
    print("6. Create metrics for monitoring critical events")
    print("7. Use filters to reduce noise and focus on important logs")
    print("8. Include source location for debugging")
    print("9. Add HTTP request metadata for web applications")
    print("10. Regularly review and clean up unused metrics and sinks")

    print("\n💡 COMMON USE CASES:")
    print("-" * 80)
    print("• Application logging and debugging")
    print("• Security audit trails")
    print("• Performance monitoring")
    print("• Error tracking and alerting")
    print("• Distributed tracing")
    print("• Compliance and data retention")
    print("• Real-time log streaming")
    print("• Log-based analytics")


if __name__ == "__main__":
    main()
