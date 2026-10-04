from __future__ import annotations

import math

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpRequest
from ninja import Router, Schema

from apps.core.models import AuditEvent
from apps.infrastructure.models import InfrastructureTag
from apps.infrastructure.policies import scope_infrastructure_resources_for_user
from authentication.ninja.schemas import ProblemDetail

from .resource_schemas import InfrastructureTagOut
from .specialist_views import StaffProblem, _permission_problem, _problem, _validation_problem

tag_router = Router(tags=["admin-infrastructure-tags"])
RESPONSES = {400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail}


class TagIn(Schema):
    name: str
    slug: str
    colour: str = ""


class TagPageOut(Schema):
    items: list[InfrastructureTagOut]
    page: int
    page_size: int
    total: int
    total_pages: int


@tag_router.get("/infrastructure/tags", response={200: TagPageOut, **RESPONSES})
def list_tags(
    request: HttpRequest, search: str = "", page: int = 1, page_size: int = 25
) -> TagPageOut | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_infrastructuretag")
    if problem:
        return problem
    tags = InfrastructureTag.objects.filter(name__icontains=search.strip())
    page, page_size = max(1, page), min(100, max(1, page_size))
    total = tags.count()
    return TagPageOut(
        items=[
            InfrastructureTagOut.from_orm(tag)
            for tag in tags[(page - 1) * page_size : page * page_size]
        ],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=math.ceil(total / page_size),
    )


@tag_router.post("/infrastructure/tags", response={201: InfrastructureTagOut, **RESPONSES})
def create_tag(
    request: HttpRequest, payload: TagIn
) -> tuple[int, InfrastructureTagOut | dict[str, object]]:
    problem = _permission_problem(request, "infrastructure.add_infrastructuretag")
    if problem:
        return problem
    tag = InfrastructureTag(**{key: value.strip() for key, value in payload.model_dump().items()})
    try:
        with transaction.atomic():
            tag.full_clean()
            tag.save()
            AuditEvent.record(action="created", target=tag, actor=request.user)
    except ValidationError as error:
        return _validation_problem(error)
    except IntegrityError:
        return _problem(
            400, "A tag with that name or slug already exists.", "invalid_infrastructure"
        )
    return 201, InfrastructureTagOut.from_orm(tag)


@tag_router.patch(
    "/infrastructure/tags/{tag_id}", response={200: InfrastructureTagOut, **RESPONSES}
)
def update_tag(
    request: HttpRequest, tag_id: int, payload: TagIn
) -> InfrastructureTagOut | StaffProblem:
    problem = _permission_problem(
        request, "infrastructure.view_infrastructuretag", "infrastructure.change_infrastructuretag"
    )
    if problem:
        return problem
    try:
        with transaction.atomic():
            tag = InfrastructureTag.objects.select_for_update().filter(id=tag_id).first()
            if tag is None:
                return _problem(404, "Tag not found.", "not_found")
            for key, value in payload.model_dump().items():
                setattr(tag, key, value.strip())
            tag.full_clean()
            tag.save()
            AuditEvent.record(action="updated", target=tag, actor=request.user)
    except ValidationError as error:
        return _validation_problem(error)
    except IntegrityError:
        return _problem(
            400, "A tag with that name or slug already exists.", "invalid_infrastructure"
        )
    return InfrastructureTagOut.from_orm(tag)


def _change_tag(
    request: HttpRequest, resource_id: int, tag_id: int, *, remove: bool
) -> list[InfrastructureTagOut] | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.change_infrastructureresource",
        "infrastructure.view_infrastructuretag",
    )
    if problem:
        return problem
    resource = scope_infrastructure_resources_for_user(request.user).filter(id=resource_id).first()
    tag = InfrastructureTag.objects.filter(id=tag_id).first()
    if resource is None or tag is None:
        return _problem(404, "Resource or tag not found.", "not_found")
    with transaction.atomic():
        if remove:
            resource.tags.remove(tag)
        else:
            resource.tags.add(tag)
        AuditEvent.record(
            action="tag_removed" if remove else "tag_added",
            target=resource,
            actor=request.user,
            metadata={"tag_id": tag.id},
        )
    return [InfrastructureTagOut.from_orm(item) for item in resource.tags.all()]


@tag_router.put(
    "/infrastructure/resources/{resource_id}/tags/{tag_id}",
    response={200: list[InfrastructureTagOut], **RESPONSES},
)
def attach_tag(
    request: HttpRequest, resource_id: int, tag_id: int
) -> list[InfrastructureTagOut] | StaffProblem:
    return _change_tag(request, resource_id, tag_id, remove=False)


@tag_router.delete(
    "/infrastructure/resources/{resource_id}/tags/{tag_id}",
    response={200: list[InfrastructureTagOut], **RESPONSES},
)
def remove_tag(
    request: HttpRequest, resource_id: int, tag_id: int
) -> list[InfrastructureTagOut] | StaffProblem:
    return _change_tag(request, resource_id, tag_id, remove=True)
