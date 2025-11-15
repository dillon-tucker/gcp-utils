"""
IAM (Identity and Access Management) controller for managing service accounts and policies.

This module provides a controller for GCP IAM operations including:
- Creating and managing service accounts
- Creating and managing service account keys
- Managing IAM policies and role bindings
- Listing and querying service accounts
"""

from typing import Optional

from google.api_core import exceptions as google_exceptions
from google.auth.credentials import Credentials
from google.cloud import iam_admin_v1
from google.cloud.iam_admin_v1.types import (
    CreateServiceAccountKeyRequest,
    CreateServiceAccountRequest,
    DeleteServiceAccountKeyRequest,
    DeleteServiceAccountRequest,
    GetServiceAccountRequest,
    ListServiceAccountKeysRequest,
    ListServiceAccountsRequest,
    PatchServiceAccountRequest,
    ServiceAccount as GCPServiceAccount,
)
from google.iam.v1 import iam_policy_pb2, policy_pb2

from ..config import GCPSettings, get_settings
from ..exceptions import IAMError, ResourceNotFoundError
from ..models.iam import (
    IAMBinding,
    IAMPolicy,
    ServiceAccount,
    ServiceAccountInfo,
    ServiceAccountKey,
    ServiceAccountKeyAlgorithm,
)


