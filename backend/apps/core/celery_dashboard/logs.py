from __future__ import annotations

import logging
import os
import re
import traceback
from collections.abc import Mapping
from typing import Any

from celery import current_task
from django.core.cache import cache
from django.db import transaction

from apps.core.live.events import LiveChange, publish_change
from apps.core.models import CeleryTaskExecution, CeleryTaskLog

MAX_TASK_LOGS = 2000
MAX_LOG_CHARACTERS = 8000
SECRET_NAME = re.compile(
    r"password|passwd|secret|token|private.?key|passphrase|authorization|credential|encryption.?keys",
    re.IGNORECASE,
)
SECRET_FIELD = re.compile(
    r"""((?:["']?)(?:password|passwd|secret|token|access_token|refresh_token|client_secret|api_key|private_key|passphrase|authorization)(?:["']?)\s*[:=]\s*)(?:"[^"\n]*"|'[^'\n]*'|[^\s,;}\]]+)""",
    re.IGNORECASE,
)
PEM = re.compile(r"-----BEGIN [^-]+-----.*?-----END [^-]+-----", re.DOTALL)


def sensitive_values(value: Any, *, secret: bool = False) -> set[str]:
    if isinstance(value, Mapping):
        result: set[str] = set()
        for key, item in value.items():
            result.update(
                sensitive_values(item, secret=secret or bool(SECRET_NAME.search(str(key))))
            )
        return result
    if isinstance(value, (list, tuple)):
        return set().union(*(sensitive_values(item, secret=secret) for item in value))
    return {value} if secret and isinstance(value, str) and len(value) >= 4 else set()


def redact(message: str, *, task: Any = None) -> str:
    secrets = {
        value for name, value in os.environ.items() if SECRET_NAME.search(name) and len(value) >= 4
    }
    if task is not None:
        secrets.update(sensitive_values(getattr(task.request, "kwargs", {})))
        secrets.update(sensitive_values(getattr(task.request, "args", ())))
    message = PEM.sub("[REDACTED PEM]", message)
    message = re.sub(r"(?i)\b(Bearer|Basic)\s+[^\s,;\"']+", r"\1 [REDACTED]", message)
    message = re.sub(r"(\w+://)[^\s/@]+:[^\s/@]+@", r"\1[REDACTED]@", message)
    message = SECRET_FIELD.sub(r"\1[REDACTED]", message)
    message = re.sub(r"(/(?:reset-password|verify-email)/)[^\s/\"'<>]+", r"\1[REDACTED]", message)
    # Match credential syntax before literal values can alter field names or delimiters.
    for secret in sorted(secrets, key=len, reverse=True):
        message = message.replace(secret, "[REDACTED]")
        if "\\n" in secret:
            message = message.replace(secret.replace("\\n", "\n"), "[REDACTED]")
    # Keep diagnostics readable, and avoid storing terminal control sequences.
    message = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", message)
    message = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", message)
    return message[:MAX_LOG_CHARACTERS] + (
        "\n[Log entry truncated]" if len(message) > MAX_LOG_CHARACTERS else ""
    )


def append_log(
    task_id: str,
    message: str,
    *,
    level: int = logging.INFO,
    logger_name: str = "celery.lifecycle",
    attempt: int = 0,
    task: Any = None,
) -> None:
    try:
        clean = redact(message, task=task)
        with transaction.atomic():
            execution = CeleryTaskExecution.objects.select_for_update().filter(pk=task_id).first()
            if execution is None:
                return
            if execution.log_count >= MAX_TASK_LOGS:
                if not execution.logs_truncated:
                    execution.logs_truncated = True
                    execution.save(update_fields=["logs_truncated"])
                    publish_change(LiveChange("celery", global_scope=True, superuser_only=True))
                return
            CeleryTaskLog.objects.create(
                execution=execution,
                level=max(0, min(level, 65535)),
                logger_name=logger_name[:150],
                message=clean,
                attempt=max(attempt, 0),
            )
            execution.log_count += 1
            execution.save(update_fields=["log_count"])

            def notify() -> None:
                try:
                    if cache.add(f"celery_dashboard:log_hint:{task_id}", True, timeout=1):
                        publish_change(LiveChange("celery", global_scope=True, superuser_only=True))
                except Exception:
                    pass  # Worker heartbeat/reconciliation also refreshes the log viewer.

            transaction.on_commit(notify)
    except Exception:
        # Never recursively log persistence errors or interrupt the task.
        return


def exception_text(exception: BaseException) -> str:
    # No local-variable dumps. Redaction occurs before this text is persisted.
    return "".join(
        traceback.TracebackException.from_exception(exception, capture_locals=False).format()
    )


class TaskLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if record.name.startswith(("apps.core.celery_dashboard", "django.db", "celery.app.trace")):
            return
        if getattr(record, "_celery_dashboard_captured", False):
            return
        try:
            task = current_task
            if not task or task.request.is_eager or not task.request.id:
                return
            record._celery_dashboard_captured = True
            message = record.getMessage()
            if record.exc_info and record.exc_info[1]:
                message += "\n" + exception_text(record.exc_info[1])
            append_log(
                str(task.request.id),
                message,
                level=record.levelno,
                logger_name=record.name,
                attempt=task.request.retries,
                task=task,
            )
        except Exception:
            return


def install(logger: logging.Logger | None = None, **kwargs: Any) -> None:
    targets = [
        logging.getLogger(),
        logging.getLogger("celery.task"),
        logging.getLogger("celery.redirected"),
    ]
    if logger is not None:
        targets.append(logger)
    for target in targets:
        if not any(isinstance(handler, TaskLogHandler) for handler in target.handlers):
            target.addHandler(TaskLogHandler())
