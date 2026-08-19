"use client";

import {
    Badge,
    DataError,
    DataLoading,
    EmptyState,
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
import { useCallback, useEffect, useState } from "react";

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

function formatBudget(value: string | null) {
    if (!value) return "—";
    return new Intl.NumberFormat("en-GB", {
        style: "currency",
        currency: "GBP",
        maximumFractionDigits: 0,
    }).format(Number(value));
}

export function ProjectList() {
    const [projects, setProjects] = useState<ProjectSummary[]>([]);
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

    useEffect(() => {
        void loadProjects();
    }, [loadProjects]);

    if (isLoading) {
        return <DataLoading label="Loading operational projects..." />;
    }

    if (error) {
        return <DataError message={error} onRetry={() => void loadProjects()} />;
    }

    if (projects.length === 0) {
        return (
            <EmptyState
                title="No projects in your scope"
                description="Create a client or internal project to start tracking delivery work."
            />
        );
    }

    return (
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
                {projects.map((project) => (
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
    );
}
