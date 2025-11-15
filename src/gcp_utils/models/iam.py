"""Data models for IAM (Identity and Access Management) operations."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ServiceAccountKeyAlgorithm(str, Enum):
    """Service account key algorithm types."""

    KEY_ALG_UNSPECIFIED = "KEY_ALG_UNSPECIFIED"
    KEY_ALG_RSA_1024 = "KEY_ALG_RSA_1024"
    KEY_ALG_RSA_2048 = "KEY_ALG_RSA_2048"


class ServiceAccountKeyType(str, Enum):
    """Service account key types."""

    TYPE_UNSPECIFIED = "TYPE_UNSPECIFIED"
    USER_MANAGED = "USER_MANAGED"
    SYSTEM_MANAGED = "SYSTEM_MANAGED"


class ServiceAccountKey(BaseModel):
    """
    Represents a service account key.

    Attributes:
        name: Resource name of the key
        private_key_type: Output format for the key
        key_algorithm: Algorithm used for the key
        private_key_data: Private key data (base64 encoded)
        public_key_data: Public key data
        valid_after_time: Key valid after this time
        valid_before_time: Key valid before this time
        key_origin: Key origin (GOOGLE_PROVIDED or USER_PROVIDED)
        key_type: Key type (USER_MANAGED or SYSTEM_MANAGED)
    """

    name: str = Field(..., description="Resource name of the key")
    private_key_type: Optional[str] = Field(
        default=None, description="Private key type"
    )
    key_algorithm: Optional[ServiceAccountKeyAlgorithm] = Field(
        default=None, description="Key algorithm"
    )
    private_key_data: Optional[str] = Field(
        default=None, description="Private key data (base64 encoded)"
    )
    public_key_data: Optional[str] = Field(default=None, description="Public key data")
    valid_after_time: Optional[datetime] = Field(
        default=None, description="Key valid after time"
    )
    valid_before_time: Optional[datetime] = Field(
        default=None, description="Key valid before time"
    )
    key_origin: Optional[str] = Field(default=None, description="Key origin")
    key_type: Optional[ServiceAccountKeyType] = Field(
        default=None, description="Key type"
    )

    model_config = ConfigDict(use_enum_values=True)

    @field_serializer("valid_after_time", "valid_before_time")
    def serialize_dt(self, dt: Optional[datetime], _info: Any) -> Optional[str]:
        return dt.isoformat() if dt else None


class ServiceAccount(BaseModel):
    """
    Represents a GCP service account.

    Attributes:
        name: Resource name (format: projects/{project}/serviceAccounts/{email})
        project_id: Project ID
        unique_id: Unique numeric ID
        email: Email address of the service account
        display_name: Display name
        description: Description
        oauth2_client_id: OAuth2 client ID
        disabled: Whether the service account is disabled
    """

    name: str = Field(..., description="Resource name of the service account")
    project_id: str = Field(..., description="Project ID")
    unique_id: str = Field(..., description="Unique numeric ID")
    email: str = Field(..., description="Service account email address")
    display_name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Description")
    oauth2_client_id: Optional[str] = Field(None, description="OAuth2 client ID")
    disabled: bool = Field(default=False, description="Whether disabled")


class IAMBinding(BaseModel):
    """
    Represents an IAM policy binding.

    Attributes:
        role: Role identifier (e.g., 'roles/storage.admin')
        members: List of members (e.g., 'user:email@example.com', 'serviceAccount:sa@project.iam.gserviceaccount.com')
        condition: Optional condition for conditional role bindings
    """

    role: str = Field(..., description="IAM role")
    members: list[str] = Field(
        default_factory=list, description="List of member identifiers"
    )
    condition: Optional[dict[str, Any]] = Field(
        default=None, description="Optional IAM condition"
    )


class IAMPolicy(BaseModel):
    """
    Represents an IAM policy.

    Attributes:
        version: Policy version (should be 1 or 3 for conditional policies)
        bindings: List of role bindings
        etag: ETag for concurrency control
    """

    version: int = Field(default=1, description="Policy version")
    bindings: list[IAMBinding] = Field(
        default_factory=list, description="Role bindings"
    )
    etag: Optional[str] = Field(None, description="ETag for concurrency control")


class ServiceAccountInfo(BaseModel):
    """
    Extended service account information with statistics.

    Attributes:
        account: Service account details
        keys_count: Number of keys associated with the account
        user_managed_keys_count: Number of user-managed keys
        system_managed_keys_count: Number of system-managed keys
    """

    account: ServiceAccount = Field(..., description="Service account details")
    keys_count: int = Field(default=0, description="Total number of keys")
    user_managed_keys_count: int = Field(
        default=0, description="Number of user-managed keys"
    )
    system_managed_keys_count: int = Field(
        default=0, description="Number of system-managed keys"
    )
