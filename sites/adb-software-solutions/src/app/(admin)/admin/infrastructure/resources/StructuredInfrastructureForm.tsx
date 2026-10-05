"use client";

import {
    Button,
    Card,
    DataError,
    DataLoading,
    Input,
    PageHeader,
    Select,
    Textarea,
} from "@/components/ui";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import { FormEvent, useEffect, useMemo, useState } from "react";

type SpecialistType = "server" | "network" | "subnet";
type SpecialistEditValue = string | number | boolean | null | string[];

interface ClientOption {
    id: number;
    name: string;
}

interface ProviderAccountOption {
    resource_id: number;
    name: string;
    provider_name: string;
    ownership_type: string;
    client_id: number | null;
    client_name: string | null;
}

interface NetworkOption {
    resource_id: number;
    name: string;
    ownership_type: string;
    client_id: number | null;
    client_name: string | null;
}

interface SubnetOption {
    resource_id: number;
    name: string;
    network_resource_id: number;
    cidr: string;
    ownership_type: string;
    client_id: number | null;
    client_name: string | null;
}

interface SpecialistOptions {
    clients: ClientOption[];
    provider_accounts: ProviderAccountOption[];
    networks: NetworkOption[];
    subnets: SubnetOption[];
}

interface SpecialistEditDetails {
    resource_id: number;
    resource_type: SpecialistType;
    ownership_type: "internal" | "client";
    client_id: number | null;
    client_name: string | null;
    name: string;
    lifecycle_status: string;
    environment: string;
    criticality: string;
    description: string;
    values: Record<string, SpecialistEditValue>;
}

interface SaveResult {
    resource_id: number;
}

interface StructuredInfrastructureFormProps {
    allowedTypes: SpecialistType[];
    creationContext?: {
        ownership_type: "internal" | "client";
        client_id: number | null;
        network_resource_id?: number;
    };
    onCancel: () => void;
    onCreated?: (resourceId: number) => void;
    editResourceId?: number;
    onSaved?: () => void;
}

function numberOrNull(value: string): number | null {
    const trimmed = value.trim();
    return trimmed ? Number(trimmed) : null;
}

function stringValue(value: SpecialistEditValue | undefined): string {
    if (value === null || value === undefined || Array.isArray(value))
        return "";
    return String(value);
}

function numberValue(value: SpecialistEditValue | undefined): string {
    return typeof value === "number" ? String(value) : "";
}

function booleanValue(value: SpecialistEditValue | undefined): string {
    return value === true ? "yes" : value === false ? "no" : "";
}

function listValue(value: SpecialistEditValue | undefined): string {
    return Array.isArray(value) ? value.join("\n") : "";
}

function dateTimeLocalValue(value: SpecialistEditValue | undefined): string {
    const rendered = stringValue(value);
    return rendered.includes("T") ? rendered.slice(0, 16) : rendered;
}

function label(value: SpecialistType): string {
    return value === "server"
        ? "Server"
        : value === "network"
          ? "Network"
          : "Subnet";
}

function collectionPath(type: SpecialistType): string {
    return type === "subnet" ? "subnets" : `${type}s`;
}

