from datetime import datetime
from datetime import timezone as datetime_timezone

from django.test import TestCase

from apps.clients.models import Client
from apps.core.models import Brand
from apps.ticketing.models import Mailbox, MicrosoftGraphConnection, Ticket, TicketQueue
from apps.ticketing.services.classification import classify_message
from apps.ticketing.services.contracts import CanonicalMessage


class TicketClassificationTests(TestCase):
    def setUp(self) -> None:
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
            email_address="support@adb-test.example.test",
            brand=self.brand,
            purpose=Mailbox.Purpose.SUPPORT,
            default_queue=self.queue,
        )
        self.client_account = Client.objects.create(
            name="Known Client",
            email="client@example.test",
        )

    @staticmethod
    def _canonical(
        *,
        sender_address: str = "unknown@example.test",
        subject: str = "Question",
        body_text: str = "Hello",
        body_html: str = "",
    ) -> CanonicalMessage:
        return CanonicalMessage(
            provider="microsoft_graph",
            provider_message_id="message-id",
            provider_conversation_id="conversation-id",
            internet_message_id="<message@example.test>",
            in_reply_to="",
            references=(),
            sender_name="Sender",
            sender_address=sender_address,
            to_recipients=("support@adb-test.example.test",),
            cc_recipients=(),
            bcc_recipients=(),
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            sent_or_received_at=datetime(
                2026,
                8,
                19,
                0,
                30,
                tzinfo=datetime_timezone.utc,
            ),
        )

    def test_known_client_is_never_promoted_to_probable_spam_by_content(self) -> None:
        decision = classify_message(
            self.mailbox,
            self._canonical(body_text="Guest post and SEO services proposal"),
            self.client_account,
        )

        self.assertEqual(decision.classification, Ticket.Classification.CLIENT_SUPPORT)
        self.assertEqual(decision.score, 100)
        self.assertIn("known_client", decision.reasons)

    def test_unknown_sender_requires_multiple_spam_indicators(self) -> None:
        one_indicator = classify_message(
            self.mailbox,
            self._canonical(body_text="We offer guest post placements"),
            None,
        )
        multiple_indicators = classify_message(
            self.mailbox,
            self._canonical(body_text="Guest post placements and link building packages"),
            None,
        )

        self.assertEqual(one_indicator.classification, Ticket.Classification.UNKNOWN)
        self.assertEqual(
            multiple_indicators.classification,
            Ticket.Classification.PROBABLE_SPAM,
        )
        self.assertEqual(multiple_indicators.suggested_priority, Ticket.Priority.LOW)
        self.assertGreaterEqual(multiple_indicators.score, 80)

    def test_monitoring_sender_is_classified_without_being_marked_spam(self) -> None:
        decision = classify_message(
            self.mailbox,
            self._canonical(
                sender_address="alerts@monitoring.example.test",
                subject="[Alert] Website response time",
            ),
            None,
        )

        self.assertEqual(decision.classification, Ticket.Classification.MONITORING)
        self.assertIn("monitoring_subject", decision.reasons)

    def test_no_reply_sender_is_automated_system(self) -> None:
        decision = classify_message(
            self.mailbox,
            self._canonical(sender_address="no-reply@example.test"),
            None,
        )

        self.assertEqual(decision.classification, Ticket.Classification.AUTOMATED_SYSTEM)
        self.assertEqual(decision.reasons, ("automated_sender:no-reply",))

    def test_newsletter_requires_marketing_context_with_unsubscribe(self) -> None:
        decision = classify_message(
            self.mailbox,
            self._canonical(
                subject="August newsletter",
                body_text="View in browser. Unsubscribe from future updates.",
            ),
            None,
        )

        self.assertEqual(
            decision.classification,
            Ticket.Classification.NEWSLETTER_MARKETING,
        )
        self.assertEqual(decision.suggested_priority, Ticket.Priority.LOW)

    def test_sales_mailbox_remains_default_for_unknown_non_spam_sender(self) -> None:
        self.mailbox.purpose = Mailbox.Purpose.SALES
        self.mailbox.save(update_fields=["purpose"])

        decision = classify_message(
            self.mailbox,
            self._canonical(subject="New project enquiry"),
            None,
        )

        self.assertEqual(decision.classification, Ticket.Classification.SALES)
        self.assertEqual(decision.reasons, ("sales_mailbox",))
