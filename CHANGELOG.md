# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD pipeline
- PyPI publishing workflow
- Comprehensive package metadata for PyPI
- MIT License
- Code quality badges in README

## [0.1.0] - 2025-01-20

### Added

#### Controllers
- **Cloud Storage**: Full CRUD operations for buckets and blobs
  - File upload/download with progress tracking
  - Signed URLs for temporary access
  - Bucket lifecycle management
  - Object metadata management

- **Firestore**: Complete NoSQL database operations
  - Document CRUD operations
  - Complex queries with multiple operators
  - Transactions for atomic operations
  - Batch operations for efficiency

- **Firebase Authentication**: User management and authentication
  - User CRUD operations
  - Email/password authentication
  - Custom claims for role-based access
  - Token generation and verification
  - Email verification and password reset links

- **Firebase Hosting**: Complete website deployment
  - Hash-based file upload with deduplication
  - Version and release management
  - Custom domain configuration
  - One-step `deploy_site()` method
  - Comprehensive deployment workflow

- **Artifact Registry**: Container image management
  - Docker repository creation and management
  - Image listing with metadata
  - Docker authentication configuration
  - Image URL generation for deployments

- **Cloud Run**: Container deployment and management
  - Service creation and updates
  - Traffic splitting for canary deployments
  - Environment variable configuration
  - Resource allocation (CPU, memory)
  - Service account configuration

- **Workflows**: Service orchestration
  - Workflow creation with YAML definitions
  - Execution management
  - Parameter passing
  - Execution monitoring

- **Cloud Tasks**: Task queue management
  - Queue creation with rate limiting
  - HTTP task creation
  - Task scheduling
  - Task cancellation

- **Pub/Sub**: Message publishing and subscriptions
  - Topic creation and management
  - Message publishing (single and batch)
  - Subscription management
  - Pull subscriptions with acknowledgments

- **Secret Manager**: Secure secret storage
  - Secret creation with labels
  - Version management
  - Secret rotation
  - Access control

- **IAM**: Identity and Access Management
  - Service account management
  - Service account key generation
  - IAM policy management
  - Role bindings

#### Utilities
- **Docker Builder**: Build and push Docker images
  - Multi-platform build support
  - Build arguments
  - Tag management
  - One-step `build_and_push()` method

#### Infrastructure
- **Configuration Management**: Pydantic-based settings
  - Environment variable support with `GCP_` prefix
  - `.env` file auto-discovery
  - Type-safe configuration
  - Sensible defaults

- **Type Safety**: Full type hints throughout
  - Strict mypy configuration
  - Pydantic models for all data structures
  - Type-safe return values

- **Error Handling**: Custom exception hierarchy
  - Service-specific exceptions
  - Operation-specific exceptions
  - Detailed error messages with context

- **Testing**: Comprehensive test suite
  - 110+ test cases across all controllers
  - Mocked GCP clients for fast testing
  - High code coverage

- **Examples**: Production-ready examples
  - 12 complete example scripts
  - Real-world use cases
  - Best practices demonstrated

#### Documentation
- Comprehensive README with usage examples
- Detailed CLAUDE.md for AI-assisted development
- Extensive docstrings (Google-style)
- Type hints for IDE support
- Complete deployment guide for Firebase Hosting

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- No known security issues

## Release Notes

### How to Upgrade

This is the initial release. To install:

```bash
pip install gcp-utils==0.1.0
```

### Breaking Changes
- N/A (initial release)

### Migration Guide
- N/A (initial release)

---

[Unreleased]: https://github.com/dillon-tucker/gcp-utils/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dillon-tucker/gcp-utils/releases/tag/v0.1.0
