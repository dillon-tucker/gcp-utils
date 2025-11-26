"""
Example usage of the Secret Manager controller.

This example demonstrates:
- Creating secrets with metadata and labels
- Adding and managing secret versions
- Accessing secret values
- Listing secrets and versions
- Enabling, disabling, and destroying versions
- Secret lifecycle management
"""

import sys
from pathlib import Path

# Add src to path for running without installation
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gcp_utils.controllers import SecretManagerController


def main() -> None:
    """Demonstrate Secret Manager controller functionality."""

    # Initialize controller (automatically loads from .env)
    secrets = SecretManagerController()

    print("=" * 80)
    print("Secret Manager Controller Example")
    print("=" * 80)

    # 1. Create a secret with initial value
    print("\n1. Creating secret with initial value...")
    secret_id = "example-api-key"
    try:
        version = secrets.create_secret_with_value(
            secret_id=secret_id,
            payload="sk_test_1234567890abcdef",
            labels={
                "environment": "development",
                "service": "api",
                "managed_by": "gcp-utils",
            },
            replication_locations=[
                "us-central1",
                "us-east1",
            ],  # Multi-region replication
        )
        print(f"[OK] Created secret: {secret_id}")
        print(f"  Version: {version.name.split('/')[-1]}")
        print(f"  State: {version.state}")
    except Exception as e:
        print(f"[FAIL] Failed to create secret: {e}")
        print("  Secret might already exist - continuing...")

    # 2. Get secret metadata
    print("\n2. Getting secret metadata...")
    try:
        secret = secrets.get_secret(secret_id)
        print(f"[OK] Retrieved secret: {secret.name}")
        print(f"  Labels: {secret.labels}")
        print(f"  Replication: {secret.replication}")
        print(f"  Created: {secret.create_time}")
    except Exception as e:
        print(f"[FAIL] Failed to get secret: {e}")

    # 3. Access secret value (latest version)
    print("\n3. Accessing secret value (latest version)...")
    try:
        value = secrets.access_secret_version(secret_id)
        print(f"[OK] Retrieved secret value (masked): {'*' * 10}{value[-6:]}")
        print("  Full value available in application")
    except Exception as e:
        print(f"[FAIL] Failed to access secret: {e}")

    # 4. Add a new version of the secret
    print("\n4. Adding new version of secret...")
    try:
        new_version = secrets.add_secret_version(
            secret_id=secret_id,
            payload="sk_prod_newkey567890xyz",
        )
        print(f"[OK] Added new version: {new_version.name.split('/')[-1]}")
        print(f"  State: {new_version.state}")
        latest_version = new_version.name.split("/")[-1]
    except Exception as e:
        print(f"[FAIL] Failed to add version: {e}")
        latest_version = "1"

    # 5. List all secret versions
    print("\n5. Listing all secret versions...")
    try:
        versions = secrets.list_secret_versions(secret_id)
        print(f"[OK] Found {len(versions)} version(s):")
        for version in versions:
            version_num = version.name.split("/")[-1]
            print(f"  - Version {version_num}: {version.state}")
    except Exception as e:
        print(f"[FAIL] Failed to list versions: {e}")

    # 6. Access specific version
    print("\n6. Accessing specific version...")
    try:
        value = secrets.access_secret_version(secret_id, version="1")
        print(f"[OK] Retrieved version 1 value (masked): {'*' * 10}{value[-6:]}")
    except Exception as e:
        print(f"[FAIL] Failed to access version 1: {e}")

    # 7. Create secret for database password
    print("\n7. Creating database password secret...")
    db_secret_id = "example-db-password"
    try:
        version = secrets.create_secret_with_value(
            secret_id=db_secret_id,
            payload="SuperSecurePassword123!",
            labels={
                "environment": "production",
                "service": "database",
            },
        )
        print(f"[OK] Created database password secret: {db_secret_id}")
        print(f"  Version: {version.name.split('/')[-1]}")
    except Exception as e:
        print(f"[FAIL] Failed to create database secret: {e}")
        print("  Secret might already exist - continuing...")

    # 8. Create secret with binary data (e.g., certificate)
    print("\n8. Creating secret with binary data...")
    cert_secret_id = "example-tls-cert"
    try:
        # Simulate a certificate or binary file
        binary_data = b"-----BEGIN CERTIFICATE-----\nMIIC...fake...cert...data\n-----END CERTIFICATE-----"

        version = secrets.create_secret_with_value(
            secret_id=cert_secret_id,
            payload=binary_data.decode("utf-8"),  # Convert bytes to string
            labels={
                "type": "certificate",
                "environment": "production",
            },
        )
        print(f"[OK] Created TLS certificate secret: {cert_secret_id}")
        print(f"  Version: {version.name.split('/')[-1]}")
    except Exception as e:
        print(f"[FAIL] Failed to create certificate secret: {e}")
        print("  Secret might already exist - continuing...")

    # 9. List all secrets
    print("\n9. Listing all secrets...")
    try:
        all_secrets = secrets.list_secrets()
        print(f"[OK] Found {len(all_secrets)} secret(s):")
        for secret in all_secrets[:5]:  # Show first 5
            secret_name = secret.name.split("/")[-1]
            labels = secret.labels or {}
            env = labels.get("environment", "N/A")
            print(f"  - {secret_name} (env: {env})")
        if len(all_secrets) > 5:
            print(f"  ... and {len(all_secrets) - 5} more")
    except Exception as e:
        print(f"[FAIL] Failed to list secrets: {e}")

    # 10. Disable a secret version
    print("\n10. Disabling secret version...")
    try:
        version = secrets.disable_secret_version(secret_id, latest_version)
        print(f"[OK] Disabled version {latest_version}")
        print(f"  State: {version.state}")
        print("  This version can no longer be accessed")
    except Exception as e:
        print(f"[FAIL] Failed to disable version: {e}")

    # 11. Enable the secret version again
    print("\n11. Re-enabling secret version...")
    try:
        version = secrets.enable_secret_version(secret_id, latest_version)
        print(f"[OK] Enabled version {latest_version}")
        print(f"  State: {version.state}")
        print("  This version can now be accessed again")
    except Exception as e:
        print(f"[FAIL] Failed to enable version: {e}")

    # 12. Rotate secret (add new version and disable old)
    print("\n12. Rotating secret (best practice)...")
    try:
        # Add new version
        new_version = secrets.add_secret_version(
            secret_id=secret_id,
            payload="sk_prod_rotated_key_2024",
        )
        new_version_num = new_version.name.split("/")[-1]
        print(f"[OK] Added new rotated version: {new_version_num}")

        # Disable old version after grace period
        # In production, you'd wait for services to update before disabling
        print("  In production: wait for services to update, then disable old versions")
        print(
            f"  Example: secrets.disable_secret_version('{secret_id}', '{latest_version}')"
        )
    except Exception as e:
        print(f"[FAIL] Failed to rotate secret: {e}")

    # 13. Cleanup - Destroy a version (IRREVERSIBLE)
    print("\n13. Destroying secret version (IRREVERSIBLE)...")
    print("  [SKIP] Skipping destruction - this permanently deletes the data")
    print(
        f"  To destroy: secrets.destroy_secret_version('{secret_id}', '{latest_version}')"
    )

    # 14. Cleanup - Delete secrets
    print("\n14. Cleaning up secrets...")
    try:
        secrets.delete_secret(secret_id)
        print(f"[OK] Deleted secret: {secret_id}")
    except Exception as e:
        print(f"[FAIL] Failed to delete secret: {e}")

    try:
        secrets.delete_secret(db_secret_id)
        print(f"[OK] Deleted secret: {db_secret_id}")
    except Exception as e:
        print(f"[FAIL] Failed to delete database secret: {e}")

    try:
        secrets.delete_secret(cert_secret_id)
        print(f"[OK] Deleted secret: {cert_secret_id}")
    except Exception as e:
        print(f"[FAIL] Failed to delete certificate secret: {e}")

    # Example use cases and best practices
    print("\n" + "=" * 80)
    print("Common Use Cases & Best Practices:")
    print("=" * 80)
    print(
        """
1. API Keys and Tokens:
   - Store third-party API keys
   - Manage OAuth tokens and refresh tokens
   - Rotate keys regularly

2. Database Credentials:
   - Store connection strings
   - Manage database passwords
   - Use versioning for password rotation

3. Encryption Keys:
   - Store symmetric encryption keys
   - Manage certificate private keys
   - Keep binary data secure

4. Configuration Secrets:
   - Store environment-specific configs
   - Manage feature flags with sensitive data
   - Centralize secret management

5. Secret Rotation Best Practices:
   - Add new version first
   - Update all services to use new version
   - Verify new version works
   - Disable (not destroy) old version
   - Keep old version for rollback
   - Destroy after retention period

6. Access Control:
   - Use IAM to control who can access secrets
   - Grant minimum necessary permissions
   - Audit secret access regularly
   - Use service accounts for applications

7. Replication:
   - Use multi-region for high availability
   - Choose regions close to your services
   - Balance cost vs availability needs

8. Version Management:
   - Latest version accessed by default
   - Pin to specific versions for stability
   - Keep version history for audit trail
   - Disable versions instead of destroying
"""
    )

    print("=" * 80)
    print("Example completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
