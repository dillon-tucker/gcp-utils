"""
Tests for FirebaseAuthController.
"""
from unittest.mock import MagicMock, Mock, patch

import pytest

from gcp_utils.config import GCPSettings
from gcp_utils.controllers.firebase_auth import FirebaseAuthController
from gcp_utils.exceptions import (
    AuthenticationError,
    ResourceNotFoundError,
    ValidationError,
)


@pytest.fixture
def settings():
    """Fixture for GCPSettings."""
    return GCPSettings()


@pytest.fixture
def firebase_auth_controller(settings):
    """Fixture for FirebaseAuthController with mocked Firebase."""
    with patch('firebase_admin.get_app') as mock_get_app, \
         patch('firebase_admin.initialize_app'), \
         patch('firebase_admin.auth') as mock_auth:

        # Simulate Firebase already initialized
        mock_get_app.return_value = Mock()

        controller = FirebaseAuthController(settings)
        yield controller, mock_auth


def test_create_user_success(firebase_auth_controller):
    """Test creating a user successfully."""
    controller, mock_auth = firebase_auth_controller

    mock_user = MagicMock()
    mock_user.uid = "test-uid-123"
    mock_user.email = "test@example.com"
    mock_user.email_verified = False
    mock_user.phone_number = None
    mock_user.display_name = "Test User"
    mock_user.photo_url = None
    mock_user.disabled = False
    mock_user.custom_claims = {}
    mock_user.provider_data = []
    mock_user.tokens_valid_after_timestamp = 0
    mock_user.user_metadata = None

    mock_auth.create_user.return_value = mock_user

    user = controller.create_user(
        email="test@example.com",
        password="password123",
        display_name="Test User"
    )

    assert user["uid"] == "test-uid-123"
    assert user["email"] == "test@example.com"
    assert user["display_name"] == "Test User"
    mock_auth.create_user.assert_called_once()


def test_create_user_validation_error(firebase_auth_controller):
    """Test creating a user without email or phone number."""
    controller, mock_auth = firebase_auth_controller

    with pytest.raises(ValidationError) as exc_info:
        controller.create_user(password="password123")

    assert "Either email or phone_number must be provided" in str(exc_info.value.message)


def test_get_user_success(firebase_auth_controller):
    """Test getting a user by UID successfully."""
    controller, mock_auth = firebase_auth_controller

    mock_user = MagicMock()
    mock_user.uid = "test-uid-123"
    mock_user.email = "test@example.com"
    mock_user.email_verified = True
    mock_user.phone_number = None
    mock_user.display_name = "Test User"
    mock_user.photo_url = None
    mock_user.disabled = False
    mock_user.custom_claims = {"role": "admin"}
    mock_user.provider_data = []
    mock_user.tokens_valid_after_timestamp = 0
    mock_user.user_metadata = None

    mock_auth.get_user.return_value = mock_user

    user = controller.get_user("test-uid-123")

    assert user["uid"] == "test-uid-123"
    assert user["email"] == "test@example.com"
    assert user["custom_claims"]["role"] == "admin"


def test_get_user_not_found(firebase_auth_controller):
    """Test getting a non-existent user."""
    controller, mock_auth = firebase_auth_controller

    from firebase_admin.auth import UserNotFoundError
    mock_auth.get_user.side_effect = UserNotFoundError("User not found")
    mock_auth.UserNotFoundError = UserNotFoundError

    with pytest.raises(ResourceNotFoundError) as exc_info:
        controller.get_user("nonexistent-uid")

    assert "not found" in str(exc_info.value.message).lower()


def test_get_user_by_email_success(firebase_auth_controller):
    """Test getting a user by email successfully."""
    controller, mock_auth = firebase_auth_controller

    mock_user = MagicMock()
    mock_user.uid = "test-uid-123"
    mock_user.email = "test@example.com"
    mock_user.email_verified = True
    mock_user.phone_number = None
    mock_user.display_name = "Test User"
    mock_user.photo_url = None
    mock_user.disabled = False
    mock_user.custom_claims = {}
    mock_user.provider_data = []
    mock_user.tokens_valid_after_timestamp = 0
    mock_user.user_metadata = None

    mock_auth.get_user_by_email.return_value = mock_user

    user = controller.get_user_by_email("test@example.com")

    assert user["email"] == "test@example.com"


