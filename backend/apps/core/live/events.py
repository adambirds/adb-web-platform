from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from typing import Any

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django_redis import get_redis_connection
from redis.exceptions import RedisError

from apps.access_control.policies import scope_clients_for_user, scope_ticket_queues_for_user
from authentication.models import User

logger = logging.getLogger(__name__)


def channel_name() -> str:
    return cache.make_key("platform:live:changes")


@dataclass(frozen=True)
class LiveChange:
    """Internal routing only. Never publish names, secrets, bodies or observations."""

    topic: str
    permissions: tuple[str, ...] = ()
    client_id: int | None = None
    queue_id: int | None = None
    user_id: str | None = None
    internal: bool = False
    global_scope: bool = False
    superuser_only: bool = False

    @classmethod
    def decode(cls, raw: str) -> LiveChange:
        data: dict[str, Any] = json.loads(raw)
        return cls(**data)


def publish_change(change: LiveChange) -> None:
    """Publish only after commit; Redis outages never roll back business writes."""

    def send() -> None:
        try:
            get_redis_connection("default").publish(channel_name(), json.dumps(asdict(change)))
        except (RedisError, OSError, ValueError, ImproperlyConfigured, NotImplementedError):
            logger.warning("Live invalidation unavailable; clients will reconcile through the API.")

    transaction.on_commit(send)


def can_receive(user: User, change: LiveChange) -> bool:
    if not user.is_active or not user.is_staff:
        return False
    if (change.superuser_only or change.topic == "celery") and not user.is_superuser:
        return False
    if change.user_id is not None and change.user_id != str(user.pk):
        return False
    if not user.has_perms(change.permissions):
        return False
    if (
        change.client_id is not None
        and not scope_clients_for_user(user).filter(pk=change.client_id).exists()
    ):
        return False
    if (
        change.queue_id is not None
        and not scope_ticket_queues_for_user(user).filter(pk=change.queue_id).exists()
    ):
        return False
    return (
        change.client_id is not None
        or change.queue_id is not None
        or change.internal
        or change.global_scope
        or change.user_id is not None
    )


def topics_for(change: LiveChange) -> list[str]:
    topics = [change.topic]
    if change.topic not in ("access", "notifications", "activity", "celery"):
        topics.append("dashboard")
    if change.topic in ("monitoring", "tasks", "calendar", "tickets", "credentials"):
        topics.append("notifications")
    return topics
