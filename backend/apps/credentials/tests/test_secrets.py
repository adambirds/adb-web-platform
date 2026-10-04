from unittest.mock import patch

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
    copy_credential_secret,
    download_credential_secret,
    load_credential_secrets_for_service,
    merge_credential_secrets,
    migrate_legacy_plaintext_secrets,
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

    def _user(self, email: str) -> User:
        return User.objects.create_user(
            email=email,
            password="not-a-real-password",
            first_name="Credential",
            last_name="User",
            is_staff=True,
        )

    def _grant(self, user: User, codename: str) -> User:
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="credentials",
                codename=codename,
            )
        )
        return User.objects.get(pk=user.pk)

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
            self.assertEqual(
                self.credential.secret_field_keys,
                ["certificate", "passphrase", "private_key"],
            )
            self.assertEqual(load_credential_secrets_for_service(self.credential), secrets)
            self.assertIsNotNone(self.credential.last_rotated_at)

    def test_merge_updates_secrets_without_revealing_unchanged_values(self) -> None:
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.primary_key]):
            store_credential_secrets(
                self.credential,
                {"password": "original", "notes": "encrypted note"},
            )
            merge_credential_secrets(
                self.credential,
                {"password": "replacement"},
            )

            self.assertEqual(
                load_credential_secrets_for_service(self.credential),
                {"password": "replacement", "notes": "encrypted note"},
            )
            self.credential.refresh_from_db()
            self.assertEqual(self.credential.secret_field_keys, ["notes", "password"])
            self.assertEqual(self.credential.notes, "")

    def test_merge_can_clear_one_secret_field(self) -> None:
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.primary_key]):
            store_credential_secrets(
                self.credential,
                {"private_key": "key", "passphrase": "old-passphrase"},
            )
            merge_credential_secrets(self.credential, {}, clear_fields=["passphrase"])

            self.assertEqual(
                load_credential_secrets_for_service(self.credential),
                {"private_key": "key"},
            )

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
        user = self._user("credential-user@example.test")
        secrets = {"client_secret": "never-audit-this-value"}
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.primary_key]):
            store_credential_secrets(self.credential, secrets)

            with self.assertRaises(PermissionDenied):
                reveal_credential_secrets(self.credential, actor=user)

            user = self._grant(user, "reveal_storedcredential")
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

    def test_copy_has_separate_permission_and_audit_action(self) -> None:
        user = self._grant(self._user("copy@example.test"), "copy_storedcredential_secret")
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.primary_key]):
            store_credential_secrets(self.credential, {"password": "copy-me"})
            self.assertEqual(
                copy_credential_secret(self.credential, "password", actor=user),
                "copy-me",
            )
            with self.assertRaises(PermissionDenied):
                reveal_credential_secrets(self.credential, actor=user)

        event = AuditEvent.objects.get(action="credentials.secret_copied")
        self.assertEqual(event.metadata, {"secret_fields": ["password"]})
        self.assertNotIn("copy-me", str(event.metadata))

    def test_download_has_separate_permission_and_audit_action(self) -> None:
        user = self._grant(
            self._user("download@example.test"),
            "download_storedcredential_secret",
        )
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.primary_key]):
            store_credential_secrets(self.credential, {"private_key": "private-key-data"})
            self.assertEqual(
                download_credential_secret(self.credential, "private_key", actor=user),
                "private-key-data",
            )

        event = AuditEvent.objects.get(action="credentials.secret_downloaded")
        self.assertEqual(event.metadata, {"secret_fields": ["private_key"]})
        self.assertNotIn("private-key-data", str(event.metadata))

    def test_legacy_migration_refreshes_and_locks_the_current_row(self) -> None:
        user = self._grant(self._user("migrate@example.test"), "change_storedcredential")
        self.credential.password = "legacy-password"
        self.credential.save(update_fields=["password", "updated_at"])
        stale_credential = StoredCredential.objects.get(pk=self.credential.pk)

        current_credential = StoredCredential.objects.get(pk=self.credential.pk)
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.primary_key]):
            store_credential_secrets(current_credential, {"notes": "current-encrypted-note"})
            migrated = migrate_legacy_plaintext_secrets(stale_credential, actor=user)

            current_credential.refresh_from_db()
            self.assertEqual(
                load_credential_secrets_for_service(current_credential),
                {
                    "notes": "current-encrypted-note",
                    "password": "legacy-password",
                },
            )

        self.assertEqual(migrated, ["password"])
        self.assertEqual(current_credential.password, "")

    def test_legacy_migration_rolls_back_when_audit_fails(self) -> None:
        user = self._grant(self._user("rollback@example.test"), "change_storedcredential")
        self.credential.password = "legacy-password"
        self.credential.save(update_fields=["password", "updated_at"])

        with (
            override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.primary_key]),
            patch.object(AuditEvent, "record", side_effect=RuntimeError("audit unavailable")),
            self.assertRaisesMessage(RuntimeError, "audit unavailable"),
        ):
            migrate_legacy_plaintext_secrets(self.credential, actor=user)

        self.credential.refresh_from_db()
        self.assertEqual(self.credential.password, "legacy-password")
        self.assertEqual(self.credential.encrypted_secret_payload, "")
