"use client";

import { useAuth } from "@/contexts/AuthContext";
import { useLiveRefresh } from "@/contexts/LiveEventsContext";
import {
    celeryAPI,
    type CeleryExecution,
    type CeleryHistory,
    type CeleryHour,
    type CeleryOverview,
} from "@/lib/api/celery";
import { TaskLogs } from "./TaskLogs";
import { Dialog, DialogPanel } from "@headlessui/react";
import { useCallback, useEffect, useRef, useState } from "react";

const panel = "rounded-xl border border-slate-800 bg-slate-900/50 p-5";
const button =
    "rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-40";
const labels: Record<string, string> = {
    QUEUED: "Queued",
    STARTED: "Running",
    RETRY: "Retrying",
    SUCCESS: "Succeeded",
    FAILURE: "Failed",
    REVOKED: "Revoked",
    IGNORED: "Ignored",
    RESERVED: "Reserved",
    SCHEDULED: "Scheduled",
};
function date(value: string | null) {
    return value ? new Date(value).toLocaleString("en-GB") : "—";
}
function duration(value: number | null) {
    return value === null
        ? "—"
        : value < 60
          ? `${value.toFixed(2)}s`
          : `${(value / 60).toFixed(1)}m`;
}
function State({ state }: { state: string }) {
    const colour =
        state === "SUCCESS"
            ? "text-emerald-400"
            : state === "FAILURE"
              ? "text-rose-400"
              : state === "STARTED"
                ? "text-cyan-400"
                : "text-amber-300";
    return (
        <span className={`text-xs font-semibold ${colour}`}>
            {labels[state] || state}
        </span>
    );
}
function ActivityChart({ hours }: { hours: CeleryHour[] }) {
    const max = Math.max(
        1,
        ...hours.map((hour) => hour.succeeded + hour.failed),
    );
    const [selected, setSelected] = useState<number | null>(null);
    const value = selected === null ? null : hours[selected];
    return (
        <section className={panel}>
            <h2 className="font-semibold text-white">
                Task activity · last 24 hours
            </h2>
            <p className="mt-1 text-xs text-slate-400">
                Succeeded <span className="text-emerald-400">●</span> · Failed{" "}
                <span className="text-rose-400">●</span> · Select an hour for
                counts and average duration.
            </p>
            <div
                className="mt-5 flex h-36 items-end gap-1"
                role="group"
                aria-label="Hourly task activity"
            >
                {hours.map((hour, index) => (
                    <button
                        key={hour.hour}
                        type="button"
                        onClick={() => setSelected(index)}
                        aria-label={`${date(hour.hour)}: ${hour.succeeded} succeeded, ${hour.failed} failed`}
                        className="flex h-full min-w-0 flex-1 flex-col justify-end rounded-t border-b border-slate-700 hover:bg-slate-800 focus-visible:outline-2 focus-visible:outline-cyan-400"
                    >
                        <span
                            className="block w-full bg-rose-500"
                            style={{ height: `${(hour.failed / max) * 100}%` }}
                        />
                        <span
                            className="block w-full bg-emerald-500"
                            style={{
                                height: `${(hour.succeeded / max) * 100}%`,
                            }}
                        />
                    </button>
                ))}
            </div>
            <div className="mt-2 flex justify-between text-xs text-slate-500">
                <span>{hours[0] ? date(hours[0].hour) : ""}</span>
                <span>Now</span>
            </div>
            <p
                className="mt-3 min-h-5 text-sm text-slate-300"
                aria-live="polite"
            >
                {value
                    ? `${date(value.hour)} · ${value.succeeded} succeeded · ${value.failed} failed · average ${duration(value.average_runtime)}`
                    : "Hourly totals reflect recorded task completions."}
            </p>
        </section>
    );
}

