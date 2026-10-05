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
    Pagination,
    Select,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeaderCell,
    TableRow,
    Textarea,
} from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

type Ownership = "client" | "internal";
type ContextType = "internal" | "client" | "project" | "task" | "ticket";
type RecordingPanel = "manual" | "timer" | null;
type BrowseMode = "clients" | "projects" | "internal";
type Period = "this_week" | "last_week" | "30d" | "this_month" | "last_month" | "this_year";

interface ClientOption {
    id: number;
    name: string;
}

interface ProjectOption {
    id: number;
    name: string;
    ownership_type: Ownership;
    client_id: number | null;
    client_name: string | null;
}

interface TaskOption {
    id: number;
    title: string;
    ownership_type: Ownership;
    client_id: number | null;
    client_name: string | null;
    project_id: number | null;
    project_name: string | null;
}

interface TicketOption {
    id: number;
    reference: string;
    subject: string;
    client_id: number | null;
    client_name: string | null;
}

interface TimeOptions {
    clients: ClientOption[];
    projects: ProjectOption[];
    tasks: TaskOption[];
    tickets: TicketOption[];
    can_add_time: boolean;
}

interface RunningTimer {
    id: number;
    started_at: string;
    elapsed_seconds: number;
    description: string;
    billable: boolean;
    ownership_type: Ownership;
    client_id: number | null;
    client_name: string | null;
    project_id: number | null;
    project_name: string | null;
    task_id: number | null;
    task_title: string | null;
    ticket_id: number | null;
    ticket_reference: string | null;
    ticket_subject: string | null;
}

interface ClientSummary {
    client_id: number;
    client_name: string;
    tracked_hours: string;
    billable_hours: string;
    non_billable_hours: string;
    entry_count: number;
    project_count: number;
}

interface TimeSummary {
    date_from: string;
    date_to: string;
    tracked_hours: string;
    billable_hours: string;
    non_billable_hours: string;
    client_hours: string;
    internal_hours: string;
    entry_count: number;
    clients: ClientSummary[];
}

interface TimeEntry {
    id: number;
    date: string;
    duration_hours: string;
    description: string;
    billable: boolean;
    entry_type: string;
    ownership_type: Ownership;
    client_id: number | null;
    client_name: string | null;
    project_id: number | null;
    project_name: string | null;
    task_id: number | null;
    task_title: string | null;
    ticket_id: number | null;
    ticket_reference: string | null;
    ticket_subject: string | null;
    user_name: string | null;
}

interface TimeEntriesReport {
    date_from: string;
    date_to: string;
    tracked_hours: string;
    billable_hours: string;
    non_billable_hours: string;
    total: number;
    page: number;
    page_size: number;
    items: TimeEntry[];
}

interface ContextSelection {
    type: ContextType;
    targetId: number | null;
}

interface ContextPayload {
    ownership_type: Ownership;
    client_id: number | null;
    project_id: number | null;
    task_id: number | null;
    ticket_id: number | null;
    internal: boolean;
}

interface DrilldownScope {
    type: "client" | "project" | "internal";
    id: number | null;
    label: string;
}

const PAGE_SIZE = 50;
const labelClasses = "space-y-1.5 text-sm font-medium text-slate-300";
const INTERNAL_CONTEXT: ContextSelection = { type: "internal", targetId: null };
const periods: Array<{ value: Period; label: string }> = [
    { value: "this_week", label: "This week" },
    { value: "last_week", label: "Last week" },
    { value: "30d", label: "30 days" },
    { value: "this_month", label: "This month" },
    { value: "last_month", label: "Last month" },
    { value: "this_year", label: "This year" },
];

function todayValue() {
    const now = new Date();
    const offset = now.getTimezoneOffset();
    return new Date(now.getTime() - offset * 60_000).toISOString().slice(0, 10);
}

function formatDate(value: string) {
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    }).format(new Date(`${value}T00:00:00`));
}

function formatHours(value: string | number) {
    return `${Number(value).toLocaleString("en-GB", { maximumFractionDigits: 2 })}h`;
}

function formatElapsed(seconds: number) {
    const safeSeconds = Math.max(0, Math.floor(seconds));
    const hours = Math.floor(safeSeconds / 3600);
    const minutes = Math.floor((safeSeconds % 3600) / 60);
    const remainder = safeSeconds % 60;
    return [hours, minutes, remainder].map((part) => String(part).padStart(2, "0")).join(":");
}

