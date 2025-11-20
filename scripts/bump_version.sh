#!/bin/bash
# Version bumping script for local development
# Usage: ./scripts/bump_version.sh [patch|minor|major]

set -e

# Check if bump2version is installed
if ! command -v bump2version &> /dev/null; then
    echo "❌ bump2version is not installed"
    echo "Install it with: pip install bump2version"
    exit 1
fi

# Get version part (default to patch)
VERSION_PART=${1:-patch}

# Validate input
if [[ ! "$VERSION_PART" =~ ^(patch|minor|major)$ ]]; then
    echo "❌ Invalid version part: $VERSION_PART"
    echo "Usage: $0 [patch|minor|major]"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(grep 'current_version' .bumpversion.cfg | cut -d' ' -f3)

echo "Current version: $CURRENT_VERSION"
echo "Bumping $VERSION_PART version..."

# Bump version
bump2version $VERSION_PART

# Get new version
NEW_VERSION=$(grep 'current_version' .bumpversion.cfg | cut -d' ' -f3)

echo "✅ Version bumped: $CURRENT_VERSION → $NEW_VERSION"
echo ""
echo "Next steps:"
echo "  1. Review the changes: git diff HEAD~1"
echo "  2. Push the changes: git push origin master --follow-tags"
echo "  3. Create a release on GitHub to trigger PyPI deployment"
echo ""
echo "Or use the automated workflow:"
echo "  gh workflow run bump-version.yml -f version_part=$VERSION_PART"
