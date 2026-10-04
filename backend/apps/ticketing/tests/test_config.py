from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from apps.ticketing.config import (
    DEFAULT_GRAPH_SYNC_INTERVAL_SECONDS,
    DEFAULT_GRAPH_SYNC_LOCK_SECONDS,
    graph_sync_interval_seconds,
    graph_sync_lock_seconds,
    malware_scanning_enabled,
)


class TicketingConfigurationTests(SimpleTestCase):
    @patch.dict(
        "os.environ",
        {
            "TICKETING_GRAPH_SYNC_INTERVAL_SECONDS": "",
            "TICKETING_GRAPH_SYNC_LOCK_SECONDS": "",
        },
    )
    def test_graph_sync_timing_defaults_are_safe(self) -> None:
        self.assertEqual(graph_sync_interval_seconds(), DEFAULT_GRAPH_SYNC_INTERVAL_SECONDS)
        self.assertEqual(graph_sync_lock_seconds(), DEFAULT_GRAPH_SYNC_LOCK_SECONDS)

    @patch.dict(
        "os.environ",
        {
            "TICKETING_GRAPH_SYNC_INTERVAL_SECONDS": "120",
            "TICKETING_GRAPH_SYNC_LOCK_SECONDS": "600",
        },
    )
    def test_graph_sync_timing_can_be_configured(self) -> None:
        self.assertEqual(graph_sync_interval_seconds(), 120)
        self.assertEqual(graph_sync_lock_seconds(), 600)

    @patch.dict("os.environ", {"TICKETING_GRAPH_SYNC_INTERVAL_SECONDS": "fast"})
    def test_graph_sync_interval_rejects_non_integer_value(self) -> None:
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "TICKETING_GRAPH_SYNC_INTERVAL_SECONDS must be an integer number of seconds.",
        ):
            graph_sync_interval_seconds()

    @patch.dict("os.environ", {"TICKETING_GRAPH_SYNC_INTERVAL_SECONDS": "10"})
    def test_graph_sync_interval_rejects_overly_aggressive_polling(self) -> None:
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "TICKETING_GRAPH_SYNC_INTERVAL_SECONDS must be at least 30 seconds.",
        ):
            graph_sync_interval_seconds()

    @patch.dict("os.environ", {"TICKETING_GRAPH_SYNC_LOCK_SECONDS": "30"})
    def test_graph_sync_lock_rejects_too_short_timeout(self) -> None:
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "TICKETING_GRAPH_SYNC_LOCK_SECONDS must be at least 60 seconds.",
        ):
            graph_sync_lock_seconds()

    @patch.dict("os.environ", {"TICKETING_MALWARE_SCANNING_ENABLED": ""})
    def test_malware_scanning_is_disabled_by_default(self) -> None:
        self.assertFalse(malware_scanning_enabled())

    @patch.dict("os.environ", {"TICKETING_MALWARE_SCANNING_ENABLED": "true"})
    def test_malware_scanning_can_be_enabled(self) -> None:
        self.assertTrue(malware_scanning_enabled())

    @patch.dict("os.environ", {"TICKETING_MALWARE_SCANNING_ENABLED": "sometimes"})
    def test_malware_scanning_rejects_invalid_boolean(self) -> None:
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "TICKETING_MALWARE_SCANNING_ENABLED must be a boolean value.",
        ):
            malware_scanning_enabled()

    def test_celery_beat_schedule_dispatches_ticketing_work(self) -> None:
        from adbsoftwaresolutions.celery import app

        graph_schedule = app.conf.beat_schedule["ticketing-graph-mailbox-sync"]
        self.assertEqual(graph_schedule["task"], "ticketing.enqueue_graph_mailbox_syncs")
        attachment_schedule = app.conf.beat_schedule["ticketing-attachment-scan-dispatch"]
        self.assertEqual(attachment_schedule["task"], "ticketing.enqueue_attachment_scans")
