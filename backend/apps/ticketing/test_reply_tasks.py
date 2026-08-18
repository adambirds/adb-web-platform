from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from apps.core.models import Brand
from apps.core.ownership import OwnershipType
from apps.credentials.models import StoredCredential
from apps.ticketing.models import (
    Mailbox,
    MicrosoftGraphConnection,
    Ticket,
    TicketMessage,
    TicketQueue,
)
from apps.ticketing.services.graph import MicrosoftGraphError
from apps.ticketing.services.graph_outbound import GraphReplyReceipt
from apps.ticketing.services.replies import prepare_ticket_reply
from apps.ticketing.tasks import _deliver_graph_ticket_reply, deliver_ticket_reply_task
from authentication.models import User


class TicketReplyDeliveryTaskTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="agent@example.test",
            password="not-a-real-password",
            first_name="Support",
            last_name="Agent",
            is_staff=True,
        )
        self.brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="adb-test.example.test",
        )
        self.queue = TicketQueue.objects.create(
            name="Support",
            key="support",
            brand=self.brand,
        )
        self.credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Graph credential",
        )
        self.connection = MicrosoftGraphConnection.objects.create(
            name="Microsoft 365",
            tenant_id="tenant-id",
            client_id="client-id",
            authentication_method=MicrosoftGraphConnection.AuthenticationMethod.CERTIFICATE,
            credential=self.credential,
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
            subject="Website issue",
            status=Ticket.Status.OPEN,
        )
        self.source_message = TicketMessage.objects.create(
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
        self.reply = prepare_ticket_reply(
            self.ticket,
            self.user,
            "We have fixed this.",
            cc_recipients=("cc@example.test",),
        )

    @patch("apps.ticketing.tasks._deliver_graph_ticket_reply")
    @patch("apps.ticketing.tasks._ticket_reply_delivery_lock")
    def test_task_delivers_eligible_reply_inside_lock(
        self,
        reply_lock: Mock,
        deliver: Mock,
    ) -> None:
        reply_lock.return_value.__enter__.return_value = True
        deliver.return_value = 1

        result = deliver_ticket_reply_task.run(self.reply.id)

        self.assertEqual(result, 1)
        reply_lock.assert_called_once_with(self.reply.id)
        deliver.assert_called_once()
        self.assertEqual(deliver.call_args.args[0].id, self.reply.id)

    @patch("apps.ticketing.tasks._deliver_graph_ticket_reply")
    @patch("apps.ticketing.tasks._ticket_reply_delivery_lock")
    def test_task_skips_reply_when_another_worker_holds_lock(
        self,
        reply_lock: Mock,
        deliver: Mock,
    ) -> None:
        reply_lock.return_value.__enter__.return_value = False

        result = deliver_ticket_reply_task.run(self.reply.id)

        self.assertEqual(result, 0)
        deliver.assert_not_called()

    @patch("apps.ticketing.tasks.MicrosoftGraphOutboundAdapter")
    @patch("apps.ticketing.tasks.MicrosoftGraphTokenProvider")
    def test_delivery_uses_ticket_mailbox_and_persists_graph_receipt(
        self,
        token_provider: Mock,
        outbound_adapter: Mock,
    ) -> None:
        token_instance = token_provider.return_value
        outbound_adapter.return_value.send_reply.return_value = GraphReplyReceipt(
            provider_message_id="sent-provider-id",
            internet_message_id="<sent@example.test>",
            provider_conversation_id="conversation-id",
        )

        result = _deliver_graph_ticket_reply(self.reply)

        self.assertEqual(result, 1)
        token_provider.assert_called_once_with(self.connection)
        outbound_adapter.assert_called_once_with(token_instance)
        outbound_adapter.return_value.send_reply.assert_called_once_with(
            self.mailbox,
            "source-message-id",
            ticket_reference=self.ticket.reference,
            ticket_subject="Website issue",
            body_html="",
            body_text="We have fixed this.",
            cc_recipients=["cc@example.test"],
            bcc_recipients=[],
        )
        self.reply.refresh_from_db()
        self.ticket.refresh_from_db()
        self.assertEqual(self.reply.delivery_status, "sent")
        self.assertEqual(self.reply.provider_message_id, "sent-provider-id")
        self.assertEqual(self.reply.internet_message_id, "<sent@example.test>")
        self.assertEqual(self.ticket.status, Ticket.Status.WAITING_CUSTOMER)
        self.assertIsNotNone(self.ticket.first_response_at)
        self.assertEqual(self.ticket.last_message_at, self.reply.sent_or_received_at)

    @patch("apps.ticketing.tasks.MicrosoftGraphOutboundAdapter")
    @patch("apps.ticketing.tasks.MicrosoftGraphTokenProvider")
    def test_delivery_records_retryable_graph_failure(
        self,
        token_provider: Mock,
        outbound_adapter: Mock,
    ) -> None:
        outbound_adapter.return_value.send_reply.side_effect = MicrosoftGraphError(
            "delivery failed"
        )

        with self.assertRaisesMessage(MicrosoftGraphError, "delivery failed"):
            _deliver_graph_ticket_reply(self.reply)

        token_provider.assert_called_once_with(self.connection)
        self.reply.refresh_from_db()
        self.ticket.refresh_from_db()
        self.assertEqual(self.reply.delivery_status, "failed")
        self.assertEqual(
            self.reply.delivery_error,
            "MicrosoftGraphError: delivery failed",
        )
        self.assertEqual(self.ticket.status, Ticket.Status.OPEN)
        self.assertIsNone(self.ticket.first_response_at)

    def test_delivery_fails_closed_when_mailbox_is_not_background_eligible(self) -> None:
        self.connection.credential = None
        self.connection.save(update_fields=["credential"])

        result = _deliver_graph_ticket_reply(self.reply)

        self.assertEqual(result, 0)
        self.reply.refresh_from_db()
        self.assertEqual(self.reply.delivery_status, "failed")
        self.assertEqual(
            self.reply.delivery_error,
            "Ticket mailbox is not eligible for background Graph delivery.",
        )
