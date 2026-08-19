from datetime import datetime
from datetime import timezone as datetime_timezone

from django.test import TestCase

from apps.core.models import Brand
from apps.ticketing.models import Mailbox, MicrosoftGraphConnection, Ticket, TicketQueue
from apps.ticketing.services.contracts import CanonicalMessage
from apps.ticketing.services.ingestion import ingest_canonical_message


class ClassificationIngestionTests(TestCase):
    def setUp(self) -> None:
        brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="adb-test.example.test",
        )
        queue = TicketQueue.objects.create(
            name="Support",
            key="support",
            brand=brand,
            default_priority=Ticket.Priority.NORMAL,
        )
        connection = MicrosoftGraphConnection.objects.create(
            name="Microsoft 365",
            tenant_id="tenant-id",
            client_id="client-id",
        )
        self.mailbox = Mailbox.objects.create(
            graph_connection=connection,
            email_address="support@adb-test.example.test",
            brand=brand,
            purpose=Mailbox.Purpose.SUPPORT,
            default_queue=queue,
        )

    @staticmethod
    def _canonical(
        provider_message_id: str,
        *,
        sender_address: str,
        subject: str,
        body_text: str,
    ) -> CanonicalMessage:
        return CanonicalMessage(
            provider="microsoft_graph",
            provider_message_id=provider_message_id,
            provider_conversation_id="conversation-id",
            internet_message_id=f"<{provider_message_id}@example.test>",
            in_reply_to="",
            references=(),
            sender_name="Unknown Sender",
            sender_address=sender_address,
            to_recipients=("support@adb-test.example.test",),
            cc_recipients=(),
            bcc_recipients=(),
            subject=subject,
            body_html="",
            body_text=body_text,
            sent_or_received_at=datetime(
                2026,
                8,
                19,
                0,
                45,
                tzinfo=datetime_timezone.utc,
            ),
        )

    def test_probable_spam_is_low_priority_but_remains_a_normal_ticket(self) -> None:
        result = ingest_canonical_message(
            self.mailbox,
            self._canonical(
                "spam-message",
                sender_address="sales@unknown.example.test",
                subject="Guest post opportunity",
                body_text="We provide guest post placements and link building packages.",
            ),
        )

        self.assertEqual(result.ticket.classification, Ticket.Classification.PROBABLE_SPAM)
        self.assertEqual(result.ticket.priority, Ticket.Priority.LOW)
        self.assertEqual(result.ticket.status, Ticket.Status.NEW)

    def test_monitoring_message_keeps_queue_default_priority(self) -> None:
        result = ingest_canonical_message(
            self.mailbox,
            self._canonical(
                "monitoring-message",
                sender_address="alerts@monitoring.example.test",
                subject="[Alert] Origin unreachable",
                body_text="The origin server is not responding.",
            ),
        )

        self.assertEqual(result.ticket.classification, Ticket.Classification.MONITORING)
        self.assertEqual(result.ticket.priority, Ticket.Priority.NORMAL)
