from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, suppress
from functools import partial
from typing import BinaryIO, cast

from celery import shared_task
from django.core.files.storage import default_storage
from django.utils import timezone
from django_redis import get_redis_connection
from redis.exceptions import LockError

from apps.ticketing.config import graph_sync_lock_seconds, malware_scanning_enabled
from apps.ticketing.models import Mailbox, MicrosoftGraphConnection, TicketAttachment, TicketMessage
from apps.ticketing.services.attachments import quarantine_attachment
from apps.ticketing.services.contracts import CanonicalMessage
from apps.ticketing.services.graph import (
    MicrosoftGraphAdapter,
    MicrosoftGraphError,
    sync_graph_mailbox,
)
from apps.ticketing.services.graph_auth import (
    MicrosoftGraphAuthenticationError,
    MicrosoftGraphTokenProvider,
)
from apps.ticketing.services.graph_outbound import MicrosoftGraphOutboundAdapter
from apps.ticketing.services.ingestion import ingest_canonical_message
from apps.ticketing.services.replies import (
    DELIVERY_STATUS_SENT,
    GRAPH_PROVIDER,
    complete_ticket_reply,
    fail_ticket_reply,
    mark_ticket_reply_sending,
)
from apps.ticketing.services.scanning import AttachmentScanError, clamav_scanner_from_environment

