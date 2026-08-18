from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, suppress

from celery import shared_task
from django_redis import get_redis_connection
from redis.exceptions import LockError

from apps.ticketing.config import graph_sync_lock_seconds
from apps.ticketing.models import Mailbox, MicrosoftGraphConnection
from apps.ticketing.services.contracts import CanonicalMessage
from apps.ticketing.services.graph import MicrosoftGraphAdapter, sync_graph_mailbox
from apps.ticketing.services.graph_auth import MicrosoftGraphTokenProvider
from apps.ticketing.services.ingestion import ingest_canonical_message

GRAPH_SYNC_LOCK_PREFIX = "ticketing:graph-mailbox-sync"
BACKGROUND_AUTH_METHODS = (
    MicrosoftGraphConnection.AuthenticationMethod.CERTIFICATE,
    MicrosoftGraphConnection.AuthenticationMethod.CLIENT_SECRET,
)


@shared_task(name="ticketing.enqueue_graph_mailbox_syncs")
def enqueue_graph_mailbox_syncs() -> int:
    """Enqueue one sync task for every mailbox eligible for background Graph sync."""
    mailbox_ids = list(
        Mailbox.objects.filter(
            enabled=True,
            graph_connection__enabled=True,
            graph_connection__credential__isnull=False,
            graph_connection__authentication_method__in=BACKGROUND_AUTH_METHODS,
        )
        .order_by("id")
        .values_list("id", flat=True)
    )
    for mailbox_id in mailbox_ids:
        sync_graph_mailbox_task.delay(mailbox_id)
    return len(mailbox_ids)


@shared_task(name="ticketing.sync_graph_mailbox")
def sync_graph_mailbox_task(mailbox_id: int) -> int:
    """Synchronise one configured mailbox into the canonical ticket ingestion path."""
    mailbox = (
        Mailbox.objects.select_related(
            "graph_connection__credential",
            "brand",
            "default_queue",
        )
        .filter(id=mailbox_id)
        .first()
    )
    if mailbox is None or not _mailbox_can_sync(mailbox):
        return 0

    with _graph_mailbox_sync_lock(mailbox.id) as acquired:
        if not acquired:
            return 0

        token_provider = MicrosoftGraphTokenProvider(mailbox.graph_connection)
        adapter = MicrosoftGraphAdapter(token_provider)
        return sync_graph_mailbox(mailbox, adapter, _consume_canonical_message)


def _mailbox_can_sync(mailbox: Mailbox) -> bool:
    return bool(
        mailbox.enabled
        and mailbox.graph_connection.enabled
        and mailbox.graph_connection.credential_id
        and mailbox.graph_connection.authentication_method in BACKGROUND_AUTH_METHODS
    )


def _consume_canonical_message(mailbox: Mailbox, canonical: CanonicalMessage) -> None:
    ingest_canonical_message(mailbox, canonical)


@contextmanager
def _graph_mailbox_sync_lock(mailbox_id: int) -> Iterator[bool]:
    """Prevent concurrent workers from advancing the same mailbox delta cursor."""
    redis = get_redis_connection("default")
    lock = redis.lock(
        f"{GRAPH_SYNC_LOCK_PREFIX}:{mailbox_id}",
        timeout=graph_sync_lock_seconds(),
        blocking_timeout=0,
    )
    acquired = bool(lock.acquire(blocking=False))
    try:
        yield acquired
    finally:
        if acquired:
            # An expired lock must never cause an otherwise successful sync to fail.
            with suppress(LockError):
                lock.release()
