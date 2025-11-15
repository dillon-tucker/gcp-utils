# Firebase Hosting - Deployment Feature Guide

## Overview

The Firebase Hosting controller now supports complete website deployments including file uploads, version management, and release creation - all from Python code!

## New Methods Added

### 1. `populate_files(version_name, files)`
Upload files to a hosting version using Firebase's hash-based upload system.

**Features**:
- Automatically hashes all files using SHA256
- Only uploads files that aren't already cached by Firebase
- Handles binary files efficiently
- Validates all file paths before upload

**Example**:
```python
files = {
    "/index.html": "./public/index.html",
    "/css/style.css": "./public/css/style.css",
    "/js/app.js": "./public/js/app.js",
}

result = hosting.populate_files(version_name, files)
print(f"Uploaded {result['uploadedFileCount']} new files")
print(f"Cached {result['cachedFileCount']} files")
```

### 2. `finalize_version(version_name)`
Finalize a version to make it ready for deployment.

**Features**:
- Marks version as immutable
- Required before creating a release
- Processes uploaded files

**Example**:
```python
finalized = hosting.finalize_version(version_name)
print(f"Status: {finalized['status']}")  # Should be "FINALIZED"
```

### 3. `deploy_site(site_id, files, config, message)` 🎯
**One-step deployment** - the easiest way to deploy!

**Features**:
- Creates version with configuration
- Uploads all files
- Finalizes the version
- Creates a release
- Returns complete deployment info

**Example**:
```python
result = hosting.deploy_site(
    site_id="my-site",
    files={
        "/index.html": "./public/index.html",
        "/css/style.css": "./public/css/style.css",
    },
    config={
        "redirects": [{
            "source": "/old",
            "destination": "/new",
            "type": 301
        }]
    },
    message="Production v1.0.0"
)

print(f"Deployed to: {result['site_url']}")
```

## Complete Deployment Workflow

### Option 1: One-Step Deployment (Recommended)

```python
from gcp_utils.config import GCPSettings
from gcp_utils.controllers import FirebaseHostingController

# Initialize
settings = GCPSettings(project_id="my-project")
hosting = FirebaseHostingController(settings)

# Define files to deploy
files = {
    "/index.html": "./public/index.html",
    "/404.html": "./public/404.html",
    "/css/style.css": "./public/css/style.css",
    "/js/app.js": "./public/js/app.js",
    "/images/logo.png": "./public/images/logo.png",
}

# Define hosting configuration
config = {
    "redirects": [
        {"source": "/old-page", "destination": "/new-page", "type": 301}
    ],
    "headers": [
        {
            "source": "**/*.@(jpg|jpeg|gif|png|css|js)",
            "headers": {"Cache-Control": "max-age=31536000"}
        }
    ],
    "cleanUrls": True,
    "trailingSlashBehavior": "REMOVE"
}

# Deploy everything in one call!
result = hosting.deploy_site(
    site_id="my-site",
    files=files,
    config=config,
    message="Production deployment v1.2.3"
)

# Check results
print(f"✓ Deployed to: {result['site_url']}")
print(f"✓ Version: {result['version']['name']}")
print(f"✓ Files: {result['upload_result']['totalFileCount']}")
```

### Option 2: Step-by-Step Deployment (Advanced)

For more control over each step:

```python
# Step 1: Create version
version = hosting.create_version("my-site", config=config)
version_name = version["name"]
print(f"Created version: {version_name}")

# Step 2: Upload files
upload_result = hosting.populate_files(version_name, files)
print(f"Uploaded {upload_result['uploadedFileCount']} files")

# Step 3: Finalize version
finalized = hosting.finalize_version(version_name)
print(f"Version status: {finalized['status']}")

# Step 4: Create release
release = hosting.create_release(
    site_id="my-site",
    version_name=version_name,
    message="Manual deployment"
)
print(f"Release created: {release['name']}")
```

## File Upload System

### How It Works

Firebase Hosting uses a content-addressable storage system:

1. **Hash Calculation**: Each file is hashed using SHA256
2. **Deduplication**: Firebase checks which files it already has
3. **Efficient Upload**: Only new/changed files are uploaded
4. **Binary Safe**: Handles all file types correctly

