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

export type DataApplicationType =
    | "database_instance"
    | "logical_database"
    | "application"
    | "application_environment"
    | "source_repository";

interface ScopedOption {
    resource_id: number;
    name: string;
    ownership_type: string;
    client_id: number | null;
    client_name: string | null;
}

interface ClientOption {
    id: number;
    name: string;
}

interface ProviderAccountOption extends ScopedOption {
    provider_name: string;
}

interface ServerOption extends ScopedOption {
    hostname: string;
}

interface DatabaseInstanceOption extends ScopedOption {
    engine: string;
}

interface ApplicationOption extends ScopedOption {
    application_type: string;
}

interface SourceRepositoryOption extends ScopedOption {
    repository_name: string;
}

interface DataApplicationOptions {
    clients: ClientOption[];
    provider_accounts: ProviderAccountOption[];
    servers: ServerOption[];
    database_instances: DatabaseInstanceOption[];
    applications: ApplicationOption[];
    source_repositories: SourceRepositoryOption[];
}

interface SpecialistEditDetail {
    resource_id: number;
    resource_type: string;
    ownership_type: string;
    client_id: number | null;
    client_name: string | null;
    name: string;
    lifecycle_status: string;
    environment: string;
    criticality: string;
    description: string;
    values: Record<string, string | number | boolean | string[] | null>;
}

interface DataApplicationInfrastructureFormProps {
    allowedTypes: DataApplicationType[];
    creationContext?: { ownership_type: string; client_id: number | null };
    editResourceId?: number;
    onCancel: () => void;
    onCreated?: (resourceId: number) => void;
    onSaved?: () => void;
}

const ENDPOINTS: Record<DataApplicationType, string> = {
    database_instance: "database-instances",
    logical_database: "logical-databases",
    application: "applications",
    application_environment: "application-environments",
    source_repository: "source-repositories",
};

function label(value: DataApplicationType): string {
    const labels: Record<DataApplicationType, string> = {
        database_instance: "Database instance",
        logical_database: "Logical database",
        application: "Application",
        application_environment: "Application environment",
        source_repository: "Source repository",
    };
    return labels[value];
}

function numberOrNull(value: string): number | null {
    const trimmed = value.trim();
    return trimmed ? Number(trimmed) : null;
}

function textValue(value: unknown): string {
    return value === null || value === undefined ? "" : String(value);
}

function triStateValue(value: unknown): string {
    return value === true ? "true" : value === false ? "false" : "";
}

function triStatePayload(value: string): boolean | null {
    return value === "true" ? true : value === "false" ? false : null;
}

function optionAllowed(
    option: ScopedOption,
    ownership: string,
    clientId: string,
): boolean {
    if (ownership === "internal") return option.ownership_type === "internal";
    return (
        option.ownership_type === "internal" ||
        option.client_id === Number(clientId)
    );
}

