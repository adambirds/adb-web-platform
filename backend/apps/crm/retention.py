from __future__ import annotations

import calendar
import logging
from dataclasses import dataclass
from datetime import datetime

from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from apps.clients.models import Client, ClientContact
from apps.core.models import AuditEvent
from apps.crm.models import Lead, LeadRetentionReview, LeadStatus
from apps.ticketing.models import Ticket, TicketAttachment, TicketMessage
from authentication.models import User

logger = logging.getLogger(__name__)
RETENTION_MONTHS = 36


def add_months(value: datetime, months: int) -> datetime:
    total = value.year * 12 + value.month - 1 + months
    year, month = divmod(total, 12)
    month += 1
    return value.replace(
        year=year, month=month, day=min(value.day, calendar.monthrange(year, month)[1])
    )


@dataclass(frozen=True)
class RetentionAssessment:
    last_activity_at: datetime
    due_at: datetime
    ticket_ids: tuple[int, ...]
    eligible: bool


def assess_lead(lead: Lead, *, now: datetime | None = None) -> RetentionAssessment:
    now = now or timezone.now()
    baseline = max(lead.created_at, lead.updated_at)
    empty = RetentionAssessment(baseline, add_months(baseline, RETENTION_MONTHS), (), False)
    if (
        lead.brand_id is None
        or lead.converted_at is not None
        or lead.converted_client_id is not None
        or lead.converted_contact_id is not None
        or lead.status is None
        or lead.status.outcome != LeadStatus.Outcome.LOST
    ):
        return empty
    if (
        Client.objects.filter(email__iexact=lead.email).exists()
        or ClientContact.objects.filter(email__iexact=lead.email).exists()
    ):
        return empty
    siblings = Lead.objects.filter(brand_id=lead.brand_id, email__iexact=lead.email).exclude(
        pk=lead.pk
    )
    if siblings.filter(
        Q(status__isnull=True)
        | ~Q(status__outcome=LeadStatus.Outcome.LOST)
        | Q(converted_at__isnull=False)
    ).exists():
        return empty
    sibling_activity = siblings.aggregate(latest=Max("updated_at"))["latest"]
    if sibling_activity is not None:
        baseline = max(baseline, sibling_activity)
    messages = (
        TicketMessage.objects.filter(ticket__brand_id=lead.brand_id)
        .filter(
            Q(sender_address__iexact=lead.email)
            | Q(to_recipients__icontains=lead.email)
            | Q(cc_recipients__icontains=lead.email)
            | Q(bcc_recipients__icontains=lead.email)
        )
        .select_related("ticket")
    )
    # Validate exact addresses after the deliberately broad JSON prefilter.
    tickets: dict[int, Ticket] = {}
    for message in messages:
        addresses = [
            message.sender_address,
            *message.to_recipients,
            *message.cc_recipients,
            *message.bcc_recipients,
        ]
        if lead.email.casefold() not in {str(address).casefold() for address in addresses}:
            continue
        tickets[message.ticket_id] = message.ticket
        baseline = max(baseline, message.sent_or_received_at, message.created_at)
        if message.direction == TicketMessage.Direction.OUTBOUND and message.delivery_status in {
            "queued",
            "sending",
        }:
            return empty
    for ticket in tickets.values():
        if (
            ticket.client_id is not None
            or ticket.primary_contact_id is not None
            or ticket.vendor_id is not None
            or ticket.time_entries.exists()
            or ticket.running_timers.exists()
        ):
            return empty
        if ticket.status not in {Ticket.Status.CLOSED, Ticket.Status.RESOLVED, Ticket.Status.SPAM}:
            return empty
        if (
            ticket.source != Ticket.Source.CONTACT_FORM
            and ticket.classification != Ticket.Classification.SALES
        ):
            return empty
        baseline = max(baseline, ticket.updated_at, ticket.last_message_at or ticket.created_at)
        note_activity = ticket.notes.aggregate(latest=Max("updated_at"))["latest"]
        if note_activity is not None:
            baseline = max(baseline, note_activity)
    due = add_months(baseline, RETENTION_MONTHS)
    # Shared correspondence is removed only after the last associated lead is approved.
    ticket_ids = () if siblings.exists() else tuple(sorted(tickets))
    return RetentionAssessment(baseline, due, ticket_ids, due <= now)


def refresh_retention_reviews(*, now: datetime | None = None) -> dict[str, int]:
    now = now or timezone.now()
    created = cancelled = 0
    cutoff = add_months(now, -RETENTION_MONTHS)
    candidates = Lead.objects.select_related("status").filter(
        status__outcome=LeadStatus.Outcome.LOST,
        converted_at__isnull=True,
        converted_client__isnull=True,
        updated_at__lte=cutoff,
    )
    for lead in candidates.iterator():
        assessment = assess_lead(lead, now=now)
        if not assessment.eligible:
            continue
        review, is_new = LeadRetentionReview.objects.get_or_create(
            lead=lead,
            defaults={"last_activity_at": assessment.last_activity_at, "due_at": assessment.due_at},
        )
        created += int(is_new)
        if not is_new and (
            review.status == review.Status.CANCELLED
            or (
                review.status == review.Status.DEFERRED
                and review.review_after is not None
                and review.review_after <= now
            )
        ):
            review.status = review.Status.PENDING
            review.last_activity_at = assessment.last_activity_at
            review.due_at = assessment.due_at
            review.save(update_fields=["status", "last_activity_at", "due_at", "updated_at"])
    for review in LeadRetentionReview.objects.filter(
        status=LeadRetentionReview.Status.PENDING
    ).select_related("lead__status"):
        if review.lead is None or not assess_lead(review.lead, now=now).eligible:
            review.status = review.Status.CANCELLED
            review.save(update_fields=["status", "updated_at"])
            cancelled += 1
    cleaned = cleanup_retention_files()
    return {"queued": created, "cancelled": cancelled, "files_cleaned": cleaned}


