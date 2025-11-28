# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-ready Python package providing type-safe controllers for Google Cloud Platform services. The package is built with Python 3.12+, uses UV for dependency management, and emphasizes type safety, comprehensive error handling, and developer experience.

## Development Commands

### Installation & Setup

**IMPORTANT: Virtual Environment Location**

This project uses a Python 3.12+ virtual environment located at `../.venv` (one level up from the project root). This is required because the project requires Python 3.12+.

**Initial Setup (First Time):**

```bash
# Create Python 3.12 virtual environment (if not exists)
cd /home/user && python3.12 -m venv .venv

# Install package in editable mode with dev dependencies
cd gcp-utils

# Using pip (standard)
../.venv/bin/pip install -e ".[all,dev]"

# OR using uv (faster, recommended)
uv pip install -e ".[all,dev]"

# Create .env file from template
cp .env.example .env

# Edit .env with your project settings (minimum required: GCP_PROJECT_ID)
# For tests, you can use: GCP_PROJECT_ID=test-project
```

**Optional Dependencies - Install Only What You Need:**

This package uses optional dependencies to reduce installation overhead. Install only the GCP services you need:

**Using pip:**
```bash
# Install specific services
../.venv/bin/pip install -e ".[storage]"              # Cloud Storage only
../.venv/bin/pip install -e ".[bigquery]"             # BigQuery only
../.venv/bin/pip install -e ".[firestore]"            # Firestore only
../.venv/bin/pip install -e ".[firebase]"             # Firebase (Auth + Hosting)

# Install multiple services
../.venv/bin/pip install -e ".[storage,bigquery,firestore]"

# Install all services (for development or production with many services)
../.venv/bin/pip install -e ".[all]"

# Install with dev dependencies (for development)
../.venv/bin/pip install -e ".[all,dev]"
```

**Using uv (faster alternative):**
```bash
# Install specific services
uv pip install -e ".[storage]"
uv pip install -e ".[bigquery]"
uv pip install -e ".[firestore]"
uv pip install -e ".[firebase]"

# Install multiple services
uv pip install -e ".[storage,bigquery,firestore]"

# Install all services
uv pip install -e ".[all]"

# Install with dev dependencies
uv pip install -e ".[all,dev]"
```

**Available Optional Dependencies:**

Individual services:
- `storage` - Cloud Storage
- `firestore` - Firestore Database
- `bigquery` - BigQuery Analytics
- `artifact-registry` - Artifact Registry
- `cloud-run` - Cloud Run
- `cloud-tasks` - Cloud Tasks
- `cloud-functions` - Cloud Functions
- `cloud-scheduler` - Cloud Scheduler
- `cloud-build` - Cloud Build
- `workflows` - Workflows
- `pubsub` - Pub/Sub Messaging
- `secret-manager` - Secret Manager
- `iam` - IAM (Identity and Access Management)
- `logging` - Cloud Logging
- `firebase` - Firebase (Auth + Hosting)
- `firebase-auth` - Firebase Auth only
- `firebase-hosting` - Firebase Hosting only

Special extras:
- `all` - Install all GCP services
- `dev` - Development dependencies (pytest, mypy, black, ruff, etc.)

**Virtual Environment Usage:**

Always use the virtual environment for all commands:
- **Python**: `../.venv/bin/python` (or `../.venv/Scripts/python.exe` on Windows)
- **Pytest**: `../.venv/bin/pytest`
- **Pip**: `../.venv/bin/pip`

**Adding Dependencies:**

When adding new dependencies to `pyproject.toml`, install them in the virtual environment:
```bash
# Using pip
../.venv/bin/pip install <package-name>

# OR using uv (faster)
uv pip install <package-name>
```

For new GCP services, add them to the appropriate optional dependency group in `pyproject.toml`.

### Code Quality & Type Checking

**Note**: These tools should be run with the virtual environment:

```bash
# Type checking (strict mode) - REQUIRED before commits
../.venv/bin/mypy src/

# Linting (fast linter with auto-fix)
../.venv/bin/ruff check src/ tests/ examples/ --fix

# Code formatting (auto-format)
../.venv/bin/black src/ tests/ examples/

# Import sorting (auto-sort)
../.venv/bin/isort src/ tests/ examples/

# Run all checks (for CI/verification)
../.venv/bin/mypy src/ && ../.venv/bin/ruff check src/ && ../.venv/bin/black --check src/ && ../.venv/bin/isort --check src/
```

**CRITICAL - Before Committing:**

ALWAYS run these quality checks before committing code:

```bash
# 1. Format code
../.venv/bin/black src/ tests/ examples/
../.venv/bin/isort src/ tests/ examples/

# 2. Fix linting issues
../.venv/bin/ruff check src/ tests/ examples/ --fix --unsafe-fixes

# 3. Type check
../.venv/bin/mypy src/

# 4. Run tests
../.venv/bin/pytest tests/

# OR run all in one command:
../.venv/bin/black src/ tests/ examples/ && \
  ../.venv/bin/isort src/ tests/ examples/ && \
  ../.venv/bin/ruff check src/ tests/ examples/ --fix --unsafe-fixes && \
  ../.venv/bin/mypy src/ && \
  ../.venv/bin/pytest tests/
```

If any of these checks fail, fix the issues before committing.

### Testing

**CRITICAL**: Always use the virtual environment's pytest:

```bash
# Run all tests
../.venv/bin/pytest tests/

# Run with coverage
../.venv/bin/pytest --cov=src/gcp_utils tests/

# Run specific test file
../.venv/bin/pytest tests/test_import.py

# Run tests matching a pattern
../.venv/bin/pytest -k "test_pattern"

# Run tests for specific controllers
../.venv/bin/pytest tests/test_firebase_auth.py
../.venv/bin/pytest tests/test_firebase_hosting.py
../.venv/bin/pytest tests/test_cloud_run.py

# Run tests with verbose output
../.venv/bin/pytest -v tests/

# Run tests and stop on first failure
../.venv/bin/pytest -x tests/
```

**Test Environment Requirements:**
- `.env` file must exist with at minimum `GCP_PROJECT_ID=test-project`
- Tests use mocked GCP clients, so no real credentials are needed
- All tests follow the pattern of mocking external dependencies

**Test Coverage:**

The test suite includes comprehensive coverage for all controllers:

1. **test_import.py** - Package import validation (5 tests)
2. **test_models.py** - Pydantic model validation (15+ tests)
3. **test_storage.py** - Cloud Storage controller (5 tests)
4. **test_firestore.py** - Firestore controller (3 tests)
5. **test_firebase_auth.py** - Firebase Auth controller (27 tests) ✨ NEW
   - User CRUD operations
   - Token management and verification
   - Custom claims
   - Email verification and password reset
