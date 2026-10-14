from datetime import datetime
from math import ceil
from typing import Any, Literal, cast

from django.http import HttpRequest
from ninja import Router, Schema
from pydantic import Field

from apps.access_control.policies import scope_ticket_queues_for_user
from apps.crm.models import LeadRetentionReview
from apps.crm.retention import (
    RETENTION_MONTHS,
    approve_retention_review,
    assess_lead,
    defer_retention_review,
    refresh_retention_reviews,
)
from apps.ticketing.models import Ticket
from authentication.models import User
from authentication.ninja.schemas import ProblemDetail

from .admin_views import _permission_problem

retention_router = Router(tags=["admin-retention"])
Problem = tuple[int, dict[str, Any]]


class RetentionItem(Schema):
    id: int
    lead_id: int | None
    name: str
    email: str
    brand: str
    notes: str
    status: str
    due_at: datetime
    last_activity_at: datetime
    review_after: datetime | None
    decision_reason: str
    conversation_count: int | None
    can_approve: bool
    can_keep: bool
    files_pending: int


class RetentionPage(Schema):
    items: list[RetentionItem]
    page: int
    total: int
    total_pages: int
    retention_months: int
    can_scan: bool


class RetentionDecision(Schema):
    action: Literal["approve", "keep"]
    reason: str = Field(default="", max_length=2000)
    months: Literal[3, 6, 12] = 6


class ScanOut(Schema):
    queued: int
    cancelled: int
    files_cleaned: int


def permission(request: HttpRequest, change: bool = False) -> Problem | None:
    for capability in [
        "crm.view_lead",
        "crm.change_leadretentionreview" if change else "crm.view_leadretentionreview",
    ]:
        problem = _permission_problem(request, capability)
        if problem:
            return problem
    return None


@retention_router.get(
    "/retention/leads",
    response={200: RetentionPage, 401: ProblemDetail, 403: ProblemDetail, 400: ProblemDetail},
)
def list_reviews(
    request: HttpRequest, status: str = "pending", page: int = 1
) -> RetentionPage | Problem:
    problem = permission(request)
    if problem:
        return problem
    if page < 1 or status not in LeadRetentionReview.Status.values:
        return 400, {
            "message": "Invalid review filter.",
            "success": False,
            "code": "invalid_filter",
        }
    rows = (
        LeadRetentionReview.objects.filter(status=status)
        .select_related("lead__brand", "lead__status")
        .order_by("due_at", "id")
    )
    total = rows.count()
    user = cast(User, request.user)
    items: list[RetentionItem] = []
    for review in rows[(page - 1) * 25 : page * 25]:
        lead = review.lead
        eligible = False
        can_approve = False
        count: int | None = None
        if lead is not None:
            assessment = assess_lead(lead)
            eligible = assessment.eligible
            tickets = Ticket.objects.filter(pk__in=assessment.ticket_ids)
            visible = user.has_perm("ticketing.view_ticket") and (
                user.is_superuser
                or not tickets.exclude(queue__in=scope_ticket_queues_for_user(user)).exists()
            )
            count = len(assessment.ticket_ids) if visible or not assessment.ticket_ids else None
            can_approve = bool(
                eligible
                and user.has_perm("crm.delete_lead")
                and (
                    not assessment.ticket_ids
                    or (visible and user.has_perm("ticketing.delete_ticket"))
                )
            )
        can_change = (
            user.has_perm("crm.change_leadretentionreview")
            and review.status == review.Status.PENDING
        )
        items.append(
            RetentionItem(
                id=review.id,
                lead_id=review.lead_id,
                name=lead.name if lead else "Deleted record",
                email=lead.email if lead else "",
                brand=lead.brand.name if lead and lead.brand else "",
                notes=lead.notes if lead else "",
                status=review.status,
                due_at=review.due_at,
                last_activity_at=review.last_activity_at,
                review_after=review.review_after,
                decision_reason=review.decision_reason,
                conversation_count=count,
                can_approve=bool(can_change and can_approve),
                can_keep=bool(can_change and lead is not None),
                files_pending=len(review.pending_storage_keys),
            )
        )
    return RetentionPage(
        items=items,
        page=page,
        total=total,
        total_pages=max(1, ceil(total / 25)),
        retention_months=RETENTION_MONTHS,
        can_scan=user.has_perm("crm.change_leadretentionreview"),
    )


@retention_router.post(
    "/retention/leads/scan", response={200: ScanOut, 401: ProblemDetail, 403: ProblemDetail}
)
def scan_reviews(request: HttpRequest) -> ScanOut | Problem:
    problem = permission(request, change=True)
    if problem:
        return problem
    return ScanOut(**refresh_retention_reviews())


@retention_router.post(
    "/retention/leads/{review_id}/decision",
    response={
        200: dict,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def decide_review(
    request: HttpRequest, review_id: int, payload: RetentionDecision
) -> dict[str, Any] | Problem:
    problem = permission(request, change=True)
    if problem:
        return problem
    user = cast(User, request.user)
    try:
        if payload.action == "approve":
            if not user.has_perm("crm.delete_lead"):
                raise PermissionError("Deleting a lead requires lead delete permission.")
            review = approve_retention_review(review_id, user)
        else:
            review = defer_retention_review(review_id, user, payload.reason, payload.months)
    except LeadRetentionReview.DoesNotExist:
        return 404, {
            "message": "Retention review not found.",
            "success": False,
            "code": "not_found",
        }
    except PermissionError as error:
        return 403, {"message": str(error), "success": False, "code": "forbidden"}
    except ValueError as error:
        return 400, {"message": str(error), "success": False, "code": "review_changed"}
    return {"success": True, "status": review.status}
