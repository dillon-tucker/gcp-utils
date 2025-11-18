"""
Example usage of the Firebase Authentication controller.

This example demonstrates:
- Creating and managing users
- Updating user information
- Verifying ID tokens
- Setting custom claims
- Generating authentication links
- Listing and deleting users
"""

import sys
from pathlib import Path

# Add src to path for running without installation
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gcp_utils.controllers import FirebaseAuthController


def main() -> None:
    """Demonstrate Firebase Auth controller functionality."""

    # Initialize controller (automatically loads from .env)
    auth = FirebaseAuthController()

    print("=" * 80)
    print("Firebase Authentication Controller Example")
    print("=" * 80)

    # 1. Create a user
    print("\n1. Creating a user...")
    try:
        user = auth.create_user(
            email="example-user@example.com",
            password="SecurePassword123!",
            display_name="Example User",
            email_verified=False,
        )
        print(f"[OK] Created user: {user['email']}")
        print(f"  UID: {user['uid']}")
        print(f"  Display name: {user['display_name']}")
        print(f"  Email verified: {user['email_verified']}")
        user_uid = user["uid"]
    except Exception as e:
        print(f"[FAIL] Failed to create user: {e}")
        # User might already exist
        try:
            user = auth.get_user_by_email("example-user@example.com")
            user_uid = user["uid"]
            print(f"[INFO] User already exists with UID: {user_uid}")
        except Exception:
            print("[ERROR] Could not retrieve existing user")
            return

    # 2. Get user by UID
    print("\n2. Getting user by UID...")
    try:
        user = auth.get_user(user_uid)
        print(f"[OK] Retrieved user: {user['email']}")
        print(f"  Display name: {user['display_name']}")
        print(f"  Disabled: {user['disabled']}")
    except Exception as e:
        print(f"[FAIL] Failed to get user: {e}")

    # 3. Get user by email
    print("\n3. Getting user by email...")
    try:
        user = auth.get_user_by_email("example-user@example.com")
        print(f"[OK] Retrieved user by email: {user['email']}")
        print(f"  UID: {user['uid']}")
    except Exception as e:
        print(f"[FAIL] Failed to get user by email: {e}")

    # 4. Update user information
    print("\n4. Updating user information...")
    try:
        updated_user = auth.update_user(
            uid=user_uid,
            display_name="Updated Example User",
            email_verified=True,
        )
        print(f"[OK] Updated user: {updated_user['email']}")
        print(f"  New display name: {updated_user['display_name']}")
        print(f"  Email verified: {updated_user['email_verified']}")
    except Exception as e:
        print(f"[FAIL] Failed to update user: {e}")

    # 5. Set custom claims
    print("\n5. Setting custom user claims...")
    try:
        auth.set_custom_user_claims(
            uid=user_uid,
            custom_claims={
                "role": "admin",
                "tier": "premium",
                "access_level": 5,
            },
        )
        print(f"[OK] Set custom claims for user {user_uid}")

        # Verify claims were set
        user = auth.get_user(user_uid)
        print(f"  Custom claims: {user['custom_claims']}")
    except Exception as e:
        print(f"[FAIL] Failed to set custom claims: {e}")

    # 6. Create custom token
    print("\n6. Creating custom authentication token...")
    try:
        custom_token = auth.create_custom_token(
            uid=user_uid,
            developer_claims={"temp_access": True},
        )
        print(f"[OK] Created custom token (length: {len(custom_token)} chars)")
        print(f"  Token preview: {custom_token[:50]}...")
    except Exception as e:
        print(f"[FAIL] Failed to create custom token: {e}")

    # 7. Generate email verification link
    print("\n7. Generating email verification link...")
    try:
        verification_link = auth.generate_email_verification_link(
            email="example-user@example.com"
        )
        print(f"[OK] Generated email verification link")
        print(f"  Link: {verification_link[:80]}...")
    except Exception as e:
        print(f"[FAIL] Failed to generate verification link: {e}")

    # 8. Generate password reset link
    print("\n8. Generating password reset link...")
    try:
        reset_link = auth.generate_password_reset_link(
            email="example-user@example.com"
        )
        print(f"[OK] Generated password reset link")
        print(f"  Link: {reset_link[:80]}...")
    except Exception as e:
        print(f"[FAIL] Failed to generate reset link: {e}")

    # 9. List users
    print("\n9. Listing users...")
    try:
        result = auth.list_users(max_results=10)
        users = result["users"]
        print(f"[OK] Found {len(users)} users:")
        for user in users[:5]:  # Show first 5
            print(f"  - {user['email'] or 'No email'} (UID: {user['uid']})")
        if len(users) > 5:
            print(f"  ... and {len(users) - 5} more")

        if result["next_page_token"]:
            print(f"  Next page token available for pagination")
    except Exception as e:
        print(f"[FAIL] Failed to list users: {e}")

    # 10. Revoke refresh tokens
    print("\n10. Revoking refresh tokens...")
    try:
        auth.revoke_refresh_tokens(user_uid)
        print(f"[OK] Revoked all refresh tokens for user {user_uid}")
        print("  User will need to re-authenticate on next request")
    except Exception as e:
        print(f"[FAIL] Failed to revoke tokens: {e}")

    # 11. Create user with phone number
    print("\n11. Creating user with phone number...")
    try:
        phone_user = auth.create_user(
            phone_number="+15555551234",
            display_name="Phone User",
        )
        print(f"[OK] Created user with phone number")
        print(f"  UID: {phone_user['uid']}")
        print(f"  Phone: {phone_user['phone_number']}")
        phone_user_uid = phone_user["uid"]
    except Exception as e:
        print(f"[FAIL] Failed to create phone user: {e}")
        phone_user_uid = None

    # 12. Cleanup - Delete test users
    print("\n12. Cleaning up test users...")
    try:
        # Delete the first user
        auth.delete_user(user_uid)
        print(f"[OK] Deleted user {user_uid}")

        # Delete the phone user if created
        if phone_user_uid:
            auth.delete_user(phone_user_uid)
            print(f"[OK] Deleted phone user {phone_user_uid}")
    except Exception as e:
        print(f"[FAIL] Failed to delete users: {e}")

    # 13. Batch delete (if you have multiple users to delete)
    print("\n13. Batch delete users (example)...")
    print("  [INFO] Skipped - use auth.delete_users(['uid1', 'uid2', ...]) for batch deletion")

    print("\n" + "=" * 80)
    print("Example completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
