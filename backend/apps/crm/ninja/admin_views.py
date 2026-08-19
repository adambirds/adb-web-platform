from typing import Any, cast

from django.core.exceptions import ValidationError
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from ninja import Router

from apps.access_control.policies import scope_clients_for_user, scope_ticket_queues_for_user
from apps.core.models import Brand
from apps.crm.models import Lead, LeadSource, LeadStatus
from apps.crm.services import LeadOperationError, assign_lead, convert_lead
from apps.ticketing.models import Ticket
from authentication.models import User
from authentication.ninja.schemas import ProblemDetail

from .schemas import (
    LeadAgentOut,
    LeadAssignmentIn,
    LeadConversionOut,
    LeadDetailOut,
    LeadIn,
    LeadLookupOut,
    LeadOptionsOut,
    LeadSummaryOut,
    LeadTicketOut,
)

crm_admin_router = Router(tags=["admin-crm"])

StaffProblem = tuple[int, dict[str, Any]]


def _staff_problem(request: HttpRequest) -> StaffProblem | None:
    if not request.user.is_authenticated:
        return 401, {
            "message": "User not authenticated",
            "success": False,
            "code": "unauthenticated",
        }
    if not (request.user.is_staff or request.user.is_superuser):
        return 403, {
            "message": "You do not have permission to access this resource.",
            "success": False,
            "code": "forbidden",
        }
    return None


def _permission_problem(request: HttpRequest, permission: str) -> StaffProblem | None:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem
    if not request.user.has_perm(permission):
        return 403, {
            "message": "You do not have permission to access this resource.",
            "success": False,
            "code": "forbidden",
        }
    return None


def _validation_problem(error: ValidationError) -> StaffProblem:
    return 400, {
        "message": "; ".join(error.messages) or "Invalid lead details.",
        "success": False,
        "code": "validation_error",
    }


def _not_found_problem(resource: str) -> StaffProblem:
    return 404, {
        "message": f"{resource} not found.",
        "success": False,
        "code": "not_found",
    }


def _user_label(user: User | None) -> str | None:
    if user is None:
        return None
    return user.get_full_name().strip() or user.email


def _assignee_options() -> list[LeadAgentOut]:
    assignees: list[LeadAgentOut] = []
    for user in User.objects.filter(is_staff=True, is_active=True).order_by(
        "first_name",
        "last_name",
        "email",
    ):
        if not user.has_perm("crm.view_lead"):
            continue
        assignees.append(
            LeadAgentOut(
                id=user.id,
                name=_user_label(user) or user.email,
                email=user.email,
            )
        )
    return assignees


def _related_tickets(request: HttpRequest, lead: Lead) -> list[LeadTicketOut]:
    if not request.user.has_perm("ticketing.view_ticket"):
        return []

    tickets = Ticket.objects.select_related("queue").filter(
        Q(messages__sender_address__iexact=lead.email)
        | Q(primary_contact__email__iexact=lead.email)
    )
    if not request.user.is_superuser:
        clients = scope_clients_for_user(request.user)
        queues = scope_ticket_queues_for_user(request.user)
        tickets = tickets.filter(
            Q(queue__in=queues) & (Q(client__isnull=True) | Q(client__in=clients))
        )

    return [
        LeadTicketOut(
            id=ticket.id,
            reference=ticket.reference,
            subject=ticket.subject,
            status=ticket.status,
            priority=ticket.priority,
            queue_name=ticket.queue.name,
            last_message_at=ticket.last_message_at,
        )
        for ticket in tickets.distinct().order_by("-last_message_at", "-created_at")[:10]
    ]