6. **test_firebase_hosting.py** - Firebase Hosting controller (19 tests) ✨ NEW
   - Site management
   - Custom domains
   - Version and release workflows
   - File upload and deployment
7. **test_cloud_run.py** - Cloud Run Services controller (15 tests)
8. **test_cloud_run_jobs.py** - Cloud Run Jobs controller (23 tests) ✨ NEW
   - Job lifecycle (create, get, list, update, delete)
   - Execution management (run, get, list, cancel)
   - Status tracking and monitoring
   - Resource path construction
9. **test_cloud_tasks.py** - Cloud Tasks controller (7 tests)
10. **test_workflows.py** - Workflows controller (6 tests)
11. **test_pubsub.py** - Pub/Sub controller (7 tests)
12. **test_secret_manager.py** - Secret Manager controller (3 tests)
13. **test_iam.py** - IAM controller (6 tests)
14. **test_artifact_registry.py** - Artifact Registry controller (6 tests)

**Total: 133+ test cases across all controllers**

### Running Examples

**Note**: Examples require real GCP credentials and a valid `.env` configuration:

```bash
# Firebase Authentication
../.venv/bin/python examples/example_firebase_auth.py

# Cloud Storage
../.venv/bin/python examples/example_storage.py

# Firestore
../.venv/bin/python examples/example_firestore.py

# Firebase Hosting (deployment)
../.venv/bin/python examples/example_firebase_hosting.py

# Cloud Run (simple deployment)
../.venv/bin/python examples/example_cloud_run.py

# Cloud Tasks (queue management)
../.venv/bin/python examples/example_cloud_tasks.py

# Pub/Sub (messaging)
../.venv/bin/python examples/example_pubsub.py

# Secret Manager
../.venv/bin/python examples/example_secret_manager.py

# Workflows (orchestration)
../.venv/bin/python examples/example_workflows.py

# IAM (service accounts and policies)
../.venv/bin/python examples/example_iam.py

# Docker build and Cloud Run deployment
../.venv/bin/python examples/example_docker_cloudrun_deploy.py

# Multi-service integration
../.venv/bin/python examples/example_all_services.py
```

**Example Requirements:**
- Valid GCP project and credentials
- `.env` file with real `GCP_PROJECT_ID` and optionally `GCP_CREDENTIALS_PATH`
- Appropriate GCP API permissions enabled for the service being tested

**Available Examples:**

All examples follow a consistent pattern with comprehensive documentation:

1. **example_firebase_auth.py** ✨ NEW - Firebase Authentication
   - User management and authentication
   - Custom claims and token generation
   - Email verification and password reset links
   - Best practices for user lifecycle

2. **example_cloud_run.py** ✨ NEW - Cloud Run (Simple Deployment)
   - Service deployment from container images
   - Environment variables and configuration
   - Traffic splitting and canary deployments
   - Resource optimization tips

3. **example_cloud_tasks.py** ✨ NEW - Cloud Tasks
   - Queue creation with rate limiting
   - HTTP task creation (immediate and scheduled)
   - Task monitoring and cancellation
   - Common use cases

4. **example_pubsub.py** ✨ NEW - Pub/Sub Messaging
   - Topic and subscription management
   - Single and batch message publishing
   - Pull subscriptions with acknowledgments
   - Event-driven architecture patterns

5. **example_secret_manager.py** ✨ NEW - Secret Manager
   - Secret creation with labels and replication
   - Version management and rotation
   - Access control best practices
   - Binary data handling (certificates)

6. **example_workflows.py** ✨ NEW - Workflows Orchestration
   - Simple and complex workflow definitions
   - Parameterized workflows
   - Error handling patterns
   - Execution monitoring

7. **example_storage.py** - Cloud Storage
   - Bucket and blob operations
   - File uploads and downloads
   - Signed URLs

8. **example_firestore.py** - Firestore
   - Document CRUD operations
   - Queries and transactions
   - Batch operations

9. **example_firebase_hosting.py** - Firebase Hosting
   - Complete website deployment
   - Custom domain configuration
   - Version and release management

10. **example_iam.py** - IAM (Identity and Access Management)
    - Service account management
    - Service account keys
    - IAM policy configuration

11. **example_docker_cloudrun_deploy.py** - Full CI/CD Pipeline
    - Docker build and push to Artifact Registry
    - Cloud Run deployment
    - Complete workflow

12. **example_all_services.py** - Multi-Service Integration
    - Cross-service workflows
    - Integration patterns

## Architecture

### Controller Pattern
All GCP service integrations follow a consistent controller pattern:

1. **Controller Initialization**: Each controller takes `GCPSettings` and optional credentials
2. **Lazy Client Init**: Google Cloud clients are created on first use via `_get_client()`
3. **Error Wrapping**: All GCP API exceptions are caught and wrapped in custom exceptions from `exceptions.py`
4. **Type-Safe Returns**: All methods return typed models from `models/` or primitive types

Example controller structure:
```python
from ..config import GCPSettings, get_settings

class ServiceController:
    def __init__(
        self,
        settings: Optional[GCPSettings] = None,
        credentials: Optional[Credentials] = None
    ):
        """
        Initialize the controller.

        Args:
            settings: GCP configuration. If not provided, loads from environment/.env file.
            credentials: Optional custom credentials.
        """
        self._settings = settings or get_settings()  # Auto-load if not provided
        self._credentials = credentials
        self._client: Optional[Client] = None

    def _get_client(self) -> Client:
        """Lazy initialization of the GCP client."""
        if self._client is None:
            self._client = create_client(...)
        return self._client

    def operation(self, ...) -> ReturnType:
        """Public method that wraps GCP API calls."""
        try:
            client = self._get_client()
            result = client.api_method(...)
            return ReturnType(...)
        except GoogleAPIError as e:
            raise ServiceError(...) from e
```

**Key Points**:
- Make `settings` parameter `Optional[GCPSettings] = None`
- Use `settings or get_settings()` to auto-load from environment
- Update docstring to indicate settings loads from environment/.env if not provided
- Update class docstring example to show simple instantiation without settings

### Configuration System
- **Location**: `src/gcp_utils/config/settings.py`
- **Pattern**: Pydantic BaseSettings with environment variable support
- **Prefix**: All env vars are prefixed with `GCP_` (e.g., `GCP_PROJECT_ID`)
- **Required**: Only `project_id` is required; all other settings have sensible defaults
- **Auto-Loading**: Controllers automatically load settings from `.env` file if not provided
- **Usage**: Controllers accept optional `GCPSettings` instance; defaults to `get_settings()`

**Simple Usage** (Recommended):
```python
# Just works! Automatically loads from .env file
from gcp_utils.controllers import CloudStorageController

storage = CloudStorageController()
```

