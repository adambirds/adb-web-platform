"use client";

import { RecordDrawer } from "@/components/admin/RecordDrawer";
import {
    Button,
    ButtonLink,
    Card,
    DataError,
    DataLoading,
    EmptyState,
    Pagination,
    Select,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
    OperationalInfrastructureForm,
    OperationalType,
} from "../resources/OperationalInfrastructureForm";

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
    updated_at: string;
}

interface ResourcePage {
    items: ResourceSummary[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
}

const OPERATIONAL_TYPES: OperationalType[] = [
    "storage",
    "backup_plan",
    "container_stack",
    "kubernetes_cluster",
    "kubernetes_namespace",
    "kubernetes_workload",
    "system_service",
    "scheduled_job",
];

const ADD_PERMISSIONS: Record<OperationalType, string> = {
    storage: "infrastructure.add_storageprofile",
    backup_plan: "infrastructure.add_backupplanprofile",
    container_stack: "infrastructure.add_containerstackprofile",
    kubernetes_cluster: "infrastructure.add_kubernetesclusterprofile",
    kubernetes_namespace: "infrastructure.add_kubernetesnamespaceprofile",
    kubernetes_workload: "infrastructure.add_kubernetesworkloadprofile",
    system_service: "infrastructure.add_systemserviceprofile",
    scheduled_job: "infrastructure.add_scheduledjobprofile",
};

const CHANGE_PERMISSIONS: Record<OperationalType, string> = {
    storage: "infrastructure.change_storageprofile",
    backup_plan: "infrastructure.change_backupplanprofile",
    container_stack: "infrastructure.change_containerstackprofile",
    kubernetes_cluster: "infrastructure.change_kubernetesclusterprofile",
    kubernetes_namespace: "infrastructure.change_kubernetesnamespaceprofile",
    kubernetes_workload: "infrastructure.change_kubernetesworkloadprofile",
    system_service: "infrastructure.change_systemserviceprofile",
    scheduled_job: "infrastructure.change_scheduledjobprofile",
};

function label(value: string): string {
    return value
        .replaceAll("_", " ")
        .replace(/^./, (character) => character.toUpperCase());
}

export function SpecialistOperationsWorkspace() {
    const { hasPermission } = useAuth();
    const [page, setPage] = useState(1);
    const [type, setType] = useState<OperationalType>("container_stack");
    const [data, setData] = useState<ResourcePage | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreate, setShowCreate] = useState(false);
    const [editResourceId, setEditResourceId] = useState<number | null>(null);

    const allowedTypes = useMemo(
        () =>
            OPERATIONAL_TYPES.filter(
                (item) =>
                    hasPermission(
                        "infrastructure.add_infrastructureresource",
                    ) && hasPermission(ADD_PERMISSIONS[item]),
            ),
        [hasPermission],
    );

    const load = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const params = new URLSearchParams({
                resource_type: type,
                lifecycle: "current",
                ownership: "all",
                page: String(page),
                page_size: "25",
            });
            setData(
                (await fetchAPI(
                    `${API_URL}/api/admin/infrastructure/resources?${params.toString()}`,
                )) as ResourcePage,
            );
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load specialist operations.",
            );
        } finally {
            setIsLoading(false);
        }
    }, [page, type]);

    useEffect(() => {
        void load();
    }, [load]);

    function closeAndReload() {
        setShowCreate(false);
        setEditResourceId(null);
        void load();
    }

    return (
        <div className="space-y-5">
            <Card className="p-4">
                <div className="flex flex-wrap items-end justify-between gap-4">
                    <label className="min-w-64 text-sm text-slate-300">
                        Operational resource type
                        <Select
                            className="mt-1.5"
                            value={type}
                            onChange={(event) => {
                                setType(event.target.value as OperationalType);
                                setPage(1);
                            }}
                        >
                            {OPERATIONAL_TYPES.map((item) => (
                                <option key={item} value={item}>
                                    {label(item)}
                                </option>
                            ))}
                        </Select>
                    </label>
                    <div className="flex flex-wrap gap-2">
                        {allowedTypes.length > 0 ? (
                            <Button
                                type="button"
                                onClick={() => {
                                    setEditResourceId(null);
                                    setShowCreate(true);
                                }}
                            >
                                Add operational resource
                            </Button>
                        ) : null}
                        <ButtonLink
                            href="/admin/infrastructure/resources"
                            variant="secondary"
                        >
                            All structured resources
                        </ButtonLink>
                    </div>
                </div>
            </Card>

            {error ? (
                <DataError message={error} onRetry={() => void load()} />
            ) : null}
            {isLoading && !data ? (
                <DataLoading label="Loading operational resources…" />
            ) : null}

            {!isLoading && data?.items.length === 0 ? (
                <EmptyState
                    title={`No ${label(type).toLowerCase()} resources yet`}
                    description="Create a structured operational resource or choose another type."
                />
            ) : null}

            <div className="grid gap-3 xl:grid-cols-2">
                {data?.items.map((resource) => {
                    const resourceType =
                        resource.resource_type as OperationalType;
                    const canEdit =
                        hasPermission(
                            "infrastructure.change_infrastructureresource",
                        ) && hasPermission(CHANGE_PERMISSIONS[resourceType]);
                    return (
                        <Card key={resource.id} className="p-5">
                            <div className="flex items-start justify-between gap-4">
                                <div className="min-w-0">
                                    <p className="text-adb-cyan-300 text-xs font-medium tracking-wide uppercase">
                                        {label(resource.resource_type)}
                                    </p>
                                    <h2 className="mt-1 truncate font-semibold text-slate-100">
                                        {resource.name}
                                    </h2>
                                    <p className="mt-2 text-sm text-slate-500">
                                        {resource.client_name ?? "ADB Internal"}{" "}
                                        · {label(resource.environment)} ·{" "}
                                        {label(resource.lifecycle_status)}
                                    </p>
                                </div>
                                <div className="flex shrink-0 flex-wrap gap-2">
                                    <ButtonLink
                                        size="sm"
                                        variant="secondary"
                                        href={`/admin/infrastructure/resources/${resource.id}`}
                                    >
                                        Open
                                    </ButtonLink>
                                    {canEdit ? (
                                        <Button
                                            size="sm"
                                            type="button"
                                            onClick={() =>
                                                setEditResourceId(resource.id)
                                            }
                                        >
                                            Edit
                                        </Button>
                                    ) : null}
                                </div>
                            </div>
                        </Card>
                    );
                })}
            </div>

            {data ? (
                <Pagination
                    page={data.page}
                    pageSize={data.page_size}
                    totalItems={data.total}
                    onPageChange={setPage}
                    disabled={isLoading}
                />
            ) : null}

            {showCreate ? (
                <RecordDrawer onClose={() => setShowCreate(false)}>
                    <OperationalInfrastructureForm
                        allowedTypes={allowedTypes}
                        onCancel={() => setShowCreate(false)}
                        onCreated={closeAndReload}
                    />
                </RecordDrawer>
            ) : null}

            {editResourceId !== null ? (
                <RecordDrawer
                    onClose={() => setEditResourceId(null)}
                    fullPageHref={`/admin/infrastructure/resources/${editResourceId}`}
                >
                    <OperationalInfrastructureForm
                        allowedTypes={OPERATIONAL_TYPES}
                        editResourceId={editResourceId}
                        onCancel={() => setEditResourceId(null)}
                        onSaved={closeAndReload}
                    />
                </RecordDrawer>
            ) : null}
        </div>
    );
}
