# Publishing Guide

This guide explains how to publish `gcp-utils` to PyPI.

## Prerequisites

### 1. PyPI Account Setup

1. Create accounts on:
   - [PyPI](https://pypi.org/account/register/) (production)
   - [Test PyPI](https://test.pypi.org/account/register/) (testing)

2. Enable 2FA on both accounts (required)

3. Create API tokens:
   - PyPI: https://pypi.org/manage/account/token/
   - Test PyPI: https://test.pypi.org/manage/account/token/

### 2. GitHub Secrets Setup

Add the following secrets to your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

- `PYPI_API_TOKEN`: Your PyPI API token
- `TEST_PYPI_API_TOKEN`: Your Test PyPI API token
- `CODECOV_TOKEN`: Your Codecov token (optional, for coverage reports)

### 3. PyPI Trusted Publishing (Recommended)

Instead of using API tokens, you can set up trusted publishing (OIDC):

1. Go to PyPI project settings
2. Add a new "trusted publisher"
3. Configure:
   - **Owner**: `dillon-tucker`
   - **Repository**: `gcp-utils`
   - **Workflow**: `publish.yml`
   - **Environment**: `pypi`

This allows publishing without storing API tokens.

## Publishing Workflow

### Option 1: Automated Release (Recommended)

1. **Update version in `pyproject.toml`**:
   ```toml
   [project]
   version = "0.2.0"
   ```

2. **Update CHANGELOG.md**:
   - Move items from `[Unreleased]` to new version section
   - Add release date
   - Add comparison link at bottom

3. **Commit changes**:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Bump version to 0.2.0"
   git push origin main
   ```

4. **Create and push a tag**:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

5. **Create GitHub Release**:
   - Go to: https://github.com/dillon-tucker/gcp-utils/releases/new
   - Select the tag you just created
   - Title: `v0.2.0`
   - Description: Copy from CHANGELOG.md
   - Click "Publish release"

6. **Automated publishing**:
   - GitHub Actions will automatically build and publish to PyPI
   - Monitor: https://github.com/dillon-tucker/gcp-utils/actions

### Option 2: Manual Workflow Dispatch

For testing or specific scenarios:

1. Go to GitHub Actions: https://github.com/dillon-tucker/gcp-utils/actions/workflows/publish.yml

2. Click "Run workflow"

3. Choose:
   - **Branch**: `main`
   - **Test PyPI**: Check if testing, uncheck for production

4. Click "Run workflow"

### Option 3: Manual Local Publishing

For emergency situations or testing:

```bash
# Install build tools
pip install build twine hatchling

# Build the package
python -m build

# Check the distribution
twine check dist/*

# Upload to Test PyPI (testing)
twine upload --repository testpypi dist/*

# Upload to PyPI (production)
twine upload dist/*
```

## Pre-Release Checklist

Before creating a release, ensure:

- [ ] All tests pass: `pytest tests/`
- [ ] Type checking passes: `mypy src/`
- [ ] Linting passes: `ruff check src/`
- [ ] Code is formatted: `black src/ && isort src/`
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG.md updated with new version
- [ ] README.md is up to date
- [ ] All examples work
- [ ] Documentation is current
- [ ] GitHub Actions CI is green

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **Major version** (X.0.0): Breaking changes
- **Minor version** (0.X.0): New features, backward compatible
- **Patch version** (0.0.X): Bug fixes, backward compatible

### Examples

- `0.1.0` → `0.1.1`: Bug fix
- `0.1.1` → `0.2.0`: New feature (Cloud Functions controller)
- `0.2.0` → `1.0.0`: Breaking change (API redesign)

## Testing a Release

### Test PyPI

1. Publish to Test PyPI (see Option 2 above with Test PyPI checked)

2. Install from Test PyPI:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple gcp-utils
   ```

3. Test the installation:
   ```bash
   python -c "from gcp_utils.controllers import CloudStorageController; print('✓ Import successful')"
   ```

4. If everything works, proceed with production release

## Post-Release

After publishing to PyPI:

1. **Verify the release**:
   - Check PyPI: https://pypi.org/project/gcp-utils/
   - Verify badges update in README

2. **Announce the release**:
   - GitHub Discussions
   - Social media (if applicable)
   - Email list (if applicable)

3. **Monitor for issues**:
   - Watch GitHub Issues
   - Check download stats on PyPI

4. **Prepare for next version**:
   - Add `[Unreleased]` section to CHANGELOG.md
   - Start tracking new changes

## Troubleshooting

### Build Fails

```bash
# Clean build artifacts
rm -rf dist/ build/ *.egg-info

# Rebuild
python -m build
```

### Upload Fails - "File already exists"

PyPI doesn't allow re-uploading the same version. You must:

1. Bump the version number
2. Rebuild
3. Upload again

### Upload Fails - "Invalid credentials"

1. Verify API token is correct
2. Ensure token has upload permissions
3. Check token hasn't expired
4. Try regenerating the token

### CI Workflow Fails

1. Check GitHub Actions logs
2. Verify secrets are configured
3. Ensure workflow file syntax is correct
4. Test locally with `python -m build`

## Security Considerations

1. **Never commit API tokens** to the repository
2. **Use GitHub Secrets** for sensitive data
3. **Enable 2FA** on PyPI account
4. **Use trusted publishing** when possible
5. **Rotate tokens** periodically
6. **Sign releases** with Sigstore (automated in workflow)

## Reference Links

- **PyPI Project**: https://pypi.org/project/gcp-utils/
- **Test PyPI Project**: https://test.pypi.org/project/gcp-utils/
- **GitHub Releases**: https://github.com/dillon-tucker/gcp-utils/releases
- **GitHub Actions**: https://github.com/dillon-tucker/gcp-utils/actions
- **Packaging Guide**: https://packaging.python.org/
- **Semantic Versioning**: https://semver.org/
- **Keep a Changelog**: https://keepachangelog.com/
