from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpRequest
from ninja import Router

from apps.access_control.policies import scope_clients_for_user
from apps.clients.models import Client
from apps.core.models import AuditEvent
from apps.infrastructure.models import (
    ApplicationEnvironment,
    ApplicationProfile,
    ApplicationRepositoryLink,
    DatabaseInstance,
    InfrastructureResource,
    LogicalDatabase,
    ProviderAccount,
    ServerProfile,
    SourceRepository,
)
from apps.infrastructure.policies import scope_infrastructure_resources_for_user
from authentication.ninja.schemas import ProblemDetail

from .data_application_schemas import (
    ApplicationCreateIn,
    ApplicationEnvironmentCreateIn,
    ApplicationEnvironmentOut,
    ApplicationEnvironmentUpdateIn,
    ApplicationOptionOut,
    ApplicationOut,
    ApplicationRepositoryLinkCreateIn,
    ApplicationRepositoryLinkOut,
    ApplicationUpdateIn,
    DataApplicationSpecialistOptionsOut,
    DatabaseInstanceCreateIn,
    DatabaseInstanceOptionOut,
    DatabaseInstanceOut,
    DatabaseInstanceUpdateIn,
    LogicalDatabaseCreateIn,
    LogicalDatabaseOut,
    LogicalDatabaseUpdateIn,
    ServerOptionOut,
    SourceRepositoryCreateIn,
    SourceRepositoryOptionOut,
    SourceRepositoryOut,
    SourceRepositoryUpdateIn,
)
from .specialist_schemas import ClientOptionOut, ProviderAccountOptionOut
from .specialist_views import (
    CURRENT_LIFECYCLE_STATUSES,
    StaffProblem,
    _archive_resource,
    _new_resource,
    _permission_problem,
    _problem,
    _update_resource,
    _validation_problem,
)

data_application_specialist_router = Router(tags=["admin-infrastructure-data-applications"])


def _visible_queryset(request: HttpRequest) -> Any:
    return scope_infrastructure_resources_for_user(request.user)


def _visible_provider_account(
    request: HttpRequest,
    resource_id: int | None,
) -> ProviderAccount | None:
    if resource_id is None:
        return None
    return (
        ProviderAccount.objects.select_related("resource", "resource__client", "provider")
        .filter(resource__in=_visible_queryset(request), resource_id=resource_id)
        .first()
    )


def _visible_server(request: HttpRequest, resource_id: int | None) -> ServerProfile | None:
    if resource_id is None:
        return None
    return (
        ServerProfile.objects.select_related("resource", "resource__client")
        .filter(resource__in=_visible_queryset(request), resource_id=resource_id)
        .first()
    )


def _visible_database_instance(
    request: HttpRequest,
    resource_id: int | None,
) -> DatabaseInstance | None:
    if resource_id is None:
        return None
    return (
        DatabaseInstance.objects.select_related(
            "resource",
            "resource__client",
            "server__resource",
            "provider_account__resource",
            "provider_account__provider",
        )
        .filter(resource__in=_visible_queryset(request), resource_id=resource_id)
        .first()
    )


def _visible_application(
    request: HttpRequest,
    resource_id: int | None,
) -> ApplicationProfile | None:
    if resource_id is None:
        return None
    return (
        ApplicationProfile.objects.select_related("resource", "resource__client")
        .prefetch_related("repository_links__repository__resource")
        .filter(resource__in=_visible_queryset(request), resource_id=resource_id)
        .first()
    )


def _visible_source_repository(
    request: HttpRequest,
    resource_id: int | None,
) -> SourceRepository | None:
    if resource_id is None:
        return None
    return (
        SourceRepository.objects.select_related(
            "resource",
            "resource__client",
            "provider_account__resource",
            "provider_account__provider",
        )
        .filter(resource__in=_visible_queryset(request), resource_id=resource_id)
        .first()
    )


