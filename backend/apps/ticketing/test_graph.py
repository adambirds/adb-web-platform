from datetime import datetime, timezone as datetime_timezone
from unittest.mock import Mock

import requests
from django.test import TestCase

from apps.core.models import Brand
from apps.ticketing.models import Mailbox, MicrosoftGraphConnection, TicketQueue
from apps.ticketing.services.contracts import CanonicalMessage
from apps.ticketing.services.graph import (
    GRAPH_API_ROOT,
    GraphDeltaPage,
    MicrosoftGraphAdapter,
    MicrosoftGraphError,
    sync_graph_mailbox,
)


class MicrosoftGraphAdapterTests(TestCase):
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
            email_address="Support@ADB-Test.Example.Test",
            graph_user_id="mailbox-object-id",
            brand=self.brand,
            default_queue=self.queue,
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

    def test_delta_page_maps_graph_message_to_canonical_contract(self) -> None:
        next_link = f"{GRAPH_API_ROOT}/users/mailbox/messages/delta?$skiptoken=next"
        self.session.get.return_value = self._response(
            {
                "value": [
                    {"id": "deleted-message", "@removed": {"reason": "deleted"}},
                    {
                        "id": "immutable-message-id",
                        "conversationId": "conversation-id",
                        "subject": "Re: Website issue",
                        "body": {"contentType": "html", "content": "<p>Hello Adam</p>"},
                        "from": {
                            "emailAddress": {
                                "name": "Client User",
                                "address": "CLIENT@EXAMPLE.TEST",
                            }
                        },
                        "toRecipients": [
                            {"emailAddress": {"address": "SUPPORT@ADB-TEST.EXAMPLE.TEST"}}
                        ],
                        "ccRecipients": [
                            {"emailAddress": {"address": "OTHER@EXAMPLE.TEST"}}
                        ],
                        "bccRecipients": [],
                        "receivedDateTime": "2026-08-18T19:30:00Z",
                        "internetMessageId": "<message@example.test>",
                        "internetMessageHeaders": [
                            {"name": "In-Reply-To", "value": "<previous@example.test>"},
                            {
                                "name": "References",
                                "value": "<first@example.test> <previous@example.test>",
                            },
                        ],
                        "hasAttachments": True,
                    },
                ],
                "@odata.nextLink": next_link,
            }
        )

        page = self.adapter.fetch_delta_page(self.mailbox)

        self.assertEqual(page.next_link, next_link)
        self.assertEqual(page.delta_link, "")
        self.assertEqual(len(page.messages), 1)
        message = page.messages[0]
        self.assertEqual(message.provider_message_id, "immutable-message-id")
        self.assertEqual(message.provider_conversation_id, "conversation-id")
        self.assertEqual(message.internet_message_id, "<message@example.test>")
        self.assertEqual(message.in_reply_to, "<previous@example.test>")
        self.assertEqual(
            message.references,
            ("<first@example.test>", "<previous@example.test>"),
        )
        self.assertEqual(message.sender_name, "Client User")
        self.assertEqual(message.sender_address, "client@example.test")
        self.assertEqual(message.to_recipients, ("support@adb-test.example.test",))
        self.assertEqual(message.cc_recipients, ("other@example.test",))
        self.assertEqual(message.body_html, "<p>Hello Adam</p>")
        self.assertEqual(message.body_text, "")
        self.assertTrue(message.has_attachments)
        self.assertEqual(
            message.sent_or_received_at,
            datetime(2026, 8, 18, 19, 30, tzinfo=datetime_timezone.utc),
        )

        _url, kwargs = self.session.get.call_args
        self.assertEqual(kwargs["params"]["$top"], 50)
        self.assertIn("internetMessageHeaders", kwargs["params"]["$select"])
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-access-token")
        self.assertIn('IdType="ImmutableId"', kwargs["headers"]["Prefer"])

    def test_delta_page_uses_saved_delta_url_without_reapplying_query(self) -> None:
        delta_link = f"{GRAPH_API_ROOT}/users/mailbox/messages/delta?$deltatoken=current"
        next_delta_link = f"{GRAPH_API_ROOT}/users/mailbox/messages/delta?$deltatoken=next"
        self.session.get.return_value = self._response(
            {"value": [], "@odata.deltaLink": next_delta_link}
        )

        page = self.adapter.fetch_delta_page(self.mailbox, url=delta_link)

        self.assertEqual(page.delta_link, next_delta_link)
        _url, kwargs = self.session.get.call_args
        self.assertIsNone(kwargs["params"])

    def test_delta_page_refuses_non_graph_continuation_url(self) -> None:
        with self.assertRaisesMessage(
            MicrosoftGraphError,
            "Refusing to send credentials to a non-Graph URL.",
        ):
            self.adapter.fetch_delta_page(
                self.mailbox,
                url="https://attacker.example.test/steal-token",
            )

        self.session.get.assert_not_called()


