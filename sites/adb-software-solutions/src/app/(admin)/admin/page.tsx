"use client";

import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Container,
    PageHeader,
    StatCard,
} from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import {
    BuildingOffice2Icon,
    CalendarDaysIcon,
    ClockIcon,
    ExclamationTriangleIcon,
    FolderIcon,
    ListBulletIcon,
    MegaphoneIcon,
    ServerStackIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";
import { useEffect, useState } from "react";

interface DashboardLead {
    id: number;
    name: string;
    company: string;
    status: string;
    brand: string;
    created_at: string;
}

interface DashboardTask {
    id: number;
    title: string;
    status: string;
    priority: number;
    due_date: string | null;
}

interface DashboardActivity {
    id: number;
    action: string;
    target_label: string;
    created_at: string;
}

interface DashboardSummary {
    active_clients: number;
    active_projects: number;
    open_leads: number;
    open_tasks: number;
    overdue_tasks: number;
    hours_this_week: number;
    expiring_domains: number;
    renewing_licences: number;
    recent_leads: DashboardLead[];
    upcoming_tasks: DashboardTask[];
    recent_activity: DashboardActivity[];
}

function formatDate(value: string | null) {
    if (!value) return "No due date";
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

export default function AdminDashboard() {
    const [summary, setSummary] = useState<DashboardSummary | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let active = true;
        void fetchAPI(AdminAPI.dashboard.summary())
            .then((data) => {
                if (active) setSummary(data as DashboardSummary);
            })
            .catch((reason: unknown) => {
                if (!active) return;
                setError(
                    reason instanceof Error
                        ? reason.message
                        : "Unable to load dashboard data",
                );
            });
        return () => {
            active = false;
        };
    }, []);

    return (
        <Container className="py-6 lg:py-8">
            <PageHeader
                eyebrow="Operations"
                title="Dashboard"
                description="What needs attention across clients, projects, sales and infrastructure."
            />

            {error ? (
                <div className="mt-6 rounded-xl border border-red-900/60 bg-red-950/30 px-4 py-3 text-sm text-red-300">
                    {error}
                </div>
            ) : null}

            <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard
                    label="Active clients"
                    value={summary ? String(summary.active_clients) : "—"}
                    helper="Within your access scope"
                    icon={<BuildingOffice2Icon className="h-5 w-5" />}
                />
                <StatCard
                    label="Active projects"
                    value={summary ? String(summary.active_projects) : "—"}
                    helper="Currently in delivery"
                    icon={<FolderIcon className="h-5 w-5" />}
                />
                <StatCard
                    label="Open leads"
                    value={summary ? String(summary.open_leads) : "—"}
                    helper="Excludes won and lost"
                    icon={<MegaphoneIcon className="h-5 w-5" />}
                />
                <StatCard
                    label="Hours this week"
                    value={summary ? summary.hours_this_week.toFixed(1) : "—"}
                    helper="Tracked against accessible projects"
                    icon={<ClockIcon className="h-5 w-5" />}
                />
            </div>

            <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard
                    label="Open tasks"
                    value={summary ? String(summary.open_tasks) : "—"}
                    helper={summary ? `${summary.overdue_tasks} overdue` : undefined}
                    icon={<ListBulletIcon className="h-5 w-5" />}
                    accent={summary && summary.overdue_tasks > 0 ? "red" : "cyan"}
                />
                <StatCard
                    label="Domains expiring"
                    value={summary ? String(summary.expiring_domains) : "—"}
                    helper="Within the next 45 days"
                    icon={<ServerStackIcon className="h-5 w-5" />}
                    accent={summary && summary.expiring_domains > 0 ? "amber" : "slate"}
                />
                <StatCard
                    label="Licence renewals"
                    value={summary ? String(summary.renewing_licences) : "—"}
                    helper="Within the next 45 days"
                    icon={<CalendarDaysIcon className="h-5 w-5" />}
                    accent={summary && summary.renewing_licences > 0 ? "amber" : "slate"}
                />
                <StatCard
                    label="Overdue work"
                    value={summary ? String(summary.overdue_tasks) : "—"}
                    helper="Tasks requiring attention"
                    icon={<ExclamationTriangleIcon className="h-5 w-5" />}
                    accent={summary && summary.overdue_tasks > 0 ? "red" : "green"}
                />
            </div>

            <div className="mt-6 grid gap-4 xl:grid-cols-12">
                <Card className="xl:col-span-7">
                    <CardHeader className="flex flex-row items-center justify-between gap-4 border-b border-slate-800">
                        <div>
                            <CardTitle>Upcoming work</CardTitle>
                            <p className="mt-1 text-xs text-slate-500">
                                Nearest due tasks across the platform.
                            </p>
                        </div>
                        <Link
                            href="/admin/tasks"
                            className="text-xs font-medium text-adb-cyan-400 hover:text-adb-cyan-300"
                        >
                            View tasks
                        </Link>
                    </CardHeader>
                    <CardContent className="p-0">
                        {summary?.upcoming_tasks.length ? (
                            <div className="divide-y divide-slate-800">
                                {summary.upcoming_tasks.map((task) => (
                                    <div
                                        key={task.id}
                                        className="flex items-center gap-4 px-5 py-3.5"
                                    >
                                        <span
                                            className={`h-2 w-2 shrink-0 rounded-full ${
                                                task.priority >= 4
                                                    ? "bg-red-400"
                                                    : task.priority === 3
                                                      ? "bg-yellow-400"
                                                      : "bg-slate-600"
                                            }`}
                                        />
                                        <div className="min-w-0 flex-1">
                                            <p className="truncate text-sm font-medium text-slate-200">
                                                {task.title}
                                            </p>
                                            <p className="mt-0.5 text-xs text-slate-600">
                                                {task.status}
                                            </p>
                                        </div>
                                        <div className="text-xs text-slate-500">
                                            {formatDate(task.due_date)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="px-5 py-10 text-center text-sm text-slate-600">
                                No upcoming tasks to show.
                            </div>
                        )}
                    </CardContent>
                </Card>

                <Card className="xl:col-span-5">
                    <CardHeader className="flex flex-row items-center justify-between gap-4 border-b border-slate-800">
                        <div>
                            <CardTitle>Recent leads</CardTitle>
                            <p className="mt-1 text-xs text-slate-500">
                                Latest sales activity across the ADB brands.
                            </p>
                        </div>
                        <Link
                            href="/admin/leads"
                            className="text-xs font-medium text-adb-cyan-400 hover:text-adb-cyan-300"
                        >
                            View CRM
                        </Link>
                    </CardHeader>
                    <CardContent className="p-0">
                        {summary?.recent_leads.length ? (
                            <div className="divide-y divide-slate-800">
                                {summary.recent_leads.map((lead) => (
                                    <div key={lead.id} className="px-5 py-3.5">
                                        <div className="flex items-start justify-between gap-3">
                                            <div className="min-w-0">
                                                <p className="truncate text-sm font-medium text-slate-200">
                                                    {lead.company || lead.name}
                                                </p>
                                                <p className="mt-0.5 truncate text-xs text-slate-600">
                                                    {lead.brand} · {lead.name}
                                                </p>
                                            </div>
                                            <span className="rounded-md bg-slate-800 px-2 py-1 text-[10px] font-semibold text-slate-400">
                                                {lead.status}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="px-5 py-10 text-center text-sm text-slate-600">
                                No recent leads to show.
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            <Card className="mt-4">
                <CardHeader className="border-b border-slate-800">
                    <CardTitle>Recent activity</CardTitle>
                    <p className="mt-1 text-xs text-slate-500">
                        Security-sensitive and operational changes visible to you.
                    </p>
                </CardHeader>
                <CardContent className="p-0">
                    {summary?.recent_activity.length ? (
                        <div className="divide-y divide-slate-800">
                            {summary.recent_activity.map((activity) => (
                                <div
                                    key={activity.id}
                                    className="grid gap-1 px-5 py-3.5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:gap-4"
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
                        <div className="px-5 py-10 text-center text-sm text-slate-600">
                            No recent activity is available for your account.
                        </div>
                    )}
                </CardContent>
            </Card>
        </Container>
    );
}
