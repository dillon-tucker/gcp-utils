"""
Google BigQuery controller for data warehouse operations.

This module provides a type-safe controller for managing BigQuery datasets,
tables, and running queries for data engineering and analytics workflows.
"""

from typing import Any

from google.api_core.exceptions import GoogleAPIError
from google.auth.credentials import Credentials
from google.cloud import bigquery
from google.cloud.bigquery import (
    Dataset as BQDataset,
)
from google.cloud.bigquery import (
    LoadJobConfig as BQLoadJobConfig,
)
from google.cloud.bigquery import (
    QueryJobConfig,
)
from google.cloud.bigquery import (
    Table as BQTable,
)

from ..config import GCPSettings, get_settings
from ..exceptions import BigQueryError, ResourceNotFoundError
from ..models.bigquery import (
    Dataset,
    DatasetListResponse,
    Job,
    QueryResult,
    QueryRow,
    SchemaField,
    Table,
    TableListResponse,
)


class BigQueryController:
    """
    Controller for managing Google BigQuery resources.

    Provides methods for managing datasets, tables, running queries, and loading data
    for data engineering and analytics workflows.

    Example:
        ```python
        from gcp_utils.controllers import BigQueryController

        # Controller auto-loads settings from .env file
        bq = BigQueryController()

        # Create a dataset
        dataset = bq.create_dataset("my_dataset", location="US")

        # Run a query
        result = bq.query("SELECT * FROM `project.dataset.table` LIMIT 10")
        for row in result.rows:
            print(row.values)
        ```
    """

    def __init__(
        self,
        settings: GCPSettings | None = None,
        credentials: Credentials | None = None,
    ) -> None:
        """
        Initialize the BigQuery controller.

        Args:
            settings: GCP configuration. If not provided, loads from environment/.env file.
            credentials: Optional custom credentials.
        """
        self._settings = settings or get_settings()
        self._credentials = credentials
        self._client: bigquery.Client | None = None

    def _get_client(self) -> bigquery.Client:
        """Lazy initialization of the BigQuery client."""
        if self._client is None:
            self._client = bigquery.Client(
                project=self._settings.project_id,
                credentials=self._credentials,
            )
        return self._client

    def create_dataset(
        self,
        dataset_id: str,
        location: str | None = None,
        description: str | None = None,
        labels: dict[str, str] | None = None,
        default_table_expiration_ms: int | None = None,
    ) -> Dataset:
        """
        Create a new BigQuery dataset.

        Args:
            dataset_id: Dataset ID
            location: Dataset location (defaults to settings.bigquery_location)
            description: Dataset description
            labels: Dataset labels
            default_table_expiration_ms: Default table expiration in milliseconds

        Returns:
            Dataset model

        Raises:
            BigQueryError: If dataset creation fails

        Example:
            ```python
            dataset = bq.create_dataset(
                dataset_id="analytics",
                location="US",
                description="Analytics data warehouse",
                labels={"environment": "production"},
            )
            ```
        """
        try:
            client = self._get_client()
            dataset_ref = f"{self._settings.project_id}.{dataset_id}"

            dataset = BQDataset(dataset_ref)
            dataset.location = location or self._settings.bigquery_location

            if description:
                dataset.description = description

            if labels:
                dataset.labels = labels

            if default_table_expiration_ms:
                dataset.default_table_expiration_ms = default_table_expiration_ms

            created_dataset = client.create_dataset(dataset)

            return Dataset(
                dataset_id=created_dataset.dataset_id,
                project=created_dataset.project,
                location=created_dataset.location,
                description=created_dataset.description,
                friendly_name=created_dataset.friendly_name,
                labels=dict(created_dataset.labels) if created_dataset.labels else None,
                default_table_expiration_ms=created_dataset.default_table_expiration_ms,
                created=created_dataset.created,
                modified=created_dataset.modified,
            )

        except GoogleAPIError as e:
            raise BigQueryError(
                message=f"Failed to create dataset '{dataset_id}': {str(e)}",
                details={"dataset_id": dataset_id, "error": str(e)},
            ) from e

    def get_dataset(self, dataset_id: str) -> Dataset:
        """
        Get a BigQuery dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            Dataset model

        Raises:
            ResourceNotFoundError: If dataset doesn't exist
            BigQueryError: If retrieval fails

        Example:
            ```python
            dataset = bq.get_dataset("my_dataset")
            print(f"Location: {dataset.location}")
            ```
        """
        try:
            client = self._get_client()
            dataset_ref = f"{self._settings.project_id}.{dataset_id}"
            dataset = client.get_dataset(dataset_ref)

            return Dataset(
                dataset_id=dataset.dataset_id,
                project=dataset.project,
                location=dataset.location,
                description=dataset.description,
                friendly_name=dataset.friendly_name,
                labels=dict(dataset.labels) if dataset.labels else None,
                default_table_expiration_ms=dataset.default_table_expiration_ms,
                created=dataset.created,
                modified=dataset.modified,
            )

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Dataset '{dataset_id}' not found",
                    details={"dataset_id": dataset_id},
                ) from e

            raise BigQueryError(
                message=f"Failed to get dataset '{dataset_id}': {str(e)}",
                details={"dataset_id": dataset_id, "error": str(e)},
            ) from e

    def list_datasets(
        self, max_results: int | None = None
    ) -> DatasetListResponse:
        """
        List BigQuery datasets in the project.

        Args:
            max_results: Maximum number of datasets to return

        Returns:
            DatasetListResponse with list of datasets

        Raises:
            BigQueryError: If listing fails

        Example:
            ```python
            response = bq.list_datasets()
            for dataset in response.datasets:
                print(f"{dataset.dataset_id}: {dataset.location}")
            ```
        """
        try:
            client = self._get_client()
            datasets_iter = client.list_datasets(max_results=max_results)

            datasets = []
            for dataset in datasets_iter:
                datasets.append(
                    Dataset(
                        dataset_id=dataset.dataset_id,
                        project=dataset.project,
                        location="",  # List doesn't return location
                    )
                )

            return DatasetListResponse(datasets=datasets)

        except GoogleAPIError as e:
            raise BigQueryError(
                message=f"Failed to list datasets: {str(e)}",
                details={"error": str(e)},
            ) from e

    def delete_dataset(
        self, dataset_id: str, delete_contents: bool = False
    ) -> None:
        """
        Delete a BigQuery dataset.

        Args:
            dataset_id: Dataset ID
            delete_contents: If True, delete all tables in the dataset

        Raises:
            ResourceNotFoundError: If dataset doesn't exist
            BigQueryError: If deletion fails

        Example:
            ```python
            # Delete empty dataset
            bq.delete_dataset("temp_dataset")

            # Delete dataset with all tables
            bq.delete_dataset("old_dataset", delete_contents=True)
            ```
        """
        try:
            client = self._get_client()
            dataset_ref = f"{self._settings.project_id}.{dataset_id}"
            client.delete_dataset(dataset_ref, delete_contents=delete_contents)

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Dataset '{dataset_id}' not found",
                    details={"dataset_id": dataset_id},
                ) from e

            raise BigQueryError(
                message=f"Failed to delete dataset '{dataset_id}': {str(e)}",
                details={"dataset_id": dataset_id, "error": str(e)},
            ) from e

    def create_table(
        self,
        dataset_id: str,
        table_id: str,
        schema: list[SchemaField],
        description: str | None = None,
        labels: dict[str, str] | None = None,
        partition_field: str | None = None,
        clustering_fields: list[str] | None = None,
    ) -> Table:
        """
        Create a new BigQuery table.

        Args:
            dataset_id: Dataset ID
            table_id: Table ID
            schema: Table schema (list of SchemaField models)
            description: Table description
            labels: Table labels
            partition_field: Field to partition by (optional)
            clustering_fields: Fields to cluster by (optional, max 4)

        Returns:
            Table model

        Raises:
            BigQueryError: If table creation fails

        Example:
            ```python
            from gcp_utils.models.bigquery import SchemaField

            schema = [
                SchemaField(name="id", field_type="INTEGER", mode="REQUIRED"),
                SchemaField(name="name", field_type="STRING", mode="REQUIRED"),
                SchemaField(name="created_at", field_type="TIMESTAMP", mode="REQUIRED"),
            ]

            table = bq.create_table(
                dataset_id="my_dataset",
                table_id="users",
                schema=schema,
                partition_field="created_at",
                clustering_fields=["name"],
            )
            ```
        """
        try:
            client = self._get_client()
            table_ref = f"{self._settings.project_id}.{dataset_id}.{table_id}"

            # Convert SchemaField models to BigQuery schema
            bq_schema = [
                bigquery.SchemaField(
                    name=field.name,
                    field_type=field.field_type,
                    mode=field.mode,
                    description=field.description or "",
                )
                for field in schema
            ]

            table = BQTable(table_ref, schema=bq_schema)

            if description:
                table.description = description

            if labels:
                table.labels = labels

            if partition_field:
                table.time_partitioning = bigquery.TimePartitioning(field=partition_field)

            if clustering_fields:
                table.clustering_fields = clustering_fields

            created_table = client.create_table(table)

            return Table(
                table_id=created_table.table_id,
                dataset_id=created_table.dataset_id,
                project=created_table.project,
                description=created_table.description,
                friendly_name=created_table.friendly_name,
                labels=dict(created_table.labels) if created_table.labels else None,
                num_rows=created_table.num_rows,
                num_bytes=created_table.num_bytes,
                created=created_table.created,
                modified=created_table.modified,
                expires=created_table.expires,
            )

        except GoogleAPIError as e:
            raise BigQueryError(
                message=f"Failed to create table '{dataset_id}.{table_id}': {str(e)}",
                details={
                    "dataset_id": dataset_id,
                    "table_id": table_id,
                    "error": str(e),
                },
            ) from e

    def get_table(self, dataset_id: str, table_id: str) -> Table:
        """
        Get a BigQuery table.

        Args:
            dataset_id: Dataset ID
            table_id: Table ID

        Returns:
            Table model

        Raises:
            ResourceNotFoundError: If table doesn't exist
            BigQueryError: If retrieval fails

        Example:
            ```python
            table = bq.get_table("my_dataset", "users")
            print(f"Rows: {table.num_rows}")
            print(f"Size: {table.num_bytes} bytes")
            ```
        """
        try:
            client = self._get_client()
            table_ref = f"{self._settings.project_id}.{dataset_id}.{table_id}"
            table = client.get_table(table_ref)

            return Table(
                table_id=table.table_id,
                dataset_id=table.dataset_id,
                project=table.project,
                description=table.description,
                friendly_name=table.friendly_name,
                labels=dict(table.labels) if table.labels else None,
                num_rows=table.num_rows,
                num_bytes=table.num_bytes,
                created=table.created,
                modified=table.modified,
                expires=table.expires,
            )

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Table '{dataset_id}.{table_id}' not found",
                    details={"dataset_id": dataset_id, "table_id": table_id},
                ) from e

            raise BigQueryError(
                message=f"Failed to get table '{dataset_id}.{table_id}': {str(e)}",
                details={
                    "dataset_id": dataset_id,
                    "table_id": table_id,
                    "error": str(e),
                },
            ) from e

    def list_tables(
        self, dataset_id: str, max_results: int | None = None
    ) -> TableListResponse:
        """
        List tables in a BigQuery dataset.

        Args:
            dataset_id: Dataset ID
            max_results: Maximum number of tables to return

        Returns:
            TableListResponse with list of tables

        Raises:
            BigQueryError: If listing fails

        Example:
            ```python
            response = bq.list_tables("my_dataset")
            for table in response.tables:
                print(f"{table.table_id}: {table.num_rows} rows")
            ```
        """
        try:
            client = self._get_client()
            dataset_ref = f"{self._settings.project_id}.{dataset_id}"
            tables_iter = client.list_tables(dataset_ref, max_results=max_results)

            tables = []
            for table in tables_iter:
                tables.append(
                    Table(
                        table_id=table.table_id,
                        dataset_id=table.dataset_id,
                        project=table.project,
                    )
                )

            return TableListResponse(tables=tables)

        except GoogleAPIError as e:
            raise BigQueryError(
                message=f"Failed to list tables in dataset '{dataset_id}': {str(e)}",
                details={"dataset_id": dataset_id, "error": str(e)},
            ) from e

    def delete_table(self, dataset_id: str, table_id: str) -> None:
        """
        Delete a BigQuery table.

        Args:
            dataset_id: Dataset ID
            table_id: Table ID

        Raises:
            ResourceNotFoundError: If table doesn't exist
            BigQueryError: If deletion fails

        Example:
            ```python
            bq.delete_table("my_dataset", "temp_table")
            ```
        """
        try:
            client = self._get_client()
            table_ref = f"{self._settings.project_id}.{dataset_id}.{table_id}"
            client.delete_table(table_ref)

        except GoogleAPIError as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    message=f"Table '{dataset_id}.{table_id}' not found",
                    details={"dataset_id": dataset_id, "table_id": table_id},
                ) from e

            raise BigQueryError(
                message=f"Failed to delete table '{dataset_id}.{table_id}': {str(e)}",
                details={
                    "dataset_id": dataset_id,
                    "table_id": table_id,
                    "error": str(e),
                },
            ) from e

    def query(
        self,
        sql: str,
        location: str | None = None,
        use_legacy_sql: bool = False,
        max_results: int | None = None,
    ) -> QueryResult:
        """
        Execute a BigQuery SQL query.

        Args:
            sql: SQL query string
            location: Query location (defaults to settings.bigquery_location)
            use_legacy_sql: Use legacy SQL syntax (default: False for standard SQL)
            max_results: Maximum number of rows to return

        Returns:
            QueryResult with query results

        Raises:
            BigQueryError: If query execution fails

        Example:
            ```python
            # Run a query
            result = bq.query('''
                SELECT name, COUNT(*) as count
                FROM `my_dataset.users`
                GROUP BY name
                ORDER BY count DESC
                LIMIT 10
            ''')

            # Access results
            print(f"Total rows: {result.total_rows}")
            print(f"Bytes processed: {result.total_bytes_processed}")

            for row in result.rows:
                print(f"{row.values['name']}: {row.values['count']}")
            ```
        """
        try:
            client = self._get_client()

            job_config = QueryJobConfig(
                use_legacy_sql=use_legacy_sql,
            )

            query_job = client.query(
                sql,
                location=location or self._settings.bigquery_location,
                job_config=job_config,
            )

            # Wait for query to complete
            results = query_job.result(max_results=max_results)

            # Convert results to QueryResult model
            rows = []
            for row in results:
                row_dict = dict(row.items())
                rows.append(QueryRow(values=row_dict))

            # Convert schema
            schema = [
                SchemaField(
                    name=field.name,
                    field_type=field.field_type,
                    mode=field.mode,
                    description=field.description,
                )
                for field in results.schema
            ]

            return QueryResult(
                total_rows=results.total_rows,
                rows=rows,
                schema=schema,
                job_id=query_job.job_id,
                total_bytes_processed=query_job.total_bytes_processed,
                total_bytes_billed=query_job.total_bytes_billed,
                cache_hit=query_job.cache_hit,
            )

        except GoogleAPIError as e:
            raise BigQueryError(
                message=f"Query execution failed: {str(e)}",
                details={"sql": sql, "error": str(e)},
            ) from e

    def load_table_from_uri(
        self,
        source_uris: list[str],
        dataset_id: str,
        table_id: str,
        source_format: str = "CSV",
        schema: list[SchemaField] | None = None,
        write_disposition: str = "WRITE_EMPTY",
        autodetect: bool = False,
        skip_leading_rows: int = 0,
    ) -> Job:
        """
        Load data into a BigQuery table from Cloud Storage.

        Args:
            source_uris: GCS URIs (e.g., ['gs://bucket/file.csv'])
            dataset_id: Destination dataset ID
            table_id: Destination table ID
            source_format: Source format (CSV, JSON, AVRO, PARQUET)
            schema: Table schema (required if table doesn't exist and autodetect=False)
            write_disposition: Write disposition (WRITE_EMPTY, WRITE_APPEND, WRITE_TRUNCATE)
            autodetect: Auto-detect schema and options
            skip_leading_rows: Number of header rows to skip (CSV only)

        Returns:
            Job model with load job details

        Raises:
            BigQueryError: If load job fails

        Example:
            ```python
            from gcp_utils.models.bigquery import SchemaField

            schema = [
                SchemaField(name="id", field_type="INTEGER"),
                SchemaField(name="name", field_type="STRING"),
            ]

            job = bq.load_table_from_uri(
                source_uris=["gs://my-bucket/data.csv"],
                dataset_id="my_dataset",
                table_id="users",
                source_format="CSV",
                schema=schema,
                skip_leading_rows=1,
            )
            ```
        """
        try:
            client = self._get_client()
            table_ref = f"{self._settings.project_id}.{dataset_id}.{table_id}"

            job_config = BQLoadJobConfig(
                source_format=source_format,
                write_disposition=write_disposition,
                autodetect=autodetect,
            )

            if schema:
                job_config.schema = [
                    bigquery.SchemaField(
                        name=field.name,
                        field_type=field.field_type,
                        mode=field.mode,
                        description=field.description or "",
                    )
                    for field in schema
                ]

            if skip_leading_rows > 0 and source_format == "CSV":
                job_config.skip_leading_rows = skip_leading_rows

            load_job = client.load_table_from_uri(
                source_uris,
                table_ref,
                job_config=job_config,
            )

            # Wait for job to complete
            load_job.result()

            return Job(
                job_id=load_job.job_id,
                project=self._settings.project_id,
                location=load_job.location,
                state="DONE" if load_job.done() else "RUNNING",  # type: ignore[arg-type]
                job_type="LOAD",  # type: ignore[arg-type]
                created=load_job.created,
                started=load_job.started,
                ended=load_job.ended,
            )

        except GoogleAPIError as e:
            raise BigQueryError(
                message=f"Failed to load data into '{dataset_id}.{table_id}': {str(e)}",
                details={
                    "dataset_id": dataset_id,
                    "table_id": table_id,
                    "source_uris": source_uris,
                    "error": str(e),
                },
            ) from e

    def insert_rows(
        self, dataset_id: str, table_id: str, rows: list[dict[str, Any]]
    ) -> None:
        """
        Insert rows into a BigQuery table using streaming insert.

        Args:
            dataset_id: Dataset ID
            table_id: Table ID
            rows: List of row dictionaries to insert

        Raises:
            BigQueryError: If insertion fails

        Example:
            ```python
            rows = [
                {"id": 1, "name": "Alice", "age": 30},
                {"id": 2, "name": "Bob", "age": 25},
            ]

            bq.insert_rows("my_dataset", "users", rows)
            ```
        """
        try:
            client = self._get_client()
            table_ref = f"{self._settings.project_id}.{dataset_id}.{table_id}"
            table = client.get_table(table_ref)

            errors = client.insert_rows(table, rows)

            if errors:
                raise BigQueryError(
                    message=f"Failed to insert rows into '{dataset_id}.{table_id}'",
                    details={"errors": errors},
                )

        except GoogleAPIError as e:
            raise BigQueryError(
                message=f"Failed to insert rows into '{dataset_id}.{table_id}': {str(e)}",
                details={
                    "dataset_id": dataset_id,
                    "table_id": table_id,
                    "error": str(e),
                },
            ) from e
