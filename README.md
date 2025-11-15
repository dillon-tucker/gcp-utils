# GCP Utilities

A comprehensive, production-ready Python package for Google Cloud Platform (GCP) services. Built with modern Python practices, type safety, and developer experience in mind.

## Features

- **Type-safe**: Full type hints throughout the codebase
- **Modern Python**: Requires Python 3.12+, uses latest best practices
- **Production-ready**: Comprehensive error handling, logging, and validation
- **Well-documented**: Extensive docstrings and examples
- **Easy configuration**: Environment-based configuration with Pydantic
- **Multiple services**: Support for 8+ major GCP services

## Supported GCP Services

- **Cloud Storage**: Bucket and blob operations, signed URLs, file transfers
- **Firestore**: NoSQL database operations, queries, transactions, batch operations
- **Firebase Authentication**: User management, token verification, custom claims
- **Firebase Hosting**: Website deployment, custom domains, file uploads, version management
- **Artifact Registry**: Docker image storage, repository management, CI/CD integration
- **Cloud Run**: Container deployment and management, traffic splitting
- **Workflows**: Service orchestration, execution management
- **Cloud Tasks**: Task queue management, HTTP tasks, scheduling
- **Pub/Sub**: Message publishing, subscriptions, push/pull delivery
- **Secret Manager**: Secure secret storage and versioning

**Utilities:**
- **Docker Builder**: Build and push Docker images for Cloud Run deployments

## Installation

### Using uv (recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/gcp-utilities.git
cd gcp-utilities

# Install with uv
uv pip install -e .

# Install with development dependencies
uv pip install -e ".[dev]"
```

### Using pip

```bash
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

## Quick Start

### 1. Configuration

Create a `.env` file in your project root:

```env
GCP_PROJECT_ID=my-gcp-project
GCP_CREDENTIALS_PATH=/path/to/service-account.json
GCP_LOCATION=us-central1
GCP_STORAGE_BUCKET=my-default-bucket
```

Or set configuration programmatically:

```python
from gcp_utilities.config import GCPSettings

settings = GCPSettings(
    project_id="my-gcp-project",
    credentials_path="/path/to/service-account.json",
    location="us-central1",
)
```

### 2. Using Controllers

#### Cloud Storage

```python
from gcp_utilities.config import GCPSettings
from gcp_utilities.controllers import CloudStorageController

settings = GCPSettings(project_id="my-project")
storage = CloudStorageController(settings)

# Upload a file
result = storage.upload_file(
    bucket_name="my-bucket",
    source_path="local_file.txt",
    destination_blob_name="uploads/file.txt",
)

# Download a file
storage.download_file(
    bucket_name="my-bucket",
    blob_name="uploads/file.txt",
    destination_path="downloaded.txt",
)

# List blobs
blobs = storage.list_blobs(
    bucket_name="my-bucket",
    prefix="uploads/",
)
```

#### Firestore

```python
from gcp_utilities.controllers import FirestoreController
from gcp_utilities.models.firestore import FirestoreQuery, QueryOperator

firestore = FirestoreController(settings)

# Create a document
doc = firestore.create_document(
    collection="users",
    data={"name": "John Doe", "email": "john@example.com"},
    document_id="user123",
)

# Query documents
queries = [
    FirestoreQuery(
        field="age",
        operator=QueryOperator.GREATER_THAN,
        value=25,
    )
]
results = firestore.query_documents("users", queries)

# Run a transaction
def update_balance(transaction, user_id, amount):
    doc_ref = firestore.client.collection('users').document(user_id)
    snapshot = doc_ref.get(transaction=transaction)
    new_balance = snapshot.get('balance') + amount
    transaction.update(doc_ref, {'balance': new_balance})
    return new_balance

new_balance = firestore.run_transaction(update_balance, 'user123', 100)
```

#### Firebase Authentication

```python
from gcp_utilities.controllers import FirebaseAuthController

auth = FirebaseAuthController(settings)

# Create a user
user = auth.create_user(
    email="user@example.com",
    password="securepassword123",
    display_name="John Doe",
)

# Verify ID token
decoded_token = auth.verify_id_token(id_token, check_revoked=True)

# Set custom claims
auth.set_custom_user_claims(user["uid"], {"admin": True, "tier": "premium"})
```

#### Firebase Hosting

```python
from gcp_utilities.controllers import FirebaseHostingController

hosting = FirebaseHostingController(settings)

# Deploy a website with one command!
result = hosting.deploy_site(
    site_id="my-site",
    files={
        "/index.html": "./public/index.html",
        "/css/style.css": "./public/css/style.css",
        "/js/app.js": "./public/js/app.js",
    },
    config={
        "redirects": [{"source": "/old", "destination": "/new", "type": 301}],
        "headers": [{"source": "**/*.css", "headers": {"Cache-Control": "max-age=31536000"}}],
    },
    message="Production v1.0.0"
)

print(f"Deployed to: {result['site_url']}")

# Add custom domain
domain = hosting.add_custom_domain("my-site", "example.com")
print(f"Domain status: {domain['status']}")
```