**Custom Settings** (When Needed):
```python
# Override settings explicitly
from gcp_utils.config import GCPSettings
from gcp_utils.controllers import CloudStorageController

settings = GCPSettings(project_id="custom-project", location="europe-west1")
storage = CloudStorageController(settings)
```

**Environment Variables** (.env file):
```bash
GCP_PROJECT_ID=my-project-id
GCP_LOCATION=us-central1
GCP_CREDENTIALS_PATH=/path/to/service-account.json
GCP_STORAGE_BUCKET=my-default-bucket
```

### Exception Hierarchy
All exceptions inherit from `GCPUtilitiesError` (base exception):
- Service-specific exceptions (e.g., `StorageError`, `FirestoreError`)
- Operation-specific exceptions (e.g., `ResourceNotFoundError`, `ValidationError`)
- When wrapping GCP exceptions, preserve the original exception via `from e`
- Always include descriptive `message` and optional `details` dict

### Type Safety
- **All functions must have type hints** for parameters and return values
- Use Pydantic models from `models/` for complex return types
- Controllers return domain models, not raw GCP API responses
- `mypy` runs in strict mode - all new code must pass type checking

### Binding Native GCP Objects to Pydantic Models

**Pattern**: Controllers should bind the actual GCP objects to Pydantic models using a private `_gcs_object` field. This provides users with both structured data (via Pydantic) and full API access (via the native object).

**Benefits**:
- ✅ **Structured Data**: Pydantic validation, serialization, type safety
- ✅ **Full API Access**: All native GCP methods available via `._gcs_object`
- ✅ **Convenience Methods**: Helper methods that delegate to the native object
- ✅ **Backward Compatible**: Existing code using Pydantic fields continues to work

**Example Implementation**:

```python
# In models/storage.py
from typing import TYPE_CHECKING, Optional
from pydantic import BaseModel, ConfigDict, PrivateAttr

if TYPE_CHECKING:
    from google.cloud.storage import Blob

class BlobMetadata(BaseModel):
    """Metadata for a Cloud Storage blob."""

    name: str
    size: int
    # ... other Pydantic fields ...

    # Bind the actual GCS object (private attribute, not serialized)
    _gcs_object: Optional["Blob"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Convenience methods that delegate to the GCS object
    def make_public(self) -> None:
        """Make the blob publicly accessible."""
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this metadata")
        self._gcs_object.make_public()
        self.public_url = self._gcs_object.public_url

    def download_as_bytes(self) -> bytes:
        """Download blob content as bytes."""
        if not self._gcs_object:
            raise ValueError("No GCS object bound to this metadata")
        return self._gcs_object.download_as_bytes()
```

**Controller Implementation**:

```python
# In controllers/storage.py
def _blob_to_metadata(self, blob: Blob) -> BlobMetadata:
    """Convert a Blob object to BlobMetadata model with bound GCS object."""
    return BlobMetadata(
        name=blob.name,
        size=blob.size or 0,
        # ... other fields ...
        _gcs_object=blob,  # Bind the actual GCS Blob object
    )
```

**Usage**:

```python
# Get blob metadata with bound GCS object
blob_meta = storage.get_blob_metadata("my-bucket", "file.txt")

# Use Pydantic model fields
print(f"Size: {blob_meta.size}")

# Access full GCS API directly
blob_meta._gcs_object.make_public()
blob_meta._gcs_object.download_to_filename("local.txt")

# Or use convenience methods
blob_meta.make_public()
signed_url = blob_meta.generate_signed_url()
```

**When to Use This Pattern**:
- ✅ When the underlying GCP SDK provides rich object APIs (like Blob, Bucket)
- ✅ When users might need access to methods beyond what we expose
- ✅ When the native object has many useful operations
- ❌ When the GCP SDK only returns simple dictionaries or primitives
- ❌ For REST-only APIs (like Firebase Hosting) where there's no rich object

## Firebase Hosting Controller - Special Considerations

The Firebase Hosting controller is unique because it uses the REST API instead of a gRPC client library. This requires special patterns:

### HTTP Client Pattern
Instead of using a Google Cloud client library, Firebase Hosting uses `httpx` for HTTP requests:

```python
class FirebaseHostingController:
    def __init__(self, settings: GCPSettings, credentials_obj: Optional[Credentials] = None):
        self._settings = settings
        self._credentials = credentials_obj
        self._api_base_url = "https://firebasehosting.googleapis.com/v1beta1"
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Lazy HTTP client initialization with authentication."""
        if self._client is None:
            # Get credentials and create authenticated HTTP client
            creds, _ = default()
            self._client = httpx.Client(
                headers={"Authorization": f"Bearer {creds.token}"},
                timeout=30.0,
            )
        return self._client
```

### File Upload Workflow
Firebase Hosting uses a hash-based file upload system:

1. **Hash files**: Calculate SHA256 hash for each file
2. **Populate files**: Send file manifest with hashes to API
3. **Upload missing files**: API returns which files it needs; upload only those
4. **Finalize version**: Mark version as ready for deployment
5. **Create release**: Deploy the finalized version

Key method:
```python
def deploy_site(
    self,
    site_id: str,
    files: dict[str, str],  # {"/index.html": "./public/index.html"}
    config: Optional[dict[str, Any]] = None,
    message: Optional[str] = None,
) -> dict[str, Any]:
    """One-step deployment: create version, upload files, finalize, release."""
```

### Helper Methods Pattern
Private helper methods for internal operations:

```python
def _calculate_file_hash(self, file_path: Path) -> str:
    """Calculate SHA256 hash - used internally by populate_files."""

def _make_request(self, method: str, endpoint: str, ...) -> dict[str, Any]:
    """Make authenticated HTTP request - used by all public methods."""
```

### Progress Feedback
The `deploy_site()` method prints progress updates. This is acceptable for deployment operations where users expect feedback:

```python
print(f"Creating version for site '{site_id}'...")
print(f"✓ Created version: {version_name}")
```

For other controllers, avoid printing unless it's a long-running operation.

## Artifact Registry & Docker Builder - Special Considerations

The Artifact Registry controller and Docker Builder utility enable complete CI/CD pipelines for containerized applications. Unlike most controllers, the Docker Builder uses subprocess calls instead of a Python SDK.

### Artifact Registry Controller Pattern
Follows the standard controller pattern with lazy client initialization:

```python
class ArtifactRegistryController:
    def __init__(self, settings: GCPSettings, credentials: Optional[Credentials] = None):
        self._settings = settings
        self._credentials = credentials
        self._client: Optional[ArtifactRegistryServiceClient] = None

    def _get_client(self) -> ArtifactRegistryServiceClient:
        """Lazy initialization of Artifact Registry client."""
        if self._client is None:
            self._client = ArtifactRegistryServiceClient(
                credentials=self._credentials or self._get_credentials()
            )
        return self._client
```

