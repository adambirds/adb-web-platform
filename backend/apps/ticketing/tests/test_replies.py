from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.core.models import Brand
from apps.ticketing.models import (
    Mailbox,
    MicrosoftGraphConnection,
    Ticket,
    TicketMessage,
    TicketQueue,
)
from apps.ticketing.services.replies import (
    DELIVERY_STATUS_FAILED,
    DELIVERY_STATUS_SENDING,
    DELIVERY_STATUS_SENT,
    TicketReplyError,
    complete_ticket_reply,
    fail_ticket_reply,
    mark_ticket_reply_sending,
    prepare_ticket_reply,
)
from authentication.models import User


class TicketReplyPreparationTests(TestCase):
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
        self.connection = MicrosoftGraphConnection.objects.create(
            name="Microsoft 365",
            tenant_id="tenant-id",
            client_id="client-id",
        )
        self.mailbox = Mailbox.objects.create(
            graph_connection=self.connection,
            email_address="Support@ADB-Test.Example.Test",
            display_name="ADB Support",
            brand=self.brand,
            default_queue=self.queue,
        )
        self.ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue,
            mailbox=self.mailbox,
            subject="Re: Website issue",
        )
        now = timezone.now()
        self.older_message = TicketMessage.objects.create(
            ticket=self.ticket,
            direction=TicketMessage.Direction.INBOUND,
            sender_name="Client",
            sender_address="old@example.test",
            subject="Website issue",
            body_text="Old message",
            provider="microsoft_graph",
            provider_message_id="old-provider-id",
            internet_message_id="<old@example.test>",
            references=["<first@example.test>"],
            sent_or_received_at=now - timedelta(hours=1),
        )
        self.latest_message = TicketMessage.objects.create(
            ticket=self.ticket,
            direction=TicketMessage.Direction.INBOUND,
            sender_name="Client",
            sender_address="CLIENT@Example.Test",
            subject="Re: Website issue",
            body_text="Latest message",
            provider="microsoft_graph",
            provider_message_id="latest-provider-id",
            internet_message_id="<latest@example.test>",
            references=["<first@example.test>", "<old@example.test>"],
            sent_or_received_at=now,
        )

    def test_prepare_reply_targets_latest_graph_message_and_normalises_recipients(self) -> None:
        reply = prepare_ticket_reply(
            self.ticket,
            self.user,
            "  We have fixed this.  ",
            cc_recipients=(
                " CC@Example.Test ",
                "cc@example.test",
                "client@example.test",
                "support@adb-test.example.test",
            ),
            bcc_recipients=(
                "Audit@Example.Test",
                "cc@example.test",
                "client@example.test",
            ),
        )

        self.assertEqual(reply.direction, TicketMessage.Direction.OUTBOUND)
        self.assertEqual(reply.sender_name, "ADB Support")
        self.assertEqual(reply.sender_address, "support@adb-test.example.test")
        self.assertEqual(reply.to_recipients, ["client@example.test"])
        self.assertEqual(reply.cc_recipients, ["cc@example.test"])
        self.assertEqual(reply.bcc_recipients, ["audit@example.test"])
        self.assertEqual(reply.subject, f"Re: [{self.ticket.reference}] Website issue")
        self.assertEqual(reply.body_text, "We have fixed this.")
        self.assertEqual(reply.body_text_normalised, "We have fixed this.")
        self.assertEqual(reply.provider, "microsoft_graph")
        self.assertIsNone(reply.provider_message_id)
        self.assertEqual(reply.provider_reply_to_message_id, "latest-provider-id")
        self.assertEqual(reply.in_reply_to, "<latest@example.test>")
        self.assertEqual(
            reply.references,
            ["<first@example.test>", "<old@example.test>", "<latest@example.test>"],
        )
        self.assertEqual(reply.delivery_status, "queued")
        self.assertEqual(reply.created_by, self.user)

    def test_complete_reply_marks_message_sent_and_advances_ticket(self) -> None:
        closed_at = timezone.now() - timedelta(minutes=10)
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.resolved_at = closed_at
        self.ticket.closed_at = closed_at
        self.ticket.save(update_fields=["status", "resolved_at", "closed_at"])
        reply = prepare_ticket_reply(self.ticket, self.user, "We have fixed this.")
        delivered_at = timezone.now()

        delivered = complete_ticket_reply(
            reply,
            provider_message_id="sent-provider-id",
            internet_message_id="<sent@example.test>",
            sent_at=delivered_at,
        )

        self.assertEqual(delivered.delivery_status, DELIVERY_STATUS_SENT)
        self.assertEqual(delivered.provider_message_id, "sent-provider-id")
        self.assertEqual(delivered.internet_message_id, "<sent@example.test>")
        self.assertEqual(delivered.sent_or_received_at, delivered_at)
        self.assertEqual(delivered.delivery_error, "")
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.WAITING_CUSTOMER)
        self.assertEqual(self.ticket.first_response_at, delivered_at)
        self.assertEqual(self.ticket.last_message_at, delivered_at)
        self.assertIsNone(self.ticket.resolved_at)
        self.assertIsNone(self.ticket.closed_at)

    def test_failed_reply_records_error_without_advancing_ticket(self) -> None:
        original_last_message_at = self.latest_message.sent_or_received_at
        self.ticket.status = Ticket.Status.OPEN
        self.ticket.last_message_at = original_last_message_at
        self.ticket.save(update_fields=["status", "last_message_at"])
        reply = prepare_ticket_reply(self.ticket, self.user, "Trying this now.")

        mark_ticket_reply_sending(reply)
        self.assertEqual(reply.delivery_status, DELIVERY_STATUS_SENDING)
        fail_ticket_reply(reply, "MicrosoftGraphError: delivery failed")

        reply.refresh_from_db()
        self.ticket.refresh_from_db()
        self.assertEqual(reply.delivery_status, DELIVERY_STATUS_FAILED)
        self.assertEqual(reply.delivery_error, "MicrosoftGraphError: delivery failed")
        self.assertEqual(self.ticket.status, Ticket.Status.OPEN)
        self.assertEqual(self.ticket.last_message_at, original_last_message_at)
        self.assertIsNone(self.ticket.first_response_at)

    def test_complete_reply_requires_provider_message_id(self) -> None:
        reply = prepare_ticket_reply(self.ticket, self.user, "Hello")

        with self.assertRaisesMessage(TicketReplyError, "provider message ID"):
            complete_ticket_reply(reply, provider_message_id="   ")

    def test_prepare_reply_requires_non_empty_body(self) -> None:
        with self.assertRaisesMessage(TicketReplyError, "reply body"):
            prepare_ticket_reply(self.ticket, self.user, "   ")

        self.assertEqual(self.ticket.messages.count(), 2)

    def test_prepare_reply_requires_ticket_mailbox(self) -> None:
        self.ticket.mailbox = None
        self.ticket.save(update_fields=["mailbox"])

        with self.assertRaisesMessage(TicketReplyError, "not linked"):
            prepare_ticket_reply(self.ticket, self.user, "Hello")

    def test_prepare_reply_requires_graph_source_message(self) -> None:
        self.ticket.messages.all().delete()
        TicketMessage.objects.create(
            ticket=self.ticket,
            direction=TicketMessage.Direction.INBOUND,
            sender_name="Web form",
            sender_address="form@example.test",
            subject="Website issue",
            body_text="Form message",
            provider="contact_form",
            provider_message_id="form-message-id",
            sent_or_received_at=timezone.now(),
        )

        with self.assertRaisesMessage(TicketReplyError, "no Microsoft Graph message"):
            prepare_ticket_reply(self.ticket, self.user, "Hello")

    def test_prepare_reply_requires_enabled_mailbox_and_connection(self) -> None:
        self.mailbox.enabled = False
        self.mailbox.save(update_fields=["enabled"])

        with self.assertRaisesMessage(TicketReplyError, "not enabled"):
            prepare_ticket_reply(self.ticket, self.user, "Hello")

        self.mailbox.enabled = True
        self.mailbox.save(update_fields=["enabled"])
        self.connection.enabled = False
        self.connection.save(update_fields=["enabled"])

        with self.assertRaisesMessage(TicketReplyError, "not enabled"):
            prepare_ticket_reply(self.ticket, self.user, "Hello")
