"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";

import {
    Badge,
    Button,
    ButtonLink,
    Card,
    DataError,
    DataLoading,
    EmptyState,
    StatCard,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import {
    CheckCircleIcon,
    ClockIcon,
    ExclamationTriangleIcon,
    SignalIcon,
} from "@heroicons/react/24/outline";
import { useCallback, useEffect, useState } from "react";

interface MonitorCheck {
    id: number;
    resource_id: number;
    resource_name: string;
    client_name: string | null;
    name: string;
    check_type: string;
    severity: string;
    enabled: boolean;
    target: string;
    port: number | null;
    status: string;
    last_checked_at: string | null;
    last_duration_ms: number | null;
    last_message: string;
}

interface MonitorIncident {
    id: number;
    check_name: string;
    resource_name: string;
    client_name: string | null;
    status: string;
    severity: string;
    opened_at: string;
    failure_count: number;
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

const statusClasses: Record<string, string> = {
    healthy: "border-emerald-800 bg-emerald-950/60 text-emerald-300",
    degraded: "border-yellow-800 bg-yellow-950/60 text-yellow-300",
    failing: "border-red-800 bg-red-950/60 text-red-300",
    pending: "border-slate-700 bg-slate-800/70 text-slate-300",
    paused: "border-slate-700 bg-slate-900 text-slate-400",
    open: "border-red-800 bg-red-950/60 text-red-300",
    acknowledged: "border-yellow-800 bg-yellow-950/60 text-yellow-300",
};

function formatDate(value: string | null) {
    if (!value) return "Not run yet";
    return new Intl.DateTimeFormat("en-GB", {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(new Date(value));
}

export function MonitoringWorkspace() {
    const { hasPermission } = useAuth();
    const canAcknowledge = hasPermission("monitoring.change_monitorincident");
    const [overview, setOverview] = useState<MonitoringOverview | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [acknowledgingId, setAcknowledgingId] = useState<number | null>(null);

    const loadOverview = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            setOverview(
                (await fetchAPI(
                    AdminAPI.monitoring.overview(),
                )) as MonitoringOverview,
            );
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Monitoring health is unavailable.",
            );
        } finally {
            setLoading(false);
        }
    }, []);

    useLiveRefresh(["monitoring"], loadOverview);

    useEffect(() => {
        void loadOverview();
    }, [loadOverview]);

    const acknowledge = async (incidentId: number) => {
        if (!canAcknowledge) return;
        try {
            setAcknowledgingId(incidentId);
            setError(null);
            await fetchAPI(AdminAPI.monitoring.acknowledge(incidentId), {
                method: "POST",
            });
            await loadOverview();
        } catch (acknowledgeError) {
            setError(
                acknowledgeError instanceof Error
                    ? acknowledgeError.message
                    : "The incident could not be acknowledged.",
            );
        } finally {
            setAcknowledgingId(null);
        }
    };

    if (loading && !overview) {
        return <DataLoading label="Loading technical health..." />;
    }
    if (error && !overview) {
        return (
            <DataError
                message={error}
                onRetry={() => void loadOverview()}
            />
        );
    }
    if (!overview) return null;

    return (
        <div className="space-y-6">
            {error ? (
                <DataError
                    message={error}
                    onRetry={() => void loadOverview()}
                />
            ) : null}

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard
                    label="Healthy checks"
                    value={String(overview.healthy_checks)}
                    helper={`${overview.total_checks} enabled checks`}
                    icon={<CheckCircleIcon className="h-5 w-5" />}
                    accent="green"
                />
                <StatCard
                    label="Degraded"
                    value={String(overview.degraded_checks)}
                    helper="Below incident threshold"
                    icon={<ExclamationTriangleIcon className="h-5 w-5" />}
                    accent={overview.degraded_checks > 0 ? "amber" : "slate"}
                />
                <StatCard
                    label="Failing"
                    value={String(overview.failing_checks)}
                    helper="Checks in a failing state"
                    icon={<SignalIcon className="h-5 w-5" />}
                    accent={overview.failing_checks > 0 ? "red" : "slate"}
                />
                <StatCard
                    label="Active incidents"
                    value={String(overview.open_incidents)}
                    helper={`${overview.pending_checks} checks awaiting first run`}
                    icon={<ClockIcon className="h-5 w-5" />}
                    accent={overview.open_incidents > 0 ? "red" : "cyan"}
                />
            </div>

            <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(22rem,1fr)]">
                <Card className="overflow-hidden">
                    <div className="border-b border-slate-800 px-5 py-4">
                        <h2 className="text-sm font-semibold text-white">
                            Current health
                        </h2>
                        <p className="mt-1 text-xs text-slate-500">
                            Latest state for the first 100 visible checks.
                        </p>
                    </div>
                    {overview.checks.length === 0 ? (
                        <div className="p-5">
                            <EmptyState
                                title="No monitoring checks"
                                description="Checks will appear here after they are attached to infrastructure resources."
                            />
                        </div>
                    ) : (
                        <div className="divide-y divide-slate-800">
                            {overview.checks.map((check) => (
                                <div
                                    key={check.id}
                                    className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
                                >
                                    <div className="min-w-0">
                                        <div className="flex flex-wrap items-center gap-2">
                                            <p className="truncate text-sm font-medium text-slate-100">
                                                {check.name}
                                            </p>
                                            <Badge
                                                className={
                                                    statusClasses[
                                                        check.status
                                                    ]
                                                }
                                            >
                                                {check.status}
                                            </Badge>
                                        </div>
                                        <p className="mt-1 truncate text-xs text-slate-500">
                                            {check.client_name
                                                ? `${check.client_name} · `
                                                : ""}
                                            {check.resource_name} · {check.target}
                                            {check.port
                                                ? `:${check.port}`
                                                : ""}
                                        </p>
                                        {check.last_message ? (
                                            <p className="mt-1 truncate text-xs text-slate-600">
                                                {check.last_message}
                                            </p>
                                        ) : null}
                                    </div>
                                    <div className="flex shrink-0 items-center gap-3">
                                        <div className="text-left text-xs text-slate-500 sm:text-right">
                                            <p>{formatDate(check.last_checked_at)}</p>
                                            <p className="mt-1 uppercase">
                                                {check.check_type}
                                                {check.last_duration_ms !== null
                                                    ? ` · ${check.last_duration_ms} ms`
                                                    : ""}
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
                                </div>
                            ))}
                        </div>
                    )}
                </Card>

                <Card className="overflow-hidden">
                    <div className="border-b border-slate-800 px-5 py-4">
                        <h2 className="text-sm font-semibold text-white">
                            Active incidents
                        </h2>
                        <p className="mt-1 text-xs text-slate-500">
                            Open and acknowledged threshold breaches.
                        </p>
                    </div>
                    {overview.incidents.length === 0 ? (
                        <div className="p-5">
                            <EmptyState
                                title="No active incidents"
                                description="Threshold breaches requiring attention will appear here."
                            />
                        </div>
                    ) : (
                        <div className="divide-y divide-slate-800">
                            {overview.incidents.map((incident) => (
                                <div key={incident.id} className="p-5">
                                    <div className="flex items-start justify-between gap-3">
                                        <div className="min-w-0">
                                            <p className="text-sm font-medium text-slate-100">
                                                {incident.check_name}
                                            </p>
                                            <p className="mt-1 text-xs text-slate-500">
                                                {incident.client_name
                                                    ? `${incident.client_name} · `
                                                    : ""}
                                                {incident.resource_name}
                                            </p>
                                        </div>
                                        <Badge
                                            className={
                                                statusClasses[incident.status]
                                            }
                                        >
                                            {incident.status}
                                        </Badge>
                                    </div>
                                    <p className="mt-3 text-xs leading-5 text-slate-400">
                                        {incident.summary}
                                    </p>
                                    <div className="mt-4 flex items-center justify-between gap-3">
                                        <p className="text-xs text-slate-600">
                                            {incident.failure_count} failures ·{" "}
                                            {formatDate(incident.opened_at)}
                                        </p>
                                        {incident.status === "open" && canAcknowledge ? (
                                            <Button
                                                type="button"
                                                size="sm"
                                                variant="secondary"
                                                disabled={acknowledgingId === incident.id}
                                                onClick={() => void acknowledge(incident.id)}
                                            >
                                                {acknowledgingId === incident.id
                                                    ? "Acknowledging..."
                                                    : "Acknowledge"}
                                            </Button>
                                        ) : null}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </Card>
            </div>
        </div>
    );
}
