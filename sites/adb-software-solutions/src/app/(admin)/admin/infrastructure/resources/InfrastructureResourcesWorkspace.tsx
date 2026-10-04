"use client";

import { RecordDrawer } from "@/components/admin/RecordDrawer";
import {
    Button,
    ButtonLink,
    Card,
    DataError,
    DataLoading,
    EmptyState,
    Input,
    PageHeader,
    Pagination,
    Select,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import { useCallback, useEffect, useMemo, useState } from "react";
import { InfrastructureResourceWorkspace } from "./[id]/InfrastructureResourceWorkspace";
import { InfrastructureCreateForm } from "./InfrastructureCreateForm";
import {
    RESOURCE_TYPES,
    canCreateResource,
    type CreatableResourceType,
} from "./resourceCreation";

interface ResourceSummary {
    id: number;
    name: string;
    resource_type: string;
    lifecycle_status: string;
    environment: string;
    criticality: string;
    ownership_type: string;
    client_id: number | null;
    client_name: string | null;
    tags: { id: number; name: string; slug: string; colour: string }[];
    updated_at: string;
    expires_on?: string | null;
    expires_at?: string | null;
    auto_renew?: boolean | null;
}

interface ResourcePage {
    items: ResourceSummary[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
}

const PAGE_SIZE = 25;

const LIFECYCLE = [
    "current",
    "all",
    "planned",
    "active",
    "maintenance",
    "deprecated",
    "retired",
    "archived",
] as const;

const ENVIRONMENTS = [
    "production",
    "staging",
    "development",
    "testing",
    "shared",
    "not_applicable",
] as const;

function label(value: string): string {
    const special: Record<string, string> = {
        all: "All",
        current: "Current",
        not_applicable: "Not applicable",
        database_instance: "Database instance",
        logical_database: "Logical database",
        application_environment: "Application environment",
        source_repository: "Source repository",
        website_endpoint: "Website endpoint",
        dns_zone: "DNS zone",
        tls_certificate: "TLS certificate",
        provider_account: "Provider account",
        backup_plan: "Backup plan",
        container_stack: "Container stack",
        kubernetes_cluster: "Kubernetes cluster",
        kubernetes_namespace: "Kubernetes namespace",
        kubernetes_workload: "Kubernetes workload",
        system_service: "System service",
        scheduled_job: "Scheduled job",
        mobile_app: "Mobile app",
        email_system: "Email system",
        network_device: "Network device",
    };
    return (
        special[value] ??
        `${value.charAt(0).toUpperCase()}${value.slice(1).replaceAll("_", " ")}`
    );
}

interface InfrastructureResourcesWorkspaceProps {
    resourceTypeFilter?: CreatableResourceType;
    title?: string;
    description?: string;
}

export function InfrastructureResourcesWorkspace({
    resourceTypeFilter,
    title = "Resources",
    description = "Technical resources across ADB Internal and Client infrastructure. Open a resource to manage its details, credentials and relationships.",
}: InfrastructureResourcesWorkspaceProps = {}) {
    const { hasPermission } = useAuth();
    const [data, setData] = useState<ResourcePage | null>(null);
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");
    const [ownership, setOwnership] = useState("all");
    const [lifecycle, setLifecycle] = useState("current");
    const [resourceType, setResourceType] = useState<string>(
        resourceTypeFilter ?? "all",
    );
    const [environment, setEnvironment] = useState("all");
    const [selectedResourceId, setSelectedResourceId] = useState<number | null>(
        null,
    );
    const [showCreate, setShowCreate] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const createTypes = RESOURCE_TYPES.filter(
        (type) =>
            (!resourceTypeFilter || resourceTypeFilter === type) &&
            canCreateResource(type, hasPermission),
    );

    const url = useMemo(() => {
        const params = new URLSearchParams({
            page: String(page),
            page_size: String(PAGE_SIZE),
            ownership,
            lifecycle,
        });
        if (search.trim()) params.set("search", search.trim());
        if (resourceTypeFilter) params.set("resource_type", resourceTypeFilter);
        else if (resourceType !== "all")
            params.set("resource_type", resourceType);
        if (environment !== "all") params.set("environment", environment);
        return `${API_URL}/api/admin/infrastructure/resources?${params.toString()}`;
    }, [
        environment,
        lifecycle,
        ownership,
        page,
        resourceType,
        resourceTypeFilter,
        search,
    ]);

    const load = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            setData((await fetchAPI(url)) as ResourcePage);
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load infrastructure resources.",
            );
        } finally {
            setIsLoading(false);
        }
    }, [url]);

    useEffect(() => {
        void load();
    }, [load]);

    useEffect(() => {
        setPage(1);
        setSelectedResourceId(null);
        setShowCreate(false);
    }, [resourceTypeFilter]);

    function resetPage() {
        setPage(1);
    }

    function openCreatedResource(resourceId: number) {
        setShowCreate(false);
        setSelectedResourceId(resourceId);
        void load();
    }

    if (isLoading && !data) {
        return <DataLoading label="Loading infrastructure..." />;
    }
    if (error || !data) {
        return (
            <DataError
                message={error || "Infrastructure is unavailable."}
                onRetry={() => void load()}
            />
        );
    }

    return (
        <div className="space-y-6">
            <PageHeader
                eyebrow="Technical operations"
                title={title}
                description={description}
                actions={
                    <>
                        {createTypes.length > 0 ? (
                            <Button
                                type="button"
                                onClick={() => {
                                    setSelectedResourceId(null);
                                    setShowCreate(true);
                                }}
                            >
                                Add resource
                            </Button>
                        ) : null}
                        <ButtonLink
                            href="/admin/infrastructure/provider-accounts"
                            variant="secondary"
                        >
                            Provider accounts
                        </ButtonLink>
                        {hasPermission(
                            "infrastructure.view_serviceprovider",
                        ) ? (
                            <ButtonLink
                                href="/admin/infrastructure/service-providers"
                                variant="secondary"
                            >
                                Service providers
                            </ButtonLink>
                        ) : null}
                        <ButtonLink
                            href="/admin/infrastructure"
                            variant="secondary"
                        >
                            Infrastructure overview
                        </ButtonLink>
                    </>
                }
            />

            <Card className="p-4">
                <div className="grid gap-3 lg:grid-cols-[minmax(14rem,2fr)_repeat(4,minmax(10rem,1fr))]">
                    <Input
                        aria-label="Search resources"
                        placeholder="Search name, description, client or tag..."
                        value={search}
                        onChange={(event) => {
                            setSearch(event.target.value);
                            resetPage();
                        }}
                    />
                    <Select
                        aria-label="Ownership"
                        value={ownership}
                        onChange={(event) => {
                            setOwnership(event.target.value);
                            resetPage();
                        }}
                    >
                        <option value="all">All ownership</option>
                        <option value="internal">ADB Internal</option>
                        <option value="client">Client-owned</option>
                    </Select>
                    <Select
                        aria-label="Lifecycle"
                        value={lifecycle}
                        onChange={(event) => {
                            setLifecycle(event.target.value);
                            resetPage();
                        }}
                    >
                        {LIFECYCLE.map((value) => (
                            <option key={value} value={value}>
                                {label(value)} lifecycle
                            </option>
                        ))}
                    </Select>
                    <Select
                        aria-label="Resource type"
                        disabled={Boolean(resourceTypeFilter)}
                        value={resourceTypeFilter ?? resourceType}
                        onChange={(event) => {
                            setResourceType(event.target.value);
                            resetPage();
                        }}
                    >
                        <option value="all">All resource types</option>
                        {RESOURCE_TYPES.map((value) => (
                            <option key={value} value={value}>
                                {label(value)}
                            </option>
                        ))}
                    </Select>
                    <Select
                        aria-label="Environment"
                        value={environment}
                        onChange={(event) => {
                            setEnvironment(event.target.value);
                            resetPage();
                        }}
                    >
                        <option value="all">All environments</option>
                        {ENVIRONMENTS.map((value) => (
                            <option key={value} value={value}>
                                {label(value)}
                            </option>
                        ))}
                    </Select>
                </div>
            </Card>

            <Card className="overflow-hidden">
                <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
                    <div>
                        <h2 className="text-sm font-semibold text-white">
                            Resource register
                        </h2>
                        <p className="mt-0.5 text-xs text-slate-500">
                            {data.total.toLocaleString("en-GB")} resources match
                            this view.
                        </p>
                    </div>
                    {isLoading ? (
                        <span className="text-xs text-slate-600">
                            Refreshing…
                        </span>
                    ) : null}
                </div>

                {data.items.length === 0 ? (
                    <div className="p-5">
                        <EmptyState
                            title="No resources match this view"
                            description="Try changing the filters or add a resource using the available actions."
                        />
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-slate-800 text-sm">
                            <thead className="bg-slate-950/60 text-left text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
                                <tr>
                                    <th className="px-4 py-3">Resource</th>
                                    <th className="px-4 py-3">Type</th>
                                    <th className="px-4 py-3">Owner</th>
                                    <th className="px-4 py-3">Environment</th>
                                    <th className="px-4 py-3">Lifecycle</th>
                                    <th className="px-4 py-3">Criticality</th>
                                    {resourceTypeFilter === "domain" ||
                                    resourceTypeFilter === "tls_certificate" ? (
                                        <>
                                            <th className="px-4 py-3">
                                                Expires
                                            </th>
                                            <th className="px-4 py-3">
                                                Auto renew
                                            </th>
                                        </>
                                    ) : null}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/80">
                                {data.items.map((resource) => (
                                    <tr
                                        key={resource.id}
                                        className="bg-slate-900/20 hover:bg-slate-900/55"
                                    >
                                        <td className="px-4 py-3">
                                            <button
                                                type="button"
                                                onClick={() =>
                                                    setSelectedResourceId(
                                                        resource.id,
                                                    )
                                                }
                                                className="hover:text-adb-cyan-300 text-left font-medium text-slate-100"
                                            >
                                                {resource.name}
                                            </button>
                                            {resource.tags.length > 0 ? (
                                                <div className="mt-1 flex flex-wrap gap-1">
                                                    {resource.tags.map(
                                                        (tag) => (
                                                            <span
                                                                key={tag.id}
                                                                className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] text-slate-400"
                                                            >
                                                                {tag.name}
                                                            </span>
                                                        ),
                                                    )}
                                                </div>
                                            ) : null}
                                        </td>
                                        <td className="px-4 py-3 text-slate-400">
                                            {label(resource.resource_type)}
                                        </td>
                                        <td className="px-4 py-3 text-slate-400">
                                            {resource.client_name ||
                                                "ADB Internal"}
                                        </td>
                                        <td className="px-4 py-3 text-slate-400">
                                            {label(resource.environment)}
                                        </td>
                                        <td className="px-4 py-3 text-slate-400">
                                            {label(resource.lifecycle_status)}
                                        </td>
                                        <td className="px-4 py-3">
                                            <span
                                                className={
                                                    resource.criticality ===
                                                    "critical"
                                                        ? "text-red-300"
                                                        : resource.criticality ===
                                                            "high"
                                                          ? "text-amber-300"
                                                          : "text-slate-400"
                                                }
                                            >
                                                {label(resource.criticality)}
                                            </span>
                                        </td>
                                        {resourceTypeFilter === "domain" ||
                                        resourceTypeFilter ===
                                            "tls_certificate" ? (
                                            <>
                                                <td className="px-4 py-3 text-slate-400">
                                                    {resource.expires_on ||
                                                    resource.expires_at
                                                        ? new Intl.DateTimeFormat(
                                                              "en-GB",
                                                              {
                                                                  dateStyle:
                                                                      "medium",
                                                              },
                                                          ).format(
                                                              new Date(
                                                                  resource.expires_on ||
                                                                      resource.expires_at!,
                                                              ),
                                                          )
                                                        : "Unknown"}
                                                </td>
                                                <td className="px-4 py-3 text-slate-400">
                                                    {resource.auto_renew == null
                                                        ? "Unknown"
                                                        : resource.auto_renew
                                                          ? "Yes"
                                                          : "No"}
                                                </td>
                                            </>
                                        ) : null}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                <Pagination
                    page={data.page}
                    pageSize={data.page_size}
                    totalItems={data.total}
                    onPageChange={setPage}
                    disabled={isLoading}
                />
            </Card>

            {showCreate ? (
                <RecordDrawer onClose={() => setShowCreate(false)}>
                    <InfrastructureCreateForm
                        allowedTypes={createTypes}
                        initialType={
                            resourceTypeFilter ??
                            RESOURCE_TYPES.find((type) => type === resourceType)
                        }
                        onCancel={() => setShowCreate(false)}
                        onCreated={openCreatedResource}
                    />
                </RecordDrawer>
            ) : null}

            {selectedResourceId !== null ? (
                <RecordDrawer
                    onClose={() => {
                        setSelectedResourceId(null);
                        void load();
                    }}
                    fullPageHref={`/admin/infrastructure/resources/${selectedResourceId}`}
                >
                    <InfrastructureResourceWorkspace
                        resourceId={selectedResourceId}
                        presentation="drawer"
                    />
                </RecordDrawer>
            ) : null}
        </div>
    );
}
