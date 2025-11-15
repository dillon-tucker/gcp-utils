"""
Pub/Sub controller for messaging and event streaming.

This module provides a high-level interface for Google Cloud Pub/Sub
operations including topic and subscription management.
"""

import json
from typing import Any, Callable, Optional

from google.cloud import pubsub_v1
from google.auth.credentials import Credentials
from google.api_core import retry

from ..config import GCPSettings, get_settings
from ..exceptions import PubSubError, ResourceNotFoundError, ValidationError
from ..models.pubsub import TopicInfo, SubscriptionInfo


class PubSubController:
    """
    Controller for Google Cloud Pub/Sub operations.

    This controller provides methods for managing topics, subscriptions,
    and publishing/consuming messages.

    Example:
        >>> from gcp_utils.controllers import PubSubController
        >>>
        >>> # Automatically loads from .env file
        >>> pubsub_ctrl = PubSubController()
        >>>
        >>> # Publish a message
        >>> future = pubsub_ctrl.publish_message(
        ...     "my-topic",
        ...     {"event": "user_created", "user_id": "123"}
        ... )
    """

    def __init__(
        self,
        settings: Optional[GCPSettings] = None,
        credentials: Optional[Credentials] = None,
    ) -> None:
        """
        Initialize the Pub/Sub controller.

        Args:
            settings: GCP configuration settings. If not provided, loads from environment/.env file.
            credentials: Optional custom credentials

        Raises:
            PubSubError: If client initialization fails
        """
        self.settings = settings or get_settings()

        try:
            self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
            self.subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
        except Exception as e:
            raise PubSubError(
                f"Failed to initialize Pub/Sub client: {e}",
                details={"error": str(e)},
            )

    def create_topic(
        self,
        topic_name: str,
        labels: Optional[dict[str, str]] = None,
    ) -> TopicInfo:
        """
        Create a new Pub/Sub topic.

        Args:
            topic_name: Name of the topic (without prefix)
            labels: Optional labels for the topic

        Returns:
            TopicInfo object with native object binding

        Raises:
            ValidationError: If topic name is invalid
            PubSubError: If creation fails
        """
        if not topic_name:
            raise ValidationError("Topic name cannot be empty")

        try:
            topic_path = self._get_topic_path(topic_name)

            topic = self.publisher.create_topic(
                request={
                    "name": topic_path,
                    "labels": labels or {},
                }
            )

            return self._topic_to_model(topic)

        except ValidationError:
            raise
        except Exception as e:
            if "already exists" in str(e).lower():
                # Topic already exists, get it instead
                return self.get_topic(topic_name)
            raise PubSubError(
                f"Failed to create topic '{topic_name}': {e}",
                details={"topic": topic_name, "error": str(e)},
            )

    def get_topic(self, topic_name: str) -> TopicInfo:
        """
        Get topic information.

        Args:
            topic_name: Name of the topic

        Returns:
            TopicInfo object with native object binding

        Raises:
            ResourceNotFoundError: If topic doesn't exist
            PubSubError: If operation fails
        """
        try:
            topic_path = self._get_topic_path(topic_name)
            topic = self.publisher.get_topic(topic=topic_path)

            return self._topic_to_model(topic)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Topic '{topic_name}' not found",
                    details={"topic": topic_name},
                )
            raise PubSubError(
                f"Failed to get topic '{topic_name}': {e}",
                details={"topic": topic_name, "error": str(e)},
            )

    def list_topics(self) -> list[TopicInfo]:
        """
        List all topics in the project.

        Returns:
            List of TopicInfo objects with native object binding

        Raises:
            PubSubError: If listing fails
        """
        try:
            project_path = f"projects/{self.settings.project_id}"
            topics = self.publisher.list_topics(project=project_path)

            return [self._topic_to_model(topic) for topic in topics]

        except Exception as e:
            raise PubSubError(
                f"Failed to list topics: {e}",
                details={"error": str(e)},
            )

    def delete_topic(self, topic_name: str) -> None:
        """
        Delete a topic.

        Args:
            topic_name: Name of the topic to delete

        Raises:
            PubSubError: If deletion fails
        """
        try:
            topic_path = self._get_topic_path(topic_name)
            self.publisher.delete_topic(topic=topic_path)

        except Exception as e:
            raise PubSubError(
                f"Failed to delete topic '{topic_name}': {e}",
                details={"topic": topic_name, "error": str(e)},
            )

    def publish_message(
        self,
        topic_name: str,
        data: dict[str, Any] | str | bytes,
        attributes: Optional[dict[str, str]] = None,
        ordering_key: Optional[str] = None,
    ) -> str:
        """
        Publish a message to a topic.

        Args:
            topic_name: Name of the topic
            data: Message data (dict, string, or bytes)
            attributes: Optional message attributes
            ordering_key: Optional ordering key for ordered delivery

        Returns:
            Message ID

        Raises:
            ValidationError: If data is invalid
            PubSubError: If publishing fails
        """
        try:
            topic_path = self._get_topic_path(topic_name)

            # Convert data to bytes
            if isinstance(data, dict):
                data_bytes = json.dumps(data).encode("utf-8")
            elif isinstance(data, str):
                data_bytes = data.encode("utf-8")
            elif isinstance(data, bytes):
                data_bytes = data
            else:
                raise ValidationError(f"Invalid data type: {type(data)}")

            # Publish message
            future = self.publisher.publish(
                topic_path,
                data_bytes,
                **(attributes or {}),
                ordering_key=ordering_key or "",
            )

            # Wait for the message to be published
            message_id = future.result()

            return message_id

        except ValidationError:
            raise
        except Exception as e:
            raise PubSubError(
                f"Failed to publish message to topic '{topic_name}': {e}",
                details={"topic": topic_name, "error": str(e)},
            )

    def publish_messages_batch(
        self,
        topic_name: str,
        messages: list[dict[str, Any]],
    ) -> list[str]:
        """
        Publish multiple messages in batch.

        Args:
            topic_name: Name of the topic
            messages: List of message dictionaries with 'data' and optional 'attributes'

        Returns:
            List of message IDs

        Raises:
            ValidationError: If messages are invalid
            PubSubError: If publishing fails
        """
        if not messages:
            raise ValidationError("Messages list cannot be empty")

        try:
            topic_path = self._get_topic_path(topic_name)
            futures = []

            for msg in messages:
                data = msg.get("data")
                if data is None:
                    raise ValidationError("Each message must have 'data'")

                # Convert data to bytes
                if isinstance(data, dict):
                    data_bytes = json.dumps(data).encode("utf-8")
                elif isinstance(data, str):
                    data_bytes = data.encode("utf-8")
                elif isinstance(data, bytes):
                    data_bytes = data
                else:
                    raise ValidationError(f"Invalid data type: {type(data)}")

                attributes = msg.get("attributes", {})
                ordering_key = msg.get("ordering_key", "")

                future = self.publisher.publish(
                    topic_path,
                    data_bytes,
                    **attributes,
                    ordering_key=ordering_key,
                )
                futures.append(future)

            # Wait for all messages to be published
            message_ids = [future.result() for future in futures]

            return message_ids

        except ValidationError:
            raise
        except Exception as e:
            raise PubSubError(
                f"Failed to publish batch messages to topic '{topic_name}': {e}",
                details={"topic": topic_name, "error": str(e)},
            )

    def create_subscription(
        self,
        topic_name: str,
        subscription_name: str,
        ack_deadline_seconds: int = 10,
        push_endpoint: Optional[str] = None,
        filter_expression: Optional[str] = None,
        retain_acked_messages: bool = False,
        message_retention_duration_seconds: int = 604800,  # 7 days
    ) -> SubscriptionInfo:
        """
        Create a subscription to a topic.

        Args:
            topic_name: Name of the topic to subscribe to
            subscription_name: Name for the subscription
            ack_deadline_seconds: Acknowledgement deadline (10-600 seconds)
            push_endpoint: Optional HTTP endpoint for push delivery
            filter_expression: Optional filter for messages
            retain_acked_messages: Whether to retain acknowledged messages
            message_retention_duration_seconds: Message retention duration

        Returns:
            SubscriptionInfo object with native object binding

        Raises:
            ValidationError: If parameters are invalid
            PubSubError: If creation fails
        """
        if not subscription_name:
            raise ValidationError("Subscription name cannot be empty")

        try:
            topic_path = self._get_topic_path(topic_name)
            subscription_path = self._get_subscription_path(subscription_name)

            subscription_config = {
                "name": subscription_path,
                "topic": topic_path,
                "ack_deadline_seconds": ack_deadline_seconds,
                "retain_acked_messages": retain_acked_messages,
                "message_retention_duration": {
                    "seconds": message_retention_duration_seconds
                },
            }

            if push_endpoint:
                subscription_config["push_config"] = {"push_endpoint": push_endpoint}

            if filter_expression:
                subscription_config["filter"] = filter_expression

            subscription = self.subscriber.create_subscription(
                request=subscription_config
            )

            return self._subscription_to_model(subscription)

        except ValidationError:
            raise
        except Exception as e:
            if "already exists" in str(e).lower():
                return self.get_subscription(subscription_name)
            raise PubSubError(
                f"Failed to create subscription '{subscription_name}': {e}",
                details={"subscription": subscription_name, "error": str(e)},
            )

    def get_subscription(self, subscription_name: str) -> SubscriptionInfo:
        """
        Get subscription information.

        Args:
            subscription_name: Name of the subscription

        Returns:
            SubscriptionInfo object with native object binding

        Raises:
            ResourceNotFoundError: If subscription doesn't exist
            PubSubError: If operation fails
        """
        try:
            subscription_path = self._get_subscription_path(subscription_name)
            subscription = self.subscriber.get_subscription(
                subscription=subscription_path
            )

            return self._subscription_to_model(subscription)

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Subscription '{subscription_name}' not found",
                    details={"subscription": subscription_name},
                )
            raise PubSubError(
                f"Failed to get subscription '{subscription_name}': {e}",
                details={"subscription": subscription_name, "error": str(e)},
            )

    def list_subscriptions(
        self, topic_name: Optional[str] = None
    ) -> list[SubscriptionInfo]:
        """
        List subscriptions.

        Args:
            topic_name: Optional topic name to filter subscriptions

        Returns:
            List of SubscriptionInfo objects with native object binding

        Raises:
            PubSubError: If listing fails
        """
        try:
            if topic_name:
                topic_path = self._get_topic_path(topic_name)
                subscriptions = self.publisher.list_topic_subscriptions(
                    topic=topic_path
                )
                # Get full subscription details
                return [
                    self._subscription_to_model(self.subscriber.get_subscription(subscription=sub))
                    for sub in subscriptions
                ]
            else:
                project_path = f"projects/{self.settings.project_id}"
                subscriptions = self.subscriber.list_subscriptions(project=project_path)
                return [self._subscription_to_model(sub) for sub in subscriptions]

        except Exception as e:
            raise PubSubError(
                f"Failed to list subscriptions: {e}",
                details={"error": str(e)},
            )

    def delete_subscription(self, subscription_name: str) -> None:
        """
        Delete a subscription.

        Args:
            subscription_name: Name of the subscription to delete

        Raises:
            PubSubError: If deletion fails
        """
        try:
            subscription_path = self._get_subscription_path(subscription_name)
            self.subscriber.delete_subscription(subscription=subscription_path)

        except Exception as e:
            raise PubSubError(
                f"Failed to delete subscription '{subscription_name}': {e}",
                details={"subscription": subscription_name, "error": str(e)},
            )

    def pull_messages(
        self,
        subscription_name: str,
        max_messages: int = 10,
        return_immediately: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Pull messages from a subscription.

        Args:
            subscription_name: Name of the subscription
            max_messages: Maximum number of messages to pull
            return_immediately: Return immediately if no messages

        Returns:
            List of message dictionaries

        Raises:
            PubSubError: If pull fails
        """
        try:
            subscription_path = self._get_subscription_path(subscription_name)

            response = self.subscriber.pull(
                request={
                    "subscription": subscription_path,
                    "max_messages": max_messages,
                    "return_immediately": return_immediately,
                }
            )

            messages = []
            for received_message in response.received_messages:
                msg = received_message.message
                try:
                    data = json.loads(msg.data.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    data = msg.data.decode("utf-8", errors="replace")

                messages.append(
                    {
                        "ack_id": received_message.ack_id,
                        "message_id": msg.message_id,
                        "data": data,
                        "attributes": dict(msg.attributes),
                        "publish_time": msg.publish_time,
                    }
                )

            return messages

        except Exception as e:
            raise PubSubError(
                f"Failed to pull messages from subscription '{subscription_name}': {e}",
                details={"subscription": subscription_name, "error": str(e)},
            )

    def acknowledge_messages(
        self,
        subscription_name: str,
        ack_ids: list[str],
    ) -> None:
        """
        Acknowledge received messages.

        Args:
            subscription_name: Name of the subscription
            ack_ids: List of acknowledgement IDs from pulled messages

        Raises:
            ValidationError: If ack_ids is empty
            PubSubError: If acknowledgement fails
        """
        if not ack_ids:
            raise ValidationError("Acknowledgement IDs list cannot be empty")

        try:
            subscription_path = self._get_subscription_path(subscription_name)

            self.subscriber.acknowledge(
                request={
                    "subscription": subscription_path,
                    "ack_ids": ack_ids,
                }
            )

        except ValidationError:
            raise
        except Exception as e:
            raise PubSubError(
                f"Failed to acknowledge messages: {e}",
                details={"subscription": subscription_name, "error": str(e)},
            )

    def _get_topic_path(self, topic_name: str) -> str:
        """Get the full topic path."""
        prefix = self.settings.pubsub_topic_prefix
        full_name = f"{prefix}{topic_name}" if prefix else topic_name
        return self.publisher.topic_path(self.settings.project_id, full_name)

    def _get_subscription_path(self, subscription_name: str) -> str:
        """Get the full subscription path."""
        return self.subscriber.subscription_path(
            self.settings.project_id, subscription_name
        )

    def _topic_to_model(self, topic: Any) -> TopicInfo:
        """Convert Topic to TopicInfo model with native object binding."""
        model = TopicInfo(
            name=topic.name.split("/")[-1],
            full_name=topic.name,
            labels=dict(topic.labels) if hasattr(topic, "labels") else {},
        )
        # Bind the native object
        model._topic_object = topic
        return model

    def _subscription_to_model(self, subscription: Any) -> SubscriptionInfo:
        """Convert Subscription to SubscriptionInfo model with native object binding."""
        model = SubscriptionInfo(
            name=subscription.name.split("/")[-1],
            full_name=subscription.name,
            topic=subscription.topic if hasattr(subscription, "topic") else None,
            ack_deadline_seconds=(
                subscription.ack_deadline_seconds
                if hasattr(subscription, "ack_deadline_seconds")
                else None
            ),
            retain_acked_messages=(
                subscription.retain_acked_messages
                if hasattr(subscription, "retain_acked_messages")
                else False
            ),
        )
        # Bind the native object
        model._subscription_object = subscription
        return model