### File Mapping

The `files` dictionary maps destination paths to source paths:

```python
files = {
    # Key = Path in the deployed site
    # Value = Local file path
    "/index.html": "./src/index.html",
    "/about/index.html": "./src/about.html",
    "/assets/app.js": "./dist/app.bundle.js",
}
```

### Supported File Types

All file types are supported:
- HTML, CSS, JavaScript
- Images (PNG, JPG, SVG, etc.)
- Fonts (WOFF, TTF, etc.)
- JSON, XML, TXT
- Binary files
- Compressed files

## Hosting Configuration

### Redirects

```python
config = {
    "redirects": [
        {
            "source": "/blog/*",
            "destination": "https://blog.example.com/:splat",
            "type": 301  # Permanent redirect
        },
        {
            "source": "/temp",
            "destination": "/permanent",
            "type": 302  # Temporary redirect
        }
    ]
}
```

### Rewrites (Cloud Functions / Cloud Run)

```python
config = {
    "rewrites": [
        # Cloud Function
        {
            "source": "/api/**",
            "function": "myApiFunction"
        },
        # Cloud Run
        {
            "source": "/api/**",
            "run": {
                "serviceId": "my-api-service",
                "region": "us-central1"
            }
        },
        # SPA fallback
        {
            "source": "**",
            "destination": "/index.html"
        }
    ]
}
```

### Headers

```python
config = {
    "headers": [
        {
            "source": "**/*.@(jpg|jpeg|gif|png|webp)",
            "headers": {
                "Cache-Control": "max-age=31536000",
                "Access-Control-Allow-Origin": "*"
            }
        },
        {
            "source": "/api/**",
            "headers": {
                "Access-Control-Allow-Origin": "https://app.example.com",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE"
            }
        }
    ]
}
```

### Clean URLs

```python
config = {
    "cleanUrls": True,  # /about.html -> /about
    "trailingSlashBehavior": "REMOVE"  # or "ADD"
}
```

## Deployment Results

The `deploy_site()` method returns comprehensive results:

```python
{
    "version": {
        "name": "projects/.../sites/.../versions/...",
        "status": "FINALIZED",
        "createTime": "...",
        "finalizeTime": "...",
        "fileCount": 10,
        "versionBytes": 524288
    },
    "upload_result": {
        "totalFileCount": 10,
        "uploadedFileCount": 3,  # New files
        "cachedFileCount": 7,    # Already on Firebase
        "uploadUrl": "https://..."
    },
    "release": {
        "name": "projects/.../sites/.../releases/...",
        "version": {...},
        "message": "Production v1.0.0",
        "releaseTime": "..."
    },
    "site_url": "https://my-site.web.app",
    "success": True
}
```

## Error Handling

```python
from gcp_utils.exceptions import (
    FirebaseHostingError,
    ValidationError,
    ResourceNotFoundError
)

try:
    result = hosting.deploy_site(
        site_id="my-site",
        files=files,
        message="Deployment"
    )
    print(f"✓ Deployed successfully!")

except ValidationError as e:
    print(f"Invalid input: {e.message}")
    # E.g., file doesn't exist, empty files dict

except ResourceNotFoundError as e:
    print(f"Resource not found: {e.message}")
    # E.g., site doesn't exist

except FirebaseHostingError as e:
    print(f"Deployment failed: {e.message}")
    print(f"Details: {e.details}")
```

## Best Practices

### 1. Organize Your Files

```python
from pathlib import Path

# Use Path for cross-platform compatibility
public_dir = Path("./public")

files = {
    f"/{file.relative_to(public_dir)}": str(file)
    for file in public_dir.rglob("*")
    if file.is_file()
}
```

### 2. Use Configuration Templates

```python
# config_templates.py
PRODUCTION_CONFIG = {
    "headers": [
        {
            "source": "**",
            "headers": {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block"
            }
        }
    ],
    "cleanUrls": True
}

# Use it
hosting.deploy_site("my-site", files, config=PRODUCTION_CONFIG)
```

