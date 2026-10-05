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
    PageHeader,
    Pagination,
    StatCard,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import {
    ArrowPathIcon,
    ChartBarIcon,
    ClockIcon,
    PauseIcon,
    PlayIcon,
} from "@heroicons/react/24/outline";
import { useCallback, useEffect, useRef, useState } from "react";

import { MonitoringHistoryChart } from "./MonitoringHistoryChart";

interface MonitorResult {
    id: number;
    outcome: string;
    started_at: string;
    finished_at: string;
    duration_ms: number;
    status_code: number | null;
    observed_value: string;
    message: string;
}

interface MonitorIncident {
    id: number;
    status: string;
    severity: string;
    opened_at: string;
    acknowledged_at: string | null;
    resolved_at: string | null;
    failure_count: number;
    summary: string;
}

interface MonitorCheckDetail {
    id: number;
    resource_id: number;
    resource_name: string;
    client_id: number | null;
    client_name: string | null;
    name: string;
    check_type: string;
    severity: string;
    enabled: boolean;
    target: string;
    port: number | null;
    status: string;
    consecutive_failures: number;
    consecutive_successes: number;
    last_checked_at: string | null;
    next_run_at: string | null;
    last_duration_ms: number | null;
    last_message: string;
    expected_value: string;
    forbidden_value: string;
    interval_seconds: number;
    timeout_seconds: number;
    failure_threshold: number;
    recovery_threshold: number;
    expiry_warning_days: number;
    credential_id: number | null;
    uptime_24h_percent: number | null;
    uptime_7d_percent: number | null;
    average_response_24h_ms: number | null;
    average_response_7d_ms: number | null;
    results: MonitorResult[];
    results_page: number;
    results_page_size: number;
    results_total: number;
    trend_results: MonitorResult[];
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
    resolved: "border-emerald-800 bg-emerald-950/60 text-emerald-300",
    success: "border-emerald-800 bg-emerald-950/60 text-emerald-300",
    failure: "border-red-800 bg-red-950/60 text-red-300",
    error: "border-red-800 bg-red-950/60 text-red-300",
};