export function DataApplicationInfrastructureForm({
    allowedTypes,
    editResourceId,
    onCancel,
    onCreated,
    onSaved,
    creationContext,
}: DataApplicationInfrastructureFormProps) {
    const isEditing = editResourceId !== undefined;
    const [options, setOptions] = useState<DataApplicationOptions | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [type, setType] = useState<DataApplicationType>(
        allowedTypes[0] ?? "database_instance",
    );
    const [ownership, setOwnership] = useState(
        creationContext?.ownership_type ?? "internal",
    );
    const [clientId, setClientId] = useState(
        creationContext?.client_id ? String(creationContext.client_id) : "",
    );
    const [name, setName] = useState("");
    const [lifecycle, setLifecycle] = useState("active");
    const [environment, setEnvironment] = useState("not_applicable");
    const [criticality, setCriticality] = useState("normal");
    const [description, setDescription] = useState("");

    const [engine, setEngine] = useState("postgresql");
    const [engineVersion, setEngineVersion] = useState("");
    const [hostingType, setHostingType] = useState("managed");
    const [serverResourceId, setServerResourceId] = useState("");
    const [providerAccountId, setProviderAccountId] = useState("");
    const [providerResourceId, setProviderResourceId] = useState("");
    const [endpoint, setEndpoint] = useState("");
    const [port, setPort] = useState("");
    const [region, setRegion] = useState("");
    const [zone, setZone] = useState("");
    const [tlsMode, setTlsMode] = useState("unknown");
    const [highAvailability, setHighAvailability] = useState("");
    const [replicaCount, setReplicaCount] = useState("");
    const [backupEnabled, setBackupEnabled] = useState("");
    const [maintenanceWindow, setMaintenanceWindow] = useState("");

    const [instanceResourceId, setInstanceResourceId] = useState("");
    const [databaseName, setDatabaseName] = useState("");
    const [purpose, setPurpose] = useState("");
    const [defaultSchema, setDefaultSchema] = useState("");
    const [charset, setCharset] = useState("");
    const [collation, setCollation] = useState("");

    const [applicationType, setApplicationType] = useState("web_app");
    const [ownerTeam, setOwnerTeam] = useState("");
    const [primaryLanguage, setPrimaryLanguage] = useState("");
    const [framework, setFramework] = useState("");

    const [applicationResourceId, setApplicationResourceId] = useState("");
    const [deploymentType, setDeploymentType] = useState("server");
    const [runtime, setRuntime] = useState("");
    const [runtimeVersion, setRuntimeVersion] = useState("");
    const [releaseVersion, setReleaseVersion] = useState("");
    const [branchOrRef, setBranchOrRef] = useState("");
    const [automaticDeployments, setAutomaticDeployments] = useState("");

    const [webUrl, setWebUrl] = useState("");
    const [cloneUrl, setCloneUrl] = useState("");
    const [providerRepositoryId, setProviderRepositoryId] = useState("");
    const [ownerName, setOwnerName] = useState("");
    const [repositoryName, setRepositoryName] = useState("");
    const [defaultBranch, setDefaultBranch] = useState("");
    const [visibility, setVisibility] = useState("private");
    const [isFork, setIsFork] = useState(false);

    useEffect(() => {
        let active = true;

        async function load() {
            try {
                setIsLoading(true);
                setError(null);
                const optionResult = (await fetchAPI(
                    `${API_URL}/api/admin/infrastructure/data-application-options`,
                )) as DataApplicationOptions;
                if (!active) return;
                setOptions(optionResult);

                if (editResourceId === undefined) return;
                const detail = (await fetchAPI(
                    `${API_URL}/api/admin/infrastructure/resources/${editResourceId}/specialist-edit`,
                )) as SpecialistEditDetail;
                if (!active) return;
                const resourceType =
                    detail.resource_type as DataApplicationType;
                if (!allowedTypes.includes(resourceType)) {
                    throw new Error(
                        "This resource type cannot be edited with this form.",
                    );
                }

                setType(resourceType);
                setOwnership(detail.ownership_type);
                setClientId(
                    detail.client_id === null ? "" : String(detail.client_id),
                );
                setName(detail.name);
                setLifecycle(detail.lifecycle_status);
                setEnvironment(detail.environment);
                setCriticality(detail.criticality);
                setDescription(detail.description);

                const values = detail.values;
                setEngine(textValue(values.engine) || "postgresql");
                setEngineVersion(textValue(values.engine_version));
                setHostingType(textValue(values.hosting_type) || "managed");
                setServerResourceId(textValue(values.server_resource_id));
                setProviderAccountId(
                    textValue(values.provider_account_resource_id),
                );
                setProviderResourceId(textValue(values.provider_resource_id));
                setEndpoint(textValue(values.endpoint));
                setPort(textValue(values.port));
                setRegion(textValue(values.region));
                setZone(textValue(values.zone));
                setTlsMode(textValue(values.tls_mode) || "unknown");
                setHighAvailability(triStateValue(values.high_availability));
                setReplicaCount(textValue(values.replica_count));
                setBackupEnabled(triStateValue(values.backup_enabled));
                setMaintenanceWindow(textValue(values.maintenance_window));

                setInstanceResourceId(textValue(values.instance_resource_id));
                setDatabaseName(textValue(values.database_name));
                setPurpose(textValue(values.purpose));
                setDefaultSchema(textValue(values.default_schema));
                setCharset(textValue(values.charset));
                setCollation(textValue(values.collation));

                setApplicationType(
                    textValue(values.application_type) || "web_app",
                );
                setOwnerTeam(textValue(values.owner_team));
                setPrimaryLanguage(textValue(values.primary_language));
                setFramework(textValue(values.framework));

                setApplicationResourceId(
                    textValue(values.application_resource_id),
                );
                setDeploymentType(
                    textValue(values.deployment_type) || "server",
                );
                setRuntime(textValue(values.runtime));
                setRuntimeVersion(textValue(values.runtime_version));
                setReleaseVersion(textValue(values.release_version));
                setBranchOrRef(textValue(values.branch_or_ref));
                setAutomaticDeployments(
                    triStateValue(values.automatic_deployments),
                );

                setWebUrl(textValue(values.web_url));
                setCloneUrl(textValue(values.clone_url));
                setProviderRepositoryId(
                    textValue(values.provider_repository_id),
                );
                setOwnerName(textValue(values.owner_name));
                setRepositoryName(textValue(values.repository_name));
                setDefaultBranch(textValue(values.default_branch));
                setVisibility(textValue(values.visibility) || "private");
                setIsFork(values.is_fork === true);
            } catch (loadError) {
                if (active) {
                    setError(
                        loadError instanceof Error
                            ? loadError.message
                            : "Unable to load infrastructure resource options.",
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
    }, [editResourceId]);

    useEffect(() => {
        if (ownership === "internal") setClientId("");
        if (!isEditing) {
            setServerResourceId("");
            setProviderAccountId("");
            setInstanceResourceId("");
            setApplicationResourceId("");
        }
    }, [ownership, clientId, isEditing]);

    const providerAccounts = useMemo(
        () =>
            options?.provider_accounts.filter((option) =>
                optionAllowed(option, ownership, clientId),
            ) ?? [],
        [clientId, options, ownership],
    );
    const servers = useMemo(
        () =>
            options?.servers.filter((option) =>
                optionAllowed(option, ownership, clientId),
            ) ?? [],
        [clientId, options, ownership],
    );
    const databaseInstances = useMemo(
        () =>
            options?.database_instances.filter((option) =>
                optionAllowed(option, ownership, clientId),
            ) ?? [],
        [clientId, options, ownership],
    );
    const applications = useMemo(
        () =>
            options?.applications.filter((option) =>
                optionAllowed(option, ownership, clientId),
            ) ?? [],
        [clientId, options, ownership],
    );

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
        if (
            type === "logical_database" &&
            (!instanceResourceId || !databaseName.trim())
        ) {
            setError(
                "Choose a Database Instance and enter the logical database name.",
            );
            return;
        }
        if (type === "application_environment" && !applicationResourceId) {
            setError("Choose the Application this environment belongs to.");
            return;
        }
        if (type === "source_repository" && !repositoryName.trim()) {
            setError("Enter the repository name.");
            return;
        }

        const common: Record<string, unknown> = {
            name: name.trim(),
            lifecycle_status: lifecycle,
            environment,
            criticality,
            description: description.trim(),
        };
        if (!isEditing) {
            common.ownership_type = ownership;
            common.client_id = ownership === "client" ? Number(clientId) : null;
        }

        let payload: Record<string, unknown>;
        if (type === "database_instance") {
            payload = {
                ...common,
                engine,
                engine_version: engineVersion.trim(),
                hosting_type: hostingType,
                server_resource_id:
                    hostingType === "managed"
                        ? null
                        : numberOrNull(serverResourceId),
                provider_account_resource_id: numberOrNull(providerAccountId),
                provider_resource_id: providerResourceId.trim(),
                endpoint: endpoint.trim(),
                port: numberOrNull(port),
                region: region.trim(),
                zone: zone.trim(),
                tls_mode: tlsMode,
                high_availability: triStatePayload(highAvailability),
                replica_count: numberOrNull(replicaCount),
                backup_enabled: triStatePayload(backupEnabled),
                maintenance_window: maintenanceWindow.trim(),
            };
        } else if (type === "logical_database") {
            payload = {
                ...common,
                instance_resource_id: Number(instanceResourceId),
                database_name: databaseName.trim(),
                purpose: purpose.trim(),
                default_schema: defaultSchema.trim(),
                charset: charset.trim(),
                collation: collation.trim(),
            };
        } else if (type === "application") {
            payload = {
                ...common,
                application_type: applicationType,
                owner_team: ownerTeam.trim(),
                primary_language: primaryLanguage.trim(),
                framework: framework.trim(),
            };
        } else if (type === "application_environment") {
            payload = {
                ...common,
                application_resource_id: Number(applicationResourceId),
                deployment_type: deploymentType,
                server_resource_id: numberOrNull(serverResourceId),
                provider_account_resource_id: numberOrNull(providerAccountId),
                provider_resource_id: providerResourceId.trim(),
                runtime: runtime.trim(),
                runtime_version: runtimeVersion.trim(),
                release_version: releaseVersion.trim(),
                region: region.trim(),
                branch_or_ref: branchOrRef.trim(),
                automatic_deployments: triStatePayload(automaticDeployments),
            };
        } else {
            payload = {
                ...common,
                provider_account_resource_id: numberOrNull(providerAccountId),
                web_url: webUrl.trim(),
                clone_url: cloneUrl.trim(),
                provider_repository_id: providerRepositoryId.trim(),
                owner_name: ownerName.trim(),
                repository_name: repositoryName.trim(),
                default_branch: defaultBranch.trim(),
                visibility,
                is_fork: isFork,
            };
        }

        try {
            setIsSaving(true);
            setError(null);
            const baseEndpoint = `${API_URL}/api/admin/infrastructure/${ENDPOINTS[type]}`;
            const saved = (await fetchAPI(
                isEditing ? `${baseEndpoint}/${editResourceId}` : baseEndpoint,
                {
                    method: isEditing ? "PUT" : "POST",
                    body: JSON.stringify(payload),
                },
            )) as { resource_id: number };

            if (isEditing) onSaved?.();
            else onCreated?.(saved.resource_id);
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
        return <DataLoading label="Loading data and application options..." />;
    }
    if (!options && error) {
        return <DataError message={error} />;
    }

    return (
        <form className="space-y-6" onSubmit={submit}>
            <PageHeader
                eyebrow="Structured infrastructure"
                title={`${isEditing ? "Edit" : "Add"} ${label(type).toLowerCase()}`}
                description="Operational metadata stays on the typed resource. Passwords, tokens and private keys belong in the linked Credential Vault."
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
                                setType(
                                    event.target.value as DataApplicationType,
                                )
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
                                setOwnership(event.target.value)
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
                            <Select
                                value={clientId}
                                onChange={(event) =>
                                    setClientId(event.target.value)
                                }
                                disabled={
                                    isSaving || isEditing || !!creationContext
                                }
                            >
                                <option value="">Choose client</option>
                                {options?.clients.map((client) => (
                                    <option key={client.id} value={client.id}>
                                        {client.name}
                                    </option>
                                ))}
                            </Select>
                        </label>
                    ) : null}
                    <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                        Name
                        <Input
                            value={name}
                            onChange={(event) => setName(event.target.value)}
                            disabled={isSaving}
                        />
                    </label>
                    {isEditing ? (
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
                    ) : null}
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

            {type === "database_instance" ? (
                <Card className="space-y-4 p-5">
                    <h2 className="text-sm font-semibold text-white">
                        Database instance
                    </h2>
                    <div className="grid gap-4 md:grid-cols-2">
                        <label className="space-y-2 text-xs text-slate-400">
                            Engine
                            <Select
                                value={engine}
                                onChange={(event) =>
                                    setEngine(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="postgresql">PostgreSQL</option>
                                <option value="mysql">MySQL</option>
                                <option value="mariadb">MariaDB</option>
                                <option value="mongodb">MongoDB</option>
                                <option value="redis">Redis</option>
                                <option value="sql_server">SQL Server</option>
                                <option value="oracle">Oracle</option>
                                <option value="other">Other</option>
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Engine version
                            <Input
                                value={engineVersion}
                                onChange={(event) =>
                                    setEngineVersion(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Hosting
                            <Select
                                value={hostingType}
                                onChange={(event) => {
                                    setHostingType(event.target.value);
                                    if (event.target.value === "managed")
                                        setServerResourceId("");
                                }}
                                disabled={isSaving}
                            >
                                <option value="managed">Managed service</option>
                                <option value="self_hosted">Self-hosted</option>
                                <option value="container">Container</option>
                                <option value="appliance">Appliance</option>
                                <option value="other">Other</option>
                            </Select>
                        </label>
                        {hostingType !== "managed" ? (
                            <label className="space-y-2 text-xs text-slate-400">
                                Hosting server
                                <Select
                                    value={serverResourceId}
                                    onChange={(event) =>
                                        setServerResourceId(event.target.value)
                                    }
                                    disabled={isSaving}
                                >
                                    <option value="">No server selected</option>
                                    {servers.map((server) => (
                                        <option
                                            key={server.resource_id}
                                            value={server.resource_id}
                                        >
                                            {server.name} · {server.hostname}
                                        </option>
                                    ))}
                                </Select>
                            </label>
                        ) : null}
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
                            Endpoint
                            <Input
                                value={endpoint}
                                onChange={(event) =>
                                    setEndpoint(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Port
                            <Input
                                type="number"
                                min="1"
                                max="65535"
                                value={port}
                                onChange={(event) =>
                                    setPort(event.target.value)
                                }
                                disabled={isSaving}
                            />
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
                            TLS
                            <Select
                                value={tlsMode}
                                onChange={(event) =>
                                    setTlsMode(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="required">Required</option>
                                <option value="preferred">Preferred</option>
                                <option value="disabled">Disabled</option>
                                <option value="unknown">Unknown</option>
                            </Select>
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
                            High availability
                            <Select
                                value={highAvailability}
                                onChange={(event) =>
                                    setHighAvailability(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="">Unknown</option>
                                <option value="true">Enabled</option>
                                <option value="false">Disabled</option>
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Replica count
                            <Input
                                type="number"
                                min="0"
                                value={replicaCount}
                                onChange={(event) =>
                                    setReplicaCount(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Backups
                            <Select
                                value={backupEnabled}
                                onChange={(event) =>
                                    setBackupEnabled(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="">Unknown</option>
                                <option value="true">Enabled</option>
                                <option value="false">Disabled</option>
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Maintenance window
                            <Input
                                value={maintenanceWindow}
                                onChange={(event) =>
                                    setMaintenanceWindow(event.target.value)
                                }
                                placeholder="Sunday 03:00 Europe/London"
                                disabled={isSaving}
                            />
                        </label>
                    </div>
                </Card>
            ) : null}

            {type === "logical_database" ? (
                <Card className="space-y-4 p-5">
                    <h2 className="text-sm font-semibold text-white">
                        Logical database
                    </h2>
                    <div className="grid gap-4 md:grid-cols-2">
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                            Database instance
                            <Select
                                value={instanceResourceId}
                                onChange={(event) =>
                                    setInstanceResourceId(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="">
                                    Choose database instance
                                </option>
                                {databaseInstances.map((database) => (
                                    <option
                                        key={database.resource_id}
                                        value={database.resource_id}
                                    >
                                        {database.name} · {database.engine}
                                    </option>
                                ))}
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Database name
                            <Input
                                value={databaseName}
                                onChange={(event) =>
                                    setDatabaseName(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Default schema
                            <Input
                                value={defaultSchema}
                                onChange={(event) =>
                                    setDefaultSchema(event.target.value)
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
                        <label className="space-y-2 text-xs text-slate-400">
                            Character set
                            <Input
                                value={charset}
                                onChange={(event) =>
                                    setCharset(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Collation
                            <Input
                                value={collation}
                                onChange={(event) =>
                                    setCollation(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                    </div>
                </Card>
            ) : null}

            {type === "application" ? (
                <Card className="space-y-4 p-5">
                    <h2 className="text-sm font-semibold text-white">
                        Application
                    </h2>
                    <div className="grid gap-4 md:grid-cols-2">
                        <label className="space-y-2 text-xs text-slate-400">
                            Application type
                            <Select
                                value={applicationType}
                                onChange={(event) =>
                                    setApplicationType(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="web_app">Web application</option>
                                <option value="saas">SaaS</option>
                                <option value="api">API</option>
                                <option value="service">Service</option>
                                <option value="worker">Worker</option>
                                <option value="bot">Bot</option>
                                <option value="mobile">Mobile app</option>
                                <option value="hybrid">Hybrid</option>
                                <option value="integration">Integration</option>
                                <option value="other">Other</option>
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Owner / team
                            <Input
                                value={ownerTeam}
                                onChange={(event) =>
                                    setOwnerTeam(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Primary language
                            <Input
                                value={primaryLanguage}
                                onChange={(event) =>
                                    setPrimaryLanguage(event.target.value)
                                }
                                placeholder="Python"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Framework
                            <Input
                                value={framework}
                                onChange={(event) =>
                                    setFramework(event.target.value)
                                }
                                placeholder="Django / FastAPI / Next.js"
                                disabled={isSaving}
                            />
                        </label>
                    </div>
                </Card>
            ) : null}

            {type === "application_environment" ? (
                <Card className="space-y-4 p-5">
                    <h2 className="text-sm font-semibold text-white">
                        Application environment
                    </h2>
                    <div className="grid gap-4 md:grid-cols-2">
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                            Application
                            <Select
                                value={applicationResourceId}
                                onChange={(event) =>
                                    setApplicationResourceId(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="">Choose application</option>
                                {applications.map((application) => (
                                    <option
                                        key={application.resource_id}
                                        value={application.resource_id}
                                    >
                                        {application.name}
                                    </option>
                                ))}
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Deployment type
                            <Select
                                value={deploymentType}
                                onChange={(event) =>
                                    setDeploymentType(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="server">Server</option>
                                <option value="paas">PaaS</option>
                                <option value="container">Container</option>
                                <option value="kubernetes">Kubernetes</option>
                                <option value="serverless">Serverless</option>
                                <option value="static">Static</option>
                                <option value="other">Other</option>
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Server
                            <Select
                                value={serverResourceId}
                                onChange={(event) =>
                                    setServerResourceId(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="">No server selected</option>
                                {servers.map((server) => (
                                    <option
                                        key={server.resource_id}
                                        value={server.resource_id}
                                    >
                                        {server.name} · {server.hostname}
                                    </option>
                                ))}
                            </Select>
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
                            Runtime
                            <Input
                                value={runtime}
                                onChange={(event) =>
                                    setRuntime(event.target.value)
                                }
                                placeholder="python / node"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Runtime version
                            <Input
                                value={runtimeVersion}
                                onChange={(event) =>
                                    setRuntimeVersion(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Release version
                            <Input
                                value={releaseVersion}
                                onChange={(event) =>
                                    setReleaseVersion(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Branch / ref
                            <Input
                                value={branchOrRef}
                                onChange={(event) =>
                                    setBranchOrRef(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                            Automatic deployments
                            <Select
                                value={automaticDeployments}
                                onChange={(event) =>
                                    setAutomaticDeployments(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="">Unknown</option>
                                <option value="true">Enabled</option>
                                <option value="false">Disabled</option>
                            </Select>
                        </label>
                    </div>
                </Card>
            ) : null}

            {type === "source_repository" ? (
                <Card className="space-y-4 p-5">
                    <h2 className="text-sm font-semibold text-white">
                        Source repository
                    </h2>
                    <div className="grid gap-4 md:grid-cols-2">
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
                            Owner / namespace
                            <Input
                                value={ownerName}
                                onChange={(event) =>
                                    setOwnerName(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Repository name
                            <Input
                                value={repositoryName}
                                onChange={(event) =>
                                    setRepositoryName(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                            Web URL
                            <Input
                                type="url"
                                value={webUrl}
                                onChange={(event) =>
                                    setWebUrl(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                            Clone URL
                            <Input
                                value={cloneUrl}
                                onChange={(event) =>
                                    setCloneUrl(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Provider repository ID
                            <Input
                                value={providerRepositoryId}
                                onChange={(event) =>
                                    setProviderRepositoryId(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Default branch
                            <Input
                                value={defaultBranch}
                                onChange={(event) =>
                                    setDefaultBranch(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Visibility
                            <Select
                                value={visibility}
                                onChange={(event) =>
                                    setVisibility(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="private">Private</option>
                                <option value="internal">Internal</option>
                                <option value="public">Public</option>
                            </Select>
                        </label>
                        <label className="flex items-center gap-3 pt-6 text-xs text-slate-400">
                            <input
                                type="checkbox"
                                checked={isFork}
                                onChange={(event) =>
                                    setIsFork(event.target.checked)
                                }
                                disabled={isSaving}
                                className="h-4 w-4 rounded border-slate-700 bg-slate-950"
                            />
                            Repository is a fork
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
                        : `${isEditing ? "Save" : "Create"} ${label(type).toLowerCase()}`}
                </Button>
            </div>
        </form>
    );
}
