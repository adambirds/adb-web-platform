from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from django.db.models import Q, QuerySet
from django.http import HttpRequest
from ninja import Router, Schema

from apps.access_control.policies import (
    can_access_client,
    can_access_ticket_queue,
    scope_clients_for_user,
    scope_ticket_queues_for_user,
)
from apps.ticketing.models import Ticket, TicketQueue
from apps.ticketing.services.operations import (
    TicketOperationError,
    assign_ticket,
    move_ticket_queue,
    set_ticket_priority,
    set_ticket_status,
)
from authentication.models import User
from authentication.ninja.schemas import ProblemDetail

operations_router = Router(tags=["admin-ticket-operations"])

StaffProblem = tuple[int, dict[str, Any]]
TERMINAL_STATUSES = {Ticket.Status.RESOLVED, Ticket.Status.CLOSED}
NON_TERMINAL_STATUSES = (
    Ticket.Status.NEW,
    Ticket.Status.OPEN,
    Ticket.Status.WAITING_CUSTOMER,
    Ticket.Status.WAITING_INTERNAL,
    Ticket.Status.SPAM,
)


class TicketChoiceOut(Schema):
    value: str
    label: str


class TicketAgentOut(Schema):
    id: UUID
    name: str
    email: str


class TicketQueueOptionOut(Schema):
    id: int
    name: str
    brand_id: int | None
    brand_name: str | None


class TicketMutableOut(Schema):
    id: int
    status: str
    priority: str
    queue_id: int
    queue_name: str
    assigned_to_id: UUID | None
    assigned_to_name: str | None
    resolved_at: datetime | None
    closed_at: datetime | None
    updated_at: datetime


class TicketOperationOptionsOut(Schema):
    ticket: TicketMutableOut
    can_assign: bool
    can_change: bool
    can_close: bool
    statuses: list[TicketChoiceOut]
    priorities: list[TicketChoiceOut]
    queues: list[TicketQueueOptionOut]
    assignees: list[TicketAgentOut]


class TicketAssignmentIn(Schema):
    assigned_to_id: UUID | None = None


class TicketStatusIn(Schema):
    status: str


class TicketPriorityIn(Schema):
    priority: str


class TicketQueueIn(Schema):
    queue_id: int


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


def _visible_tickets(request: HttpRequest) -> QuerySet[Ticket]:
    tickets = Ticket.objects.select_related(
        "brand",
        "queue",
        "client",
        "assigned_to",
    )
    if request.user.is_superuser:
        return tickets

    clients = scope_clients_for_user(request.user)
    queues = scope_ticket_queues_for_user(request.user)
    return tickets.filter(
        Q(queue__in=queues) & (Q(client__isnull=True) | Q(client__in=clients))
    ).distinct()


def _ticket_or_problem(
    request: HttpRequest,
    ticket_id: int,
) -> tuple[Ticket | None, StaffProblem | None]:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return None, staff_problem
    if not request.user.has_perm("ticketing.view_ticket"):
        return None, (
            403,
            {
                "message": "You do not have permission to view tickets.",
                "success": False,
                "code": "forbidden",
            },
        )

    ticket = _visible_tickets(request).filter(id=ticket_id).first()
    if ticket is None:
        return None, (
            404,
            {
                "message": "Ticket not found.",
                "success": False,
                "code": "not_found",
            },
        )
    return ticket, None


def _user_label(user: User | None) -> str | None:
    if user is None:
        return None
    return user.get_full_name().strip() or user.email


def _mutable_out(ticket: Ticket) -> TicketMutableOut:
    return TicketMutableOut(
        id=ticket.id,
        status=ticket.status,
        priority=ticket.priority,
        queue_id=ticket.queue_id,
        queue_name=ticket.queue.name,
        assigned_to_id=ticket.assigned_to_id,
        assigned_to_name=_user_label(ticket.assigned_to),
        resolved_at=ticket.resolved_at,
        closed_at=ticket.closed_at,
        updated_at=ticket.updated_at,
    )


def _choice(value: str, label: str) -> TicketChoiceOut:
    return TicketChoiceOut(value=value, label=label)