Key methods:
- `create_repository()` - Create Docker/Python/Maven repositories
- `get_docker_image_url()` - Generate full image URLs for deployments
- `configure_docker_auth()` - Set up Docker authentication with gcloud
- `list_docker_images()` - List all images in a repository

### Docker Builder Pattern - Subprocess Integration
The Docker Builder utility uses `subprocess` to execute Docker CLI commands since there's no official Python SDK for Docker operations:

```python
class DockerBuilder:
    """Utility for building and pushing Docker images."""

    def build_image(
        self,
        dockerfile_path: str,
        context_path: str,
        image_url: str,
        build_args: Optional[dict[str, str]] = None,
        platform: Optional[str] = None,
    ) -> dict[str, Any]:
        """Build a Docker image using subprocess."""
        cmd = ["docker", "build"]

        if platform:
            cmd.extend(["--platform", platform])  # Important for Cloud Run

        if build_args:
            for key, value in build_args.items():
                cmd.extend(["--build-arg", f"{key}={value}"])

        cmd.extend(["-t", image_url, "-f", dockerfile_path, context_path])

        # Execute subprocess
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
```

### Error Handling for Subprocess Calls
Docker Builder wraps subprocess errors in `ArtifactRegistryError`:

```python
try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return {"success": True, "image_url": image_url}
except subprocess.CalledProcessError as e:
    raise ArtifactRegistryError(
        message=f"Docker build failed: {e.stderr}",
        details={
            "command": " ".join(cmd),
            "stderr": e.stderr,
            "stdout": e.stdout,
        }
    ) from e
```

### CI/CD Workflow Pattern
Complete deployment pipeline combining Artifact Registry, Docker Builder, and Cloud Run:

```python
# 1. Create repository (one-time setup)
registry = ArtifactRegistryController(settings)
registry.create_repository("my-app", "us-central1", "DOCKER")

# 2. Build and push image
builder = DockerBuilder()
image_url = registry.get_docker_image_url("my-app", "us-central1", "api", "v1.0.0")
builder.build_and_push("./Dockerfile", ".", image_url, platform="linux/amd64")

# 3. Deploy to Cloud Run
cloud_run = CloudRunController(settings)
cloud_run.create_service("my-api", image_url, "us-central1")
```

### Platform Considerations
Always specify `platform="linux/amd64"` when building for Cloud Run, regardless of your local architecture:

```python
# Good - explicit platform for Cloud Run
builder.build_image(
    dockerfile_path="./Dockerfile",
    context_path=".",
    image_url=image_url,
    platform="linux/amd64",  # Required for Cloud Run
)

# Bad - may fail on ARM Macs when deploying to Cloud Run
builder.build_image(
    dockerfile_path="./Dockerfile",
    context_path=".",
    image_url=image_url,
    # No platform specified
)
```

### Docker Authentication
Before pushing images, Docker must be authenticated with GCP:

```python
# Method 1: Use controller helper (recommended)
registry.configure_docker_auth("us-central1")

# Method 2: Manual gcloud command
# gcloud auth configure-docker us-central1-docker.pkg.dev
```

The controller method executes `gcloud auth configure-docker` via subprocess.

### Image URL Format
Artifact Registry uses a specific URL format:

```
{location}-docker.pkg.dev/{project_id}/{repository_id}/{image_name}:{tag}

Example:
us-central1-docker.pkg.dev/my-project/my-app/api:v1.0.0
```

Use `get_docker_image_url()` to generate correctly formatted URLs:

```python
image_url = registry.get_docker_image_url(
    repository_id="my-app",
    location="us-central1",
    image_name="api",
    tag="v1.0.0",
)
# Returns: us-central1-docker.pkg.dev/my-project/my-app/api:v1.0.0
```

## Adding New Controllers

When adding a new GCP service controller:

1. **Create controller file**: `src/gcp_utils/controllers/service_name.py`
2. **Follow the pattern**:
   - Constructor takes `GCPSettings` and optional `Credentials`
   - Lazy client initialization via `_get_client()`
   - Wrap all exceptions in custom exception type
   - Use type hints everywhere

3. **Create models** (if needed): `src/gcp_utils/models/service_name.py`
   - Use Pydantic `BaseModel` for all models
   - Include docstrings and field descriptions
   - Add validation where appropriate

4. **Add custom exception**: Update `src/gcp_utils/exceptions.py`
   - Inherit from `GCPUtilitiesError`
   - Use descriptive error messages

5. **Update exports**:
   - Add to `src/gcp_utils/controllers/__init__.py`
   - Add to `src/gcp_utils/models/__init__.py` (if models created)

6. **Add settings**: Update `src/gcp_utils/config/settings.py`
   - Add service-specific settings with defaults
   - Follow naming convention: `{service_name}_{setting}`

7. **Create example**: Add `examples/example_service_name.py`
   - Demonstrate key functionality
   - Include error handling
   - Add comments explaining usage

8. **Update dependencies**: Add GCP client library to `pyproject.toml`

## Code Style Rules

### Type Hints
```python
# Good - explicit types
def get_document(self, collection: str, document_id: str) -> FirestoreDocument:
    ...

# Bad - no types
def get_document(self, collection, document_id):
    ...
```

### Error Handling
```python
# Good - wrap and preserve original exception
try:
    result = client.operation()
except GoogleAPIError as e:
    raise ServiceError(
        message=f"Failed to perform operation: {str(e)}",
        details={"operation": "name", "error": str(e)}
    ) from e

# Bad - generic exception
try:
    result = client.operation()
except Exception as e:
    raise Exception(f"Error: {e}")
```

### Docstrings
Use Google-style docstrings for all public methods:
```python
def create_document(
    self,
    collection: str,
    data: dict[str, Any],
    document_id: Optional[str] = None
) -> FirestoreDocument:
    """
    Create a new document in a Firestore collection.

    Args:
        collection: Name of the collection
        data: Document data as a dictionary
        document_id: Optional document ID (auto-generated if not provided)

    Returns:
        FirestoreDocument containing the created document data

    Raises:
        FirestoreError: If document creation fails
        ValidationError: If data is invalid

    Example:
        ```python
        doc = firestore.create_document(
            collection="users",
            data={"name": "John", "email": "john@example.com"}
        )
        ```
    """
```

## Important Patterns & Conventions

### Credential Handling
- Never hardcode credentials
- Support both service account JSON and Application Default Credentials
- Let controllers accept optional `Credentials` for custom auth
- Validate credential paths in settings

### Client Lifecycle
- Always use lazy initialization for GCP clients
- Store client as `_client` (private attribute)
- Create via `_get_client()` method
- Don't create multiple clients per controller instance

### Method Naming
- Use verb-first naming: `create_`, `get_`, `update_`, `delete_`, `list_`
- Be explicit: `create_http_task()` not `create_task()`
- Avoid abbreviations: `destination_blob_name` not `dest_blob`