GRAPH_SYNC_LOCK_PREFIX = "ticketing:graph-mailbox-sync"
REPLY_DELIVERY_LOCK_PREFIX = "ticketing:reply-delivery"
ATTACHMENT_SCAN_LOCK_PREFIX = "ticketing:attachment-scan"
REPLY_DELIVERY_LOCK_SECONDS = 300
ATTACHMENT_SCAN_LOCK_SECONDS = 5 * 60
ATTACHMENT_SCAN_DISPATCH_BATCH_SIZE = 200
BACKGROUND_AUTH_METHODS = (
    MicrosoftGraphConnection.AuthenticationMethod.CERTIFICATE,
    MicrosoftGraphConnection.AuthenticationMethod.CLIENT_SECRET,
)
RETRYABLE_GRAPH_ERRORS = (MicrosoftGraphError, MicrosoftGraphAuthenticationError)
TERMINAL_ATTACHMENT_SCAN_STATUSES = (
    TicketAttachment.ScanStatus.SAFE,
    TicketAttachment.ScanStatus.INFECTED,
    TicketAttachment.ScanStatus.BLOCKED,
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
        consumer = partial(_consume_canonical_message, adapter=adapter)
        return sync_graph_mailbox(mailbox, adapter, consumer)


@shared_task(name="ticketing.enqueue_attachment_scans")
def enqueue_attachment_scans() -> int:
    """Backfill pending/failed attachment scans when malware scanning is enabled."""
    if not malware_scanning_enabled():
        return 0

    attachment_ids = list(
        TicketAttachment.objects.filter(
            scan_status__in=(
                TicketAttachment.ScanStatus.PENDING,
                TicketAttachment.ScanStatus.FAILED,
            )
        )
        .exclude(storage_key="")
        .order_by("id")
        .values_list("id", flat=True)[:ATTACHMENT_SCAN_DISPATCH_BATCH_SIZE]
    )
    for attachment_id in attachment_ids:
        scan_ticket_attachment_task.delay(attachment_id)
    return len(attachment_ids)


@shared_task(
    name="ticketing.scan_ticket_attachment",
    autoretry_for=(AttachmentScanError,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def scan_ticket_attachment_task(attachment_id: int) -> int:
    """Scan a quarantined attachment and release it only after a clean verdict."""
    if not malware_scanning_enabled():
        return 0

    attachment = TicketAttachment.objects.filter(id=attachment_id).first()
    if attachment is None or attachment.scan_status in TERMINAL_ATTACHMENT_SCAN_STATUSES:
        return 0

    with _ticket_attachment_scan_lock(attachment.id) as acquired:
        if not acquired:
            return 0

        attachment.refresh_from_db()
        if attachment.scan_status in TERMINAL_ATTACHMENT_SCAN_STATUSES:
            return 0

        scanner = clamav_scanner_from_environment()
        attachment.scan_status = TicketAttachment.ScanStatus.SCANNING
        attachment.scan_engine = scanner.engine_name
        attachment.scan_result = ""
        attachment.scanned_at = None
        attachment.safe_at = None
        attachment.save(
            update_fields=[
                "scan_status",
                "scan_engine",
                "scan_result",
                "scanned_at",
                "safe_at",
            ]
        )

        try:
            if not attachment.storage_key:
                raise AttachmentScanError("Quarantined attachment content is unavailable.")
            with default_storage.open(attachment.storage_key, "rb") as stream:
                verdict = scanner.scan(cast(BinaryIO, stream))
        except AttachmentScanError as exc:
            _record_attachment_scan_failure(attachment, scanner.engine_name, exc)
            raise
        except OSError as exc:
            scan_error = AttachmentScanError("Unable to read quarantined attachment content.")
            _record_attachment_scan_failure(attachment, scanner.engine_name, scan_error)
            raise scan_error from exc

        attachment.scan_engine = scanner.engine_name
        attachment.scanned_at = timezone.now()
        attachment.safe_at = None
        if verdict.clean:
            attachment.scan_status = TicketAttachment.ScanStatus.SAFE
            attachment.scan_result = "OK"
            attachment.safe_at = attachment.scanned_at
        else:
            attachment.scan_status = TicketAttachment.ScanStatus.INFECTED
            attachment.scan_result = verdict.signature or "Malware detected"
        attachment.save(
            update_fields=[
                "scan_status",
                "scan_engine",
                "scan_result",
                "scanned_at",
                "safe_at",
            ]
        )
        return 1


@shared_task(
    name="ticketing.deliver_ticket_reply",
    autoretry_for=RETRYABLE_GRAPH_ERRORS,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
)
def deliver_ticket_reply_task(message_id: int) -> int:
    """Deliver one queued outbound ticket reply through its Microsoft 365 mailbox."""
    message = (
        TicketMessage.objects.select_related(
            "ticket__mailbox__graph_connection__credential",
            "ticket__mailbox",
            "ticket",
        )
        .filter(id=message_id)
        .first()
    )
    if message is None or not _message_can_deliver(message):
        return 0

    with _ticket_reply_delivery_lock(message.id) as acquired:
        if not acquired:
            return 0

        message.refresh_from_db()
        if message.delivery_status == DELIVERY_STATUS_SENT:
            return 0
        return _deliver_graph_ticket_reply(message)


def _mailbox_can_sync(mailbox: Mailbox) -> bool:
    return bool(
        mailbox.enabled
        and mailbox.graph_connection.enabled
        and mailbox.graph_connection.credential_id
        and mailbox.graph_connection.authentication_method in BACKGROUND_AUTH_METHODS
    )


def _message_can_deliver(message: TicketMessage) -> bool:
    return bool(
        message.direction == TicketMessage.Direction.OUTBOUND
        and message.provider == GRAPH_PROVIDER
        and message.provider_reply_to_message_id
        and message.delivery_status != DELIVERY_STATUS_SENT
    )


def _deliver_graph_ticket_reply(message: TicketMessage) -> int:
    ticket = message.ticket
    mailbox = ticket.mailbox
    if mailbox is None:
        fail_ticket_reply(message, "Ticket mailbox is no longer configured.")
        return 0
    if not _mailbox_can_sync(mailbox):
        fail_ticket_reply(message, "Ticket mailbox is not eligible for background Graph delivery.")
        return 0

    mark_ticket_reply_sending(message)
    token_provider = MicrosoftGraphTokenProvider(mailbox.graph_connection)
    adapter = MicrosoftGraphOutboundAdapter(token_provider)
    try:
        receipt = adapter.send_reply(
            mailbox,
            message.provider_reply_to_message_id,
            ticket_reference=ticket.reference,
            ticket_subject=ticket.subject,
            body_html=message.body_html,
            body_text=message.body_text,
            cc_recipients=message.cc_recipients,
            bcc_recipients=message.bcc_recipients,
        )
    except RETRYABLE_GRAPH_ERRORS as exc:
        fail_ticket_reply(message, f"{type(exc).__name__}: {exc}")
        raise

    complete_ticket_reply(
        message,
        provider_message_id=receipt.provider_message_id,
        internet_message_id=receipt.internet_message_id,
    )
    return 1


def _consume_canonical_message(
    mailbox: Mailbox,
    canonical: CanonicalMessage,
    *,
    adapter: MicrosoftGraphAdapter,
) -> None:
    result = ingest_canonical_message(mailbox, canonical)
    if not canonical.has_attachments:
        return

    for payload in adapter.fetch_file_attachments(mailbox, canonical.provider_message_id):
        quarantined = quarantine_attachment(result.message, payload)
        if malware_scanning_enabled() and quarantined.attachment.scan_status in (
            TicketAttachment.ScanStatus.PENDING,
            TicketAttachment.ScanStatus.FAILED,
        ):
            scan_ticket_attachment_task.delay(quarantined.attachment.id)


def _record_attachment_scan_failure(
    attachment: TicketAttachment,
    engine_name: str,
    error: Exception,
) -> None:
    attachment.scan_status = TicketAttachment.ScanStatus.FAILED
    attachment.scan_engine = engine_name
    attachment.scan_result = f"{type(error).__name__}: {error}"[:2000]
    attachment.scanned_at = timezone.now()
    attachment.safe_at = None
    attachment.save(
        update_fields=[
            "scan_status",
            "scan_engine",
            "scan_result",
            "scanned_at",
            "safe_at",
        ]
    )


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


@contextmanager
def _ticket_reply_delivery_lock(message_id: int) -> Iterator[bool]:
    """Prevent concurrent workers from sending the same queued ticket reply."""
    redis = get_redis_connection("default")
    lock = redis.lock(
        f"{REPLY_DELIVERY_LOCK_PREFIX}:{message_id}",
        timeout=REPLY_DELIVERY_LOCK_SECONDS,
        blocking_timeout=0,
    )
    acquired = bool(lock.acquire(blocking=False))
    try:
        yield acquired
    finally:
        if acquired:
            with suppress(LockError):
                lock.release()


@contextmanager
def _ticket_attachment_scan_lock(attachment_id: int) -> Iterator[bool]:
    """Prevent duplicate scanner workers from scanning the same attachment concurrently."""
    redis = get_redis_connection("default")
    lock = redis.lock(
        f"{ATTACHMENT_SCAN_LOCK_PREFIX}:{attachment_id}",
        timeout=ATTACHMENT_SCAN_LOCK_SECONDS,
        blocking_timeout=0,
    )
    acquired = bool(lock.acquire(blocking=False))
    try:
        yield acquired
    finally:
        if acquired:
            with suppress(LockError):
                lock.release()
