from unittest.mock import Mock, patch

from django.test import TestCase

from apps.core.models import Brand
from apps.core.ownership import OwnershipType
from apps.credentials.models import StoredCredential
from apps.ticketing.models import Mailbox, MicrosoftGraphConnection, TicketQueue
from apps.ticketing.tasks import (
    _graph_mailbox_sync_lock,
    enqueue_graph_mailbox_syncs,
    sync_graph_mailbox_task,
)


class GraphMailboxTaskTests(TestCase):
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
        self.credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Graph credential",
        )
        self.connection = MicrosoftGraphConnection.objects.create(
            name="Microsoft 365",
            tenant_id="tenant-id",
            client_id="client-id",
            authentication_method=MicrosoftGraphConnection.AuthenticationMethod.CERTIFICATE,
            credential=self.credential,
        )
        self.mailbox = Mailbox.objects.create(
            graph_connection=self.connection,
            email_address="support@adb-test.example.test",
            brand=self.brand,
            default_queue=self.queue,
        )

    def _connection(
        self,
        *,
        suffix: str,
        authentication_method: str = MicrosoftGraphConnection.AuthenticationMethod.CERTIFICATE,
        enabled: bool = True,
        credential: StoredCredential | None = None,
    ) -> MicrosoftGraphConnection:
        return MicrosoftGraphConnection.objects.create(
            name=f"Graph {suffix}",
            tenant_id=f"tenant-{suffix}",
            client_id=f"client-{suffix}",
            authentication_method=authentication_method,
            enabled=enabled,
            credential=self.credential if credential is None else credential,
        )

    def _mailbox(
        self,
        *,
        suffix: str,
        connection: MicrosoftGraphConnection,
        enabled: bool = True,
    ) -> Mailbox:
        return Mailbox.objects.create(
            graph_connection=connection,
            email_address=f"{suffix}@adb-test.example.test",
            brand=self.brand,
            default_queue=self.queue,
            enabled=enabled,
        )

    @patch("apps.ticketing.tasks.sync_graph_mailbox_task.delay")
    def test_dispatcher_enqueues_only_background_eligible_mailboxes(self, delay: Mock) -> None:
        delegated = self._connection(
            suffix="delegated",
            authentication_method=MicrosoftGraphConnection.AuthenticationMethod.DELEGATED,
        )
        self._mailbox(suffix="delegated", connection=delegated)

        disabled_connection = self._connection(suffix="disabled", enabled=False)
        self._mailbox(suffix="disabled-connection", connection=disabled_connection)

        disabled_mailbox_connection = self._connection(suffix="disabled-mailbox")
        self._mailbox(
            suffix="disabled-mailbox",
            connection=disabled_mailbox_connection,
            enabled=False,
        )

        no_credential_connection = MicrosoftGraphConnection.objects.create(
            name="No credential",
            tenant_id="tenant-no-credential",
            client_id="client-no-credential",
        )
        self._mailbox(suffix="no-credential", connection=no_credential_connection)

        count = enqueue_graph_mailbox_syncs.run()

        self.assertEqual(count, 1)
        delay.assert_called_once_with(self.mailbox.id)

    @patch("apps.ticketing.tasks.sync_graph_mailbox")
    @patch("apps.ticketing.tasks.MicrosoftGraphAdapter")
    @patch("apps.ticketing.tasks.MicrosoftGraphTokenProvider")
    @patch("apps.ticketing.tasks._graph_mailbox_sync_lock")
    def test_mailbox_task_wires_auth_adapter_and_ingestion(
        self,
        mailbox_lock: Mock,
        token_provider: Mock,
        adapter: Mock,
        sync_service: Mock,
    ) -> None:
        mailbox_lock.return_value.__enter__.return_value = True
        token_instance = token_provider.return_value
        adapter_instance = adapter.return_value
        sync_service.return_value = 4

        result = sync_graph_mailbox_task.run(self.mailbox.id)

        self.assertEqual(result, 4)
        token_provider.assert_called_once()
        called_connection = token_provider.call_args.args[0]
        self.assertEqual(called_connection.id, self.connection.id)
        adapter.assert_called_once_with(token_instance)
        sync_service.assert_called_once()
        called_mailbox, called_adapter, consumer = sync_service.call_args.args
        self.assertEqual(called_mailbox.id, self.mailbox.id)
        self.assertIs(called_adapter, adapter_instance)
        self.assertTrue(callable(consumer))

    @patch("apps.ticketing.tasks.MicrosoftGraphTokenProvider")
    @patch("apps.ticketing.tasks._graph_mailbox_sync_lock")
    def test_mailbox_task_skips_when_another_worker_holds_lock(
        self,
        mailbox_lock: Mock,
        token_provider: Mock,
    ) -> None:
        mailbox_lock.return_value.__enter__.return_value = False

        result = sync_graph_mailbox_task.run(self.mailbox.id)

        self.assertEqual(result, 0)
        token_provider.assert_not_called()

    def test_mailbox_task_ignores_missing_or_ineligible_mailbox(self) -> None:
        self.assertEqual(sync_graph_mailbox_task.run(999999), 0)

        self.connection.authentication_method = (
            MicrosoftGraphConnection.AuthenticationMethod.DELEGATED
        )
        self.connection.save(update_fields=["authentication_method"])
        self.assertEqual(sync_graph_mailbox_task.run(self.mailbox.id), 0)

    @patch.dict("os.environ", {"TICKETING_GRAPH_SYNC_LOCK_SECONDS": "120"})
    @patch("apps.ticketing.tasks.get_redis_connection")
    def test_mailbox_lock_uses_redis_and_releases_owned_lock(self, get_redis: Mock) -> None:
        redis = get_redis.return_value
        lock = redis.lock.return_value
        lock.acquire.return_value = True

        with _graph_mailbox_sync_lock(self.mailbox.id) as acquired:
            self.assertTrue(acquired)

        redis.lock.assert_called_once_with(
            f"ticketing:graph-mailbox-sync:{self.mailbox.id}",
            timeout=120,
            blocking_timeout=0,
        )
        lock.acquire.assert_called_once_with(blocking=False)
        lock.release.assert_called_once_with()