### 3. Version Your Deployments

```python
import datetime

timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
git_commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()

message = f"Deploy {timestamp} - commit {git_commit}"

hosting.deploy_site(
    site_id="my-site",
    files=files,
    message=message
)
```

### 4. Monitor Progress

The `deploy_site()` method prints progress updates:

```
Creating version for site 'my-site'...
✓ Created version: projects/.../versions/abc123
Uploading 15 file(s)...
✓ Uploaded 3 new file(s), 12 cached
Finalizing version...
✓ Version finalized: FINALIZED
Creating release...
✓ Release created: projects/.../releases/def456
```

## Integration Examples

### Deploy from CI/CD

```python
# deploy.py
import sys
from pathlib import Path
from gcp_utils.config import GCPSettings
from gcp_utils.controllers import FirebaseHostingController


def deploy(site_id: str, build_dir: str, message: str):
    settings = GCPSettings(project_id="my-project")
    hosting = FirebaseHostingController(settings)

    # Collect all files from build directory
    build_path = Path(build_dir)
    files = {
        f"/{file.relative_to(build_path)}": str(file)
        for file in build_path.rglob("*")
        if file.is_file()
    }

    # Deploy
    result = hosting.deploy_site(
        site_id=site_id,
        files=files,
        message=message
    )

    print(f"Deployed to: {result['site_url']}")
    return result


if __name__ == "__main__":
    deploy(
        site_id=sys.argv[1],
        build_dir=sys.argv[2],
        message=sys.argv[3] if len(sys.argv) > 3 else "Automated deployment"
    )
```

### Deploy with Rollback

```python
def deploy_with_rollback(site_id: str, files: dict, config: dict):
    hosting = FirebaseHostingController(settings)

    # Get current release for rollback
    releases = hosting.list_releases(site_id, page_size=1)
    current_release = releases[0] if releases else None

    try:
        # Deploy new version
        result = hosting.deploy_site(site_id, files, config)
        print(f"✓ Deployed: {result['site_url']}")
        return result

    except Exception as e:
        print(f"✗ Deployment failed: {e}")

        # Rollback to previous version
        if current_release:
            print("Rolling back to previous version...")
            hosting.create_release(
                site_id=site_id,
                version_name=current_release["version"]["name"],
                message="Rollback due to deployment failure"
            )
            print("✓ Rolled back successfully")

        raise
```

## Comparison with Firebase CLI

| Feature | Python Controller | Firebase CLI |
|---------|------------------|--------------|
| File Upload | ✅ Yes | ✅ Yes |
| Hosting Config | ✅ Yes | ✅ Yes |
| Custom Domains | ✅ Yes | ❌ No (manual) |
| Programmatic | ✅ Yes | ❌ No |
| CI/CD Integration | ✅ Easy | ⚠️ Requires Node.js |
| Version Control | ✅ Full API access | ⚠️ Limited |
| Batch Operations | ✅ Yes | ❌ No |

## Limitations

1. **File Size**: Individual files are limited by Firebase Hosting (typically 2GB per file)
2. **Total Size**: Total deployment size limited by Firebase quota
3. **File Count**: Thousands of files are supported, but consider bundling for performance
4. **Binary Files**: All file types supported, handled as binary data

## Troubleshooting

### Files Not Uploading

```python
# Check file paths
for dest, source in files.items():
    if not Path(source).exists():
        print(f"Missing: {source}")
```

### Version Finalization Fails

```python
# Ensure all files were uploaded first
upload_result = hosting.populate_files(version_name, files)
if upload_result['uploadedFileCount'] + upload_result['cachedFileCount'] != upload_result['totalFileCount']:
    print("Not all files uploaded successfully!")
```

### Authentication Errors

```python
# Ensure credentials have correct permissions
# Required: Firebase Hosting Admin
settings = GCPSettings(
    project_id="my-project",
    credentials_path="/path/to/service-account.json"
)
```

## Next Steps

- See `examples/example_firebase_hosting.py` for complete working examples
- Read Firebase Hosting documentation for advanced configuration options
- Check `FIREBASE_HOSTING_FEATURE.md` for API reference
