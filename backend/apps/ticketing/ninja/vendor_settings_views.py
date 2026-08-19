from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpRequest
from ninja import Router, Schema

from apps.ticketing.config import malware_scanning_enabled
from apps.ticketing.models import Ticket, TicketQueue, Vendor, VendorSenderRule
from authentication.ninja.schemas import ProblemDetail

vendor_settings_router = Router(tags=["admin-ticketing-vendors"])

StaffProblem = tuple[int, dict[str, Any]]


class TicketingRuntimeOut(Schema):
    malware_scanning_enabled: bool


class VendorOut(Schema):
    id: int
    name: str
    website_url: str
    notes: str
    enabled: bool


class VendorIn(Schema):
    name: str
    website_url: str = ""
    notes: str = ""
    enabled: bool = True


class VendorSenderRuleOut(Schema):
    id: int
    vendor_id: int
    vendor_name: str
    match_type: str
    match_value: str
    target_queue_id: int | None
    target_queue_name: str | None
    priority: str
    enabled: bool
    ordering: int
    notes: str


class VendorSenderRuleIn(Schema):
    vendor_id: int
    match_type: str
    match_value: str
    target_queue_id: int | None = None
    priority: str = ""
    enabled: bool = True
    ordering: int = 0
    notes: str = ""


class EnabledIn(Schema):
    enabled: bool


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


def _problem(message: str, code: str = "invalid") -> StaffProblem:
    return 400, {"message": message, "success": False, "code": code}


def _vendor_out(vendor: Vendor) -> VendorOut:
    return VendorOut(
        id=vendor.id,
        name=vendor.name,
        website_url=vendor.website_url,
        notes=vendor.notes,
        enabled=vendor.enabled,
    )


def _rule_out(rule: VendorSenderRule) -> VendorSenderRuleOut:
    return VendorSenderRuleOut(
        id=rule.id,
        vendor_id=rule.vendor_id,
        vendor_name=rule.vendor.name,
        match_type=rule.match_type,
        match_value=rule.match_value,
        target_queue_id=rule.target_queue_id,
        target_queue_name=rule.target_queue.name if rule.target_queue else None,
        priority=rule.priority,
        enabled=rule.enabled,
        ordering=rule.ordering,
        notes=rule.notes,
    )


def _validation_message(error: DjangoValidationError) -> str:
    if hasattr(error, "message_dict"):
        messages = [message for values in error.message_dict.values() for message in values]
        if messages:
            return messages[0]
    return str(error)


@vendor_settings_router.get(
    "/settings/ticketing/runtime",
    response={200: TicketingRuntimeOut, 401: ProblemDetail, 403: ProblemDetail},
)
def get_ticketing_runtime(request: HttpRequest) -> TicketingRuntimeOut | StaffProblem:
    problem = _staff_problem(request)
    if problem:
        return problem
    if not request.user.has_perm("ticketing.view_ticket"):
        return 403, {
            "message": "You do not have permission to view ticketing runtime settings.",
            "success": False,
            "code": "forbidden",
        }
    return TicketingRuntimeOut(malware_scanning_enabled=malware_scanning_enabled())


