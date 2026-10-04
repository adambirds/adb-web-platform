from __future__ import annotations

from typing import Any

from .models import (
    BackupPlanProfile,
    ContainerStackProfile,
    InfrastructureResource,
    KubernetesClusterProfile,
    KubernetesNamespaceProfile,
    KubernetesWorkloadProfile,
    ScheduledJobProfile,
    StorageProfile,
    SystemServiceProfile,
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


def _storage_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    profile = (
        StorageProfile.objects.select_related(
            "provider_account__provider",
            "provider_account__resource",
        )
        .filter(resource=resource)
        .first()
    )
    if profile is None:
        return ()
    provider = profile.provider_account
    return _fields(
        _field("storage_type", "Storage type", profile.get_storage_type_display()),
        _field("provider", "Provider", provider.provider.name if provider else ""),
        _field(
            "provider_account",
            "Provider account",
            provider.resource.name if provider else "",
        ),
        _field(
            "provider_resource_id",
            "Provider resource ID",
            profile.provider_resource_id,
            "code",
        ),
        _field("region", "Region", profile.region),
        _field(
            "capacity_gb",
            "Capacity",
            f"{profile.capacity_gb} GB" if profile.capacity_gb is not None else "",
        ),
        _field("filesystem", "Filesystem", profile.filesystem, "code"),
        _field("storage_class", "Storage class", profile.storage_class),
        _field("mount_path", "Mount path", profile.mount_path, "code"),
        _field("endpoint_url", "Endpoint", profile.endpoint_url, "url"),
        _field("encrypted", "Encrypted", profile.encrypted),
        _field(
            "retention_notes",
            "Retention notes",
            profile.retention_notes,
            "multiline",
        ),
    )


def _backup_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    profile = (
        BackupPlanProfile.objects.select_related(
            "destination_storage__resource",
            "provider_account__provider",
        )
        .prefetch_related("sources__source_resource")
        .filter(resource=resource)
        .first()
    )
    if profile is None:
        return ()
    provider = profile.provider_account
    sources = [
        f"{source.source_resource.name}{f' — {source.scope}' if source.scope else ''}"
        for source in profile.sources.all()
    ]
    return _fields(
        _field("backup_type", "Backup type", profile.get_backup_type_display()),
        _field("schedule", "Schedule", profile.schedule, "code"),
        _field("timezone", "Timezone", profile.timezone),
        _field("retention_days", "Retention days", profile.retention_days),
        _field("retention_copies", "Retention copies", profile.retention_copies),
        _field(
            "destination_storage",
            "Destination storage",
            profile.destination_storage.resource.name if profile.destination_storage else "",
        ),
        _field("provider", "Provider", provider.provider.name if provider else ""),
        _field("encrypted", "Encrypted", profile.encrypted),
        _field("last_success_at", "Last success", profile.last_success_at),
        _field("last_failure_at", "Last failure", profile.last_failure_at),
        _field("last_restore_test_at", "Last restore test", profile.last_restore_test_at),
        _field("sources", "Protected resources", "\n".join(sources), "multiline"),
        _field("recovery_notes", "Recovery notes", profile.recovery_notes, "multiline"),
    )


def _container_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    profile = (
        ContainerStackProfile.objects.select_related("host_resource")
        .prefetch_related("services")
        .filter(resource=resource)
        .first()
    )
    if profile is None:
        return ()
    services: list[str] = []
    for service in profile.services.all():
        parts = [service.name]
        if service.image:
            parts.append(service.image)
        if service.replicas is not None:
            parts.append(f"replicas={service.replicas}")
        if service.ports:
            parts.append(", ".join(str(port) for port in service.ports))
        services.append(" · ".join(parts))
    return _fields(
        _field("orchestrator", "Orchestrator", profile.get_orchestrator_display()),
        _field("host", "Host", profile.host_resource.name if profile.host_resource else ""),
        _field("project_name", "Project name", profile.project_name, "code"),
        _field(
            "orchestrator_version",
            "Version",
            profile.orchestrator_version,
            "code",
        ),
        _field("compose_path", "Compose/config path", profile.compose_path, "code"),
        _field(
            "working_directory",
            "Working directory",
            profile.working_directory,
            "code",
        ),
        _field("management_url", "Management URL", profile.management_url, "url"),
        _field("services", "Services", "\n".join(services), "multiline"),
        _field("notes", "Notes", profile.notes, "multiline"),
    )


def _cluster_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    profile = (
        KubernetesClusterProfile.objects.select_related("provider_account__provider")
        .prefetch_related("namespaces")
        .filter(resource=resource)
        .first()
    )
    if profile is None:
        return ()
    provider = profile.provider_account
    namespaces = [namespace.namespace for namespace in profile.namespaces.all()]
    return _fields(
        _field("distribution", "Distribution", profile.distribution),
        _field("version", "Kubernetes version", profile.version, "code"),
        _field("provider", "Provider", provider.provider.name if provider else ""),
        _field("api_server_url", "API server", profile.api_server_url, "url"),
        _field("management_url", "Management URL", profile.management_url, "url"),
        _field(
            "provider_cluster_id",
            "Provider cluster ID",
            profile.provider_cluster_id,
            "code",
        ),
        _field("region", "Region", profile.region),
        _field("node_count", "Nodes", profile.node_count),
        _field("high_availability", "High availability", profile.high_availability),
        _field("upgrade_channel", "Upgrade channel", profile.upgrade_channel),
        _field("namespaces", "Namespaces", "\n".join(namespaces), "multiline"),
        _field("notes", "Notes", profile.notes, "multiline"),
    )


def _namespace_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    profile = (
        KubernetesNamespaceProfile.objects.select_related("cluster__resource")
        .prefetch_related(
            "workloads",
            "services",
            "ingresses",
            "helm_releases",
            "persistent_storage",
        )
        .filter(resource=resource)
        .first()
    )
    if profile is None:
        return ()
    workloads = [
        f"{workload.get_workload_kind_display()} · {workload.workload_name}"
        for workload in profile.workloads.all()
    ]
    services = [service.name for service in profile.services.all()]
    ingresses: list[str] = []
    for ingress in profile.ingresses.all():
        hosts = ", ".join(str(host) for host in ingress.hosts)
        ingresses.append(f"{ingress.name} · {hosts}" if hosts else ingress.name)
    releases = [
        f"{release.name} · {release.chart}{f' {release.chart_version}' if release.chart_version else ''}"
        for release in profile.helm_releases.all()
    ]
    storage = [
        f"{item.name}{f' · {item.capacity_gb} GB' if item.capacity_gb is not None else ''}"
        for item in profile.persistent_storage.all()
    ]
    return _fields(
        _field("cluster", "Cluster", profile.cluster.resource.name),
        _field("namespace", "Namespace", profile.namespace, "code"),
        _field("purpose", "Purpose", profile.purpose),
        _field(
            "resource_quota_summary",
            "Resource quota",
            profile.resource_quota_summary,
            "multiline",
        ),
        _field("workloads", "Workloads", "\n".join(workloads), "multiline"),
        _field("services", "Services", "\n".join(services), "multiline"),
        _field("ingresses", "Ingresses", "\n".join(ingresses), "multiline"),
        _field("helm_releases", "Helm releases", "\n".join(releases), "multiline"),
        _field(
            "persistent_storage",
            "Persistent storage",
            "\n".join(storage),
            "multiline",
        ),
    )


def _workload_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    profile = (
        KubernetesWorkloadProfile.objects.select_related(
            "namespace__cluster__resource",
        )
        .prefetch_related("services")
        .filter(resource=resource)
        .first()
    )
    if profile is None:
        return ()
    return _fields(
        _field("cluster", "Cluster", profile.namespace.cluster.resource.name),
        _field("namespace", "Namespace", profile.namespace.namespace, "code"),
        _field("workload_kind", "Kind", profile.get_workload_kind_display()),
        _field("workload_name", "Workload name", profile.workload_name, "code"),
        _field("replicas_desired", "Desired replicas", profile.replicas_desired),
        _field("image_summary", "Images", profile.image_summary, "multiline"),
        _field("selector_summary", "Selector", profile.selector_summary, "code"),
        _field("service_account", "Service account", profile.service_account, "code"),
        _field(
            "services",
            "Services",
            "\n".join(service.name for service in profile.services.all()),
            "multiline",
        ),
        _field("notes", "Notes", profile.notes, "multiline"),
    )


def _system_service_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    profile = (
        SystemServiceProfile.objects.select_related("host_resource")
        .filter(resource=resource)
        .first()
    )
    if profile is None:
        return ()
    return _fields(
        _field("host", "Host", profile.host_resource.name),
        _field("manager", "Service manager", profile.get_manager_display()),
        _field("unit_name", "Unit/service name", profile.unit_name, "code"),
        _field("display_name", "Display name", profile.display_name),
        _field("expected_state", "Expected state", profile.expected_state),
        _field("startup_type", "Startup type", profile.startup_type),
        _field("executable", "Executable", profile.executable, "code"),
        _field("config_path", "Config path", profile.config_path, "code"),
        _field(
            "working_directory",
            "Working directory",
            profile.working_directory,
            "code",
        ),
        _field("log_location", "Logs", profile.log_location, "code"),
        _field("restart_policy", "Restart policy", profile.restart_policy),
        _field("notes", "Notes", profile.notes, "multiline"),
    )


def _scheduled_job_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    profile = (
        ScheduledJobProfile.objects.select_related("host_resource")
        .filter(resource=resource)
        .first()
    )
    if profile is None:
        return ()
    return _fields(
        _field("scheduler", "Scheduler", profile.get_scheduler_display()),
        _field(
            "host",
            "Host/context",
            profile.host_resource.name if profile.host_resource else "",
        ),
        _field("schedule_expression", "Schedule", profile.schedule_expression, "code"),
        _field("timezone", "Timezone", profile.timezone),
        _field("enabled", "Enabled", profile.enabled),
        _field(
            "command_summary",
            "Command/job summary",
            profile.command_summary,
            "multiline",
        ),
        _field("config_path", "Config path", profile.config_path, "code"),
        _field(
            "working_directory",
            "Working directory",
            profile.working_directory,
            "code",
        ),
        _field("run_as", "Run as", profile.run_as, "code"),
        _field("last_success_at", "Last success", profile.last_success_at),
        _field("last_failure_at", "Last failure", profile.last_failure_at),
        _field("next_run_at", "Next run", profile.next_run_at),
        _field("notes", "Notes", profile.notes, "multiline"),
    )


def operational_resource_snapshot(
    resource: InfrastructureResource,
) -> tuple[SpecialistField, ...]:
    if resource.resource_type == InfrastructureResource.ResourceType.STORAGE:
        return _storage_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.BACKUP_PLAN:
        return _backup_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.CONTAINER_STACK:
        return _container_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.KUBERNETES_CLUSTER:
        return _cluster_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.KUBERNETES_NAMESPACE:
        return _namespace_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.KUBERNETES_WORKLOAD:
        return _workload_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.SYSTEM_SERVICE:
        return _system_service_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.SCHEDULED_JOB:
        return _scheduled_job_fields(resource)
    return ()