def _database_instance_out(database: DatabaseInstance) -> DatabaseInstanceOut:
    resource = database.resource
    server = database.server
    provider_account = database.provider_account
    return DatabaseInstanceOut(
        resource_id=resource.id,
        name=resource.name,
        ownership_type=resource.ownership_type,
        client_id=resource.client_id,
        client_name=str(resource.client) if resource.client else None,
        lifecycle_status=resource.lifecycle_status,
        environment=resource.environment,
        criticality=resource.criticality,
        description=resource.description,
        engine=database.engine,
        engine_version=database.engine_version,
        hosting_type=database.hosting_type,
        server_resource_id=server.resource_id if server else None,
        server_name=server.resource.name if server else None,
        provider_account_resource_id=(provider_account.resource_id if provider_account else None),
        provider_account_name=(provider_account.resource.name if provider_account else None),
        provider_name=(provider_account.provider.name if provider_account else None),
        provider_resource_id=database.provider_resource_id,
        endpoint=database.endpoint,
        port=database.port,
        region=database.region,
        zone=database.zone,
        tls_mode=database.tls_mode,
        high_availability=database.high_availability,
        replica_count=database.replica_count,
        backup_enabled=database.backup_enabled,
        maintenance_window=database.maintenance_window,
        updated_at=resource.updated_at,
    )


def _logical_database_out(database: LogicalDatabase) -> LogicalDatabaseOut:
    resource = database.resource
    return LogicalDatabaseOut(
        resource_id=resource.id,
        name=resource.name,
        ownership_type=resource.ownership_type,
        client_id=resource.client_id,
        client_name=str(resource.client) if resource.client else None,
        lifecycle_status=resource.lifecycle_status,
        environment=resource.environment,
        criticality=resource.criticality,
        description=resource.description,
        instance_resource_id=database.instance.resource_id,
        instance_name=database.instance.resource.name,
        database_name=database.database_name,
        purpose=database.purpose,
        default_schema=database.default_schema,
        charset=database.charset,
        collation=database.collation,
        updated_at=resource.updated_at,
    )


def _repository_link_out(link: ApplicationRepositoryLink) -> ApplicationRepositoryLinkOut:
    return ApplicationRepositoryLinkOut(
        id=link.id,
        repository_resource_id=link.repository.resource_id,
        repository_name=link.repository.resource.name,
        role=link.role,
        path=link.path,
        notes=link.notes,
    )


def _application_out(application: ApplicationProfile) -> ApplicationOut:
    resource = application.resource
    return ApplicationOut(
        resource_id=resource.id,
        name=resource.name,
        ownership_type=resource.ownership_type,
        client_id=resource.client_id,
        client_name=str(resource.client) if resource.client else None,
        lifecycle_status=resource.lifecycle_status,
        environment=resource.environment,
        criticality=resource.criticality,
        description=resource.description,
        application_type=application.application_type,
        owner_team=application.owner_team,
        primary_language=application.primary_language,
        framework=application.framework,
        repositories=[_repository_link_out(link) for link in application.repository_links.all()],
        updated_at=resource.updated_at,
    )


def _application_environment_out(environment: ApplicationEnvironment) -> ApplicationEnvironmentOut:
    resource = environment.resource
    server = environment.server
    provider_account = environment.provider_account
    return ApplicationEnvironmentOut(
        resource_id=resource.id,
        name=resource.name,
        ownership_type=resource.ownership_type,
        client_id=resource.client_id,
        client_name=str(resource.client) if resource.client else None,
        lifecycle_status=resource.lifecycle_status,
        environment=resource.environment,
        criticality=resource.criticality,
        description=resource.description,
        application_resource_id=environment.application.resource_id,
        application_name=environment.application.resource.name,
        deployment_type=environment.deployment_type,
        server_resource_id=server.resource_id if server else None,
        server_name=server.resource.name if server else None,
        provider_account_resource_id=(provider_account.resource_id if provider_account else None),
        provider_account_name=(provider_account.resource.name if provider_account else None),
        provider_name=(provider_account.provider.name if provider_account else None),
        provider_resource_id=environment.provider_resource_id,
        runtime=environment.runtime,
        runtime_version=environment.runtime_version,
        release_version=environment.release_version,
        region=environment.region,
        branch_or_ref=environment.branch_or_ref,
        automatic_deployments=environment.automatic_deployments,
        updated_at=resource.updated_at,
    )


