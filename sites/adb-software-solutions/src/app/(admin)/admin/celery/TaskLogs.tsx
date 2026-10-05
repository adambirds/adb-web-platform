"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";
import { celeryAPI, type CeleryLogPage } from "@/lib/api/celery";
import { useCallback, useEffect, useRef, useState } from "react";

const button =
    "rounded-lg border border-slate-700 px-3 py-2 text-xs text-slate-200 hover:bg-slate-800 disabled:opacity-40";
const severities: Record<number, string> = {
    10: "DEBUG",
    20: "INFO",
    30: "WARNING",
    40: "ERROR",
    50: "CRITICAL",
};

export function TaskLogs({ taskId }: { taskId: string }) {
    const [logs, setLogs] = useState<CeleryLogPage | null>(null);
    const [page, setPage] = useState(1);
    const [level, setLevel] = useState("");
    const [follow, setFollow] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const sequence = useRef(0);
    const viewport = useRef<HTMLDivElement>(null);
    const load = useCallback(async () => {
        const current = ++sequence.current;
        setBusy(true);
        try {
            const result = await celeryAPI.logs(taskId, page, level);
            if (current !== sequence.current) return;
            const pages = Math.max(
                1,
                Math.ceil(result.total / result.page_size),
            );
            if (page > pages) {
                setPage(pages);
                return;
            }
            setLogs(result);
            setError(null);
        } catch (loadError) {
            if (current === sequence.current)
                setError(
                    loadError instanceof Error
                        ? loadError.message
                        : "Task logs are unavailable.",
                );
        } finally {
            if (current === sequence.current) setBusy(false);
        }
    }, [taskId, page, level]);
    useEffect(() => {
        setLogs(null);
        setPage(1);
        setFollow(true);
    }, [taskId]);
    useEffect(() => {
        void load();
        return () => {
            sequence.current++;
        };
    }, [load]);
    useLiveRefresh(["celery"], async () => {
        if (follow) await load();
    });
    useEffect(() => {
        if (follow && viewport.current)
            viewport.current.scrollTop = viewport.current.scrollHeight;
    }, [logs, follow]);
    const pages = logs
        ? Math.max(1, Math.ceil(logs.total / logs.page_size))
        : 1;
    return (
        <section
            className="mt-6 border-t border-slate-800 pt-5"
            aria-label="Task logs"
        >
            <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="font-semibold text-white">Task logs</h3>
                <div className="flex flex-wrap items-center gap-3">
                    <select
                        aria-label="Minimum log severity"
                        value={level}
                        onChange={(event) => {
                            setLevel(event.target.value);
                            setPage(1);
                        }}
                        className="rounded-lg border border-slate-700 bg-slate-950 px-2 py-2 text-xs text-white"
                    >
                        <option value="">All severities</option>
                        {Object.entries(severities).map(([value, label]) => (
                            <option key={value} value={label}>
                                {label} and above
                            </option>
                        ))}
                    </select>
                    <label className="flex items-center gap-2 text-xs text-slate-300">
                        <input
                            type="checkbox"
                            checked={follow}
                            onChange={(event) => {
                                setFollow(event.target.checked);
                                if (event.target.checked) setPage(1);
                            }}
                        />
                        Follow live
                    </label>
                    <button
                        type="button"
                        className={button}
                        disabled={busy}
                        onClick={() => void load()}
                    >
                        {busy ? "Loading…" : "Refresh logs"}
                    </button>
                </div>
            </div>
            {error && (
                <p role="alert" className="mt-3 text-sm text-rose-300">
                    {error}
                </p>
            )}
            {logs?.truncated && (
                <p role="status" className="mt-3 text-xs text-amber-300">
                    This task reached the 2,000-entry capture limit. Some later
                    logs were not recorded.
                </p>
            )}
            <div
                ref={viewport}
                className="mt-3 max-h-96 overflow-auto rounded-lg border border-slate-800 bg-black/40 p-3 font-mono text-xs"
                tabIndex={0}
                aria-label="Captured log entries"
            >
                {!logs && !error && (
                    <p className="text-slate-500">Loading task logs…</p>
                )}
                {logs?.items.length === 0 && (
                    <p className="text-slate-500">
                        No captured logs for this view. Logs are recorded by
                        updated workers when tasks run; older executions cannot
                        be backfilled.
                    </p>
                )}
                {logs?.items.map((entry) => (
                    <div key={entry.id} className="mb-3 last:mb-0">
                        <p className="mb-1 text-slate-500">
                            {new Date(entry.created_at).toLocaleString("en-GB")}{" "}
                            ·{" "}
                            <span
                                className={
                                    entry.level >= 40
                                        ? "text-rose-400"
                                        : entry.level >= 30
                                          ? "text-amber-300"
                                          : "text-cyan-300"
                                }
                            >
                                {severities[entry.level] || entry.level}
                            </span>{" "}
                            · {entry.logger_name} · attempt {entry.attempt + 1}
                        </p>
                        <pre className="font-inherit break-words whitespace-pre-wrap text-slate-200">
                            {entry.message}
                        </pre>
                    </div>
                ))}
            </div>
            <div className="mt-3 flex items-center justify-between gap-3 text-xs text-slate-500">
                <span>
                    {logs?.total ?? 0} entries · Page {page} of {pages} (latest
                    first)
                </span>
                <div className="flex gap-2">
                    <button
                        type="button"
                        className={button}
                        disabled={busy || page >= pages}
                        onClick={() => {
                            setFollow(false);
                            setPage((value) => value + 1);
                        }}
                    >
                        Older
                    </button>
                    <button
                        type="button"
                        className={button}
                        disabled={busy || page <= 1}
                        onClick={() => setPage((value) => value - 1)}
                    >
                        Newer
                    </button>
                </div>
            </div>
        </section>
    );
}
