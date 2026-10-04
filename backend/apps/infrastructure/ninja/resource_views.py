from __future__ import annotations

import math

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest
from ninja import Router

from apps.core.models import AuditEvent
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import InfrastructureResource, ResourceRelationship
from apps.infrastructure.policies import scope_infrastructure_resources_for_user
from apps.infrastructure.specialist_snapshot import specialist_resource_snapshot
from authentication.ninja.schemas import ProblemDetail

from .catalogue_schemas import BasicResourceIn, BasicResourceUpdateIn, ResourceMutationOut
from .resource_schemas import (
    InfrastructureRelationshipCreateIn,
    InfrastructureRelationshipOptionsOut,
    InfrastructureRelationshipOut,
    InfrastructureRelationshipTargetOut,
    InfrastructureRelationshipTypeOut,
    InfrastructureResourceDetailOut,
    InfrastructureResourcePageOut,
    InfrastructureResourceSummaryOut,
    InfrastructureTagOut,
    ResourceEnvironmentFilter,
    ResourceLifecycleFilter,
    ResourceOwnershipFilter,
    ResourceTypeFilter,
    SpecialistFieldOut,
)
from .specialist_views import _new_resource, _problem, _update_resource
from .specialist_views import _permission_problem as _write_permission_problem

infrastructure_resource_router = Router(tags=["admin-infrastructure-resources"])
StaffProblem = tuple[int, dict[str, object]]
CURRENT_LIFECYCLE_STATUSES = (
    InfrastructureResource.LifecycleStatus.PLANNED,
    InfrastructureResource.LifecycleStatus.ACTIVE,
    InfrastructureResource.LifecycleStatus.MAINTENANCE,
    InfrastructureResource.LifecycleStatus.DEPRECATED,
)


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


def _permission_problem(request: HttpRequest) -> StaffProblem | None:
    problem = _staff_problem(request)
    if problem:
        return problem
    if not request.user.has_perm("infrastructure.view_infrastructureresource"):
        return 403, {
            "message": "You do not have permission to view infrastructure resources.",
            "success": False,
            "code": "forbidden",
        }
    return None


def _relationship_permission_problem(
    request: HttpRequest,
    permission: str,
    message: str,
) -> StaffProblem | None:
    problem = _permission_problem(request)
    if problem:
        return problem
    if not request.user.has_perm(permission):
        return 403, {
            "message": message,
            "success": False,
            "code": "forbidden",
        }
    return None


def _visible_resource(
    request: HttpRequest,
    resource_id: int,
) -> InfrastructureResource | None:
    return (
        scope_infrastructure_resources_for_user(
            request.user,
            InfrastructureResource.objects.select_related(
                "client", "domain_profile", "tls_certificate"
            ).prefetch_related("tags"),
        )
        .filter(id=resource_id)
        .first()
    )


def _resource_not_found() -> StaffProblem:
    return 404, {
        "message": "Infrastructure resource not found.",
        "success": False,
        "code": "not_found",
    }


def _resource_summary(resource: InfrastructureResource) -> InfrastructureResourceSummaryOut:
    domain = getattr(resource, "domain_profile", None)
    certificate = getattr(resource, "tls_certificate", None)
    return InfrastructureResourceSummaryOut(
        id=resource.id,
        name=resource.name,
        resource_type=resource.resource_type,
        lifecycle_status=resource.lifecycle_status,
        environment=resource.environment,
        criticality=resource.criticality,
        ownership_type=resource.ownership_type,
        client_id=resource.client_id,
        client_name=str(resource.client) if resource.client else None,
        tags=[
            InfrastructureTagOut(
                id=tag.id,
                name=tag.name,
                slug=tag.slug,
                colour=tag.colour,
            )
            for tag in resource.tags.all()
        ],
        updated_at=resource.updated_at,
        expires_on=domain.expires_on if domain else None,
        expires_at=certificate.expires_at if certificate else None,
        auto_renew=domain.auto_renew if domain else certificate.auto_renew if certificate else None,
    )


