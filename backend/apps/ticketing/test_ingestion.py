from datetime import datetime
from datetime import timezone as datetime_timezone

from django.test import TestCase
from django.utils import timezone

from apps.clients.models import Client, ClientContact
from apps.core.models import Brand
from apps.ticketing.models import (
    Mailbox,
    MicrosoftGraphConnection,
    Ticket,
    TicketMessage,
    TicketQueue,
)
from apps.ticketing.services.contracts import CanonicalMessage
from apps.ticketing.services.ingestion import ingest_canonical_message
from apps.ticketing.services.normalisation import normalize_message_body


class MessageNormalisationTests(TestCase):
    def test_html_body_is_reduced_to_new_message_content(self) -> None:
        normalised = normalize_message_body(
            body_text="",
            body_html=(
                "<p>Hello Adam,</p><p>The website is down again.</p>"
                "<p>Kind regards,<br>Jane<br>Example Ltd</p>"
            ),
        )

        self.assertEqual(normalised, "Hello Adam,\nThe website is down again.")

    def test_outlook_history_is_removed_conservatively(self) -> None:
        normalised = normalize_message_body(
            body_text=(
                "Thanks, that fixed it.\n\n"
                "From: ADB Support <support@example.test>\n"
                "Sent: 18 August 2026 19:00\n"
                "To: Jane <jane@example.test>\n"
                "Subject: Re: Website issue\n\n"
                "Previous reply"
            ),
            body_html="",
        )

        self.assertEqual(normalised, "Thanks, that fixed it.")

    def test_gmail_style_quote_is_removed(self) -> None:
        normalised = normalize_message_body(
            body_text=(
                "I have attached the screenshot.\n\n"
                "On Tue, 18 Aug 2026 at 19:00, ADB Support <support@example.test> wrote:\n"
                "> Can you send a screenshot?"
            ),
            body_html="",
        )

        self.assertEqual(normalised, "I have attached the screenshot.")


