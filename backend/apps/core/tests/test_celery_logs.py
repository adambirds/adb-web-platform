from __future__ import annotations

import logging
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.core.celery_dashboard.logs import TaskLogHandler, append_log, install
from apps.core.celery_dashboard.signals import failed, finished, started
from apps.core.models import CeleryTaskExecution, CeleryTaskLog
from apps.core.tasks import purge_celery_history
from authentication.models import User


@override_settings(
    CACHES={
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        "session": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "log-test-sessions",
        },
    }
)
class CeleryLogTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.admin = User.objects.create_user(
            email="log-admin@example.test",
            password="test",
            first_name="Full",
            last_name="Admin",
            is_staff=True,
            is_superuser=True,
        )
        self.staff = User.objects.create_user(
            email="log-staff@example.test",
            password="test",
            first_name="Limited",
            last_name="Staff",
            is_staff=True,
        )
        self.staff.user_permissions.set(Permission.objects.filter(content_type__app_label="core"))
        self.task = SimpleNamespace(
            name="test.logged",
            request=SimpleNamespace(
                id="task-log",
                is_eager=False,
                hostname="worker",
                retries=0,
                delivery_info={"routing_key": "general"},
                args=(),
                kwargs={"password": "task-secret-value"},
            ),
        )
        self.execution = CeleryTaskExecution.objects.create(id="task-log", task_name="test.logged")

    def test_task_python_logging_is_correlated_and_deduplicated(self) -> None:
        entry = logging.LogRecord(
            "test.worker", logging.INFO, __file__, 1, "Progress: %s records", (12,), None
        )
        handler = TaskLogHandler()
        with patch("apps.core.celery_dashboard.logs.current_task", self.task):
            handler.emit(entry)
            handler.emit(entry)
        self.assertEqual(CeleryTaskLog.objects.count(), 1)
        row = CeleryTaskLog.objects.get()
        self.assertEqual(row.execution_id, "task-log")
        self.assertEqual(row.message, "Progress: 12 records")
        self.assertEqual(row.logger_name, "test.worker")

    def test_only_current_task_logs_are_captured_and_result_dumps_are_excluded(self) -> None:
        handler = TaskLogHandler()
        with patch("apps.core.celery_dashboard.logs.current_task", None):
            handler.emit(
                logging.LogRecord(
                    "test.worker", logging.INFO, __file__, 1, "unrelated log", (), None
                )
            )
        with patch("apps.core.celery_dashboard.logs.current_task", self.task):
            handler.emit(
                logging.LogRecord(
                    "celery.app.trace",
                    logging.INFO,
                    __file__,
                    1,
                    "Task succeeded: secret-result",
                    (),
                    None,
                )
            )
            handler.emit(
                logging.LogRecord(
                    "django.db.backends", logging.DEBUG, __file__, 1, "secret SQL payload", (), None
                )
            )
        self.assertFalse(CeleryTaskLog.objects.exists())

    def test_secret_redaction_happens_before_storage(self) -> None:
        text = 'password="quoted secret" Bearer opaque-bearer redis://user:pass@host/0 /reset-password/private-uuid env-secret-value task-secret-value\n-----BEGIN PRIVATE KEY-----\nprivate material\n-----END PRIVATE KEY-----'
        with patch.dict("os.environ", {"GITHUB_WEBHOOK_SECRET": "env-secret-value"}):
            append_log("task-log", text, task=self.task)
        output = CeleryTaskLog.objects.get().message
        for secret in [
            "quoted secret",
            "opaque-bearer",
            "user:pass",
            "private-uuid",
            "env-secret-value",
            "task-secret-value",
            "private material",
        ]:
            self.assertNotIn(secret, output)
        self.assertIn("[REDACTED]", output)

    def test_lifecycle_failure_traceback_and_retry_attempt_are_recorded(self) -> None:
        started(task_id="task-log", task=self.task)
        try:
            raise ValueError("provider rejected password=super-private")
        except ValueError as error:
            failed(task_id="task-log", sender=self.task, exception=error)
        output = "\n".join(CeleryTaskLog.objects.values_list("message", flat=True))
        self.assertIn("Task execution started", output)
        self.assertIn("Traceback", output)
        self.assertIn("ValueError", output)
        self.assertNotIn("super-private", output)
        finished(task_id="task-log", task=self.task, state="FAILURE")
        self.assertEqual(CeleryTaskLog.objects.filter(level=logging.ERROR).count(), 1)

    def test_log_api_denies_non_superusers_even_with_all_core_permissions(self) -> None:
        append_log("task-log", "administrator diagnostics")
        for user, status in [(None, 401), (self.staff, 403), (self.admin, 200)]:
            self.client.logout()
            if user:
                self.client.force_login(user)
            response = self.client.get("/api/admin/celery/tasks/task-log/logs")
            self.assertEqual(response.status_code, status)
            if status != 200:
                self.assertNotIn("administrator diagnostics", response.content.decode())
        self.admin.is_superuser = False
        self.admin.save()
        self.assertEqual(self.client.get("/api/admin/celery/tasks/task-log/logs").status_code, 403)

    def test_api_pages_latest_logs_in_chronological_order_and_filters_severity(self) -> None:
        for number in range(7):
            append_log(
                "task-log", f"line {number}", level=logging.ERROR if number % 2 else logging.INFO
            )
        self.client.force_login(self.admin)
        response = self.client.get("/api/admin/celery/tasks/task-log/logs", {"page_size": "3"})
        self.assertEqual(
            [item["message"] for item in response.json()["items"]], ["line 4", "line 5", "line 6"]
        )
        older = self.client.get(
            "/api/admin/celery/tasks/task-log/logs", {"page": "2", "page_size": "3"}
        )
        self.assertEqual(
            [item["message"] for item in older.json()["items"]], ["line 1", "line 2", "line 3"]
        )
        errors = self.client.get("/api/admin/celery/tasks/task-log/logs", {"level": "ERROR"})
        self.assertEqual(errors.json()["total"], 3)
        self.assertEqual(
            self.client.get(
                "/api/admin/celery/tasks/task-log/logs", {"level": "invalid"}
            ).status_code,
            400,
        )
        self.assertEqual(self.client.get("/api/admin/celery/tasks/missing/logs").status_code, 404)

    def test_entry_and_per_task_limits_bound_storage(self) -> None:
        append_log("task-log", "x" * 9000)
        self.assertLess(len(CeleryTaskLog.objects.get().message), 8050)
        with patch("apps.core.celery_dashboard.logs.MAX_TASK_LOGS", 2):
            append_log("task-log", "second")
            append_log("task-log", "third")
        self.execution.refresh_from_db()
        self.assertEqual(self.execution.log_count, 2)
        self.assertTrue(self.execution.logs_truncated)
        self.assertEqual(CeleryTaskLog.objects.count(), 2)

    def test_failure_to_store_logs_cannot_interrupt_business_task(self) -> None:
        with patch.object(
            CeleryTaskExecution.objects, "select_for_update", side_effect=RuntimeError("db failed")
        ):
            append_log("task-log", "diagnostics")
        self.assertFalse(CeleryTaskLog.objects.exists())

    def test_retention_removes_old_logs_even_on_unfinished_executions(self) -> None:
        append_log("task-log", "old diagnostics")
        CeleryTaskLog.objects.update(created_at=timezone.now() - timedelta(days=15))
        self.assertEqual(purge_celery_history(), 0)
        self.assertTrue(CeleryTaskExecution.objects.filter(pk="task-log").exists())
        self.assertFalse(CeleryTaskLog.objects.exists())

    def test_install_does_not_duplicate_handlers(self) -> None:
        logger = logging.getLogger("test.celery.install")
        try:
            install(logger=logger)
            install(logger=logger)
            self.assertEqual(
                sum(isinstance(handler, TaskLogHandler) for handler in logger.handlers), 1
            )
        finally:
            for handler in list(logger.handlers):
                if isinstance(handler, TaskLogHandler):
                    logger.removeHandler(handler)

    def test_log_hints_publish_after_commit_without_message_content(self) -> None:
        with (
            patch("apps.core.celery_dashboard.logs.publish_change") as publish,
            self.captureOnCommitCallbacks(execute=True),
        ):
            append_log("task-log", "internal diagnostics")
        publish.assert_called_once()
        hint = publish.call_args.args[0]
        self.assertTrue(hint.superuser_only)
        self.assertEqual(hint.topic, "celery")
        self.assertNotIn("internal diagnostics", str(hint))