class IAMController:
    """
    Controller for Google Cloud IAM operations.

    This controller provides methods for managing service accounts, keys,
    and IAM policies in Google Cloud Platform.

    Attributes:
        settings: GCP configuration settings
        client: IAM Admin API client (lazy-initialized)
    """

    def __init__(
        self,
        settings: Optional[GCPSettings] = None,
        credentials: Optional[Credentials] = None,
    ) -> None:
        """
        Initialize the IAM controller.

        Args:
            settings: GCP settings (auto-loads from .env if not provided)
            credentials: Optional custom credentials
        """
        self.settings = settings or get_settings()
        self._credentials = credentials
        self._client: Optional[iam_admin_v1.IAMClient] = None

    def _get_client(self) -> iam_admin_v1.IAMClient:
        """Lazy initialization of IAM client."""
        if self._client is None:
            self._client = iam_admin_v1.IAMClient(credentials=self._credentials)
        return self._client

    def create_service_account(
        self,
        account_id: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ServiceAccount:
        """
        Create a new service account.

        Args:
            account_id: Unique ID for the service account (e.g., 'my-service-account')
            display_name: Human-readable display name
            description: Optional description

        Returns:
            ServiceAccount object with created account details

        Raises:
            IAMError: If service account creation fails

        Example:
            ```python
            iam = IAMController()
            account = iam.create_service_account(
                account_id="my-app-service",
                display_name="My Application Service Account",
                description="Service account for my application"
            )
            print(f"Created: {account.email}")
            ```
        """
        try:
            client = self._get_client()
            project_name = f"projects/{self.settings.project_id}"

            service_account = GCPServiceAccount(
                display_name=display_name or account_id,
                description=description,
            )

            request = CreateServiceAccountRequest(
                name=project_name,
                account_id=account_id,
                service_account=service_account,
            )

            response = client.create_service_account(request=request)

            return ServiceAccount(
                name=response.name,
                project_id=response.project_id,
                unique_id=response.unique_id,
                email=response.email,
                display_name=response.display_name,
                description=response.description,
                oauth2_client_id=response.oauth2_client_id,
                disabled=response.disabled,
            )

        except google_exceptions.GoogleAPIError as e:
            raise IAMError(
                message=f"Failed to create service account '{account_id}': {str(e)}",
                details={"account_id": account_id, "error": str(e)},
            ) from e

    def get_service_account(self, email: str) -> ServiceAccount:
        """
        Get service account details by email.

        Args:
            email: Service account email address

        Returns:
            ServiceAccount object

        Raises:
            ResourceNotFoundError: If service account not found
            IAMError: If retrieval fails

        Example:
            ```python
            iam = IAMController()
            account = iam.get_service_account("my-sa@project.iam.gserviceaccount.com")
            print(f"Display name: {account.display_name}")
            ```
        """
        try:
            client = self._get_client()
            name = f"projects/{self.settings.project_id}/serviceAccounts/{email}"

            request = GetServiceAccountRequest(name=name)
            response = client.get_service_account(request=request)

            return ServiceAccount(
                name=response.name,
                project_id=response.project_id,
                unique_id=response.unique_id,
                email=response.email,
                display_name=response.display_name,
                description=response.description,
                oauth2_client_id=response.oauth2_client_id,
                disabled=response.disabled,
            )

        except google_exceptions.NotFound as e:
            raise ResourceNotFoundError(
                message=f"Service account '{email}' not found",
                details={"email": email},
            ) from e
        except google_exceptions.GoogleAPIError as e:
            raise IAMError(
                message=f"Failed to get service account '{email}': {str(e)}",
                details={"email": email, "error": str(e)},
            ) from e

    def list_service_accounts(self, max_results: int = 100) -> list[ServiceAccount]:
        """
        List all service accounts in the project.

        Args:
            max_results: Maximum number of accounts to return

        Returns:
            List of ServiceAccount objects

        Raises:
            IAMError: If listing fails

        Example:
            ```python
            iam = IAMController()
            accounts = iam.list_service_accounts()
            for account in accounts:
                print(f"{account.email} - {account.display_name}")
            ```
        """
        try:
            client = self._get_client()
            project_name = f"projects/{self.settings.project_id}"

            request = ListServiceAccountsRequest(
                name=project_name,
                page_size=max_results,
            )

            accounts = []
            for response in client.list_service_accounts(request=request):
                accounts.append(
                    ServiceAccount(
                        name=response.name,
                        project_id=response.project_id,
                        unique_id=response.unique_id,
                        email=response.email,
                        display_name=response.display_name,
                        description=response.description,
                        oauth2_client_id=response.oauth2_client_id,
                        disabled=response.disabled,
                    )
                )

            return accounts

        except google_exceptions.GoogleAPIError as e:
            raise IAMError(
                message=f"Failed to list service accounts: {str(e)}",
                details={"error": str(e)},
            ) from e

    def update_service_account(
        self,
        email: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ServiceAccount:
        """
        Update a service account's display name or description.

        Args:
            email: Service account email address
            display_name: New display name (optional)
            description: New description (optional)

        Returns:
            Updated ServiceAccount object

        Raises:
            IAMError: If update fails

        Example:
            ```python
            iam = IAMController()
            account = iam.update_service_account(
                email="my-sa@project.iam.gserviceaccount.com",
                display_name="Updated Display Name"
            )
            ```
        """
        try:
            from google.protobuf import field_mask_pb2

            client = self._get_client()
            name = f"projects/{self.settings.project_id}/serviceAccounts/{email}"

            service_account = GCPServiceAccount(name=name)
            update_mask_paths = []

            if display_name is not None:
                service_account.display_name = display_name
                update_mask_paths.append("display_name")

            if description is not None:
                service_account.description = description
                update_mask_paths.append("description")

            update_mask = field_mask_pb2.FieldMask(paths=update_mask_paths)
            request = PatchServiceAccountRequest(
                service_account=service_account, update_mask=update_mask
            )

            response = client.patch_service_account(request=request)

            return ServiceAccount(
                name=response.name,
                project_id=response.project_id,
                unique_id=response.unique_id,
                email=response.email,
                display_name=response.display_name,
                description=response.description,
                oauth2_client_id=response.oauth2_client_id,
                disabled=response.disabled,
            )

        except google_exceptions.GoogleAPIError as e:
            raise IAMError(
                message=f"Failed to update service account '{email}': {str(e)}",
                details={"email": email, "error": str(e)},
            ) from e

    def delete_service_account(self, email: str) -> None:
        """
        Delete a service account.

        Args:
            email: Service account email address

        Raises:
            IAMError: If deletion fails

        Example:
            ```python
            iam = IAMController()
            iam.delete_service_account("my-sa@project.iam.gserviceaccount.com")
            print("Service account deleted")
            ```
        """
        try:
            client = self._get_client()
            name = f"projects/{self.settings.project_id}/serviceAccounts/{email}"

            request = DeleteServiceAccountRequest(name=name)
            client.delete_service_account(request=request)

        except google_exceptions.GoogleAPIError as e:
            raise IAMError(
                message=f"Failed to delete service account '{email}': {str(e)}",
                details={"email": email, "error": str(e)},
            ) from e

    def create_service_account_key(
        self,
        email: str,
        key_algorithm: ServiceAccountKeyAlgorithm = ServiceAccountKeyAlgorithm.KEY_ALG_RSA_2048,
    ) -> ServiceAccountKey:
        """
        Create a new key for a service account.

        Args:
            email: Service account email address
            key_algorithm: Key algorithm (default: RSA_2048)

        Returns:
            ServiceAccountKey with private key data (base64 encoded JSON)

        Raises:
            IAMError: If key creation fails

        Example:
            ```python
            iam = IAMController()
            key = iam.create_service_account_key("my-sa@project.iam.gserviceaccount.com")

            # Save the private key data to a file
            import base64
            import json
            key_json = base64.b64decode(key.private_key_data)
            with open("key.json", "wb") as f:
                f.write(key_json)
            ```
        """
        try:
            client = self._get_client()
            name = f"projects/{self.settings.project_id}/serviceAccounts/{email}"

            request = CreateServiceAccountKeyRequest(
                name=name,
                private_key_type=iam_admin_v1.ServiceAccountPrivateKeyType.TYPE_GOOGLE_CREDENTIALS_FILE,
                key_algorithm=iam_admin_v1.ServiceAccountKeyAlgorithm[
                    key_algorithm.value
                ],
            )

            response = client.create_service_account_key(request=request)

            return ServiceAccountKey(
                name=response.name,
                private_key_type=str(response.private_key_type),
                key_algorithm=ServiceAccountKeyAlgorithm(
                    response.key_algorithm.name
                    if hasattr(response.key_algorithm, "name")
                    else "KEY_ALG_RSA_2048"
                ),
                private_key_data=response.private_key_data.decode("utf-8")
                if response.private_key_data
                else None,
                valid_after_time=response.valid_after_time,
                valid_before_time=response.valid_before_time,
            )

        except google_exceptions.GoogleAPIError as e:
            raise IAMError(
                message=f"Failed to create key for service account '{email}': {str(e)}",
                details={"email": email, "error": str(e)},
            ) from e

    def list_service_account_keys(self, email: str) -> list[ServiceAccountKey]:
        """
        List all keys for a service account.

        Args:
            email: Service account email address

        Returns:
            List of ServiceAccountKey objects (without private key data)

        Raises:
            IAMError: If listing fails

        Example:
            ```python
            iam = IAMController()
            keys = iam.list_service_account_keys("my-sa@project.iam.gserviceaccount.com")
            for key in keys:
                print(f"Key: {key.name}, Algorithm: {key.key_algorithm}")
            ```
        """
        try:
            client = self._get_client()
            name = f"projects/{self.settings.project_id}/serviceAccounts/{email}"

            request = ListServiceAccountKeysRequest(name=name)
            response = client.list_service_account_keys(request=request)

            keys = []
            for key in response.keys:
                keys.append(
                    ServiceAccountKey(
                        name=key.name,
                        key_algorithm=ServiceAccountKeyAlgorithm(
                            key.key_algorithm.name
                            if hasattr(key.key_algorithm, "name")
                            else "KEY_ALG_RSA_2048"
                        ),
                        valid_after_time=key.valid_after_time,
                        valid_before_time=key.valid_before_time,
                        key_type=key.key_type.name if hasattr(key.key_type, "name") else None,
                    )
                )

            return keys

        except google_exceptions.GoogleAPIError as e:
            raise IAMError(
                message=f"Failed to list keys for service account '{email}': {str(e)}",
                details={"email": email, "error": str(e)},
            ) from e

    def delete_service_account_key(self, key_name: str) -> None:
        """
        Delete a service account key.

        Args:
            key_name: Full resource name of the key (e.g., from ServiceAccountKey.name)

        Raises:
            IAMError: If deletion fails

        Example:
            ```python
            iam = IAMController()
            keys = iam.list_service_account_keys("my-sa@project.iam.gserviceaccount.com")
            if keys:
                iam.delete_service_account_key(keys[0].name)
                print("Key deleted")
            ```
        """
        try:
            client = self._get_client()
            request = DeleteServiceAccountKeyRequest(name=key_name)
            client.delete_service_account_key(request=request)

        except google_exceptions.GoogleAPIError as e:
            raise IAMError(
                message=f"Failed to delete key '{key_name}': {str(e)}",
                details={"key_name": key_name, "error": str(e)},
            ) from e

    def get_iam_policy(self, resource: str) -> IAMPolicy:
        """
        Get the IAM policy for a resource.

        Args:
            resource: Full resource name (e.g., 'projects/my-project')

        Returns:
            IAMPolicy object

        Raises:
            IAMError: If retrieval fails

        Example:
            ```python
            iam = IAMController()
            policy = iam.get_iam_policy(f"projects/{iam.settings.project_id}")
            for binding in policy.bindings:
                print(f"Role: {binding.role}, Members: {binding.members}")
            ```
        """
        try:
            client = self._get_client()
            request = iam_policy_pb2.GetIamPolicyRequest(resource=resource)
            response = client.get_iam_policy(request=request)

            bindings = []
            for binding in response.bindings:
                bindings.append(
                    IAMBinding(
                        role=binding.role,
                        members=list(binding.members),
                        condition=None,  # TODO: Parse condition if exists
                    )
                )

            return IAMPolicy(
                version=response.version,
                bindings=bindings,
                etag=response.etag.decode("utf-8") if response.etag else None,
            )

        except google_exceptions.GoogleAPIError as e:
            raise IAMError(
                message=f"Failed to get IAM policy for '{resource}': {str(e)}",
                details={"resource": resource, "error": str(e)},
            ) from e

    def set_iam_policy(self, resource: str, policy: IAMPolicy) -> IAMPolicy:
        """
        Set the IAM policy for a resource.

        Args:
            resource: Full resource name
            policy: IAMPolicy to set

        Returns:
            Updated IAMPolicy

        Raises:
            IAMError: If setting policy fails

        Example:
            ```python
            iam = IAMController()

            # Get current policy
            policy = iam.get_iam_policy(f"projects/{iam.settings.project_id}")

            # Add a new binding
            from gcp_utils.models.iam import IAMBinding
            new_binding = IAMBinding(
                role="roles/viewer",
                members=["serviceAccount:my-sa@project.iam.gserviceaccount.com"]
            )
            policy.bindings.append(new_binding)

            # Update policy
            updated = iam.set_iam_policy(f"projects/{iam.settings.project_id}", policy)
            ```
        """
        try:
            client = self._get_client()

            # Build policy proto
            bindings = []
            for binding in policy.bindings:
                proto_binding = policy_pb2.Binding(
                    role=binding.role,
                    members=binding.members,
                )
                bindings.append(proto_binding)

            policy_proto = policy_pb2.Policy(
                version=policy.version,
                bindings=bindings,
                etag=policy.etag.encode("utf-8") if policy.etag else b"",
            )

            request = iam_policy_pb2.SetIamPolicyRequest(
                resource=resource, policy=policy_proto
            )
            response = client.set_iam_policy(request=request)

            result_bindings = []
            for binding in response.bindings:
                result_bindings.append(
                    IAMBinding(
                        role=binding.role,
                        members=list(binding.members),
                    )
                )

            return IAMPolicy(
                version=response.version,
                bindings=result_bindings,
                etag=response.etag.decode("utf-8") if response.etag else None,
            )

        except google_exceptions.GoogleAPIError as e:
            raise IAMError(
                message=f"Failed to set IAM policy for '{resource}': {str(e)}",
                details={"resource": resource, "error": str(e)},
            ) from e

    def get_service_account_info(self, email: str) -> ServiceAccountInfo:
        """
        Get detailed service account information including key counts.

        Args:
            email: Service account email address

        Returns:
            ServiceAccountInfo with account details and key statistics

        Raises:
            IAMError: If retrieval fails

        Example:
            ```python
            iam = IAMController()
            info = iam.get_service_account_info("my-sa@project.iam.gserviceaccount.com")
            print(f"Account: {info.account.email}")
            print(f"Total keys: {info.keys_count}")
            print(f"User-managed keys: {info.user_managed_keys_count}")
            ```
        """
        account = self.get_service_account(email)
        keys = self.list_service_account_keys(email)

        user_managed = sum(1 for k in keys if k.key_type == "USER_MANAGED")
        system_managed = sum(1 for k in keys if k.key_type == "SYSTEM_MANAGED")

        return ServiceAccountInfo(
            account=account,
            keys_count=len(keys),
            user_managed_keys_count=user_managed,
            system_managed_keys_count=system_managed,
        )
