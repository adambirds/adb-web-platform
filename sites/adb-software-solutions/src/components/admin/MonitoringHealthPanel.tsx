"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";

import {
    Badge,
    ButtonLink,
    Card,
    DataError,
    DataLoading,
    EmptyState,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { useCallback, useEffect, useMemo, useState } from "react";

interface MonitorCheck {
    id: number;
    name: string;
    check_type: string;
    status: string;
    target: string;
    port: number | null;
    last_checked_at: string | null;
}

interface MonitorIncident {
    id: number;
    check_id: number;
    check_name: string;
    status: string;
    severity: string;
    opened_at: string;
    summary: string;
}

interface MonitoringOverview {
    total_checks: number;
    healthy_checks: number;
    degraded_checks: number;
    failing_checks: number;
    pending_checks: number;
    open_incidents: number;
    checks: MonitorCheck[];
    incidents: MonitorIncident[];
}

interface MonitoringHealthPanelProps {
    clientId?: number;
    resourceId?: number;
    title?: string;
    description?: string;
}

const statusClasses: Record<string, string> = {
    healthy: "border-emerald-800 bg-emerald-950/60 text-emerald-300",
    degraded: "border-yellow-800 bg-yellow-950/60 text-yellow-300",
    failing: "border-red-800 bg-red-950/60 text-red-300",
    pending: "border-slate-700 bg-slate-800/70 text-slate-300",
    paused: "border-slate-700 bg-slate-900 text-slate-400",
    open: "border-red-800 bg-red-950/60 text-red-300",
    acknowledged: "border-yellow-800 bg-yellow-950/60 text-yellow-300",
};

function formatDate(value: string | null): string {
    if (!value) return "Not run yet";
    return new Intl.DateTimeFormat("en-GB", {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(new Date(value));
}

export function MonitoringHealthPanel({
    clientId,
    resourceId,
    title = "Technical health",
    description = "Current monitoring state for this operational context.",
}: MonitoringHealthPanelProps) {
    const { hasPermission } = useAuth();
    const canView =
        hasPermission("monitoring.view_monitorcheck") &&
        hasPermission("monitoring.view_monitorincident");
    const [overview, setOverview] = useState<MonitoringOverview | null>(null);
    const [isLoading, setIsLoading] = useState(canView);
    const [error, setError] = useState<string | null>(null);

    const endpoint = useMemo(() => {
        const url = new URL(AdminAPI.monitoring.overview());
        if (clientId !== undefined) {
            url.searchParams.set("client_id", String(clientId));
        }
        if (resourceId !== undefined) {
            url.searchParams.set("resource_id", String(resourceId));
        }
        return url.toString();
    }, [clientId, resourceId]);

    const load = useCallback(async () => {
        if (!canView) return;
        try {
            setIsLoading(true);
            setError(null);
            setOverview((await fetchAPI(endpoint)) as MonitoringOverview);
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Technical health is unavailable.",
            );
        } finally {
            setIsLoading(false);
        }
    }, [canView, endpoint]);

    useLiveRefresh(["monitoring"], load);

    useEffect(() => {
        void load();
    }, [load]);

    if (!canView) return null;

    if (isLoading && !overview) {
        return (
            <Card className="p-5">
                <DataLoading label="Loading technical health..." />
            </Card>
        );
    }
    if (error && !overview) {
        return (
            <Card className="p-5">
                <DataError message={error} onRetry={() => void load()} />
            </Card>
        );
    }
    if (!overview) return null;

    return (
        <Card className="overflow-hidden">
            <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-800 px-5 py-4">
                <div>
                    <h2 className="text-sm font-semibold text-white">{title}</h2>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{description}</p>
                </div>
                <ButtonLink href="/admin/monitoring" size="sm" variant="ghost">
                    Open monitoring
                </ButtonLink>
            </div>

            <div className="grid grid-cols-2 gap-px bg-slate-800 sm:grid-cols-4">
                {[
                    {
                        label: "Healthy",
                        value: overview.healthy_checks,
                        valueClass: "text-emerald-300",
                    },
                    {
                        label: "Degraded",
                        value: overview.degraded_checks,
                        valueClass: "text-yellow-300",
                    },
                    {
                        label: "Failing",
                        value: overview.failing_checks,
                        valueClass: "text-red-300",
                    },
                    {
                        label: "Incidents",
                        value: overview.open_incidents,
                        valueClass: "text-slate-200",
                    },
                ].map((metric) => (
                    <div key={metric.label} className="bg-slate-950 px-4 py-3">
                        <div className="text-[11px] font-medium tracking-wide text-slate-600 uppercase">
                            {metric.label}
                        </div>
                        <div
                            className={`mt-1 text-xl font-semibold ${metric.valueClass}`}
                        >
                            {metric.value}
                        </div>
                    </div>
                ))}
            </div>

            {overview.checks.length === 0 ? (
                <div className="p-5">
                    <EmptyState
                        title="No monitoring checks"
                        description="No enabled checks are attached to this operational context yet."
                    />
                </div>
            ) : (
                <div className="divide-y divide-slate-800">
                    {overview.checks.slice(0, 5).map((check) => (
                        <div
                            key={check.id}
                            className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
                        >
                            <div className="min-w-0">
                                <div className="flex flex-wrap items-center gap-2">
                                    <p className="truncate text-sm font-medium text-slate-100">
                                        {check.name}
                                    </p>
                                    <Badge className={statusClasses[check.status]}>
                                        {check.status}
                                    </Badge>
                                </div>
                                <p className="mt-1 truncate text-xs text-slate-500">
                                    {check.target}
                                    {check.port ? `:${check.port}` : ""} · {check.check_type}
                                </p>
                                <p className="mt-1 text-xs text-slate-600">
                                    {formatDate(check.last_checked_at)}
                                </p>
                            </div>
                            <ButtonLink
                                href={`/admin/monitoring/checks/${check.id}`}
                                size="sm"
                                variant="outline"
                            >
                                View
                            </ButtonLink>
                        </div>
                    ))}
                </div>
            )}

            {overview.incidents.length > 0 ? (
                <div className="border-t border-slate-800 bg-red-950/10 px-5 py-4">
                    <p className="text-xs font-semibold tracking-wide text-red-300 uppercase">
                        Active incidents
                    </p>
                    <div className="mt-3 space-y-3">
                        {overview.incidents.slice(0, 3).map((incident) => (
                            <div
                                key={incident.id}
                                className="flex items-start justify-between gap-3"
                            >
                                <div className="min-w-0">
                                    <p className="text-sm font-medium text-slate-200">
                                        {incident.check_name}
                                    </p>
                                    <p className="mt-1 text-xs leading-5 text-slate-500">
                                        {incident.summary}
                                    </p>
                                </div>
                                <Badge className={statusClasses[incident.status]}>
                                    {incident.status}
                                </Badge>
                            </div>
                        ))}
                    </div>
                </div>
            ) : null}
        </Card>
    );
}
