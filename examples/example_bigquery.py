"""
Example usage of BigQuery controller.

This example demonstrates:
- Creating and managing datasets
- Creating and managing tables with schemas
- Running SQL queries
- Loading data from Cloud Storage
- Streaming inserts
- Data engineering workflows

Requirements:
- Valid GCP project with BigQuery API enabled
- .env file with GCP_PROJECT_ID set
- Cloud Storage bucket for data loading
"""

from gcp_utils.controllers import BigQueryController
from gcp_utils.models.bigquery import SchemaField

# Initialize controller (auto-loads from .env)
bq = BigQueryController()


def example_create_dataset() -> None:
    """
    Create a BigQuery dataset.

    A dataset is a top-level container for tables.
    """
    print("\n=== Creating Dataset ===")

    try:
        dataset = bq.create_dataset(
            dataset_id="analytics",
            location="US",
            description="Analytics data warehouse",
            labels={
                "environment": "production",
                "team": "data",
            },
        )

        print(f"✓ Dataset created: {dataset.dataset_id}")
        print(f"  Location: {dataset.location}")
        print(f"  Project: {dataset.project}")

    except Exception as e:
        print(f"✗ Error creating dataset: {e}")


def example_create_table_with_schema() -> None:
    """
    Create a BigQuery table with a defined schema.

    This includes partitioning and clustering for better query performance.
    """
    print("\n=== Creating Table with Schema ===")

    # Define table schema
    schema = [
        SchemaField(
            name="user_id",
            field_type="STRING",
            mode="REQUIRED",
            description="Unique user identifier",
        ),
        SchemaField(
            name="event_type",
            field_type="STRING",
            mode="REQUIRED",
            description="Type of event (view, click, purchase)",
        ),
        SchemaField(
            name="event_timestamp",
            field_type="TIMESTAMP",
            mode="REQUIRED",
            description="When the event occurred",
        ),
        SchemaField(
            name="page_url",
            field_type="STRING",
            mode="NULLABLE",
            description="URL where event occurred",
        ),
        SchemaField(
            name="revenue",
            field_type="NUMERIC",
            mode="NULLABLE",
            description="Revenue amount for purchase events",
        ),
    ]

    try:
        table = bq.create_table(
            dataset_id="analytics",
            table_id="user_events",
            schema=schema,
            description="User event tracking data",
            labels={"type": "events"},
            partition_field="event_timestamp",  # Partition by timestamp for performance
            clustering_fields=["user_id", "event_type"],  # Cluster for better queries
        )

        print(f"✓ Table created: {table.dataset_id}.{table.table_id}")
        print("  Partitioned by: event_timestamp")
        print("  Clustered by: user_id, event_type")

    except Exception as e:
        print(f"✗ Error creating table: {e}")


def example_run_query() -> None:
    """
    Run a SQL query and process results.

    This demonstrates querying data and working with results.
    """
    print("\n=== Running SQL Query ===")

    sql = """
        SELECT
            event_type,
            COUNT(*) as event_count,
            SUM(revenue) as total_revenue
        FROM `analytics.user_events`
        WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        GROUP BY event_type
        ORDER BY event_count DESC
    """

    try:
        result = bq.query(sql, location="US")

        print("✓ Query completed")
        print(f"  Total rows: {result.total_rows}")
        print(f"  Bytes processed: {result.total_bytes_processed:,}")
        print(f"  Bytes billed: {result.total_bytes_billed:,}")
        print(f"  Cache hit: {result.cache_hit}")

        print("\nResults:")
        for row in result.rows:
            event_type = row.values.get("event_type")
            event_count = row.values.get("event_count")
            total_revenue = row.values.get("total_revenue")
            print(
                f"  {event_type:15} | Count: {event_count:6} | Revenue: ${total_revenue or 0:.2f}"
            )

    except Exception as e:
        print(f"✗ Error running query: {e}")


def example_load_data_from_gcs() -> None:
    """
    Load data into BigQuery from Cloud Storage.

    This is the recommended way to load large amounts of data.
    """
    print("\n=== Loading Data from Cloud Storage ===")

    # Define schema for the CSV file
    schema = [
        SchemaField(name="user_id", field_type="STRING", mode="REQUIRED"),
        SchemaField(name="event_type", field_type="STRING", mode="REQUIRED"),
        SchemaField(name="event_timestamp", field_type="TIMESTAMP", mode="REQUIRED"),
        SchemaField(name="page_url", field_type="STRING", mode="NULLABLE"),
        SchemaField(name="revenue", field_type="NUMERIC", mode="NULLABLE"),
    ]

    try:
        job = bq.load_table_from_uri(
            source_uris=["gs://my-bucket/events/events_*.csv"],
            dataset_id="analytics",
            table_id="user_events",
            source_format="CSV",
            schema=schema,
            write_disposition="WRITE_APPEND",  # Append to existing data
            skip_leading_rows=1,  # Skip header row
        )

        print("✓ Data loaded successfully")
        print(f"  Job ID: {job.job_id}")
        print(f"  Location: {job.location}")

    except Exception as e:
        print(f"✗ Error loading data: {e}")