function queryId(value: string | null) {
    if (!value) return null;
    const parsed = Number(value);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function initialContextFromParams(searchParams: { get(name: string): string | null }) {
    const candidates: Array<[ContextType, string]> = [
        ["task", "task_id"],
        ["ticket", "ticket_id"],
        ["project", "project_id"],
        ["client", "client_id"],
    ];
    for (const [type, key] of candidates) {
        const targetId = queryId(searchParams.get(key));
        if (targetId !== null) return { type, targetId } satisfies ContextSelection;
    }
    return INTERNAL_CONTEXT;
}

function resolveContext(selection: ContextSelection, options: TimeOptions): ContextPayload | null {
    if (selection.type === "internal") {
        return {
            ownership_type: "internal",
            client_id: null,
            project_id: null,
            task_id: null,
            ticket_id: null,
            internal: true,
        };
    }
    if (selection.targetId === null) return null;

    if (selection.type === "client") {
        const client = options.clients.find((item) => item.id === selection.targetId);
        return client
            ? {
                  ownership_type: "client",
                  client_id: client.id,
                  project_id: null,
                  task_id: null,
                  ticket_id: null,
                  internal: false,
              }
            : null;
    }
    if (selection.type === "project") {
        const project = options.projects.find((item) => item.id === selection.targetId);
        return project
            ? {
                  ownership_type: project.ownership_type,
                  client_id: project.client_id,
                  project_id: project.id,
                  task_id: null,
                  ticket_id: null,
                  internal: project.ownership_type === "internal",
              }
            : null;
    }
    if (selection.type === "task") {
        const task = options.tasks.find((item) => item.id === selection.targetId);
        return task
            ? {
                  ownership_type: task.ownership_type,
                  client_id: task.client_id,
                  project_id: task.project_id,
                  task_id: task.id,
                  ticket_id: null,
                  internal: task.ownership_type === "internal",
              }
            : null;
    }

    const ticket = options.tickets.find((item) => item.id === selection.targetId);
    return ticket
        ? {
              ownership_type: ticket.client_id ? "client" : "internal",
              client_id: ticket.client_id,
              project_id: null,
              task_id: null,
              ticket_id: ticket.id,
              internal: ticket.client_id === null,
          }
        : null;
}

function contextLabel(entry: TimeEntry | RunningTimer) {
    if (entry.task_title) return entry.task_title;
    if (entry.ticket_reference) {
        return `${entry.ticket_reference}: ${entry.ticket_subject || "Ticket"}`;
    }
    if (entry.project_name) return entry.project_name;
    if (entry.client_name) return entry.client_name;
    return "ADB Internal";
}

function contextLink(entry: TimeEntry) {
    if (entry.task_id) return `/admin/tasks/${entry.task_id}`;
    if (entry.ticket_id) return `/admin/tickets/${entry.ticket_id}`;
    if (entry.project_id) return `/admin/projects/${entry.project_id}`;
    if (entry.client_id) return `/admin/clients/${entry.client_id}`;
    return null;
}

function ContextFields({
    value,
    onChange,
    options,
}: {
    value: ContextSelection;
    onChange: (value: ContextSelection) => void;
    options: TimeOptions;
}) {
    return (
        <div className="grid gap-4 sm:grid-cols-2">
            <label className={labelClasses}>
                <span>Context</span>
                <Select
                    value={value.type}
                    onChange={(event) =>
                        onChange({ type: event.target.value as ContextType, targetId: null })
                    }
                >
                    <option value="internal">ADB internal</option>
                    <option value="client">Client</option>
                    <option value="project">Project</option>
                    <option value="task">Task</option>
                    <option value="ticket">Ticket</option>
                </Select>
            </label>
            {value.type === "internal" ? (
                <div className="rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-3 text-sm text-slate-500">
                    Internal work stays separate from Clients and is always non-billable.
                </div>
            ) : (
                <label className={labelClasses}>
                    <span className="capitalize">{value.type}</span>
                    <Select
                        value={value.targetId ?? ""}
                        onChange={(event) =>
                            onChange({
                                ...value,
                                targetId: event.target.value ? Number(event.target.value) : null,
                            })
                        }
                        required
                    >
                        <option value="">Select {value.type}</option>
                        {value.type === "client"
                            ? options.clients.map((client) => (
                                  <option key={client.id} value={client.id}>
                                      {client.name}
                                  </option>
                              ))
                            : null}
                        {value.type === "project"
                            ? options.projects.map((project) => (
                                  <option key={project.id} value={project.id}>
                                      {project.name} — {project.client_name || "ADB Internal"}
                                  </option>
                              ))
                            : null}
                        {value.type === "task"
                            ? options.tasks.map((task) => (
                                  <option key={task.id} value={task.id}>
                                      {task.title} — {task.project_name || task.client_name || "ADB Internal"}
                                  </option>
                              ))
                            : null}
                        {value.type === "ticket"
                            ? options.tickets.map((ticket) => (
                                  <option key={ticket.id} value={ticket.id}>
                                      {ticket.reference} — {ticket.subject}
                                  </option>
                              ))
                            : null}
                    </Select>
                </label>
            )}
        </div>
    );
}

export function TimeTrackingWorkspace() {
    const searchParams = useSearchParams();
    const initialContext = useMemo(() => initialContextFromParams(searchParams), [searchParams]);
    const requestedMode = searchParams.get("mode");
    const [options, setOptions] = useState<TimeOptions | null>(null);
    const [timer, setTimer] = useState<RunningTimer | null>(null);
    const [summary, setSummary] = useState<TimeSummary | null>(null);
    const [entries, setEntries] = useState<TimeEntriesReport | null>(null);
    const [period, setPeriod] = useState<Period>("this_month");
    const [browseMode, setBrowseMode] = useState<BrowseMode>(
        initialContext.type === "project" ? "projects" : "clients",
    );
    const [scope, setScope] = useState<DrilldownScope | null>(null);
    const [page, setPage] = useState(1);
    const [recordingPanel, setRecordingPanel] = useState<RecordingPanel>(
        requestedMode === "manual" || requestedMode === "timer" ? requestedMode : null,
    );
    const [now, setNow] = useState(Date.now());
    const [loading, setLoading] = useState(true);
    const [reportLoading, setReportLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [refreshVersion, setRefreshVersion] = useState(0);

    const [manualContext, setManualContext] = useState<ContextSelection>(initialContext);
    const [manualDate, setManualDate] = useState(todayValue());
    const [manualHours, setManualHours] = useState("0");
    const [manualMinutes, setManualMinutes] = useState("30");
    const [manualDescription, setManualDescription] = useState("");
    const [manualBillable, setManualBillable] = useState(false);
    const [timerContext, setTimerContext] = useState<ContextSelection>(initialContext);
    const [timerDescription, setTimerDescription] = useState("");
    const [timerBillable, setTimerBillable] = useState(false);

    useLiveRefresh(["time"], async () => {
        setTimer((await fetchAPI(AdminAPI.timeEntries.timer.current())) as RunningTimer | null);
        setRefreshVersion((version) => version + 1);
    });

    const loadBootstrap = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const [loadedOptions, loadedTimer] = await Promise.all([
                fetchAPI(AdminAPI.timeEntries.options()) as Promise<TimeOptions>,
                fetchAPI(AdminAPI.timeEntries.timer.current()) as Promise<RunningTimer | null>,
            ]);
            setOptions(loadedOptions);
            setTimer(loadedTimer);

            if (initialContext.type === "client" && initialContext.targetId) {
                const client = loadedOptions.clients.find((item) => item.id === initialContext.targetId);
                if (client) {
                    setBrowseMode("clients");
                    setScope({ type: "client", id: client.id, label: client.name });
                }
            }
            if (initialContext.type === "project" && initialContext.targetId) {
                const project = loadedOptions.projects.find((item) => item.id === initialContext.targetId);
                if (project) {
                    setBrowseMode("projects");
                    setScope({ type: "project", id: project.id, label: project.name });
                }
            }
        } catch (loadError) {
            setError(loadError instanceof Error ? loadError.message : "Unable to load time tracking.");
        } finally {
            setLoading(false);
        }
    }, [initialContext]);

    useEffect(() => {
        void loadBootstrap();
    }, [loadBootstrap]);

    useEffect(() => {
        if (!timer) return;
        const interval = window.setInterval(() => setNow(Date.now()), 1000);
        return () => window.clearInterval(interval);
    }, [timer]);

    useEffect(() => {
        async function loadSummary() {
            try {
                setReportLoading(true);
                const query = new URLSearchParams({ period });
                setSummary(
                    (await fetchAPI(AdminAPI.timeEntries.report(query.toString()))) as TimeSummary,
                );
            } catch (loadError) {
                setError(loadError instanceof Error ? loadError.message : "Unable to load time summary.");
            } finally {
                setReportLoading(false);
            }
        }
        void loadSummary();
    }, [period, refreshVersion]);

    useEffect(() => {
        if (!scope) {
            setEntries(null);
            return;
        }

        async function loadEntries() {
            try {
                setReportLoading(true);
                const query = new URLSearchParams({
                    period,
                    page: String(page),
                    page_size: String(PAGE_SIZE),
                });
                if (scope?.type === "client" && scope.id) query.set("client_id", String(scope.id));
                if (scope?.type === "project" && scope.id) query.set("project_id", String(scope.id));
                if (scope?.type === "internal") query.set("ownership_type", "internal");
                setEntries(
                    (await fetchAPI(
                        `${API_URL}/api/admin/time-reports/entries?${query.toString()}`,
                    )) as TimeEntriesReport,
                );
            } catch (loadError) {
                setError(loadError instanceof Error ? loadError.message : "Unable to load time entries.");
            } finally {
                setReportLoading(false);
            }
        }
        void loadEntries();
    }, [page, period, refreshVersion, scope]);

    const manualPayload = options ? resolveContext(manualContext, options) : null;
    const timerPayload = options ? resolveContext(timerContext, options) : null;
    const clientSummaryById = useMemo(
        () => new Map((summary?.clients ?? []).map((client) => [client.client_id, client])),
        [summary],
    );

    function selectBrowseMode(mode: BrowseMode) {
        setBrowseMode(mode);
        setPage(1);
        if (mode === "internal") {
            setScope({ type: "internal", id: null, label: "ADB Internal" });
        } else {
            setScope(null);
        }
    }

    async function addManualEntry(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!manualPayload) {
            setError("Select a valid context before recording time.");
            return;
        }
        const duration = Number(manualHours || 0) + Number(manualMinutes || 0) / 60;
        if (duration <= 0) {
            setError("Tracked time must be greater than zero.");
            return;
        }
        setSaving(true);
        setError(null);
        try {
            await fetchAPI(AdminAPI.timeEntries.create(), {
                method: "POST",
                body: JSON.stringify({
                    ...manualPayload,
                    date: manualDate,
                    duration_hours: duration.toFixed(4),
                    description: manualDescription,
                    billable: manualPayload.internal ? false : manualBillable,
                }),
            });
            setManualHours("0");
            setManualMinutes("30");
            setManualDescription("");
            setRecordingPanel(null);
            setRefreshVersion((value) => value + 1);
        } catch (saveError) {
            setError(saveError instanceof Error ? saveError.message : "Unable to record time.");
        } finally {
            setSaving(false);
        }
    }

    async function startTimer(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!timerPayload) {
            setError("Select a valid context before starting the timer.");
            return;
        }
        setSaving(true);
        setError(null);
        try {
            const started = (await fetchAPI(AdminAPI.timeEntries.timer.start(), {
                method: "POST",
                body: JSON.stringify({
                    ...timerPayload,
                    description: timerDescription,
                    billable: timerPayload.internal ? false : timerBillable,
                }),
            })) as RunningTimer;
            setTimer(started);
            setNow(Date.now());
            setRecordingPanel(null);
        } catch (startError) {
            setError(startError instanceof Error ? startError.message : "Unable to start timer.");
        } finally {
            setSaving(false);
        }
    }

    async function stopTimer() {
        setSaving(true);
        setError(null);
        try {
            await fetchAPI(AdminAPI.timeEntries.timer.stop(), {
                method: "POST",
                body: JSON.stringify({}),
            });
            setTimer(null);
            setTimerDescription("");
            setRefreshVersion((value) => value + 1);
        } catch (stopError) {
            setError(stopError instanceof Error ? stopError.message : "Unable to stop timer.");
        } finally {
            setSaving(false);
        }
    }

    async function cancelTimer() {
        setSaving(true);
        setError(null);
        try {
            await fetchAPI(AdminAPI.timeEntries.timer.cancel(), { method: "POST" });
            setTimer(null);
        } catch (cancelError) {
            setError(cancelError instanceof Error ? cancelError.message : "Unable to cancel timer.");
        } finally {
            setSaving(false);
        }
    }

    if (loading && !options) return <DataLoading label="Loading time tracking..." />;
    if (error && !options) return <DataError message={error} onRetry={() => void loadBootstrap()} />;
    if (!options) return null;

    const elapsed = timer
        ? Math.max(
              timer.elapsed_seconds,
              Math.floor((now - new Date(timer.started_at).getTime()) / 1000),
          )
        : 0;

    return (
        <div className="space-y-8">
            {error ? (
                <div className="rounded-lg border border-red-900/70 bg-red-950/40 px-4 py-3 text-sm text-red-200">
                    {error}
                </div>
            ) : null}

            <section className="space-y-4">
                {timer ? (
                    <Card className="border-emerald-900/60 p-5">
                        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                            <div>
                                <div className="text-xs font-semibold uppercase tracking-wide text-emerald-400">
                                    Active timer
                                </div>
                                <div className="mt-1 text-lg font-semibold text-white">
                                    {contextLabel(timer)}
                                </div>
                                <div className="mt-1 text-sm text-slate-500">
                                    {timer.description || "Tracking work"}
                                </div>
                            </div>
                            <div className="flex flex-wrap items-center gap-3">
                                <div className="font-mono text-3xl font-semibold tabular-nums text-white">
                                    {formatElapsed(elapsed)}
                                </div>
                                <Button disabled={saving} onClick={() => void stopTimer()}>
                                    {saving ? "Stopping…" : "Stop timer"}
                                </Button>
                                <Button variant="outline" disabled={saving} onClick={() => void cancelTimer()}>
                                    Cancel
                                </Button>
                            </div>
                        </div>
                    </Card>
                ) : null}

                {options.can_add_time ? (
                    <Card className="overflow-hidden">
                        <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
                            <div>
                                <h2 className="text-sm font-semibold text-white">Record time</h2>
                                <p className="mt-1 text-xs text-slate-500">
                                    Keep recording controls available without letting them dominate the page.
                                </p>
                            </div>
                            <div className="flex gap-2">
                                <Button
                                    variant={recordingPanel === "timer" ? "secondary" : "outline"}
                                    disabled={timer !== null}
                                    onClick={() =>
                                        setRecordingPanel((current) => (current === "timer" ? null : "timer"))
                                    }
                                >
                                    Start timer
                                </Button>
                                <Button
                                    variant={recordingPanel === "manual" ? "secondary" : "outline"}
                                    onClick={() =>
                                        setRecordingPanel((current) =>
                                            current === "manual" ? null : "manual",
                                        )
                                    }
                                >
                                    Add manually
                                </Button>
                            </div>
                        </div>

                        {recordingPanel === "timer" && !timer ? (
                            <form
                                onSubmit={(event) => void startTimer(event)}
                                className="space-y-4 border-t border-slate-800 p-5"
                            >
                                <ContextFields
                                    value={timerContext}
                                    onChange={setTimerContext}
                                    options={options}
                                />
                                <label className={`block ${labelClasses}`}>
                                    <span>Description</span>
                                    <Textarea
                                        value={timerDescription}
                                        onChange={(event) => setTimerDescription(event.target.value)}
                                        rows={2}
                                        placeholder="Optional — the work item will be used if left blank."
                                    />
                                </label>
                                <label className="flex items-center gap-2 text-sm text-slate-300">
                                    <input
                                        type="checkbox"
                                        checked={timerPayload?.internal ? false : timerBillable}
                                        disabled={timerPayload?.internal ?? false}
                                        onChange={(event) => setTimerBillable(event.target.checked)}
                                    />
                                    Billable
                                </label>
                                <Button type="submit" disabled={saving}>
                                    Start timer
                                </Button>
                            </form>
                        ) : null}

                        {recordingPanel === "manual" ? (
                            <form
                                onSubmit={(event) => void addManualEntry(event)}
                                className="space-y-4 border-t border-slate-800 p-5"
                            >
                                <ContextFields
                                    value={manualContext}
                                    onChange={setManualContext}
                                    options={options}
                                />
                                <div className="grid gap-4 sm:grid-cols-3">
                                    <label className={labelClasses}>
                                        <span>Date</span>
                                        <Input
                                            type="date"
                                            value={manualDate}
                                            onChange={(event) => setManualDate(event.target.value)}
                                            required
                                        />
                                    </label>
                                    <label className={labelClasses}>
                                        <span>Hours</span>
                                        <Input
                                            type="number"
                                            min="0"
                                            step="1"
                                            value={manualHours}
                                            onChange={(event) => setManualHours(event.target.value)}
                                            required
                                        />
                                    </label>
                                    <label className={labelClasses}>
                                        <span>Minutes</span>
                                        <Input
                                            type="number"
                                            min="0"
                                            max="59"
                                            step="1"
                                            value={manualMinutes}
                                            onChange={(event) => setManualMinutes(event.target.value)}
                                            required
                                        />
                                    </label>
                                </div>
                                <label className={`block ${labelClasses}`}>
                                    <span>Description</span>
                                    <Textarea
                                        value={manualDescription}
                                        onChange={(event) => setManualDescription(event.target.value)}
                                        rows={2}
                                        required
                                    />
                                </label>
                                <label className="flex items-center gap-2 text-sm text-slate-300">
                                    <input
                                        type="checkbox"
                                        checked={manualPayload?.internal ? false : manualBillable}
                                        disabled={manualPayload?.internal ?? false}
                                        onChange={(event) => setManualBillable(event.target.checked)}
                                    />
                                    Billable
                                </label>
                                <Button type="submit" disabled={saving}>
                                    Add time
                                </Button>
                            </form>
                        ) : null}
                    </Card>
                ) : null}
            </section>

            <section className="space-y-5">
                <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
                    <div>
                        <h2 className="text-lg font-semibold text-white">Time workspace</h2>
                        <p className="mt-1 text-sm text-slate-500">
                            Choose a period, then drill into the Client, Project or Internal work you care about.
                        </p>
                    </div>
                    <div className="flex flex-wrap gap-1 rounded-lg border border-slate-800 bg-slate-900 p-1">
                        {periods.map((option) => (
                            <button
                                key={option.value}
                                type="button"
                                onClick={() => {
                                    setPeriod(option.value);
                                    setPage(1);
                                }}
                                className={`rounded-md px-3 py-2 text-xs font-medium transition ${
                                    period === option.value
                                        ? "bg-slate-700 text-white"
                                        : "text-slate-400 hover:text-slate-200"
                                }`}
                            >
                                {option.label}
                            </button>
                        ))}
                    </div>
                </div>

                {summary ? (
                    <>
                        <div className="text-xs text-slate-600">
                            {formatDate(summary.date_from)} – {formatDate(summary.date_to)} · {summary.entry_count} entries
                        </div>
                        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                            <Card className="p-5">
                                <div className="text-xs uppercase tracking-wide text-slate-500">Tracked</div>
                                <div className="mt-2 text-2xl font-semibold text-white">
                                    {formatHours(summary.tracked_hours)}
                                </div>
                            </Card>
                            <Card className="p-5">
                                <div className="text-xs uppercase tracking-wide text-slate-500">Billable</div>
                                <div className="mt-2 text-2xl font-semibold text-white">
                                    {formatHours(summary.billable_hours)}
                                </div>
                            </Card>
                            <Card className="p-5">
                                <div className="text-xs uppercase tracking-wide text-slate-500">Client work</div>
                                <div className="mt-2 text-2xl font-semibold text-white">
                                    {formatHours(summary.client_hours)}
                                </div>
                            </Card>
                            <Card className="p-5">
                                <div className="text-xs uppercase tracking-wide text-slate-500">Internal</div>
                                <div className="mt-2 text-2xl font-semibold text-white">
                                    {formatHours(summary.internal_hours)}
                                </div>
                            </Card>
                        </div>
                    </>
                ) : reportLoading ? (
                    <DataLoading label="Loading time overview..." />
                ) : null}

                <div className="flex gap-1 overflow-x-auto border-b border-slate-800">
                    {(
                        [
                            ["clients", "Clients"],
                            ["projects", "Projects"],
                            ["internal", "Internal"],
                        ] as Array<[BrowseMode, string]>
                    ).map(([value, label]) => (
                        <button
                            key={value}
                            type="button"
                            onClick={() => selectBrowseMode(value)}
                            className={`border-b-2 px-4 py-3 text-sm font-medium transition ${
                                browseMode === value
                                    ? "border-adb-cyan-400 text-white"
                                    : "border-transparent text-slate-500 hover:text-slate-300"
                            }`}
                        >
                            {label}
                        </button>
                    ))}
                </div>

                {!scope && browseMode === "clients" ? (
                    <Card className="overflow-hidden">
                        <div className="border-b border-slate-800 px-5 py-4">
                            <h3 className="text-sm font-semibold text-white">Clients</h3>
                            <p className="mt-1 text-xs text-slate-500">
                                Open a Client to inspect only their entries for the selected period.
                            </p>
                        </div>
                        {options.clients.length ? (
                            <div className="divide-y divide-slate-800">
                                {options.clients.map((client) => {
                                    const clientSummary = clientSummaryById.get(client.id);
                                    return (
                                        <button
                                            key={client.id}
                                            type="button"
                                            onClick={() => {
                                                setScope({ type: "client", id: client.id, label: client.name });
                                                setPage(1);
                                            }}
                                            className="grid w-full gap-2 px-5 py-4 text-left transition hover:bg-slate-900/60 sm:grid-cols-[minmax(0,1fr)_7rem_7rem_6rem] sm:items-center"
                                        >
                                            <div>
                                                <div className="font-medium text-slate-200">{client.name}</div>
                                                <div className="mt-1 text-xs text-slate-600">
                                                    {clientSummary?.entry_count ?? 0} entries · {clientSummary?.project_count ?? 0} projects
                                                </div>
                                            </div>
                                            <div className="text-sm tabular-nums text-slate-400">
                                                {formatHours(clientSummary?.tracked_hours ?? 0)}
                                            </div>
                                            <div className="text-sm tabular-nums text-slate-500">
                                                {formatHours(clientSummary?.billable_hours ?? 0)} billable
                                            </div>
                                            <div className="text-right text-xs font-medium text-adb-cyan-300">
                                                View time →
                                            </div>
                                        </button>
                                    );
                                })}
                            </div>
                        ) : (
                            <EmptyState title="No Clients available" description="Clients in your access scope will appear here." />
                        )}
                    </Card>
                ) : null}

                {!scope && browseMode === "projects" ? (
                    <Card className="overflow-hidden">
                        <div className="border-b border-slate-800 px-5 py-4">
                            <h3 className="text-sm font-semibold text-white">Projects</h3>
                            <p className="mt-1 text-xs text-slate-500">
                                Open a Project to review its time ledger for the selected period.
                            </p>
                        </div>
                        {options.projects.length ? (
                            <div className="divide-y divide-slate-800">
                                {options.projects.map((project) => (
                                    <button
                                        key={project.id}
                                        type="button"
                                        onClick={() => {
                                            setScope({ type: "project", id: project.id, label: project.name });
                                            setPage(1);
                                        }}
                                        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition hover:bg-slate-900/60"
                                    >
                                        <div>
                                            <div className="font-medium text-slate-200">{project.name}</div>
                                            <div className="mt-1 text-xs text-slate-600">
                                                {project.client_name || "ADB Internal"}
                                            </div>
                                        </div>
                                        <span className="text-xs font-medium text-adb-cyan-300">View time →</span>
                                    </button>
                                ))}
                            </div>
                        ) : (
                            <EmptyState title="No Projects available" description="Projects in your access scope will appear here." />
                        )}
                    </Card>
                ) : null}

                {scope ? (
                    <div className="space-y-5">
                        {scope.type !== "internal" ? (
                            <button
                                type="button"
                                onClick={() => setScope(null)}
                                className="text-sm text-slate-500 hover:text-slate-300"
                            >
                                ← Back to {scope.type === "client" ? "Clients" : "Projects"}
                            </button>
                        ) : null}

                        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                            <div>
                                <div className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                                    {scope.type === "internal" ? "Internal time" : `${scope.type} time`}
                                </div>
                                <h3 className="mt-1 text-xl font-semibold text-white">{scope.label}</h3>
                            </div>
                            {scope.type === "client" && scope.id ? (
                                <Link
                                    href={`/admin/clients/${scope.id}`}
                                    className="text-sm text-slate-500 hover:text-adb-cyan-300"
                                >
                                    Open Client workspace →
                                </Link>
                            ) : null}
                            {scope.type === "project" && scope.id ? (
                                <Link
                                    href={`/admin/projects/${scope.id}`}
                                    className="text-sm text-slate-500 hover:text-adb-cyan-300"
                                >
                                    Open Project →
                                </Link>
                            ) : null}
                        </div>

                        {entries ? (
                            <>
                                <div className="grid gap-4 sm:grid-cols-3">
                                    <Card className="p-5">
                                        <div className="text-xs uppercase tracking-wide text-slate-500">Tracked</div>
                                        <div className="mt-2 text-2xl font-semibold text-white">
                                            {formatHours(entries.tracked_hours)}
                                        </div>
                                    </Card>
                                    <Card className="p-5">
                                        <div className="text-xs uppercase tracking-wide text-slate-500">Billable</div>
                                        <div className="mt-2 text-2xl font-semibold text-white">
                                            {formatHours(entries.billable_hours)}
                                        </div>
                                    </Card>
                                    <Card className="p-5">
                                        <div className="text-xs uppercase tracking-wide text-slate-500">Non-billable</div>
                                        <div className="mt-2 text-2xl font-semibold text-white">
                                            {formatHours(entries.non_billable_hours)}
                                        </div>
                                    </Card>
                                </div>

                                <Card className="overflow-hidden">
                                    <div className="border-b border-slate-800 px-5 py-4">
                                        <h4 className="text-sm font-semibold text-white">Time entries</h4>
                                        <p className="mt-1 text-xs text-slate-500">
                                            {formatDate(entries.date_from)} – {formatDate(entries.date_to)} · {entries.total} entries
                                        </p>
                                    </div>
                                    {entries.items.length ? (
                                        <>
                                            <Table>
                                                <TableHead>
                                                    <tr>
                                                        <TableHeaderCell>Date</TableHeaderCell>
                                                        <TableHeaderCell>Work</TableHeaderCell>
                                                        <TableHeaderCell>Description</TableHeaderCell>
                                                        <TableHeaderCell>Staff</TableHeaderCell>
                                                        <TableHeaderCell>Billing</TableHeaderCell>
                                                        <TableHeaderCell className="text-right">Time</TableHeaderCell>
                                                    </tr>
                                                </TableHead>
                                                <TableBody>
                                                    {entries.items.map((entry) => {
                                                        const href = contextLink(entry);
                                                        return (
                                                            <TableRow key={entry.id}>
                                                                <TableCell className="whitespace-nowrap text-slate-400">
                                                                    {formatDate(entry.date)}
                                                                </TableCell>
                                                                <TableCell>
                                                                    {href ? (
                                                                        <Link
                                                                            href={href}
                                                                            className="font-medium text-slate-200 hover:text-adb-cyan-300"
                                                                        >
                                                                            {contextLabel(entry)}
                                                                        </Link>
                                                                    ) : (
                                                                        <span className="font-medium text-slate-200">
                                                                            {contextLabel(entry)}
                                                                        </span>
                                                                    )}
                                                                </TableCell>
                                                                <TableCell className="max-w-md text-slate-400">
                                                                    {entry.description || "—"}
                                                                </TableCell>
                                                                <TableCell className="text-slate-400">
                                                                    {entry.user_name || "Unknown"}
                                                                </TableCell>
                                                                <TableCell>
                                                                    <Badge>
                                                                        {entry.billable ? "Billable" : "Non-billable"}
                                                                    </Badge>
                                                                </TableCell>
                                                                <TableCell className="text-right font-semibold tabular-nums text-slate-200">
                                                                    {formatHours(entry.duration_hours)}
                                                                </TableCell>
                                                            </TableRow>
                                                        );
                                                    })}
                                                </TableBody>
                                            </Table>
                                            <Pagination
                                                page={entries.page}
                                                pageSize={entries.page_size}
                                                totalItems={entries.total}
                                                onPageChange={setPage}
                                                disabled={reportLoading}
                                            />
                                        </>
                                    ) : (
                                        <EmptyState
                                            title="No time in this period"
                                            description="Choose another period or record time against this work context."
                                        />
                                    )}
                                </Card>
                            </>
                        ) : reportLoading ? (
                            <DataLoading label="Loading time entries..." />
                        ) : null}
                    </div>
                ) : null}
            </section>
        </div>
    );
}
