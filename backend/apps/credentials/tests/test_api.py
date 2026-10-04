from typing import cast

from cryptography.fernet import Fernet
from django.contrib.auth.models import Permission
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.credentials.models import CredentialType, StoredCredential
from apps.credentials.ninja.schemas import (
    CredentialCreateIn,
    CredentialDetailOut,
    CredentialLegacyMigrationOut,
    CredentialPageOut,
    CredentialResourceLinkIn,
    CredentialSecretRevealIn,
    CredentialSecretsOut,
    CredentialSecretValueOut,
    CredentialUpdateIn,
)
from apps.credentials.ninja.views import (
    archive_credential,
    copy_credential_field,
    create_credential,
    download_credential_field,
    get_credential,
    list_credentials,
    migrate_credential_legacy_secrets,
    reveal_credential,
    update_credential,
)
from apps.credentials.secrets import load_credential_secrets_for_service, store_credential_secrets
from apps.infrastructure.models import InfrastructureResource
from authentication.models import User


class CredentialVaultApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.encryption_key = Fernet.generate_key().decode("ascii")
        self.client_a = Client.objects.create(
            name="Client A",
            company="Client A Ltd",
            email="client-a@example.test",
        )
        self.client_b = Client.objects.create(
            name="Client B",
            company="Client B Ltd",
            email="client-b@example.test",
        )
        self.internal_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        self.client_a_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_a,
            name="Client A website",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
        )
        self.client_b_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_b,
            name="Client B website",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
        )
        self.password_type = CredentialType.objects.get(slug="username-password")
        self.internal = StoredCredential.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB account",
            credential_type=self.password_type,
        )
        self.credential_a = StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_a,
            name="Client A login",
            credential_type=self.password_type,
        )
        self.credential_b = StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_b,
            name="Client B login",
            credential_type=self.password_type,
        )
        self.archived = StoredCredential.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Old account",
            credential_type=self.password_type,
            status=StoredCredential.Status.ARCHIVED,
        )

    def _user(self, email: str, permissions: tuple[str, ...]) -> User:
        user = User.objects.create_user(
            email=email,
            password="test-password",
            first_name="Credential",
            last_name="User",
            is_staff=True,
        )
        for codename in permissions:
            user.user_permissions.add(
                Permission.objects.get(
                    content_type__app_label="credentials",
                    codename=codename,
                )
            )
        return User.objects.get(pk=user.pk)

    def _request(self, user: User | None, method: str = "get") -> HttpRequest:
        request = getattr(self.factory, method)("/api/admin/credentials")
        request.user = user if user is not None else cast(User, _AnonymousUser())
        return request

    def test_unauthenticated_list_is_rejected(self) -> None:
        result = list_credentials(self._request(None))

        self.assertIsInstance(result, tuple)
        status, payload = cast(tuple[int, dict[str, object]], result)
        self.assertEqual(status, 401)
        self.assertEqual(payload["code"], "unauthenticated")

    def test_selected_client_scope_includes_internal_and_selected_client_only(
        self,
    ) -> None:
        user = self._user("scope@example.test", ("view_storedcredential",))
        profile = StaffAccessProfile.objects.create(user=user)
        ClientAccessGrant.objects.create(profile=profile, client=self.client_a)

        result = cast(CredentialPageOut, list_credentials(self._request(user)))

        self.assertSetEqual(
            {item.id for item in result.items},
            {self.internal.id, self.credential_a.id},
        )
        self.assertNotIn(self.credential_b.id, {item.id for item in result.items})
        self.assertNotIn(self.archived.id, {item.id for item in result.items})

    def test_archived_credentials_require_explicit_filter(self) -> None:
        user = self._user("history@example.test", ("view_storedcredential",))

        current = cast(CredentialPageOut, list_credentials(self._request(user)))
        history = cast(
            CredentialPageOut,
            list_credentials(self._request(user), status="archived"),
        )

        self.assertNotIn(self.archived.id, {item.id for item in current.items})
        self.assertEqual([item.id for item in history.items], [self.archived.id])

    def test_detail_does_not_return_secret_values(self) -> None:
        user = self._user("detail@example.test", ("view_storedcredential",))
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.encryption_key]):
            store_credential_secrets(
                self.internal,
                {"password": "never-in-metadata", "notes": "also-encrypted"},
            )
            result = cast(
                CredentialDetailOut,
                get_credential(self._request(user), self.internal.id),
            )

        self.assertEqual(result.secret_field_keys, ["notes", "password"])
        self.assertNotIn("never-in-metadata", str(result.model_dump()))
        self.assertNotIn("also-encrypted", str(result.model_dump()))

    def test_detail_describes_untyped_encrypted_legacy_fields(self) -> None:
        user = self._user("legacy-detail@example.test", ("view_storedcredential",))
        legacy_type = CredentialType.objects.create(name="Legacy API credential")
        self.internal.credential_type = legacy_type
        self.internal.save(update_fields=["credential_type", "updated_at"])

        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.encryption_key]):
            store_credential_secrets(self.internal, {"api_key": "encrypted-legacy-key"})
            result = cast(
                CredentialDetailOut,
                get_credential(self._request(user), self.internal.id),
            )

        api_key_field = next(field for field in result.fields if field.key == "api_key")
        self.assertEqual(api_key_field.label, "API key")
        self.assertEqual(api_key_field.storage, "secret")
        self.assertEqual(api_key_field.kind, "password")
        self.assertNotIn("encrypted-legacy-key", str(result.model_dump()))

    def test_create_encrypts_secret_values_and_links_resources(self) -> None:
        user = self._user(
            "create@example.test",
            ("view_storedcredential", "add_storedcredential"),
        )
        StaffAccessProfile.objects.create(user=user, all_clients=True)
        payload = CredentialCreateIn(
            name="Shared portal login",
            credential_type_id=self.password_type.id,
            ownership_type="internal",
            values={
                "username": "adam@example.test",
                "password": "encrypted-password",
                "notes": "encrypted notes",
            },
            resource_links=[
                CredentialResourceLinkIn(
                    resource_id=self.internal_resource.id,
                    purpose="Server login",
                ),
                CredentialResourceLinkIn(
                    resource_id=self.client_a_resource.id,
                    purpose="Website login",
                ),
            ],
        )

        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.encryption_key]):
            status, body = create_credential(self._request(user, "post"), payload)

        self.assertEqual(status, 201)
        detail = cast(CredentialDetailOut, body)
        credential = StoredCredential.objects.get(id=detail.id)
        self.assertEqual(credential.username, "adam@example.test")
        self.assertEqual(credential.password, "")
        self.assertEqual(credential.notes, "")
        self.assertEqual(credential.resource_links.count(), 2)
        self.assertNotIn("encrypted-password", credential.encrypted_secret_payload)
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.encryption_key]):
            self.assertEqual(
                load_credential_secrets_for_service(credential),
                {"password": "encrypted-password", "notes": "encrypted notes"},
            )

    def test_client_create_rejects_cross_client_resource_link(self) -> None:
        user = self._user(
            "cross-client@example.test",
            ("view_storedcredential", "add_storedcredential"),
        )
        StaffAccessProfile.objects.create(user=user, all_clients=True)
        payload = CredentialCreateIn(
            name="Client A login",
            credential_type_id=self.password_type.id,
            ownership_type="client",
            client_id=self.client_a.id,
            values={"password": "secret"},
            resource_links=[CredentialResourceLinkIn(resource_id=self.client_b_resource.id)],
        )

        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.encryption_key]):
            status, body = create_credential(self._request(user, "post"), payload)

        self.assertEqual(status, 400)
        self.assertEqual(
            cast(dict[str, object], body)["code"],
            "invalid_resource_link",
        )
        self.assertFalse(
            StoredCredential.objects.filter(
                name="Client A login",
                created_by=user,
            ).exists()
        )

    def test_update_merges_new_secret_without_exposing_existing_secret(self) -> None:
        user = self._user(
            "update@example.test",
            ("view_storedcredential", "change_storedcredential"),
        )
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.encryption_key]):
            store_credential_secrets(
                self.internal,
                {"password": "keep-me", "notes": "old notes"},
            )
            result = update_credential(
                self._request(user, "put"),
                self.internal.id,
                CredentialUpdateIn(values={"notes": "replacement notes"}),
            )
            self.assertIsInstance(result, CredentialDetailOut)
            self.internal.refresh_from_db()
            self.assertEqual(
                load_credential_secrets_for_service(self.internal),
                {"password": "keep-me", "notes": "replacement notes"},
            )

    def test_reveal_and_copy_permissions_are_separate(self) -> None:
        user = self._user(
            "copy-only@example.test",
            ("view_storedcredential", "copy_storedcredential_secret"),
        )
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.encryption_key]):
            store_credential_secrets(self.internal, {"password": "copy-value"})
            copy_result = copy_credential_field(
                self._request(user, "post"),
                self.internal.id,
                "password",
            )
            reveal_result = reveal_credential(
                self._request(user, "post"),
                self.internal.id,
                CredentialSecretRevealIn(),
            )

        self.assertIsInstance(copy_result, CredentialSecretValueOut)
        self.assertEqual(
            cast(CredentialSecretValueOut, copy_result).value,
            "copy-value",
        )
        self.assertIsInstance(reveal_result, tuple)
        self.assertEqual(cast(tuple[int, object], reveal_result)[0], 403)

    def test_reveal_can_return_selected_secret_fields(self) -> None:
        user = self._user(
            "reveal@example.test",
            ("view_storedcredential", "reveal_storedcredential"),
        )
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.encryption_key]):
            store_credential_secrets(
                self.internal,
                {"password": "visible", "notes": "not-requested"},
            )
            result = reveal_credential(
                self._request(user, "post"),
                self.internal.id,
                CredentialSecretRevealIn(fields=["password"]),
            )

        self.assertIsInstance(result, CredentialSecretsOut)
        self.assertEqual(
            cast(CredentialSecretsOut, result).fields,
            {"password": "visible"},
        )

    def test_download_requires_download_permission_and_disables_caching(self) -> None:
        user = self._user(
            "download@example.test",
            ("view_storedcredential", "download_storedcredential_secret"),
        )
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.encryption_key]):
            store_credential_secrets(self.internal, {"private_key": "private-key"})
            response = download_credential_field(
                self._request(user, "post"),
                self.internal.id,
                "private_key",
            )

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertIn(".pem", response["Content-Disposition"])
        self.assertEqual(response.content, b"private-key")

    def test_legacy_plaintext_migration_encrypts_and_blanks_old_columns(self) -> None:
        user = self._user(
            "migrate@example.test",
            ("view_storedcredential", "change_storedcredential"),
        )
        self.internal.password = "legacy-password"
        self.internal.notes = "legacy-sensitive-notes"
        self.internal.save(update_fields=["password", "notes", "updated_at"])

        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.encryption_key]):
            result = cast(
                CredentialLegacyMigrationOut,
                migrate_credential_legacy_secrets(
                    self._request(user, "post"),
                    self.internal.id,
                ),
            )
            self.internal.refresh_from_db()
            decrypted = load_credential_secrets_for_service(self.internal)

        self.assertEqual(result.migrated_fields, ["notes", "password"])
        self.assertEqual(self.internal.password, "")
        self.assertEqual(self.internal.notes, "")
        self.assertEqual(
            decrypted,
            {
                "password": "legacy-password",
                "notes": "legacy-sensitive-notes",
            },
        )

    def test_archive_requires_delete_permission(self) -> None:
        user = self._user(
            "archive@example.test",
            ("view_storedcredential", "delete_storedcredential"),
        )

        result = archive_credential(self._request(user, "post"), self.internal.id)

        self.assertIsInstance(result, CredentialDetailOut)
        self.internal.refresh_from_db()
        self.assertEqual(self.internal.status, StoredCredential.Status.ARCHIVED)


class _AnonymousUser:
    is_authenticated = False
    is_staff = False
    is_superuser = False

    def has_perm(self, permission: str) -> bool:
        return False
