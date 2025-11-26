"""
Example usage of FirebaseHostingController.

This example demonstrates Firebase Hosting operations including
site management, custom domain configuration, and deployments.
"""

from gcp_utils.config import GCPSettings
from gcp_utils.controllers import FirebaseHostingController
from gcp_utils.exceptions import (
    FirebaseHostingError,
    ResourceNotFoundError,
)


def main():
    # Initialize settings (reads from environment variables or .env file)
    settings = GCPSettings(
        project_id="my-gcp-project",
        firebase_hosting_default_site="my-site",
    )

    # Create controller
    hosting = FirebaseHostingController(settings)

    # Example 1: Create a new site
    print("=" * 60)
    print("Creating a new Firebase Hosting site...")
    print("=" * 60)
    try:
        site = hosting.create_site(site_id="my-awesome-site")
        print(f"✓ Created site: {site['name']}")
        print(f"  Default URL: {site['defaultUrl']}")
        print(f"  Site ID: {site.get('siteId', 'N/A')}")
    except FirebaseHostingError as e:
        print(f"✗ Failed to create site: {e.message}")

    # Example 2: List all sites
    print("\n" + "=" * 60)
    print("Listing all sites...")
    print("=" * 60)
    try:
        sites = hosting.list_sites()
        print(f"Found {len(sites)} site(s):")
        for site in sites:
            print(f"  - {site['name']}")
            print(f"    URL: {site.get('defaultUrl', 'N/A')}")
    except FirebaseHostingError as e:
        print(f"✗ Failed to list sites: {e.message}")

    # Example 3: Get site information
    print("\n" + "=" * 60)
    print("Getting site information...")
    print("=" * 60)
    try:
        site = hosting.get_site("my-awesome-site")
        print(f"✓ Site: {site['name']}")
        print(f"  Default URL: {site['defaultUrl']}")
        print(f"  Type: {site.get('type', 'DEFAULT_SITE_TYPE')}")
    except ResourceNotFoundError:
        print("✗ Site not found")
    except FirebaseHostingError as e:
        print(f"✗ Failed to get site: {e.message}")

    # Example 4: Add a custom domain
    print("\n" + "=" * 60)
    print("Adding a custom domain...")
    print("=" * 60)
    try:
        domain = hosting.add_custom_domain(
            site_id="my-awesome-site",
            domain_name="example.com",
        )
        print(f"✓ Added domain: {domain['domainName']}")
        print(f"  Status: {domain.get('status', 'PENDING')}")

        # Show DNS provisioning info if available
        if "provisioning" in domain:
            print("\n  DNS Configuration Required:")
            provisioning = domain["provisioning"]
            if "expectedDnsRecords" in provisioning:
                for record in provisioning["expectedDnsRecords"]:
                    print(f"    {record.get('type')} record:")
                    print(f"      Name: {record.get('domainName')}")
                    print(f"      Value: {record.get('requiredValue')}")
    except FirebaseHostingError as e:
        print(f"✗ Failed to add domain: {e.message}")

    # Example 5: List custom domains
    print("\n" + "=" * 60)
    print("Listing custom domains...")
    print("=" * 60)
    try:
        domains = hosting.list_domains(site_id="my-awesome-site")
        print(f"Found {len(domains)} custom domain(s):")
        for domain in domains:
            print(f"  - {domain['domainName']}: {domain.get('status', 'UNKNOWN')}")
    except FirebaseHostingError as e:
        print(f"✗ Failed to list domains: {e.message}")

    # Example 6: Get domain status
    print("\n" + "=" * 60)
    print("Getting domain status...")
    print("=" * 60)
    try:
        domain = hosting.get_domain(
            site_id="my-awesome-site",
            domain_name="example.com",
        )
        print(f"✓ Domain: {domain['domainName']}")
        print(f"  Status: {domain.get('status', 'UNKNOWN')}")

        # Show SSL certificate info if available
        if "cert" in domain:
            cert = domain["cert"]
            print(f"  SSL Status: {cert.get('status', 'UNKNOWN')}")
            if "state" in cert:
                print(f"  SSL State: {cert['state']}")
    except ResourceNotFoundError:
        print("✗ Domain not found")
    except FirebaseHostingError as e:
        print(f"✗ Failed to get domain: {e.message}")

    # Example 7: Create a version with configuration
    print("\n" + "=" * 60)
    print("Creating a new version with redirects...")
    print("=" * 60)
    try:
        config = {
            "redirects": [
                {
                    "source": "/old-page",
                    "destination": "/new-page",
                    "type": 301,  # Permanent redirect
                },
                {
                    "source": "/blog/*",
                    "destination": "https://blog.example.com/:splat",
                    "type": 302,  # Temporary redirect
                },
            ],
            "headers": [
                {
                    "source": "/images/**",
                    "headers": {
                        "Cache-Control": "max-age=31536000",
                        "Access-Control-Allow-Origin": "*",
                    },
                },
            ],
            "rewrites": [
                {
                    "source": "/api/**",
                    "function": "api",  # Cloud Function
                },
            ],
        }

        version = hosting.create_version(
            site_id="my-awesome-site",
            config=config,
        )
        print(f"✓ Created version: {version['name']}")
        print(f"  Status: {version.get('status', 'CREATED')}")

        # Save version name for later use
        version_name = version["name"]
    except FirebaseHostingError as e:
        print(f"✗ Failed to create version: {e.message}")
        version_name = None

    # Example 8: Create a release (deploy the version)
    if version_name:
        print("\n" + "=" * 60)
        print("Creating a release (deploying version)...")
        print("=" * 60)
        try:
            release = hosting.create_release(
                site_id="my-awesome-site",
                version_name=version_name,
                message="Production deployment from example script",
            )
            print(f"✓ Created release: {release['name']}")
            print(f"  Version: {release.get('version', {}).get('name', version_name)}")
            print(f"  Message: {release.get('message', 'No message')}")
            if "releaseTime" in release:
                print(f"  Released at: {release['releaseTime']}")
        except FirebaseHostingError as e:
            print(f"✗ Failed to create release: {e.message}")

    # Example 9: List releases
    print("\n" + "=" * 60)
    print("Listing recent releases...")
    print("=" * 60)
    try:
        releases = hosting.list_releases(site_id="my-awesome-site", page_size=5)
        print(f"Found {len(releases)} release(s) (showing up to 5):")
        for release in releases[:5]:
            print(f"  - {release['name']}")
            print(f"    Version: {release.get('version', {}).get('name', 'N/A')}")
            print(f"    Message: {release.get('message', 'No message')}")
            if "releaseTime" in release:
                print(f"    Time: {release['releaseTime']}")
    except FirebaseHostingError as e:
        print(f"✗ Failed to list releases: {e.message}")

    # Example 10: Delete a custom domain
    print("\n" + "=" * 60)
    print("Deleting a custom domain...")
    print("=" * 60)
    try:
        hosting.delete_domain(
            site_id="my-awesome-site",
            domain_name="old-domain.com",
        )
        print("✓ Deleted domain: old-domain.com")
    except ResourceNotFoundError:
        print("✗ Domain not found (may already be deleted)")
    except FirebaseHostingError as e:
        print(f"✗ Failed to delete domain: {e.message}")

    # Example 11: Complete deployment with file upload
    print("\n" + "=" * 60)
    print("Complete deployment with file upload...")
    print("=" * 60)
    print(
        """
    This example demonstrates the complete deployment workflow including
    file uploads. First, let's create some sample HTML files to deploy.
    """
    )

    # Create sample files for deployment
    import tempfile
    import os

    try:
        # Create temporary directory with sample website
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Creating sample website in {temp_dir}...")

            # Create index.html
            index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Awesome Site</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <h1>Welcome to My Awesome Site!</h1>
    <p>Deployed with Firebase Hosting Controller</p>
    <script src="/js/app.js"></script>
