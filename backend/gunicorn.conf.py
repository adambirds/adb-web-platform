"""Gunicorn settings, read from the working directory (/opt/adbsoftwaresolutions) in
the image.

- Prometheus multiprocess mode: entrypoint.sh points PROMETHEUS_MULTIPROC_DIR
  at an empty directory, every worker writes its metrics there and /metrics
  (served by any worker) adds them up. A worker that exits is marked dead.
- With LOG_FORMAT=json, Gunicorn's and Uvicorn's own lines are JSON too.
"""

import os
from typing import Any

from adbsoftwaresolutions.logs import JsonFormatter, json_enabled


def child_exit(server: Any, worker: Any) -> None:
    # Set by entrypoint.sh in the image only (not a configuration variable).
    if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        from prometheus_client import multiprocess

        multiprocess.mark_process_dead(worker.pid)


if json_enabled():
    logconfig_dict = {
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {"level": "INFO", "handlers": ["console"]},
        "loggers": {
            "gunicorn.error": {"level": "INFO", "handlers": ["console"], "propagate": False},
            # No access log, as before: Docker polls /healthz every 30 seconds.
            "gunicorn.access": {"level": "INFO", "handlers": [], "propagate": False},
        },
    }