#### Artifact Registry & Docker Builder

```python
from gcp_utilities.controllers import ArtifactRegistryController
from gcp_utilities.utils import DockerBuilder

registry = ArtifactRegistryController(settings)
builder = DockerBuilder()

# Create Docker repository
repo = registry.create_repository(
    repository_id="my-app-images",
    location="us-central1",
    format="DOCKER"
)

# Build and push Docker image
image_url = registry.get_docker_image_url(
    repository_id="my-app-images",
    location="us-central1",
    image_name="my-app",
    tag="v1.0.0"
)

result = builder.build_and_push(
    dockerfile_path="./Dockerfile",
    context_path=".",
    image_url=image_url,
    platform="linux/amd64"  # For Cloud Run
)

print(f"Image ready: {result['image_url']}")
```

#### Cloud Run

```python
from gcp_utilities.controllers import CloudRunController

cloud_run = CloudRunController(settings)

# Deploy a service
service = cloud_run.create_service(
    service_name="my-api",
    image="gcr.io/my-project/my-api:latest",
    cpu="1000m",
    memory="512Mi",
    max_instances=10,
    env_vars={"DATABASE_URL": "postgres://..."},
    allow_unauthenticated=True,
)

# Update traffic split
from gcp_utilities.models.cloud_run import TrafficTarget

cloud_run.update_traffic(
    service_name="my-api",
    traffic_targets=[
        TrafficTarget(revision_name="my-api-v1", percent=80),
        TrafficTarget(revision_name="my-api-v2", percent=20),
    ],
)
```

#### Workflows

```python
from gcp_utilities.controllers import WorkflowsController

workflows = WorkflowsController(settings)

# Create a workflow
workflow_definition = """
- step1:
    call: http.get
    args:
      url: https://api.example.com/data
    result: api_response
- step2:
    return: ${api_response.body}
"""

workflow = workflows.create_workflow(
    workflow_name="data-pipeline",
    source_contents=workflow_definition,
)

# Execute workflow
execution = workflows.execute_workflow(
    workflow_name="data-pipeline",
    argument={"input": "value"},
)
```

#### Cloud Tasks

```python
from gcp_utilities.controllers import CloudTasksController

tasks = CloudTasksController(settings)

# Create a queue
queue = tasks.create_queue(
    queue_name="email-queue",
    max_dispatches_per_second=10.0,
)

# Create an HTTP task
task = tasks.create_http_task(
    queue="email-queue",
    url="https://myapp.com/send-email",
    payload={"to": "user@example.com", "subject": "Welcome"},
    delay_seconds=60,  # Execute in 1 minute
)
```

#### Pub/Sub

```python
from gcp_utilities.controllers import PubSubController

pubsub = PubSubController(settings)

# Create a topic
topic = pubsub.create_topic("user-events")

# Publish a message
message_id = pubsub.publish_message(
    topic_name="user-events",
    data={"event": "user_created", "user_id": "123"},
    attributes={"source": "api", "version": "1.0"},
)

# Create a subscription
subscription = pubsub.create_subscription(
    topic_name="user-events",
    subscription_name="email-processor",
    ack_deadline_seconds=30,
)

# Pull messages
messages = pubsub.pull_messages(
    subscription_name="email-processor",
    max_messages=10,
)

# Acknowledge messages
ack_ids = [msg["ack_id"] for msg in messages]
pubsub.acknowledge_messages("email-processor", ack_ids)
```

#### Secret Manager

```python
from gcp_utilities.controllers import SecretManagerController

secrets = SecretManagerController(settings)

# Create a secret with value
version = secrets.create_secret_with_value(
    secret_id="database-password",
    payload="super-secure-password",
    labels={"environment": "production"},
)

# Access the secret
password = secrets.access_secret_version("database-password")

# Add a new version
new_version = secrets.add_secret_version(
    secret_id="database-password",
    payload="new-password",
)

# List all versions
versions = secrets.list_secret_versions("database-password")
```

## Error Handling

All controllers use custom exceptions for better error handling:

```python
from gcp_utilities.exceptions import (
    GCPUtilitiesError,
    StorageError,
    FirestoreError,
    ResourceNotFoundError,
    ValidationError,
)

try:
    doc = firestore.get_document("users", "nonexistent")
except ResourceNotFoundError as e:
    print(f"Document not found: {e.message}")
    print(f"Details: {e.details}")
except FirestoreError as e:
    print(f"Firestore error: {e.message}")
```

## Project Structure

```
gcp-utilities/
    src/
        gcp_utilities/
             __init__.py
        config/
           __init__.py
           settings.py          # Configuration management
        controllers/
           __init__.py
           storage.py           # Cloud Storage
           firestore.py         # Firestore
           firebase_auth.py     # Firebase Auth
           cloud_run.py         # Cloud Run
           workflows.py         # Workflows
           cloud_tasks.py       # Cloud Tasks
           pubsub.py            # Pub/Sub
           secret_manager.py    # Secret Manager
        models/
           __init__.py
           storage.py
           firestore.py
           cloud_run.py
           workflows.py
           tasks.py
        exceptions.py            # Custom exceptions
    examples/
        example_storage.py
        example_firestore.py
        example_all_services.py
    tests/                            # Test suite (to be implemented)
    pyproject.toml                    # Project configuration
    README.md
```