class CanonicalMessageIngestionTests(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="adb-test.example.test",
        )
        self.connection = MicrosoftGraphConnection.objects.create(
            name="Microsoft 365",
            tenant_id="tenant-id",
            client_id="client-id",
        )
        self.support_queue = TicketQueue.objects.create(
            name="Support",
            key="support",
            brand=self.brand,
        )
        self.sales_queue = TicketQueue.objects.create(
            name="Sales",
            key="sales",
            brand=self.brand,
        )
        self.support_mailbox = Mailbox.objects.create(
            graph_connection=self.connection,
            email_address="support@adb-test.example.test",
            brand=self.brand,
            purpose=Mailbox.Purpose.SUPPORT,
            default_queue=self.support_queue,
        )
        self.sales_mailbox = Mailbox.objects.create(
            graph_connection=self.connection,
            email_address="sales@adb-test.example.test",
            brand=self.brand,
            purpose=Mailbox.Purpose.SALES,
            default_queue=self.sales_queue,
        )
        self.client_account = Client.objects.create(
            name="Example Client",
            company="Example Ltd",
            email="hello@example.test",
        )
        self.contact = ClientContact.objects.create(
            client=self.client_account,
            name="Jane Client",
            email="jane@example.test",
            is_primary=True,
        )

    @staticmethod
    def _canonical(
        *,
        provider_message_id: str,
        sender_address: str = "jane@example.test",
        subject: str = "Website issue",
        internet_message_id: str = "",
        in_reply_to: str = "",
        references: tuple[str, ...] = (),
        body_text: str = "Please can you take a look?",
        body_html: str = "",
    ) -> CanonicalMessage:
        return CanonicalMessage(
            provider="microsoft_graph",
            provider_message_id=provider_message_id,
            provider_conversation_id="graph-conversation-id",
            internet_message_id=internet_message_id,
            in_reply_to=in_reply_to,
            references=references,
            sender_name="Jane Client",
            sender_address=sender_address,
            to_recipients=("support@adb-test.example.test",),
            cc_recipients=(),
            bcc_recipients=(),
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            sent_or_received_at=datetime(2026, 8, 18, 19, 30, tzinfo=datetime_timezone.utc),
        )

    def test_known_contact_creates_client_support_ticket(self) -> None:
        result = ingest_canonical_message(
            self.support_mailbox,
            self._canonical(
                provider_message_id="known-contact-message",
                body_text="",
                body_html=(
                    "<p>The website is down.</p><p>Kind regards,<br>Jane Client<br>Example Ltd</p>"
                ),
            ),
        )

        self.assertTrue(result.created)
        self.assertEqual(result.ticket.client, self.client_account)
        self.assertEqual(result.ticket.primary_contact, self.contact)
        self.assertEqual(result.ticket.queue, self.support_queue)
        self.assertEqual(result.ticket.brand, self.brand)
        self.assertEqual(result.ticket.classification, Ticket.Classification.CLIENT_SUPPORT)
        self.assertEqual(result.message.matched_contact, self.contact)
        self.assertEqual(result.message.body_text_normalised, "The website is down.")
        self.assertIn("Kind regards", result.message.body_html)

    def test_client_account_email_links_without_inventing_contact(self) -> None:
        result = ingest_canonical_message(
            self.support_mailbox,
            self._canonical(
                provider_message_id="client-account-message",
                sender_address="HELLO@EXAMPLE.TEST",
            ),
        )

        self.assertEqual(result.ticket.client, self.client_account)
        self.assertIsNone(result.ticket.primary_contact)
        self.assertIsNone(result.message.matched_contact)

    def test_unknown_sales_sender_routes_to_sales_without_becoming_spam(self) -> None:
        result = ingest_canonical_message(
            self.sales_mailbox,
            self._canonical(
                provider_message_id="sales-enquiry",
                sender_address="prospect@example.test",
                subject="New project enquiry",
            ),
        )

        self.assertIsNone(result.ticket.client)
        self.assertEqual(result.ticket.queue, self.sales_queue)
        self.assertEqual(result.ticket.classification, Ticket.Classification.SALES)
        self.assertNotEqual(result.ticket.classification, Ticket.Classification.PROBABLE_SPAM)

    def test_in_reply_to_threads_onto_existing_ticket(self) -> None:
        first = ingest_canonical_message(
            self.support_mailbox,
            self._canonical(
                provider_message_id="thread-first",
                internet_message_id="<thread-first@example.test>",
            ),
        )

        second = ingest_canonical_message(
            self.support_mailbox,
            self._canonical(
                provider_message_id="thread-second",
                internet_message_id="<thread-second@example.test>",
                in_reply_to="<thread-first@example.test>",
                references=("<thread-first@example.test>",),
                subject="Re: Website issue",
            ),
        )

        self.assertEqual(second.ticket, first.ticket)
        self.assertEqual(first.ticket.messages.count(), 2)

    def test_ticket_reference_threads_onto_existing_ticket(self) -> None:
        ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.support_queue,
            mailbox=self.support_mailbox,
            client=self.client_account,
            subject="Existing support issue",
            last_message_at=timezone.now(),
        )

        result = ingest_canonical_message(
            self.support_mailbox,
            self._canonical(
                provider_message_id="ticket-reference-reply",
                subject=f"Re: [{ticket.reference}] Existing support issue",
            ),
        )

        self.assertEqual(result.ticket, ticket)
        self.assertEqual(ticket.messages.count(), 1)

    def test_provider_message_id_makes_replay_idempotent(self) -> None:
        canonical = self._canonical(provider_message_id="replayed-message")

        first = ingest_canonical_message(self.support_mailbox, canonical)
        replay = ingest_canonical_message(self.support_mailbox, canonical)

        self.assertTrue(first.created)
        self.assertFalse(replay.created)
        self.assertEqual(replay.ticket, first.ticket)
        self.assertEqual(replay.message, first.message)
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(TicketMessage.objects.count(), 1)

    def test_customer_reply_reopens_resolved_ticket(self) -> None:
        ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.support_queue,
            mailbox=self.support_mailbox,
            client=self.client_account,
            subject="Resolved support issue",
            status=Ticket.Status.RESOLVED,
            resolved_at=timezone.now(),
            last_message_at=timezone.now(),
        )

        ingest_canonical_message(
            self.support_mailbox,
            self._canonical(
                provider_message_id="resolved-ticket-reply",
                subject=f"Re: [{ticket.reference}] Resolved support issue",
            ),
        )

        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.Status.OPEN)
        self.assertIsNone(ticket.resolved_at)
        self.assertIsNone(ticket.closed_at)
