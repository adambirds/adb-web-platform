"""Logging: one JSON object per line (for Loki), or plain text for local runs.

LOG_FORMAT=json, set in the Docker images, selects JSON. SERVICE_NAME names
the component in each line (the backend by default; the Celery images set
their own). Standard library only: gunicorn.conf.py imports this before
Django is set up.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import UTC, datetime
from typing import Any

# Attributes every LogRecord has; anything else was passed with `extra=`
# (except Uvicorn's colour-coded copy of the message).
_STANDARD = set(vars(logging.makeLogRecord({}))) | {"message", "asctime", "color_message"}
_OAUTH_CALLBACK = re.compile(r"(/api/analytics/oauth/callback)\?[^\s\"']+")


def redact_oauth_callback(value: str) -> str:
    return _OAUTH_CALLBACK.sub(r"\1?[redacted]", value)


class OAuthCallbackLogFilter(logging.Filter):
    """Preserve access-formatter arguments while removing OAuth codes/state."""

    def filter(self, record: logging.LogRecord) -> bool:
        if "/api/analytics/oauth/callback" not in record.getMessage():
            return True
        record.msg = redact_oauth_callback(str(record.msg))

        def clean(value: object) -> object:
            if isinstance(value, str):
                redacted = redact_oauth_callback(value)
                if redacted == value and ("code=" in value or "state=" in value):
                    return "[redacted]"
                return redacted
            return value

        if isinstance(record.args, tuple):
            record.args = tuple(clean(value) for value in record.args)
        elif isinstance(record.args, dict):
            record.args = {key: clean(value) for key, value in record.args.items()}
        return True


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str | None = None) -> None:
        super().__init__()
        self.service = service or os.environ.get("SERVICE_NAME") or "adb-web-platform-backend"

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": redact_oauth_callback(record.getMessage()),
            "service": self.service,
        }
        if record.exc_info:
            entry["exception"] = redact_oauth_callback(self.formatException(record.exc_info))
        for key, value in vars(record).items():
            if key not in _STANDARD and not key.startswith("_"):
                rendered = (
                    value if isinstance(value, str | int | float | bool | None) else repr(value)
                )
                entry[key] = (
                    redact_oauth_callback(rendered) if isinstance(rendered, str) else rendered
                )
        return json.dumps(entry, ensure_ascii=False)


def json_enabled() -> bool:
    return os.environ.get("LOG_FORMAT", "text").lower() == "json"


def logging_config(level: str = "INFO") -> dict[str, Any]:
    """settings.LOGGING: everything to stdout through the root logger."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {"()": JsonFormatter},
            "text": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "json" if json_enabled() else "text",
            },
        },
        "root": {"handlers": ["console"], "level": level.upper()},
        # Django's own console handler only prints when DEBUG is on; drop it
        # so its messages are not printed twice.
        "loggers": {"django": {"level": "INFO"}},
    }
