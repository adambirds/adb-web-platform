from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

from asgiref.sync import async_to_sync
from django.contrib.auth.models import Permission
from django.db import transaction
from django.test import TestCase, override_settings
from redis.exceptions import ConnectionError as RedisConnectionError

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile, TicketQueueAccessGrant
from apps.clients.models import Client
from apps.core.live.events import LiveChange, can_receive, publish_change
from apps.core.live.signals import change_for
from apps.core.live.views import stream, stream_user
from apps.ticketing.models import TicketQueue
from authentication.models import User


class LiveEventsTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="live@example.test",
            password="test",
            first_name="Live",
            last_name="Staff",
            is_staff=True,
        )
        self.account = Client.objects.create(name="A", email="a@example.test")
        self.other = Client.objects.create(name="B", email="b@example.test")
        self.profile = StaffAccessProfile.objects.create(user=self.user)
        self.permission = Permission.objects.get(
            content_type__app_label="clients", codename="view_client"
        )
        self.user.user_permissions.add(self.permission)
        ClientAccessGrant.objects.create(profile=self.profile, client=self.account)

    def test_client_scope_and_capability_are_both_required(self) -> None:
        allowed = LiveChange("clients", ("clients.view_client",), client_id=self.account.pk)
        self.assertTrue(can_receive(self.user, allowed))
        self.assertFalse(
            can_receive(
                self.user, LiveChange("clients", allowed.permissions, client_id=self.other.pk)
            )
        )
        self.assertFalse(
            can_receive(
                self.user,
                LiveChange("clients", ("clients.change_client",), client_id=self.account.pk),
            )
        )
        self.assertFalse(can_receive(self.user, LiveChange("clients", allowed.permissions)))

    def test_ticket_queue_scope_is_required(self) -> None:
        queue = TicketQueue.objects.create(name="Live queue")
        event = LiveChange("tickets", client_id=self.account.pk, queue_id=queue.pk)
        self.assertFalse(can_receive(self.user, event))
        TicketQueueAccessGrant.objects.create(profile=self.profile, queue=queue)
        self.assertTrue(can_receive(self.user, event))

    def test_notification_is_private_and_staff_only(self) -> None:
        self.assertTrue(
            can_receive(self.user, LiveChange("notifications", user_id=str(self.user.pk)))
        )
        self.assertFalse(
            can_receive(self.user, LiveChange("notifications", user_id="another-user"))
        )
        self.user.is_staff = False
        self.assertFalse(
            can_receive(self.user, LiveChange("notifications", user_id=str(self.user.pk)))
        )

    @patch("apps.core.live.events.get_redis_connection")
    def test_publish_only_after_commit_and_contains_no_record_content(
        self, connection: MagicMock
    ) -> None:
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            publish_change(
                LiveChange("clients", ("clients.view_client",), client_id=self.account.pk)
            )
            connection.assert_not_called()
        self.assertEqual(len(callbacks), 1)
        callbacks[0]()
        payload = json.loads(connection.return_value.publish.call_args.args[1])
        self.assertEqual(payload["topic"], "clients")
        self.assertNotIn("email", payload)
        self.assertNotIn("name", payload)

    @patch("apps.core.live.events.get_redis_connection")
    def test_rollback_does_not_publish(self, connection: MagicMock) -> None:
        with self.captureOnCommitCallbacks(execute=True), transaction.atomic():
            publish_change(LiveChange("clients", global_scope=True))
            transaction.set_rollback(True)
        connection.assert_not_called()

    @patch(
        "apps.core.live.events.get_redis_connection", side_effect=RedisConnectionError("offline")
    )
    def test_broker_failure_does_not_fail_business_write(self, connection: MagicMock) -> None:
        with self.captureOnCommitCallbacks(execute=True):
            self.account.name = "Changed"
            self.account.save()
        self.account.refresh_from_db()
        self.assertEqual(self.account.name, "Changed")
        connection.assert_called()

    def test_client_model_signal_uses_explicit_scope(self) -> None:
        event = change_for(self.account, "clients")
        assert event is not None
        self.assertEqual(event.client_id, self.account.pk)
        self.assertFalse(event.global_scope)

    def test_stream_requires_staff_session(self) -> None:
        self.assertEqual(self.client.get("/api/admin/events").status_code, 401)
        self.client.force_login(self.user)
        response = self.client.get("/api/admin/events")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        self.assertEqual(response["X-Accel-Buffering"], "no")
        self.assertEqual(response["Cache-Control"], "no-store, no-transform")
        self.user.is_staff = False
        self.user.save()
        self.assertEqual(self.client.get("/api/admin/events").status_code, 403)

    @override_settings(CORS_ALLOWED_ORIGINS=["https://admin.example.test"])
    def test_stream_rejects_untrusted_origins(self) -> None:
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.get(
                "/api/admin/events", HTTP_ORIGIN="https://evil.example.test"
            ).status_code,
            403,
        )
        response = self.client.get("/api/admin/events", HTTP_ORIGIN="https://admin.example.test")
        self.assertEqual(response.status_code, 200)

    def test_session_is_revalidated_after_revocation_and_password_change(self) -> None:
        self.client.force_login(self.user)
        key = self.client.session.session_key
        assert key is not None
        self.assertIsNotNone(stream_user(key, str(self.user.pk)))
        self.user.set_password("changed")
        self.user.save()
        self.assertIsNone(stream_user(key, str(self.user.pk)))
        self.client.force_login(self.user)
        key = self.client.session.session_key
        assert key is not None
        self.client.logout()
        self.assertIsNone(stream_user(key, str(self.user.pk)))

    def test_stream_filters_events_and_cleans_up(self) -> None:
        async def consume() -> None:
            subscription = AsyncMock()
            subscription.__aenter__.return_value = subscription
            subscription.get_message.side_effect = [
                {
                    "type": "message",
                    "data": json.dumps({"topic": "clients", "client_id": self.other.pk}),
                },
                {"type": "message", "data": json.dumps({"topic": "monitoring", "internal": True})},
            ]
            client = AsyncMock()
            client.pubsub = lambda: subscription
            with (
                patch("channels.db.close_old_connections"),
                patch("apps.core.live.views.Redis.from_url", return_value=client),
                patch("apps.core.live.views.stream_user", return_value=self.user),
                patch("apps.core.live.views.can_receive", side_effect=[False, True]),
            ):
                generator = stream("session", str(self.user.pk))
                self.assertIn("event: ready", await anext(generator))
                event = await anext(generator)
                self.assertIn('"topics":["monitoring","dashboard","notifications"]', event)
                self.assertNotIn("client_id", event)
                await generator.aclose()
                client.aclose.assert_awaited_once()
                subscription.__aexit__.assert_awaited_once()

        async_to_sync(consume)()
