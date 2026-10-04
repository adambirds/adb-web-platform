from __future__ import annotations

from typing import Any

from .models import (
    ApplicationEnvironment,
    ApplicationProfile,
    DatabaseInstance,
    InfrastructureResource,
    LogicalDatabase,
    SourceRepository,
)
from .snapshot_types import SpecialistField, SpecialistFieldKind


def _value(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _field(
    key: str,
    label: str,
    value: Any,
    kind: SpecialistFieldKind = "text",
) -> SpecialistField | None:
    rendered = _value(value)
    if not rendered:
        return None
    return SpecialistField(key=key, label=label, value=rendered, kind=kind)


def _fields(*fields: SpecialistField | None) -> tuple[SpecialistField, ...]:
    return tuple(field for field in fields if field is not None)


def _database_instance_fields(
    resource: InfrastructureResource,
) -> tuple[SpecialistField, ...]:
    database = (
        DatabaseInstance.objects.select_related(
            "server__resource",
            "provider_account__resource",
            "provider_account__provider",
        )
        .filter(resource=resource)
        .first()
    )
    if database is None:
        return ()
    server = database.server
    provider_account = database.provider_account
    return _fields(
        _field("engine", "Engine", database.get_engine_display()),
        _field("engine_version", "Engine version", database.engine_version, "code"),
        _field("hosting_type", "Hosting", database.get_hosting_type_display()),
        _field("server", "Server", server.resource.name if server else ""),
        _field(
            "provider_account",
            "Provider account",
            provider_account.resource.name if provider_account else "",
        ),
        _field(
            "provider",
            "Provider",
            provider_account.provider.name if provider_account else "",
        ),
        _field(
            "provider_resource_id",
            "Provider resource ID",
            database.provider_resource_id,
            "code",
        ),
        _field("endpoint", "Endpoint", database.endpoint, "code"),
        _field("port", "Port", database.port, "code"),
        _field("region", "Region", database.region),
        _field("zone", "Zone", database.zone),
        _field("tls_mode", "TLS", database.get_tls_mode_display()),
        _field("high_availability", "High availability", database.high_availability),
        _field("replica_count", "Replica count", database.replica_count),
        _field("backup_enabled", "Backups enabled", database.backup_enabled),
        _field("maintenance_window", "Maintenance window", database.maintenance_window),
    )


def _logical_database_fields(
    resource: InfrastructureResource,
) -> tuple[SpecialistField, ...]:
    database = (
        LogicalDatabase.objects.select_related("instance__resource")
        .filter(resource=resource)
        .first()
    )
    if database is None:
        return ()
    return _fields(
        _field("instance", "Database instance", database.instance.resource.name),
        _field("database_name", "Database name", database.database_name, "code"),
        _field("purpose", "Purpose", database.purpose),
        _field("default_schema", "Default schema", database.default_schema, "code"),
        _field("charset", "Character set", database.charset, "code"),
        _field("collation", "Collation", database.collation, "code"),
    )


def _application_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    application = (
        ApplicationProfile.objects.prefetch_related("repository_links__repository__resource")
        .filter(resource=resource)
        .first()
    )
    if application is None:
        return ()
    repository_rows = []
    for link in application.repository_links.all():
        text = f"{link.get_role_display()}: {link.repository.resource.name}"
        if link.path:
            text = f"{text} · {link.path}"
        repository_rows.append(text)
    return _fields(
        _field("application_type", "Application type", application.get_application_type_display()),
        _field("owner_team", "Owner/team", application.owner_team),
        _field("primary_language", "Primary language", application.primary_language),
        _field("framework", "Framework", application.framework),
        _field("repositories", "Source repositories", "\n".join(repository_rows), "multiline"),
    )


def _application_environment_fields(
    resource: InfrastructureResource,
) -> tuple[SpecialistField, ...]:
    environment = (
        ApplicationEnvironment.objects.select_related(
            "application__resource",
            "server__resource",
            "provider_account__resource",
            "provider_account__provider",
        )
        .filter(resource=resource)
        .first()
    )
    if environment is None:
        return ()
    server = environment.server
    provider_account = environment.provider_account
    return _fields(
        _field("application", "Application", environment.application.resource.name),
        _field("deployment_type", "Deployment", environment.get_deployment_type_display()),
        _field("server", "Server", server.resource.name if server else ""),
        _field(
            "provider_account",
            "Provider account",
            provider_account.resource.name if provider_account else "",
        ),
        _field(
            "provider",
            "Provider",
            provider_account.provider.name if provider_account else "",
        ),
        _field(
            "provider_resource_id",
            "Provider resource ID",
            environment.provider_resource_id,
            "code",
        ),
        _field("runtime", "Runtime", environment.runtime),
        _field("runtime_version", "Runtime version", environment.runtime_version, "code"),
        _field("release_version", "Release version", environment.release_version, "code"),
        _field("region", "Region", environment.region),
        _field("branch_or_ref", "Branch/ref", environment.branch_or_ref, "code"),
        _field("automatic_deployments", "Automatic deployments", environment.automatic_deployments),
    )


def _source_repository_fields(
    resource: InfrastructureResource,
) -> tuple[SpecialistField, ...]:
    repository = (
        SourceRepository.objects.select_related(
            "provider_account__resource",
            "provider_account__provider",
        )
        .filter(resource=resource)
        .first()
    )
    if repository is None:
        return ()
    provider_account = repository.provider_account
    return _fields(
        _field(
            "provider_account",
            "Provider account",
            provider_account.resource.name if provider_account else "",
        ),
        _field(
            "provider",
            "Provider",
            provider_account.provider.name if provider_account else "",
        ),
        _field("web_url", "Repository URL", repository.web_url, "url"),
        _field("clone_url", "Clone URL", repository.clone_url, "code"),
        _field(
            "provider_repository_id",
            "Provider repository ID",
            repository.provider_repository_id,
            "code",
        ),
        _field("owner_name", "Owner/namespace", repository.owner_name),
        _field("repository_name", "Repository name", repository.repository_name, "code"),
        _field("default_branch", "Default branch", repository.default_branch, "code"),
        _field("visibility", "Visibility", repository.get_visibility_display()),
        _field("is_fork", "Fork", repository.is_fork),
    )


def data_application_resource_snapshot(
    resource: InfrastructureResource,
) -> tuple[SpecialistField, ...]:
    """Return safe native data/application specialist fields for one resource."""

    if resource.resource_type == InfrastructureResource.ResourceType.DATABASE_INSTANCE:
        return _database_instance_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.LOGICAL_DATABASE:
        return _logical_database_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.APPLICATION:
        return _application_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.APPLICATION_ENVIRONMENT:
        return _application_environment_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.SOURCE_REPOSITORY:
        return _source_repository_fields(resource)
    return ()
