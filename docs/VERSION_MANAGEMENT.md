# Version Management

This document explains how to manage versions and releases for the `gcp-utils` package.

## Overview

The project uses [bump2version](https://github.com/c4urself/bump2version/) for automated version management. Versions follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (x.0.0) - Breaking changes
- **MINOR** version (0.x.0) - New features, backward compatible
- **PATCH** version (0.0.x) - Bug fixes, backward compatible

## Automated Version Bumping (Recommended)

### Via GitHub Actions (Easiest)

1. Go to: **Actions** → **Bump Version** → **Run workflow**
2. Select version part to bump (patch/minor/major)
3. Click **Run workflow**

This will:
- ✅ Bump the version in `pyproject.toml` and `src/gcp_utils/__init__.py`
- ✅ Create a git commit with message: "Bump version: X.Y.Z → X.Y.Z+1"
- ✅ Create a git tag: `vX.Y.Z+1`
- ✅ Push changes and tag to GitHub
- ✅ Create a GitHub Release (which triggers PyPI deployment)

**No manual steps needed!** The package will be published to PyPI automatically.

### Via GitHub CLI

```bash
# Bump patch version (0.1.0 → 0.1.1)
gh workflow run bump-version.yml -f version_part=patch

# Bump minor version (0.1.0 → 0.2.0)
gh workflow run bump-version.yml -f version_part=minor

# Bump major version (0.1.0 → 1.0.0)
gh workflow run bump-version.yml -f version_part=major
```

## Manual Version Bumping (Local Development)

### Prerequisites

Install bump2version:
```bash
pip install bump2version
```

### Using the Helper Script

```bash
# Bump patch version (0.1.0 → 0.1.1)
./scripts/bump_version.sh patch

# Bump minor version (0.1.0 → 0.2.0)
./scripts/bump_version.sh minor

# Bump major version (0.1.0 → 1.0.0)
./scripts/bump_version.sh major
```

This creates a commit and tag locally. Then push:
```bash
git push origin master --follow-tags
```

### Direct bump2version Usage

```bash
# Bump version
bump2version patch  # or minor, or major

# Push changes
git push origin master --follow-tags
```

## Creating a Release Manually

If you've bumped the version but want to create the release manually:

```bash
# Via GitHub CLI
gh release create v0.1.1 --title "v0.1.1" --generate-notes

# Or via GitHub UI
# 1. Go to Releases
# 2. Click "Draft a new release"
# 3. Choose tag: v0.1.1
# 4. Generate release notes
# 5. Publish release
```

Publishing a release triggers the PyPI deployment workflow.

## Version Bump Decision Guide

### When to bump PATCH (0.0.x)
- Bug fixes
- Documentation updates
- Performance improvements
- Internal refactoring (no API changes)
- Dependency updates (non-breaking)

**Examples:**
- "Fix bug in CloudStorageController.upload_file()"
- "Update docstrings for FirebaseAuthController"
- "Optimize batch operations in Firestore"

### When to bump MINOR (0.x.0)
- New features (backward compatible)
- New controllers for GCP services
- New methods in existing controllers
- New optional parameters
- Deprecation warnings (before removal)

**Examples:**
- "Add Cloud Functions controller"
- "Add batch_upload() method to CloudStorageController"
- "Add support for custom domains in Firebase Hosting"

### When to bump MAJOR (x.0.0)
- Breaking changes to public API
- Removal of deprecated features
- Changes to method signatures
- Changes to return types
- Python version requirement changes

**Examples:**
- "Remove deprecated CloudStorageController.legacy_upload()"
- "Change return type of get_document() from dict to Document model"
- "Require Python 3.13+"

## Current Version

Current version is tracked in:
- `pyproject.toml` - Line 3: `version = "0.1.0"`
- `src/gcp_utils/__init__.py` - Line 25: `__version__ = "0.1.0"`
- `.bumpversion.cfg` - Line 2: `current_version = 0.1.0`

**Note:** Always use bump2version to update versions. Manual editing can cause inconsistencies.

## Release Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ Developer Action                                            │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│ Run "Bump Version" workflow (patch/minor/major)            │
│   - Updates version in pyproject.toml & __init__.py        │
│   - Creates commit: "Bump version: X.Y.Z → X.Y.Z+1"        │
│   - Creates tag: vX.Y.Z+1                                   │
│   - Pushes to master with tag                               │
│   - Creates GitHub Release                                  │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│ "Publish to PyPI" workflow triggers (automatic)            │
│   - Builds package distribution (wheel + sdist)            │
│   - Publishes to PyPI                                       │
│   - Signs artifacts with Sigstore                           │
│   - Uploads signed artifacts to GitHub Release             │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│ Package available on PyPI                                   │
│   pip install gcp-utils==X.Y.Z+1                            │
└─────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### "bump2version: command not found"
```bash
pip install bump2version
```

### "tag 'vX.Y.Z' already exists"
The version was already bumped. Check current version:
```bash
grep 'current_version' .bumpversion.cfg
```

### PyPI deployment failed
Check:
1. `PYPI_API_TOKEN` secret is configured in GitHub
2. GitHub environment `pypi` exists
3. Workflow logs for detailed error

### Version mismatch between files
Reset and use bump2version:
```bash
# Manually fix .bumpversion.cfg current_version
# Then run:
bump2version --new-version X.Y.Z patch --allow-dirty
```

## See Also

- [PyPI Publishing Workflow](../.github/workflows/publish.yml)
- [Bump Version Workflow](../.github/workflows/bump-version.yml)
- [Semantic Versioning Specification](https://semver.org/)
- [bump2version Documentation](https://github.com/c4urself/bump2version/)