def cleanup_retention_files() -> int:
    cleaned = 0
    for review in LeadRetentionReview.objects.filter(
        status=LeadRetentionReview.Status.DELETED
    ).exclude(pending_storage_keys=[]):
        remaining: list[str] = []
        for key in review.pending_storage_keys:
            try:
                default_storage.delete(key)
                cleaned += 1
            except Exception:
                remaining.append(key)
                logger.warning("Retention attachment cleanup deferred; it will be retried.")
        review.pending_storage_keys = remaining
        review.save(update_fields=["pending_storage_keys", "updated_at"])
    return cleaned


@transaction.atomic
def approve_retention_review(review_id: int, user: User) -> LeadRetentionReview:
    if (
        not user.is_active
        or not user.is_staff
        or not user.has_perms(
            ["crm.view_lead", "crm.change_leadretentionreview", "crm.delete_lead"]
        )
    ):
        raise PermissionError("You do not have permission to approve lead deletion.")
    review = (
        LeadRetentionReview.objects.select_for_update(of=("self",))
        .select_related("lead__status")
        .get(pk=review_id)
    )
    if review.status != review.Status.PENDING or review.lead is None:
        raise ValueError("This review is no longer awaiting approval.")
    assert review.lead_id is not None
    lead = (
        Lead.objects.select_for_update(of=("self",)).select_related("status").get(pk=review.lead_id)
    )
    assessment = assess_lead(lead)
    if not assessment.eligible:
        raise ValueError(
            "This record has recent activity or is protected. Refresh the review list."
        )
    tickets = Ticket.objects.select_for_update(of=("self",)).filter(pk__in=assessment.ticket_ids)
    # Evaluate now: a lazy queryset would not lock the rows before reassessment.
    locked_ticket_ids = tuple(sorted(ticket.pk for ticket in tickets))
    if assessment.ticket_ids:
        from apps.access_control.policies import scope_ticket_queues_for_user

        if not user.has_perms(["ticketing.view_ticket", "ticketing.delete_ticket"]):
            raise PermissionError(
                "Deleting linked conversations requires ticket view and delete permission."
            )
        allowed = scope_ticket_queues_for_user(user)
        if not user.is_superuser and tickets.exclude(queue__in=allowed).exists():
            raise PermissionError("A linked conversation is outside your ticket queue access.")
    review.pending_storage_keys = list(
        TicketAttachment.objects.filter(message__ticket__in=tickets)
        .exclude(storage_key="")
        .values_list("storage_key", flat=True)
    )
    review.status = review.Status.DELETED
    review.decided_by = user
    review.decided_at = timezone.now()
    review.decision_reason = ""
    review.save()
    # Recheck after locking conversations to catch activity since the preview.
    current = assess_lead(lead)
    if not current.eligible or current.ticket_ids != locked_ticket_ids:
        raise ValueError("This record has recent activity. Refresh the review list.")
    AuditEvent.record(
        action="crm.retention_deleted",
        actor=user,
        target=review,
        target_label="Lead retention decision",
        metadata={"conversation_count": len(assessment.ticket_ids)},
    )
    tickets.delete()
    lead.delete()
    transaction.on_commit(cleanup_retention_files)
    return review


@transaction.atomic
def defer_retention_review(
    review_id: int, user: User, reason: str, months: int
) -> LeadRetentionReview:
    if (
        not user.is_active
        or not user.is_staff
        or not user.has_perms(["crm.view_lead", "crm.change_leadretentionreview"])
    ):
        raise PermissionError("You do not have permission to review lead retention.")
    if not reason.strip() or months not in {3, 6, 12}:
        raise ValueError(
            "Give a retention reason and choose a review interval of 3, 6 or 12 months."
        )
    review = LeadRetentionReview.objects.select_for_update(of=("self",)).get(pk=review_id)
    if review.status != review.Status.PENDING or review.lead_id is None:
        raise ValueError("This review is no longer awaiting a decision.")
    review.status = review.Status.DEFERRED
    review.decision_reason = reason.strip()
    review.review_after = add_months(timezone.now(), months)
    review.decided_by = user
    review.decided_at = timezone.now()
    review.save()
    AuditEvent.record(
        action="crm.retention_deferred",
        actor=user,
        target=review,
        target_label="Lead retention decision",
        metadata={"months": months},
    )
    return review