def _source_repository_out(repository: SourceRepository) -> SourceRepositoryOut:
    resource = repository.resource
    provider_account = repository.provider_account
    return SourceRepositoryOut(
        resource_id=resource.id,
        name=resource.name,
        ownership_type=resource.ownership_type,
        client_id=resource.client_id,
        client_name=str(resource.client) if resource.client else None,
        lifecycle_status=resource.lifecycle_status,
        environment=resource.environment,
        criticality=resource.criticality,
        description=resource.description,
        provider_account_resource_id=(provider_account.resource_id if provider_account else None),
        provider_account_name=(provider_account.resource.name if provider_account else None),
        provider_name=(provider_account.provider.name if provider_account else None),
        web_url=repository.web_url,
        clone_url=repository.clone_url,
        provider_repository_id=repository.provider_repository_id,
        owner_name=repository.owner_name,
        repository_name=repository.repository_name,
        default_branch=repository.default_branch,
        visibility=repository.visibility,
        is_fork=repository.is_fork,
        updated_at=resource.updated_at,
    )


def _populate_database_instance(
    database: DatabaseInstance,
    payload: DatabaseInstanceCreateIn | DatabaseInstanceUpdateIn,
) -> None:
    for field in (
        "engine",
        "engine_version",
        "hosting_type",
        "provider_resource_id",
        "endpoint",
        "port",
        "region",
        "zone",
        "tls_mode",
        "high_availability",
        "replica_count",
        "backup_enabled",
        "maintenance_window",
    ):
        setattr(database, field, getattr(payload, field))


def _populate_application(
    application: ApplicationProfile,
    payload: ApplicationCreateIn | ApplicationUpdateIn,
) -> None:
    application.application_type = payload.application_type
    application.owner_team = payload.owner_team.strip()
    application.primary_language = payload.primary_language.strip()
    application.framework = payload.framework.strip()


def _populate_application_environment(
    environment: ApplicationEnvironment,
    payload: ApplicationEnvironmentCreateIn | ApplicationEnvironmentUpdateIn,
) -> None:
    for field in (
        "deployment_type",
        "provider_resource_id",
        "runtime",
        "runtime_version",
        "release_version",
        "region",
        "branch_or_ref",
        "automatic_deployments",
    ):
        value = getattr(payload, field)
        setattr(environment, field, value.strip() if isinstance(value, str) else value)


def _populate_source_repository(
    repository: SourceRepository,
    payload: SourceRepositoryCreateIn | SourceRepositoryUpdateIn,
) -> None:
    for field in (
        "web_url",
        "clone_url",
        "provider_repository_id",
        "owner_name",
        "repository_name",
        "default_branch",
        "visibility",
        "is_fork",
    ):
        value = getattr(payload, field)
        setattr(repository, field, value.strip() if isinstance(value, str) else value)


