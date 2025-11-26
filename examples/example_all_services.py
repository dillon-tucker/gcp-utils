"""
Comprehensive example using multiple GCP services together.

This example demonstrates how to use multiple controllers together
for a realistic workflow.
"""

from datetime import timedelta

from gcp_utils.config import GCPSettings
from gcp_utils.controllers import (
    CloudStorageController,
    CloudTasksController,
    FirebaseAuthController,
    FirestoreController,
    PubSubController,
    SecretManagerController,
)


def main():
    # Initialize settings from environment
    settings = GCPSettings(
        project_id="my-gcp-project",
        storage_bucket="my-app-bucket",
    )

    print("=== GCP Utilities - Multi-Service Example ===\n")

    # 1. Secret Manager - Store database credentials
    print("1. Secret Manager: Storing database credentials...")
    secrets = SecretManagerController(settings)

    try:
        db_password = secrets.create_secret_with_value(
            secret_id="database-password",
            payload="super-secure-password-123",
            labels={"environment": "production"},
        )
        print(f"   Created secret: {db_password['name']}")

        # Retrieve the secret
        password = secrets.access_secret_version("database-password")
        print(f"   Retrieved password: {'*' * len(password)}")
    except Exception as e:
        print(f"   Note: {e}")

    # 2. Firebase Auth - Create a user
    print("\n2. Firebase Auth: Creating user...")
    auth = FirebaseAuthController(settings)

    try:
        user = auth.create_user(
            email="testuser@example.com",
            password="testpassword123",
            display_name="Test User",
            email_verified=True,
        )
        print(f"   Created user: {user['uid']} ({user['email']})")
        user_uid = user["uid"]

        # Set custom claims
        auth.set_custom_user_claims(user_uid, {"role": "admin", "tier": "premium"})
        print("   Set custom claims for user")
    except Exception as e:
        print(f"   Note: {e}")
        user_uid = None

    # 3. Firestore - Store user profile
    print("\n3. Firestore: Storing user profile...")
    firestore = FirestoreController(settings)

    if user_uid:
        profile = firestore.create_document(
            collection="user_profiles",
            document_id=user_uid,
            data={
                "display_name": "Test User",
                "email": "testuser@example.com",
                "created_at": firestore.client.SERVER_TIMESTAMP,
                "tier": "premium",
                "settings": {
                    "notifications": True,
                    "theme": "dark",
                },
            },
        )
        print(f"   Created profile: {profile.id}")

    # 4. Cloud Storage - Upload user avatar
    print("\n4. Cloud Storage: Uploading user avatar...")
    storage = CloudStorageController(settings)

    try:
        # Create bucket if needed
        storage.create_bucket(
            bucket_name=settings.storage_bucket,
            location=settings.location,
        )
    except Exception:
        pass  # Bucket may already exist

    avatar_result = storage.upload_from_string(
        bucket_name=settings.storage_bucket,
        destination_blob_name=f"avatars/{user_uid}/profile.png",
        content=b"fake-image-data",
        content_type="image/png",
        metadata={"user_id": user_uid or "test"},
    )
    print(f"   Uploaded avatar: {avatar_result.blob_name}")

    # Generate signed URL for avatar
    signed_url = storage.generate_signed_url(
        bucket_name=settings.storage_bucket,
        blob_name=avatar_result.blob_name,
        expiration=timedelta(hours=24),
    )
    print(f"   Generated signed URL (valid 24h)\n{signed_url}")

    # 5. Pub/Sub - Publish user registration event
    print("\n5. Pub/Sub: Publishing registration event...")
    pubsub = PubSubController(settings)

    try:
        # Create topic
        topic = pubsub.create_topic("user-registrations")
        print(f"   Created topic: {topic['name']}")

        # Publish event
        message_id = pubsub.publish_message(
            topic_name="user-registrations",
            data={
                "event": "user_registered",
                "user_id": user_uid or "test",
                "email": "testuser@example.com",
                "timestamp": "2025-11-14T10:00:00Z",
            },
            attributes={"source": "example_script", "version": "1.0"},
        )
        print(f"   Published message: {message_id}")

        # Create subscription
        subscription = pubsub.create_subscription(
            topic_name="user-registrations",
            subscription_name="email-notifications",
            ack_deadline_seconds=30,
        )
        print(f"   Created subscription: {subscription['name']}")
    except Exception as e:
        print(f"   Note: {e}")

    # 6. Cloud Tasks - Schedule welcome email
    print("\n6. Cloud Tasks: Scheduling welcome email...")
    tasks = CloudTasksController(settings)

    try:
        # Create queue
        queue = tasks.create_queue(
            queue_name="email-queue",
            max_dispatches_per_second=10.0,
        )
        print(f"   Created queue: {queue['name']}")

        # Create task to send welcome email
        task = tasks.create_http_task(
            queue="email-queue",
            url="https://myapp.com/send-welcome-email",
            payload={
                "user_id": user_uid or "test",
                "email": "testuser@example.com",
                "template": "welcome",
            },
            delay_seconds=60,  # Send after 1 minute
        )
        print(f"   Created task: {task.task_id}")
        print(f"   Scheduled for: {task.schedule_time}")
    except Exception as e:
        print(f"   Note: {e}")

    # 7. Cleanup demonstration
    print("\n7. Cleanup (commented out for safety)...")
    print("   # Clean up created resources:")
    print("   # - Delete Firebase user")
    print("   # - Delete Firestore documents")
    print("   # - Delete storage objects")
    print("   # - Delete Pub/Sub topic and subscriptions")
    print("   # - Delete Cloud Tasks queue")
    print("   # - Delete secrets")

    # Uncomment to actually clean up:
    # if user_uid:
    #     auth.delete_user(user_uid)
    #     firestore.delete_document("user_profiles", user_uid)
    # storage.delete_blob(settings.storage_bucket, avatar_result.blob_name)
    # pubsub.delete_subscription("email-notifications")
    # pubsub.delete_topic("user-registrations")
    # tasks.delete_queue("email-queue")
    # secrets.delete_secret("database-password")

    print("\n=== Example completed successfully! ===")


if __name__ == "__main__":
    main()
