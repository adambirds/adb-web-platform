"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";
import { Button, Card, Pagination } from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { useCallback, useRef, useEffect, useState } from "react";
import { githubAPI, type GitHubItem } from "./contracts";
interface Job {
    id: number;
    name: string;
    status: string;
    conclusion: string | null;
    url: string;
}
export function GitHubRunJobs({
    run,
    onClose,
}: {
    run: GitHubItem;
    onClose: () => void;
}) {
    const { hasPermission } = useAuth();
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [jobs, setJobs] = useState<Job[]>([]);
    const [error, setError] = useState("");
    const [log, setLog] = useState<{ text: string; truncated: boolean } | null>(
        null,
    );
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);
    const endpoint = `${githubAPI}/repositories/${run.repository_id}/runs/${run.github_id}/jobs`;
    const sequence = useRef(0);
    const load = useCallback(async () => {
        const request = ++sequence.current;
        try {
            const result = (await fetchAPI(`${endpoint}?page=${page}`)) as {
                rows: Job[];
                total: number;
            };
            if (request === sequence.current) {
                setJobs(result.rows);
                setTotal(result.total);
                setError("");
            }
        } catch (reason) {
            if (request === sequence.current)
                setError(
                    reason instanceof Error
                        ? reason.message
                        : "Unable to load jobs.",
                );
        } finally {
            if (request === sequence.current) setLoading(false);
        }
    }, [endpoint, page]);
    useEffect(() => {
        setLog(null);
        setJobs([]);
        setError("");
        setLoading(true);
        void load();
        return () => {
            ++sequence.current;
        };
    }, [load]);
    useLiveRefresh(["github"], load);
    async function logs(job: Job) {
        setBusy(true);
        setError("");
        setLog(null);
        try {
            setLog(
                (await fetchAPI(`${endpoint}/${job.id}/logs`)) as {
                    text: string;
                    truncated: boolean;
                },
            );
        } catch (reason) {
            setError(
                reason instanceof Error
                    ? reason.message
                    : "Unable to load logs.",
            );
        } finally {
            setBusy(false);
        }
    }
    return (
        <Card className="space-y-4 p-4">
            <div className="flex justify-between gap-4">
                <h2 className="font-semibold text-white">Jobs · {run.title}</h2>
                <Button variant="secondary" onClick={onClose}>
                    Close
                </Button>
            </div>
            {error ? (
                <p role="alert" className="text-sm text-red-300">
                    {error}
                </p>
            ) : null}
            {loading ? (
                <p className="text-sm text-slate-400">Loading jobs…</p>
            ) : jobs.length === 0 ? (
                <p className="text-sm text-slate-400">
                    No jobs yet. This view refreshes automatically.
                </p>
            ) : null}
            {jobs.map((job) => (
                <div
                    key={job.id}
                    className="flex items-center justify-between gap-4"
                >
                    <a
                        className="text-sm text-cyan-300"
                        href={job.url}
                        target="_blank"
                        rel="noreferrer"
                    >
                        {job.name} · {job.conclusion || job.status}
                    </a>
                    {hasPermission("github_integration.view_workflow_logs") ? (
                        <Button
                            size="sm"
                            disabled={busy}
                            onClick={() => void logs(job)}
                        >
                            View logs
                        </Button>
                    ) : null}
                </div>
            ))}
            <Pagination
                page={page}
                pageSize={25}
                totalItems={total}
                onPageChange={setPage}
                disabled={busy}
            />
            {log ? (
                <div>
                    {log.truncated ? (
                        <p className="text-sm text-slate-400">
                            Showing the first 256 KB. Open the job in GitHub for
                            its complete log.
                        </p>
                    ) : null}
                    <pre className="max-h-96 overflow-auto rounded-lg bg-slate-950 p-4 text-xs whitespace-pre-wrap text-slate-300">
                        {log.text}
                    </pre>
                </div>
            ) : null}
        </Card>
    );
}
