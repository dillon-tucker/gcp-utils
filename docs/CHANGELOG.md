# Changelog

## 2025-11-16

### Added

*   **IAM Controller**: Added comprehensive IAM (Identity and Access Management) controller for managing service accounts, keys, and IAM policies
    *   `src/gcp_utils/controllers/iam.py` - Full-featured IAM controller with 14+ methods
    *   `src/gcp_utils/models/iam.py` - Type-safe Pydantic models (ServiceAccount, ServiceAccountKey, IAMPolicy, IAMBinding, ServiceAccountInfo)
    *   `examples/example_iam.py` - Complete example demonstrating all IAM operations
    *   Service account management: create, get, list, update, delete, get detailed info
    *   Service account key management: create, list, delete with base64-encoded JSON credentials
    *   IAM policy management: get and set IAM policies with typed bindings
    *   Added `google-cloud-iam>=2.15.0` dependency to `pyproject.toml`
*   **GCS Object Binding**: Enhanced Cloud Storage models to bind native Google Cloud Storage objects
    *   Added `_gcs_object` private attribute to `BlobMetadata`, `BucketInfo`, and `UploadResult` using Pydantic's `PrivateAttr()`
    *   Added convenience methods to delegate to native GCS objects: `make_public()`, `delete()`, `download_as_bytes()`, `download_as_text()`, `generate_signed_url()`, `list_blobs()`, `reload()`
    *   Enables seamless integration between type-safe Pydantic models and full GCS API functionality
*   **Optional Settings Parameter**: Made `settings` parameter optional in all controllers (10 total)
    *   Controllers now auto-load settings from `.env` file if not provided via `get_settings()`
    *   Added `_find_project_root()` function to locate `.env` file relative to `pyproject.toml`
    *   Eliminates boilerplate code in examples and simplifies controller instantiation
*   **Bucket Access Control**: Added `uniform_bucket_level_access` parameter to `create_bucket()` method
    *   Allows choosing between uniform bucket-level access (recommended) and fine-grained ACLs
    *   Default changed to `True` to align with GCP best practices and organization policies

### Fixed

*   Fixed IAM controller imports to use correct request types from `google.iam.v1.iam_policy_pb2`
*   Added required `field_mask` parameter to `PatchServiceAccountRequest` for service account updates
*   Fixed Unicode encoding errors in `example_iam.py` by replacing checkmarks and symbols with ASCII equivalents (`[OK]`, `[FAIL]`, `[WARN]`)
*   Added `sys.path` manipulation to `example_iam.py` for running without package installation

### Changed

*   Updated CLAUDE.md with comprehensive IAM controller documentation including:
    *   Controller initialization pattern and key operations
    *   Service account key handling and security considerations
    *   IAM policy management patterns with code examples
    *   Model descriptions and common use cases
*   Updated CLAUDE.md with instructions for installing dependencies in `../.venv` virtual environment
*   Updated all example files to demonstrate auto-loading settings from `.env` file
*   Updated README.md to emphasize `.env` file auto-discovery and simpler controller instantiation

## 2025-11-15

### Added

*   Created test scripts for `CloudStorageController`, `FirestoreController`, and `SecretManagerController` in the `tests/` directory. These tests include both mocked unit tests and integration tests.

### Fixed

*   Resolved `AttributeError` in `tests/test_firestore.py::test_create_document` by updating the assertion to use `created_doc.id` instead of `created_doc.document_id`, aligning with the `FirestoreDocument` model's field name.
*   Corrected `TypeError` in `tests/test_secret_manager.py::test_create_secret` by modifying the assertion to access attributes of the `CreateSecretRequest` object directly via `call_args.kwargs['request'].parent` and `call_args.kwargs['request'].secret_id`.
*   Fixed code bug in `tests/test_firestore.py::test_document_lifecycle` integration test by changing `created_doc.document_id` to `created_doc.id` to match the `FirestoreDocument` model field name.
*   Removed invalid `retry.DEFAULT` references from `src/gcp_utils/controllers/storage.py` (lines 251, 313, 373, 418, 463) - Google Cloud Storage client has built-in retry logic, so explicit retry parameter is not needed.
*   Updated all test fixtures in `tests/test_*.py` to read configuration from `.env` file instead of hardcoding `project_id="test-project"`, enabling tests to run with real GCP projects.
*   Fixed `tests/test_secret_manager.py::test_secret_lifecycle` to:
    *   Access dict keys correctly (`version["full_name"]` instead of `version.name`)
    *   Add cleanup logic at test start to handle existing secrets from previous runs
    *   Use correct version number assertion (`new_version["name"] == "2"`)

### Changed

*   Updated all Pydantic models in `src/gcp_utils/models/` to replace deprecated `json_encoders` with the modern `@field_serializer` decorator for custom `datetime` and `timedelta` serialization. This change eliminates deprecation warnings and aligns with Pydantic v2 best practices. Affected files include:
    *   `src/gcp_utils/models/storage.py`
    *   `src/gcp_utils/models/firestore.py`
    *   `src/gcp_utils/models/cloud_run.py`
    *   `src/gcp_utils/models/workflows.py`
    *   `src/gcp_utils/models/tasks.py`
    *   `src/gcp_utils/models/firebase_hosting.py`
    *   `src/gcp_utils/models/artifact_registry.py`
*   Fixed type annotations for all `@field_serializer` methods across all Pydantic models to satisfy mypy's strict type checking requirements. Added proper type hints for parameters and return types, reducing mypy errors from 65 to 28.
*   Fixed type annotation issues in `src/gcp_utils/config/settings.py`:
    *   Added type cast for `json.load()` return value in `get_credentials_dict()` method
    *   Added type ignore comments for `GCPSettings()` instantiation in `get_settings()` and `reload_settings()` to handle Pydantic's automatic environment variable loading
