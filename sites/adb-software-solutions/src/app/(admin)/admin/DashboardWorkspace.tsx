"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";

import { Button, Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import {
    ArrowDownIcon,
    ArrowUpIcon,
    CalendarDaysIcon,
    ClockIcon,
    Cog6ToothIcon,
    FolderIcon,
    ListBulletIcon,
    MegaphoneIcon,
    ServerStackIcon,
    TicketIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";
import { type ReactNode, useEffect, useState } from "react";

interface WidgetPreference {
    key: string;
    span: number;
}

interface WidgetOption {
    key: string;
    title: string;
    description: string;
    default_span: number;
}

interface DashboardTask {
    id: number;
    title: string;
    status: string;
    priority: number;
    due_date: string | null;
    client_name: string | null;
    project_name: string | null;
}

interface DashboardTicket {
    id: number;
    reference: string;
    subject: string;
    status: string;
    priority: string;
    queue_name: string;
    client_name: string | null;
    last_message_at: string | null;
}

interface DashboardWorkspaceData {
    layout: WidgetPreference[];
    available_widgets: WidgetOption[];
    my_tasks: {
        open_count: number;
        overdue_count: number;
        today_count: number;
        items: DashboardTask[];
    } | null;
    my_tickets: {
        mine_count: number;
        unassigned_count: number;
        active_count: number;
        items: DashboardTicket[];
    } | null;
    active_timer: {
        running: boolean;
        started_at: string | null;
        description: string;
        context_label: string;
        hours_this_week: number;
    } | null;
    lead_follow_up: {
        open_count: number;
        items: Array<{
            id: number;
            name: string;
            company: string;
            status: string;
            brand: string;
        }>;
    } | null;
    current_projects: {
        current_count: number;
        items: Array<{
            id: number;
            name: string;
            status: string;
            client_name: string | null;
            end_date: string | null;
        }>;
    } | null;
    technical_health: {
        active_incident_count: number;
        failing_check_count: number;
        items: Array<{
            id: number;
            check_name: string;
            resource_name: string;
            severity: string;
            status: string;
            summary: string;
        }>;
    } | null;
    agenda: {
        today_count: number;
        next_seven_days_count: number;
        items: DashboardTask[];
    } | null;
    recent_activity: Array<{
        id: number;
        action: string;
        target_label: string;
        created_at: string;
    }> | null;
}

const spanClass: Record<number, string> = {
    4: "xl:col-span-4",
    6: "xl:col-span-6",
    8: "xl:col-span-8",
    12: "xl:col-span-12",
};

const widgetIcons: Record<string, ReactNode> = {
    my_tasks: <ListBulletIcon className="h-5 w-5" />,
    my_tickets: <TicketIcon className="h-5 w-5" />,
    active_timer: <ClockIcon className="h-5 w-5" />,
    lead_follow_up: <MegaphoneIcon className="h-5 w-5" />,
    current_projects: <FolderIcon className="h-5 w-5" />,
    technical_health: <ServerStackIcon className="h-5 w-5" />,
    agenda: <CalendarDaysIcon className="h-5 w-5" />,
};

function formatDate(value: string | null) {
    if (!value) return "No date";
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
    }).format(new Date(`${value}T12:00:00`));
}

function formatDateTime(value: string) {
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
    }).format(new Date(value));
}

function Metric({
    label,
    value,
    warning = false,
}: {
    label: string;
    value: number | string;
    warning?: boolean;
}) {
    return (
        <div className="rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2.5">
            <p className="text-[11px] uppercase tracking-wide text-slate-600">{label}</p>
            <p
                className={`mt-1 text-xl font-semibold ${
                    warning ? "text-amber-300" : "text-slate-100"
                }`}
            >
                {value}
            </p>
        </div>
    );
}

function WidgetShell({
    title,
    description,
    href,
    children,
}: {
    title: string;
    description: string;
    href?: string;
    children: ReactNode;
}) {
    return (
        <Card className="h-full">
            <CardHeader className="flex flex-row items-start justify-between gap-4 border-b border-slate-800">
                <div>
                    <CardTitle>{title}</CardTitle>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{description}</p>
                </div>
                {href ? (
                    <Link
                        href={href}
                        className="shrink-0 text-xs font-medium text-adb-cyan-400 hover:text-adb-cyan-300"
                    >
                        Open
                    </Link>
                ) : null}
            </CardHeader>
            <CardContent>{children}</CardContent>
        </Card>
    );
}