def _build_lead_detail(request: HttpRequest, lead: Lead) -> LeadDetailOut:
    converted = lead.converted_at is not None
    return LeadDetailOut(
        id=lead.id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        company=lead.company,
        brand_id=lead.brand_id,
        brand_name=lead.brand.name if lead.brand else None,
        status_id=lead.status_id,
        status_name=lead.status.name if lead.status else None,
        source_id=lead.source_id,
        source_name=lead.source.name if lead.source else None,
        assigned_to_id=lead.assigned_to_id,
        assigned_to_name=_user_label(lead.assigned_to),
        converted_client_id=lead.converted_client_id,
        converted_contact_id=lead.converted_contact_id,
        converted_by_name=_user_label(lead.converted_by),
        converted_at=lead.converted_at,
        can_assign=request.user.has_perm("crm.assign_lead") and not converted,
        can_convert=(
            request.user.has_perm("crm.convert_lead")
            and request.user.has_perm("clients.add_client")
            and request.user.has_perm("clients.add_clientcontact")
            and not converted
        ),
        message=lead.message,
        notes=lead.notes,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
        related_tickets=_related_tickets(request, lead),
    )


def _apply_lead_payload(lead: Lead, payload: LeadIn) -> StaffProblem | None:
    brand = None
    if payload.brand_id is not None:
        brand = Brand.objects.filter(id=payload.brand_id).first()
        if brand is None:
            return _not_found_problem("Brand")

    status = None
    if payload.status_id is not None:
        status = LeadStatus.objects.filter(id=payload.status_id).first()
        if status is None:
            return _not_found_problem("Lead status")

    source = None
    if payload.source_id is not None:
        source = LeadSource.objects.filter(id=payload.source_id).first()
        if source is None:
            return _not_found_problem("Lead source")

    lead.name = payload.name.strip()
    lead.email = payload.email.strip().lower()
    lead.phone = payload.phone.strip()
    lead.company = payload.company.strip()
    lead.brand = brand
    lead.status = status
    lead.source = source
    lead.message = payload.message.strip()
    lead.notes = payload.notes.strip()
    return None


def _lead_queryset() -> QuerySet[Lead]:
    return Lead.objects.select_related(
        "brand",
        "status",
        "source",
        "assigned_to",
        "converted_client",
        "converted_contact",
        "converted_by",
    )


