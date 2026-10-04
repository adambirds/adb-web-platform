from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from apps.access_control.models import StaffAccessProfile
from apps.clients.models import Client
from apps.core.models import AuditEvent, Notification
from apps.core.ownership import OwnershipType
from apps.tasks.models import Task
from authentication.models import User


class OperationalPolishAPITests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="operations@example.test",
            password="test-password",
            first_name="Ops",
            last_name="User",
            is_staff=True,
        )
        self.other = User.objects.create_user(
            email="other@example.test",
            password="test-password",
            first_name="Other",
            last_name="User",
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

    def _grant(self, app_label: str, codename: str) -> None:
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label=app_label, codename=codename)
        )

    def test_client_activity_is_scoped_and_hides_sensitive_metadata(self) -> None:
        self._grant("clients", "view_client")
        allowed = AuditEvent.record(
            action="client.allowed",
            actor=self.other,
            target=self.allowed_client,
            metadata={"private": "metadata"},
            ip_address="192.0.2.10",
        )
        AuditEvent.record(
            action="client.hidden",
            actor=self.other,
            target=self.hidden_client,
        )

        response = self.client.get(
            "/api/admin/activity",
            {"client_id": str(self.allowed_client.id)},
        )
        hidden = self.client.get(
            "/api/admin/activity",
            {"client_id": str(self.hidden_client.id)},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["id"] for item in payload["items"]], [allowed.id])
        self.assertEqual(payload["items"][0]["metadata"], {})
        self.assertIsNone(payload["items"][0]["ip_address"])
        self.assertFalse(payload["metadata_visible"])
        self.assertEqual(hidden.status_code, 404)

    def test_global_audit_requires_permission_and_only_exposes_scoped_rows(self) -> None:
        own = AuditEvent.record(action="own.event", actor=self.user)
        scoped = AuditEvent.record(
            action="scoped.event",
            actor=self.other,
            target=self.allowed_client,
        )
        hidden = AuditEvent.record(
            action="hidden.event",
            actor=self.other,
            target=self.hidden_client,
        )

        denied = self.client.get("/api/admin/activity")
        self.assertEqual(denied.status_code, 403)

        self._grant("core", "view_auditevent")
        response = self.client.get("/api/admin/activity")
        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.json()["items"]}
        self.assertEqual(ids, {own.id, scoped.id})
        self.assertNotIn(hidden.id, ids)

    def test_sensitive_audit_permission_reveals_metadata_only_to_authorised_user(self) -> None:
        self._grant("core", "view_auditevent")
        self._grant("core", "view_sensitive_audit_metadata")
        event = AuditEvent.record(
            action="security.event",
            actor=self.user,
            metadata={"reason": "test"},
            ip_address="198.51.100.20",
            user_agent="Test Agent",
        )

        response = self.client.get("/api/admin/activity")

        self.assertEqual(response.status_code, 200)
        item = next(item for item in response.json()["items"] if item["id"] == event.id)
        self.assertEqual(item["metadata"], {"reason": "test"})
        self.assertEqual(item["ip_address"], "198.51.100.20")
        self.assertEqual(item["user_agent"], "Test Agent")

    def test_notification_refresh_creates_only_current_users_overdue_tasks(self) -> None:
        self._grant("tasks", "view_task")
        due = timezone.localdate() - timedelta(days=2)
        visible = Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.allowed_client,
            title="Visible overdue task",
            due_date=due,
            assigned_to=self.user,
        )
        Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            title="Hidden overdue task",
            due_date=due,
            assigned_to=self.user,
        )
        Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.allowed_client,
            title="Other user's overdue task",
            due_date=due,
            assigned_to=self.other,
        )

        response = self.client.get("/api/admin/notifications")

        self.assertEqual(response.status_code, 200)
        payload: dict[str, Any] = response.json()
        self.assertEqual(payload["unread_count"], 1)
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["title"], "Overdue task: Visible overdue task")
        self.assertEqual(payload["items"][0]["client_id"], self.allowed_client.id)
        self.assertTrue(
            Notification.objects.filter(
                user=self.user,
                source_key=f"task:overdue:{visible.id}",
            ).exists()
        )

    def test_dismissed_notification_stays_dismissed_while_source_is_unchanged(self) -> None:
        self._grant("tasks", "view_task")
        task = Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            title="Dismiss me",
            due_date=timezone.localdate() - timedelta(days=1),
            assigned_to=self.user,
        )
        initial = self.client.get("/api/admin/notifications").json()
        notification_id = initial["items"][0]["id"]

        dismissed = self.client.post(f"/api/admin/notifications/{notification_id}/dismiss")
        refreshed = self.client.get("/api/admin/notifications")

        self.assertEqual(dismissed.status_code, 200)
        self.assertEqual(refreshed.status_code, 200)
        self.assertEqual(refreshed.json()["items"], [])
        notification = Notification.objects.get(
            user=self.user,
            source_key=f"task:overdue:{task.id}",
        )
        self.assertIsNotNone(notification.dismissed_at)
