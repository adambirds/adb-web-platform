from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile, TicketQueueAccessGrant
from apps.clients.models import Client
from apps.core.models import Brand
from apps.ticketing.models import Ticket, TicketNote, TicketQueue
from authentication.models import User


class TicketNoteApiTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="agent@example.test",
            password="not-a-real-password",
            first_name="Support",
            last_name="Agent",
            is_staff=True,
        )
        self.profile = StaffAccessProfile.objects.create(user=self.user)
        self.brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="adb-test.example.test",
        )
        self.client_account = Client.objects.create(
            name="Client A",
            email="client@example.test",
        )
        self.other_client = Client.objects.create(
            name="Client B",
            email="other@example.test",
        )
        self.queue = TicketQueue.objects.create(
            name="Support",
            key="support",
            brand=self.brand,
        )
        self.ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue,
            client=self.client_account,
            subject="Website issue",
            last_message_at=timezone.now(),
        )
        self.hidden_ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue,
            client=self.other_client,
            subject="Hidden ticket",
            last_message_at=timezone.now(),
        )

        ClientAccessGrant.objects.create(profile=self.profile, client=self.client_account)
        TicketQueueAccessGrant.objects.create(profile=self.profile, queue=self.queue)
        self._grant("view_ticket", "add_ticket_note")
        self.client.force_login(self.user)

    def _grant(self, *codenames: str) -> None:
        permissions = Permission.objects.filter(
            content_type__app_label="ticketing",
            codename__in=codenames,
        )
        self.user.user_permissions.add(*permissions)

    def test_note_endpoint_creates_internal_note(self) -> None:
        response = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/notes",
            data={"body": "  Customer called and confirmed the issue.  "},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["body"], "Customer called and confirmed the issue.")
        self.assertEqual(payload["author_name"], "Support Agent")
        note = TicketNote.objects.get(id=payload["id"])
        self.assertEqual(note.ticket, self.ticket)
        self.assertEqual(note.author, self.user)

    def test_note_endpoint_requires_note_capability(self) -> None:
        self.user.user_permissions.remove(
            Permission.objects.get(
                content_type__app_label="ticketing",
                codename="add_ticket_note",
            )
        )

        response = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/notes",
            data={"body": "Internal note"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(TicketNote.objects.exists())

    def test_note_endpoint_hides_ticket_outside_client_scope(self) -> None:
        response = self.client.post(
            f"/api/admin/tickets/{self.hidden_ticket.id}/notes",
            data={"body": "Internal note"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(TicketNote.objects.exists())

    def test_note_endpoint_rejects_empty_body(self) -> None:
        response = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/notes",
            data={"body": "   "},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "note_body_required")
        self.assertFalse(TicketNote.objects.exists())

    def test_ticket_detail_exposes_mutation_capabilities(self) -> None:
        response = self.client.get(f"/api/admin/tickets/{self.ticket.id}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["can_add_note"])
        self.assertFalse(payload["can_reply"])
