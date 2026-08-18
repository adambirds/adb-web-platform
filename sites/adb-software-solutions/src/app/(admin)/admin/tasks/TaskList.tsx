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
import { useCallback, useEffect, useState } from "react";

interface TaskSummary {
    id: number;
    title: string;
    status: string;
    priority: number;
    due_date: string | null;
    ownership_type: string;
    client_name: string | null;
    project_name: string | null;
    task_list_name: string | null;
}

const priorityLabels: Record<number, string> = {
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Critical",
};

function priorityClasses(priority: number) {
    if (priority === 4) {
        return "border-red-950 bg-red-950/30 text-red-300";
    }
    if (priority === 3) {
        return "border-amber-900/70 bg-amber-950/40 text-amber-300";
    }
    return "border-slate-700 bg-slate-900 text-slate-400";
}

function formatDate(value: string | null) {
    if (!value) return "No due date";
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    }).format(new Date(`${value}T00:00:00`));
}

function isOverdue(value: string | null, status: string) {
    if (!value || status.toLowerCase() === "done") return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return new Date(`${value}T00:00:00`) < today;
}

export function TaskList() {
    const [tasks, setTasks] = useState<TaskSummary[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadTasks = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const data = (await fetchAPI(AdminAPI.tasks.list())) as TaskSummary[];
            setTasks(data);
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "An unexpected error occurred while loading tasks.",
            );
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        void loadTasks();
    }, [loadTasks]);

    if (isLoading) {
        return <DataLoading label="Loading operational tasks..." />;
    }

    if (error) {
        return <DataError message={error} onRetry={() => void loadTasks()} />;
    }

    if (tasks.length === 0) {
        return (
            <EmptyState
                title="No tasks in your scope"
                description="Standalone internal work and client or project tasks will appear here as they are created."
            />
        );
    }

    return (
        <Table>
            <TableHead>
                <tr>
                    <TableHeaderCell>Task</TableHeaderCell>
                    <TableHeaderCell>Status</TableHeaderCell>
                    <TableHeaderCell>Priority</TableHeaderCell>
                    <TableHeaderCell>Context</TableHeaderCell>
                    <TableHeaderCell>Due</TableHeaderCell>
                </tr>
            </TableHead>
            <TableBody>
                {tasks.map((task) => {
                    const overdue = isOverdue(task.due_date, task.status);
                    return (
                        <TableRow key={task.id}>
                            <TableCell>
                                <div className="font-medium text-slate-100">
                                    {task.title}
                                </div>
                                {task.task_list_name ? (
                                    <div className="mt-1 text-xs text-slate-500">
                                        {task.task_list_name}
                                    </div>
                                ) : null}
                            </TableCell>
                            <TableCell className="text-slate-400">
                                {task.status}
                            </TableCell>
                            <TableCell>
                                <Badge className={priorityClasses(task.priority)}>
                                    {priorityLabels[task.priority] ?? "Unknown"}
                                </Badge>
                            </TableCell>
                            <TableCell>
                                <div className="text-slate-300">
                                    {task.project_name ||
                                        task.client_name ||
                                        "ADB Internal"}
                                </div>
                                <div className="mt-1 text-xs text-slate-500">
                                    {task.ownership_type === "internal"
                                        ? "Internal"
                                        : task.project_name
                                          ? "Project"
                                          : "Client"}
                                </div>
                            </TableCell>
                            <TableCell
                                className={
                                    overdue
                                        ? "font-medium text-red-300"
                                        : "text-slate-400"
                                }
                            >
                                {formatDate(task.due_date)}
                                {overdue ? (
                                    <div className="mt-1 text-xs text-red-400/70">
                                        Overdue
                                    </div>
                                ) : null}
                            </TableCell>
                        </TableRow>
                    );
                })}
            </TableBody>
        </Table>
    );
}
