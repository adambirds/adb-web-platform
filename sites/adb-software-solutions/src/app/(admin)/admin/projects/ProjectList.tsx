"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";

import {
    Badge,
    DataError,
    DataLoading,
    EmptyState,
    Select,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeaderCell,
    TableRow,
} from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

interface ProjectSummary {
    id: number;
    name: string;
    status: string;
    ownership_type: string;
    client_id: number | null;
    client_name: string | null;
    start_date: string;
    end_date: string | null;
    budget: string | null;
}

type ProjectView = "current" | "completed" | "archived" | "all";

const CURRENT_STATUSES = new Set(["planning", "active", "paused"]);

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
    return "border-slate-700 bg-slate-900 text-slate-500";
}

function formatDate(value: string | null) {
    if (!value) return "—";
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    }).format(new Date(`${value}T00:00:00`));
}

function formatBudget(value: string | null) {
    if (!value) return "—";
    return new Intl.NumberFormat("en-GB", {
        style: "currency",
        currency: "GBP",
        maximumFractionDigits: 0,
    }).format(Number(value));
}

function viewDescription(view: ProjectView) {
    if (view === "completed") return "Completed project history.";
    if (view === "archived") return "Archived projects retained for historical reference.";
    if (view === "all") return "All current and historical projects in your scope.";
    return "Planning, active and paused projects that still belong in your day-to-day work.";
}

export function ProjectList() {
    const [projects, setProjects] = useState<ProjectSummary[]>([]);
    const [view, setView] = useState<ProjectView>("current");
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadProjects = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const data = (await fetchAPI(AdminAPI.projects.list())) as ProjectSummary[];
            setProjects(data);
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "An unexpected error occurred while loading projects.",
            );
        } finally {
            setIsLoading(false);
        }
    }, []);

    useLiveRefresh(["projects"], loadProjects);

    useEffect(() => {
        void loadProjects();
    }, [loadProjects]);

    const visibleProjects = useMemo(() => {
        if (view === "all") return projects;
        if (view === "current") {
            return projects.filter((project) => CURRENT_STATUSES.has(project.status));
        }
        return projects.filter((project) => project.status === view);
    }, [projects, view]);

    if (isLoading) {
        return <DataLoading label="Loading operational projects..." />;
    }

    if (error) {
        return <DataError message={error} onRetry={() => void loadProjects()} />;
    }

    return (
        <div className="space-y-4">
            <div className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-950/60 p-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                    <div className="text-sm font-medium text-slate-200">
                        {view === "current"
                            ? "Current projects"
                            : view === "completed"
                              ? "Completed projects"
                              : view === "archived"
                                ? "Archived projects"
                                : "All projects"}
                    </div>
                    <p className="mt-1 text-xs text-slate-500">{viewDescription(view)}</p>
                </div>
                <label className="w-full space-y-1.5 text-xs text-slate-500 sm:w-56">
                    <span>Project view</span>
                    <Select
                        value={view}
                        onChange={(event) => setView(event.target.value as ProjectView)}
                    >
                        <option value="current">Current projects</option>
                        <option value="completed">Completed</option>
                        <option value="archived">Archived</option>
                        <option value="all">All projects</option>
                    </Select>
                </label>
            </div>

            {view !== "current" ? (
                <div className="rounded-lg border border-slate-800 bg-slate-900/30 px-4 py-2 text-xs text-slate-500">
                    Historical project records are visible because you selected a history view.
                </div>
            ) : null}

            {visibleProjects.length === 0 ? (
                <EmptyState
                    title={view === "current" ? "No current projects in your scope" : "No projects in this view"}
                    description={
                        view === "current"
                            ? "Create a client or internal project to start tracking delivery work."
                            : "Choose another project view to see different project history."
                    }
                />
            ) : (
                <Table>
                    <TableHead>
                        <tr>
                            <TableHeaderCell>Project</TableHeaderCell>
                            <TableHeaderCell>Owner</TableHeaderCell>
                            <TableHeaderCell>Status</TableHeaderCell>
                            <TableHeaderCell>Start</TableHeaderCell>
                            <TableHeaderCell>End</TableHeaderCell>
                            <TableHeaderCell className="text-right">Budget</TableHeaderCell>
                        </tr>
                    </TableHead>
                    <TableBody>
                        {visibleProjects.map((project) => (
                            <TableRow key={project.id}>
                                <TableCell>
                                    <Link
                                        href={`/admin/projects/${project.id}`}
                                        className="font-medium text-slate-100 hover:text-adb-cyan-300"
                                    >
                                        {project.name}
                                    </Link>
                                    <div className="mt-1 text-xs text-slate-500">
                                        {project.ownership_type === "internal"
                                            ? "Internal project"
                                            : "Client project"}
                                    </div>
                                </TableCell>
                                <TableCell className="text-slate-400">
                                    {project.client_name || "ADB Internal"}
                                </TableCell>
                                <TableCell>
                                    <Badge className={statusClasses(project.status)}>
                                        {project.status}
                                    </Badge>
                                </TableCell>
                                <TableCell className="text-slate-400">
                                    {formatDate(project.start_date)}
                                </TableCell>
                                <TableCell className="text-slate-400">
                                    {formatDate(project.end_date)}
                                </TableCell>
                                <TableCell className="text-right font-medium tabular-nums text-slate-300">
                                    {formatBudget(project.budget)}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            )}
        </div>
    );
}