### Return Values
- Return Pydantic models for complex data
- Return simple types (str, int, bool) for simple operations
- Return lists of models for batch operations
- Return `None` for operations with no meaningful return value

### Settings Access
- Controllers store settings as `self._settings`
- Access via `self._settings.project_id`, not individual parameters
- Add new settings to `GCPSettings` class, not as constructor params

## Testing Guidelines

When writing tests:
- Mock GCP clients, don't make real API calls
- Test error handling paths, not just happy paths
- Use `pytest.raises()` for exception testing
- Create fixtures for common test data
- Mark integration tests with `@pytest.mark.integration`
- Mark slow tests with `@pytest.mark.slow`

## IAM Controller - Service Account Management

The IAM controller provides comprehensive service account and IAM policy management capabilities. It follows the standard controller pattern with some notable features:

### Controller Initialization Pattern
```python
class IAMController:
    def __init__(
        self,
        settings: Optional[GCPSettings] = None,
        credentials: Optional[Credentials] = None
    ):
        self.settings = settings or get_settings()
        self._credentials = credentials
        self._client: Optional[iam_admin_v1.IAMClient] = None

    def _get_client(self) -> iam_admin_v1.IAMClient:
        """Lazy initialization of IAM Admin client."""
        if self._client is None:
            self._client = iam_admin_v1.IAMClient(credentials=self._credentials)
        return self._client
```

### Key Operations

**Service Account Management:**
- `create_service_account()` - Create new service accounts with display name and description
- `get_service_account()` - Retrieve service account details by email
- `list_service_accounts()` - List all service accounts in the project
- `update_service_account()` - Update display name or description
- `delete_service_account()` - Delete a service account
- `get_service_account_info()` - Get account details with key statistics

**Service Account Key Management:**
- `create_service_account_key()` - Create new keys (returns base64-encoded JSON)
- `list_service_account_keys()` - List all keys for an account
- `delete_service_account_key()` - Delete a specific key

**IAM Policy Management:**
- `get_iam_policy()` - Retrieve IAM policy for a resource
- `set_iam_policy()` - Update IAM policy with new bindings

### Service Account Key Handling

When creating keys, the controller returns a `ServiceAccountKey` object with `private_key_data` containing the base64-encoded JSON credentials file:

```python
key = iam.create_service_account_key(
    email="my-sa@project.iam.gserviceaccount.com",
    key_algorithm=ServiceAccountKeyAlgorithm.KEY_ALG_RSA_2048
)

# Save to file
import base64
key_json = base64.b64decode(key.private_key_data)
with open("service-account-key.json", "wb") as f:
    f.write(key_json)
```

**Important**: Store service account keys securely. Never commit them to version control.

### IAM Policy Management Pattern

The IAM controller uses Pydantic models for type-safe policy management:

```python
# Get current policy
policy = iam.get_iam_policy(f"projects/{project_id}")

# Add new binding
from gcp_utils.models.iam import IAMBinding
new_binding = IAMBinding(
    role="roles/viewer",
    members=["serviceAccount:my-sa@project.iam.gserviceaccount.com"]
)
policy.bindings.append(new_binding)

# Update policy
updated_policy = iam.set_iam_policy(f"projects/{project_id}", policy)
```

### Models

The IAM controller uses the following Pydantic models:

**ServiceAccount**: Core service account information
- name: Resource name
- project_id, unique_id, email
- display_name, description
- oauth2_client_id
- disabled: Whether the account is disabled

**ServiceAccountKey**: Key information
- name: Resource name
- key_algorithm: Algorithm used (RSA_1024, RSA_2048)
- key_type: USER_MANAGED or SYSTEM_MANAGED
- private_key_data: Base64-encoded key (only on creation)
- valid_after_time, valid_before_time: Validity period

**IAMPolicy**: IAM policy document
- version: Policy version (1 or 3 for conditional policies)
- bindings: List of IAMBinding objects
- etag: For concurrency control

**IAMBinding**: Role binding
- role: Role identifier (e.g., "roles/viewer")
- members: List of members (e.g., "user:email@example.com", "serviceAccount:...")
- condition: Optional condition for conditional bindings

**ServiceAccountInfo**: Extended account information
- account: ServiceAccount details
- keys_count: Total number of keys
- user_managed_keys_count: Count of user-managed keys
- system_managed_keys_count: Count of system-managed keys

### Common Use Cases

**1. Create service account with key:**
```python
iam = IAMController()

# Create service account
account = iam.create_service_account(
    account_id="my-app-sa",
    display_name="My App Service Account"
)

# Create key
key = iam.create_service_account_key(account.email)

# Save key to file
import base64
with open("key.json", "wb") as f:
    f.write(base64.b64decode(key.private_key_data))
```

**2. Audit service accounts:**
```python
iam = IAMController()

# List all accounts
accounts = iam.list_service_accounts()

for account in accounts:
    info = iam.get_service_account_info(account.email)
    print(f"{account.email}: {info.user_managed_keys_count} keys")
```

**3. Grant role to service account:**
```python
iam = IAMController()

# Get current policy
resource = f"projects/{iam.settings.project_id}"
policy = iam.get_iam_policy(resource)

# Add binding
policy.bindings.append(IAMBinding(
    role="roles/storage.admin",
    members=[f"serviceAccount:{service_account_email}"]
))

# Update policy
iam.set_iam_policy(resource, policy)
```

### Error Handling

All IAM operations wrap Google API exceptions in `IAMError`:

```python
from gcp_utils.exceptions import IAMError, ResourceNotFoundError

try:
    account = iam.get_service_account("nonexistent@project.iam.gserviceaccount.com")
except ResourceNotFoundError as e:
    print(f"Account not found: {e.message}")
except IAMError as e:
    print(f"IAM error: {e.message}")
    print(f"Details: {e.details}")
```

### Security Considerations

1. **Key Management**: Service account keys are long-lived credentials. Use key rotation policies.
2. **Least Privilege**: Grant only the minimum required roles
3. **Key Storage**: Never commit keys to version control. Use secret management services.
4. **Audit**: Regularly audit service accounts and their keys using `list_service_accounts()` and `get_service_account_info()`
5. **Cleanup**: Delete unused service accounts and keys

## Cloud Logging Controller - Best Practices

The Cloud Logging controller follows Google's recommended patterns for Python logging integration.

### Python Logging Integration (Recommended Pattern)

Google recommends using `setup_logging()` to integrate Cloud Logging with Python's standard logging module. This allows you to use standard Python logging while automatically sending logs to Google Cloud.