def example_streaming_inserts() -> None:
    """
    Insert rows using streaming API.

    This is useful for real-time data ingestion with low latency.
    """
    print("\n=== Streaming Inserts ===")

    rows = [
        {
            "user_id": "user123",
            "event_type": "view",
            "event_timestamp": "2025-01-20T10:00:00",
            "page_url": "https://example.com/products",
            "revenue": None,
        },
        {
            "user_id": "user456",
            "event_type": "purchase",
            "event_timestamp": "2025-01-20T10:05:00",
            "page_url": "https://example.com/checkout",
            "revenue": 99.99,
        },
        {
            "user_id": "user789",
            "event_type": "click",
            "event_timestamp": "2025-01-20T10:10:00",
            "page_url": "https://example.com/about",
            "revenue": None,
        },
    ]

    try:
        bq.insert_rows("analytics", "user_events", rows)

        print(f"✓ {len(rows)} rows inserted successfully")
        print("  Note: Streaming inserts may take a few seconds to appear in queries")

    except Exception as e:
        print(f"✗ Error inserting rows: {e}")


def example_list_datasets() -> None:
    """
    List all datasets in the project.
    """
    print("\n=== Listing Datasets ===")

    try:
        response = bq.list_datasets()

        print(f"Found {len(response.datasets)} datasets:")
        for dataset in response.datasets:
            print(f"  - {dataset.dataset_id}")

    except Exception as e:
        print(f"✗ Error listing datasets: {e}")


def example_list_tables() -> None:
    """
    List all tables in a dataset.
    """
    print("\n=== Listing Tables in Dataset ===")

    try:
        response = bq.list_tables("analytics")

        print(f"Found {len(response.tables)} tables in analytics:")
        for table in response.tables:
            print(f"  - {table.table_id}")

    except Exception as e:
        print(f"✗ Error listing tables: {e}")


def example_get_table_info() -> None:
    """
    Get detailed information about a table.
    """
    print("\n=== Getting Table Information ===")

    try:
        table = bq.get_table("analytics", "user_events")

        print(f"Table: {table.dataset_id}.{table.table_id}")
        print(f"  Description: {table.description}")
        print(f"  Rows: {table.num_rows:,}" if table.num_rows else "  Rows: N/A")
        print(
            f"  Size: {table.num_bytes:,} bytes" if table.num_bytes else "  Size: N/A"
        )
        print(f"  Created: {table.created}")
        print(f"  Modified: {table.modified}")

    except Exception as e:
        print(f"✗ Error getting table info: {e}")


def example_complex_analytics_query() -> None:
    """
    Run a complex analytics query with aggregations and window functions.
    """
    print("\n=== Running Complex Analytics Query ===")

    sql = """
        WITH daily_revenue AS (
            SELECT
                DATE(event_timestamp) as event_date,
                user_id,
                SUM(revenue) as daily_revenue
            FROM `analytics.user_events`
            WHERE event_type = 'purchase'
                AND event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
            GROUP BY event_date, user_id
        ),
        user_metrics AS (
            SELECT
                user_id,
                COUNT(DISTINCT event_date) as active_days,
                SUM(daily_revenue) as total_revenue,
                AVG(daily_revenue) as avg_daily_revenue
            FROM daily_revenue
            GROUP BY user_id
        )
        SELECT
            CASE
                WHEN total_revenue >= 1000 THEN 'High Value'
                WHEN total_revenue >= 100 THEN 'Medium Value'
                ELSE 'Low Value'
            END as customer_segment,
            COUNT(*) as customer_count,
            AVG(total_revenue) as avg_revenue,
            AVG(active_days) as avg_active_days
        FROM user_metrics
        GROUP BY customer_segment
        ORDER BY avg_revenue DESC
    """

    try:
        result = bq.query(sql, location="US")

        print("✓ Analytics query completed")
        print("\nCustomer Segmentation:")
        for row in result.rows:
            segment = row.values.get("customer_segment")
            count = row.values.get("customer_count")
            revenue = row.values.get("avg_revenue")
            days = row.values.get("avg_active_days")
            print(
                f"  {segment:15} | Customers: {count:4} | Avg Revenue: ${revenue:.2f} | Avg Active Days: {days:.1f}"
            )

    except Exception as e:
        print(f"✗ Error running analytics query: {e}")


def example_delete_table() -> None:
    """
    Delete a BigQuery table.

    CAUTION: This permanently deletes the table and all its data.
    """
    print("\n=== Deleting Table ===")

    try:
        bq.delete_table("analytics", "user_events")
        print("✓ Table deleted successfully")

    except Exception as e:
        print(f"✗ Error deleting table: {e}")


def example_delete_dataset() -> None:
    """
    Delete a BigQuery dataset.

    CAUTION: This permanently deletes the dataset and all its tables.
    """
    print("\n=== Deleting Dataset ===")

    try:
        bq.delete_dataset("analytics", delete_contents=True)
        print("✓ Dataset deleted successfully")

    except Exception as e:
        print(f"✗ Error deleting dataset: {e}")


if __name__ == "__main__":
    print("BigQuery Controller Example")
    print("=" * 50)

    # Run examples
    # example_create_dataset()
    # example_create_table_with_schema()
    # example_run_query()
    # example_load_data_from_gcs()
    # example_streaming_inserts()
    example_list_datasets()
    # example_list_tables()
    # example_get_table_info()
    # example_complex_analytics_query()
    # example_delete_table()  # Uncomment to test deletion
    # example_delete_dataset()  # Uncomment to test deletion

    print("\n" + "=" * 50)
    print("Example completed!")