type Action = { kind: "run" | "revoke"; id: string; label: string };
export function CeleryWorkspace() {
    const { user, isLoading: authLoading } = useAuth();
    const allowed = user?.isStaff === true && user?.isSuperuser === true;
    const [overview, setOverview] = useState<CeleryOverview | null>(null);
    const [history, setHistory] = useState<CeleryHistory | null>(null);
    const [page, setPage] = useState(1);
    const [state, setState] = useState("");
    const [input, setInput] = useState("");
    const [search, setSearch] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);
    const [action, setAction] = useState<Action | null>(null);
    const [actionBusy, setActionBusy] = useState(false);
    const [message, setMessage] = useState("");
    const [detail, setDetail] = useState<CeleryExecution | null>(null);
    const sequence = useRef(0);
    useEffect(() => {
        if (input === search) return;
        const timer = setTimeout(() => {
            setSearch(input);
            setPage(1);
        }, 300);
        return () => clearTimeout(timer);
    }, [input, search]);
    const reload = useCallback(async () => {
        if (!allowed) return;
        const current = ++sequence.current;
        setBusy(true);
        try {
            const [summary, tasks] = await Promise.all([
                celeryAPI.overview(),
                celeryAPI.history(page, state, search),
            ]);
            if (current !== sequence.current) return;
            setOverview(summary);
            setHistory(tasks);
            setDetail((previous) =>
                previous
                    ? tasks.items.find((item) => item.id === previous.id) ||
                      previous
                    : null,
            );
            setError(null);
        } catch (loadError) {
            if (current === sequence.current)
                setError(
                    loadError instanceof Error
                        ? loadError.message
                        : "Celery dashboard is unavailable.",
                );
        } finally {
            if (current === sequence.current) setBusy(false);
        }
    }, [allowed, page, state, search]);
    useEffect(() => {
        void reload();
        return () => {
            sequence.current++;
        };
    }, [reload]);
    useLiveRefresh(["celery"], reload);
    const perform = async () => {
        if (!action || !allowed) return;
        setActionBusy(true);
        try {
            const result =
                action.kind === "run"
                    ? await celeryAPI.run(action.id)
                    : await celeryAPI.revoke(action.id);
            setMessage(`${result.message} Task: ${result.task_id}`);
            setAction(null);
            await reload();
        } catch (actionError) {
            setMessage(
                actionError instanceof Error
                    ? actionError.message
                    : "Action failed.",
            );
        } finally {
            setActionBusy(false);
        }
    };
    if (authLoading) return <p className="text-slate-400">Loading access…</p>;
    if (!allowed)
        return (
            <p role="alert" className="text-slate-300">
                Full administrator access is required to view Celery operations.
            </p>
        );
    const snapshot = overview?.snapshot;
    const pages = history
        ? Math.max(1, Math.ceil(history.total / history.page_size))
        : 1;
    return (
        <div className="space-y-6">
            <header className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-800 pb-5">
                <div>
                    <h1 className="text-2xl font-bold text-white">
                        Celery operations
                    </h1>
                    <p className="mt-2 text-sm text-slate-400">
                        Workers, queues, background tasks and scheduled jobs.
                    </p>
                </div>
                <button
                    type="button"
                    className={button}
                    disabled={busy}
                    onClick={() => void reload()}
                >
                    {busy ? "Refreshing…" : "Refresh"}
                </button>
            </header>
            {error && (
                <p
                    role="alert"
                    className="rounded-lg border border-rose-900 bg-rose-950/30 p-4 text-rose-300"
                >
                    {error}
                </p>
            )}
            {message && (
                <p
                    role="status"
                    className="rounded-lg border border-slate-700 p-4 text-sm break-words text-slate-200"
                >
                    {message}
                </p>
            )}
            {snapshot?.warning && (
                <p
                    role="status"
                    className="rounded-lg border border-amber-900 bg-amber-950/20 p-4 text-sm text-amber-200"
                >
                    {snapshot.warning}
                </p>
            )}
            {overview && (
                <>
                    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
                        {[
                            [
                                "Broker",
                                snapshot?.broker_available
                                    ? "Connected"
                                    : "Unavailable",
                            ],
                            [
                                "Workers responding",
                                snapshot?.workers.length ?? 0,
                            ],
                            [
                                "Queued in broker",
                                snapshot?.queues.every(
                                    (queue) => queue.depth !== null,
                                )
                                    ? snapshot.queues.reduce(
                                          (sum, queue) =>
                                              sum + (queue.depth ?? 0),
                                          0,
                                      )
                                    : "Unknown",
                            ],
                            ["Succeeded · 24h", overview.counts.SUCCESS ?? 0],
                            ["Failed · 24h", overview.counts.FAILURE ?? 0],
                            [
                                "Average duration · 24h",
                                duration(overview.average_runtime),
                            ],
                        ].map(([label, value]) => (
                            <div className={panel} key={label}>
                                <p className="text-xs text-slate-400">
                                    {label}
                                </p>
                                <p className="mt-2 text-xl font-semibold text-white">
                                    {value}
                                </p>
                            </div>
                        ))}
                    </div>
                    <ActivityChart hours={overview.hours} />
                    <div className="grid gap-5 xl:grid-cols-3">
                        <section className={`${panel} xl:col-span-2`}>
                            <h2 className="font-semibold text-white">
                                Workers
                            </h2>
                            <p className="mt-1 text-xs text-slate-500">
                                Inspection at{" "}
                                {date(snapshot?.checked_at || null)} · cached
                                for up to 10 seconds
                            </p>
                            {!snapshot?.workers.length && (
                                <p className="mt-4 text-sm text-slate-400">
                                    No responding workers.
                                </p>
                            )}
                            <div className="mt-4 space-y-3">
                                {snapshot?.workers.map((worker) => (
                                    <details
                                        key={worker.name}
                                        className="rounded-lg border border-slate-800 p-3"
                                    >
                                        <summary className="cursor-pointer text-sm break-words text-white">
                                            {worker.name}{" "}
                                            <span className="ml-2 text-xs text-slate-400">
                                                {worker.concurrency ??
                                                    "Unknown"}{" "}
                                                concurrency ·{" "}
                                                {worker.tasks.length}{" "}
                                                active/reserved/scheduled ·{" "}
                                                {worker.processed} processed
                                            </span>
                                        </summary>
                                        <p className="mt-3 text-xs text-slate-400">
                                            Queues:{" "}
                                            {worker.queues.join(", ") ||
                                                "Unknown"}
                                        </p>
                                        <ul className="mt-3 space-y-2">
                                            {worker.tasks.map((task) => (
                                                <li
                                                    key={`${task.state}-${task.id}`}
                                                    className="text-sm break-words text-slate-300"
                                                >
                                                    <State state={task.state} />{" "}
                                                    {task.task_name}
                                                    <span className="block text-xs text-slate-500">
                                                        {task.id}
                                                        {task.eta
                                                            ? ` · ETA ${date(task.eta)}`
                                                            : ""}
                                                    </span>
                                                </li>
                                            ))}
                                        </ul>
                                    </details>
                                ))}
                            </div>
                        </section>
                        <section className={panel}>
                            <h2 className="font-semibold text-white">
                                Queue depths
                            </h2>
                            <p className="mt-1 text-xs text-slate-400">
                                Messages waiting in the broker; reserved and
                                scheduled tasks are shown under workers.
                            </p>
                            <dl className="mt-4 space-y-3">
                                {snapshot?.queues.map((queue) => (
                                    <div
                                        className="flex justify-between gap-3 text-sm"
                                        key={queue.name}
                                    >
                                        <dt className="break-all text-slate-300">
                                            {queue.name}
                                        </dt>
                                        <dd className="text-white">
                                            {queue.depth ?? "Unknown"}
                                        </dd>
                                    </div>
                                ))}
                            </dl>
                        </section>
                    </div>
                </>
            )}
            <section className={panel}>
                <h2 className="font-semibold text-white">Task history</h2>
                <p className="mt-1 text-xs text-slate-400">
                    {overview?.history_since
                        ? `Recording since ${date(overview.history_since)}. Completed history retained for ${overview.retention_days} days.`
                        : "History starts when the updated backend and workers publish or execute tasks."}{" "}
                    States reflect the last recorded lifecycle event; an
                    interrupted worker may leave an unfinished record.
                </p>
                <div className="mt-4 flex flex-wrap gap-3">
                    <input
                        aria-label="Search task history"
                        placeholder="Search task, ID, worker or queue"
                        value={input}
                        onChange={(event) => setInput(event.target.value)}
                        className="min-w-64 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
                    />
                    <select
                        aria-label="Task state"
                        value={state}
                        onChange={(event) => {
                            setState(event.target.value);
                            setPage(1);
                        }}
                        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
                    >
                        <option value="">All states</option>
                        {Object.entries(labels)
                            .filter(
                                ([key]) =>
                                    !["RESERVED", "SCHEDULED"].includes(key),
                            )
                            .map(([key, label]) => (
                                <option key={key} value={key}>
                                    {label}
                                </option>
                            ))}
                    </select>
                </div>
                <div className="mt-4 overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="border-b border-slate-800 text-xs text-slate-400">
                            <tr>
                                {[
                                    "Task",
                                    "State",
                                    "Queue / worker",
                                    "Created",
                                    "Duration",
                                    "",
                                ].map((heading, index) => (
                                    <th key={index} className="px-3 py-3">
                                        {heading}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {history?.items.map((task) => (
                                <tr
                                    key={task.id}
                                    className="border-b border-slate-800/60 text-slate-300"
                                >
                                    <td className="px-3 py-3">
                                        <button
                                            type="button"
                                            onClick={() => setDetail(task)}
                                            className="text-left text-cyan-300 hover:underline"
                                        >
                                            {task.task_name}
                                        </button>
                                        <span className="block text-xs text-slate-500">
                                            {task.id}
                                        </span>
                                    </td>
                                    <td className="px-3 py-3">
                                        <State state={task.state} />
                                        {task.revoke_requested_at && (
                                            <span className="block text-xs text-amber-300">
                                                Revoke requested
                                            </span>
                                        )}
                                    </td>
                                    <td className="px-3 py-3">
                                        {task.queue || "—"}
                                        <span className="block text-xs text-slate-500">
                                            {task.worker || "—"}
                                        </span>
                                    </td>
                                    <td className="px-3 py-3 whitespace-nowrap">
                                        {date(task.created_at)}
                                    </td>
                                    <td className="px-3 py-3">
                                        {duration(task.runtime_seconds)}
                                    </td>
                                    <td className="px-3 py-3">
                                        {["QUEUED", "RETRY"].includes(
                                            task.state,
                                        ) &&
                                            !task.revoke_requested_at && (
                                                <button
                                                    type="button"
                                                    className={button}
                                                    onClick={() =>
                                                        setAction({
                                                            kind: "revoke",
                                                            id: task.id,
                                                            label: task.task_name,
                                                        })
                                                    }
                                                >
                                                    Revoke
                                                </button>
                                            )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {history?.items.length === 0 && (
                    <p className="py-6 text-sm text-slate-400">
                        No task executions match this view.
                    </p>
                )}
                <div className="mt-4 flex items-center justify-between gap-4 text-sm text-slate-400">
                    <span>
                        {history?.total ?? 0} executions · Page {page} of{" "}
                        {pages}
                    </span>
                    <div className="flex gap-2">
                        <button
                            className={button}
                            disabled={page <= 1 || busy}
                            onClick={() => setPage((value) => value - 1)}
                        >
                            Previous
                        </button>
                        <button
                            className={button}
                            disabled={page >= pages || busy}
                            onClick={() => setPage((value) => value + 1)}
                        >
                            Next
                        </button>
                    </div>
                </div>
            </section>
            {overview && (
                <section className={panel}>
                    <h2 className="font-semibold text-white">Scheduled jobs</h2>
                    <p className="mt-1 text-xs text-slate-400">
                        Configured Beat schedule. Beat must be running to
                        dispatch automatically. Run now queues an additional
                        execution.
                    </p>
                    <div className="mt-4 overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead className="text-xs text-slate-400">
                                <tr>
                                    <th className="p-3">Job</th>
                                    <th className="p-3">Schedule</th>
                                    <th className="p-3">Queue</th>
                                    <th className="p-3">Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {overview.schedules.map((job) => (
                                    <tr
                                        key={job.name}
                                        className="border-t border-slate-800 text-slate-300"
                                    >
                                        <td className="p-3">
                                            {job.name}
                                            <span className="block text-xs text-slate-500">
                                                {job.task_name}
                                            </span>
                                        </td>
                                        <td className="p-3">{job.schedule}</td>
                                        <td className="p-3">{job.queue}</td>
                                        <td className="p-3">
                                            <button
                                                className={button}
                                                disabled={
                                                    !job.can_run || actionBusy
                                                }
                                                onClick={() =>
                                                    setAction({
                                                        kind: "run",
                                                        id: job.name,
                                                        label: job.name,
                                                    })
                                                }
                                            >
                                                Run now
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>
            )}
            {detail && (
                <Dialog
                    open
                    onClose={() => setDetail(null)}
                    aria-label="Task execution details"
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
                >
                    <DialogPanel
                        className={`${panel} max-h-[85vh] w-full max-w-5xl overflow-y-auto bg-slate-950`}
                    >
                        <div className="flex items-center justify-between gap-4">
                            <h2 className="font-semibold text-white">
                                Task execution
                            </h2>
                            <button
                                className={button}
                                onClick={() => setDetail(null)}
                            >
                                Close
                            </button>
                        </div>
                        <dl className="mt-5 space-y-3 text-sm">
                            {[
                                ["Task", detail.task_name],
                                ["ID", detail.id],
                                ["State", labels[detail.state]],
                                ["Queue", detail.queue],
                                ["Worker", detail.worker],
                                ["Retries", detail.retries],
                                ["Published", date(detail.published_at)],
                                ["Started", date(detail.started_at)],
                                ["Finished", date(detail.finished_at)],
                                ["Last update", date(detail.updated_at)],
                                ["Duration", duration(detail.runtime_seconds)],
                                ["Error type", detail.error_type || "—"],
                            ].map(([label, value]) => (
                                <div
                                    key={label}
                                    className="grid grid-cols-3 gap-3"
                                >
                                    <dt className="text-slate-500">{label}</dt>
                                    <dd className="col-span-2 break-all text-slate-200">
                                        {value || "—"}
                                    </dd>
                                </div>
                            ))}
                        </dl>
                        <TaskLogs key={detail.id} taskId={detail.id} />
                    </DialogPanel>
                </Dialog>
            )}
            {action && (
                <Dialog
                    open
                    onClose={() => {
                        if (!actionBusy) setAction(null);
                    }}
                    aria-label="Confirm Celery action"
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
                >
                    <DialogPanel
                        className={`${panel} w-full max-w-lg bg-slate-950`}
                    >
                        <h2 className="font-semibold text-white">
                            {action.kind === "run"
                                ? "Run scheduled job now?"
                                : "Request task revocation?"}
                        </h2>
                        <p className="mt-3 text-sm break-words text-slate-300">
                            {action.label}
                        </p>
                        <p className="mt-2 text-sm text-slate-400">
                            {action.kind === "run"
                                ? "This queues an additional execution and leaves the automatic schedule in place."
                                : "The worker will skip this task if it has not started. A task already running may still finish."}
                        </p>
                        <div className="mt-5 flex justify-end gap-3">
                            <button
                                className={button}
                                disabled={actionBusy}
                                onClick={() => setAction(null)}
                            >
                                Cancel
                            </button>
                            <button
                                className={button}
                                disabled={actionBusy}
                                onClick={() => void perform()}
                            >
                                {actionBusy ? "Submitting…" : "Confirm"}
                            </button>
                        </div>
                    </DialogPanel>
                </Dialog>
            )}
        </div>
    );
}
