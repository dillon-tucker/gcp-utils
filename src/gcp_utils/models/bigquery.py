"""
Pydantic models for Google BigQuery.

This module provides type-safe models for BigQuery resources including
datasets, tables, schemas, query results, and job configurations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class DatasetAccess(BaseModel):
    """Access control configuration for a dataset."""

    role: Optional[str] = Field(default=None, description="IAM role (e.g., 'READER', 'WRITER', 'OWNER')")
    user_by_email: Optional[str] = Field(default=None, description="User email")
    group_by_email: Optional[str] = Field(default=None, description="Group email")
    domain: Optional[str] = Field(default=None, description="Domain")
    special_group: Optional[str] = Field(
        default=None,
        description="Special group (e.g., 'projectReaders', 'projectWriters', 'projectOwners')",
    )
    view: Optional[dict[str, str]] = Field(
        default=None, description="Authorized view reference"
    )


class Dataset(BaseModel):
    """BigQuery dataset model."""

    dataset_id: str = Field(..., description="Dataset ID")
    project: str = Field(..., description="Project ID")
    location: str = Field(default="US", description="Dataset location")
    description: Optional[str] = Field(default=None, description="Dataset description")
    friendly_name: Optional[str] = Field(default=None, description="Dataset friendly name")
    labels: Optional[dict[str, str]] = Field(default=None, description="Dataset labels")
    access_entries: Optional[list[DatasetAccess]] = Field(
        default=None, description="Access control entries"
    )
    default_table_expiration_ms: Optional[int] = Field(
        default=None, description="Default table expiration in milliseconds"
    )
    created: Optional[datetime] = Field(default=None, description="Creation timestamp")
    modified: Optional[datetime] = Field(default=None, description="Last modified timestamp")


class FieldMode(str, Enum):
    """BigQuery field mode."""

    NULLABLE = "NULLABLE"
    REQUIRED = "REQUIRED"
    REPEATED = "REPEATED"


class FieldType(str, Enum):
    """BigQuery field types."""

    STRING = "STRING"
    BYTES = "BYTES"
    INTEGER = "INTEGER"
    INT64 = "INT64"
    FLOAT = "FLOAT"
    FLOAT64 = "FLOAT64"
    NUMERIC = "NUMERIC"
    BIGNUMERIC = "BIGNUMERIC"
    BOOLEAN = "BOOLEAN"
    BOOL = "BOOL"
    TIMESTAMP = "TIMESTAMP"
    DATE = "DATE"
    TIME = "TIME"
    DATETIME = "DATETIME"
    GEOGRAPHY = "GEOGRAPHY"
    RECORD = "RECORD"
    STRUCT = "STRUCT"
    JSON = "JSON"


class SchemaField(BaseModel):
    """BigQuery table schema field."""

    name: str = Field(..., description="Field name")
    field_type: str = Field(..., description="Field type (e.g., 'STRING', 'INTEGER')")
    mode: str = Field(default="NULLABLE", description="Field mode (NULLABLE, REQUIRED, REPEATED)")
    description: Optional[str] = Field(default=None, description="Field description")
    fields: Optional[list["SchemaField"]] = Field(
        default=None, description="Nested fields (for RECORD/STRUCT types)"
    )


class TableType(str, Enum):
    """BigQuery table type."""

    TABLE = "TABLE"
    VIEW = "VIEW"
    EXTERNAL = "EXTERNAL"
    MATERIALIZED_VIEW = "MATERIALIZED_VIEW"
    SNAPSHOT = "SNAPSHOT"


class TimePartitioningType(str, Enum):
    """Time partitioning type."""

    DAY = "DAY"
    HOUR = "HOUR"
    MONTH = "MONTH"
    YEAR = "YEAR"


class TimePartitioning(BaseModel):
    """Time partitioning configuration."""

    type_: TimePartitioningType = Field(
        ..., description="Partitioning type", alias="type"
    )
    field: Optional[str] = Field(
        default=None, description="Field to partition by (optional for _PARTITIONTIME)"
    )
    expiration_ms: Optional[int] = Field(
        default=None, description="Partition expiration in milliseconds"
    )
    require_partition_filter: bool = Field(
        default=False, description="Require partition filter in queries"
    )


class Clustering(BaseModel):
    """Table clustering configuration."""

    fields: list[str] = Field(..., description="Fields to cluster by (max 4)")


class Table(BaseModel):
    """BigQuery table model."""

    model_config = {"protected_namespaces": ()}

    table_id: str = Field(..., description="Table ID")
    dataset_id: str = Field(..., description="Dataset ID")
    project: str = Field(..., description="Project ID")
    description: Optional[str] = Field(default=None, description="Table description")
    friendly_name: Optional[str] = Field(default=None, description="Table friendly name")
    labels: Optional[dict[str, str]] = Field(default=None, description="Table labels")
    table_schema: Optional[list[SchemaField]] = Field(default=None, description="Table schema", alias="schema")
    num_rows: Optional[int] = Field(default=None, description="Number of rows")
    num_bytes: Optional[int] = Field(default=None, description="Size in bytes")
    table_type: Optional[TableType] = Field(default=None, description="Table type")
    time_partitioning: Optional[TimePartitioning] = Field(
        default=None, description="Time partitioning configuration"
    )
    clustering_fields: Optional[Clustering] = Field(
        default=None, description="Clustering configuration"
    )
    created: Optional[datetime] = Field(default=None, description="Creation timestamp")
    modified: Optional[datetime] = Field(default=None, description="Last modified timestamp")
    expires: Optional[datetime] = Field(default=None, description="Expiration timestamp")


class JobState(str, Enum):
    """BigQuery job state."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"


