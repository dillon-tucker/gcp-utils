"""
Example usage of the Pub/Sub controller.

This example demonstrates:
- Creating and managing topics
- Creating and managing subscriptions
- Publishing messages with attributes
- Batch publishing
- Pulling and acknowledging messages
- Push and pull subscription models
"""

import sys
import time
from pathlib import Path

# Add src to path for running without installation
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gcp_utils.controllers import PubSubController


def main() -> None:
    """Demonstrate Pub/Sub controller functionality."""

    # Initialize controller (automatically loads from .env)
    pubsub = PubSubController()

    print("=" * 80)
    print("Pub/Sub Controller Example")
    print("=" * 80)

    # 1. Create a topic
    print("\n1. Creating topic...")
    topic_name = "example-topic"
    try:
        topic = pubsub.create_topic(topic_name)
        print(f"[OK] Created topic: {topic.name}")
        print(f"  Full path: {topic.full_name}")
    except Exception as e:
        print(f"[FAIL] Failed to create topic: {e}")
        print("  Topic might already exist - continuing...")

    # 2. Get topic details
    print("\n2. Getting topic details...")
    try:
        topic = pubsub.get_topic(topic_name)
        print(f"[OK] Retrieved topic: {topic.name}")
        print(f"  Labels: {topic.labels or 'None'}")
    except Exception as e:
        print(f"[FAIL] Failed to get topic: {e}")

    # 3. List all topics
    print("\n3. Listing topics...")
    try:
        topics = pubsub.list_topics()
        print(f"[OK] Found {len(topics)} topic(s):")
        for topic in topics[:5]:  # Show first 5
            print(f"  - {topic.name}")
        if len(topics) > 5:
            print(f"  ... and {len(topics) - 5} more")
    except Exception as e:
        print(f"[FAIL] Failed to list topics: {e}")

    # 4. Create a pull subscription
    print("\n4. Creating pull subscription...")
    subscription_name = "example-subscription"
    try:
        subscription = pubsub.create_subscription(
            topic_name=topic_name,
            subscription_name=subscription_name,
            ack_deadline_seconds=30,
            enable_message_ordering=False,
        )
        print(f"[OK] Created subscription: {subscription.name}")
        print(f"  Topic: {subscription.topic}")
        print(f"  Ack deadline: {subscription.ack_deadline_seconds}s")
    except Exception as e:
        print(f"[FAIL] Failed to create subscription: {e}")
        print("  Subscription might already exist - continuing...")

    # 5. Create a push subscription (with endpoint URL)
    print("\n5. Creating push subscription...")
    push_subscription_name = "example-push-subscription"
    try:
        subscription = pubsub.create_subscription(
            topic_name=topic_name,
            subscription_name=push_subscription_name,
            push_endpoint="https://example.com/webhook",
            ack_deadline_seconds=60,
        )
        print(f"[OK] Created push subscription: {subscription.name}")
        print(f"  Push endpoint: {subscription.push_endpoint or 'N/A'}")
    except Exception as e:
        print(f"[FAIL] Failed to create push subscription: {e}")
        print("  Push subscription might already exist - continuing...")

    # 6. List subscriptions for topic
    print("\n6. Listing subscriptions for topic...")
    try:
        subscriptions = pubsub.list_subscriptions(topic_name=topic_name)
        print(
            f"[OK] Found {len(subscriptions)} subscription(s) for topic '{topic_name}':"
        )
        for sub in subscriptions:
            print(f"  - {sub.name}")
    except Exception as e:
        print(f"[FAIL] Failed to list subscriptions: {e}")

    # 7. Publish a simple message
    print("\n7. Publishing simple message...")
    try:
        message_id = pubsub.publish_message(
            topic_name=topic_name,
            data={"message": "Hello from Pub/Sub!", "timestamp": time.time()},
        )
        print(f"[OK] Published message ID: {message_id}")
    except Exception as e:
        print(f"[FAIL] Failed to publish message: {e}")

    # 8. Publish message with attributes
    print("\n8. Publishing message with attributes...")
    try:
        message_id = pubsub.publish_message(
            topic_name=topic_name,
            data={
                "event": "user_signup",
                "user_id": "12345",
                "email": "user@example.com",
            },
            attributes={
                "source": "web_app",
                "version": "1.0",
                "priority": "high",
            },
        )
        print(f"[OK] Published message with attributes, ID: {message_id}")
    except Exception as e:
        print(f"[FAIL] Failed to publish message with attributes: {e}")

    # 9. Batch publish messages
    print("\n9. Batch publishing messages...")
    try:
        messages = [
            {
                "data": {"event": "page_view", "page": "/home"},
                "attributes": {"user": "user1"},
            },
            {
                "data": {"event": "page_view", "page": "/products"},
                "attributes": {"user": "user2"},
            },
            {
                "data": {"event": "purchase", "amount": 99.99},
                "attributes": {"user": "user1", "priority": "high"},
            },
        ]

        message_ids = pubsub.publish_messages_batch(topic_name, messages)
        print(f"[OK] Published {len(message_ids)} messages in batch")
        for i, msg_id in enumerate(message_ids):
            print(f"  Message {i+1} ID: {msg_id}")
    except Exception as e:
        print(f"[FAIL] Failed to batch publish: {e}")

    # 10. Pull messages
    print("\n10. Pulling messages from subscription...")
    print("  Waiting 2 seconds for messages to propagate...")
    time.sleep(2)

    try:
        messages = pubsub.pull_messages(
            subscription_name=subscription_name,
            max_messages=10,
            return_immediately=True,
        )
        print(f"[OK] Pulled {len(messages)} message(s):")

        ack_ids = []
        for i, msg in enumerate(messages[:3], 1):  # Show first 3 messages
            print(f"\n  Message {i}:")
            print(f"    Message ID: {msg['message_id']}")
            print(f"    Publish time: {msg['publish_time']}")
            print(f"    Data: {msg['data']}")
            if msg.get("attributes"):
                print(f"    Attributes: {msg['attributes']}")
            ack_ids.append(msg["ack_id"])

        if len(messages) > 3:
            print(f"\n  ... and {len(messages) - 3} more messages")
            ack_ids.extend([msg["ack_id"] for msg in messages[3:]])

        # 11. Acknowledge messages
        if ack_ids:
            print(f"\n11. Acknowledging {len(ack_ids)} message(s)...")
            try:
                pubsub.acknowledge_messages(subscription_name, ack_ids)
                print(f"[OK] Acknowledged {len(ack_ids)} message(s)")
                print("  Messages will not be redelivered")
            except Exception as e:
                print(f"[FAIL] Failed to acknowledge messages: {e}")
        else:
            print("\n11. No messages to acknowledge")

    except Exception as e:
        print(f"[FAIL] Failed to pull messages: {e}")

    # 12. Get subscription details
    print("\n12. Getting subscription details...")
    try:
        subscription = pubsub.get_subscription(subscription_name)
        print(f"[OK] Retrieved subscription: {subscription.name}")
        print(f"  Topic: {subscription.topic}")
        print(f"  Ack deadline: {subscription.ack_deadline_seconds}s")
        print(f"  Message ordering: {subscription.enable_message_ordering}")
    except Exception as e:
        print(f"[FAIL] Failed to get subscription: {e}")

    # 13. Cleanup - Delete subscriptions
    print("\n13. Cleaning up subscriptions...")
    try:
        pubsub.delete_subscription(subscription_name)
        print(f"[OK] Deleted subscription: {subscription_name}")
    except Exception as e:
        print(f"[FAIL] Failed to delete subscription: {e}")

    try:
        pubsub.delete_subscription(push_subscription_name)
        print(f"[OK] Deleted push subscription: {push_subscription_name}")
    except Exception as e:
        print(f"[FAIL] Failed to delete push subscription: {e}")

    # 14. Cleanup - Delete topic
    print("\n14. Cleaning up topic...")
    try:
        pubsub.delete_topic(topic_name)
        print(f"[OK] Deleted topic: {topic_name}")
    except Exception as e:
        print(f"[FAIL] Failed to delete topic: {e}")

    # Example use cases
    print("\n" + "=" * 80)
    print("Common Use Cases:")
    print("=" * 80)
    print(
        """
1. Event-Driven Architecture:
   - User actions trigger events (signup, purchase, etc.)
   - Multiple services subscribe to process events
   - Decoupled microservices communication

2. Data Streaming:
   - Stream logs from multiple sources
   - Real-time analytics pipelines
   - IoT sensor data processing

3. Asynchronous Task Processing:
   - Background job processing
   - Email/notification queues
   - Image/video processing pipelines

4. Integration Patterns:
   - Fan-out: One publisher, multiple subscribers
   - Fan-in: Multiple publishers, one subscriber
   - Message routing with attributes

5. Message Ordering:
   - Enable message ordering for sequential processing
   - Use ordering keys to maintain message order
   - Guaranteed delivery with at-least-once semantics

6. Dead Letter Topics:
   - Configure dead letter topics for failed messages
   - Retry policies for transient failures
   - Monitor and alert on message delivery issues
"""
    )

    print("=" * 80)
    print("Example completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
