from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from pathlib import PurePosixPath

from django.core.files.base import ContentFile
from django.core.files.storage import Storage, default_storage
from django.db import IntegrityError
from django.utils import timezone

from apps.ticketing.models import TicketAttachment, TicketMessage

DEFAULT_MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024
_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._() -]+")


class AttachmentQuarantineError(ValueError):
    """Raised when an attachment cannot safely enter quarantine."""


@dataclass(frozen=True, slots=True)
class AttachmentPayload:
    provider_attachment_id: str
    filename: str
    content: bytes
    declared_content_type: str = ""
    reported_size: int | None = None
    content_id: str = ""
    is_inline: bool = False


@dataclass(frozen=True, slots=True)
class QuarantinedAttachmentResult:
    attachment: TicketAttachment
    created: bool


def quarantine_attachment(
    message: TicketMessage,
    payload: AttachmentPayload,
    *,
    storage: Storage | None = None,
    max_bytes: int = DEFAULT_MAX_ATTACHMENT_BYTES,
) -> QuarantinedAttachmentResult:
    """Persist an untrusted attachment in quarantine before any scanning or use."""
    provider_attachment_id = payload.provider_attachment_id.strip()
    if not provider_attachment_id:
        raise AttachmentQuarantineError("A provider attachment ID is required.")
    if max_bytes <= 0:
        raise AttachmentQuarantineError("The attachment size limit must be positive.")

    existing = TicketAttachment.objects.filter(
        message=message,
        provider_attachment_id=provider_attachment_id,
    ).first()
    if existing is not None:
        return QuarantinedAttachmentResult(attachment=existing, created=False)

    content_size = len(payload.content)
    if payload.reported_size is not None and payload.reported_size < 0:
        raise AttachmentQuarantineError("The provider reported an invalid attachment size.")
    if content_size > max_bytes or (
        payload.reported_size is not None and payload.reported_size > max_bytes
    ):
        raise AttachmentQuarantineError(
            f"Attachment exceeds the {max_bytes}-byte quarantine limit."
        )

    safe_filename = _safe_filename(payload.filename)
    storage_backend = storage or default_storage
    storage_key = storage_backend.save(
        f"ticketing/quarantine/{uuid.uuid4().hex}/{safe_filename}",
        ContentFile(payload.content),
    )

    try:
        attachment = TicketAttachment.objects.create(
            message=message,
            provider_attachment_id=provider_attachment_id,
            original_filename=safe_filename,
            content_id=payload.content_id.strip()[:512],
            is_inline=payload.is_inline,
            storage_key=storage_key,
            declared_content_type=payload.declared_content_type.strip()[:255],
            detected_content_type=_detect_content_type(payload.content),
            size=content_size,
            sha256=hashlib.sha256(payload.content).hexdigest(),
            scan_status=TicketAttachment.ScanStatus.PENDING,
            quarantined_at=timezone.now(),
        )
    except IntegrityError:
        storage_backend.delete(storage_key)
        existing = TicketAttachment.objects.filter(
            message=message,
            provider_attachment_id=provider_attachment_id,
        ).first()
        if existing is None:
            raise
        return QuarantinedAttachmentResult(attachment=existing, created=False)
    except Exception:
        storage_backend.delete(storage_key)
        raise

    return QuarantinedAttachmentResult(attachment=attachment, created=True)


def _safe_filename(filename: str) -> str:
    normalised = filename.replace("\\", "/").strip()
    basename = PurePosixPath(normalised).name
    printable = "".join(character for character in basename if character.isprintable())
    safe = _SAFE_FILENAME_RE.sub("_", printable).strip(" .")
    if not safe:
        safe = "attachment.bin"

    if len(safe) <= 180:
        return safe

    suffix = PurePosixPath(safe).suffix[:20]
    stem_length = max(1, 180 - len(suffix))
    return f"{safe[:stem_length].rstrip(' .')}{suffix}"


def _detect_content_type(content: bytes) -> str:
    if content.startswith(b"%PDF-"):
        return "application/pdf"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if content.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        return "application/zip"
    return "application/octet-stream"
