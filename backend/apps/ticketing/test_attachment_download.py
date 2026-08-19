from collections.abc import Iterable
from tempfile import TemporaryDirectory
from typing import cast
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import StreamingHttpResponse
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile, TicketQueueAccessGrant
from apps.clients.models import Client
from apps.core.models import Brand
from apps.ticketing.models import Ticket, TicketAttachment, TicketMessage, TicketQueue
from authentication.models import User


class TicketAttachmentDownloadTests(TestCase):
    def setUp(self) -> None:
        self.media_directory = TemporaryDirectory()
        self.addCleanup(self.media_directory.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

        self.user = User.objects.create_user(
            email="agent@example.test",
            password="not-a-real-password",
            first_name="Support",
            last_name="Agent",
            is_staff=True,
        )
        profile = StaffAccessProfile.objects.create(user=self.user)
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
        ClientAccessGrant.objects.create(profile=profile, client=self.client_account)
        TicketQueueAccessGrant.objects.create(profile=profile, queue=self.queue)
        self._grant("view_ticket", "view_ticket_attachment")
        self.client.force_login(self.user)

        self.ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue,
            client=self.client_account,
            subject="Safe attachment",
        )
        self.message = TicketMessage.objects.create(
            ticket=self.ticket,
            direction=TicketMessage.Direction.INBOUND,
            sender_address="client@example.test",
            provider="microsoft_graph",
            provider_message_id="message-id",
            sent_or_received_at=timezone.now(),
        )
        storage_key = default_storage.save(
            "ticketing/quarantine/test/invoice.pdf",
            ContentFile(b"safe attachment bytes"),
        )
        self.attachment = TicketAttachment.objects.create(
            message=self.message,
            provider_attachment_id="attachment-id",
            original_filename="invoice.pdf",
            storage_key=storage_key,
            detected_content_type="application/pdf",
            size=21,
            scan_status=TicketAttachment.ScanStatus.SAFE,
            quarantined_at=timezone.now(),
            scanned_at=timezone.now(),
            safe_at=timezone.now(),
        )

    def _grant(self, *codenames: str) -> None:
        permissions = Permission.objects.filter(
            content_type__app_label="ticketing",
            codename__in=codenames,
        )
        self.user.user_permissions.add(*permissions)

    def test_safe_attachment_is_streamed_as_download(self) -> None:
        response = self.client.get(f"/api/admin/ticket-attachments/{self.attachment.id}/download")

        self.assertEqual(response.status_code, 200)
        streaming_response = cast(StreamingHttpResponse, response)
        streaming_content = cast(Iterable[bytes], streaming_response.streaming_content)
        self.assertEqual(b"".join(streaming_content), b"safe attachment bytes")
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("invoice.pdf", response["Content-Disposition"])
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_pending_attachment_is_downloadable_when_scanning_is_disabled(self) -> None:
        self.attachment.scan_status = TicketAttachment.ScanStatus.PENDING
        self.attachment.safe_at = None
        self.attachment.save(update_fields=["scan_status", "safe_at"])

        response = self.client.get(f"/api/admin/ticket-attachments/{self.attachment.id}/download")

        self.assertEqual(response.status_code, 200)

    @patch.dict("os.environ", {"TICKETING_MALWARE_SCANNING_ENABLED": "1"})
    def test_pending_attachment_is_not_downloadable_when_scanning_is_enabled(self) -> None:
        self.attachment.scan_status = TicketAttachment.ScanStatus.PENDING
        self.attachment.safe_at = None
        self.attachment.save(update_fields=["scan_status", "safe_at"])

        response = self.client.get(f"/api/admin/ticket-attachments/{self.attachment.id}/download")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "attachment_not_safe")

    def test_infected_attachment_is_never_downloadable(self) -> None:
        self.attachment.scan_status = TicketAttachment.ScanStatus.INFECTED
        self.attachment.safe_at = None
        self.attachment.save(update_fields=["scan_status", "safe_at"])

        response = self.client.get(f"/api/admin/ticket-attachments/{self.attachment.id}/download")

        self.assertEqual(response.status_code, 409)

    def test_attachment_permission_is_required(self) -> None:
        self.user.user_permissions.remove(
            Permission.objects.get(
                content_type__app_label="ticketing",
                codename="view_ticket_attachment",
            )
        )

        response = self.client.get(f"/api/admin/ticket-attachments/{self.attachment.id}/download")

        self.assertEqual(response.status_code, 403)

    def test_attachment_outside_client_scope_is_hidden(self) -> None:
        hidden_ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue,
            client=self.other_client,
            subject="Hidden attachment",
        )
        hidden_message = TicketMessage.objects.create(
            ticket=hidden_ticket,
            direction=TicketMessage.Direction.INBOUND,
            sender_address="other@example.test",
            provider="microsoft_graph",
            provider_message_id="hidden-message-id",
            sent_or_received_at=timezone.now(),
        )
        hidden_attachment = TicketAttachment.objects.create(
            message=hidden_message,
            provider_attachment_id="hidden-attachment-id",
            original_filename="hidden.pdf",
            storage_key=self.attachment.storage_key,
            scan_status=TicketAttachment.ScanStatus.SAFE,
            scanned_at=timezone.now(),
            safe_at=timezone.now(),
        )

        response = self.client.get(f"/api/admin/ticket-attachments/{hidden_attachment.id}/download")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "not_found")