def _relationship_rows(
    request: HttpRequest,
    resource: InfrastructureResource,
) -> list[InfrastructureRelationshipOut]:
    visible_resources = scope_infrastructure_resources_for_user(request.user)
    relationships = (
        ResourceRelationship.objects.filter(
            Q(source_resource=resource, target_resource__in=visible_resources)
            | Q(target_resource=resource, source_resource__in=visible_resources)
        )
        .select_related("source_resource", "target_resource")
        .order_by("relationship_type", "id")
    )
    rows: list[InfrastructureRelationshipOut] = []
    for relationship in relationships:
        outgoing = relationship.source_resource_id == resource.id
        related = relationship.target_resource if outgoing else relationship.source_resource
        rows.append(
            InfrastructureRelationshipOut(
                id=relationship.id,
                direction="outgoing" if outgoing else "incoming",
                relationship_type=relationship.relationship_type,
                label=relationship.label,
                notes=relationship.notes,
                related_resource_id=related.id,
                related_resource_name=related.name,
                related_resource_type=related.resource_type,
            )
        )
    return rows


@infrastructure_resource_router.get(
    "/infrastructure/resources",
    response={200: InfrastructureResourcePageOut, 401: ProblemDetail, 403: ProblemDetail},
)
def list_infrastructure_resources(
    request: HttpRequest,
    page: int = 1,
    page_size: int = 25,
    ownership: ResourceOwnershipFilter = "all",
    lifecycle: ResourceLifecycleFilter = "current",
    client_id: int | None = None,
    resource_type: ResourceTypeFilter | None = None,
    environment: ResourceEnvironmentFilter | None = None,
    search: str | None = None,
) -> InfrastructureResourcePageOut | StaffProblem:
    problem = _permission_problem(request)
    if problem:
        return problem

    resources = scope_infrastructure_resources_for_user(
        request.user,
        InfrastructureResource.objects.select_related(
            "client", "domain_profile", "tls_certificate"
        ).prefetch_related("tags"),
    )

    if ownership != "all":
        resources = resources.filter(ownership_type=ownership)
    if lifecycle == "current":
        resources = resources.filter(lifecycle_status__in=CURRENT_LIFECYCLE_STATUSES)
    elif lifecycle != "all":
        resources = resources.filter(lifecycle_status=lifecycle)
    if client_id is not None:
        resources = resources.filter(client_id=client_id)
    if resource_type is not None:
        resources = resources.filter(resource_type=resource_type)
    if environment is not None:
        resources = resources.filter(environment=environment)
    if search:
        term = search.strip()
        if term:
            resources = resources.filter(
                Q(name__icontains=term)
                | Q(description__icontains=term)
                | Q(client__name__icontains=term)
                | Q(client__company__icontains=term)
                | Q(tags__name__icontains=term)
            ).distinct()

    resources = resources.order_by("name", "id")
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    total = resources.count()
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    page_items = resources[start : start + page_size]

    return InfrastructureResourcePageOut(
        items=[_resource_summary(resource) for resource in page_items],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@infrastructure_resource_router.get(
    "/infrastructure/resources/{resource_id}/relationship-options",
    response={
        200: InfrastructureRelationshipOptionsOut,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def infrastructure_relationship_options(
    request: HttpRequest,
    resource_id: int,
    search: str | None = None,
) -> InfrastructureRelationshipOptionsOut | StaffProblem:
    problem = _permission_problem(request)
    if problem:
        return problem

    resource = _visible_resource(request, resource_id)
    if resource is None:
        return _resource_not_found()

    targets = scope_infrastructure_resources_for_user(
        request.user,
        InfrastructureResource.objects.select_related("client"),
    ).filter(lifecycle_status__in=CURRENT_LIFECYCLE_STATUSES)
    targets = targets.exclude(id=resource.id)
    if resource.ownership_type == OwnershipType.CLIENT:
        targets = targets.filter(
            Q(ownership_type=OwnershipType.INTERNAL) | Q(client_id=resource.client_id)
        )
    if search:
        term = search.strip()
        if term:
            targets = targets.filter(
                Q(name__icontains=term)
                | Q(client__name__icontains=term)
                | Q(client__company__icontains=term)
            )

    return InfrastructureRelationshipOptionsOut(
        relationship_types=[
            InfrastructureRelationshipTypeOut(value=value, label=label)
            for value, label in ResourceRelationship.RelationshipType.choices
        ],
        targets=[
            InfrastructureRelationshipTargetOut(
                id=target.id,
                name=target.name,
                resource_type=target.resource_type,
                ownership_type=target.ownership_type,
                client_name=str(target.client) if target.client else None,
            )
            for target in targets.order_by("name", "id")[:100]
        ],
    )


@infrastructure_resource_router.post(
    "/infrastructure/resources/{resource_id}/relationships",
    response={
        201: InfrastructureRelationshipOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_infrastructure_relationship(
    request: HttpRequest,
    resource_id: int,
    payload: InfrastructureRelationshipCreateIn,
) -> tuple[int, InfrastructureRelationshipOut | dict[str, object]]:
    problem = _relationship_permission_problem(
        request,
        "infrastructure.add_resourcerelationship",
        "You do not have permission to create infrastructure relationships.",
    )
    if problem:
        return problem

    source = _visible_resource(request, resource_id)
    target = _visible_resource(request, payload.target_resource_id)
    if source is None or target is None:
        return _resource_not_found()

    if payload.relationship_type not in ResourceRelationship.RelationshipType.values:
        return 400, {
            "message": "Choose a valid infrastructure relationship type.",
            "success": False,
            "code": "invalid_relationship_type",
        }

    relationship = ResourceRelationship(
        source_resource=source,
        target_resource=target,
        relationship_type=payload.relationship_type,
        label=payload.label.strip(),
        notes=payload.notes.strip(),
        created_by_id=request.user.pk,
    )
    try:
        relationship.full_clean()
    except ValidationError as error:
        return 400, {
            "message": " ".join(error.messages),
            "success": False,
            "code": "invalid_relationship",
        }
    relationship.save()

    return 201, InfrastructureRelationshipOut(
        id=relationship.id,
        direction="outgoing",
        relationship_type=relationship.relationship_type,
        label=relationship.label,
        notes=relationship.notes,
        related_resource_id=target.id,
        related_resource_name=target.name,
        related_resource_type=target.resource_type,
    )


@infrastructure_resource_router.patch(
    "/infrastructure/resources/{resource_id}/relationships/{relationship_id}",
    response={
        200: InfrastructureRelationshipOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_infrastructure_relationship(
    request: HttpRequest,
    resource_id: int,
    relationship_id: int,
    payload: InfrastructureRelationshipCreateIn,
) -> InfrastructureRelationshipOut | StaffProblem:
    problem = _relationship_permission_problem(
        request,
        "infrastructure.change_resourcerelationship",
        "You do not have permission to edit infrastructure relationships.",
    )
    if problem:
        return problem
    source = _visible_resource(request, resource_id)
    target = _visible_resource(request, payload.target_resource_id)
    if source is None or target is None:
        return _resource_not_found()
    try:
        with transaction.atomic():
            relationship = (
                ResourceRelationship.objects.select_for_update()
                .filter(
                    id=relationship_id,
                    source_resource=source,
                    target_resource__in=scope_infrastructure_resources_for_user(request.user),
                )
                .first()
            )
            if relationship is None:
                return _resource_not_found()
            relationship.target_resource = target
            relationship.relationship_type = payload.relationship_type
            relationship.label = payload.label.strip()
            relationship.notes = payload.notes.strip()
            relationship.full_clean()
            relationship.save()
            AuditEvent.record(
                action="updated",
                target=relationship,
                actor=request.user,
                resource_id=source.id,
                client_id=source.client_id,
            )
    except ValidationError as error:
        return _problem(400, " ".join(error.messages), "invalid_relationship")
    return InfrastructureRelationshipOut(
        id=relationship.id,
        direction="outgoing",
        relationship_type=relationship.relationship_type,
        label=relationship.label,
        notes=relationship.notes,
        related_resource_id=target.id,
        related_resource_name=target.name,
        related_resource_type=target.resource_type,
    )


@infrastructure_resource_router.delete(
    "/infrastructure/resources/{resource_id}/relationships/{relationship_id}",
    response={
        204: None,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def delete_infrastructure_relationship(
    request: HttpRequest,
    resource_id: int,
    relationship_id: int,
) -> tuple[int, dict[str, object] | None]:
    problem = _relationship_permission_problem(
        request,
        "infrastructure.delete_resourcerelationship",
        "You do not have permission to delete infrastructure relationships.",
    )
    if problem:
        return problem

    resource = _visible_resource(request, resource_id)
    if resource is None:
        return _resource_not_found()

    relationship = (
        ResourceRelationship.objects.select_related("source_resource", "target_resource")
        .filter(id=relationship_id)
        .filter(Q(source_resource=resource) | Q(target_resource=resource))
        .first()
    )
    if relationship is None:
        return 404, {
            "message": "Infrastructure relationship not found.",
            "success": False,
            "code": "not_found",
        }

    related_id = (
        relationship.target_resource_id
        if relationship.source_resource_id == resource.id
        else relationship.source_resource_id
    )
    if not scope_infrastructure_resources_for_user(request.user).filter(id=related_id).exists():
        return 404, {
            "message": "Infrastructure relationship not found.",
            "success": False,
            "code": "not_found",
        }

    relationship.delete()
    return 204, None


@infrastructure_resource_router.get(
    "/infrastructure/resources/{resource_id}",
    response={
        200: InfrastructureResourceDetailOut,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def get_infrastructure_resource(
    request: HttpRequest,
    resource_id: int,
) -> InfrastructureResourceDetailOut | StaffProblem:
    problem = _permission_problem(request)
    if problem:
        return problem

    resource = _visible_resource(request, resource_id)
    if resource is None:
        return _resource_not_found()

    native_fields = specialist_resource_snapshot(resource)
    summary = _resource_summary(resource)
    return InfrastructureResourceDetailOut(
        **summary.model_dump(),
        description=resource.description,
        is_portal_visible=resource.is_portal_visible,
        relationships=_relationship_rows(request, resource),
        specialist_fields=[
            SpecialistFieldOut(
                key=field.key,
                label=field.label,
                value=field.value,
                kind=field.kind,
            )
            for field in native_fields
        ],
        created_at=resource.created_at,
    )


BASIC_RESOURCE_TYPES = frozenset(
    {"api", "bot", "mobile_app", "licence", "email_system", "network_device", "other"}
)
RESPONSES = {400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail}


@infrastructure_resource_router.post(
    "/infrastructure/resources", response={201: ResourceMutationOut, **RESPONSES}
)
def create_basic_resource(
    request: HttpRequest, payload: BasicResourceIn
) -> tuple[int, ResourceMutationOut | dict[str, object]]:
    problem = _write_permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.add_infrastructureresource",
    )
    if problem:
        return problem
    with transaction.atomic():
        resource, problem = _new_resource(request, payload, payload.resource_type)
        if problem:
            return problem
        assert resource is not None
        AuditEvent.record(
            action="created", target=resource, actor=request.user, client_id=resource.client_id
        )
    return 201, ResourceMutationOut(resource_id=resource.id)


@infrastructure_resource_router.patch(
    "/infrastructure/resources/{resource_id}", response={200: ResourceMutationOut, **RESPONSES}
)
def update_basic_resource(
    request: HttpRequest, resource_id: int, payload: BasicResourceUpdateIn
) -> ResourceMutationOut | StaffProblem:
    problem = _write_permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.change_infrastructureresource",
    )
    if problem:
        return problem
    resource = (
        scope_infrastructure_resources_for_user(request.user)
        .filter(id=resource_id, resource_type__in=BASIC_RESOURCE_TYPES)
        .first()
    )
    if resource is None:
        return _problem(404, "Basic resource not found.", "not_found")
    with transaction.atomic():
        problem = _update_resource(request, resource, payload)
        if problem:
            return problem
        AuditEvent.record(
            action="updated", target=resource, actor=request.user, client_id=resource.client_id
        )
    return ResourceMutationOut(resource_id=resource.id)
