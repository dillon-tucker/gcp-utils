"""Data models for Pub/Sub operations."""

from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

if TYPE_CHECKING:
    from google.cloud.pubsub_v1.types import Topic, Subscription


class TopicInfo(BaseModel):
    """
    Information about a Pub/Sub topic with native object binding.

    This model wraps the Google Cloud Topic object, providing both
    structured Pydantic data and access to the full Pub/Sub API
    via `_topic_object`.

    Example:
        >>> topic = pubsub_ctrl.create_topic("my-topic")
        >>>
        >>> # Use Pydantic fields
        >>> print(f"Topic: {topic.name}")
        >>>
        >>> # Use convenience methods
        >>> message_id = topic.publish({"data": "value"})
        >>> topic.delete()
    """

    name: str = Field(..., description="Topic name (without prefix)")
    full_name: str = Field(..., description="Full topic path")
    labels: dict[str, str] = Field(default_factory=dict, description="Topic labels")

    # The actual Topic object (private attribute, not serialized)
    _topic_object: Optional["Topic"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Convenience methods that delegate to controller operations

    def publish(self, data: dict[str, Any] | str | bytes, attributes: Optional[dict[str, str]] = None) -> str:
        """
        Publish a message to this topic.

        Args:
            data: Message data
            attributes: Optional message attributes

        Returns:
            Message ID

        Raises:
            ValueError: If no Topic object is bound

        Note:
            This requires access to the controller. Consider using
            PubSubController.publish_message() directly instead.
        """
        if not self._topic_object:
            raise ValueError("No Topic object bound to this TopicInfo")
        raise NotImplementedError(
            "Message publishing must be performed via PubSubController.publish_message()"
        )

    def delete(self) -> None:
        """
        Delete this topic.

        Raises:
            ValueError: If no Topic object is bound

        Note:
            This requires access to the controller. Consider using
            PubSubController.delete_topic() directly instead.
        """
        if not self._topic_object:
            raise ValueError("No Topic object bound to this TopicInfo")
        raise NotImplementedError(
            "Topic deletion must be performed via PubSubController.delete_topic()"
        )


class SubscriptionInfo(BaseModel):
    """
    Information about a Pub/Sub subscription with native object binding.

    This model wraps the Google Cloud Subscription object, providing both
    structured Pydantic data and access to the full Pub/Sub API
    via `_subscription_object`.

    Example:
        >>> subscription = pubsub_ctrl.create_subscription("my-topic", "my-sub")
        >>>
        >>> # Use Pydantic fields
        >>> print(f"Subscription: {subscription.name}")
        >>> print(f"Ack deadline: {subscription.ack_deadline_seconds}s")
        >>>
        >>> # Use convenience methods
        >>> messages = subscription.pull(max_messages=10)
        >>> subscription.acknowledge(ack_ids)
        >>> subscription.delete()
    """

    name: str = Field(..., description="Subscription name (without prefix)")
    full_name: str = Field(..., description="Full subscription path")
    topic: Optional[str] = Field(None, description="Topic path")
    ack_deadline_seconds: Optional[int] = Field(None, description="Acknowledgement deadline in seconds")
    retain_acked_messages: bool = Field(default=False, description="Whether to retain acknowledged messages")

    # The actual Subscription object (private attribute, not serialized)
    _subscription_object: Optional["Subscription"] = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Convenience methods that delegate to controller operations

    def pull(self, max_messages: int = 10) -> list[dict[str, Any]]:
        """
        Pull messages from this subscription.

        Args:
            max_messages: Maximum number of messages to pull

        Returns:
            List of message dictionaries

        Raises:
            ValueError: If no Subscription object is bound

        Note:
            This requires access to the controller. Consider using
            PubSubController.pull_messages() directly instead.
        """
        if not self._subscription_object:
            raise ValueError("No Subscription object bound to this SubscriptionInfo")
        raise NotImplementedError(
            "Message pulling must be performed via PubSubController.pull_messages()"
        )

    def acknowledge(self, ack_ids: list[str]) -> None:
        """
        Acknowledge received messages.

        Args:
            ack_ids: List of acknowledgement IDs

        Raises:
            ValueError: If no Subscription object is bound

        Note:
            This requires access to the controller. Consider using
            PubSubController.acknowledge_messages() directly instead.
        """
        if not self._subscription_object:
            raise ValueError("No Subscription object bound to this SubscriptionInfo")
        raise NotImplementedError(
            "Message acknowledgement must be performed via PubSubController.acknowledge_messages()"
        )

    def delete(self) -> None:
        """
        Delete this subscription.

        Raises:
            ValueError: If no Subscription object is bound

        Note:
            This requires access to the controller. Consider using
            PubSubController.delete_subscription() directly instead.
        """
        if not self._subscription_object:
            raise ValueError("No Subscription object bound to this SubscriptionInfo")
        raise NotImplementedError(
            "Subscription deletion must be performed via PubSubController.delete_subscription()"
        )
