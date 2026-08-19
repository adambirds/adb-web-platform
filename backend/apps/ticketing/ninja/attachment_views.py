from __future__ import annotations

from typing import Any

from django.core.files.storage import default_storage
from django.http import FileResponse, HttpRequest, JsonResponse
from ninja import Router

from apps.access_control.policies import can_access_client, can_access_ticket_queue
from apps.ticketing.config import malware_scanning_enabled
from apps.ticketing.models import Ticket, TicketAttachment

attachment_router = Router(tags=["admin-ticket-attachments"])


def _problem(status: int, message: str, code: str) -> JsonResponse:
    return JsonResponse(
        {
            "message": message,
            "success": False,
            "code": code,
        },
        status=status,
    )


def _can_view_ticket(user: Any, ticket: Ticket) -> bool:
    if user.is_superuser:
        return True
    if not can_access_ticket_queue(user, ticket.queue):
        return False
    if ticket.client is not None and not can_access_client(user, ticket.client):
        return False
    return True


def _attachment_is_downloadable(attachment: TicketAttachment) -> bool:
    if not attachment.storage_key:
        return False
    if attachment.scan_status == TicketAttachment.ScanStatus.SAFE:
        return attachment.safe_at is not None
    if malware_scanning_enabled():
        return False
    return attachment.scan_status in {
        TicketAttachment.ScanStatus.PENDING,
        TicketAttachment.ScanStatus.FAILED,
    }


@attachment_router.get("/ticket-attachments/{attachment_id}/download")
def download_ticket_attachment(
    request: HttpRequest,
    attachment_id: int,
) -> FileResponse | JsonResponse:
    """Stream an attachment when its current malware-scanning policy allows access."""
    if not request.user.is_authenticated:
        return _problem(401, "User not authenticated", "unauthenticated")
    if not (request.user.is_staff or request.user.is_superuser):
        return _problem(
            403,
            "You do not have permission to access this resource.",
            "forbidden",
        )
    if not request.user.has_perm("ticketing.view_ticket") or not request.user.has_perm(
        "ticketing.view_ticket_attachment"
    ):
        return _problem(
            403,
            "You do not have permission to view ticket attachments.",
            "forbidden",
        )

    attachment = (
        TicketAttachment.objects.select_related(
            "message__ticket__queue",
            "message__ticket__client",
        )
        .filter(id=attachment_id)
        .first()
    )
    if attachment is None or not _can_view_ticket(request.user, attachment.message.ticket):
        return _problem(404, "Attachment not found.", "not_found")

    if not _attachment_is_downloadable(attachment):
        return _problem(
            409,
            "Attachment is not available under the current malware-scanning policy.",
            "attachment_not_safe",
        )
    if not default_storage.exists(attachment.storage_key):
        return _problem(404, "Attachment content is unavailable.", "content_not_found")

    file_handle = default_storage.open(attachment.storage_key, "rb")
    response = FileResponse(
        file_handle,
        as_attachment=True,
        filename=attachment.original_filename,
        content_type=attachment.detected_content_type or "application/octet-stream",
    )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
