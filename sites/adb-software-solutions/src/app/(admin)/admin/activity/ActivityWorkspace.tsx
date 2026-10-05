"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";

import {
    Button,
    Card,
    DataError,
    DataLoading,
    EmptyState,
} from "@/components/ui";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import { useCallback, useEffect, useMemo, useState } from "react";

interface ActivityItem {
    id: number;
    action: string;
    actor_name: string;
    target_type: string;
    target_id: string;
    target_label: string;
    client_id: number | null;
    resource_id: number | null;
    metadata: Record<string, unknown>;
    ip_address: string | null;
    user_agent: string;
    occurred_at: string;
}

interface ActivityResponse {
    items: ActivityItem[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    metadata_visible: boolean;
}

interface ClientOption {
    id: number;
    name: string;
    company: string;
}

interface ResourceOption {
    id: number;
    name: string;
    client_id: number | null;
    client_name: string | null;
    resource_type: string;
}

interface ResourcePage {
    items: ResourceOption[];
}

function labelAction(action: string) {
    return action.replaceAll(".", " · ").replaceAll("_", " ");
}

export function ActivityWorkspace() {
    const [data, setData] = useState<ActivityResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [page, setPage] = useState(1);
    const [clientId, setClientId] = useState<number | null>(null);
    const [resourceId, setResourceId] = useState<number | null>(null);
    const [clients, setClients] = useState<ClientOption[]>([]);
    const [resources, setResources] = useState<ResourceOption[]>([]);

    useEffect(() => {
        async function loadContextOptions() {
            const [clientResult, resourceResult] = await Promise.allSettled([
                fetchAPI(`${API_URL}/api/admin/clients`) as Promise<
                    ClientOption[]
                >,
                fetchAPI(
                    `${API_URL}/api/admin/infrastructure/resources?page_size=100&lifecycle=current`,
                ) as Promise<ResourcePage>,
            ]);
            if (clientResult.status === "fulfilled")
                setClients(clientResult.value);
            if (resourceResult.status === "fulfilled")
                setResources(resourceResult.value.items);
        }
        void loadContextOptions();
    }, []);

    const visibleResources = useMemo(
        () =>
            resources.filter(
                (resource) =>
                    clientId === null || resource.client_id === clientId,
            ),
        [clientId, resources],
    );

    const load = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const query = new URLSearchParams({
                page: String(page),
                page_size: "50",
            });
            if (clientId !== null) query.set("client_id", String(clientId));
            if (resourceId !== null)
                query.set("resource_id", String(resourceId));
            setData(
                (await fetchAPI(
                    `${API_URL}/api/admin/activity?${query.toString()}`,
                )) as ActivityResponse,
            );
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load activity.",
            );
        } finally {
            setLoading(false);
        }
    }, [clientId, page, resourceId]);

    useLiveRefresh(["activity"], load);

    useEffect(() => {
        void load();
    }, [load]);

    async function acknowledge(eventId: number) {
        await fetchAPI(
            `${API_URL}/api/admin/audit-events/${eventId}/acknowledge`,
            {
                method: "POST",
            },
        );
        await load();
    }

    function changeClient(value: string) {
        setClientId(value ? Number(value) : null);
        setResourceId(null);
        setPage(1);
    }

    if (loading && !data)
        return <DataLoading label="Loading operational activity..." />;
    if (error && !data)
        return <DataError message={error} onRetry={() => void load()} />;

    return (
        <div className="space-y-5">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
                <div>
                    <p className="text-adb-cyan-400 text-xs font-semibold tracking-[0.18em] uppercase">
                        Stage 9 · Audit & security
                    </p>
                    <h1 className="mt-2 text-2xl font-semibold text-white">
                        Operational activity
                    </h1>
                    <p className="mt-1 max-w-3xl text-sm text-slate-400">
                        Append-only platform, Client and resource history
                        filtered through your current object access. Sensitive
                        request metadata is shown only when your role explicitly
                        permits it.
                    </p>
                </div>
                <Button variant="outline" onClick={() => void load()}>
                    Refresh
                </Button>
            </div>

            <Card className="p-4">
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-[1fr_1fr_auto] xl:items-end">
                    <label className="space-y-1 text-xs text-slate-500">
                        <span>Client context</span>
                        <select
                            value={clientId ?? ""}
                            onChange={(event) =>
                                changeClient(event.target.value)
                            }
                            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                        >
                            <option value="">Platform-wide</option>
                            {clients.map((client) => (
                                <option key={client.id} value={client.id}>
                                    {client.company || client.name}
                                </option>
                            ))}
                        </select>
                    </label>
                    <label className="space-y-1 text-xs text-slate-500">
                        <span>Resource context</span>
                        <select
                            value={resourceId ?? ""}
                            onChange={(event) => {
                                setResourceId(
                                    event.target.value
                                        ? Number(event.target.value)
                                        : null,
                                );
                                setPage(1);
                            }}
                            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                        >
                            <option value="">All visible resources</option>
                            {visibleResources.map((resource) => (
                                <option key={resource.id} value={resource.id}>
                                    {resource.name} ·{" "}
                                    {resource.resource_type.replaceAll(
                                        "_",
                                        " ",
                                    )}
                                </option>
                            ))}
                        </select>
                    </label>
                    {clientId !== null || resourceId !== null ? (
                        <Button
                            variant="ghost"
                            onClick={() => {
                                setClientId(null);
                                setResourceId(null);
                                setPage(1);
                            }}
                        >
                            Clear context
                        </Button>
                    ) : null}
                </div>
            </Card>

            {error ? (
                <div className="rounded-lg border border-red-900/70 bg-red-950/40 px-4 py-3 text-sm text-red-200">
                    {error}
                </div>
            ) : null}

            <Card>
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
                    <div>
                        <h2 className="font-semibold text-slate-100">
                            {resourceId !== null
                                ? "Resource activity"
                                : clientId !== null
                                  ? "Client activity"
                                  : "Audit trail"}
                        </h2>
                        <p className="text-xs text-slate-500">
                            {data?.total ?? 0} visible events
                        </p>
                    </div>
                    <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400">
                        {data?.metadata_visible
                            ? "Sensitive metadata permitted"
                            : "Sensitive metadata hidden"}
                    </span>
                </div>

                <div className="divide-y divide-slate-800">
                    {data?.items.map((item) => (
                        <div
                            key={item.id}
                            className="grid gap-3 px-5 py-4 lg:grid-cols-[1fr_auto]"
                        >
                            <div className="min-w-0">
                                <div className="flex flex-wrap items-center gap-2">
                                    <span className="text-adb-cyan-200 rounded-md bg-slate-800 px-2 py-1 text-[11px] font-semibold">
                                        {labelAction(item.action)}
                                    </span>
                                    <span className="text-xs text-slate-500">
                                        {new Intl.DateTimeFormat("en-GB", {
                                            dateStyle: "medium",
                                            timeStyle: "short",
                                        }).format(new Date(item.occurred_at))}
                                    </span>
                                </div>
                                <p className="mt-2 text-sm text-slate-200">
                                    <span className="font-medium">
                                        {item.actor_name || "System"}
                                    </span>
                                    {item.target_label
                                        ? ` · ${item.target_label}`
                                        : ""}
                                </p>
                                <p className="mt-1 text-xs text-slate-500">
                                    {item.target_type || "platform"}
                                    {item.target_id
                                        ? ` #${item.target_id}`
                                        : ""}
                                    {item.client_id
                                        ? ` · Client ${item.client_id}`
                                        : ""}
                                    {item.resource_id
                                        ? ` · Resource ${item.resource_id}`
                                        : ""}
                                </p>
                                {data?.metadata_visible &&
                                Object.keys(item.metadata).length > 0 ? (
                                    <pre className="mt-3 overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-3 text-[11px] text-slate-400">
                                        {JSON.stringify(item.metadata, null, 2)}
                                    </pre>
                                ) : null}
                                {data?.metadata_visible &&
                                (item.ip_address || item.user_agent) ? (
                                    <p className="mt-2 text-[11px] break-all text-slate-600">
                                        {item.ip_address || "No IP"} ·{" "}
                                        {item.user_agent || "No user agent"}
                                    </p>
                                ) : null}
                            </div>
                            {!item.action.startsWith("audit.acknowledged") ? (
                                <Button
                                    variant="ghost"
                                    onClick={() => void acknowledge(item.id)}
                                >
                                    Acknowledge
                                </Button>
                            ) : null}
                        </div>
                    ))}
                </div>
            </Card>

            {!loading && data?.items.length === 0 ? (
                <EmptyState
                    title="No activity in scope"
                    description="Operational and security events will appear here as scoped actions are recorded."
                />
            ) : null}

            {(data?.total_pages ?? 0) > 1 ? (
                <div className="flex items-center justify-end gap-3 text-sm text-slate-400">
                    <Button
                        variant="outline"
                        disabled={page <= 1}
                        onClick={() => setPage((value) => value - 1)}
                    >
                        Previous
                    </Button>
                    <span>
                        Page {page} of {data?.total_pages ?? 1}
                    </span>
                    <Button
                        variant="outline"
                        disabled={page >= (data?.total_pages ?? 1)}
                        onClick={() => setPage((value) => value + 1)}
                    >
                        Next
                    </Button>
                </div>
            ) : null}
        </div>
    );
}
