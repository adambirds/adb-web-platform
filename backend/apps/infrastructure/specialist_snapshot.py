from __future__ import annotations

from typing import Any

from .data_application_snapshot import data_application_resource_snapshot
from .models import InfrastructureResource, Network, ProviderAccount, ServerProfile, Subnet
from .operational_snapshot import operational_resource_snapshot
from .snapshot_types import SpecialistField, SpecialistFieldKind
from .web_domain_snapshot import web_domain_resource_snapshot


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


def _server_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    server = (
        ServerProfile.objects.select_related(
            "provider_account__resource",
            "provider_account__provider",
        )
        .prefetch_related(
            "interfaces__network__resource",
            "interfaces__subnet__resource",
            "interfaces__ip_addresses",
            "resource__ip_addresses",
        )
        .filter(resource=resource)
        .first()
    )
    if server is None:
        return ()

    provider_account = server.provider_account
    interface_rows: list[str] = []
    for interface in server.interfaces.all():
        parts = [interface.name]
        if interface.network:
            parts.append(interface.network.resource.name)
        if interface.subnet:
            parts.append(interface.subnet.resource.name)
        addresses = [item.address for item in interface.ip_addresses.all()]
        if addresses:
            parts.append(", ".join(addresses))
        interface_rows.append(" · ".join(parts))

    direct_addresses = [
        item.address for item in resource.ip_addresses.all() if item.interface_id is None
    ]

    return _fields(
        _field("hostname", "Hostname", server.hostname, "code"),
        _field("fqdn", "FQDN", server.fqdn, "code"),
        _field("purpose", "Purpose", server.purpose),
        _field("role", "Role", server.role),
        _field("compute_type", "Compute type", server.get_compute_type_display()),
        _field("architecture", "Architecture", server.architecture, "code"),
        _field("cpu_model", "CPU", server.cpu_model),
        _field("cpu_cores", "CPU cores", server.cpu_cores),
        _field("ram_mb", "RAM", f"{server.ram_mb} MB" if server.ram_mb is not None else ""),
        _field(
            "root_disk_gb",
            "Root disk",
            f"{server.root_disk_gb} GB" if server.root_disk_gb is not None else "",
        ),
        _field("os_family", "OS family", server.get_os_family_display()),
        _field("distribution", "Distribution", server.distribution),
        _field("os_version", "OS version", server.os_version, "code"),
        _field("kernel_version", "Kernel", server.kernel_version, "code"),
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
        _field("provider_resource_id", "Provider resource ID", server.provider_resource_id, "code"),
        _field("region", "Region", server.region),
        _field("zone", "Zone", server.zone),
        _field("datacenter", "Datacentre", server.datacenter),
        _field("virtualization_type", "Virtualisation", server.virtualization_type),
        _field("hypervisor", "Hypervisor", server.hypervisor),
        _field("ssh_port", "SSH port", server.ssh_port, "code"),
        _field("timezone", "Timezone", server.timezone),
        _field("automatic_updates", "Automatic updates", server.automatic_updates),
        _field("patch_window", "Patch window", server.patch_window),
        _field("last_patched_at", "Last patched", server.last_patched_at),
        _field("commissioned_at", "Commissioned", server.commissioned_at),
        _field("decommissioned_at", "Decommissioned", server.decommissioned_at),
        _field("interfaces", "Network interfaces", "\n".join(interface_rows), "multiline"),
        _field(
            "direct_ip_addresses",
            "Direct IP addresses",
            "\n".join(direct_addresses),
            "multiline",
        ),
    )


def _network_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    network = (
        Network.objects.select_related(
            "provider_account__resource",
            "provider_account__provider",
        )
        .filter(resource=resource)
        .first()
    )
    if network is None:
        return ()
    provider_account = network.provider_account
    return _fields(
        _field("network_type", "Network type", network.get_network_type_display()),
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
        _field("provider_network_id", "Provider network ID", network.provider_network_id, "code"),
        _field("cidr", "CIDR", network.cidr, "code"),
        _field("gateway", "Gateway", network.gateway, "code"),
        _field("region", "Region", network.region),
        _field("vlan_id", "VLAN ID", network.vlan_id, "code"),
        _field(
            "dns_servers",
            "DNS servers",
            "\n".join(str(value) for value in network.dns_servers),
            "multiline",
        ),
    )


def _subnet_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    subnet = Subnet.objects.select_related("network__resource").filter(resource=resource).first()
    if subnet is None:
        return ()
    return _fields(
        _field("network", "Network", subnet.network.resource.name),
        _field("cidr", "CIDR", subnet.cidr, "code"),
        _field("gateway", "Gateway", subnet.gateway, "code"),
        _field("vlan_id", "VLAN ID", subnet.vlan_id, "code"),
        _field("availability_zone", "Availability zone", subnet.availability_zone),
        _field("purpose", "Purpose", subnet.purpose),
    )


def _provider_account_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    account = ProviderAccount.objects.select_related("provider").filter(resource=resource).first()
    if account is None:
        return ()
    return _fields(
        _field("provider", "Service provider", account.provider.name),
        _field("account_identifier", "Account identifier", account.account_identifier, "code"),
        _field("tenant_id", "Tenant ID", account.tenant_id, "code"),
        _field("project_id", "Project ID", account.project_id, "code"),
        _field("portal_url", "Provider portal", account.portal_url, "url"),
        _field("default_region", "Default region", account.default_region),
        _field("support_plan", "Support plan", account.support_plan),
        _field("billing_reference", "Billing reference", account.billing_reference),
    )


def specialist_resource_snapshot(
    resource: InfrastructureResource,
) -> tuple[SpecialistField, ...]:
    """Return safe native specialist fields for one structured resource."""

    if resource.resource_type == InfrastructureResource.ResourceType.PROVIDER_ACCOUNT:
        return _provider_account_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.SERVER:
        return _server_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.NETWORK:
        return _network_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.SUBNET:
        return _subnet_fields(resource)
    snapshot = operational_resource_snapshot(resource)
    if snapshot:
        return snapshot
    snapshot = data_application_resource_snapshot(resource)
    if snapshot:
        return snapshot
    return web_domain_resource_snapshot(resource)
