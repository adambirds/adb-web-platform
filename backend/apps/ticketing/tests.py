from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile, TicketQueueAccessGrant
from apps.clients.models import Client
from apps.core.models import Brand
from apps.ticketing.models import Ticket, TicketMessage, TicketQueue

User = get_user_model()


class TicketingAdminScopeTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="agent@example.test",
            first_name="Ticket",
            last_name="Agent",
            password="test-password-123",
            is_staff=True,
        )
        self.profile = StaffAccessProfile.objects.create(user=self.user)
        self.brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="adb-test.example.test",
        )
        self.client_a = Client.objects.create(name="Client A", email="a@example.test")
        self.client_b = Client.objects.create(name="Client B", email="b@example.test")
        self.queue_a = TicketQueue.objects.create(
            name="Support A",
            key="support-a",
            brand=self.brand,
        )
        self.queue_b = TicketQueue.objects.create(
            name="Support B",
            key="support-b",
            brand=self.brand,
        )
        self.ticket_a = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue_a,
            client=self.client_a,
            subject="Visible ticket",
            last_message_at=timezone.now(),
        )
        self.ticket_wrong_client = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue_a,
            client=self.client_b,
            subject="Wrong client",
            last_message_at=timezone.now(),
        )
        self.ticket_wrong_queue = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue_b,
            client=self.client_a,
            subject="Wrong queue",
            last_message_at=timezone.now(),
        )
        TicketMessage.objects.create(
            ticket=self.ticket_a,
            direction=TicketMessage.Direction.INBOUND,
            sender_address="a@example.test",
            body_text="Hello",
            body_text_normalised="Hello",
            sent_or_received_at=timezone.now(),
        )

        ClientAccessGrant.objects.create(profile=self.profile, client=self.client_a)
        TicketQueueAccessGrant.objects.create(profile=self.profile, queue=self.queue_a)
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_ticket"),
            Permission.objects.get(codename="view_ticketqueue"),
        )
        self.client.force_login(self.user)

    def test_ticket_list_requires_both_client_and_queue_scope(self) -> None:
        response = self.client.get("/api/admin/tickets", {"page": 1, "page_size": 25})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["items"][0]["id"], self.ticket_a.id)

    def test_ticket_detail_outside_queue_scope_is_hidden(self) -> None:
        response = self.client.get(f"/api/admin/tickets/{self.ticket_wrong_queue.id}")

        self.assertEqual(response.status_code, 404)

    def test_queue_list_only_returns_granted_queues(self) -> None:
        response = self.client.get("/api/admin/ticket-queues")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([row["id"] for row in payload], [self.queue_a.id])