def test_get_user_by_phone_number_success(firebase_auth_controller):
    """Test getting a user by phone number successfully."""
    controller, mock_auth = firebase_auth_controller

    mock_user = MagicMock()
    mock_user.uid = "test-uid-123"
    mock_user.email = None
    mock_user.email_verified = False
    mock_user.phone_number = "+15555551234"
    mock_user.display_name = "Test User"
    mock_user.photo_url = None
    mock_user.disabled = False
    mock_user.custom_claims = {}
    mock_user.provider_data = []
    mock_user.tokens_valid_after_timestamp = 0
    mock_user.user_metadata = None

    mock_auth.get_user_by_phone_number.return_value = mock_user

    user = controller.get_user_by_phone_number("+15555551234")

    assert user["phone_number"] == "+15555551234"


def test_update_user_success(firebase_auth_controller):
    """Test updating a user successfully."""
    controller, mock_auth = firebase_auth_controller

    mock_user = MagicMock()
    mock_user.uid = "test-uid-123"
    mock_user.email = "updated@example.com"
    mock_user.email_verified = True
    mock_user.phone_number = None
    mock_user.display_name = "Updated Name"
    mock_user.photo_url = None
    mock_user.disabled = False
    mock_user.custom_claims = {}
    mock_user.provider_data = []
    mock_user.tokens_valid_after_timestamp = 0
    mock_user.user_metadata = None

    mock_auth.update_user.return_value = mock_user

    user = controller.update_user(
        "test-uid-123",
        email="updated@example.com",
        display_name="Updated Name"
    )

    assert user["email"] == "updated@example.com"
    assert user["display_name"] == "Updated Name"


def test_delete_user_success(firebase_auth_controller):
    """Test deleting a user successfully."""
    controller, mock_auth = firebase_auth_controller

    mock_auth.delete_user.return_value = None

    controller.delete_user("test-uid-123")

    mock_auth.delete_user.assert_called_once_with("test-uid-123")


def test_delete_users_success(firebase_auth_controller):
    """Test deleting multiple users successfully."""
    controller, mock_auth = firebase_auth_controller

    mock_result = MagicMock()
    mock_result.success_count = 3
    mock_result.failure_count = 0
    mock_result.errors = []

    mock_auth.delete_users.return_value = mock_result

    result = controller.delete_users(["uid1", "uid2", "uid3"])

    assert result["success_count"] == 3
    assert result["failure_count"] == 0
    assert len(result["errors"]) == 0


def test_delete_users_validation_error(firebase_auth_controller):
    """Test deleting users with empty list."""
    controller, mock_auth = firebase_auth_controller

    with pytest.raises(ValidationError) as exc_info:
        controller.delete_users([])

    assert "cannot be empty" in str(exc_info.value.message).lower()


def test_list_users_success(firebase_auth_controller):
    """Test listing users successfully."""
    controller, mock_auth = firebase_auth_controller

    mock_user1 = MagicMock()
    mock_user1.uid = "uid1"
    mock_user1.email = "user1@example.com"
    mock_user1.email_verified = True
    mock_user1.phone_number = None
    mock_user1.display_name = "User 1"
    mock_user1.photo_url = None
    mock_user1.disabled = False
    mock_user1.custom_claims = {}
    mock_user1.provider_data = []
    mock_user1.tokens_valid_after_timestamp = 0
    mock_user1.user_metadata = None

    mock_user2 = MagicMock()
    mock_user2.uid = "uid2"
    mock_user2.email = "user2@example.com"
    mock_user2.email_verified = False
    mock_user2.phone_number = None
    mock_user2.display_name = "User 2"
    mock_user2.photo_url = None
    mock_user2.disabled = False
    mock_user2.custom_claims = {}
    mock_user2.provider_data = []
    mock_user2.tokens_valid_after_timestamp = 0
    mock_user2.user_metadata = None

    mock_page = MagicMock()
    mock_page.users = [mock_user1, mock_user2]
    mock_page.has_next_page = False
    mock_page.next_page_token = None

    mock_auth.list_users.return_value = mock_page

    result = controller.list_users()

    assert len(result["users"]) == 2
    assert result["users"][0]["uid"] == "uid1"
    assert result["users"][1]["uid"] == "uid2"
    assert result["next_page_token"] is None


def test_set_custom_user_claims_success(firebase_auth_controller):
    """Test setting custom claims successfully."""
    controller, mock_auth = firebase_auth_controller

    mock_auth.set_custom_user_claims.return_value = None

    controller.set_custom_user_claims("test-uid", {"admin": True, "role": "superuser"})

    mock_auth.set_custom_user_claims.assert_called_once_with("test-uid", {"admin": True, "role": "superuser"})


