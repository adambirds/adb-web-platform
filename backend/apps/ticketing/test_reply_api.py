from unittest.mock import Mock, patch

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile, TicketQueueAccessGrant
from apps.clients.models import Client
from apps.core.models import Brand
from apps.ticketing.models import (
    Mailbox,
    MicrosoftGraphConnection,
    Ticket,
    TicketMessage,
    TicketQueue,
)
from authentication.models import User


class TicketReplyApiTests(TestCase):
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
        self.connection = MicrosoftGraphConnection.objects.create(
            name="Microsoft 365",
            tenant_id="tenant-id",
            client_id="client-id",
        )
        self.mailbox = Mailbox.objects.create(
            graph_connection=self.connection,
            email_address="support@adb-test.example.test",
            display_name="ADB Support",
            brand=self.brand,
            default_queue=self.queue,
        )
        self.ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue,
            mailbox=self.mailbox,
            client=self.client_account,
            subject="Website issue",
            last_message_at=timezone.now(),
        )
        TicketMessage.objects.create(
            ticket=self.ticket,
            direction=TicketMessage.Direction.INBOUND,
            sender_name="Client",
            sender_address="client@example.test",
            subject="Website issue",
            body_text="Please help",
            provider="microsoft_graph",
            provider_message_id="source-message-id",
            internet_message_id="<source@example.test>",
            sent_or_received_at=timezone.now(),
        )
        self.hidden_ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue,
            mailbox=self.mailbox,
            client=self.other_client,
            subject="Hidden ticket",
            last_message_at=timezone.now(),
        )
        TicketMessage.objects.create(
            ticket=self.hidden_ticket,
            direction=TicketMessage.Direction.INBOUND,
            sender_name="Other client",
            sender_address="other@example.test",
            subject="Hidden ticket",
            body_text="Private",
            provider="microsoft_graph",
            provider_message_id="hidden-source-message-id",
            sent_or_received_at=timezone.now(),
        )

        ClientAccessGrant.objects.create(profile=self.profile, client=self.client_account)
        TicketQueueAccessGrant.objects.create(profile=self.profile, queue=self.queue)
        self._grant("view_ticket", "reply_ticket")
        self.client.force_login(self.user)

    def _grant(self, *codenames: str) -> None:
        permissions = Permission.objects.filter(
            content_type__app_label="ticketing",
            codename__in=codenames,
        )
        self.user.user_permissions.add(*permissions)

    @patch("apps.ticketing.ninja.admin_views.deliver_ticket_reply_task.delay")
    def test_reply_endpoint_queues_scoped_graph_reply(self, delay: Mock) -> None:
        response = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/reply",
            data={
                "body_text": "  We have fixed this.  ",
                "cc_recipients": ["CC@Example.Test", "cc@example.test"],
                "bcc_recipients": ["audit@example.test"],
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 202)
        payload = response.json()
        self.assertEqual(payload["direction"], TicketMessage.Direction.OUTBOUND)
        self.assertEqual(payload["body_text"], "We have fixed this.")
        self.assertEqual(payload["delivery_status"], "queued")
        self.assertEqual(payload["delivery_error"], "")
        self.assertEqual(payload["cc_recipients"], ["cc@example.test"])
        self.assertEqual(payload["bcc_recipients"], ["audit@example.test"])
        delay.assert_called_once_with(payload["id"])

    @patch("apps.ticketing.ninja.admin_views.deliver_ticket_reply_task.delay")
    def test_reply_endpoint_requires_reply_capability(self, delay: Mock) -> None:
        self.user.user_permissions.remove(
            Permission.objects.get(
                content_type__app_label="ticketing",
                codename="reply_ticket",
            )
        )

        response = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/reply",
            data={"body_text": "Hello"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        delay.assert_not_called()

    @patch("apps.ticketing.ninja.admin_views.deliver_ticket_reply_task.delay")
    def test_reply_endpoint_hides_ticket_outside_client_scope(self, delay: Mock) -> None:
        response = self.client.post(
            f"/api/admin/tickets/{self.hidden_ticket.id}/reply",
            data={"body_text": "Hello"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        delay.assert_not_called()

    @patch("apps.ticketing.ninja.admin_views.deliver_ticket_reply_task.delay")
    def test_reply_endpoint_rejects_empty_body(self, delay: Mock) -> None:
        response = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/reply",
            data={"body_text": "   "},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "reply_unavailable")
        delay.assert_not_called()
