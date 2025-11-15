# Changelog

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