## Development

### Setup Development Environment

```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Run type checking
mypy src/

# Run linting
ruff check src/

# Format code
black src/
isort src/

# Run tests (when implemented)
pytest tests/
```

### Code Quality Tools

This project uses:

- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Static type checking
- **ruff**: Fast linting
- **pytest**: Testing framework

## Configuration Reference

### Environment Variables

All environment variables are prefixed with `GCP_`:

| Variable | Required | Default | Description |
|---|:---:|:---:|---|
| `GCP_PROJECT_ID` | Yes | - | GCP project ID |
| `GCP_CREDENTIALS_PATH` | No | None | Path to service account JSON |
| `GCP_LOCATION` | No | `us-central1` | Default GCP location |
| `GCP_STORAGE_BUCKET` | No | None | Default storage bucket |
| `GCP_FIRESTORE_DATABASE` | No | `(default)` | Firestore database ID |
| `GCP_CLOUD_RUN_REGION` | No | `us-central1` | Cloud Run region |
| `GCP_WORKFLOWS_LOCATION` | No | `us-central1` | Workflows location |
| `GCP_CLOUD_TASKS_LOCATION` | No | `us-central1` | Cloud Tasks location |
| `GCP_PUBSUB_TOPIC_PREFIX` | No | (empty) | Prefix for Pub/Sub topics |
| `GCP_FIREBASE_HOSTING_DEFAULT_SITE` | No | None | Default Firebase Hosting site ID |
| `GCP_ENABLE_REQUEST_LOGGING` | No | `False` | Enable detailed logging |
| `GCP_OPERATION_TIMEOUT` | No | `300` | Timeout for operations (seconds) |

### Credentials

The package supports multiple authentication methods:

1. **Service Account JSON**: Set `GCP_CREDENTIALS_PATH` to the JSON file path
2. **Application Default Credentials**: Leave `GCP_CREDENTIALS_PATH` unset
3. **Custom Credentials**: Pass credentials directly to controllers

```python
from google.auth import credentials

# Use custom credentials
storage = CloudStorageController(settings, credentials=my_credentials)
```

## Examples

See the `examples/` directory for complete working examples:

- `example_storage.py`: Cloud Storage operations
- `example_firestore.py`: Firestore operations
- `example_firebase_hosting.py`: Firebase Hosting deployment and custom domains
- `example_docker_cloudrun_deploy.py`: Complete Docker build, push, and Cloud Run deployment workflow
- `example_all_services.py`: Multi-service workflow

Run examples:

```bash
python examples/example_storage.py
python examples/example_firestore.py
python examples/example_firebase_hosting.py
python examples/example_docker_cloudrun_deploy.py
python examples/example_all_services.py
```

## Best Practices

1. **Use environment variables** for configuration in production
2. **Always handle exceptions** specific to each service
3. **Use type hints** for better IDE support and type safety
4. **Implement proper cleanup** in try/finally blocks for resources
5. **Use context managers** where applicable (coming soon)
6. **Enable logging** in development: `enable_request_logging=True`
7. **Set appropriate timeouts** for long-running operations
8. **Use batch operations** for multiple items when available

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Run type checking and linting
6. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:

- GitHub Issues: [Create an issue](https://github.com/yourusername/gcp-utilities/issues)
- Documentation: See docstrings in the code
- Examples: Check the `examples/` directory
- Detailed Guides: See the `docs/` directory for in-depth documentation

## Roadmap

- [ ] Async support for I/O-heavy operations
- [ ] Context managers for resource cleanup
- [ ] Additional GCP services (BigQuery, Cloud Functions, etc.)
- [ ] Comprehensive test suite
- [ ] Integration test examples
- [ ] Performance benchmarks
- [ ] CLI interface
- [ ] Docker support

## Changelog

### Version 0.1.0 (Initial Release)

- Cloud Storage controller with full CRUD operations
- Firestore controller with queries, transactions, batch operations
- Firebase Authentication controller with user management
- Firebase Hosting controller with:
  - Complete website deployment workflow
  - File upload with hash-based deduplication
  - Custom domain management
  - Version and release management
  - One-step deployment via `deploy_site()`
- Artifact Registry controller with:
  - Docker repository management
  - Image listing and metadata
  - Docker authentication configuration
  - Image URL generation for deployments
- Docker Builder utility with:
  - Build Docker images with custom platforms
  - Push images to Artifact Registry
  - Tag management
  - One-step `build_and_push()` method
- Cloud Run controller with deployment and traffic management
- Workflows controller with execution management
- Cloud Tasks controller with queue and task operations
- Pub/Sub controller with messaging operations
- Secret Manager controller with secure secret storage
- Comprehensive configuration management
- Type-safe models and exceptions
- Example scripts for all services including complete CI/CD workflow
