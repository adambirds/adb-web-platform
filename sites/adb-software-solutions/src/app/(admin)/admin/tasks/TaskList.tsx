"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";

import { TaskCompletionToggle } from "@/components/admin/TaskCompletionToggle";
import {
    Badge,
    ButtonLink,
    DataError,
    DataLoading,
    EmptyState,
    Input,
    Pagination,
    Select,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

type FocusView = "my" | "today" | "upcoming" | "overdue" | "completed" | "all";

interface TaskSummary {
    id: number;
    title: string;
    status: string;
    priority: number;
    due_date: string | null;
    completed_at: string | null;
    ownership_type: string;
    client_name: string | null;
    project_name: string | null;
    task_list_name: string | null;
    assigned_to_name: string | null;
    recurrence_frequency: string;
}

interface FocusCounts {
    my: number;
    today: number;
    upcoming: number;
    overdue: number;
    completed: number;
}

interface TaskFocusPage {
    focus: FocusView;
    items: TaskSummary[];
    total: number;
    page: number;
    page_size: number;
    counts: FocusCounts;
}

const PAGE_SIZE = 40;

const focusOptions: Array<{
    value: Exclude<FocusView, "all">;
    label: string;
    description: string;
}> = [
    { value: "my", label: "My tasks", description: "Open work assigned to you" },
    { value: "today", label: "Today", description: "Due today" },
    { value: "upcoming", label: "Upcoming", description: "Due after today" },
    { value: "overdue", label: "Overdue", description: "Past due" },
    { value: "completed", label: "Completed", description: "Your completed work" },
];

const priorityLabels: Record<number, string> = {
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Critical",
};

function priorityClasses(priority: number) {
    if (priority === 4) return "border-red-950 bg-red-950/30 text-red-300";
    if (priority === 3) return "border-amber-900/70 bg-amber-950/40 text-amber-300";
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

function isOverdue(task: TaskSummary) {
    if (!task.due_date || task.completed_at) return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return new Date(`${task.due_date}T00:00:00`) < today;
}

function validFocus(value: string | null): FocusView {
    if (
        value === "today" ||
        value === "upcoming" ||
        value === "overdue" ||
        value === "completed" ||
        value === "all"
    ) {
        return value;
    }
    return "my";
}

function focusHref(view: FocusView) {
    return view === "my" ? "/admin/tasks" : `/admin/tasks?view=${view}`;
}

export function TaskList() {
    const searchParams = useSearchParams();
    const { hasPermission } = useAuth();
    const focus = validFocus(searchParams.get("view"));
    const [pageData, setPageData] = useState<TaskFocusPage | null>(null);
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");
    const [ownership, setOwnership] = useState("");
    const [allCompletion, setAllCompletion] = useState("open");
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setPage(1);
    }, [focus]);

    const query = useMemo(() => {
        const params = new URLSearchParams({
            focus,
            page: String(page),
            page_size: String(PAGE_SIZE),
        });
        if (search.trim()) params.set("search", search.trim());
        if (ownership) params.set("ownership_type", ownership);
        if (focus === "all") {
            if (allCompletion === "open") params.set("completed", "false");
            if (allCompletion === "completed") params.set("completed", "true");
        }
        return params.toString();
    }, [allCompletion, focus, ownership, page, search]);

    const loadTasks = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const data = (await fetchAPI(`${API_URL}/api/admin/task-focus?${query}`)) as TaskFocusPage;
            setPageData(data);
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "An unexpected error occurred while loading tasks.",
            );
        } finally {
            setIsLoading(false);
        }
    }, [query]);

    useEffect(() => {
        void loadTasks();
    }, [loadTasks]);
    useLiveRefresh(["tasks"], loadTasks);

    const activeOption = focusOptions.find((option) => option.value === focus);
    const heading = focus === "all" ? "All tasks" : activeOption?.label || "My tasks";
    const description =
        focus === "all"
            ? "Search and manage work across every client, project and internal workspace in your scope."
            : activeOption?.description || "Open work assigned to you";

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                <div>
                    <h2 className="text-xl font-semibold text-white">{heading}</h2>
                    <p className="mt-1 text-sm text-slate-500">{description}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                    <ButtonLink href="/admin/task-lists" variant="outline">
                        Task lists
                    </ButtonLink>
                    <ButtonLink href="/admin/tasks/new">Add task</ButtonLink>
                </div>
            </div>

            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-6">
                {focusOptions.map((option) => {
                    const active = focus === option.value;
                    const count = pageData?.counts[option.value] ?? null;
                    return (
                        <Link
                            key={option.value}
                            href={focusHref(option.value)}
                            className={`rounded-xl border px-4 py-3 transition ${
                                active
                                    ? "border-adb-cyan-500/50 bg-adb-cyan-500/10"
                                    : "border-slate-800 bg-slate-900/50 hover:border-slate-700 hover:bg-slate-900"
                            }`}
                        >
                            <div className="flex items-center justify-between gap-3">
                                <span
                                    className={
                                        active
                                            ? "text-sm font-semibold text-white"
                                            : "text-sm font-medium text-slate-300"
                                    }
                                >
                                    {option.label}
                                </span>
                                {count !== null ? (
                                    <span className="rounded-full bg-slate-950 px-2 py-0.5 text-xs tabular-nums text-slate-500">
                                        {count}
                                    </span>
                                ) : null}
                            </div>
                            <div className="mt-1 text-xs text-slate-600">{option.description}</div>
                        </Link>
                    );
                })}
                <Link
                    href={focusHref("all")}
                    className={`rounded-xl border px-4 py-3 transition ${
                        focus === "all"
                            ? "border-adb-cyan-500/50 bg-adb-cyan-500/10"
                            : "border-slate-800 bg-slate-900/50 hover:border-slate-700 hover:bg-slate-900"
                    }`}
                >
                    <div
                        className={
                            focus === "all"
                                ? "text-sm font-semibold text-white"
                                : "text-sm font-medium text-slate-300"
                        }
                    >
                        All tasks
                    </div>
                    <div className="mt-1 text-xs text-slate-600">Everything in your scope</div>
                </Link>
            </div>

            <div
                className={`grid gap-3 ${focus === "all" ? "md:grid-cols-3" : "md:grid-cols-2"}`}
            >
                <label className="space-y-1 text-xs font-medium text-slate-400">
                    <span>Search</span>
                    <Input
                        value={search}
                        onChange={(event) => {
                            setSearch(event.target.value);
                            setPage(1);
                        }}
                        placeholder="Search tasks..."
                    />
                </label>
                <label className="space-y-1 text-xs font-medium text-slate-400">
                    <span>Ownership</span>
                    <Select
                        value={ownership}
                        onChange={(event) => {
                            setOwnership(event.target.value);
                            setPage(1);
                        }}
                    >
                        <option value="">All work</option>
                        <option value="internal">ADB Internal</option>
                        <option value="client">Client</option>
                    </Select>
                </label>
                {focus === "all" ? (
                    <label className="space-y-1 text-xs font-medium text-slate-400">
                        <span>State</span>
                        <Select
                            value={allCompletion}
                            onChange={(event) => {
                                setAllCompletion(event.target.value);
                                setPage(1);
                            }}
                        >
                            <option value="open">Open</option>
                            <option value="completed">Completed</option>
                            <option value="all">All</option>
                        </Select>
                    </label>
                ) : null}
            </div>

            {isLoading && !pageData ? <DataLoading label="Loading your work..." /> : null}
            {error ? <DataError message={error} onRetry={() => void loadTasks()} /> : null}

            {!error && pageData && pageData.items.length === 0 ? (
                <EmptyState
                    title={`No ${heading.toLowerCase()} to show`}
                    description={
                        focus === "my"
                            ? "Nothing open is assigned to you right now."
                            : "There are no tasks matching this view and the current filters."
                    }
                />
            ) : null}

            {!error && pageData && pageData.items.length > 0 ? (
                <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950/40">
                    <div className="grid grid-cols-[2.5rem_minmax(0,1fr)] border-b border-slate-800 bg-slate-900/60 px-4 py-2 text-[11px] font-semibold uppercase tracking-wide text-slate-600 lg:grid-cols-[2.5rem_minmax(0,1fr)_9rem_8rem_9rem]">
                        <span />
                        <span>Task</span>
                        <span className="hidden lg:block">Priority</span>
                        <span className="hidden lg:block">Assigned</span>
                        <span className="hidden lg:block">Due</span>
                    </div>
                    <div className="divide-y divide-slate-800">
                        {pageData.items.map((task) => {
                            const overdue = isOverdue(task);
                            return (
                                <div
                                    key={task.id}
                                    className="grid grid-cols-[2.5rem_minmax(0,1fr)] items-center px-4 py-3 transition hover:bg-slate-900/60 lg:grid-cols-[2.5rem_minmax(0,1fr)_9rem_8rem_9rem]"
                                >
                                    <TaskCompletionToggle
                                        taskId={task.id}
                                        completed={Boolean(task.completed_at)}
                                        canChange={hasPermission("tasks.change_task")}
                                        onChanged={loadTasks}
                                    />

                                    <div className="min-w-0 pr-4">
                                        <div className="flex flex-wrap items-center gap-2">
                                            <Link
                                                href={`/admin/tasks/${task.id}`}
                                                className={`truncate font-medium hover:text-adb-cyan-300 ${
                                                    task.completed_at
                                                        ? "text-slate-500 line-through"
                                                        : "text-slate-100"
                                                }`}
                                            >
                                                {task.title}
                                            </Link>
                                            <Badge>{task.status}</Badge>
                                        </div>
                                        <div className="mt-1 flex flex-wrap gap-x-2 gap-y-1 text-xs text-slate-600">
                                            <span>
                                                {task.project_name || task.client_name || "ADB Internal"}
                                            </span>
                                            {task.task_list_name ? (
                                                <span>· {task.task_list_name}</span>
                                            ) : null}
                                            {task.recurrence_frequency !== "none" ? (
                                                <span className="capitalize">
                                                    · {task.recurrence_frequency} recurring
                                                </span>
                                            ) : null}
                                            <span className="lg:hidden">
                                                · {task.assigned_to_name || "Unassigned"}
                                            </span>
                                            <span
                                                className={
                                                    overdue ? "text-red-400 lg:hidden" : "lg:hidden"
                                                }
                                            >
                                                · {formatDate(task.due_date)}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="hidden lg:block">
                                        <Badge className={priorityClasses(task.priority)}>
                                            {priorityLabels[task.priority] ?? "Unknown"}
                                        </Badge>
                                    </div>
                                    <div className="hidden truncate pr-3 text-sm text-slate-500 lg:block">
                                        {task.assigned_to_name || "Unassigned"}
                                    </div>
                                    <div
                                        className={`hidden text-sm lg:block ${
                                            overdue ? "font-medium text-red-300" : "text-slate-500"
                                        }`}
                                    >
                                        {formatDate(task.due_date)}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                    <Pagination
                        page={pageData.page}
                        pageSize={pageData.page_size}
                        totalItems={pageData.total}
                        onPageChange={setPage}
                        disabled={isLoading}
                    />
                </div>
            ) : null}
        </div>
    );
}
