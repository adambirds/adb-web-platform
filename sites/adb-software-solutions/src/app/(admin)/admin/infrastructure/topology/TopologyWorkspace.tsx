"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";

import {
    Badge,
    Button,
    Card,
    DataError,
    DataLoading,
    EmptyState,
    Input,
} from "@/components/ui";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

interface ResourceOption {
    id: number;
    name: string;
    resource_type: string;
    client_name: string | null;
    environment: string;
}

interface ResourcePage {
    items: ResourceOption[];
}

interface TopologyNode {
    id: number;
    name: string;
    resource_type: string;
    resource_type_label: string;
    lifecycle_status: string;
    environment: string;
    criticality: string;
    client_id: number | null;
    client_name: string | null;
    href: string;
    is_root: boolean;
}

interface TopologyEdge {
    id: number;
    source_id: number;
    target_id: number;
    relationship_type: string;
    relationship_label: string;
    label: string;
}

interface TopologyResponse {
    root_id: number;
    depth: number;
    nodes: TopologyNode[];
    edges: TopologyEdge[];
    truncated: boolean;
}

export function TopologyWorkspace() {
    const [resourceSearch, setResourceSearch] = useState("");
    const [resources, setResources] = useState<ResourceOption[]>([]);
    const [resourceId, setResourceId] = useState<number | null>(null);
    const [depth, setDepth] = useState(1);
    const [data, setData] = useState<TopologyResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let active = true;
        async function loadResources() {
            try {
                const response = (await fetchAPI(
                    `${API_URL}/api/admin/infrastructure/resources?page_size=100&lifecycle=current&search=${encodeURIComponent(resourceSearch)}`,
                )) as ResourcePage;
                if (!active) return;
                setResources(response.items);
                setResourceId((current) =>
                    response.items.some((resource) => resource.id === current)
                        ? current
                        : (response.items[0]?.id ?? null),
                );
            } catch (loadError) {
                if (!active) return;
                setError(
                    loadError instanceof Error
                        ? loadError.message
                        : "Unable to load resources.",
                );
                setLoading(false);
            }
        }
        void loadResources();
        return () => {
            active = false;
        };
    }, [resourceSearch]);

    const loadTopology = useCallback(async () => {
        if (!resourceId) {
            setData(null);
            setLoading(false);
            return;
        }
        try {
            setLoading(true);
            setError(null);
            setData(
                (await fetchAPI(
                    `${API_URL}/api/admin/infrastructure/resources/${resourceId}/topology?depth=${depth}`,
                )) as TopologyResponse,
            );
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load topology.",
            );
        } finally {
            setLoading(false);
        }
    }, [depth, resourceId]);

    useEffect(() => {
        void loadTopology();
    }, [loadTopology]);
    useLiveRefresh(["infrastructure", "credentials", "monitoring"], loadTopology);

    const nodesById = useMemo(
        () => new Map((data?.nodes ?? []).map((node) => [node.id, node])),
        [data],
    );
    const root = data?.nodes.find((node) => node.is_root) ?? null;

    if (loading && resources.length === 0)
        return <DataLoading label="Loading infrastructure topology..." />;
    if (error && resources.length === 0)
        return (
            <DataError
                message={error}
                onRetry={() => window.location.reload()}
            />
        );

    return (
        <div className="space-y-5">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
                <div>
                    <p className="text-adb-cyan-400 text-xs font-semibold tracking-[0.18em] uppercase">
                        Infrastructure · Relationships
                    </p>
                    <h1 className="mt-2 text-2xl font-semibold text-white">
                        Resource topology
                    </h1>
                    <p className="mt-1 max-w-3xl text-sm text-slate-400">
                        Explore typed resource relationships without crossing
                        your current Client or infrastructure scope. The view is
                        intentionally bounded to two hops.
                    </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                    <Input
                        aria-label="Search topology resources"
                        placeholder="Find a resource..."
                        value={resourceSearch}
                        onChange={(event) =>
                            setResourceSearch(event.target.value)
                        }
                    />
                    <select
                        value={resourceId ?? ""}
                        onChange={(event) =>
                            setResourceId(Number(event.target.value))
                        }
                        className="min-w-72 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                    >
                        {resources.map((resource) => (
                            <option key={resource.id} value={resource.id}>
                                {resource.name} ·{" "}
                                {resource.client_name || "Internal"}
                            </option>
                        ))}
                    </select>
                    {[1, 2].map((value) => (
                        <button
                            key={value}
                            type="button"
                            onClick={() => setDepth(value)}
                            className={`rounded-lg border px-3 py-2 text-sm ${
                                depth === value
                                    ? "border-adb-cyan-700 bg-adb-cyan-950/30 text-adb-cyan-200"
                                    : "border-slate-700 text-slate-400"
                            }`}
                        >
                            {value} hop{value === 1 ? "" : "s"}
                        </button>
                    ))}
                    <Button
                        variant="outline"
                        onClick={() => void loadTopology()}
                    >
                        Refresh
                    </Button>
                </div>
            </div>

            {error ? (
                <div className="rounded-lg border border-red-900/70 bg-red-950/40 px-4 py-3 text-sm text-red-200">
                    {error}
                </div>
            ) : null}

            {root ? (
                <Card className="p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                            <p className="text-adb-cyan-400 text-xs font-semibold tracking-wide uppercase">
                                Root resource
                            </p>
                            <Link
                                href={root.href}
                                className="hover:text-adb-cyan-300 mt-2 block text-xl font-semibold text-white"
                            >
                                {root.name}
                            </Link>
                            <p className="mt-1 text-sm text-slate-500">
                                {root.resource_type_label} ·{" "}
                                {root.environment.replaceAll("_", " ")} ·{" "}
                                {root.client_name || "ADB Internal"}
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Badge>{root.lifecycle_status}</Badge>
                            <Badge>{root.criticality}</Badge>
                        </div>
                    </div>
                </Card>
            ) : null}

            <div className="grid gap-4 xl:grid-cols-2">
                {data?.edges.map((edge) => {
                    const source = nodesById.get(edge.source_id);
                    const target = nodesById.get(edge.target_id);
                    if (!source || !target) return null;
                    return (
                        <Card key={edge.id} className="p-4">
                            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
                                <Link
                                    href={source.href}
                                    className="min-w-0 rounded-lg border border-slate-800 bg-slate-950 p-3 hover:border-slate-700"
                                >
                                    <p className="truncate text-sm font-semibold text-slate-200">
                                        {source.name}
                                    </p>
                                    <p className="mt-1 truncate text-xs text-slate-600">
                                        {source.resource_type_label}
                                    </p>
                                </Link>
                                <div className="text-center">
                                    <p className="text-adb-cyan-400 text-lg">
                                        →
                                    </p>
                                    <p className="max-w-28 text-[10px] font-semibold tracking-wide text-slate-500 uppercase">
                                        {edge.label || edge.relationship_label}
                                    </p>
                                </div>
                                <Link
                                    href={target.href}
                                    className="min-w-0 rounded-lg border border-slate-800 bg-slate-950 p-3 hover:border-slate-700"
                                >
                                    <p className="truncate text-sm font-semibold text-slate-200">
                                        {target.name}
                                    </p>
                                    <p className="mt-1 truncate text-xs text-slate-600">
                                        {target.resource_type_label}
                                    </p>
                                </Link>
                            </div>
                        </Card>
                    );
                })}
            </div>

            {!loading && data?.edges.length === 0 ? (
                <EmptyState
                    title="No visible relationships"
                    description="Add typed Infrastructure relationships or choose another resource to explore its topology."
                />
            ) : null}

            {data?.truncated ? (
                <div className="rounded-lg border border-amber-900/60 bg-amber-950/20 px-4 py-3 text-sm text-amber-200">
                    This topology reached the bounded node or edge limit. Open a
                    neighbouring resource to continue exploring.
                </div>
            ) : null}
        </div>
    );
}
