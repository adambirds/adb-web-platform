"use client";

import { Badge, ButtonLink, Card, DataError, DataLoading } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

interface ProjectDetail {
    id: number;
    name: string;
    description: string;
    status: string;
    ownership_type: string;
    client_id: number | null;
    client_name: string | null;
    start_date: string;
    end_date: string | null;
    budget: string | null;
    hourly_rate: string | null;
    created_at: string;
    updated_at: string;
    task_count: number;
    open_task_count: number;
    time_entry_count: number;
    tracked_hours: string;
    billable_hours: string;
    can_change: boolean;
}

function statusClasses(status: string) {
    if (status === "active") {
        return "border-emerald-900/70 bg-emerald-950/50 text-emerald-300";
    }
    if (status === "paused") {
        return "border-amber-900/70 bg-amber-950/40 text-amber-300";
    }
    if (status === "completed") {
        return "border-cyan-900/70 bg-cyan-950/40 text-cyan-300";
    }
    if (status === "planning") {
        return "border-indigo-900/70 bg-indigo-950/40 text-indigo-300";
    }
    return "border-slate-700 bg-slate-900 text-slate-400";
}

function formatDate(value: string | null) {
    if (!value) return "—";
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    }).format(new Date(`${value}T00:00:00`));
}

function formatDateTime(value: string) {
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    }).format(new Date(value));
}

function formatMoney(value: string | null) {
    if (!value) return "—";
    return new Intl.NumberFormat("en-GB", {
        style: "currency",
        currency: "GBP",
    }).format(Number(value));
}

function formatHours(value: string) {
    return `${Number(value).toLocaleString("en-GB", { maximumFractionDigits: 2 })}h`;
}

export function ProjectWorkspace({ projectId }: { projectId: number }) {
    const [project, setProject] = useState<ProjectDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadProject = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const data = (await fetchAPI(AdminAPI.projects.get(projectId))) as ProjectDetail;
            setProject(data);
        } catch (loadError) {
            setError(
                loadError instanceof Error ? loadError.message : "Unable to load project details.",
            );
        } finally {
            setIsLoading(false);
        }
    }, [projectId]);

    useEffect(() => {
        void loadProject();
    }, [loadProject]);

    if (isLoading) return <DataLoading label="Loading project..." />;
    if (error || !project) {
        return (
            <DataError
                message={error || "Project could not be loaded."}
                onRetry={() => void loadProject()}
            />
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                    <Link
                        href="/admin/projects"
                        className="text-xs text-slate-500 hover:text-slate-300"
                    >
                        ← Projects
                    </Link>
                    <div className="mt-2 flex flex-wrap items-center gap-3">
                        <h1 className="text-2xl font-semibold text-white">{project.name}</h1>
                        <Badge className={statusClasses(project.status)}>{project.status}</Badge>
                        <Badge>
                            {project.ownership_type === "internal" ? "Internal" : "Client"}
                        </Badge>
                    </div>
                    <p className="mt-1 text-sm text-slate-400">
                        {project.client_name || "ADB Internal"}
                    </p>
                </div>
                <div className="flex flex-wrap gap-2">
                    {project.client_id ? (
                        <ButtonLink href={`/admin/clients/${project.client_id}`} variant="outline">
                            View client
                        </ButtonLink>
                    ) : null}
                    {project.can_change ? (
                        <ButtonLink href={`/admin/projects/${project.id}/edit`} variant="secondary">
                            Edit project
                        </ButtonLink>
                    ) : null}
                </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
                <Card className="p-5 lg:col-span-2">
                    <h2 className="text-sm font-semibold text-white">Project details</h2>
                    <dl className="mt-4 grid gap-4 text-sm sm:grid-cols-2">
                        <div>
                            <dt className="text-xs text-slate-500">Owner</dt>
                            <dd className="mt-1 text-slate-300">
                                {project.client_name || "ADB Internal"}
                            </dd>
                        </div>
                        <div>
                            <dt className="text-xs text-slate-500">Status</dt>
                            <dd className="mt-1 capitalize text-slate-300">{project.status}</dd>
                        </div>
                        <div>
                            <dt className="text-xs text-slate-500">Start date</dt>
                            <dd className="mt-1 text-slate-300">{formatDate(project.start_date)}</dd>
                        </div>
                        <div>
                            <dt className="text-xs text-slate-500">End date</dt>
                            <dd className="mt-1 text-slate-300">{formatDate(project.end_date)}</dd>
                        </div>
                        <div>
                            <dt className="text-xs text-slate-500">Budget</dt>
                            <dd className="mt-1 text-slate-300">{formatMoney(project.budget)}</dd>
                        </div>
                        <div>
                            <dt className="text-xs text-slate-500">Hourly rate</dt>
                            <dd className="mt-1 text-slate-300">
                                {formatMoney(project.hourly_rate)}
                            </dd>
                        </div>
                    </dl>
                </Card>

                <Card className="p-5">
                    <h2 className="text-sm font-semibold text-white">Record</h2>
                    <dl className="mt-4 space-y-4 text-sm">
                        <div>
                            <dt className="text-xs text-slate-500">Created</dt>
                            <dd className="mt-1 text-slate-300">
                                {formatDateTime(project.created_at)}
                            </dd>
                        </div>
                        <div>
                            <dt className="text-xs text-slate-500">Last updated</dt>
                            <dd className="mt-1 text-slate-300">
                                {formatDateTime(project.updated_at)}
                            </dd>
                        </div>
                    </dl>
                </Card>
            </div>

            <Card className="p-5">
                <h2 className="text-sm font-semibold text-white">Description</h2>
                <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-300">
                    {project.description || "No project description has been recorded yet."}
                </p>
            </Card>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <Card className="p-5">
                    <div className="text-xs uppercase tracking-wide text-slate-500">Tasks</div>
                    <div className="mt-2 text-2xl font-semibold text-white">{project.task_count}</div>
                    <div className="mt-1 text-xs text-slate-500">
                        {project.open_task_count} currently open
                    </div>
                </Card>
                <Card className="p-5">
                    <div className="text-xs uppercase tracking-wide text-slate-500">Time entries</div>
                    <div className="mt-2 text-2xl font-semibold text-white">
                        {project.time_entry_count}
                    </div>
                    <div className="mt-1 text-xs text-slate-500">Recorded against this project</div>
                </Card>
                <Card className="p-5">
                    <div className="text-xs uppercase tracking-wide text-slate-500">Tracked time</div>
                    <div className="mt-2 text-2xl font-semibold text-white">
                        {formatHours(project.tracked_hours)}
                    </div>
                    <div className="mt-1 text-xs text-slate-500">Total recorded hours</div>
                </Card>
                <Card className="p-5">
                    <div className="text-xs uppercase tracking-wide text-slate-500">Billable time</div>
                    <div className="mt-2 text-2xl font-semibold text-white">
                        {formatHours(project.billable_hours)}
                    </div>
                    <div className="mt-1 text-xs text-slate-500">Billable recorded hours</div>
                </Card>
            </div>
        </div>
    );
}