def _status_options(ticket: Ticket, request: HttpRequest) -> list[TicketChoiceOut]:
    can_change = request.user.has_perm("ticketing.change_ticket")
    can_close = request.user.has_perm("ticketing.close_ticket")
    current_is_terminal = ticket.status in TERMINAL_STATUSES

    allowed: list[str] = [ticket.status]
    if can_change and (not current_is_terminal or can_close):
        allowed.extend(NON_TERMINAL_STATUSES)
    if can_close:
        allowed.extend((Ticket.Status.RESOLVED, Ticket.Status.CLOSED))
        if current_is_terminal:
            allowed.append(Ticket.Status.OPEN)

    labels = dict(Ticket.Status.choices)
    return [_choice(value, str(labels[value])) for value in dict.fromkeys(allowed)]


def _agent_can_access_ticket(agent: User, ticket: Ticket) -> bool:
    if not agent.has_perm("ticketing.view_ticket"):
        return False
    if not can_access_ticket_queue(agent, ticket.queue):
        return False
    if ticket.client is not None and not can_access_client(agent, ticket.client):
        return False
    return True


def _assignee_options(ticket: Ticket) -> list[TicketAgentOut]:
    agents: list[TicketAgentOut] = []
    seen: set[UUID] = set()
    candidates = User.objects.filter(is_staff=True, is_active=True).order_by(
        "first_name",
        "last_name",
        "email",
    )
    for agent in candidates:
        if not _agent_can_access_ticket(agent, ticket):
            continue
        agents.append(
            TicketAgentOut(
                id=agent.id,
                name=_user_label(agent) or agent.email,
                email=agent.email,
            )
        )
        seen.add(agent.id)

    current = ticket.assigned_to
    if current is not None and current.id not in seen:
        agents.append(
            TicketAgentOut(
                id=current.id,
                name=_user_label(current) or current.email,
                email=current.email,
            )
        )
    return agents


def _queue_options(ticket: Ticket, request: HttpRequest) -> list[TicketQueueOptionOut]:
    queues = (
        scope_ticket_queues_for_user(
            request.user,
            TicketQueue.objects.select_related("brand"),
        )
        .filter(Q(brand_id=ticket.brand_id) | Q(brand__isnull=True))
        .filter(Q(enabled=True) | Q(id=ticket.queue_id))
    )

    return [
        TicketQueueOptionOut(
            id=queue.id,
            name=queue.name,
            brand_id=queue.brand_id,
            brand_name=queue.brand.name if queue.brand else None,
        )
        for queue in queues.order_by("ordering", "name")
    ]


