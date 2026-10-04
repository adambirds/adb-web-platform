from __future__ import annotations

import math

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpRequest
from ninja import Router

from apps.access_control.policies import scope_clients_for_user
from apps.clients.models import Client
from apps.core.models import AuditEvent
from apps.infrastructure.models import InfrastructureResource, ProviderAccount, ServiceProvider
from apps.infrastructure.policies import scope_infrastructure_resources_for_user
from authentication.ninja.schemas import ProblemDetail

from .catalogue_schemas import (
    CatalogueOptionsOut,
    ProviderAccountIn,
    ProviderAccountOut,
    ProviderAccountUpdateIn,
    ResourceMutationOut,
    ServiceProviderIn,
    ServiceProviderOut,
    ServiceProviderPageOut,
    ServiceProviderUpdateIn,
)
from .specialist_schemas import ClientOptionOut
from .specialist_views import (
    StaffProblem,
    _archive_resource,
    _new_resource,
    _permission_problem,
    _problem,
    _update_resource,
    _validation_problem,
)

catalogue_router = Router(tags=["admin-infrastructure-catalogue"])
PROVIDER_FIELDS = (
    "provider_id",
    "account_identifier",
    "tenant_id",
    "project_id",
    "portal_url",
    "default_region",
    "support_plan",
    "billing_reference",
)
RESPONSES = {400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail}


def _provider_out(provider: ServiceProvider) -> ServiceProviderOut:
    return ServiceProviderOut.from_orm(provider)


def _account_out(account: ProviderAccount) -> ProviderAccountOut:
    resource = account.resource
    return ProviderAccountOut.model_validate(
        {
            "resource_id": resource.id,
            "name": resource.name,
            "ownership_type": resource.ownership_type,
            "client_id": resource.client_id,
            "lifecycle_status": resource.lifecycle_status,
            "environment": resource.environment,
            "criticality": resource.criticality,
            "description": resource.description,
            "provider_name": account.provider.name,
            **{field: getattr(account, field) for field in PROVIDER_FIELDS},
        }
    )


def _visible_account(request: HttpRequest, resource_id: int) -> ProviderAccount | None:
    return (
        ProviderAccount.objects.select_related("resource", "provider")
        .filter(
            resource_id=resource_id,
            resource__in=scope_infrastructure_resources_for_user(request.user),
        )
        .first()
    )


@catalogue_router.get(
    "/infrastructure/catalogue-options", response={200: CatalogueOptionsOut, **RESPONSES}
)
def catalogue_options(request: HttpRequest) -> CatalogueOptionsOut | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_infrastructureresource")
    if problem:
        return problem
    clients = scope_clients_for_user(request.user, Client.objects.filter(status="active"))
    providers = (
        ServiceProvider.objects.filter(is_active=True)
        if request.user.has_perm("infrastructure.view_serviceprovider")
        else ServiceProvider.objects.none()
    )
    return CatalogueOptionsOut(
        clients=[
            ClientOptionOut(id=client.id, name=str(client))
            for client in clients.order_by("name", "id")
        ],
        providers=[_provider_out(provider) for provider in providers],
    )


@catalogue_router.get(
    "/infrastructure/service-providers", response={200: ServiceProviderPageOut, **RESPONSES}
)
def list_service_providers(
    request: HttpRequest, page: int = 1, page_size: int = 25, search: str = ""
) -> ServiceProviderPageOut | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_serviceprovider")
    if problem:
        return problem
    providers = ServiceProvider.objects.all()
    if search.strip():
        providers = providers.filter(
            Q(name__icontains=search.strip()) | Q(category__icontains=search.strip())
        )
    page, page_size = max(1, page), min(100, max(1, page_size))
    total = providers.count()
    return ServiceProviderPageOut(
        items=[_provider_out(p) for p in providers[(page - 1) * page_size : page * page_size]],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=math.ceil(total / page_size),
    )


@catalogue_router.post(
    "/infrastructure/service-providers", response={201: ServiceProviderOut, **RESPONSES}
)
def create_service_provider(
    request: HttpRequest, payload: ServiceProviderIn
) -> tuple[int, ServiceProviderOut | dict[str, object]]:
    problem = _permission_problem(request, "infrastructure.add_serviceprovider")
    if problem:
        return problem
    provider = ServiceProvider(
        **{
            key: value.strip() if isinstance(value, str) else value
            for key, value in payload.model_dump().items()
        }
    )
    try:
        with transaction.atomic():
            provider.full_clean()
            provider.save()
            AuditEvent.record(action="created", target=provider, actor=request.user)
    except ValidationError as error:
        return _validation_problem(error)
    except IntegrityError:
        return _problem(
            400, "A provider with that name or slug already exists.", "invalid_infrastructure"
        )
    return 201, _provider_out(provider)