class JobType(str, Enum):
    """BigQuery job type."""

    QUERY = "QUERY"
    LOAD = "LOAD"
    EXTRACT = "EXTRACT"
    COPY = "COPY"


class QueryPriority(str, Enum):
    """Query priority."""

    INTERACTIVE = "INTERACTIVE"
    BATCH = "BATCH"


class WriteDisposition(str, Enum):
    """Write disposition for load/query jobs."""

    WRITE_TRUNCATE = "WRITE_TRUNCATE"
    WRITE_APPEND = "WRITE_APPEND"
    WRITE_EMPTY = "WRITE_EMPTY"


class CreateDisposition(str, Enum):
    """Create disposition for load/query jobs."""

    CREATE_IF_NEEDED = "CREATE_IF_NEEDED"
    CREATE_NEVER = "CREATE_NEVER"


class SourceFormat(str, Enum):
    """Source format for load jobs."""

    CSV = "CSV"
    JSON = "NEWLINE_DELIMITED_JSON"
    AVRO = "AVRO"
    PARQUET = "PARQUET"
    ORC = "ORC"
    DATASTORE_BACKUP = "DATASTORE_BACKUP"


class DestinationFormat(str, Enum):
    """Destination format for extract jobs."""

    CSV = "CSV"
    JSON = "NEWLINE_DELIMITED_JSON"
    AVRO = "AVRO"
    PARQUET = "PARQUET"


class Job(BaseModel):
    """BigQuery job model."""

    job_id: str = Field(..., description="Job ID")
    project: str = Field(..., description="Project ID")
    location: str = Field(default="US", description="Job location")
    state: Optional[JobState] = Field(default=None, description="Job state")
    job_type: Optional[JobType] = Field(default=None, description="Job type")
    created: Optional[datetime] = Field(default=None, description="Creation timestamp")
    started: Optional[datetime] = Field(default=None, description="Start timestamp")
    ended: Optional[datetime] = Field(default=None, description="End timestamp")
    error_result: Optional[dict[str, Any]] = Field(default=None, description="Error details if failed")
    total_bytes_processed: Optional[int] = Field(
        default=None, description="Total bytes processed"
    )
    total_bytes_billed: Optional[int] = Field(
        default=None, description="Total bytes billed"
    )


class QueryRow(BaseModel):
    """Single row from a query result."""

    values: dict[str, Any] = Field(..., description="Column name to value mapping")


class QueryResult(BaseModel):
    """BigQuery query result model."""

    model_config = {"protected_namespaces": ()}

    total_rows: int = Field(..., description="Total number of rows")
    rows: list[QueryRow] = Field(default_factory=list, description="Query result rows")
    result_schema: list[SchemaField] = Field(..., description="Result schema", alias="schema")
    job_id: Optional[str] = Field(default=None, description="Job ID for the query")
    total_bytes_processed: Optional[int] = Field(
        default=None, description="Total bytes processed"
    )
    total_bytes_billed: Optional[int] = Field(
        default=None, description="Total bytes billed"
    )
    cache_hit: Optional[bool] = Field(
        default=None, description="Whether the result was served from cache"
    )


class DatasetListResponse(BaseModel):
    """Response model for listing datasets."""

    datasets: list[Dataset] = Field(
        default_factory=list, description="List of datasets"
    )
    next_page_token: Optional[str] = Field(
        default=None, description="Token for fetching the next page"
    )


class TableListResponse(BaseModel):
    """Response model for listing tables."""

    tables: list[Table] = Field(
        default_factory=list, description="List of tables"
    )
    next_page_token: Optional[str] = Field(
        default=None, description="Token for fetching the next page"
    )


class JobListResponse(BaseModel):
    """Response model for listing jobs."""

    jobs: list[Job] = Field(
        default_factory=list, description="List of jobs"
    )
    next_page_token: Optional[str] = Field(
        default=None, description="Token for fetching the next page"
    )


class LoadJobConfig(BaseModel):
    """Configuration for a load job."""

    model_config = {"protected_namespaces": ()}

    source_format: SourceFormat = Field(..., description="Source file format")
    source_uris: list[str] = Field(..., description="Source file URIs (GCS paths)")
    destination_table: str = Field(..., description="Destination table reference")
    write_disposition: WriteDisposition = Field(
        default=WriteDisposition.WRITE_EMPTY, description="Write disposition"
    )
    create_disposition: CreateDisposition = Field(
        default=CreateDisposition.CREATE_IF_NEEDED, description="Create disposition"
    )
    load_schema: Optional[list[SchemaField]] = Field(
        default=None, description="Table schema (required if table doesn't exist)", alias="schema"
    )
    skip_leading_rows: Optional[int] = Field(
        default=None, description="Number of rows to skip (CSV only)"
    )
    field_delimiter: Optional[str] = Field(
        default=None, description="Field delimiter (CSV only)"
    )
    allow_jagged_rows: Optional[bool] = Field(
        default=None, description="Allow missing trailing columns (CSV only)"
    )
    allow_quoted_newlines: Optional[bool] = Field(
        default=None, description="Allow quoted newlines (CSV only)"
    )
    autodetect: Optional[bool] = Field(
        default=None, description="Automatically detect schema and options"
    )
    max_bad_records: Optional[int] = Field(
        default=None, description="Maximum number of bad records to ignore"
    )