</body>
</html>"""

            # Create style.css
            style_css = """body {
    font-family: Arial, sans-serif;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: #f5f5f5;
}

h1 {
    color: #333;
    border-bottom: 2px solid #ff6b6b;
    padding-bottom: 10px;
}

p {
    color: #666;
    line-height: 1.6;
}"""

            # Create app.js
            app_js = """console.log('Site loaded successfully!');
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM ready!');
});"""

            # Write files
            os.makedirs(os.path.join(temp_dir, "css"), exist_ok=True)
            os.makedirs(os.path.join(temp_dir, "js"), exist_ok=True)

            with open(os.path.join(temp_dir, "index.html"), "w") as f:
                f.write(index_html)

            with open(os.path.join(temp_dir, "css", "style.css"), "w") as f:
                f.write(style_css)

            with open(os.path.join(temp_dir, "js", "app.js"), "w") as f:
                f.write(app_js)

            print("✓ Sample files created")

            # Prepare file mapping
            files = {
                "/index.html": os.path.join(temp_dir, "index.html"),
                "/css/style.css": os.path.join(temp_dir, "css", "style.css"),
                "/js/app.js": os.path.join(temp_dir, "js", "app.js"),
            }

            # Prepare hosting config
            config = {
                "redirects": [
                    {
                        "source": "/home",
                        "destination": "/",
                        "type": 301,
                    }
                ],
                "headers": [
                    {
                        "source": "**/*.@(jpg|jpeg|gif|png|css|js)",
                        "headers": {
                            "Cache-Control": "max-age=31536000",
                        },
                    }
                ],
                "cleanUrls": True,
            }

            # Deploy the site!
            print("\n" + "-" * 60)
            print("Deploying site with files...")
            print("-" * 60)

            result = hosting.deploy_site(
                site_id="my-awesome-site",
                files=files,
                config=config,
                message="Deployment from example script - v1.0.0",
            )

            print("\n" + "=" * 60)
            print("DEPLOYMENT SUCCESSFUL!")
            print("=" * 60)
            print(f"Site URL: {result['site_url']}")
            print(f"Version: {result['version']['name']}")
            print(f"Release: {result['release']['name']}")
            print(f"Files deployed: {result['upload_result']['totalFileCount']}")
            print(f"  - Uploaded: {result['upload_result']['uploadedFileCount']}")
            print(f"  - Cached: {result['upload_result']['cachedFileCount']}")

    except FirebaseHostingError as e:
        print(f"✗ Deployment failed: {e.message}")
        if e.details:
            print(f"  Details: {e.details}")
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")

    # Example 12: Manual deployment workflow (step-by-step)
    print("\n" + "=" * 60)
    print("Manual deployment workflow (alternative approach)...")
    print("=" * 60)
    print(
        """
    If you prefer more control, you can do each step manually:

    # Step 1: Create version
    version = hosting.create_version('my-site', config=config)

    # Step 2: Upload files
    files = {'/index.html': './public/index.html'}
    upload_result = hosting.populate_files(version['name'], files)

    # Step 3: Finalize version
    finalized = hosting.finalize_version(version['name'])

    # Step 4: Create release
    release = hosting.create_release(
        site_id='my-site',
        version_name=version['name'],
        message='Production v1.0.0'
    )
    """
    )

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