function Empty({ children }: { children: ReactNode }) {
    return <p className="py-7 text-center text-sm text-slate-600">{children}</p>;
}

function TaskRows({ tasks }: { tasks: DashboardTask[] }) {
    if (!tasks.length) return <Empty>No assigned tasks need attention.</Empty>;
    return (
        <div className="mt-4 divide-y divide-slate-800">
            {tasks.map((task) => (
                <div key={task.id} className="flex items-center gap-3 py-2.5">
                    <span
                        className={`h-2 w-2 shrink-0 rounded-full ${
                            task.priority >= 4
                                ? "bg-red-400"
                                : task.priority === 3
                                  ? "bg-amber-400"
                                  : "bg-slate-600"
                        }`}
                    />
                    <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-slate-200">{task.title}</p>
                        <p className="truncate text-xs text-slate-600">
                            {task.project_name ?? task.client_name ?? "Internal"}
                        </p>
                    </div>
                    <span className="text-xs text-slate-500">{formatDate(task.due_date)}</span>
                </div>
            ))}
        </div>
    );
}

export function DashboardWorkspace() {
    const [data, setData] = useState<DashboardWorkspaceData | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [customising, setCustomising] = useState(false);
    const [draft, setDraft] = useState<WidgetPreference[]>([]);
    const [saving, setSaving] = useState(false);

    async function load() {
        try {
            setError(null);
            const workspace = (await fetchAPI(
                AdminAPI.dashboard.summary(),
            )) as DashboardWorkspaceData;
            setData(workspace);
            if (!customising) setDraft(workspace.layout);
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : "Unable to load your dashboard.");
        }
    }

    useEffect(() => {
        void load();
    }, []);

    useLiveRefresh(["dashboard"], load);

    function toggleWidget(option: WidgetOption) {
        setDraft((current) =>
            current.some((item) => item.key === option.key)
                ? current.filter((item) => item.key !== option.key)
                : [...current, { key: option.key, span: option.default_span }],
        );
    }

    function moveWidget(index: number, direction: -1 | 1) {
        setDraft((current) => {
            const target = index + direction;
            if (target < 0 || target >= current.length) return current;
            const next = [...current];
            [next[index], next[target]] = [next[target], next[index]];
            return next;
        });
    }

    function changeSpan(key: string, span: number) {
        setDraft((current) =>
            current.map((item) => (item.key === key ? { ...item, span } : item)),
        );
    }

    async function saveLayout() {
        try {
            setSaving(true);
            setError(null);
            const workspace = (await fetchAPI(`${AdminAPI.dashboard.summary()}/preferences`, {
                method: "PUT",
                body: JSON.stringify({ layout: draft }),
            })) as DashboardWorkspaceData;
            setData(workspace);
            if (!customising) setDraft(workspace.layout);
            setCustomising(false);
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : "Unable to save dashboard layout.");
        } finally {
            setSaving(false);
        }
    }

    function renderWidget(key: string) {
        if (!data) return null;

        if (key === "my_tasks" && data.my_tasks) {
            return (
                <WidgetShell
                    title="My tasks"
                    description="Current work assigned to you."
                    href="/admin/tasks"
                >
                    <div className="grid grid-cols-3 gap-2">
                        <Metric label="Open" value={data.my_tasks.open_count} />
                        <Metric label="Today" value={data.my_tasks.today_count} />
                        <Metric
                            label="Overdue"
                            value={data.my_tasks.overdue_count}
                            warning={data.my_tasks.overdue_count > 0}
                        />
                    </div>
                    <TaskRows tasks={data.my_tasks.items} />
                </WidgetShell>
            );
        }

        if (key === "my_tickets" && data.my_tickets) {
            return (
                <WidgetShell
                    title="My tickets"
                    description="Actionable work inside your default Queue scope."
                    href="/admin/tickets"
                >
                    <div className="grid grid-cols-3 gap-2">
                        <Metric label="Mine" value={data.my_tickets.mine_count} />
                        <Metric
                            label="Unassigned"
                            value={data.my_tickets.unassigned_count}
                            warning={data.my_tickets.unassigned_count > 0}
                        />
                        <Metric label="Active" value={data.my_tickets.active_count} />
                    </div>
                    {data.my_tickets.items.length ? (
                        <div className="mt-4 divide-y divide-slate-800">
                            {data.my_tickets.items.map((ticket) => (
                                <div key={ticket.id} className="py-2.5">
                                    <div className="flex items-center justify-between gap-3">
                                        <p className="truncate text-sm font-medium text-slate-200">
                                            {ticket.subject}
                                        </p>
                                        <span className="shrink-0 text-xs text-slate-600">
                                            {ticket.reference}
                                        </span>
                                    </div>
                                    <p className="mt-1 truncate text-xs text-slate-600">
                                        {ticket.queue_name} · {ticket.client_name ?? "Internal"} ·{" "}
                                        {ticket.status.replaceAll("_", " ")}
                                    </p>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <Empty>No assigned actionable tickets.</Empty>
                    )}
                </WidgetShell>
            );
        }

        if (key === "active_timer" && data.active_timer) {
            return (
                <WidgetShell
                    title="Time"
                    description="Your current timer and this week's tracked work."
                    href="/admin/time-tracking"
                >
                    <div className="grid grid-cols-2 gap-2">
                        <Metric
                            label="This week"
                            value={`${data.active_timer.hours_this_week.toFixed(1)}h`}
                        />
                        <Metric
                            label="Timer"
                            value={data.active_timer.running ? "Running" : "Stopped"}
                            warning={data.active_timer.running}
                        />
                    </div>
                    <div className="mt-4 rounded-lg border border-slate-800 px-3 py-3 text-sm">
                        {data.active_timer.running ? (
                            <>
                                <p className="font-medium text-slate-200">
                                    {data.active_timer.context_label}
                                </p>
                                <p className="mt-1 text-xs text-slate-500">
                                    Started{" "}
                                    {data.active_timer.started_at
                                        ? formatDateTime(data.active_timer.started_at)
                                        : "recently"}
                                </p>
                                {data.active_timer.description ? (
                                    <p className="mt-2 text-xs text-slate-400">
                                        {data.active_timer.description}
                                    </p>
                                ) : null}
                            </>
                        ) : (
                            <p className="text-slate-500">No timer is currently running.</p>
                        )}
                    </div>
                </WidgetShell>
            );
        }

        if (key === "lead_follow_up" && data.lead_follow_up) {
            return (
                <WidgetShell
                    title="Lead follow-up"
                    description="Open sales Leads assigned to you."
                    href="/admin/leads"
                >
                    <Metric label="Open assigned leads" value={data.lead_follow_up.open_count} />
                    {data.lead_follow_up.items.length ? (
                        <div className="mt-4 divide-y divide-slate-800">
                            {data.lead_follow_up.items.map((lead) => (
                                <div key={lead.id} className="py-2.5">
                                    <p className="truncate text-sm font-medium text-slate-200">
                                        {lead.company || lead.name}
                                    </p>
                                    <p className="mt-1 truncate text-xs text-slate-600">
                                        {lead.brand} · {lead.status}
                                    </p>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <Empty>No assigned Leads need follow-up.</Empty>
                    )}
                </WidgetShell>
            );
        }

        if (key === "current_projects" && data.current_projects) {
            return (
                <WidgetShell
                    title="Current projects"
                    description="Current delivery work in your Client/Internal scope."
                    href="/admin/projects"
                >
                    <Metric label="Current" value={data.current_projects.current_count} />
                    {data.current_projects.items.length ? (
                        <div className="mt-4 divide-y divide-slate-800">
                            {data.current_projects.items.map((project) => (
                                <div
                                    key={project.id}
                                    className="flex items-center justify-between gap-3 py-2.5"
                                >
                                    <div className="min-w-0">
                                        <p className="truncate text-sm font-medium text-slate-200">
                                            {project.name}
                                        </p>
                                        <p className="mt-1 truncate text-xs text-slate-600">
                                            {project.client_name ?? "Internal"} · {project.status}
                                        </p>
                                    </div>
                                    <span className="shrink-0 text-xs text-slate-500">
                                        {project.end_date
                                            ? formatDate(project.end_date)
                                            : "Open-ended"}
                                    </span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <Empty>No current projects are visible.</Empty>
                    )}
                </WidgetShell>
            );
        }

        if (key === "technical_health" && data.technical_health) {
            return (
                <WidgetShell
                    title="Technical health"
                    description="Monitoring problems inside your Infrastructure scope."
                    href="/admin/monitoring"
                >
                    <div className="grid grid-cols-2 gap-2">
                        <Metric
                            label="Active incidents"
                            value={data.technical_health.active_incident_count}
                            warning={data.technical_health.active_incident_count > 0}
                        />
                        <Metric
                            label="Failing checks"
                            value={data.technical_health.failing_check_count}
                            warning={data.technical_health.failing_check_count > 0}
                        />
                    </div>
                    {data.technical_health.items.length ? (
                        <div className="mt-4 divide-y divide-slate-800">
                            {data.technical_health.items.map((incident) => (
                                <div key={incident.id} className="py-2.5">
                                    <div className="flex items-center justify-between gap-3">
                                        <p className="truncate text-sm font-medium text-slate-200">
                                            {incident.resource_name} · {incident.check_name}
                                        </p>
                                        <span className="shrink-0 text-xs uppercase text-amber-400">
                                            {incident.severity}
                                        </span>
                                    </div>
                                    <p className="mt-1 line-clamp-2 text-xs text-slate-600">
                                        {incident.summary}
                                    </p>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <Empty>No active monitoring incidents.</Empty>
                    )}
                </WidgetShell>
            );
        }

        if (key === "agenda" && data.agenda) {
            return (
                <WidgetShell
                    title="Agenda"
                    description="Your dated Tasks for today and the next seven days."
                    href="/admin/calendar"
                >
                    <div className="grid grid-cols-2 gap-2">
                        <Metric
                            label="Today"
                            value={data.agenda.today_count}
                            warning={data.agenda.today_count > 0}
                        />
                        <Metric label="Next 7 days" value={data.agenda.next_seven_days_count} />
                    </div>
                    <TaskRows tasks={data.agenda.items} />
                </WidgetShell>
            );
        }

        if (key === "recent_activity" && data.recent_activity) {
            return (
                <WidgetShell
                    title="Recent activity"
                    description="Safe audit events available to your account."
                >
                    {data.recent_activity.length ? (
                        <div className="divide-y divide-slate-800">
                            {data.recent_activity.map((activity) => (
                                <div
                                    key={activity.id}
                                    className="grid gap-1 py-2.5 sm:grid-cols-[minmax(0,1fr)_auto] sm:gap-4"
                                >
                                    <p className="truncate text-sm text-slate-300">
                                        <span className="font-medium text-slate-100">
                                            {activity.action}
                                        </span>{" "}
                                        {activity.target_label}
                                    </p>
                                    <span className="text-xs text-slate-600">
                                        {formatDateTime(activity.created_at)}
                                    </span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <Empty>No recent audit activity.</Empty>
                    )}
                </WidgetShell>
            );
        }

        return null;
    }

    return (
        <>
            {error ? (
                <div className="mb-5 rounded-xl border border-red-900/60 bg-red-950/30 px-4 py-3 text-sm text-red-300">
                    {error}
                </div>
            ) : null}

            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm text-slate-500">
                    Your layout is stored with your staff account and follows you between browsers.
                </p>
                <Button
                    type="button"
                    variant="secondary"
                    onClick={() => {
                        setDraft(data?.layout ?? []);
                        setCustomising((value) => !value);
                    }}
                >
                    <Cog6ToothIcon className="mr-2 h-4 w-4" />
                    {customising ? "Close customizer" : "Customize dashboard"}
                </Button>
            </div>

            {customising && data ? (
                <Card className="mb-6">
                    <CardHeader className="border-b border-slate-800">
                        <CardTitle>Dashboard layout</CardTitle>
                        <p className="mt-1 text-xs text-slate-500">
                            Enable the widgets you use, order them and choose their desktop width.
                            Only widgets you are authorised to view are offered.
                        </p>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-3 lg:grid-cols-2">
                            {data.available_widgets.map((option) => {
                                const index = draft.findIndex((item) => item.key === option.key);
                                const selected = index >= 0;
                                const preference = selected ? draft[index] : null;
                                return (
                                    <div
                                        key={option.key}
                                        className={`rounded-xl border p-4 ${
                                            selected
                                                ? "border-adb-cyan-800 bg-adb-cyan-950/10"
                                                : "border-slate-800"
                                        }`}
                                    >
                                        <div className="flex items-start gap-3">
                                            <input
                                                type="checkbox"
                                                checked={selected}
                                                onChange={() => toggleWidget(option)}
                                                className="mt-1 rounded border-slate-600 bg-slate-900 text-adb-cyan-500 focus:ring-adb-cyan-500"
                                            />
                                            <div className="min-w-0 flex-1">
                                                <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                                                    {widgetIcons[option.key]}
                                                    {option.title}
                                                </div>
                                                <p className="mt-1 text-xs leading-5 text-slate-500">
                                                    {option.description}
                                                </p>
                                                {selected && preference ? (
                                                    <div className="mt-3 flex flex-wrap items-center gap-2">
                                                        <select
                                                            value={preference.span}
                                                            onChange={(event) =>
                                                                changeSpan(
                                                                    option.key,
                                                                    Number(event.target.value),
                                                                )
                                                            }
                                                            className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2 text-xs text-slate-200"
                                                        >
                                                            <option value={4}>One third</option>
                                                            <option value={6}>Half</option>
                                                            <option value={8}>Two thirds</option>
                                                            <option value={12}>Full width</option>
                                                        </select>
                                                        <Button
                                                            type="button"
                                                            size="sm"
                                                            variant="secondary"
                                                            disabled={index === 0}
                                                            onClick={() => moveWidget(index, -1)}
                                                            aria-label={`Move ${option.title} up`}
                                                        >
                                                            <ArrowUpIcon className="h-4 w-4" />
                                                        </Button>
                                                        <Button
                                                            type="button"
                                                            size="sm"
                                                            variant="secondary"
                                                            disabled={index === draft.length - 1}
                                                            onClick={() => moveWidget(index, 1)}
                                                            aria-label={`Move ${option.title} down`}
                                                        >
                                                            <ArrowDownIcon className="h-4 w-4" />
                                                        </Button>
                                                    </div>
                                                ) : null}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                        <div className="mt-5 flex flex-wrap justify-end gap-3 border-t border-slate-800 pt-4">
                            <Button
                                type="button"
                                variant="secondary"
                                onClick={() =>
                                    setDraft(
                                        data.available_widgets.map((option) => ({
                                            key: option.key,
                                            span: option.default_span,
                                        })),
                                    )
                                }
                            >
                                Recommended layout
                            </Button>
                            <Button type="button" disabled={saving} onClick={() => void saveLayout()}>
                                {saving ? "Saving…" : "Save layout"}
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            ) : null}

            {!data ? (
                <div className="rounded-xl border border-slate-800 bg-slate-900/50 px-5 py-12 text-center text-sm text-slate-500">
                    Loading your dashboard…
                </div>
            ) : null}

            {data && data.layout.length === 0 ? (
                <Card>
                    <CardContent className="py-12 text-center">
                        <p className="text-sm font-medium text-slate-300">Your dashboard is empty.</p>
                        <p className="mt-2 text-xs text-slate-500">
                            Use Customize dashboard to add the work surfaces you want here.
                        </p>
                    </CardContent>
                </Card>
            ) : null}

            {data ? (
                <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
                    {data.layout.map((item) => (
                        <div
                            key={item.key}
                            className={spanClass[item.span] ?? "xl:col-span-6"}
                        >
                            {renderWidget(item.key)}
                        </div>
                    ))}
                </div>
            ) : null}
        </>
    );
}