@crm_admin_router.get(
    "/leads",
    response={200: list[LeadSummaryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_leads(request: HttpRequest) -> list[LeadSummaryOut] | StaffProblem:
    problem = _permission_problem(request, "crm.view_lead")
    if problem:
        return problem

    leads = _lead_queryset().order_by("-created_at")
    return [
        LeadSummaryOut(
            id=lead.id,
            name=lead.name,
            company=lead.company,
            email=lead.email,
            status=lead.status.name if lead.status else "Unassigned",
            source=lead.source.name if lead.source else "Unknown",
            brand=lead.brand.name if lead.brand else "Unassigned",
            assigned_to_name=_user_label(lead.assigned_to),
            converted_at=lead.converted_at,
            created_at=lead.created_at,
        )
        for lead in leads
    ]


@crm_admin_router.get(
    "/lead-options",
    response={200: LeadOptionsOut, 401: ProblemDetail, 403: ProblemDetail},
)
def lead_options(request: HttpRequest) -> LeadOptionsOut | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem
    if not (
        request.user.has_perm("crm.view_lead")
        or request.user.has_perm("crm.add_lead")
        or request.user.has_perm("crm.change_lead")
    ):
        return 403, {
            "message": "You do not have permission to access lead configuration.",
            "success": False,
            "code": "forbidden",
        }

    return LeadOptionsOut(
        statuses=[
            LeadLookupOut(id=status.id, name=status.name)
            for status in LeadStatus.objects.order_by("order", "name")
        ],
        sources=[
            LeadLookupOut(id=source.id, name=source.name)
            for source in LeadSource.objects.order_by("name")
        ],
        assignees=_assignee_options() if request.user.has_perm("crm.assign_lead") else [],
    )


@crm_admin_router.post(
    "/leads",
    response={
        201: LeadDetailOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_lead(request: HttpRequest, payload: LeadIn) -> tuple[int, LeadDetailOut] | StaffProblem:
    problem = _permission_problem(request, "crm.add_lead")
    if problem:
        return problem

    lead = Lead()
    payload_problem = _apply_lead_payload(lead, payload)
    if payload_problem:
        return payload_problem
    try:
        lead.full_clean()
    except ValidationError as error:
        return _validation_problem(error)
    lead.save()
    return 201, _build_lead_detail(request, lead)


@crm_admin_router.get(
    "/leads/{lead_id}",
    response={200: LeadDetailOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def get_lead(request: HttpRequest, lead_id: int) -> LeadDetailOut | StaffProblem:
    problem = _permission_problem(request, "crm.view_lead")
    if problem:
        return problem

    lead = _lead_queryset().filter(id=lead_id).first()
    if lead is None:
        return _not_found_problem("Lead")
    return _build_lead_detail(request, lead)


@crm_admin_router.put(
    "/leads/{lead_id}",
    response={
        200: LeadDetailOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_lead(
    request: HttpRequest,
    lead_id: int,
    payload: LeadIn,
) -> LeadDetailOut | StaffProblem:
    problem = _permission_problem(request, "crm.change_lead")
    if problem:
        return problem

    lead = _lead_queryset().filter(id=lead_id).first()
    if lead is None:
        return _not_found_problem("Lead")

    payload_problem = _apply_lead_payload(lead, payload)
    if payload_problem:
        return payload_problem
    try:
        lead.full_clean()
    except ValidationError as error:
        return _validation_problem(error)
    lead.save()
    return _build_lead_detail(request, lead)


@crm_admin_router.post(
    "/leads/{lead_id}/assignment",
    response={
        200: LeadDetailOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_lead_assignment(
    request: HttpRequest,
    lead_id: int,
    payload: LeadAssignmentIn,
) -> LeadDetailOut | StaffProblem:
    problem = _permission_problem(request, "crm.assign_lead")
    if problem:
        return problem

    lead = _lead_queryset().filter(id=lead_id).first()
    if lead is None:
        return _not_found_problem("Lead")

    assignee: User | None = None
    if payload.assigned_to_id is not None:
        assignee = User.objects.filter(
            id=payload.assigned_to_id,
            is_staff=True,
            is_active=True,
        ).first()
        if assignee is None or not assignee.has_perm("crm.view_lead"):
            return 400, {
                "message": "The selected assignee cannot access leads.",
                "success": False,
                "code": "assignee_unavailable",
            }

    try:
        assign_lead(lead, assignee)
    except LeadOperationError as error:
        return 400, {
            "message": str(error),
            "success": False,
            "code": "assignment_invalid",
        }
    return _build_lead_detail(request, lead)


@crm_admin_router.post(
    "/leads/{lead_id}/convert",
    response={
        200: LeadConversionOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def convert_lead_to_client(
    request: HttpRequest,
    lead_id: int,
) -> LeadConversionOut | StaffProblem:
    problem = _permission_problem(request, "crm.convert_lead")
    if problem:
        return problem
    if not (
        request.user.has_perm("clients.add_client")
        and request.user.has_perm("clients.add_clientcontact")
    ):
        return 403, {
            "message": "You do not have permission to create the client and contact.",
            "success": False,
            "code": "forbidden",
        }

    lead = _lead_queryset().filter(id=lead_id).first()
    if lead is None:
        return _not_found_problem("Lead")

    user = cast(User, request.user)
    try:
        result = convert_lead(lead, user)
    except ValidationError as error:
        return _validation_problem(error)
    except LeadOperationError as error:
        return 400, {
            "message": str(error),
            "success": False,
            "code": "conversion_invalid",
        }

    lead = _lead_queryset().get(id=lead.id)
    return LeadConversionOut(
        lead=_build_lead_detail(request, lead),
        client_id=result.client.id,
        contact_id=result.contact.id,
        linked_ticket_count=result.linked_ticket_count,
    )
