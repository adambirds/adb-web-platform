from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from apps.core.models import Brand
from apps.ticketing.models import Ticket, TicketAttachment, TicketMessage, TicketQueue
from apps.ticketing.services.scanning import AttachmentScanResult
from apps.ticketing.tasks import scan_ticket_attachment_task


class AttachmentScanTaskTests(TestCase):
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
        ticket = Ticket.objects.create(
            brand=brand,
            queue=queue,
            subject="Attachment scanning",
        )
        message = TicketMessage.objects.create(
            ticket=ticket,
            direction=TicketMessage.Direction.INBOUND,
            sender_address="client@example.test",
            provider="microsoft_graph",
            provider_message_id="message-id",
            sent_or_received_at=timezone.now(),
        )
        self.attachment = TicketAttachment.objects.create(
            message=message,
            provider_attachment_id="attachment-id",
            original_filename="attachment.pdf",
            storage_key="ticketing/quarantine/test/attachment.pdf",
            scan_status=TicketAttachment.ScanStatus.PENDING,
            quarantined_at=timezone.now(),
        )

    @patch("apps.ticketing.tasks.default_storage.open")
    @patch("apps.ticketing.tasks.clamav_scanner_from_environment")
    @patch("apps.ticketing.tasks._ticket_attachment_scan_lock")
    def test_clean_attachment_is_released_after_scan(
        self,
        scan_lock: Mock,
        scanner_factory: Mock,
        storage_open: Mock,
    ) -> None:
        scan_lock.return_value.__enter__.return_value = True
        scanner = scanner_factory.return_value
        scanner.engine_name = "clamav"
        scanner.scan.return_value = AttachmentScanResult(clean=True)
        stream = storage_open.return_value.__enter__.return_value

        result = scan_ticket_attachment_task.run(self.attachment.id)

        self.assertEqual(result, 1)
        scanner.scan.assert_called_once_with(stream)
        self.attachment.refresh_from_db()
        self.assertEqual(self.attachment.scan_status, TicketAttachment.ScanStatus.SAFE)
        self.assertEqual(self.attachment.scan_engine, "clamav")
        self.assertEqual(self.attachment.scan_result, "OK")
        self.assertIsNotNone(self.attachment.scanned_at)
        self.assertIsNotNone(self.attachment.safe_at)

    @patch("apps.ticketing.tasks.default_storage.open")
    @patch("apps.ticketing.tasks.clamav_scanner_from_environment")
    @patch("apps.ticketing.tasks._ticket_attachment_scan_lock")
    def test_infected_attachment_remains_quarantined(
        self,
        scan_lock: Mock,
        scanner_factory: Mock,
        storage_open: Mock,
    ) -> None:
        scan_lock.return_value.__enter__.return_value = True
        scanner = scanner_factory.return_value
        scanner.engine_name = "clamav"
        scanner.scan.return_value = AttachmentScanResult(
            clean=False,
            signature="Eicar-Signature",
        )

        result = scan_ticket_attachment_task.run(self.attachment.id)

        self.assertEqual(result, 1)
        self.attachment.refresh_from_db()
        self.assertEqual(
            self.attachment.scan_status,
            TicketAttachment.ScanStatus.INFECTED,
        )
        self.assertEqual(self.attachment.scan_result, "Eicar-Signature")
        self.assertIsNotNone(self.attachment.scanned_at)
        self.assertIsNone(self.attachment.safe_at)
        storage_open.assert_called_once_with(self.attachment.storage_key, "rb")

    @patch("apps.ticketing.tasks.clamav_scanner_from_environment")
    def test_blocked_attachment_is_never_sent_to_scanner(self, scanner_factory: Mock) -> None:
        self.attachment.scan_status = TicketAttachment.ScanStatus.BLOCKED
        self.attachment.storage_key = ""
        self.attachment.save(update_fields=["scan_status", "storage_key"])

        result = scan_ticket_attachment_task.run(self.attachment.id)

        self.assertEqual(result, 0)
        scanner_factory.assert_not_called()