@vendor_settings_router.get(
    "/settings/ticketing/vendors",
    response={200: list[VendorOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_vendors(request: HttpRequest) -> list[VendorOut] | StaffProblem:
    problem = _staff_problem(request)
    if problem:
        return problem
    if not request.user.has_perm("ticketing.view_vendor"):
        return 403, {
            "message": "You do not have permission to view ticket vendors.",
            "success": False,
            "code": "forbidden",
        }
    return [_vendor_out(vendor) for vendor in Vendor.objects.order_by("name")]


@vendor_settings_router.post(
    "/settings/ticketing/vendors",
    response={200: VendorOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail},
)
def create_vendor(request: HttpRequest, data: VendorIn) -> VendorOut | StaffProblem:
    problem = _staff_problem(request)
    if problem:
        return problem
    if not request.user.has_perm("ticketing.configure_vendors"):
        return 403, {
            "message": "You do not have permission to configure ticket vendors.",
            "success": False,
            "code": "forbidden",
        }

    name = data.name.strip()
    if not name:
        return _problem("Vendor name is required.", "vendor_name_required")
    if Vendor.objects.filter(name__iexact=name).exists():
        return _problem("A vendor with this name already exists.", "duplicate_vendor")

    vendor = Vendor(
        name=name,
        website_url=data.website_url.strip(),
        notes=data.notes.strip(),
        enabled=data.enabled,
    )
    try:
        vendor.full_clean()
    except DjangoValidationError as exc:
        return _problem(_validation_message(exc), "invalid_vendor")
    vendor.save()
    return _vendor_out(vendor)


@vendor_settings_router.put(
    "/settings/ticketing/vendors/{vendor_id}/enabled",
    response={200: VendorOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def set_vendor_enabled(
    request: HttpRequest,
    vendor_id: int,
    data: EnabledIn,
) -> VendorOut | StaffProblem:
    problem = _staff_problem(request)
    if problem:
        return problem
    if not request.user.has_perm("ticketing.configure_vendors"):
        return 403, {
            "message": "You do not have permission to configure ticket vendors.",
            "success": False,
            "code": "forbidden",
        }
    vendor = Vendor.objects.filter(id=vendor_id).first()
    if vendor is None:
        return 404, {
            "message": "Vendor not found.",
            "success": False,
            "code": "not_found",
        }
    vendor.enabled = data.enabled
    vendor.save(update_fields=["enabled", "updated_at"])
    return _vendor_out(vendor)


@vendor_settings_router.get(
    "/settings/ticketing/vendor-sender-rules",
    response={200: list[VendorSenderRuleOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_vendor_sender_rules(request: HttpRequest) -> list[VendorSenderRuleOut] | StaffProblem:
    problem = _staff_problem(request)
    if problem:
        return problem
    if not request.user.has_perm("ticketing.view_vendorsenderrule"):
        return 403, {
            "message": "You do not have permission to view vendor sender rules.",
            "success": False,
            "code": "forbidden",
        }
    rules = VendorSenderRule.objects.select_related("vendor", "target_queue").order_by(
        "ordering", "vendor__name", "match_value"
    )
    return [_rule_out(rule) for rule in rules]


@vendor_settings_router.post(
    "/settings/ticketing/vendor-sender-rules",
    response={
        200: VendorSenderRuleOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
    },
)
def create_vendor_sender_rule(
    request: HttpRequest,
    data: VendorSenderRuleIn,
) -> VendorSenderRuleOut | StaffProblem:
    problem = _staff_problem(request)
    if problem:
        return problem
    if not request.user.has_perm("ticketing.configure_vendors"):
        return 403, {
            "message": "You do not have permission to configure vendor sender rules.",
            "success": False,
            "code": "forbidden",
        }

    vendor = Vendor.objects.filter(id=data.vendor_id).first()
    if vendor is None:
        return _problem("Vendor not found.", "vendor_not_found")
    if data.match_type not in VendorSenderRule.MatchType.values:
        return _problem("Unsupported vendor sender match type.", "invalid_match_type")
    if data.priority and data.priority not in Ticket.Priority.values:
        return _problem("Unsupported ticket priority.", "invalid_priority")

    queue = None
    if data.target_queue_id is not None:
        queue = TicketQueue.objects.filter(id=data.target_queue_id, enabled=True).first()
        if queue is None:
            return _problem("Enabled target queue not found.", "queue_not_found")

    match_value = data.match_value.strip().lower().lstrip("@")
    if VendorSenderRule.objects.filter(
        match_type=data.match_type,
        match_value=match_value,
    ).exists():
        return _problem("A sender rule already exists for this match.", "duplicate_sender_rule")

    rule = VendorSenderRule(
        vendor=vendor,
        match_type=data.match_type,
        match_value=match_value,
        target_queue=queue,
        priority=data.priority,
        enabled=data.enabled,
        ordering=max(data.ordering, 0),
        notes=data.notes.strip(),
    )
    try:
        rule.full_clean()
    except DjangoValidationError as exc:
        return _problem(_validation_message(exc), "invalid_sender_rule")
    rule.save()
    return _rule_out(rule)


@vendor_settings_router.put(
    "/settings/ticketing/vendor-sender-rules/{rule_id}/enabled",
    response={
        200: VendorSenderRuleOut,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def set_vendor_sender_rule_enabled(
    request: HttpRequest,
    rule_id: int,
    data: EnabledIn,
) -> VendorSenderRuleOut | StaffProblem:
    problem = _staff_problem(request)
    if problem:
        return problem
    if not request.user.has_perm("ticketing.configure_vendors"):
        return 403, {
            "message": "You do not have permission to configure vendor sender rules.",
            "success": False,
            "code": "forbidden",
        }
    rule = (
        VendorSenderRule.objects.select_related("vendor", "target_queue").filter(id=rule_id).first()
    )
    if rule is None:
        return 404, {
            "message": "Vendor sender rule not found.",
            "success": False,
            "code": "not_found",
        }
    rule.enabled = data.enabled
    rule.save(update_fields=["enabled", "updated_at"])
    return _rule_out(rule)