function formatDate(value: string | null) {
    if (!value) return "Not yet";
    return new Intl.DateTimeFormat("en-GB", {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(new Date(value));
}

function formatPercent(value: number | null) {
    return value === null ? "—" : `${value.toFixed(2)}%`;
}

function formatDuration(value: number | null) {
    return value === null ? "—" : `${value} ms`;
}

function formatInterval(seconds: number) {
    if (seconds % 3600 === 0) return `${seconds / 3600}h`;
    if (seconds % 60 === 0) return `${seconds / 60}m`;
    return `${seconds}s`;
}

function DetailRow({ label, value }: { label: string; value: string }) {
    return (
        <div>
            <dt className="text-xs font-medium text-slate-500">{label}</dt>
            <dd className="mt-1 text-sm break-words text-slate-200">{value}</dd>
        </div>
    );
}

export function MonitoringCheckWorkspace({ checkId }: { checkId: number }) {
    const { hasPermission } = useAuth();
    const [historyPage, setHistoryPage] = useState({ checkId, page: 1 });
    const page = historyPage.checkId === checkId ? historyPage.page : 1;
    const requestVersion = useRef(0);
    const [check, setCheck] = useState<MonitorCheckDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [changingLifecycle, setChangingLifecycle] = useState(false);

    const loadCheck = useCallback(async () => {
        const version = ++requestVersion.current;
        try {
            setLoading(true);
            setError(null);
            const detail = (await fetchAPI(
                AdminAPI.monitoring.get(
                    checkId,
                    new URLSearchParams({
                        results_page: String(page),
                        results_page_size: "10",
                    }).toString(),
                ),
            )) as MonitorCheckDetail;
            if (version === requestVersion.current) setCheck(detail);
        } catch (loadError) {
            if (version !== requestVersion.current) return;
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Monitoring check details are unavailable.",
            );
        } finally {
            if (version === requestVersion.current) setLoading(false);
        }
    }, [checkId, page]);

    useLiveRefresh(["monitoring"], loadCheck);

    useEffect(() => {
        void loadCheck();
    }, [loadCheck]);

    const changeLifecycle = async () => {
        if (!check) return;
        try {
            setChangingLifecycle(true);
            setError(null);
            await fetchAPI(
                check.enabled
                    ? AdminAPI.monitoring.pause(check.id)
                    : AdminAPI.monitoring.resume(check.id),
                { method: "POST" },
            );
            await loadCheck();
        } catch (lifecycleError) {
            setError(
                lifecycleError instanceof Error
                    ? lifecycleError.message
                    : "The monitoring check state could not be changed.",
            );
        } finally {
            setChangingLifecycle(false);
        }
    };

    if (loading && !check) {
        return <DataLoading label="Loading monitoring check..." />;
    }
    if (error && !check) {
        return <DataError message={error} onRetry={() => void loadCheck()} />;
    }
    if (!check) return null;

    const canChange = hasPermission("monitoring.change_monitorcheck");

    return (
        <div className="space-y-6">
            <PageHeader
                eyebrow="Monitoring check"
                title={check.name}
                description={`${check.client_name ? `${check.client_name} · ` : ""}${check.resource_name} · ${check.target}${check.port ? `:${check.port}` : ""}`}
                actions={
                    <>
                        <ButtonLink href="/admin/monitoring" variant="outline">
                            Monitoring
                        </ButtonLink>
                        <ButtonLink
                            href={`/admin/infrastructure/resources/${check.resource_id}`}
                            variant="secondary"
                        >
                            View resource
                        </ButtonLink>
                        {canChange ? (
                            <Button
                                type="button"
                                variant={check.enabled ? "outline" : "primary"}
                                disabled={changingLifecycle}
                                onClick={() => void changeLifecycle()}
                            >
                                {check.enabled ? (
                                    <PauseIcon className="h-4 w-4" />
                                ) : (
                                    <PlayIcon className="h-4 w-4" />
                                )}
                                {changingLifecycle
                                    ? "Updating..."
                                    : check.enabled
                                      ? "Pause check"
                                      : "Resume check"}
                            </Button>
                        ) : null}
                    </>
                }
            />

            {error ? (
                <DataError message={error} onRetry={() => void loadCheck()} />
            ) : null}

            <div className="flex flex-wrap items-center gap-2">
                <Badge
                    className={
                        statusClasses[check.status] ?? statusClasses.pending
                    }
                >
                    {check.status}
                </Badge>
                <Badge className="border-slate-700 bg-slate-900 text-slate-300">
                    {check.check_type}
                </Badge>
                <Badge className="border-slate-700 bg-slate-900 text-slate-300">
                    {check.severity}
                </Badge>
                {!check.enabled ? (
                    <span className="text-xs text-slate-500">
                        Historical results and incidents are retained while
                        paused.
                    </span>
                ) : null}
            </div>

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard
                    label="24-hour uptime"
                    value={formatPercent(check.uptime_24h_percent)}
                    helper="Successful observations"
                    icon={<ChartBarIcon className="h-5 w-5" />}
                    accent={
                        check.uptime_24h_percent !== null &&
                        check.uptime_24h_percent < 100
                            ? "amber"
                            : "green"
                    }
                />
                <StatCard
                    label="7-day uptime"
                    value={formatPercent(check.uptime_7d_percent)}
                    helper="Successful observations"
                    icon={<ChartBarIcon className="h-5 w-5" />}
                    accent={
                        check.uptime_7d_percent !== null &&
                        check.uptime_7d_percent < 100
                            ? "amber"
                            : "green"
                    }
                />
                <StatCard
                    label="24-hour response"
                    value={formatDuration(check.average_response_24h_ms)}
                    helper={`7-day avg ${formatDuration(check.average_response_7d_ms)}`}
                    icon={<ClockIcon className="h-5 w-5" />}
                    accent="cyan"
                />
                <StatCard
                    label="Last response"
                    value={formatDuration(check.last_duration_ms)}
                    helper={formatDate(check.last_checked_at)}
                    icon={<ArrowPathIcon className="h-5 w-5" />}
                    accent={check.status === "failing" ? "red" : "slate"}
                />
            </div>

            {["icmp", "tcp", "http", "content", "dns", "tls"].includes(
                check.check_type,
            ) ? (
                <MonitoringHistoryChart
                    results={check.trend_results ?? []}
                    total={check.results_total}
                />
            ) : null}

            <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(22rem,1fr)]">
                <Card className="overflow-hidden">
                    <div className="border-b border-slate-800 px-5 py-4">
                        <h2 className="text-sm font-semibold text-white">
                            Recent observations
                        </h2>
                        <p className="mt-1 text-xs text-slate-500">
                            Observations for this check, newest first.
                        </p>
                    </div>
                    {check.results.length === 0 ? (
                        <div className="p-5">
                            <EmptyState
                                title="No observations yet"
                                description="Results will appear after the check has executed."
                            />
                        </div>
                    ) : (
                        <div className="divide-y divide-slate-800">
                            {check.results.map((result) => (
                                <div
                                    key={result.id}
                                    className="grid gap-3 px-5 py-4 md:grid-cols-[minmax(0,1fr)_auto]"
                                >
                                    <div className="min-w-0">
                                        <div className="flex flex-wrap items-center gap-2">
                                            <Badge
                                                className={
                                                    statusClasses[
                                                        result.outcome
                                                    ] ?? statusClasses.pending
                                                }
                                            >
                                                {result.outcome}
                                            </Badge>
                                            {result.status_code !== null ? (
                                                <span className="text-xs text-slate-500">
                                                    HTTP {result.status_code}
                                                </span>
                                            ) : null}
                                            <span className="text-xs text-slate-600">
                                                {result.duration_ms} ms
                                            </span>
                                        </div>
                                        {result.message ? (
                                            <p className="mt-2 text-sm text-slate-300">
                                                {result.message}
                                            </p>
                                        ) : null}
                                        {result.observed_value ? (
                                            <p className="mt-1 text-xs break-all text-slate-600">
                                                {result.observed_value}
                                            </p>
                                        ) : null}
                                    </div>
                                    <p className="text-xs text-slate-500 md:text-right">
                                        {formatDate(result.started_at)}
                                    </p>
                                </div>
                            ))}
                        </div>
                    )}
                    <Pagination
                        page={check.results_page}
                        pageSize={check.results_page_size}
                        totalItems={check.results_total}
                        disabled={loading}
                        onPageChange={(nextPage) =>
                            setHistoryPage({ checkId, page: nextPage })
                        }
                    />
                </Card>

                <div className="space-y-6">
                    <Card className="p-5">
                        <h2 className="text-sm font-semibold text-white">
                            Check configuration
                        </h2>
                        <dl className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
                            <DetailRow label="Type" value={check.check_type} />
                            <DetailRow
                                label="Severity"
                                value={check.severity}
                            />
                            <DetailRow
                                label="Interval"
                                value={formatInterval(check.interval_seconds)}
                            />
                            <DetailRow
                                label="Timeout"
                                value={`${check.timeout_seconds}s`}
                            />
                            <DetailRow
                                label="Failure threshold"
                                value={String(check.failure_threshold)}
                            />
                            <DetailRow
                                label="Recovery threshold"
                                value={String(check.recovery_threshold)}
                            />
                            <DetailRow
                                label="Expiry warning"
                                value={`${check.expiry_warning_days} days`}
                            />
                            <DetailRow
                                label="Next run"
                                value={formatDate(check.next_run_at)}
                            />
                        </dl>
                        {check.expected_value ? (
                            <div className="mt-4 border-t border-slate-800 pt-4">
                                <DetailRow
                                    label="Expected value"
                                    value={check.expected_value}
                                />
                            </div>
                        ) : null}
                        {check.forbidden_value ? (
                            <div className="mt-4 border-t border-slate-800 pt-4">
                                <DetailRow
                                    label="Forbidden value"
                                    value={check.forbidden_value}
                                />
                            </div>
                        ) : null}
                        {check.last_message ? (
                            <div className="mt-4 border-t border-slate-800 pt-4">
                                <DetailRow
                                    label="Latest message"
                                    value={check.last_message}
                                />
                            </div>
                        ) : null}
                    </Card>

                    <Card className="overflow-hidden">
                        <div className="border-b border-slate-800 px-5 py-4">
                            <h2 className="text-sm font-semibold text-white">
                                Incident history
                            </h2>
                            <p className="mt-1 text-xs text-slate-500">
                                Latest 20 threshold incidents.
                            </p>
                        </div>
                        {check.incidents.length === 0 ? (
                            <div className="p-5">
                                <EmptyState
                                    title="No incidents"
                                    description="Threshold breaches will be retained here."
                                />
                            </div>
                        ) : (
                            <div className="divide-y divide-slate-800">
                                {check.incidents.map((incident) => (
                                    <div key={incident.id} className="p-5">
                                        <div className="flex items-start justify-between gap-3">
                                            <Badge
                                                className={
                                                    statusClasses[
                                                        incident.status
                                                    ] ?? statusClasses.pending
                                                }
                                            >
                                                {incident.status}
                                            </Badge>
                                            <span className="text-xs text-slate-600">
                                                {incident.failure_count}{" "}
                                                failures
                                            </span>
                                        </div>
                                        <p className="mt-3 text-sm text-slate-300">
                                            {incident.summary}
                                        </p>
                                        <p className="mt-2 text-xs text-slate-600">
                                            Opened{" "}
                                            {formatDate(incident.opened_at)}
                                            {incident.resolved_at
                                                ? ` · Resolved ${formatDate(incident.resolved_at)}`
                                                : ""}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </Card>
                </div>
            </div>
        </div>
    );
}
