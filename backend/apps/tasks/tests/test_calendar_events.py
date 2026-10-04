from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from apps.access_control.models import StaffAccessProfile
from apps.clients.models import Client, Project
from apps.core.ownership import OwnershipType
from apps.tasks.models import CalendarEvent
from authentication.models import User


class CalendarEventAPITests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="calendar@example.test",
            password="test-password",
            first_name="Calendar",
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
        self.project = Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.allowed_client,
            name="Client project",
            start_date=timezone.localdate(),
        )
        self.client.force_login(self.user)

    def _grant(self, app_label: str, codename: str) -> None:
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label=app_label, codename=codename)
        )

    def test_calendar_feed_includes_only_scoped_events(self) -> None:
        self._grant("tasks", "view_calendarevent")
        now = timezone.now()
        visible = CalendarEvent.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.allowed_client,
            title="Visible meeting",
            event_type=CalendarEvent.EventType.MEETING,
            starts_at=now,
            ends_at=now + timedelta(hours=1),
        )
        CalendarEvent.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            title="Hidden meeting",
            starts_at=now,
            ends_at=now + timedelta(hours=1),
        )

        response = self.client.get(
            "/api/admin/calendar",
            {
                "date_from": timezone.localdate().isoformat(),
                "date_to": timezone.localdate().isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["event_count"], 1)
        event_items = [item for item in payload["items"] if item["kind"] == "event"]
        self.assertEqual([item["id"] for item in event_items], [visible.id])
        self.assertEqual(event_items[0]["event_type"], "meeting")

    def test_client_event_creation_requires_accessible_client(self) -> None:
        self._grant("tasks", "add_calendarevent")
        now = timezone.now()
        hidden = self.client.post(
            "/api/admin/calendar/events",
            data={
                "ownership_type": "client",
                "client_id": self.hidden_client.id,
                "title": "Hidden client meeting",
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=1)).isoformat(),
            },
            content_type="application/json",
        )
        self.assertEqual(hidden.status_code, 404)

        allowed = self.client.post(
            "/api/admin/calendar/events",
            data={
                "ownership_type": "client",
                "client_id": self.allowed_client.id,
                "project_id": self.project.id,
                "title": "Allowed client meeting",
                "event_type": "meeting",
                "starts_at": now.isoformat(),
                "ends_at": (now + timedelta(hours=1)).isoformat(),
                "attendee_emails": ["Person@Example.Test", "person@example.test"],
            },
            content_type="application/json",
        )

        self.assertEqual(allowed.status_code, 201)
        event = CalendarEvent.objects.get(id=allowed.json()["id"])
        self.assertEqual(event.client_id, self.allowed_client.id)
        self.assertEqual(event.project_id, self.project.id)
        self.assertEqual(event.attendee_emails, ["person@example.test"])

    def test_event_update_and_delete_obey_object_scope(self) -> None:
        self._grant("tasks", "change_calendarevent")
        self._grant("tasks", "delete_calendarevent")
        now = timezone.now()
        visible = CalendarEvent.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.allowed_client,
            title="Editable",
            starts_at=now,
            ends_at=now + timedelta(hours=1),
        )
        hidden = CalendarEvent.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            title="Hidden",
            starts_at=now,
            ends_at=now + timedelta(hours=1),
        )

        updated = self.client.put(
            f"/api/admin/calendar/events/{visible.id}",
            data={"title": "Updated"},
            content_type="application/json",
        )
        hidden_update = self.client.put(
            f"/api/admin/calendar/events/{hidden.id}",
            data={"title": "Should not update"},
            content_type="application/json",
        )
        deleted = self.client.delete(f"/api/admin/calendar/events/{visible.id}")

        self.assertEqual(updated.status_code, 200)
        self.assertEqual(hidden_update.status_code, 404)
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(CalendarEvent.objects.filter(id=visible.id).exists())