```python
from gcp_utils.controllers import CloudLoggingController
import logging

# Initialize controller
logging_ctrl = CloudLoggingController()

# Setup integration with Python logging (recommended)
logging_ctrl.setup_logging()

# Now use standard Python logging
logging.info("Application started")
logging.error("An error occurred")

# Structured logging with JSON fields
logging.info("User action", extra={"json_fields": {"user_id": "123", "action": "login"}})
```

### Direct Log Writing

For cases where you need more control or don't want to use Python's logging module:

```python
from gcp_utils.controllers import CloudLoggingController
from gcp_utils.models.cloud_logging import LogSeverity

logging_ctrl = CloudLoggingController()

# Write structured logs directly
logging_ctrl.write_log(
    log_name="my-app-log",
    message={"event": "user_action", "user_id": "123"},
    severity=LogSeverity.INFO,
    labels={"environment": "production"}
)
```

### Key Features

- **Python logging integration**: Use `setup_logging()` for seamless integration with standard library
- **Structured logging**: Support for JSON payloads using `extra={"json_fields": {...}}`
- **Log querying**: Query logs with filters
- **Log-based metrics**: Create metrics from log patterns
- **Log sinks**: Export logs to BigQuery, Cloud Storage, or Pub/Sub

## Cloud Run Jobs - Batch Processing & Scheduled Tasks

The Cloud Run controller supports both **Services** (always-on HTTP containers) and **Jobs** (batch/scheduled tasks). Cloud Run Jobs are ideal for workloads that run to completion rather than serving requests.

### Services vs Jobs

| Aspect | Services | Jobs |
|--------|----------|------|
| **Purpose** | Long-running HTTP services | Batch/scheduled workloads |
| **Invocation** | Always available via URL | Triggered on-demand or by schedule |
| **Response** | HTTP response expected | No client connection needed |
| **Scaling** | Scales with request volume | Scales with execution count |
| **Client** | `run_v2.ServicesClient` | `run_v2.services.jobs.JobsClient` |
| **Billing** | Per request/instance time | Per task execution time |
| **Idle Cost** | Scales to zero but may keep warm instances | No cost when not running |

### Controller Implementation

The CloudRunController handles both services and jobs through separate clients:

```python
from gcp_utils.controllers import CloudRunController
from gcp_utils.models.cloud_run import ExecutionEnvironment, ExecutionStatus

# Initialize controller (handles both services and jobs)
run_ctrl = CloudRunController()

# Service operations
service = run_ctrl.create_service("my-api", "gcr.io/project/api:latest")

# Job operations
job = run_ctrl.create_job("batch-processor", "gcr.io/project/batch:latest")
```

### Job Lifecycle

**1. Create Job Definition:**
```python
job = run_ctrl.create_job(
    job_name="data-processor",
    image="gcr.io/my-project/processor:latest",
    task_count=10,  # Number of tasks per execution
    parallelism=3,  # Run 3 tasks concurrently
    max_retries=2,  # Retry failed tasks
    timeout=600,  # 10 minute timeout per task
    cpu="1000m",
    memory="512Mi",
    env_vars={"BATCH_SIZE": "100"},
    execution_environment=ExecutionEnvironment.EXECUTION_ENVIRONMENT_GEN2,
)
```

**2. Run Execution:**
```python
execution = run_ctrl.run_job("data-processor")
print(f"Execution ID: {execution.execution_id}")
print(f"Status: {execution.status}")
```

**3. Monitor Progress:**
```python
import time

while execution.status == ExecutionStatus.RUNNING:
    time.sleep(5)
    execution = run_ctrl.get_execution("data-processor", execution.execution_id)
    print(f"Progress: {execution.succeeded_count}/{execution.task_count} tasks")
```

**4. Manage Executions:**
```python
# List all executions
executions = run_ctrl.list_executions("data-processor")

# Cancel running execution
cancelled = run_ctrl.cancel_execution("data-processor", "execution-abc123")

# Get execution details
details = run_ctrl.get_execution("data-processor", "execution-abc123")
```

### Job Models

**CloudRunJob** - Job definition and configuration:
- `name`, `region`, `image` - Basic identification
- `task_count`, `parallelism` - Execution configuration
- `max_retries`, `timeout` - Failure handling
- `cpu`, `memory` - Resource allocation
- `env_vars`, `service_account` - Runtime configuration
- `execution_environment` - GEN1 or GEN2
- `_job_object` - Native Job object binding

**JobExecution** - Execution instance and status:
- `execution_id`, `job_name` - Identification
- `status` - PENDING, RUNNING, SUCCEEDED, FAILED, CANCELLED
- `task_count`, `succeeded_count`, `failed_count` - Task tracking
- `created`, `started`, `completed` - Timing
- `duration_seconds` - Total execution time
- `_execution_object` - Native Execution object binding

**ExecutionStatus** - Status enum:
- `PENDING` - Waiting to start
- `RUNNING` - Currently executing
- `SUCCEEDED` - All tasks completed successfully
- `FAILED` - One or more tasks failed
- `CANCELLED` - Execution was cancelled

### Key Patterns

**1. Parallel Processing:**
```python
# Process 100 items with 10 concurrent workers
job = run_ctrl.create_job(
    job_name="parallel-processor",
    image="gcr.io/project/worker:latest",
    task_count=100,  # 100 total tasks
    parallelism=10,  # 10 running at once
)

# Each task gets CLOUD_RUN_TASK_INDEX (0-99)
# Use this to partition work across tasks
```

**2. Idempotent Tasks:**
```python
# Design tasks to be safely retried
job = run_ctrl.create_job(
    job_name="idempotent-job",
    image="gcr.io/project/processor:latest",
    max_retries=3,  # Retry failed tasks
    env_vars={
        "USE_CHECKPOINTING": "true",  # Save progress
        "DEDUPE_ENABLED": "true",  # Handle duplicates
    },
)
```

**3. Resource Optimization:**
```python
# Right-size resources for cost efficiency
job = run_ctrl.create_job(
    job_name="optimized-job",
    image="gcr.io/project/batch:latest",
    cpu="500m",  # Half CPU for lightweight tasks
    memory="256Mi",  # Minimal memory
    timeout=300,  # 5 minute timeout
)
```

**4. Monitoring and Alerting:**
```python
# Check execution results
execution = run_ctrl.get_execution("my-job", "execution-id")

if execution.status == ExecutionStatus.FAILED:
    print(f"Failed tasks: {execution.failed_count}")
    print(f"Error: {execution.error_message}")
    # Send alert, trigger retry, etc.
```

### Common Use Cases

**Batch Processing:**
- ETL pipelines
- Data transformations
- Report generation
- Image/video processing

**Scheduled Tasks:**
- Nightly backups
- Weekly analytics
- Monthly billing
- Database maintenance

**Parallel Workloads:**
- Bulk API calls
- Distributed testing
- File conversions
- ML batch inference

### Best Practices

