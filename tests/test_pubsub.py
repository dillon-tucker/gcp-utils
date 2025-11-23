"""
Tests for PubSubController.
"""

from unittest.mock import MagicMock, patch

import pytest

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.pubsub import PubSubController
from gcp_utils.exceptions import ResourceNotFoundError


@pytest.fixture
def settings():
    """Fixture for GCPSettings."""
    return GCPSettings()


@pytest.fixture
def pubsub_controller(settings):
    """Fixture for PubSubController with mocked clients."""
    with (
        patch("google.cloud.pubsub_v1.PublisherClient") as mock_publisher,
        patch("google.cloud.pubsub_v1.SubscriberClient") as mock_subscriber,
    ):
        controller = PubSubController(settings)
        controller._publisher = mock_publisher.return_value
        controller._subscriber = mock_subscriber.return_value
        yield controller


def test_create_topic_success(pubsub_controller):
    """Test creating a topic successfully."""
    mock_topic = MagicMock()
    mock_topic.name = "projects/test-project/topics/test-topic"

    pubsub_controller._publisher.create_topic.return_value = mock_topic

    topic = pubsub_controller.create_topic("test-topic")

    assert topic.name == "test-topic"


def test_get_topic_success(pubsub_controller):
    """Test getting a topic successfully."""
    mock_topic = MagicMock()
    mock_topic.name = "projects/test-project/topics/test-topic"

    pubsub_controller._publisher.get_topic.return_value = mock_topic

    topic = pubsub_controller.get_topic("test-topic")

    assert topic.name == "test-topic"


def test_get_topic_not_found(pubsub_controller):
    """Test getting a non-existent topic."""
    pubsub_controller._publisher.get_topic.side_effect = Exception("404 Not Found")

    with pytest.raises(ResourceNotFoundError):
        pubsub_controller.get_topic("non-existent-topic")


def test_publish_message_success(pubsub_controller):
    """Test publishing a message successfully."""
    mock_future = MagicMock()
    mock_future.result.return_value = "message-id-123"

    pubsub_controller._publisher.publish.return_value = mock_future

    message_id = pubsub_controller.publish_message("test-topic", {"key": "value"})

    assert message_id == "message-id-123"


def test_create_subscription_success(pubsub_controller):
    """Test creating a subscription successfully."""
    mock_subscription = MagicMock()
    mock_subscription.name = "projects/test-project/subscriptions/test-subscription"

    pubsub_controller._subscriber.create_subscription.return_value = mock_subscription

    subscription = pubsub_controller.create_subscription(
        "test-subscription", "test-topic"
    )

    assert subscription.name == "test-subscription"


def test_delete_topic(pubsub_controller):
    """Test deleting a topic."""
    pubsub_controller._publisher.delete_topic.return_value = None

    pubsub_controller.delete_topic("test-topic")

    pubsub_controller._publisher.delete_topic.assert_called_once()


def test_delete_subscription(pubsub_controller):
    """Test deleting a subscription."""
    pubsub_controller._subscriber.delete_subscription.return_value = None

    pubsub_controller.delete_subscription("test-subscription")

    pubsub_controller._subscriber.delete_subscription.assert_called_once()
