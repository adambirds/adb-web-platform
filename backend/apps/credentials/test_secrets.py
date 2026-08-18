from cryptography.fernet import Fernet
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings

from apps.core.models import AuditEvent
from apps.core.ownership import OwnershipType
from apps.credentials.models import StoredCredential
from apps.credentials.secrets import (
    CredentialDecryptionError,
    CredentialEncryptionNotConfiguredError,
    load_credential_secrets_for_service,
    reveal_credential_secrets,
    rotate_credential_encryption,
    store_credential_secrets,
)
from authentication.models import User


class CredentialSecretTests(TestCase):
    def setUp(self) -> None:
        self.primary_key = Fernet.generate_key().decode("ascii")
        self.old_key = Fernet.generate_key().decode("ascii")
        self.credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Microsoft Graph certificate",
        )

    @override_settings(CREDENTIAL_ENCRYPTION_KEYS=[])
    def test_secret_storage_requires_configured_key(self) -> None:
        with self.assertRaises(CredentialEncryptionNotConfiguredError):
            store_credential_secrets(self.credential, {"client_secret": "super-secret"})

    def test_secret_payload_round_trips_without_plaintext_in_database(self) -> None:
        secrets = {
            "private_key": (
                "-----BEGIN PRIVATE KEY-----\nvery-secret-key\n-----END PRIVATE KEY-----"
            ),
            "certificate": (
                "-----BEGIN CERTIFICATE-----\npublic-certificate\n-----END CERTIFICATE-----"
            ),
            "passphrase": "correct horse battery staple",
        }

        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.primary_key]):
            store_credential_secrets(self.credential, secrets)
            self.credential.refresh_from_db()

            self.assertTrue(self.credential.encrypted_secret_payload)
            self.assertNotIn("very-secret-key", self.credential.encrypted_secret_payload)
            self.assertNotIn(
                "correct horse battery staple",
                self.credential.encrypted_secret_payload,
            )
            self.assertEqual(load_credential_secrets_for_service(self.credential), secrets)
            self.assertIsNotNone(self.credential.last_rotated_at)

    def test_wrong_key_fails_closed(self) -> None:
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.old_key]):
            store_credential_secrets(self.credential, {"client_secret": "secret-value"})

        with (
            override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.primary_key]),
            self.assertRaises(CredentialDecryptionError),
        ):
            load_credential_secrets_for_service(self.credential)

    def test_rotation_accepts_old_key_then_reencrypts_with_primary_key(self) -> None:
        secrets = {"client_secret": "rotate-me"}
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.old_key]):
            store_credential_secrets(self.credential, secrets)
            self.credential.refresh_from_db()
            old_payload = self.credential.encrypted_secret_payload

        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.primary_key, self.old_key]):
            self.assertEqual(load_credential_secrets_for_service(self.credential), secrets)
            rotate_credential_encryption(self.credential)
            self.credential.refresh_from_db()
            self.assertNotEqual(self.credential.encrypted_secret_payload, old_payload)

        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.primary_key]):
            self.assertEqual(load_credential_secrets_for_service(self.credential), secrets)

    def test_reveal_requires_permission_and_records_safe_audit_event(self) -> None:
        user = User.objects.create_user(
            email="credential-user@example.test",
            password="not-a-real-password",
            first_name="Credential",
            last_name="User",
            is_staff=True,
        )
        secrets = {"client_secret": "never-audit-this-value"}
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.primary_key]):
            store_credential_secrets(self.credential, secrets)

            with self.assertRaises(PermissionDenied):
                reveal_credential_secrets(self.credential, actor=user)

            user.user_permissions.add(
                Permission.objects.get(codename="reveal_storedcredential"),
            )
            user = User.objects.get(pk=user.pk)
            revealed = reveal_credential_secrets(
                self.credential,
                actor=user,
                ip_address="127.0.0.1",
                user_agent="credential-test",
            )

        self.assertEqual(revealed, secrets)
        event = AuditEvent.objects.get(action="credentials.secret_revealed")
        self.assertEqual(event.actor, user)
        self.assertEqual(event.target_id, str(self.credential.id))
        self.assertEqual(event.metadata, {"secret_fields": ["client_secret"]})
        self.assertNotIn("never-audit-this-value", str(event.metadata))