@data_application_specialist_router.get(
    "/infrastructure/data-application-options",
    response={200: DataApplicationSpecialistOptionsOut, 401: ProblemDetail, 403: ProblemDetail},
)
def data_application_options(
    request: HttpRequest,
) -> DataApplicationSpecialistOptionsOut | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_infrastructureresource")
    if problem:
        return problem

    clients = scope_clients_for_user(request.user, Client.objects.filter(status="active"))
    visible = _visible_queryset(request)
    current = {"resource__lifecycle_status__in": CURRENT_LIFECYCLE_STATUSES}
    provider_accounts = ProviderAccount.objects.select_related(
        "resource", "resource__client", "provider"
    ).filter(resource__in=visible, **current)
    servers = ServerProfile.objects.select_related("resource", "resource__client").filter(
        resource__in=visible,
        **current,
    )
    database_instances = DatabaseInstance.objects.select_related(
        "resource", "resource__client"
    ).filter(resource__in=visible, **current)
    applications = ApplicationProfile.objects.select_related("resource", "resource__client").filter(
        resource__in=visible,
        **current,
    )
    repositories = SourceRepository.objects.select_related("resource", "resource__client").filter(
        resource__in=visible,
        **current,
    )

    return DataApplicationSpecialistOptionsOut(
        clients=[
            ClientOptionOut(id=item.id, name=str(item))
            for item in clients.order_by("company", "name")
        ],
        provider_accounts=[
            ProviderAccountOptionOut(
                resource_id=item.resource_id,
                name=item.resource.name,
                provider_name=item.provider.name,
                ownership_type=item.resource.ownership_type,
                client_id=item.resource.client_id,
                client_name=str(item.resource.client) if item.resource.client else None,
            )
            for item in provider_accounts.order_by("resource__name")
        ],
        servers=[
            ServerOptionOut(
                resource_id=item.resource_id,
                name=item.resource.name,
                hostname=item.hostname,
                ownership_type=item.resource.ownership_type,
                client_id=item.resource.client_id,
                client_name=str(item.resource.client) if item.resource.client else None,
            )
            for item in servers.order_by("resource__name")
        ],
        database_instances=[
            DatabaseInstanceOptionOut(
                resource_id=item.resource_id,
                name=item.resource.name,
                engine=item.engine,
                ownership_type=item.resource.ownership_type,
                client_id=item.resource.client_id,
                client_name=str(item.resource.client) if item.resource.client else None,
            )
            for item in database_instances.order_by("resource__name")
        ],
        applications=[
            ApplicationOptionOut(
                resource_id=item.resource_id,
                name=item.resource.name,
                application_type=item.application_type,
                ownership_type=item.resource.ownership_type,
                client_id=item.resource.client_id,
                client_name=str(item.resource.client) if item.resource.client else None,
            )
            for item in applications.order_by("resource__name")
        ],
        source_repositories=[
            SourceRepositoryOptionOut(
                resource_id=item.resource_id,
                name=item.resource.name,
                repository_name=item.repository_name,
                ownership_type=item.resource.ownership_type,
                client_id=item.resource.client_id,
                client_name=str(item.resource.client) if item.resource.client else None,
            )
            for item in repositories.order_by("resource__name")
        ],
    )


