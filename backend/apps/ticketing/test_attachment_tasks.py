from datetime import datetime
from datetime import timezone as datetime_timezone
from unittest.mock import Mock, patch

from django.test import TestCase

from apps.core.models import Brand
from apps.ticketing.models import Mailbox, MicrosoftGraphConnection, TicketAttachment, TicketQueue
from apps.ticketing.services.attachments import AttachmentPayload
from apps.ticketing.services.contracts import CanonicalMessage
from apps.ticketing.services.graph import MicrosoftGraphAdapter
from apps.ticketing.tasks import _consume_canonical_message


class GraphAttachmentIngestionTaskTests(TestCase):
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
            default_queue=queue,
        )
        self.canonical = CanonicalMessage(
            provider="microsoft_graph",
            provider_message_id="message-id",
            provider_conversation_id="conversation-id",
            internet_message_id="<message@example.test>",
            in_reply_to="",
            references=(),
            sender_name="Client",
            sender_address="client@example.test",
            to_recipients=("support@adb-test.example.test",),
            cc_recipients=(),
            bcc_recipients=(),
            subject="Support request",
            body_html="",
            body_text="Please see attached",
            sent_or_received_at=datetime(
                2026,
                8,
                18,
                19,
                30,
                tzinfo=datetime_timezone.utc,
            ),
            has_attachments=True,
        )
        self.adapter = Mock(spec=MicrosoftGraphAdapter)

    @patch.dict("os.environ", {"TICKETING_MALWARE_SCANNING_ENABLED": "1"})
    @patch("apps.ticketing.tasks.scan_ticket_attachment_task.delay")
    @patch("apps.ticketing.tasks.quarantine_attachment")
    @patch("apps.ticketing.tasks.ingest_canonical_message")
    def test_consumer_quarantines_and_enqueues_graph_attachments(
        self,
        ingest: Mock,
        quarantine: Mock,
        scan_delay: Mock,
    ) -> None:
        stored_message = Mock()
        ingest.return_value.message = stored_message
        attachment = AttachmentPayload(
            provider_attachment_id="attachment-id",
            filename="invoice.pdf",
            content=b"pdf",
        )
        self.adapter.fetch_file_attachments.return_value = (attachment,)
        quarantined = quarantine.return_value.attachment
        quarantined.id = 42
        quarantined.scan_status = TicketAttachment.ScanStatus.PENDING

        _consume_canonical_message(
            self.mailbox,
            self.canonical,
            adapter=self.adapter,
        )

        ingest.assert_called_once_with(self.mailbox, self.canonical)
        self.adapter.fetch_file_attachments.assert_called_once_with(
            self.mailbox,
            "message-id",
        )
        quarantine.assert_called_once_with(stored_message, attachment)
        scan_delay.assert_called_once_with(42)

    @patch("apps.ticketing.tasks.scan_ticket_attachment_task.delay")
    @patch("apps.ticketing.tasks.quarantine_attachment")
    @patch("apps.ticketing.tasks.ingest_canonical_message")
    def test_consumer_keeps_unscanned_attachment_available_when_scanning_is_disabled(
        self,
        ingest: Mock,
        quarantine: Mock,
        scan_delay: Mock,
    ) -> None:
        ingest.return_value.message = Mock()
        attachment = AttachmentPayload(
            provider_attachment_id="attachment-id",
            filename="invoice.pdf",
            content=b"pdf",
        )
        self.adapter.fetch_file_attachments.return_value = (attachment,)
        quarantine.return_value.attachment.scan_status = TicketAttachment.ScanStatus.PENDING

        _consume_canonical_message(self.mailbox, self.canonical, adapter=self.adapter)

        scan_delay.assert_not_called()

    @patch("apps.ticketing.tasks.scan_ticket_attachment_task.delay")
    @patch("apps.ticketing.tasks.quarantine_attachment")
    @patch("apps.ticketing.tasks.ingest_canonical_message")
    def test_consumer_does_not_scan_policy_blocked_attachment(
        self,
        ingest: Mock,
        quarantine: Mock,
        scan_delay: Mock,
    ) -> None:
        ingest.return_value.message = Mock()
        attachment = AttachmentPayload(
            provider_attachment_id="attachment-id",
            filename="large.bin",
            content=b"",
            reported_size=100_000_000,
        )
        self.adapter.fetch_file_attachments.return_value = (attachment,)
        quarantine.return_value.attachment.scan_status = TicketAttachment.ScanStatus.BLOCKED

        _consume_canonical_message(
            self.mailbox,
            self.canonical,
            adapter=self.adapter,
        )

        scan_delay.assert_not_called()

    @patch("apps.ticketing.tasks.scan_ticket_attachment_task.delay")
    @patch("apps.ticketing.tasks.quarantine_attachment")
    @patch("apps.ticketing.tasks.ingest_canonical_message")
    def test_consumer_skips_attachment_request_when_message_has_none(
        self,
        ingest: Mock,
        quarantine: Mock,
        scan_delay: Mock,
    ) -> None:
        canonical = CanonicalMessage(
            provider=self.canonical.provider,
            provider_message_id=self.canonical.provider_message_id,
            provider_conversation_id=self.canonical.provider_conversation_id,
            internet_message_id=self.canonical.internet_message_id,
            in_reply_to=self.canonical.in_reply_to,
            references=self.canonical.references,
            sender_name=self.canonical.sender_name,
            sender_address=self.canonical.sender_address,
            to_recipients=self.canonical.to_recipients,
            cc_recipients=self.canonical.cc_recipients,
            bcc_recipients=self.canonical.bcc_recipients,
            subject=self.canonical.subject,
            body_html=self.canonical.body_html,
            body_text=self.canonical.body_text,
            sent_or_received_at=self.canonical.sent_or_received_at,
            has_attachments=False,
        )

        _consume_canonical_message(self.mailbox, canonical, adapter=self.adapter)

        ingest.assert_called_once_with(self.mailbox, canonical)
        self.adapter.fetch_file_attachments.assert_not_called()
        quarantine.assert_not_called()
        scan_delay.assert_not_called()