def test_set_custom_user_claims_validation_error(firebase_auth_controller):
    """Test setting None as custom claims."""
    controller, mock_auth = firebase_auth_controller

    with pytest.raises(ValidationError) as exc_info:
        controller.set_custom_user_claims("test-uid", None)

    assert "cannot be None" in str(exc_info.value.message)


def test_verify_id_token_success(firebase_auth_controller):
    """Test verifying an ID token successfully."""
    controller, mock_auth = firebase_auth_controller

    mock_decoded = {
        "uid": "test-uid-123",
        "email": "test@example.com",
        "exp": 1234567890
    }

    mock_auth.verify_id_token.return_value = mock_decoded

    decoded = controller.verify_id_token("valid-token")

    assert decoded["uid"] == "test-uid-123"
    assert decoded["email"] == "test@example.com"


def test_verify_id_token_invalid(firebase_auth_controller):
    """Test verifying an invalid ID token."""
    controller, mock_auth = firebase_auth_controller

    from firebase_admin import auth as firebase_auth
    mock_auth.InvalidIdTokenError = firebase_auth.InvalidIdTokenError
    mock_auth.verify_id_token.side_effect = firebase_auth.InvalidIdTokenError("Invalid token")

    with pytest.raises(AuthenticationError) as exc_info:
        controller.verify_id_token("invalid-token")

    assert "Invalid ID token" in str(exc_info.value.message)


def test_verify_id_token_expired(firebase_auth_controller):
    """Test verifying an expired ID token."""
    controller, mock_auth = firebase_auth_controller

    from firebase_admin import auth as firebase_auth
    mock_auth.ExpiredIdTokenError = firebase_auth.ExpiredIdTokenError
    mock_auth.verify_id_token.side_effect = firebase_auth.ExpiredIdTokenError("Token expired")

    with pytest.raises(AuthenticationError) as exc_info:
        controller.verify_id_token("expired-token")

    assert "Expired ID token" in str(exc_info.value.message)


def test_verify_id_token_revoked(firebase_auth_controller):
    """Test verifying a revoked ID token."""
    controller, mock_auth = firebase_auth_controller

    from firebase_admin import auth as firebase_auth
    mock_auth.RevokedIdTokenError = firebase_auth.RevokedIdTokenError
    mock_auth.verify_id_token.side_effect = firebase_auth.RevokedIdTokenError("Token revoked")

    with pytest.raises(AuthenticationError) as exc_info:
        controller.verify_id_token("revoked-token", check_revoked=True)

    assert "Revoked ID token" in str(exc_info.value.message)


def test_revoke_refresh_tokens_success(firebase_auth_controller):
    """Test revoking refresh tokens successfully."""
    controller, mock_auth = firebase_auth_controller

    mock_auth.revoke_refresh_tokens.return_value = None

    controller.revoke_refresh_tokens("test-uid")

    mock_auth.revoke_refresh_tokens.assert_called_once_with("test-uid")


def test_create_custom_token_success(firebase_auth_controller):
    """Test creating a custom token successfully."""
    controller, mock_auth = firebase_auth_controller

    mock_auth.create_custom_token.return_value = b"custom-token-bytes"

    token = controller.create_custom_token("test-uid", {"claim1": "value1"})

    assert token == "custom-token-bytes"
    mock_auth.create_custom_token.assert_called_once_with("test-uid", developer_claims={"claim1": "value1"})


def test_generate_email_verification_link_success(firebase_auth_controller):
    """Test generating an email verification link successfully."""
    controller, mock_auth = firebase_auth_controller

    mock_auth.generate_email_verification_link.return_value = "https://example.com/verify?token=abc123"

    link = controller.generate_email_verification_link("test@example.com")

    assert link == "https://example.com/verify?token=abc123"
    mock_auth.generate_email_verification_link.assert_called_once()


def test_generate_password_reset_link_success(firebase_auth_controller):
    """Test generating a password reset link successfully."""
    controller, mock_auth = firebase_auth_controller

    mock_auth.generate_password_reset_link.return_value = "https://example.com/reset?token=xyz789"

    link = controller.generate_password_reset_link("test@example.com")

    assert link == "https://example.com/reset?token=xyz789"
    mock_auth.generate_password_reset_link.assert_called_once()