@catalogue_router.patch(
    "/infrastructure/service-providers/{provider_id}",
    response={200: ServiceProviderOut, **RESPONSES},
)
def update_service_provider(
    request: HttpRequest, provider_id: int, payload: ServiceProviderUpdateIn
) -> ServiceProviderOut | StaffProblem:
    problem = _permission_problem(
        request, "infrastructure.view_serviceprovider", "infrastructure.change_serviceprovider"
    )
    if problem:
        return problem
    try:
        with transaction.atomic():
            provider = ServiceProvider.objects.select_for_update().filter(id=provider_id).first()
            if provider is None:
                return _problem(404, "Service provider not found.", "not_found")
            for key, value in payload.model_dump().items():
                setattr(provider, key, value.strip() if isinstance(value, str) else value)
            provider.full_clean()
            provider.save()
            AuditEvent.record(action="updated", target=provider, actor=request.user)
    except ValidationError as error:
        return _validation_problem(error)
    except IntegrityError:
        return _problem(400, "A provider with that slug already exists.", "invalid_infrastructure")
    return _provider_out(provider)


@catalogue_router.post(
    "/infrastructure/provider-accounts", response={201: ResourceMutationOut, **RESPONSES}
)
def create_provider_account(
    request: HttpRequest, payload: ProviderAccountIn
) -> tuple[int, ResourceMutationOut | dict[str, object]]:
    problem = _permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.view_serviceprovider",
        "infrastructure.add_infrastructureresource",
        "infrastructure.add_provideraccount",
    )
    if problem:
        return problem
    provider = ServiceProvider.objects.filter(id=payload.provider_id, is_active=True).first()
    if provider is None:
        return _problem(404, "Active service provider not found.", "not_found")
    try:
        with transaction.atomic():
            resource, problem = _new_resource(
                request, payload, InfrastructureResource.ResourceType.PROVIDER_ACCOUNT
            )
            if problem:
                return problem
            assert resource is not None
            account = ProviderAccount(resource=resource, provider=provider)
            for field in PROVIDER_FIELDS[1:]:
                setattr(account, field, getattr(payload, field).strip())
            account.full_clean()
            account.save()
            AuditEvent.record(
                action="created", target=resource, actor=request.user, client_id=resource.client_id
            )
    except ValidationError as error:
        return _validation_problem(error)
    return 201, ResourceMutationOut(resource_id=resource.id)


@catalogue_router.get(
    "/infrastructure/provider-accounts/{resource_id}",
    response={200: ProviderAccountOut, **RESPONSES},
)
def get_provider_account(
    request: HttpRequest, resource_id: int
) -> ProviderAccountOut | StaffProblem:
    problem = _permission_problem(
        request, "infrastructure.view_infrastructureresource", "infrastructure.view_provideraccount"
    )
    if problem:
        return problem
    account = _visible_account(request, resource_id)
    return (
        _account_out(account)
        if account
        else _problem(404, "Provider account not found.", "not_found")
    )


@catalogue_router.patch(
    "/infrastructure/provider-accounts/{resource_id}",
    response={200: ResourceMutationOut, **RESPONSES},
)
def update_provider_account(
    request: HttpRequest, resource_id: int, payload: ProviderAccountUpdateIn
) -> ResourceMutationOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.view_serviceprovider",
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_provideraccount",
    )
    if problem:
        return problem
    account = _visible_account(request, resource_id)
    if account is None:
        return _problem(404, "Provider account not found.", "not_found")
    provider = ServiceProvider.objects.filter(id=payload.provider_id).first()
    if provider is None or (not provider.is_active and provider.id != account.provider_id):
        return _problem(404, "Active service provider not found.", "not_found")
    try:
        with transaction.atomic():
            problem = _update_resource(request, account.resource, payload)
            if problem:
                return problem
            for field in PROVIDER_FIELDS:
                setattr(
                    account,
                    field,
                    getattr(payload, field).strip()
                    if isinstance(getattr(payload, field), str)
                    else getattr(payload, field),
                )
            account.full_clean()
            account.save()
            AuditEvent.record(
                action="updated",
                target=account.resource,
                actor=request.user,
                client_id=account.resource.client_id,
            )
    except ValidationError as error:
        return _validation_problem(error)
    return ResourceMutationOut(resource_id=resource_id)


@catalogue_router.post(
    "/infrastructure/provider-accounts/{resource_id}/archive",
    response={200: ResourceMutationOut, **RESPONSES},
)
def archive_provider_account(
    request: HttpRequest, resource_id: int
) -> ResourceMutationOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_provideraccount",
    )
    if problem:
        return problem
    account = _visible_account(request, resource_id)
    if account is None:
        return _problem(404, "Provider account not found.", "not_found")
    with transaction.atomic():
        _archive_resource(request, account.resource)
        AuditEvent.record(
            action="archived",
            target=account.resource,
            actor=request.user,
            client_id=account.resource.client_id,
        )
    return ResourceMutationOut(resource_id=resource_id)
