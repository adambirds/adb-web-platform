from __future__ import annotations

import math

from django.db.models import Q
from django.http import HttpRequest
from ninja import Router, Schema

from apps.infrastructure.policies import scope_infrastructure_resources_for_user
from authentication.ninja.schemas import ProblemDetail

from .resource_views import CURRENT_LIFECYCLE_STATUSES, StaffProblem, _permission_problem

technology_router = Router(tags=["admin-infrastructure-technology"])


class TechnologyOut(Schema):
    id: str
    resource_id: int
    resource_name: str
    technology: str
    category: str
    version: str


class TechnologyPageOut(Schema):
    items: list[TechnologyOut]
    page: int
    page_size: int
    total: int
    total_pages: int


@technology_router.get(
    "/infrastructure/technology",
    response={200: TechnologyPageOut, 401: ProblemDetail, 403: ProblemDetail},
)
def list_resource_technology(
    request: HttpRequest, page: int = 1, page_size: int = 25, search: str = ""
) -> TechnologyPageOut | StaffProblem:
    problem = _permission_problem(request)
    if problem:
        return problem
    resources = (
        scope_infrastructure_resources_for_user(request.user)
        .filter(
            lifecycle_status__in=CURRENT_LIFECYCLE_STATUSES,
        )
        .filter(
            Q(website_profile__cms__gt="")
            | Q(application_profile__framework__gt="")
            | Q(application_profile__primary_language__gt="")
            | Q(database_instance__engine__gt="")
            | Q(application_environment__runtime__gt="")
            | Q(server_profile__distribution__gt="")
        )
    )
    if search.strip():
        resources = resources.filter(
            Q(name__icontains=search.strip()) | Q(client__company__icontains=search.strip())
        )
    resources = resources.select_related(
        "website_profile",
        "application_profile",
        "database_instance",
        "application_environment",
        "server_profile",
    ).order_by("name", "id")
    total = resources.count()
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    rows: list[TechnologyOut] = []
    fields = (
        ("website_profile", "cms", "cms_version", "CMS"),
        ("application_profile", "framework", "", "Framework"),
        ("application_profile", "primary_language", "", "Language"),
        ("database_instance", "engine", "engine_version", "Database"),
        ("application_environment", "runtime", "runtime_version", "Runtime"),
        ("server_profile", "distribution", "os_version", "Operating system"),
    )
    for resource in resources[(page - 1) * page_size : page * page_size]:
        for relation, field, version_field, category in fields:
            profile = getattr(resource, relation, None)
            technology = str(getattr(profile, field, "")).strip()
            if not technology:
                continue
            rows.append(
                TechnologyOut(
                    id=f"{resource.id}:{field}",
                    resource_id=resource.id,
                    resource_name=resource.name,
                    technology=technology,
                    category=category,
                    version=str(getattr(profile, version_field, "")) if version_field else "",
                )
            )
    return TechnologyPageOut(
        items=rows,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=math.ceil(total / page_size) if total else 0,
    )