@operations_router.get(
    "/tickets/{ticket_id}/operations",
    response={
        200: TicketOperationOptionsOut,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def ticket_operation_options(
    request: HttpRequest,
    ticket_id: int,
) -> TicketOperationOptionsOut | StaffProblem:
    ticket, problem = _ticket_or_problem(request, ticket_id)
    if problem:
        return problem
    assert ticket is not None

    can_assign = request.user.has_perm("ticketing.assign_ticket")
    can_change = request.user.has_perm("ticketing.change_ticket")
    can_close = request.user.has_perm("ticketing.close_ticket")

    return TicketOperationOptionsOut(
        ticket=_mutable_out(ticket),
        can_assign=can_assign,
        can_change=can_change,
        can_close=can_close,
        statuses=_status_options(ticket, request),
        priorities=(
            [_choice(value, str(label)) for value, label in Ticket.Priority.choices]
            if can_change
            else []
        ),
        queues=_queue_options(ticket, request) if can_change else [],
        assignees=_assignee_options(ticket) if can_assign else [],
    )


@operations_router.post(
    "/tickets/{ticket_id}/assignment",
    response={
        200: TicketMutableOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_ticket_assignment(
    request: HttpRequest,
    ticket_id: int,
    data: TicketAssignmentIn,
) -> TicketMutableOut | StaffProblem:
    ticket, problem = _ticket_or_problem(request, ticket_id)
    if problem:
        return problem
    assert ticket is not None

    if not request.user.has_perm("ticketing.assign_ticket"):
        return 403, {
            "message": "You do not have permission to assign tickets.",
            "success": False,
            "code": "forbidden",
        }

    assignee: User | None = None
    if data.assigned_to_id is not None:
        assignee = User.objects.filter(
            id=data.assigned_to_id,
            is_staff=True,
            is_active=True,
        ).first()
        if assignee is None or not _agent_can_access_ticket(assignee, ticket):
            return 400, {
                "message": "The selected assignee cannot access this ticket.",
                "success": False,
                "code": "assignee_unavailable",
            }

    try:
        assign_ticket(ticket, assignee)
    except TicketOperationError as exc:
        return 400, {
            "message": str(exc),
            "success": False,
            "code": "assignment_invalid",
        }
    return _mutable_out(ticket)


@operations_router.post(
    "/tickets/{ticket_id}/priority",
    response={
        200: TicketMutableOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_ticket_priority(
    request: HttpRequest,
    ticket_id: int,
    data: TicketPriorityIn,
) -> TicketMutableOut | StaffProblem:
    ticket, problem = _ticket_or_problem(request, ticket_id)
    if problem:
        return problem
    assert ticket is not None

    if not request.user.has_perm("ticketing.change_ticket"):
        return 403, {
            "message": "You do not have permission to change ticket priority.",
            "success": False,
            "code": "forbidden",
        }
    try:
        set_ticket_priority(ticket, data.priority)
    except TicketOperationError as exc:
        return 400, {
            "message": str(exc),
            "success": False,
            "code": "priority_invalid",
        }
    return _mutable_out(ticket)


@operations_router.post(
    "/tickets/{ticket_id}/queue",
    response={
        200: TicketMutableOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_ticket_queue(
    request: HttpRequest,
    ticket_id: int,
    data: TicketQueueIn,
) -> TicketMutableOut | StaffProblem:
    ticket, problem = _ticket_or_problem(request, ticket_id)
    if problem:
        return problem
    assert ticket is not None

    if not request.user.has_perm("ticketing.change_ticket"):
        return 403, {
            "message": "You do not have permission to move tickets between queues.",
            "success": False,
            "code": "forbidden",
        }

    queue = (
        scope_ticket_queues_for_user(
            request.user,
            TicketQueue.objects.select_related("brand"),
        )
        .filter(id=data.queue_id)
        .first()
    )
    if queue is None:
        return 400, {
            "message": "The selected queue is not available.",
            "success": False,
            "code": "queue_unavailable",
        }
    try:
        move_ticket_queue(ticket, queue)
    except TicketOperationError as exc:
        return 400, {
            "message": str(exc),
            "success": False,
            "code": "queue_invalid",
        }
    return _mutable_out(ticket)


@operations_router.post(
    "/tickets/{ticket_id}/status",
    response={
        200: TicketMutableOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_ticket_status(
    request: HttpRequest,
    ticket_id: int,
    data: TicketStatusIn,
) -> TicketMutableOut | StaffProblem:
    ticket, problem = _ticket_or_problem(request, ticket_id)
    if problem:
        return problem
    assert ticket is not None

    try:
        target = Ticket.Status(data.status)
    except ValueError:
        return 400, {
            "message": "Unknown ticket status.",
            "success": False,
            "code": "status_invalid",
        }

    if target != ticket.status:
        current_is_terminal = ticket.status in TERMINAL_STATUSES
        target_is_terminal = target in TERMINAL_STATUSES
        can_change = request.user.has_perm("ticketing.change_ticket")
        can_close = request.user.has_perm("ticketing.close_ticket")

        if current_is_terminal:
            if not can_close or (
                target not in TERMINAL_STATUSES and target != Ticket.Status.OPEN and not can_change
            ):
                return 403, {
                    "message": "You do not have permission to reopen this ticket.",
                    "success": False,
                    "code": "forbidden",
                }
        elif target_is_terminal:
            if not can_close:
                return 403, {
                    "message": "You do not have permission to resolve or close tickets.",
                    "success": False,
                    "code": "forbidden",
                }
        elif not can_change:
            return 403, {
                "message": "You do not have permission to change ticket status.",
                "success": False,
                "code": "forbidden",
            }

    try:
        set_ticket_status(ticket, target)
    except TicketOperationError as exc:
        return 400, {
            "message": str(exc),
            "success": False,
            "code": "status_invalid",
        }
    return _mutable_out(ticket)
