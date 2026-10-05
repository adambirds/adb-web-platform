from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.db import DatabaseError
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone
from ninja.errors import HttpError

from adbsoftwaresolutions.celery import app
from apps.core.celery_dashboard.services import SNAPSHOT_KEY, overview, snapshot
from apps.core.celery_dashboard.signals import (
    failed,
    finished,
    published,
    record,
    retrying,
    revoked,
    started,
)
from apps.core.celery_dashboard.views import require_administrator
from apps.core.live.events import LiveChange, can_receive
from apps.core.models import AuditEvent, CeleryTaskExecution
from apps.core.tasks import purge_celery_history
from authentication.models import User


@override_settings(
    CACHES={
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        "session": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "celery-test-sessions",
        },
    }
)
class CeleryDashboardTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.admin = User.objects.create_user(
            email="celery-admin@example.test",
            password="test",
            is_staff=True,
            is_superuser=True,
            first_name="Full",
            last_name="Admin",
        )
        self.staff = User.objects.create_user(
            email="celery-staff@example.test",
            password="test",
            is_staff=True,
            first_name="Scoped",
            last_name="Staff",
        )
        self.staff.user_permissions.set(Permission.objects.filter(content_type__app_label="core"))
        self.task = SimpleNamespace(
            name="monitoring.run_check",
            request=SimpleNamespace(
                id="task-one",
                is_eager=False,
                hostname="worker@general",
                retries=0,
                delivery_info={"routing_key": "general"},
            ),
        )

    def test_all_read_and_control_endpoints_reject_non_superusers_before_side_effects(self) -> None:
        for user in [None, self.staff]:
            self.client.logout()
            if user:
                self.client.force_login(user)
            for method, path in [
                ("get", "/api/admin/celery/overview"),
                ("get", "/api/admin/celery/tasks"),
                ("get", "/api/admin/celery/tasks/task-one"),
                ("post", "/api/admin/celery/tasks/task-one/revoke"),
                ("post", "/api/admin/celery/schedules/monitoring-due-check-dispatch/run"),
            ]:
                with (
                    patch("apps.core.celery_dashboard.views.overview") as service,
                    patch.object(app.control, "revoke") as control,
                    patch.object(app, "send_task") as dispatch,
                ):
                    response = getattr(self.client, method)(path)
                self.assertEqual(
                    response.status_code, 403 if user else 401, (path, response.content)
                )
                service.assert_not_called()
                control.assert_not_called()
                dispatch.assert_not_called()

    def test_inactive_or_nonstaff_superusers_are_rejected(self) -> None:
        request = RequestFactory().get("/")
        for active, staff in [(False, True), (True, False)]:
            self.admin.is_active, self.admin.is_staff = active, staff
            request.user = self.admin
            with self.assertRaises(HttpError) as error:
                require_administrator(request)
            self.assertEqual(error.exception.status_code, 403)

    def test_metadata_signals_track_retry_success_without_payloads(self) -> None:
        with patch("apps.core.celery_dashboard.signals.publish_change") as live:
            published(
                sender=self.task.name,
                headers={"id": "task-one"},
                routing_key="general",
                body={"password": "hidden-payload"},
            )
            started(task_id="task-one", task=self.task, args=["hidden-argument"])
            retrying(sender=self.task, request=self.task.request, reason=ValueError("hidden-retry"))
            self.assertEqual(CeleryTaskExecution.objects.get(pk="task-one").state, "RETRY")
            self.task.request.retries = 1
            started(task_id="task-one", task=self.task)
            finished(
                task_id="task-one",
                task=self.task,
                state="SUCCESS",
                retval={"secret": "hidden-result"},
            )
        task = CeleryTaskExecution.objects.get(pk="task-one")
        self.assertEqual(task.state, "SUCCESS")
        self.assertEqual(task.retries, 1)
        self.assertEqual(task.queue, "general")
        self.assertEqual(task.worker, "worker@general")
        self.assertIsNotNone(task.runtime_seconds)
        self.assertNotIn("hidden", str(task.__dict__))
        self.assertTrue(all(call.args[0].superuser_only for call in live.call_args_list))
        # Late publisher signals cannot regress a completed task.
        published(sender=self.task.name, headers={"id": "task-one"}, routing_key="general")
        self.assertEqual(CeleryTaskExecution.objects.get(pk="task-one").state, "SUCCESS")

    def test_failure_stores_exception_class_only(self) -> None:
        started(task_id="task-one", task=self.task)
        failed(
            task_id="task-one",
            sender=self.task,
            exception=ValueError("https://token:private@provider.test"),
        )
        finished(task_id="task-one", task=self.task, state="FAILURE", retval="secret-result")
        task = CeleryTaskExecution.objects.get(pk="task-one")
        self.assertEqual(task.error_type, "ValueError")
        self.assertNotIn("private", str(task.__dict__))
        self.client.force_login(self.admin)
        response = self.client.get("/api/admin/celery/tasks/task-one")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["error_type"], "ValueError")
        self.assertNotIn("private", response.content.decode())

    def test_worker_revocation_is_recorded(self) -> None:
        revoked(
            request=SimpleNamespace(
                id="revoked-task", name="ticketing.sync", hostname="worker@general"
            )
        )
        self.assertEqual(CeleryTaskExecution.objects.get(pk="revoked-task").state, "REVOKED")

    def test_telemetry_failure_does_not_interrupt_tasks(self) -> None:
        with (
            patch.object(
                CeleryTaskExecution.objects,
                "select_for_update",
                side_effect=DatabaseError("secret-db-error"),
            ),
            self.assertLogs("apps.core.celery_dashboard.signals", level="WARNING") as logs,
        ):
            record("task-one", "ticketing.sync", "STARTED")
        self.assertNotIn("secret-db-error", str(logs.output))

    def test_history_filters_and_paginates_on_server(self) -> None:
        self.client.force_login(self.admin)
        for number in range(30):
            record(f"task-{number}", "monitoring.run_check", "FAILURE")
        record("other", "ticketing.sync", "SUCCESS")
        response = self.client.get(
            "/api/admin/celery/tasks",
            {"page": "2", "page_size": "25", "state": "FAILURE", "search": "monitoring"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 30)
        self.assertEqual(len(response.json()["items"]), 5)
        self.assertEqual(
            self.client.get("/api/admin/celery/tasks", {"state": "invented"}).status_code, 400
        )

    def test_cooperative_revoke_is_audited_and_never_claims_completion(self) -> None:
        self.client.force_login(self.admin)
        record("task-one", self.task.name, "QUEUED")
        with patch.object(app.control, "revoke") as control:
            response = self.client.post("/api/admin/celery/tasks/task-one/revoke")
        self.assertEqual(response.status_code, 200, response.content)
        control.assert_called_once_with("task-one", terminate=False)
        task = CeleryTaskExecution.objects.get(pk="task-one")
        self.assertEqual(task.state, "QUEUED")
        self.assertIsNotNone(task.revoke_requested_at)
        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.admin, action="celery.task.revoke_requested"
            ).exists()
        )
        self.assertEqual(
            self.client.post("/api/admin/celery/tasks/task-one/revoke").status_code, 409
        )
        record("running", self.task.name, "STARTED")
        self.assertEqual(
            self.client.post("/api/admin/celery/tasks/running/revoke").status_code, 409
        )

    def test_schedule_dispatch_is_allowlisted_and_audited(self) -> None:
        self.client.force_login(self.admin)
        with patch.object(
            app, "send_task", return_value=SimpleNamespace(id="dispatch-id")
        ) as dispatch:
            response = self.client.post(
                "/api/admin/celery/schedules/monitoring-due-check-dispatch/run"
            )
            unknown = self.client.post("/api/admin/celery/schedules/arbitrary.secret_task/run")
            duplicate = self.client.post(
                "/api/admin/celery/schedules/monitoring-due-check-dispatch/run"
            )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(unknown.status_code, 404)
        self.assertEqual(duplicate.status_code, 429)
        dispatch.assert_called_once_with("monitoring.enqueue_due_checks", args=(), kwargs={})
        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.admin, action="celery.schedule.dispatched"
            ).exists()
        )

    def test_broker_failures_are_safe_and_history_remains_available(self) -> None:
        self.client.force_login(self.admin)
        with patch.object(
            app, "connection_for_read", side_effect=OSError("redis://password@private.test")
        ):
            response = self.client.get("/api/admin/celery/overview")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(response.json()["snapshot"]["broker_available"])
        self.assertIsNone(response.json()["snapshot"]["queues"][0]["depth"])
        self.assertNotIn("password", response.content.decode())
        self.assertEqual(len(response.json()["hours"]), 24)

    def test_live_inspection_is_sanitized_and_cached(self) -> None:
        inspector = MagicMock()
        inspector.stats.return_value = {
            "worker@general": {
                "pool": {"max-concurrency": 2},
                "total": {"test": 4},
                "broker": {"password": "hidden-password"},
            }
        }
        inspector.active.return_value = {
            "worker@general": [
                {
                    "id": "live",
                    "name": "monitoring.run",
                    "args": ["hidden-args"],
                    "kwargs": {"secret": "hidden-value"},
                }
            ]
        }
        inspector.reserved.return_value = {"worker@general": []}
        inspector.scheduled.return_value = {"worker@general": []}
        inspector.active_queues.return_value = {"worker@general": [{"name": "general"}]}
        connection = MagicMock()
        connection.default_channel.queue_declare.return_value.message_count = 5
        with (
            patch.object(app, "connection_for_read") as connect,
            patch.object(app.control, "inspect", return_value=inspector),
        ):
            connect.return_value.__enter__.return_value = connection
            result = snapshot()
            again = snapshot()
        self.assertEqual(result, again)
        self.assertEqual(connect.call_count, 1)
        self.assertEqual(result.queues[0].depth, 5)
        self.assertEqual(result.workers[0].processed, 4)
        self.assertNotIn("hidden", result.model_dump_json())
        self.assertIsNotNone(cache.get(SNAPSHOT_KEY))

    def test_overview_groups_completions_and_retention_preserves_unfinished(self) -> None:
        record("complete", "test.task", "SUCCESS")
        record("failure", "test.task", "FAILURE")
        record("pending", "test.task", "QUEUED")
        with patch("apps.core.celery_dashboard.services.snapshot") as live:
            live.return_value = {
                "checked_at": timezone.now(),
                "broker_available": True,
                "workers": [],
                "queues": [],
                "warning": "",
            }
            result = overview()
        self.assertEqual(sum(hour.succeeded for hour in result.hours), 1)
        self.assertEqual(sum(hour.failed for hour in result.hours), 1)
        CeleryTaskExecution.objects.filter(pk="complete").update(
            finished_at=timezone.now() - timedelta(days=15)
        )
        CeleryTaskExecution.objects.filter(pk="pending").update(
            created_at=timezone.now() - timedelta(days=15)
        )
        self.assertEqual(purge_celery_history(), 1)
        self.assertTrue(CeleryTaskExecution.objects.filter(pk="pending").exists())

    def test_sse_topic_requires_current_superuser_access(self) -> None:
        change = LiveChange("celery", global_scope=True, superuser_only=True)
        self.assertTrue(can_receive(self.admin, change))
        self.assertFalse(can_receive(self.staff, change))
        self.admin.is_superuser = False
        self.assertFalse(can_receive(self.admin, change))
        self.assertFalse(can_receive(self.staff, LiveChange("celery", global_scope=True)))

    def test_empty_redis_queue_is_zero_even_without_a_list_key(self) -> None:
        inspector = MagicMock()
        inspector.stats.return_value = {}
        connection = MagicMock()
        connection.transport.driver_type = "redis"
        connection.default_channel._size.return_value = 0
        connection.default_channel.queue_declare.side_effect = ValueError("Redis list key absent")
        with (
            patch.object(app, "connection_for_read") as connect,
            patch.object(app.control, "inspect", return_value=inspector),
        ):
            connect.return_value.__enter__.return_value = connection
            result = snapshot()
        self.assertTrue(result.broker_available)
        self.assertEqual(result.queues[0].depth, 0)
        connection.default_channel.queue_declare.assert_not_called()

    def test_heartbeats_are_throttled_and_publish_only_admin_hints(self) -> None:
        from apps.core.celery_dashboard.signals import heartbeat

        cache.set(SNAPSHOT_KEY, {"stale": True})
        with patch("apps.core.celery_dashboard.signals.publish_change") as publish:
            heartbeat()
            heartbeat()
        publish.assert_called_once_with(
            LiveChange("celery", global_scope=True, superuser_only=True)
        )
        self.assertIsNone(cache.get(SNAPSHOT_KEY))

    def test_jobs_with_arguments_cannot_be_replayed(self) -> None:
        self.client.force_login(self.admin)
        with (
            patch.dict(
                app.conf.beat_schedule,
                {"parameter-job": {"task": "test.task", "schedule": 60, "args": ["secret"]}},
            ),
            patch.object(app, "send_task") as dispatch,
        ):
            response = self.client.post("/api/admin/celery/schedules/parameter-job/run")
        self.assertEqual(response.status_code, 409)
        dispatch.assert_not_called()
