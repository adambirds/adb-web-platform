import base64
from unittest.mock import Mock

import requests
from django.test import TestCase

from apps.core.models import Brand
from apps.ticketing.models import Mailbox, MicrosoftGraphConnection, TicketQueue
from apps.ticketing.services.graph import (
    GRAPH_API_ROOT,
    MicrosoftGraphAdapter,
    MicrosoftGraphPayloadError,
)


class MicrosoftGraphAttachmentTests(TestCase):
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
            email_address="Support@ADB-Test.Example.Test",
            graph_user_id="mailbox-object-id",
            brand=brand,
            default_queue=queue,
        )
        self.session = Mock(spec=requests.Session)
        self.adapter = MicrosoftGraphAdapter(
            lambda: "test-access-token",
            session=self.session,
            timeout_seconds=5,
        )

    @staticmethod
    def _response(payload: dict[str, object], status_code: int = 200) -> Mock:
        response = Mock()
        response.status_code = status_code
        response.headers = {}
        response.json.return_value = payload
        return response

    def test_fetch_file_attachments_loads_content_and_skips_non_file_types(self) -> None:
        content = b"%PDF-1.7\nattachment"
        self.session.get.side_effect = [
            self._response(
                {
                    "value": [
                        {
                            "@odata.type": "#microsoft.graph.fileAttachment",
                            "id": "file-attachment-id",
                        },
                        {
                            "@odata.type": "#microsoft.graph.itemAttachment",
                            "id": "item-attachment-id",
                        },
                    ]
                }
            ),
            self._response(
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "id": "file-attachment-id",
                    "name": "invoice.pdf",
                    "contentType": "application/pdf",
                    "size": len(content),
                    "isInline": True,
                    "contentId": "invoice-content-id",
                    "contentBytes": base64.b64encode(content).decode("ascii"),
                }
            ),
        ]

        attachments = self.adapter.fetch_file_attachments(
            self.mailbox,
            "immutable-message-id",
        )

        self.assertEqual(len(attachments), 1)
        attachment = attachments[0]
        self.assertEqual(attachment.provider_attachment_id, "file-attachment-id")
        self.assertEqual(attachment.filename, "invoice.pdf")
        self.assertEqual(attachment.content, content)
        self.assertEqual(attachment.declared_content_type, "application/pdf")
        self.assertEqual(attachment.reported_size, len(content))
        self.assertEqual(attachment.content_id, "invoice-content-id")
        self.assertTrue(attachment.is_inline)
        self.assertEqual(self.session.get.call_count, 2)
        list_url = self.session.get.call_args_list[0].args[0]
        detail_url = self.session.get.call_args_list[1].args[0]
        self.assertEqual(
            list_url,
            f"{GRAPH_API_ROOT}/users/mailbox-object-id/messages/immutable-message-id/attachments",
        )
        self.assertEqual(
            detail_url,
            f"{list_url}/file-attachment-id",
        )

    def test_fetch_file_attachments_skips_content_request_for_oversized_file(self) -> None:
        self.session.get.return_value = self._response(
            {
                "value": [
                    {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "id": "large-attachment-id",
                        "name": "archive.zip",
                        "contentType": "application/zip",
                        "size": 4,
                        "isInline": False,
                    }
                ]
            }
        )

        attachments = self.adapter.fetch_file_attachments(
            self.mailbox,
            "message-id",
            max_bytes=3,
        )

        self.assertEqual(len(attachments), 1)
        attachment = attachments[0]
        self.assertEqual(attachment.provider_attachment_id, "large-attachment-id")
        self.assertEqual(attachment.filename, "archive.zip")
        self.assertEqual(attachment.declared_content_type, "application/zip")
        self.assertEqual(attachment.reported_size, 4)
        self.assertEqual(attachment.content, b"")
        self.assertEqual(self.session.get.call_count, 1)

    def test_fetch_file_attachments_uses_normalised_mailbox_address_without_graph_id(self) -> None:
        self.mailbox.graph_user_id = ""
        self.mailbox.save(update_fields=["graph_user_id"])
        self.session.get.return_value = self._response({"value": []})

        attachments = self.adapter.fetch_file_attachments(self.mailbox, "message-id")

        self.assertEqual(attachments, ())
        request_url = self.session.get.call_args.args[0]
        self.assertIn("/users/support%40adb-test.example.test/", request_url)

    def test_fetch_file_attachments_rejects_invalid_content_bytes(self) -> None:
        self.session.get.side_effect = [
            self._response(
                {
                    "value": [
                        {
                            "@odata.type": "#microsoft.graph.fileAttachment",
                            "id": "file-attachment-id",
                        }
                    ]
                }
            ),
            self._response(
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "id": "file-attachment-id",
                    "name": "broken.bin",
                    "size": 10,
                    "contentBytes": "not valid base64!",
                }
            ),
        ]

        with self.assertRaisesMessage(
            MicrosoftGraphPayloadError,
            "invalid file attachment content",
        ):
            self.adapter.fetch_file_attachments(self.mailbox, "message-id")