@data_application_specialist_router.post(
    "/infrastructure/database-instances",
    response={
        201: DatabaseInstanceOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_database_instance(
    request: HttpRequest,
    payload: DatabaseInstanceCreateIn,
) -> tuple[int, DatabaseInstanceOut | dict[str, object]]:
    problem = _permission_problem(
        request,
        "infrastructure.add_infrastructureresource",
        "infrastructure.add_databaseinstance",
    )
    if problem:
        return problem
    server = _visible_server(request, payload.server_resource_id)
    provider = _visible_provider_account(request, payload.provider_account_resource_id)
    if payload.server_resource_id is not None and server is None:
        return _problem(404, "Server not found.", "not_found")
    if payload.provider_account_resource_id is not None and provider is None:
        return _problem(404, "Provider account not found.", "not_found")
    try:
        with transaction.atomic():
            resource, resource_problem = _new_resource(
                request,
                payload,
                InfrastructureResource.ResourceType.DATABASE_INSTANCE,
            )
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            assert resource is not None
            database = DatabaseInstance(resource=resource, server=server, provider_account=provider)
            _populate_database_instance(database, payload)
            database.full_clean()
            database.save()
    except ValidationError as error:
        return _validation_problem(error)
    created = _visible_database_instance(request, resource.id)
    assert created is not None
    return 201, _database_instance_out(created)


@data_application_specialist_router.put(
    "/infrastructure/database-instances/{resource_id}",
    response={
        200: DatabaseInstanceOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_database_instance(
    request: HttpRequest,
    resource_id: int,
    payload: DatabaseInstanceUpdateIn,
) -> DatabaseInstanceOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_databaseinstance",
    )
    if problem:
        return problem
    database = _visible_database_instance(request, resource_id)
    if database is None:
        return _problem(404, "Database instance not found.", "not_found")
    server = _visible_server(request, payload.server_resource_id)
    provider = _visible_provider_account(request, payload.provider_account_resource_id)
    if payload.server_resource_id is not None and server is None:
        return _problem(404, "Server not found.", "not_found")
    if payload.provider_account_resource_id is not None and provider is None:
        return _problem(404, "Provider account not found.", "not_found")
    try:
        with transaction.atomic():
            resource_problem = _update_resource(request, database.resource, payload)
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            database.server = server
            database.provider_account = provider
            _populate_database_instance(database, payload)
            database.full_clean()
            database.save()
    except ValidationError as error:
        return _validation_problem(error)
    refreshed = _visible_database_instance(request, resource_id)
    assert refreshed is not None
    return _database_instance_out(refreshed)


@data_application_specialist_router.post(
    "/infrastructure/database-instances/{resource_id}/archive",
    response={200: DatabaseInstanceOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def archive_database_instance(
    request: HttpRequest,
    resource_id: int,
) -> DatabaseInstanceOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_databaseinstance",
    )
    if problem:
        return problem
    database = _visible_database_instance(request, resource_id)
    if database is None:
        return _problem(404, "Database instance not found.", "not_found")
    _archive_resource(request, database.resource)
    return _database_instance_out(database)


@data_application_specialist_router.post(
    "/infrastructure/logical-databases",
    response={
        201: LogicalDatabaseOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_logical_database(
    request: HttpRequest,
    payload: LogicalDatabaseCreateIn,
) -> tuple[int, LogicalDatabaseOut | dict[str, object]]:
    problem = _permission_problem(
        request,
        "infrastructure.add_infrastructureresource",
        "infrastructure.add_logicaldatabase",
    )
    if problem:
        return problem
    instance = _visible_database_instance(request, payload.instance_resource_id)
    if instance is None:
        return _problem(404, "Database instance not found.", "not_found")
    try:
        with transaction.atomic():
            resource, resource_problem = _new_resource(
                request,
                payload,
                InfrastructureResource.ResourceType.LOGICAL_DATABASE,
            )
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            assert resource is not None
            database = LogicalDatabase(
                resource=resource,
                instance=instance,
                database_name=payload.database_name.strip(),
                purpose=payload.purpose.strip(),
                default_schema=payload.default_schema.strip(),
                charset=payload.charset.strip(),
                collation=payload.collation.strip(),
            )
            database.full_clean()
            database.save()
    except ValidationError as error:
        return _validation_problem(error)
    created = LogicalDatabase.objects.select_related(
        "resource", "resource__client", "instance__resource"
    ).get(resource_id=resource.id)
    return 201, _logical_database_out(created)


@data_application_specialist_router.put(
    "/infrastructure/logical-databases/{resource_id}",
    response={
        200: LogicalDatabaseOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_logical_database(
    request: HttpRequest,
    resource_id: int,
    payload: LogicalDatabaseUpdateIn,
) -> LogicalDatabaseOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_logicaldatabase",
    )
    if problem:
        return problem
    visible = _visible_queryset(request)
    database = (
        LogicalDatabase.objects.select_related("resource", "resource__client", "instance__resource")
        .filter(resource__in=visible, resource_id=resource_id)
        .first()
    )
    if database is None:
        return _problem(404, "Logical database not found.", "not_found")
    instance = _visible_database_instance(request, payload.instance_resource_id)
    if instance is None:
        return _problem(404, "Database instance not found.", "not_found")
    try:
        with transaction.atomic():
            resource_problem = _update_resource(request, database.resource, payload)
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            database.instance = instance
            database.database_name = payload.database_name.strip()
            database.purpose = payload.purpose.strip()
            database.default_schema = payload.default_schema.strip()
            database.charset = payload.charset.strip()
            database.collation = payload.collation.strip()
            database.full_clean()
            database.save()
    except ValidationError as error:
        return _validation_problem(error)
    return _logical_database_out(database)


@data_application_specialist_router.post(
    "/infrastructure/logical-databases/{resource_id}/archive",
    response={200: LogicalDatabaseOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def archive_logical_database(
    request: HttpRequest,
    resource_id: int,
) -> LogicalDatabaseOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_logicaldatabase",
    )
    if problem:
        return problem
    database = (
        LogicalDatabase.objects.select_related("resource", "resource__client", "instance__resource")
        .filter(resource__in=_visible_queryset(request), resource_id=resource_id)
        .first()
    )
    if database is None:
        return _problem(404, "Logical database not found.", "not_found")
    _archive_resource(request, database.resource)
    return _logical_database_out(database)


@data_application_specialist_router.post(
    "/infrastructure/applications",
    response={
        201: ApplicationOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_application(
    request: HttpRequest,
    payload: ApplicationCreateIn,
) -> tuple[int, ApplicationOut | dict[str, object]]:
    problem = _permission_problem(
        request,
        "infrastructure.add_infrastructureresource",
        "infrastructure.add_applicationprofile",
    )
    if problem:
        return problem
    try:
        with transaction.atomic():
            resource, resource_problem = _new_resource(
                request,
                payload,
                InfrastructureResource.ResourceType.APPLICATION,
            )
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            assert resource is not None
            application = ApplicationProfile(resource=resource)
            _populate_application(application, payload)
            application.full_clean()
            application.save()
    except ValidationError as error:
        return _validation_problem(error)
    created = _visible_application(request, resource.id)
    assert created is not None
    return 201, _application_out(created)


@data_application_specialist_router.put(
    "/infrastructure/applications/{resource_id}",
    response={
        200: ApplicationOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_application(
    request: HttpRequest,
    resource_id: int,
    payload: ApplicationUpdateIn,
) -> ApplicationOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_applicationprofile",
    )
    if problem:
        return problem
    application = _visible_application(request, resource_id)
    if application is None:
        return _problem(404, "Application not found.", "not_found")
    try:
        with transaction.atomic():
            resource_problem = _update_resource(request, application.resource, payload)
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            _populate_application(application, payload)
            application.full_clean()
            application.save()
    except ValidationError as error:
        return _validation_problem(error)
    refreshed = _visible_application(request, resource_id)
    assert refreshed is not None
    return _application_out(refreshed)


@data_application_specialist_router.post(
    "/infrastructure/applications/{resource_id}/archive",
    response={200: ApplicationOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def archive_application(request: HttpRequest, resource_id: int) -> ApplicationOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_applicationprofile",
    )
    if problem:
        return problem
    application = _visible_application(request, resource_id)
    if application is None:
        return _problem(404, "Application not found.", "not_found")
    _archive_resource(request, application.resource)
    return _application_out(application)


@data_application_specialist_router.post(
    "/infrastructure/applications/{resource_id}/repositories",
    response={
        201: ApplicationRepositoryLinkOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_application_repository_link(
    request: HttpRequest,
    resource_id: int,
    payload: ApplicationRepositoryLinkCreateIn,
) -> tuple[int, ApplicationRepositoryLinkOut | dict[str, object]]:
    problem = _permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.view_applicationprofile",
        "infrastructure.view_sourcerepository",
        "infrastructure.view_applicationrepositorylink",
        "infrastructure.add_applicationrepositorylink",
    )
    if problem:
        return problem
    application = _visible_application(request, resource_id)
    if application is None:
        return _problem(404, "Application not found.", "not_found")
    repository = _visible_source_repository(request, payload.repository_resource_id)
    if repository is None:
        return _problem(404, "Source repository not found.", "not_found")
    link = ApplicationRepositoryLink(
        application=application,
        repository=repository,
        role=payload.role,
        path=payload.path.strip(),
        notes=payload.notes.strip(),
    )
    try:
        link.full_clean()
        link.save()
    except ValidationError as error:
        return _validation_problem(error)
    link = ApplicationRepositoryLink.objects.select_related("repository__resource").get(id=link.id)
    return 201, _repository_link_out(link)


@data_application_specialist_router.delete(
    "/infrastructure/applications/{resource_id}/repositories/{link_id}",
    response={204: None, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def delete_application_repository_link(
    request: HttpRequest,
    resource_id: int,
    link_id: int,
) -> tuple[int, None] | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.view_applicationprofile",
        "infrastructure.view_sourcerepository",
        "infrastructure.view_applicationrepositorylink",
        "infrastructure.delete_applicationrepositorylink",
    )
    if problem:
        return problem
    application = _visible_application(request, resource_id)
    if application is None:
        return _problem(404, "Application not found.", "not_found")
    link = ApplicationRepositoryLink.objects.filter(
        id=link_id,
        application=application,
        repository__resource__in=_visible_queryset(request),
    ).first()
    if link is None:
        return _problem(404, "Repository link not found.", "not_found")
    link.delete()
    return 204, None


@data_application_specialist_router.post(
    "/infrastructure/application-environments",
    response={
        201: ApplicationEnvironmentOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_application_environment(
    request: HttpRequest,
    payload: ApplicationEnvironmentCreateIn,
) -> tuple[int, ApplicationEnvironmentOut | dict[str, object]]:
    problem = _permission_problem(
        request,
        "infrastructure.add_infrastructureresource",
        "infrastructure.add_applicationenvironment",
    )
    if problem:
        return problem
    application = _visible_application(request, payload.application_resource_id)
    server = _visible_server(request, payload.server_resource_id)
    provider = _visible_provider_account(request, payload.provider_account_resource_id)
    if application is None:
        return _problem(404, "Application not found.", "not_found")
    if payload.server_resource_id is not None and server is None:
        return _problem(404, "Server not found.", "not_found")
    if payload.provider_account_resource_id is not None and provider is None:
        return _problem(404, "Provider account not found.", "not_found")
    try:
        with transaction.atomic():
            resource, resource_problem = _new_resource(
                request,
                payload,
                InfrastructureResource.ResourceType.APPLICATION_ENVIRONMENT,
            )
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            assert resource is not None
            environment = ApplicationEnvironment(
                resource=resource,
                application=application,
                server=server,
                provider_account=provider,
            )
            _populate_application_environment(environment, payload)
            environment.full_clean()
            environment.save()
    except ValidationError as error:
        return _validation_problem(error)
    created = ApplicationEnvironment.objects.select_related(
        "resource",
        "resource__client",
        "application__resource",
        "server__resource",
        "provider_account__resource",
        "provider_account__provider",
    ).get(resource_id=resource.id)
    return 201, _application_environment_out(created)


@data_application_specialist_router.put(
    "/infrastructure/application-environments/{resource_id}",
    response={
        200: ApplicationEnvironmentOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_application_environment(
    request: HttpRequest,
    resource_id: int,
    payload: ApplicationEnvironmentUpdateIn,
) -> ApplicationEnvironmentOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_applicationenvironment",
    )
    if problem:
        return problem
    environment = (
        ApplicationEnvironment.objects.select_related(
            "resource",
            "resource__client",
            "application__resource",
            "server__resource",
            "provider_account__resource",
            "provider_account__provider",
        )
        .filter(resource__in=_visible_queryset(request), resource_id=resource_id)
        .first()
    )
    if environment is None:
        return _problem(404, "Application environment not found.", "not_found")
    application = _visible_application(request, payload.application_resource_id)
    server = _visible_server(request, payload.server_resource_id)
    provider = _visible_provider_account(request, payload.provider_account_resource_id)
    if application is None:
        return _problem(404, "Application not found.", "not_found")
    if payload.server_resource_id is not None and server is None:
        return _problem(404, "Server not found.", "not_found")
    if payload.provider_account_resource_id is not None and provider is None:
        return _problem(404, "Provider account not found.", "not_found")
    try:
        with transaction.atomic():
            resource_problem = _update_resource(request, environment.resource, payload)
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            environment.application = application
            environment.server = server
            environment.provider_account = provider
            _populate_application_environment(environment, payload)
            environment.full_clean()
            environment.save()
    except ValidationError as error:
        return _validation_problem(error)
    return _application_environment_out(environment)


@data_application_specialist_router.post(
    "/infrastructure/application-environments/{resource_id}/archive",
    response={
        200: ApplicationEnvironmentOut,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def archive_application_environment(
    request: HttpRequest,
    resource_id: int,
) -> ApplicationEnvironmentOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_applicationenvironment",
    )
    if problem:
        return problem
    environment = (
        ApplicationEnvironment.objects.select_related(
            "resource",
            "resource__client",
            "application__resource",
            "server__resource",
            "provider_account__resource",
            "provider_account__provider",
        )
        .filter(resource__in=_visible_queryset(request), resource_id=resource_id)
        .first()
    )
    if environment is None:
        return _problem(404, "Application environment not found.", "not_found")
    _archive_resource(request, environment.resource)
    return _application_environment_out(environment)


@data_application_specialist_router.post(
    "/infrastructure/source-repositories",
    response={
        201: SourceRepositoryOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_source_repository(
    request: HttpRequest,
    payload: SourceRepositoryCreateIn,
) -> tuple[int, SourceRepositoryOut | dict[str, object]]:
    problem = _permission_problem(
        request,
        "infrastructure.add_infrastructureresource",
        "infrastructure.add_sourcerepository",
    )
    if problem:
        return problem
    provider = _visible_provider_account(request, payload.provider_account_resource_id)
    if payload.provider_account_resource_id is not None and provider is None:
        return _problem(404, "Provider account not found.", "not_found")
    try:
        with transaction.atomic():
            resource, resource_problem = _new_resource(
                request,
                payload,
                InfrastructureResource.ResourceType.SOURCE_REPOSITORY,
            )
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            assert resource is not None
            repository = SourceRepository(resource=resource, provider_account=provider)
            _populate_source_repository(repository, payload)
            repository.full_clean()
            repository.save()
    except ValidationError as error:
        return _validation_problem(error)
    created = _visible_source_repository(request, resource.id)
    assert created is not None
    return 201, _source_repository_out(created)


@data_application_specialist_router.put(
    "/infrastructure/source-repositories/{resource_id}",
    response={
        200: SourceRepositoryOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_source_repository(
    request: HttpRequest,
    resource_id: int,
    payload: SourceRepositoryUpdateIn,
) -> SourceRepositoryOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_sourcerepository",
    )
    if problem:
        return problem
    repository = _visible_source_repository(request, resource_id)
    if repository is None:
        return _problem(404, "Source repository not found.", "not_found")
    provider = _visible_provider_account(request, payload.provider_account_resource_id)
    if payload.provider_account_resource_id is not None and provider is None:
        return _problem(404, "Provider account not found.", "not_found")
    try:
        with transaction.atomic():
            resource_problem = _update_resource(request, repository.resource, payload)
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            repository.provider_account = provider
            _populate_source_repository(repository, payload)
            repository.full_clean()
            repository.save()
    except ValidationError as error:
        return _validation_problem(error)
    refreshed = _visible_source_repository(request, resource_id)
    assert refreshed is not None
    return _source_repository_out(refreshed)


@data_application_specialist_router.post(
    "/infrastructure/source-repositories/{resource_id}/archive",
    response={200: SourceRepositoryOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def archive_source_repository(
    request: HttpRequest,
    resource_id: int,
) -> SourceRepositoryOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_sourcerepository",
    )
    if problem:
        return problem
    repository = _visible_source_repository(request, resource_id)
    if repository is None:
        return _problem(404, "Source repository not found.", "not_found")
    _archive_resource(request, repository.resource)
    return _source_repository_out(repository)


@data_application_specialist_router.put(
    "/infrastructure/applications/{resource_id}/repositories/{link_id}",
    response={
        200: ApplicationRepositoryLinkOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_application_repository_link(
    request: HttpRequest, resource_id: int, link_id: int, payload: ApplicationRepositoryLinkCreateIn
) -> ApplicationRepositoryLinkOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.view_applicationprofile",
        "infrastructure.view_sourcerepository",
        "infrastructure.view_applicationrepositorylink",
        "infrastructure.change_applicationrepositorylink",
    )
    if problem:
        return problem
    owner = _visible_application(request, resource_id)
    related = _visible_source_repository(request, payload.repository_resource_id)
    if owner is None or related is None:
        return _problem(404, "Resource not found.", "not_found")
    try:
        with transaction.atomic():
            link = (
                ApplicationRepositoryLink.objects.select_for_update()
                .filter(
                    id=link_id,
                    application=owner,
                    repository__resource__in=_visible_queryset(request),
                )
                .first()
            )
            if link is None:
                return _problem(404, "Link not found.", "not_found")
            link.repository = related
            link.role = payload.role
            link.path = payload.path.strip()
            link.notes = payload.notes.strip()
            link.full_clean()
            link.save()
            AuditEvent.record(
                action="updated",
                target=link,
                actor=request.user,
                resource_id=owner.resource_id,
                client_id=owner.resource.client_id,
            )
    except ValidationError as error:
        return _validation_problem(error)
    return _repository_link_out(link)