class GraphMailboxSyncTests(TestCase):
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
            email_address="support@adb-test.example.test",
            brand=brand,
            default_queue=queue,
        )
        self.message = CanonicalMessage(
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
            body_text="Hello",
            sent_or_received_at=datetime(2026, 8, 18, 19, 30, tzinfo=datetime_timezone.utc),
        )

    def test_sync_consumes_every_page_before_checkpointing_delta_link(self) -> None:
        adapter = Mock(spec=MicrosoftGraphAdapter)
        first_next_link = f"{GRAPH_API_ROOT}/users/mailbox/messages/delta?$skiptoken=next"
        final_delta_link = f"{GRAPH_API_ROOT}/users/mailbox/messages/delta?$deltatoken=done"
        adapter.fetch_delta_page.side_effect = [
            GraphDeltaPage(messages=(self.message,), next_link=first_next_link, delta_link=""),
            GraphDeltaPage(messages=(self.message,), next_link="", delta_link=final_delta_link),
        ]
        consumer = Mock()

        processed = sync_graph_mailbox(self.mailbox, adapter, consumer)

        self.assertEqual(processed, 2)
        self.assertEqual(consumer.call_count, 2)
        self.mailbox.refresh_from_db()
        self.assertEqual(self.mailbox.delta_link, final_delta_link)
        self.assertIsNotNone(self.mailbox.last_synced_at)
        self.assertIsNotNone(self.mailbox.last_successful_sync_at)
        self.assertEqual(self.mailbox.last_error, "")
        self.assertEqual(
            adapter.fetch_delta_page.call_args_list[0].kwargs["url"],
            "",
        )
        self.assertEqual(
            adapter.fetch_delta_page.call_args_list[1].kwargs["url"],
            first_next_link,
        )

    def test_sync_does_not_checkpoint_delta_link_when_consumer_fails(self) -> None:
        existing_delta_link = (
            f"{GRAPH_API_ROOT}/users/mailbox/messages/delta?$deltatoken=existing"
        )
        self.mailbox.delta_link = existing_delta_link
        self.mailbox.save(update_fields=["delta_link"])
        adapter = Mock(spec=MicrosoftGraphAdapter)
        adapter.fetch_delta_page.return_value = GraphDeltaPage(
            messages=(self.message,),
            next_link="",
            delta_link=f"{GRAPH_API_ROOT}/users/mailbox/messages/delta?$deltatoken=new",
        )
        consumer = Mock(side_effect=RuntimeError("consumer failed"))

        with self.assertRaisesMessage(RuntimeError, "consumer failed"):
            sync_graph_mailbox(self.mailbox, adapter, consumer)

        self.mailbox.refresh_from_db()
        self.assertEqual(self.mailbox.delta_link, existing_delta_link)
        self.assertIsNotNone(self.mailbox.last_synced_at)
        self.assertIsNone(self.mailbox.last_successful_sync_at)
        self.assertIn("RuntimeError: consumer failed", self.mailbox.last_error)

    def test_disabled_mailbox_is_not_synced(self) -> None:
        self.mailbox.enabled = False
        self.mailbox.save(update_fields=["enabled"])
        adapter = Mock(spec=MicrosoftGraphAdapter)
        consumer = Mock()

        processed = sync_graph_mailbox(self.mailbox, adapter, consumer)

        self.assertEqual(processed, 0)
        adapter.fetch_delta_page.assert_not_called()
        consumer.assert_not_called()
