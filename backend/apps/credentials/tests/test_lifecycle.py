from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from apps.access_control.models import StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.credentials.health import evaluate_credential_health
from apps.credentials.models import StoredCredential
from authentication.models import User


class CredentialLifecycleAPITests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="vault-health@example.test",
            password="test-password",
            first_name="Vault",
            last_name="Health",
            is_staff=True,
        )
        self.allowed_client = Client.objects.create(
            name="Allowed",
            company="Allowed Ltd",
            email="allowed@example.test",
        )
        self.hidden_client = Client.objects.create(
            name="Hidden",
            company="Hidden Ltd",
            email="hidden@example.test",
        )
        profile = StaffAccessProfile.objects.create(user=self.user)
        profile.client_grants.create(client=self.allowed_client)
        self.client.force_login(self.user)

    def _grant(self, codename: str) -> None:
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="credentials",
                codename=codename,
            )
        )

    def test_health_list_is_scope_filtered_and_metadata_only(self) -> None:
        self._grant("view_storedcredential")
        visible = StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.allowed_client,
            name="Expiring metadata credential",
            expires_at=timezone.now() + timedelta(days=5),
            encrypted_secret_payload="not-a-real-payload",
        )
        StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            name="Hidden expiring credential",
            expires_at=timezone.now() + timedelta(days=5),
        )

        response = self.client.get("/api/admin/credential-health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["credential_id"] for item in payload["items"]], [visible.id])
        self.assertEqual(payload["critical_count"], 1)
        self.assertEqual(payload["items"][0]["health_status"], "expiring_soon")
        self.assertNotIn("encrypted_secret_payload", payload["items"][0])

    def test_rotation_interval_can_be_configured_and_marked_rotated(self) -> None:
        self._grant("view_storedcredential")
        self._grant("change_storedcredential")
        credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Rotate me",
        )

        response = self.client.put(
            f"/api/admin/credentials/{credential.id}/lifecycle",
            data={"rotation_interval_days": 90, "mark_rotated": True},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        credential.refresh_from_db()
        self.assertEqual(credential.rotation_interval_days, 90)
        self.assertIsNotNone(credential.last_rotated_at)
        self.assertEqual(response.json()["health_status"], "healthy")
        self.assertIsNotNone(response.json()["rotation_due_at"])

    def test_overdue_rotation_is_critical(self) -> None:
        credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Old credential",
            rotation_interval_days=30,
            last_rotated_at=timezone.now() - timedelta(days=45),
        )

        health = evaluate_credential_health(credential)

        self.assertEqual(health.status, "rotation_overdue")
        self.assertEqual(health.severity, "critical")
