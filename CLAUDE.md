# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-ready Python package providing type-safe controllers for Google Cloud Platform services. The package is built with Python 3.12+, uses UV for dependency management, and emphasizes type safety, comprehensive error handling, and developer experience.

## Development Commands

### Installation & Setup
```bash
# Install package in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Create .env file from template
cp .env.example .env
```

**Note**: This project uses a virtual environment located at `../.venv`. Always ensure you're using this virtual environment when running commands:
- On Windows: `../.venv/Scripts/python.exe`
- On Unix/macOS: `../.venv/bin/python`

**Important**: When adding new dependencies to `pyproject.toml`, install them using pip in the virtual environment:
```bash
# From the project root
cd .. && .venv/Scripts/python.exe -m pip install <package-name>

# Or on Unix/macOS
cd .. && .venv/bin/python -m pip install <package-name>
```

### Code Quality & Type Checking
```bash
# Type checking (strict mode) - REQUIRED before commits
mypy src/

# Linting (fast linter)
ruff check src/

# Code formatting
black src/
isort src/

# Run all checks
mypy src/ && ruff check src/ && black --check src/ && isort --check src/
```

### Testing
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src/gcp_utils tests/

# Run specific test file
pytest tests/test_import.py

# Run tests matching a pattern
pytest -k "test_pattern"
```

### Running Examples
```bash
# Cloud Storage example
python examples/example_storage.py

# Firestore example
python examples/example_firestore.py

# Firebase Hosting example (deployment)
python examples/example_firebase_hosting.py

# Docker build and Cloud Run deployment example
python examples/example_docker_cloudrun_deploy.py

# IAM (service accounts and policies) example
python examples/example_iam.py

# Multi-service integration example
python examples/example_all_services.py
```

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
