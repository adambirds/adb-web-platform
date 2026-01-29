# bootsteps.py
from __future__ import annotations

from pathlib import Path
from typing import Any

from celery import bootsteps
from celery.worker import WorkController

HEARTBEAT_FILE = Path("/tmp/celery_worker_heartbeat")


class LivenessProbe(bootsteps.StartStopStep):
    requires = {"celery.worker.components:Timer"}

    tref: Any  # TimerReference, but no stable public type

    def __init__(self, parent: WorkController, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.tref = None

    def start(self, worker: WorkController) -> None:
        self.tref = worker.timer.call_repeatedly(
            1.0,
            self.update_heartbeat_file,
            (worker,),
            priority=10,
        )

    def stop(self, worker: WorkController) -> None:
        HEARTBEAT_FILE.unlink(missing_ok=True)

    def update_heartbeat_file(self, worker: WorkController) -> None:
        HEARTBEAT_FILE.touch()