**1. Task Partitioning:**
- Use `CLOUD_RUN_TASK_INDEX` environment variable (0 to task_count-1)
- Partition data evenly across tasks
- Handle partial failures gracefully

**2. Timeouts:**
- Set realistic timeouts based on task complexity
- Default: 600s (10 minutes)
- Maximum: 3600s (1 hour)
- Add buffer for retries and startup time

**3. Parallelism:**
- Balance throughput vs. cost
- Consider downstream service capacity
- Monitor quota limits
- Start conservative, scale up based on metrics

**4. Error Handling:**
- Design for retry safety (idempotency)
- Use structured logging for debugging
- Set up alerting for failed executions
- Implement circuit breakers for external dependencies

**5. Cost Optimization:**
- Use GEN2 execution environment (default)
- Right-size CPU and memory
- Jobs only bill for execution time
- No charges when idle

**6. Integration with Cloud Scheduler:**
```bash
# Create scheduled job execution via Cloud Scheduler HTTP target
# Target: https://run.googleapis.com/v2/projects/PROJECT/locations/REGION/jobs/JOB_NAME:run
# Method: POST
# Auth: Service account with Cloud Run Invoker role
```

### Testing

Tests for Cloud Run Jobs follow the same patterns as service tests:

```python
def test_create_job_success(cloud_run_controller):
    """Test creating a job successfully."""
    mock_operation = MagicMock()
    mock_job = create_mock_job()
    mock_operation.result.return_value = mock_job
    cloud_run_controller.jobs_client.create_job.return_value = mock_operation

    job = cloud_run_controller.create_job(
        job_name="test-job",
        image="gcr.io/test/image:latest",
        task_count=10,
    )

    assert job.name == "test-job"
    assert job.task_count == 10
```

See `tests/test_cloud_run_jobs.py` for comprehensive job testing examples.

### Example

See `examples/example_cloud_run_jobs.py` for a complete demonstration including:
- Creating jobs with different configurations
- Running and monitoring executions
- Parallel task processing
- Updating job configuration
- Cancelling executions
- Best practices and common patterns

## Latest Library Versions & Standards (2025)

This section tracks the latest Google Cloud library versions and best practices as of January 2025.

### Current Library Versions

| Service | Library | Minimum Version | Latest Available | Notes |
|---------|---------|----------------|------------------|-------|
| Storage | `google-cloud-storage` | 3.5.0 | 3.x | Stable, integrated resumable-media |
| Firestore | `google-cloud-firestore` | 2.21.0 | 2.21.0 | AsyncClient available |
| BigQuery | `google-cloud-bigquery` | 3.38.0 | 3.38.0 | Requires Python >=3.9, OpenTelemetry support |
| Artifact Registry | `google-cloud-artifact-registry` | 1.16.0 | 1.16.1 | AsyncClient available |
| Cloud Run | `google-cloud-run` | 0.12.0 | 0.12.0 | **Uses v2 API** (run_v2) |
| Cloud Tasks | `google-cloud-tasks` | 2.20.0 | 2.20.0 | AsyncClient available |
| Cloud Functions | `google-cloud-functions` | 1.21.0 | 1.21.0 | **Uses v2 API** (functions_v2) |
| Cloud Scheduler | `google-cloud-scheduler` | 2.16.0 | 2.16.0 | Stable |
| Cloud Build | `google-cloud-build` | 3.31.0 | 3.31.3 | Stable |
| Workflows | `google-cloud-workflows` | 1.18.0 | 1.18.1 | Stable |
| Pub/Sub | `google-cloud-pubsub` | 2.33.0 | 2.33.0 | Future-based async |
| Secret Manager | `google-cloud-secret-manager` | 2.25.0 | 2.25.0 | Stable |
| IAM | `google-cloud-iam` | 2.19.0 | 2.19.1+ | Stable |
| Logging | `google-cloud-logging` | 3.12.0 | 3.12.1 | **setup_logging() recommended** |
| Firebase Admin | `firebase-admin` | **7.1.0** | **7.1.0** | **Python 3.10+ recommended** |

### API Version Best Practices

#### Cloud Run - Always Use v2 API
```python
from google.cloud import run_v2  # ✓ Correct - v2 API

# Don't use v1 for new code
client = run_v2.ServicesClient()
```

#### Cloud Functions - Use v2 API (Gen2)
```python
from google.cloud import functions_v2  # ✓ Correct - Gen2/v2 API

# Gen2 functions are now called "Cloud Run functions"
client = functions_v2.FunctionServiceClient()
```

#### Cloud Logging - Use setup_logging()
```python
# ✓ Recommended pattern
logging_ctrl.setup_logging()
import logging
logging.info("Message")

# ✗ Less recommended - more verbose
logging_ctrl.write_log("log-name", "Message")
```

#### Firebase Admin - Version 7.x Changes
- Python 3.9 support is **deprecated**
- Python 3.10+ strongly recommended
- New: `link_domain` in ActionCodeSettings (replaces `dynamic_link_domain`)
- Improved emulator support via `FIREBASE_AUTH_EMULATOR_HOST`

### Async Client Support

The following services now provide async clients:

```python
# Firestore
from google.cloud.firestore_v1 import AsyncClient
async_client = AsyncClient()

# Cloud Tasks
from google.cloud.tasks_v2 import CloudTasksAsyncClient
async_client = CloudTasksAsyncClient()

# Artifact Registry
from google.cloud.artifactregistry_v1 import ArtifactRegistryAsyncClient
async_client = ArtifactRegistryAsyncClient()
```

**Note**: Our controllers currently use synchronous clients. Async support can be added in future versions if needed.

### OpenTelemetry Support

Several libraries now support OpenTelemetry for distributed tracing:

- **BigQuery**: Set `ENABLE_OTEL_TRACES` environment variable
- **Cloud Storage**: Set `ENABLE_GCS_PYTHON_CLIENT_OTEL_TRACES` environment variable

### Migration Notes

If upgrading from older versions:

1. **Firebase Admin 6.x → 7.x**: Check Python version (3.10+ recommended)
2. **Cloud Run**: Ensure using `run_v2` API (already implemented)
3. **Cloud Functions**: Ensure using `functions_v2` API (already implemented)
4. **Cloud Logging**: Consider migrating to `setup_logging()` pattern

## Environment Configuration

Required environment variable:
- `GCP_PROJECT_ID`: Your GCP project ID

Optional but recommended:
- `GCP_CREDENTIALS_PATH`: Path to service account JSON
- `GCP_LOCATION`: Default region (default: `us-central1`)
- `GCP_FIREBASE_HOSTING_DEFAULT_SITE`: Default Firebase Hosting site ID

Service-specific settings are available for each controller. See `config/settings.py` for the complete list.

## Common Pitfalls to Avoid

