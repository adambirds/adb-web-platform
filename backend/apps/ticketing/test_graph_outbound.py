from unittest.mock import Mock

import requests
from django.test import TestCase

from apps.core.models import Brand
from apps.ticketing.models import Mailbox, MicrosoftGraphConnection, TicketQueue
from apps.ticketing.services.graph import GRAPH_API_ROOT, MicrosoftGraphError
from apps.ticketing.services.graph_outbound import MicrosoftGraphOutboundAdapter


class MicrosoftGraphOutboundAdapterTests(TestCase):
    def setUp(self) -> None:
        brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="adb-test.example.test",
        )
        queue = TicketQueue.objects.create(name="Support", key="support", brand=brand)
        connection = MicrosoftGraphConnection.objects.create(
            name="Microsoft 365",
            tenant_id="tenant-id",
            client_id="client-id",
        )
        self.mailbox = Mailbox.objects.create(
            graph_connection=connection,
            email_address="Support@ADB-Test.Example.Test",
            brand=brand,
            default_queue=queue,
        )
        self.session = Mock(spec=requests.Session)
        self.adapter = MicrosoftGraphOutboundAdapter(
            lambda: "access-token",
            session=self.session,
            timeout_seconds=5,
        )

    @staticmethod
    def _response(payload: object, status_code: int) -> Mock:
        response = Mock(spec=requests.Response)
        response.status_code = status_code
        response.headers = {}
        response.json.return_value = payload
        return response

    def test_send_reply_creates_updates_and_sends_threaded_draft(self) -> None:
        draft_response = self._response(
            {
                "id": "immutable-draft-id",
                "internetMessageId": "<outbound@example.test>",
                "conversationId": "conversation-id",
            },
            201,
        )
        patch_response = self._response({"id": "immutable-draft-id"}, 200)
        send_response = self._response({}, 202)
        self.session.request.side_effect = [draft_response, patch_response, send_response]

        receipt = self.adapter.send_reply(
            self.mailbox,
            "source/message=id",
            ticket_reference="ADB-ABC123",
            ticket_subject="Re: Website issue",
            body_html="<p>We have fixed this.</p>",
            cc_recipients=(" CC@Example.Test ", "cc@example.test"),
            bcc_recipients=("audit@example.test",),
        )

        self.assertEqual(receipt.provider_message_id, "immutable-draft-id")
        self.assertEqual(receipt.internet_message_id, "<outbound@example.test>")
        self.assertEqual(receipt.provider_conversation_id, "conversation-id")

        create_call, patch_call, send_call = self.session.request.call_args_list
        mailbox_root = f"{GRAPH_API_ROOT}/users/support%40adb-test.example.test/messages"
        self.assertEqual(create_call.args[:2], ("post", f"{mailbox_root}/source%2Fmessage%3Did/createReply"))
        self.assertEqual(
            create_call.kwargs["json"],
            {
                "message": {
                    "body": {
                        "contentType": "HTML",
                        "content": "<p>We have fixed this.</p>",
                    }
                }
            },
        )
        self.assertEqual(
            patch_call.args[:2],
            ("patch", f"{mailbox_root}/immutable-draft-id"),
        )
        self.assertEqual(patch_call.kwargs["json"]["subject"], "Re: [ADB-ABC123] Website issue")
        self.assertEqual(
            patch_call.kwargs["json"]["ccRecipients"],
            [{"emailAddress": {"address": "cc@example.test"}}],
        )
        self.assertEqual(
            patch_call.kwargs["json"]["bccRecipients"],
            [{"emailAddress": {"address": "audit@example.test"}}],
        )
        self.assertEqual(
            send_call.args[:2],
            ("post", f"{mailbox_root}/immutable-draft-id/send"),
        )
        self.assertIsNone(send_call.kwargs["json"])
        for request_call in self.session.request.call_args_list:
            self.assertEqual(
                request_call.kwargs["headers"]["Authorization"],
                "Bearer access-token",
            )
            self.assertEqual(
                request_call.kwargs["headers"]["Prefer"],
                'IdType="ImmutableId"',
            )

    def test_send_reply_requires_provider_message_id(self) -> None:
        with self.assertRaisesMessage(MicrosoftGraphError, "provider message ID"):
            self.adapter.send_reply(
                self.mailbox,
                "",
                ticket_reference="ADB-ABC123",
                ticket_subject="Website issue",
                body_text="Hello",
            )

        self.session.request.assert_not_called()

    def test_send_reply_rejects_graph_delivery_failure(self) -> None:
        failed_response = self._response({}, 403)
        failed_response.headers = {"request-id": "request-id"}
        self.session.request.return_value = failed_response

        with self.assertRaisesMessage(
            MicrosoftGraphError,
            "status 403 (request ID request-id)",
        ):
            self.adapter.send_reply(
                self.mailbox,
                "source-id",
                ticket_reference="ADB-ABC123",
                ticket_subject="Website issue",
                body_text="Hello",
            )
