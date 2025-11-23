"""
Firebase Authentication controller.

This module provides a high-level interface for Firebase Authentication
operations including user management, token verification, and custom claims.
"""

from typing import Any

import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin.auth import (
    UserNotFoundError as FirebaseUserNotFoundError,
)
from firebase_admin.auth import (
    UserRecord,
)

from ..config import GCPSettings, get_settings
from ..exceptions import (
    AuthenticationError,
    FirebaseError,
    ResourceNotFoundError,
    ValidationError,
)


class FirebaseAuthController:
    """
    Controller for Firebase Authentication operations.

    This controller provides methods for user management, token verification,
    and custom claims management.

    Example:
        >>> from gcp_utils.controllers import FirebaseAuthController
        >>>
        >>> # Automatically loads from .env file
        >>> auth_ctrl = FirebaseAuthController()
        >>>
        >>> # Create a user
        >>> user = auth_ctrl.create_user(
        ...     email="user@example.com",
        ...     password="securepassword123",
        ...     display_name="John Doe"
        ... )
    """

    def __init__(
        self,
        settings: GCPSettings | None = None,
        credentials_path: str | None = None,
    ) -> None:
        """
        Initialize the Firebase Auth controller.

        Args:
            settings: GCP configuration settings. If not provided, loads from environment/.env file.
            credentials_path: Optional path to service account credentials.
                If not provided, uses settings.credentials_path or default credentials.

        Raises:
            FirebaseError: If Firebase initialization fails
        """
        self.settings = settings or get_settings()

        try:
            # Check if Firebase is already initialized
            try:
                firebase_admin.get_app()
            except ValueError:
                # Firebase not initialized yet
                cred_path = credentials_path or (
                    str(self.settings.credentials_path) if self.settings.credentials_path else None
                )

                if cred_path:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(
                        cred,
                        {"projectId": self.settings.project_id},
                    )
                else:
                    # Use application default credentials
                    firebase_admin.initialize_app(
                        options={"projectId": self.settings.project_id}
                    )

        except Exception as e:
            raise FirebaseError(
                f"Failed to initialize Firebase: {e}",
                details={"error": str(e)},
            )

    def create_user(
        self,
        email: str | None = None,
        password: str | None = None,
        phone_number: str | None = None,
        display_name: str | None = None,
        photo_url: str | None = None,
        email_verified: bool = False,
        disabled: bool = False,
        uid: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new Firebase user.

        Args:
            email: User's email address
            password: User's password (min 6 characters)
            phone_number: User's phone number (E.164 format)
            display_name: User's display name
            photo_url: User's photo URL
            email_verified: Whether email is verified
            disabled: Whether user account is disabled
            uid: Optional custom UID

        Returns:
            Dictionary with user information

        Raises:
            ValidationError: If input is invalid
            FirebaseError: If user creation fails
        """
        if not email and not phone_number:
            raise ValidationError("Either email or phone_number must be provided")

        try:
            user = auth.create_user(
                uid=uid,
                email=email,
                email_verified=email_verified,
                phone_number=phone_number,
                password=password,
                display_name=display_name,
                photo_url=photo_url,
                disabled=disabled,
            )

            return self._user_record_to_dict(user)

        except ValidationError:
            raise
        except Exception as e:
            raise FirebaseError(
                f"Failed to create user: {e}",
                details={"error": str(e)},
            )

    def get_user(self, uid: str) -> dict[str, Any]:
        """
        Get user by UID.

        Args:
            uid: User ID

        Returns:
            Dictionary with user information

        Raises:
            ResourceNotFoundError: If user not found
            FirebaseError: If retrieval fails
        """
        try:
            user = auth.get_user(uid)
            return self._user_record_to_dict(user)

        except FirebaseUserNotFoundError:
            raise ResourceNotFoundError(
                f"User with UID '{uid}' not found",
                details={"uid": uid},
            )
        except Exception as e:
            raise FirebaseError(
                f"Failed to get user '{uid}': {e}",
                details={"uid": uid, "error": str(e)},
            )

    def get_user_by_email(self, email: str) -> dict[str, Any]:
        """
        Get user by email address.

        Args:
            email: User's email address

        Returns:
            Dictionary with user information

        Raises:
            ResourceNotFoundError: If user not found
            FirebaseError: If retrieval fails
        """
        try:
            user = auth.get_user_by_email(email)
            return self._user_record_to_dict(user)

        except FirebaseUserNotFoundError:
            raise ResourceNotFoundError(
                f"User with email '{email}' not found",
                details={"email": email},
            )
        except Exception as e:
            raise FirebaseError(
                f"Failed to get user by email '{email}': {e}",
                details={"email": email, "error": str(e)},
            )

    def get_user_by_phone_number(self, phone_number: str) -> dict[str, Any]:
        """
        Get user by phone number.

        Args:
            phone_number: User's phone number (E.164 format)

        Returns:
            Dictionary with user information

        Raises:
            ResourceNotFoundError: If user not found
            FirebaseError: If retrieval fails
        """
        try:
            user = auth.get_user_by_phone_number(phone_number)
            return self._user_record_to_dict(user)

        except FirebaseUserNotFoundError:
            raise ResourceNotFoundError(
                f"User with phone number '{phone_number}' not found",
                details={"phone_number": phone_number},
            )
        except Exception as e:
            raise FirebaseError(
                f"Failed to get user by phone number '{phone_number}': {e}",
                details={"phone_number": phone_number, "error": str(e)},
            )

    def update_user(
        self,
        uid: str,
        email: str | None = None,
        password: str | None = None,
        phone_number: str | None = None,
        display_name: str | None = None,
        photo_url: str | None = None,
        email_verified: bool | None = None,
        disabled: bool | None = None,
    ) -> dict[str, Any]:
        """
        Update user information.

        Args:
            uid: User ID
            email: New email address
            password: New password
            phone_number: New phone number
            display_name: New display name
            photo_url: New photo URL
            email_verified: Email verification status
            disabled: Account disabled status

        Returns:
            Updated user information

        Raises:
            ResourceNotFoundError: If user not found
            FirebaseError: If update fails
        """
        try:
            update_kwargs: dict[str, Any] = {}

            if email is not None:
                update_kwargs["email"] = email
            if password is not None:
                update_kwargs["password"] = password
            if phone_number is not None:
                update_kwargs["phone_number"] = phone_number
            if display_name is not None:
                update_kwargs["display_name"] = display_name
            if photo_url is not None:
                update_kwargs["photo_url"] = photo_url
            if email_verified is not None:
                update_kwargs["email_verified"] = email_verified
            if disabled is not None:
                update_kwargs["disabled"] = disabled

            user = auth.update_user(uid, **update_kwargs)
            return self._user_record_to_dict(user)

        except FirebaseUserNotFoundError:
            raise ResourceNotFoundError(
                f"User with UID '{uid}' not found",
                details={"uid": uid},
            )
        except Exception as e:
            raise FirebaseError(
                f"Failed to update user '{uid}': {e}",
                details={"uid": uid, "error": str(e)},
            )

    def delete_user(self, uid: str) -> None:
        """
        Delete a user.

        Args:
            uid: User ID to delete

        Raises:
            ResourceNotFoundError: If user not found
            FirebaseError: If deletion fails
        """
        try:
            auth.delete_user(uid)

        except FirebaseUserNotFoundError:
            raise ResourceNotFoundError(
                f"User with UID '{uid}' not found",
                details={"uid": uid},
            )
        except Exception as e:
            raise FirebaseError(
                f"Failed to delete user '{uid}': {e}",
                details={"uid": uid, "error": str(e)},
            )

    def delete_users(self, uids: list[str]) -> dict[str, Any]:
        """
        Delete multiple users.

        Args:
            uids: List of user IDs to delete

        Returns:
            Dictionary with success_count and errors list

        Raises:
            ValidationError: If uids list is empty
            FirebaseError: If operation fails
        """
        if not uids:
            raise ValidationError("UIDs list cannot be empty")

        try:
            result = auth.delete_users(uids)

            return {
                "success_count": result.success_count,
                "failure_count": result.failure_count,
                "errors": [
                    {"index": err.index, "reason": err.reason}
                    for err in result.errors
                ],
            }

        except ValidationError:
            raise
        except Exception as e:
            raise FirebaseError(
                f"Failed to delete users: {e}",
                details={"error": str(e)},
            )

    def list_users(
        self,
        max_results: int = 1000,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """
        List all users.

        Args:
            max_results: Maximum number of users to return (max 1000)
            page_token: Page token for pagination

        Returns:
            Dictionary with users list and next_page_token

        Raises:
            FirebaseError: If listing fails
        """
        try:
            page = auth.list_users(page_token=page_token, max_results=max_results)

            users = [self._user_record_to_dict(user) for user in page.users]

            return {
                "users": users,
                "next_page_token": page.next_page_token if page.has_next_page else None,
            }

        except Exception as e:
            raise FirebaseError(
                f"Failed to list users: {e}",
                details={"error": str(e)},
            )

    def set_custom_user_claims(
        self,
        uid: str,
        custom_claims: dict[str, Any],
    ) -> None:
        """
        Set custom claims for a user.

        Args:
            uid: User ID
            custom_claims: Dictionary of custom claims (e.g., {"admin": True})

        Raises:
            ResourceNotFoundError: If user not found
            ValidationError: If claims are invalid
            FirebaseError: If operation fails
        """
        if custom_claims is None:
            raise ValidationError("Custom claims cannot be None")

        try:
            auth.set_custom_user_claims(uid, custom_claims)

        except FirebaseUserNotFoundError:
            raise ResourceNotFoundError(
                f"User with UID '{uid}' not found",
                details={"uid": uid},
            )
        except ValidationError:
            raise
        except Exception as e:
            raise FirebaseError(
                f"Failed to set custom claims for user '{uid}': {e}",
                details={"uid": uid, "error": str(e)},
            )

    def verify_id_token(
        self,
        id_token: str,
        check_revoked: bool = False,
    ) -> dict[str, Any]:
        """
        Verify a Firebase ID token.

        Args:
            id_token: Firebase ID token to verify
            check_revoked: Whether to check if token has been revoked

        Returns:
            Decoded token claims

        Raises:
            AuthenticationError: If token is invalid or revoked
            FirebaseError: If verification fails
        """
        try:
            decoded_token = auth.verify_id_token(
                id_token,
                check_revoked=check_revoked,
            )
            return decoded_token

        except auth.InvalidIdTokenError as e:
            raise AuthenticationError(
                f"Invalid ID token: {e}",
                details={"error": str(e)},
            )
        except auth.ExpiredIdTokenError as e:
            raise AuthenticationError(
                f"Expired ID token: {e}",
                details={"error": str(e)},
            )
        except auth.RevokedIdTokenError as e:
            raise AuthenticationError(
                f"Revoked ID token: {e}",
                details={"error": str(e)},
            )
        except Exception as e:
            raise FirebaseError(
                f"Failed to verify ID token: {e}",
                details={"error": str(e)},
            )

    def revoke_refresh_tokens(self, uid: str) -> None:
        """
        Revoke all refresh tokens for a user.

        Args:
            uid: User ID

        Raises:
            ResourceNotFoundError: If user not found
            FirebaseError: If operation fails
        """
        try:
            auth.revoke_refresh_tokens(uid)

        except FirebaseUserNotFoundError:
            raise ResourceNotFoundError(
                f"User with UID '{uid}' not found",
                details={"uid": uid},
            )
        except Exception as e:
            raise FirebaseError(
                f"Failed to revoke refresh tokens for user '{uid}': {e}",
                details={"uid": uid, "error": str(e)},
            )

    def create_custom_token(
        self,
        uid: str,
        developer_claims: dict[str, Any] | None = None,
    ) -> str:
        """
        Create a custom authentication token.

        Args:
            uid: User ID
            developer_claims: Optional custom claims to include in the token

        Returns:
            Custom token string

        Raises:
            FirebaseError: If token creation fails
        """
        try:
            token = auth.create_custom_token(
                uid,
                developer_claims=developer_claims,
            )
            return token.decode("utf-8") if isinstance(token, bytes) else token

        except Exception as e:
            raise FirebaseError(
                f"Failed to create custom token for user '{uid}': {e}",
                details={"uid": uid, "error": str(e)},
            )

    def generate_email_verification_link(
        self,
        email: str,
        action_code_settings: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate an email verification link.

        Args:
            email: User's email address
            action_code_settings: Optional action code settings

        Returns:
            Email verification link

        Raises:
            FirebaseError: If link generation fails
        """
        try:
            link = auth.generate_email_verification_link(
                email,
                action_code_settings=action_code_settings,
            )
            return link

        except Exception as e:
            raise FirebaseError(
                f"Failed to generate email verification link for '{email}': {e}",
                details={"email": email, "error": str(e)},
            )

    def generate_password_reset_link(
        self,
        email: str,
        action_code_settings: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a password reset link.

        Args:
            email: User's email address
            action_code_settings: Optional action code settings

        Returns:
            Password reset link

        Raises:
            FirebaseError: If link generation fails
        """
        try:
            link = auth.generate_password_reset_link(
                email,
                action_code_settings=action_code_settings,
            )
            return link

        except Exception as e:
            raise FirebaseError(
                f"Failed to generate password reset link for '{email}': {e}",
                details={"email": email, "error": str(e)},
            )

    def _user_record_to_dict(self, user: UserRecord) -> dict[str, Any]:
        """Convert UserRecord to dictionary."""
        return {
            "uid": user.uid,
            "email": user.email,
            "email_verified": user.email_verified,
            "phone_number": user.phone_number,
            "display_name": user.display_name,
            "photo_url": user.photo_url,
            "disabled": user.disabled,
            "custom_claims": user.custom_claims or {},
            "provider_data": [
                {
                    "uid": provider.uid,
                    "email": provider.email,
                    "phone_number": provider.phone_number,
                    "display_name": provider.display_name,
                    "photo_url": provider.photo_url,
                    "provider_id": provider.provider_id,
                }
                for provider in user.provider_data
            ],
            "tokens_valid_after_timestamp": user.tokens_valid_after_timestamp,
            "user_metadata": {
                "creation_timestamp": user.user_metadata.creation_timestamp,
                "last_sign_in_timestamp": user.user_metadata.last_sign_in_timestamp,
                "last_refresh_timestamp": user.user_metadata.last_refresh_timestamp,
            }
            if user.user_metadata
            else None,
        }
