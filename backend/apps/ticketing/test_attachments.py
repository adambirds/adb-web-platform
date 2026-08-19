import hashlib
from tempfile import TemporaryDirectory

from django.core.files.storage import FileSystemStorage
from django.test import TestCase
from django.utils import timezone

from apps.core.models import Brand
from apps.ticketing.models import Ticket, TicketAttachment, TicketMessage, TicketQueue
from apps.ticketing.services.attachments import (
    AttachmentPayload,
    AttachmentQuarantineError,
    quarantine_attachment,
)


class AttachmentQuarantineTests(TestCase):
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
        self.ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue,
            subject="Attachment test",
        )
        self.message = TicketMessage.objects.create(
            ticket=self.ticket,
            direction=TicketMessage.Direction.INBOUND,
            sender_address="client@example.test",
            body_text="Attached",
            provider="microsoft_graph",
            provider_message_id="message-id",
            sent_or_received_at=timezone.now(),
        )
        self.temp_directory = TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.storage = FileSystemStorage(location=self.temp_directory.name)

    def test_quarantine_sanitises_filename_and_records_security_metadata(self) -> None:
        content = b"%PDF-1.7\nnot-a-real-pdf"

        result = quarantine_attachment(
            self.message,
            AttachmentPayload(
                provider_attachment_id="attachment-1",
                filename="../../private/invoice?.pdf",
                content=content,
                declared_content_type="application/pdf",
                reported_size=len(content),
                content_id="invoice-content-id",
                is_inline=True,
            ),
            storage=self.storage,
        )

        self.assertTrue(result.created)
        attachment = result.attachment
        self.assertEqual(attachment.original_filename, "invoice_.pdf")
        self.assertEqual(attachment.detected_content_type, "application/pdf")
        self.assertEqual(attachment.declared_content_type, "application/pdf")
        self.assertEqual(attachment.sha256, hashlib.sha256(content).hexdigest())
        self.assertEqual(attachment.size, len(content))
        self.assertEqual(attachment.scan_status, TicketAttachment.ScanStatus.PENDING)
        self.assertEqual(attachment.content_id, "invoice-content-id")
        self.assertTrue(attachment.is_inline)
        self.assertIsNotNone(attachment.quarantined_at)
        self.assertTrue(self.storage.exists(attachment.storage_key))
        self.assertTrue(attachment.storage_key.startswith("ticketing/quarantine/"))

    def test_quarantine_is_idempotent_for_provider_attachment_id(self) -> None:
        first = quarantine_attachment(
            self.message,
            AttachmentPayload(
                provider_attachment_id="attachment-1",
                filename="first.txt",
                content=b"first",
            ),
            storage=self.storage,
        )
        second = quarantine_attachment(
            self.message,
            AttachmentPayload(
                provider_attachment_id="attachment-1",
                filename="second.txt",
                content=b"second",
            ),
            storage=self.storage,
        )

        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(second.attachment.id, first.attachment.id)
        self.assertEqual(TicketAttachment.objects.count(), 1)
        self.assertEqual(second.attachment.original_filename, "first.txt")

    def test_quarantine_rejects_actual_or_reported_oversized_content(self) -> None:
        with self.assertRaisesMessage(AttachmentQuarantineError, "exceeds"):
            quarantine_attachment(
                self.message,
                AttachmentPayload(
                    provider_attachment_id="attachment-1",
                    filename="large.bin",
                    content=b"1234",
                ),
                storage=self.storage,
                max_bytes=3,
            )

        with self.assertRaisesMessage(AttachmentQuarantineError, "exceeds"):
            quarantine_attachment(
                self.message,
                AttachmentPayload(
                    provider_attachment_id="attachment-2",
                    filename="reported-large.bin",
                    content=b"12",
                    reported_size=4,
                ),
                storage=self.storage,
                max_bytes=3,
            )

        self.assertEqual(TicketAttachment.objects.count(), 0)

    def test_quarantine_requires_provider_attachment_id(self) -> None:
        with self.assertRaisesMessage(AttachmentQuarantineError, "provider attachment ID"):
            quarantine_attachment(
                self.message,
                AttachmentPayload(
                    provider_attachment_id="  ",
                    filename="file.txt",
                    content=b"safe",
                ),
                storage=self.storage,
            )
