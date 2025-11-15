# Contributing to GCP Utils

Thank you for your interest in contributing to GCP Utils! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- UV package manager
- Git
- GCP account (for testing)

### Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/gcp-utils.git
cd gcp-utils
```

2. **Install dependencies**

```bash
# Install package in development mode with dev dependencies
uv pip install -e ".[dev]"
```

3. **Setup pre-commit hooks** (recommended)

```bash
# Install pre-commit
uv pip install pre-commit

# Setup hooks
pre-commit install
```

4. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your GCP project details
```

## Code Style

We use multiple tools to maintain code quality:

### Formatting

```bash
# Format code with black
black src/ tests/ examples/

# Sort imports with isort
isort src/ tests/ examples/
```

### Linting

```bash
# Lint with ruff
ruff check src/ tests/

# Fix automatically fixable issues
ruff check --fix src/ tests/
```

### Type Checking

```bash
# Type check with mypy
mypy src/
```

### Run All Checks

```bash
# Run all quality checks at once
black src/ tests/ examples/
isort src/ tests/ examples/
ruff check src/ tests/
mypy src/
```

## Code Standards

### Type Hints

All code must include type hints:

```python
# Good
def upload_file(self, bucket: str, path: Path) -> UploadResult:
    ...

# Bad
def upload_file(self, bucket, path):
    ...
```

### Docstrings

All public functions, classes, and methods must have docstrings:

```python
def create_document(
    self,
    collection: str,
    data: dict[str, Any],
    document_id: Optional[str] = None,
) -> FirestoreDocument:
    """
    Create a new document in a collection.

    Args:
        collection: Collection path
        data: Document data
        document_id: Optional document ID (auto-generated if not provided)

    Returns:
        FirestoreDocument with the created document details

    Raises:
        ValidationError: If data is invalid
        FirestoreError: If creation fails

    Example:
        >>> doc = firestore.create_document(
        ...     "users",
        ...     {"name": "John", "email": "john@example.com"}
        ... )
    """
    ...
```

### Error Handling

Always use custom exceptions:

```python
# Good
from ..exceptions import StorageError, ValidationError

try:
    result = self._operation()
except Exception as e:
    raise StorageError(
        f"Operation failed: {e}",
        details={"bucket": bucket_name, "error": str(e)}
    )

# Bad
try:
    result = self._operation()
except Exception:
    print("Error occurred")
```

### Import Order

Imports should be organized in this order:

1. Standard library
2. Third-party packages
3. Local imports

```python
# Standard library
from pathlib import Path
from typing import Any, Optional

# Third-party
from google.cloud import storage
from pydantic import BaseModel

# Local
from ..config import GCPSettings
from ..exceptions import StorageError
```

## Testing

### Writing Tests

Create tests in the `tests/` directory:

```python
# tests/test_storage.py
import pytest
from gcp_utils.controllers import CloudStorageController
from gcp_utils.exceptions import ValidationError


def test_upload_validates_path():
    """Test that upload validates file path."""
    controller = CloudStorageController(settings)

    with pytest.raises(ValidationError):
        controller.upload_file("bucket", "nonexistent.txt", "dest.txt")
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src/gcp_utils tests/

# Run specific test
pytest tests/test_storage.py::test_upload_validates_path

# Run with verbose output
pytest -v tests/
```

## Adding a New Controller

### 1. Create the Controller File

Create `src/gcp_utils/controllers/new_service.py`:

```python
"""
New Service controller for ...

This module provides a high-level interface for ...
"""

from typing import Any, Optional
from google.cloud import newservice_v1
from google.auth.credentials import Credentials

from ..config import GCPSettings
from ..exceptions import NewServiceError, ResourceNotFoundError

class NewServiceController:
    """
    Controller for Google Cloud New Service operations.

    Example:
        >>> settings = GCPSettings(project_id="my-project")
        >>> controller = NewServiceController(settings)
        >>> result = controller.operation()
    """

    def __init__(
        self,
        settings: GCPSettings,
        credentials: Optional[Credentials] = None,
    ) -> None:
        """Initialize the controller."""
        self.settings = settings
        try:
            self.client = newservice_v1.Client(
                project=settings.project_id,
                credentials=credentials,
            )
        except Exception as e:
            raise NewServiceError(
                f"Failed to initialize client: {e}",
                details={"error": str(e)},
            )
```

### 2. Add Exception

In `src/gcp_utils/exceptions.py`:

```python
class NewServiceError(GCPUtilitiesError):
    """Raised when New Service operations fail."""
    pass
```

### 3. Add Models (if needed)

Create `src/gcp_utils/models/new_service.py`:

```python
"""Data models for New Service operations."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class NewServiceResource(BaseModel):
    """Represents a New Service resource."""

    name: str = Field(..., description="Resource name")
    created: Optional[datetime] = Field(None, description="Creation time")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
```

### 4. Update __init__ Files

Update `src/gcp_utils/controllers/__init__.py`:

```python
from .new_service import NewServiceController

__all__ = [
    # ... existing
    "NewServiceController",
]
```

### 5. Add Dependencies

Update `pyproject.toml`:

```toml
dependencies = [
    # ... existing
    "google-cloud-newservice>=1.0.0",
]
```

### 6. Create Example

Create `examples/example_new_service.py`:

```python
"""Example usage of NewServiceController."""

from gcp_utils.config import GCPSettings
from gcp_utils.controllers import NewServiceController


def main():
    settings = GCPSettings(project_id="my-project")
    controller = NewServiceController(settings)

    # Example operations
    result = controller.operation()
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
```

### 7. Write Tests

Create `tests/test_new_service.py`:

```python
"""Tests for NewServiceController."""


def test_import():
    """Test that controller can be imported."""
    from gcp_utils.controllers import NewServiceController
    assert NewServiceController is not None
```

### 8. Update Documentation

Add section to README.md showing usage of the new controller.

## Submitting Changes

### Before Submitting

1. **Run all checks**

```bash
black src/ tests/ examples/
isort src/ tests/ examples/
ruff check src/ tests/
mypy src/
pytest tests/
```

2. **Update documentation**
   - Add docstrings to all new code
   - Update README.md if needed
   - Add example if adding new feature

3. **Test thoroughly**
   - Write tests for new functionality
   - Ensure all tests pass
   - Test with actual GCP services if possible

### Pull Request Process

1. **Create a branch**

```bash
git checkout -b feature/my-new-feature
```

2. **Make your changes**

3. **Commit with clear messages**

```bash
git add .
git commit -m "Add NewService controller with basic operations"
```

4. **Push to your fork**

```bash
git push origin feature/my-new-feature
```

5. **Create Pull Request**
   - Provide clear description
   - Reference any related issues
   - Include testing information

### Commit Message Guidelines

Use clear, descriptive commit messages:

```
# Good
Add Cloud Logging controller with basic operations
Fix resource cleanup in Cloud Run controller
Update documentation for Firestore queries

# Bad
fix bug
updates
wip
```

## Code Review Process

1. Maintainers will review your PR
2. Address any feedback
3. Once approved, PR will be merged

## Questions?

- Open an issue for bugs
- Start a discussion for feature requests
- Check existing issues/PRs first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to GCP Utils!