1. **Don't bypass the controller pattern** - Always use controllers, never instantiate GCP clients directly
2. **Don't catch generic exceptions** - Catch specific GCP exceptions and wrap them
3. **Don't skip type hints** - All functions must be fully typed
4. **Don't return raw API responses** - Always convert to domain models
5. **Don't initialize clients in `__init__`** - Use lazy initialization
6. **Don't add dependencies without pinning versions** - Specify minimum versions in `pyproject.toml`

## Key Files Reference

- `src/gcp_utils/config/settings.py` - Configuration management
- `src/gcp_utils/exceptions.py` - Exception hierarchy
- `src/gcp_utils/controllers/__init__.py` - Controller exports
- `src/gcp_utils/controllers/firebase_hosting.py` - Firebase Hosting with deployment (1000+ lines)
- `src/gcp_utils/controllers/artifact_registry.py` - Artifact Registry controller (600+ lines)
- `src/gcp_utils/controllers/iam.py` - IAM controller for service accounts and policies (600+ lines)
- `src/gcp_utils/models/firebase_hosting.py` - Hosting models and enums
- `src/gcp_utils/models/artifact_registry.py` - Artifact Registry models
- `src/gcp_utils/models/iam.py` - IAM models (ServiceAccount, IAMPolicy, etc.)
- `src/gcp_utils/utils/docker_builder.py` - Docker build and push utility (400+ lines)
- `pyproject.toml` - Project metadata, dependencies, tool configuration
- `.env.example` - Environment variable template
- `docs/firebase-hosting-deployment.md` - Complete deployment guide
- `examples/example_firebase_hosting.py` - Firebase Hosting usage examples
- `examples/example_docker_cloudrun_deploy.py` - Complete CI/CD workflow example
- `examples/example_iam.py` - IAM controller usage examples

## Troubleshooting

### Common Issues and Solutions

#### 1. ModuleNotFoundError: No module named 'gcp_utils'

**Problem**: Tests fail with `ModuleNotFoundError` when running pytest.

**Solution**: The package needs to be installed in editable mode in the virtual environment:
```bash
../.venv/bin/pip install -e ".[dev]"
```

Verify installation:
```bash
../.venv/bin/python -c "import gcp_utils; print(gcp_utils.__file__)"
```

#### 2. Python Version Mismatch

**Problem**: Error message: `ERROR: Package 'gcp-utils' requires a different Python: 3.11.14 not in '>=3.12'`

**Solution**: This project requires Python 3.12+. Use the correct Python version:
```bash
# Check Python version
python3.12 --version

# Recreate virtual environment with Python 3.12
cd /home/user && rm -rf .venv
python3.12 -m venv .venv

# Reinstall package
cd gcp-utils
../.venv/bin/pip install -e ".[dev]"
```

#### 3. Pydantic Validation Error in Tests

**Problem**: Tests fail with `pydantic_core._pydantic_core.ValidationError: 1 validation error for GCPSettings`

**Solution**: The `.env` file is missing or doesn't have required settings. Create/update `.env`:
```bash
# For tests, minimal .env file:
echo "GCP_PROJECT_ID=test-project" > .env
echo "GCP_LOCATION=us-central1" >> .env

# For examples, use real project:
echo "GCP_PROJECT_ID=your-actual-project-id" > .env
echo "GCP_CREDENTIALS_PATH=/path/to/service-account.json" >> .env
```

#### 4. Import Errors in Tests

**Problem**: `ImportError while importing test module`

**Solution**: Ensure you're using the virtual environment's pytest:
```bash
# Wrong - uses system pytest
pytest tests/

# Correct - uses venv pytest
../.venv/bin/pytest tests/
```

#### 5. Firebase Admin Already Initialized

**Problem**: `ValueError: The default Firebase app already exists`

**Solution**: This is expected behavior in tests. The controllers handle this automatically with:
```python
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app()
```

Tests mock this behavior, so no action needed.

#### 6. Tests Running Too Slowly

**Problem**: Test suite takes a long time to run.

**Solution**:
- Run specific test files instead of the entire suite:
  ```bash
  ../.venv/bin/pytest tests/test_firebase_auth.py
  ```
- Use pytest markers to skip slow tests:
  ```bash
  ../.venv/bin/pytest -m "not slow" tests/
  ```
- Run tests in parallel (requires pytest-xdist):
  ```bash
  ../.venv/bin/pytest -n auto tests/
  ```

#### 7. Virtual Environment Not Found

**Problem**: `../.venv/bin/python: No such file or directory`

**Solution**: The virtual environment doesn't exist. Create it:
```bash
cd /home/user
python3.12 -m venv .venv
cd gcp-utils
../.venv/bin/pip install -e ".[dev]"
```

#### 8. Package Dependencies Out of Date

**Problem**: Import errors or version conflicts.

**Solution**: Reinstall dependencies:
```bash
../.venv/bin/pip install --upgrade -e ".[dev]"
```

#### 9. Examples Fail with Authentication Errors

**Problem**: Examples fail with "Could not automatically determine credentials"

**Solution**: Examples require real GCP credentials:

**Option A**: Use service account key file:
```bash
# Set in .env file
GCP_CREDENTIALS_PATH=/path/to/service-account-key.json
```

**Option B**: Use Application Default Credentials:
```bash
gcloud auth application-default login
```

**Option C**: Set environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

#### 10. Type Checking Fails with mypy

**Problem**: `mypy src/` reports errors.

**Solution**: Ensure you're using the venv mypy and all stubs are installed:
```bash
../.venv/bin/pip install --upgrade mypy
../.venv/bin/mypy src/
```

Common mypy issues are usually missing type stubs for third-party libraries. These are ignored in `pyproject.toml`:
```toml
[[tool.mypy.overrides]]
module = ["google.*", "firebase_admin.*"]
ignore_missing_imports = true
```

### Quick Diagnostics

Run these commands to diagnose environment issues:

```bash
# 1. Check Python version
python3.12 --version

# 2. Check virtual environment exists
ls -la /home/user/.venv

# 3. Check package is installed
../.venv/bin/pip list | grep gcp-utils

# 4. Check .env file exists
cat .env

# 5. Test import
../.venv/bin/python -c "from gcp_utils.controllers import CloudStorageController; print('✓ Import successful')"

# 6. Run minimal test
../.venv/bin/pytest tests/test_import.py -v

# 7. Check all tools available
../.venv/bin/pytest --version
../.venv/bin/mypy --version
../.venv/bin/black --version
../.venv/bin/ruff --version
```

### Getting Help

If issues persist:

1. Check this troubleshooting guide
2. Review error messages carefully - they often indicate the exact problem
3. Verify virtual environment setup
4. Ensure `.env` file is configured correctly
5. Check that all dependencies are installed
6. Review the test file patterns in existing tests for examples
