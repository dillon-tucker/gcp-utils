"""
Example usage of the IAM (Identity and Access Management) controller.

This example demonstrates:
- Creating service accounts
- Managing service account keys
- Listing and querying service accounts
- Managing IAM policies
"""

import sys
from pathlib import Path

# Add src to path for running without installation
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gcp_utils.controllers import IAMController
from gcp_utils.models.iam import IAMBinding, ServiceAccountKeyAlgorithm


def main() -> None:
    """Demonstrate IAM controller functionality."""

    # Initialize controller (automatically loads from .env)
    iam = IAMController()

    print("=" * 80)
    print("IAM Controller Example")
    print("=" * 80)

    # 1. Create a service account
    print("\n1. Creating service account...")
    try:
        service_account = iam.create_service_account(
            account_id="example-service-account",
            display_name="Example Service Account",
            description="Service account created by example script",
        )
        print(f"[OK] Created service account: {service_account.email}")
        print(f"  Display name: {service_account.display_name}")
        print(f"  Unique ID: {service_account.unique_id}")
    except Exception as e:
        print(f"[FAIL] Failed to create service account: {e}")
        # Service account might already exist, continue anyway
        service_account_email = (
            f"example-service-account@{iam.settings.project_id}.iam.gserviceaccount.com"
        )
    else:
        service_account_email = service_account.email

    # 2. Get service account details
    print("\n2. Getting service account details...")
    try:
        account = iam.get_service_account(service_account_email)
        print(f"[OK] Retrieved account: {account.email}")
        print(f"  Display name: {account.display_name}")
        print(f"  Description: {account.description}")
        print(f"  Disabled: {account.disabled}")
    except Exception as e:
        print(f"[FAIL] Failed to get service account: {e}")

    # 3. List all service accounts
    print("\n3. Listing service accounts...")
    try:
        accounts = iam.list_service_accounts(max_results=10)
        print(f"[OK] Found {len(accounts)} service accounts:")
        for account in accounts[:5]:  # Show first 5
            print(f"  - {account.email} ({account.display_name})")
        if len(accounts) > 5:
            print(f"  ... and {len(accounts) - 5} more")
    except Exception as e:
        print(f"[FAIL] Failed to list service accounts: {e}")

    # 4. Create a service account key
    print("\n4. Creating service account key...")
    try:
        key = iam.create_service_account_key(
            email=service_account_email,
            key_algorithm=ServiceAccountKeyAlgorithm.KEY_ALG_RSA_2048,
        )
        print(f"[OK] Created key: {key.name}")
        print(f"  Algorithm: {key.key_algorithm}")

        # In a real application, you would save the private key data
        if key.private_key_data:
            print("  [WARN] Private key data available (not shown for security)")
            # To save the key:
            # import base64
            # key_json = base64.b64decode(key.private_key_data)
            # with open("service-account-key.json", "wb") as f:
            #     f.write(key_json)

        key_name = key.name
    except Exception as e:
        print(f"[FAIL] Failed to create key: {e}")
        key_name = None

    # 5. List service account keys
    print("\n5. Listing service account keys...")
    try:
        keys = iam.list_service_account_keys(service_account_email)
        print(f"[OK] Found {len(keys)} keys for {service_account_email}:")
        for key in keys:
            print(f"  - {key.name}")
            print(f"    Algorithm: {key.key_algorithm}")
            print(f"    Type: {key.key_type}")
            if key.valid_after_time:
                print(f"    Valid after: {key.valid_after_time}")
            if key.valid_before_time:
                print(f"    Valid before: {key.valid_before_time}")
    except Exception as e:
        print(f"[FAIL] Failed to list keys: {e}")

    # 6. Get detailed service account info
    print("\n6. Getting detailed service account info...")
    try:
        info = iam.get_service_account_info(service_account_email)
        print(f"[OK] Service account info for {info.account.email}:")
        print(f"  Total keys: {info.keys_count}")
        print(f"  User-managed keys: {info.user_managed_keys_count}")
        print(f"  System-managed keys: {info.system_managed_keys_count}")
    except Exception as e:
        print(f"[FAIL] Failed to get service account info: {e}")

    # 7. Update service account
    print("\n7. Updating service account...")
    try:
        updated_account = iam.update_service_account(
            email=service_account_email,
            display_name="Updated Example Service Account",
            description="Updated description",
        )
        print(f"[OK] Updated service account: {updated_account.email}")
        print(f"  New display name: {updated_account.display_name}")
        print(f"  New description: {updated_account.description}")
    except Exception as e:
        print(f"[FAIL] Failed to update service account: {e}")

    # 8. Get IAM policy for the service account
    print("\n8. Getting service account IAM policy...")
    try:
        resource = f"projects/{iam.settings.project_id}/serviceAccounts/{service_account_email}"
        policy = iam.get_iam_policy(resource)
        print(f"[OK] Retrieved IAM policy for service account")
        print(f"  Policy version: {policy.version}")
        print(f"  Number of bindings: {len(policy.bindings)}")

        # Show first few bindings
        if policy.bindings:
            print("  Bindings:")
            for binding in policy.bindings[:3]:
                print(f"    - Role: {binding.role}")
                print(f"      Members: {len(binding.members)} member(s)")
        else:
            print("  No IAM bindings on this service account")

    except Exception as e:
        print(f"[FAIL] Failed to get IAM policy: {e}")

    # 9. Add IAM policy binding (example - not executed by default)
    print("\n9. Example: Adding IAM policy binding (commented out)")
    print("  To grant someone permission to use this service account, uncomment:")
    print(f"""
    # Get current policy for the service account
    resource = f"projects/{{iam.settings.project_id}}/serviceAccounts/{service_account_email}"
    policy = iam.get_iam_policy(resource)

    # Add new binding to allow a user to impersonate this service account
    new_binding = IAMBinding(
        role="roles/iam.serviceAccountUser",
        members=["user:admin@example.com"]
    )
    policy.bindings.append(new_binding)

    # Set updated policy
    updated_policy = iam.set_iam_policy(resource, policy)
    print(f"[OK] Updated IAM policy")
    """)

    # Cleanup
    print("\n" + "=" * 80)
    print("Cleanup")
    print("=" * 80)

    # 10. Delete service account key
    if key_name:
        print("\n10. Deleting service account key...")
        try:
            iam.delete_service_account_key(key_name)
            print(f"[OK] Deleted key: {key_name}")
        except Exception as e:
            print(f"[FAIL] Failed to delete key: {e}")

    # 11. Delete service account
    print("\n11. Deleting service account...")
    print("  [WARN] To delete the service account, uncomment the following:")
    print(f"""
    # iam.delete_service_account("{service_account_email}")
    # print(f"[OK] Deleted service account: {service_account_email}")
    """)
    print(
        "  Note: Service account left intact for demonstration. Delete manually if needed."
    )

    print("\n" + "=" * 80)
    print("IAM Controller Example Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