export function StructuredInfrastructureForm({
    allowedTypes,
    onCancel,
    onCreated,
    editResourceId,
    onSaved,
    creationContext,
}: StructuredInfrastructureFormProps) {
    const isEditing = editResourceId !== undefined;
    const [options, setOptions] = useState<SpecialistOptions | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [type, setType] = useState<SpecialistType>(
        allowedTypes[0] ?? "server",
    );
    const [ownership, setOwnership] = useState<"internal" | "client">(
        creationContext?.ownership_type ?? "internal",
    );
    const [clientId, setClientId] = useState(
        creationContext?.client_id ? String(creationContext.client_id) : "",
    );
    const [clientName, setClientName] = useState<string | null>(null);
    const [name, setName] = useState("");
    const [lifecycle, setLifecycle] = useState("active");
    const [environment, setEnvironment] = useState("production");
    const [criticality, setCriticality] = useState("normal");
    const [description, setDescription] = useState("");

    const [hostname, setHostname] = useState("");
    const [fqdn, setFqdn] = useState("");
    const [purpose, setPurpose] = useState("");
    const [role, setRole] = useState("");
    const [computeType, setComputeType] = useState("cloud_vm");
    const [architecture, setArchitecture] = useState("");
    const [cpuModel, setCpuModel] = useState("");
    const [cpuCores, setCpuCores] = useState("");
    const [ramMb, setRamMb] = useState("");
    const [rootDiskGb, setRootDiskGb] = useState("");
    const [osFamily, setOsFamily] = useState("linux");
    const [distribution, setDistribution] = useState("");
    const [osVersion, setOsVersion] = useState("");
    const [kernelVersion, setKernelVersion] = useState("");
    const [providerAccountId, setProviderAccountId] = useState("");
    const [providerResourceId, setProviderResourceId] = useState("");
    const [region, setRegion] = useState("");
    const [zone, setZone] = useState("");
    const [datacenter, setDatacenter] = useState("");
    const [virtualizationType, setVirtualizationType] = useState("");
    const [hypervisor, setHypervisor] = useState("");
    const [sshPort, setSshPort] = useState("22");
    const [timezone, setTimezone] = useState("");
    const [automaticUpdates, setAutomaticUpdates] = useState("");
    const [patchWindow, setPatchWindow] = useState("");
    const [lastPatchedAt, setLastPatchedAt] = useState("");
    const [commissionedAt, setCommissionedAt] = useState("");
    const [decommissionedAt, setDecommissionedAt] = useState("");

    const [networkType, setNetworkType] = useState("vpc");
    const [cidr, setCidr] = useState("");
    const [gateway, setGateway] = useState("");
    const [vlanId, setVlanId] = useState("");
    const [dnsServers, setDnsServers] = useState("");

    const [networkResourceId, setNetworkResourceId] = useState(
        creationContext?.network_resource_id
            ? String(creationContext.network_resource_id)
            : "",
    );
    const [availabilityZone, setAvailabilityZone] = useState("");

    useEffect(() => {
        let active = true;

        async function load() {
            try {
                setIsLoading(true);
                setError(null);
                const [loadedOptions, editDetails] = await Promise.all([
                    fetchAPI(
                        `${API_URL}/api/admin/infrastructure/specialist-options`,
                    ) as Promise<SpecialistOptions>,
                    editResourceId === undefined
                        ? Promise.resolve(null)
                        : (fetchAPI(
                              `${API_URL}/api/admin/infrastructure/resources/${editResourceId}/specialist-edit`,
                          ) as Promise<SpecialistEditDetails>),
                ]);
                if (!active) return;
                setOptions(loadedOptions);

                if (!editDetails) return;
                if (!allowedTypes.includes(editDetails.resource_type)) {
                    setError(
                        "This resource type cannot be edited from this form.",
                    );
                    return;
                }

                const values = editDetails.values;
                setType(editDetails.resource_type);
                setOwnership(editDetails.ownership_type);
                setClientId(
                    editDetails.client_id ? String(editDetails.client_id) : "",
                );
                setClientName(editDetails.client_name);
                setName(editDetails.name);
                setLifecycle(editDetails.lifecycle_status);
                setEnvironment(editDetails.environment);
                setCriticality(editDetails.criticality);
                setDescription(editDetails.description);

                setHostname(stringValue(values.hostname));
                setFqdn(stringValue(values.fqdn));
                setPurpose(stringValue(values.purpose));
                setRole(stringValue(values.role));
                setComputeType(stringValue(values.compute_type) || "cloud_vm");
                setArchitecture(stringValue(values.architecture));
                setCpuModel(stringValue(values.cpu_model));
                setCpuCores(numberValue(values.cpu_cores));
                setRamMb(numberValue(values.ram_mb));
                setRootDiskGb(numberValue(values.root_disk_gb));
                setOsFamily(stringValue(values.os_family) || "linux");
                setDistribution(stringValue(values.distribution));
                setOsVersion(stringValue(values.os_version));
                setKernelVersion(stringValue(values.kernel_version));
                setProviderAccountId(
                    numberValue(values.provider_account_resource_id),
                );
                setProviderResourceId(
                    stringValue(values.provider_resource_id) ||
                        stringValue(values.provider_network_id),
                );
                setRegion(stringValue(values.region));
                setZone(stringValue(values.zone));
                setDatacenter(stringValue(values.datacenter));
                setVirtualizationType(stringValue(values.virtualization_type));
                setHypervisor(stringValue(values.hypervisor));
                setSshPort(numberValue(values.ssh_port));
                setTimezone(stringValue(values.timezone));
                setAutomaticUpdates(booleanValue(values.automatic_updates));
                setPatchWindow(stringValue(values.patch_window));
                setLastPatchedAt(dateTimeLocalValue(values.last_patched_at));
                setCommissionedAt(stringValue(values.commissioned_at));
                setDecommissionedAt(stringValue(values.decommissioned_at));

                setNetworkType(stringValue(values.network_type) || "vpc");
                setCidr(stringValue(values.cidr));
                setGateway(stringValue(values.gateway));
                setVlanId(numberValue(values.vlan_id));
                setDnsServers(listValue(values.dns_servers));
                setNetworkResourceId(numberValue(values.network_resource_id));
                setAvailabilityZone(stringValue(values.availability_zone));
            } catch (loadError) {
                if (active) {
                    setError(
                        loadError instanceof Error
                            ? loadError.message
                            : "Unable to load infrastructure options.",
                    );
                }
            } finally {
                if (active) setIsLoading(false);
            }
        }

        void load();
        return () => {
            active = false;
        };
    }, [allowedTypes, editResourceId]);

    const providerAccounts = useMemo(
        () =>
            options?.provider_accounts.filter((provider) =>
                ownership === "internal"
                    ? provider.ownership_type === "internal"
                    : provider.ownership_type === "internal" ||
                      provider.client_id === Number(clientId),
            ) ?? [],
        [clientId, options, ownership],
    );

    const networks = useMemo(
        () =>
            options?.networks.filter((network) =>
                ownership === "internal"
                    ? network.ownership_type === "internal"
                    : network.ownership_type === "internal" ||
                      network.client_id === Number(clientId),
            ) ?? [],
        [clientId, options, ownership],
    );

    function changeOwnership(value: "internal" | "client") {
        setOwnership(value);
        setClientId("");
        setClientName(null);
        setProviderAccountId("");
        setNetworkResourceId("");
    }

    function changeClient(value: string) {
        setClientId(value);
        setProviderAccountId("");
        setNetworkResourceId("");
    }

    async function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!name.trim()) {
            setError("Enter a resource name.");
            return;
        }
        if (!isEditing && ownership === "client" && !clientId) {
            setError("Choose the Client that owns this resource.");
            return;
        }
        if (type === "server" && !hostname.trim()) {
            setError("Enter the server hostname.");
            return;
        }
        if (type === "subnet" && !networkResourceId) {
            setError("Choose the parent network.");
            return;
        }
        if ((type === "network" || type === "subnet") && !cidr.trim()) {
            setError("Enter the CIDR for this network resource.");
            return;
        }

        const common = {
            name: name.trim(),
            lifecycle_status: lifecycle,
            environment,
            criticality,
            description: description.trim(),
        };
        const createOwnership = {
            ownership_type: ownership,
            client_id: ownership === "client" ? Number(clientId) : null,
        };
        let payload: Record<string, unknown>;
        if (type === "server") {
            payload = {
                ...common,
                ...(!isEditing ? createOwnership : {}),
                hostname: hostname.trim(),
                fqdn: fqdn.trim(),
                purpose: purpose.trim(),
                role: role.trim(),
                compute_type: computeType,
                architecture: architecture.trim(),
                cpu_model: cpuModel.trim(),
                cpu_cores: numberOrNull(cpuCores),
                ram_mb: numberOrNull(ramMb),
                root_disk_gb: numberOrNull(rootDiskGb),
                os_family: osFamily,
                distribution: distribution.trim(),
                os_version: osVersion.trim(),
                kernel_version: kernelVersion.trim(),
                provider_account_resource_id: numberOrNull(providerAccountId),
                provider_resource_id: providerResourceId.trim(),
                region: region.trim(),
                zone: zone.trim(),
                datacenter: datacenter.trim(),
                virtualization_type: virtualizationType.trim(),
                hypervisor: hypervisor.trim(),
                ssh_port: numberOrNull(sshPort),
                timezone: timezone.trim(),
                automatic_updates:
                    automaticUpdates === "yes"
                        ? true
                        : automaticUpdates === "no"
                          ? false
                          : null,
                patch_window: patchWindow.trim(),
                last_patched_at: lastPatchedAt || null,
                commissioned_at: commissionedAt || null,
                decommissioned_at: decommissionedAt || null,
            };
        } else if (type === "network") {
            payload = {
                ...common,
                ...(!isEditing ? createOwnership : {}),
                network_type: networkType,
                provider_account_resource_id: numberOrNull(providerAccountId),
                provider_network_id: providerResourceId.trim(),
                cidr: cidr.trim(),
                gateway: gateway.trim() || null,
                region: region.trim(),
                vlan_id: numberOrNull(vlanId),
                dns_servers: dnsServers
                    .split(/[\n,]+/)
                    .map((value) => value.trim())
                    .filter(Boolean),
            };
        } else {
            payload = {
                ...common,
                ...(!isEditing ? createOwnership : {}),
                network_resource_id: Number(networkResourceId),
                cidr: cidr.trim(),
                gateway: gateway.trim() || null,
                vlan_id: numberOrNull(vlanId),
                availability_zone: availabilityZone.trim(),
                purpose: purpose.trim(),
            };
        }

        try {
            setIsSaving(true);
            setError(null);
            const endpoint = `${API_URL}/api/admin/infrastructure/${collectionPath(type)}${isEditing ? `/${editResourceId}` : ""}`;
            const saved = (await fetchAPI(endpoint, {
                method: isEditing ? "PUT" : "POST",
                body: JSON.stringify(payload),
            })) as SaveResult;
            if (isEditing) {
                onSaved?.();
            } else {
                onCreated?.(saved.resource_id);
            }
        } catch (saveError) {
            setError(
                saveError instanceof Error
                    ? saveError.message
                    : `Unable to ${isEditing ? "update" : "create"} this infrastructure resource.`,
            );
        } finally {
            setIsSaving(false);
        }
    }

    if (isLoading && !options) {
        return <DataLoading label="Loading infrastructure options..." />;
    }
    if (!options && error) {
        return <DataError message={error} />;
    }

    return (
        <form className="space-y-6" onSubmit={submit}>
            <PageHeader
                eyebrow="Structured infrastructure"
                title={`${isEditing ? "Edit" : "Add"} ${label(type).toLowerCase()}`}
                description={
                    isEditing
                        ? "Update native typed operational metadata. Resource type and ownership stay fixed to preserve scope and relationship integrity."
                        : "Create a native typed resource. Credentials remain separate Vault records linked after creation."
                }
            />

            <Card className="space-y-4 p-5">
                <h2 className="text-sm font-semibold text-white">
                    Resource identity
                </h2>
                <div className="grid gap-4 md:grid-cols-2">
                    <label className="space-y-2 text-xs text-slate-400">
                        Resource type
                        <Select
                            value={type}
                            onChange={(event) =>
                                setType(event.target.value as SpecialistType)
                            }
                            disabled={isSaving || isEditing}
                        >
                            {allowedTypes.map((value) => (
                                <option key={value} value={value}>
                                    {label(value)}
                                </option>
                            ))}
                        </Select>
                    </label>
                    <label className="space-y-2 text-xs text-slate-400">
                        Ownership
                        <Select
                            value={ownership}
                            onChange={(event) =>
                                changeOwnership(
                                    event.target.value as "internal" | "client",
                                )
                            }
                            disabled={
                                isSaving || isEditing || !!creationContext
                            }
                        >
                            <option value="internal">ADB Internal</option>
                            <option value="client">Client-owned</option>
                        </Select>
                    </label>
                    {ownership === "client" ? (
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                            Client
                            {isEditing ? (
                                <Input
                                    value={clientName ?? `Client #${clientId}`}
                                    disabled
                                />
                            ) : (
                                <Select
                                    value={clientId}
                                    onChange={(event) =>
                                        changeClient(event.target.value)
                                    }
                                    disabled={isSaving || !!creationContext}
                                >
                                    <option value="">Choose client</option>
                                    {options?.clients.map((client) => (
                                        <option
                                            key={client.id}
                                            value={client.id}
                                        >
                                            {client.name}
                                        </option>
                                    ))}
                                </Select>
                            )}
                        </label>
                    ) : null}
                    <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                        Name
                        <Input
                            value={name}
                            onChange={(event) => setName(event.target.value)}
                            placeholder="e.g. ADB LON Web 01"
                            disabled={isSaving}
                        />
                    </label>
                    <label className="space-y-2 text-xs text-slate-400">
                        Lifecycle
                        <Select
                            value={lifecycle}
                            onChange={(event) =>
                                setLifecycle(event.target.value)
                            }
                            disabled={isSaving}
                        >
                            <option value="planned">Planned</option>
                            <option value="active">Active</option>
                            <option value="maintenance">Maintenance</option>
                            <option value="deprecated">Deprecated</option>
                            <option value="retired">Retired</option>
                            <option value="archived">Archived</option>
                        </Select>
                    </label>
                    <label className="space-y-2 text-xs text-slate-400">
                        Environment
                        <Select
                            value={environment}
                            onChange={(event) =>
                                setEnvironment(event.target.value)
                            }
                            disabled={isSaving}
                        >
                            <option value="production">Production</option>
                            <option value="staging">Staging</option>
                            <option value="development">Development</option>
                            <option value="testing">Testing</option>
                            <option value="shared">Shared</option>
                            <option value="not_applicable">
                                Not applicable
                            </option>
                        </Select>
                    </label>
                    <label className="space-y-2 text-xs text-slate-400">
                        Criticality
                        <Select
                            value={criticality}
                            onChange={(event) =>
                                setCriticality(event.target.value)
                            }
                            disabled={isSaving}
                        >
                            <option value="low">Low</option>
                            <option value="normal">Normal</option>
                            <option value="high">High</option>
                            <option value="critical">Critical</option>
                        </Select>
                    </label>
                    <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                        Description
                        <Textarea
                            value={description}
                            onChange={(event) =>
                                setDescription(event.target.value)
                            }
                            rows={3}
                            disabled={isSaving}
                        />
                    </label>
                </div>
            </Card>

            {type === "server" ? (
                <Card className="space-y-4 p-5">
                    <h2 className="text-sm font-semibold text-white">
                        Server details
                    </h2>
                    <div className="grid gap-4 md:grid-cols-2">
                        <label className="space-y-2 text-xs text-slate-400">
                            Hostname
                            <Input
                                value={hostname}
                                onChange={(event) =>
                                    setHostname(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            FQDN
                            <Input
                                value={fqdn}
                                onChange={(event) =>
                                    setFqdn(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Purpose
                            <Input
                                value={purpose}
                                onChange={(event) =>
                                    setPurpose(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Role
                            <Input
                                value={role}
                                onChange={(event) =>
                                    setRole(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Compute type
                            <Select
                                value={computeType}
                                onChange={(event) =>
                                    setComputeType(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="cloud_vm">Cloud VM</option>
                                <option value="vps">VPS</option>
                                <option value="virtual_machine">
                                    Virtual machine
                                </option>
                                <option value="dedicated">Dedicated</option>
                                <option value="bare_metal">Bare metal</option>
                                <option value="hypervisor">Hypervisor</option>
                                <option value="container_host">
                                    Container host
                                </option>
                                <option value="nas">NAS</option>
                                <option value="other">Other</option>
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Architecture
                            <Input
                                value={architecture}
                                onChange={(event) =>
                                    setArchitecture(event.target.value)
                                }
                                placeholder="x86_64 / arm64"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                            Provider account
                            <Select
                                value={providerAccountId}
                                onChange={(event) =>
                                    setProviderAccountId(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="">No provider account</option>
                                {providerAccounts.map((provider) => (
                                    <option
                                        key={provider.resource_id}
                                        value={provider.resource_id}
                                    >
                                        {provider.name} ·{" "}
                                        {provider.provider_name}
                                    </option>
                                ))}
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Provider resource ID
                            <Input
                                value={providerResourceId}
                                onChange={(event) =>
                                    setProviderResourceId(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Region
                            <Input
                                value={region}
                                onChange={(event) =>
                                    setRegion(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Zone
                            <Input
                                value={zone}
                                onChange={(event) =>
                                    setZone(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Datacentre
                            <Input
                                value={datacenter}
                                onChange={(event) =>
                                    setDatacenter(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            CPU model
                            <Input
                                value={cpuModel}
                                onChange={(event) =>
                                    setCpuModel(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            CPU cores
                            <Input
                                type="number"
                                min="1"
                                value={cpuCores}
                                onChange={(event) =>
                                    setCpuCores(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            RAM (MB)
                            <Input
                                type="number"
                                min="1"
                                value={ramMb}
                                onChange={(event) =>
                                    setRamMb(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Root disk (GB)
                            <Input
                                type="number"
                                min="1"
                                value={rootDiskGb}
                                onChange={(event) =>
                                    setRootDiskGb(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            OS family
                            <Select
                                value={osFamily}
                                onChange={(event) =>
                                    setOsFamily(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="linux">Linux</option>
                                <option value="windows">Windows</option>
                                <option value="bsd">BSD</option>
                                <option value="appliance">Appliance</option>
                                <option value="other">Other</option>
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Distribution
                            <Input
                                value={distribution}
                                onChange={(event) =>
                                    setDistribution(event.target.value)
                                }
                                placeholder="Ubuntu"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            OS version
                            <Input
                                value={osVersion}
                                onChange={(event) =>
                                    setOsVersion(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Kernel version
                            <Input
                                value={kernelVersion}
                                onChange={(event) =>
                                    setKernelVersion(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Virtualisation
                            <Input
                                value={virtualizationType}
                                onChange={(event) =>
                                    setVirtualizationType(event.target.value)
                                }
                                placeholder="KVM / Hyper-V / VMware"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Hypervisor
                            <Input
                                value={hypervisor}
                                onChange={(event) =>
                                    setHypervisor(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            SSH port
                            <Input
                                type="number"
                                min="1"
                                max="65535"
                                value={sshPort}
                                onChange={(event) =>
                                    setSshPort(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Timezone
                            <Input
                                value={timezone}
                                onChange={(event) =>
                                    setTimezone(event.target.value)
                                }
                                placeholder="Europe/London"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Automatic updates
                            <Select
                                value={automaticUpdates}
                                onChange={(event) =>
                                    setAutomaticUpdates(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="">Not recorded</option>
                                <option value="yes">Enabled</option>
                                <option value="no">Disabled</option>
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Patch window
                            <Input
                                value={patchWindow}
                                onChange={(event) =>
                                    setPatchWindow(event.target.value)
                                }
                                placeholder="Sunday 03:00 Europe/London"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Last patched
                            <Input
                                type="datetime-local"
                                value={lastPatchedAt}
                                onChange={(event) =>
                                    setLastPatchedAt(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Commissioned
                            <Input
                                type="date"
                                value={commissionedAt}
                                onChange={(event) =>
                                    setCommissionedAt(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Decommissioned
                            <Input
                                type="date"
                                value={decommissionedAt}
                                onChange={(event) =>
                                    setDecommissionedAt(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                    </div>
                </Card>
            ) : null}

            {type === "network" ? (
                <Card className="space-y-4 p-5">
                    <h2 className="text-sm font-semibold text-white">
                        Network details
                    </h2>
                    <div className="grid gap-4 md:grid-cols-2">
                        <label className="space-y-2 text-xs text-slate-400">
                            Network type
                            <Select
                                value={networkType}
                                onChange={(event) =>
                                    setNetworkType(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="vpc">VPC</option>
                                <option value="lan">LAN</option>
                                <option value="vlan">VLAN</option>
                                <option value="vpn">VPN</option>
                                <option value="overlay">Overlay</option>
                                <option value="public">Public</option>
                                <option value="other">Other</option>
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Provider account
                            <Select
                                value={providerAccountId}
                                onChange={(event) =>
                                    setProviderAccountId(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="">No provider account</option>
                                {providerAccounts.map((provider) => (
                                    <option
                                        key={provider.resource_id}
                                        value={provider.resource_id}
                                    >
                                        {provider.name} ·{" "}
                                        {provider.provider_name}
                                    </option>
                                ))}
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            CIDR
                            <Input
                                value={cidr}
                                onChange={(event) =>
                                    setCidr(event.target.value)
                                }
                                placeholder="10.42.0.0/16"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Gateway
                            <Input
                                value={gateway}
                                onChange={(event) =>
                                    setGateway(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Provider network ID
                            <Input
                                value={providerResourceId}
                                onChange={(event) =>
                                    setProviderResourceId(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Region
                            <Input
                                value={region}
                                onChange={(event) =>
                                    setRegion(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            VLAN ID
                            <Input
                                type="number"
                                min="1"
                                max="4094"
                                value={vlanId}
                                onChange={(event) =>
                                    setVlanId(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                            DNS servers
                            <Textarea
                                value={dnsServers}
                                onChange={(event) =>
                                    setDnsServers(event.target.value)
                                }
                                placeholder="1.1.1.1, 1.0.0.1"
                                rows={2}
                                disabled={isSaving}
                            />
                        </label>
                    </div>
                </Card>
            ) : null}

            {type === "subnet" ? (
                <Card className="space-y-4 p-5">
                    <h2 className="text-sm font-semibold text-white">
                        Subnet details
                    </h2>
                    <div className="grid gap-4 md:grid-cols-2">
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                            Parent network
                            <Select
                                value={networkResourceId}
                                onChange={(event) =>
                                    setNetworkResourceId(event.target.value)
                                }
                                disabled={
                                    isSaving ||
                                    !!creationContext?.network_resource_id
                                }
                            >
                                <option value="">Choose network</option>
                                {networks.map((network) => (
                                    <option
                                        key={network.resource_id}
                                        value={network.resource_id}
                                    >
                                        {network.name} ·{" "}
                                        {network.client_name || "ADB Internal"}
                                    </option>
                                ))}
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            CIDR
                            <Input
                                value={cidr}
                                onChange={(event) =>
                                    setCidr(event.target.value)
                                }
                                placeholder="10.42.10.0/24"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Gateway
                            <Input
                                value={gateway}
                                onChange={(event) =>
                                    setGateway(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            VLAN ID
                            <Input
                                type="number"
                                min="1"
                                max="4094"
                                value={vlanId}
                                onChange={(event) =>
                                    setVlanId(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Availability zone
                            <Input
                                value={availabilityZone}
                                onChange={(event) =>
                                    setAvailabilityZone(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                            Purpose
                            <Input
                                value={purpose}
                                onChange={(event) =>
                                    setPurpose(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                    </div>
                </Card>
            ) : null}

            {error ? <p className="text-sm text-red-300">{error}</p> : null}
            <div className="flex justify-end gap-2">
                <Button
                    type="button"
                    variant="ghost"
                    onClick={onCancel}
                    disabled={isSaving}
                >
                    Cancel
                </Button>
                <Button
                    type="submit"
                    disabled={isSaving || allowedTypes.length === 0}
                >
                    {isSaving
                        ? isEditing
                            ? "Saving..."
                            : "Creating..."
                        : isEditing
                          ? "Save changes"
                          : `Create ${label(type).toLowerCase()}`}
                </Button>
            </div>
        </form>
    );
}
