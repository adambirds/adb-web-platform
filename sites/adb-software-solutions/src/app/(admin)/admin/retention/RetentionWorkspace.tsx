"use client";
import Link from "next/link";
import { useLiveRefresh } from "@/contexts/LiveEventsContext";
import { useCallback, useEffect, useState } from "react";
import { Button, Card, DataError, DataLoading } from "@/components/ui";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";

interface Review {
    id: number;
    lead_id: number | null;
    name: string;
    email: string;
    brand: string;
    notes: string;
    status: string;
    due_at: string;
    last_activity_at: string;
    review_after: string | null;
    decision_reason: string;
    conversation_count: number | null;
    can_approve: boolean;
    can_keep: boolean;
    files_pending: number;
}
interface ReviewPage {
    items: Review[];
    page: number;
    total: number;
    total_pages: number;
    can_scan: boolean;
    retention_months: number;
}
const endpoint = `${API_URL}/api/admin/retention/leads`;
const date = (value: string) => new Date(value).toLocaleDateString("en-GB");

export function RetentionWorkspace() {
    const [data, setData] = useState<ReviewPage | null>(null);
    const [status, setStatus] = useState("pending");
    const [page, setPage] = useState(1);
    const [error, setError] = useState("");
    const [busy, setBusy] = useState(false);
    const [decision, setDecision] = useState<{
        id: number;
        action: "approve" | "keep";
    } | null>(null);
    const [reason, setReason] = useState("");
    const [months, setMonths] = useState(6);
    const load = useCallback(async () => {
        try {
            const result = (await fetchAPI(
                `${endpoint}?status=${status}&page=${page}`,
            )) as ReviewPage;
            setData(result);
            setError("");
        } catch (failure) {
            setError(
                failure instanceof Error
                    ? failure.message
                    : "Unable to load retention reviews.",
            );
        }
    }, [page, status]);
    useLiveRefresh(["retention", "leads", "tickets"], load);
    useEffect(() => {
        void load();
    }, [load]);
    async function act(scan = false) {
        if (busy || (!scan && !decision)) return;
        setBusy(true);
        setError("");
        try {
            await fetchAPI(
                scan
                    ? `${endpoint}/scan`
                    : `${endpoint}/${decision!.id}/decision`,
                {
                    method: "POST",
                    ...(!scan
                        ? {
                              body: JSON.stringify({
                                  action: decision!.action,
                                  reason,
                                  months,
                              }),
                          }
                        : {}),
                },
            );
            setDecision(null);
            setReason("");
            await load();
        } catch (failure) {
            setError(
                failure instanceof Error
                    ? failure.message
                    : "Unable to save this decision.",
            );
        } finally {
            setBusy(false);
        }
    }
    return (
        <div className="mt-6 space-y-5">
            <Card>
                <p className="text-sm text-slate-300">
                    This queue covers lost, unconverted leads and eligible
                    closed sales conversations in the platform. Active
                    enquiries, client records, recent correspondence and
                    unrelated tickets are protected. Microsoft 365 mailbox
                    copies and backups have separate retention arrangements.
                </p>
            </Card>
            <div className="flex flex-wrap items-center justify-between gap-4">
                <label className="text-sm text-slate-300">
                    Show{" "}
                    <select
                        className="ml-3 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white"
                        value={status}
                        onChange={(event) => {
                            setStatus(event.target.value);
                            setPage(1);
                            setDecision(null);
                        }}
                    >
                        {[
                            ["pending", "Awaiting review"],
                            ["deferred", "Kept for now"],
                            ["cancelled", "No longer eligible"],
                            ["deleted", "Deletion history"],
                        ].map(([value, label]) => (
                            <option key={value} value={value}>
                                {label}
                            </option>
                        ))}
                    </select>
                </label>
                <div className="flex gap-3">
                    <Button onClick={() => void load()} disabled={busy}>
                        Refresh
                    </Button>
                    {data?.can_scan ? (
                        <Button onClick={() => void act(true)} disabled={busy}>
                            Scan for due records
                        </Button>
                    ) : null}
                </div>
            </div>
            {error ? <DataError message={error} /> : null}
            {!data && !error ? <DataLoading /> : null}
            {data?.items.length === 0 ? (
                <Card>
                    <h2 className="font-semibold text-white">
                        No records in this view
                    </h2>
                    <p className="mt-2 text-sm text-slate-400">
                        The daily job adds eligible records. You can also run a
                        scan now.
                    </p>
                </Card>
            ) : null}
            {data?.items.map((review) => (
                <Card key={review.id}>
                    <div className="flex flex-wrap justify-between gap-4">
                        <div>
                            <h2 className="font-semibold text-white">
                                {review.name}
                            </h2>
                            <p className="mt-1 text-sm text-slate-400">
                                {review.email}{" "}
                                {review.brand ? `· ${review.brand}` : ""}
                            </p>
                        </div>
                        {review.lead_id ? (
                            <Link
                                className="text-adb-cyan-400 text-sm"
                                href={`/admin/leads/${review.lead_id}`}
                            >
                                Open lead ↗
                            </Link>
                        ) : null}
                    </div>
                    <div className="mt-4 flex flex-wrap gap-6 text-sm text-slate-300">
                        <p>Last activity: {date(review.last_activity_at)}</p>
                        <p>Due for review: {date(review.due_at)}</p>
                        {review.review_after ? (
                            <p>Review again: {date(review.review_after)}</p>
                        ) : null}
                        <p>
                            {review.conversation_count === null
                                ? "Linked conversation access restricted"
                                : `${review.conversation_count} closed conversations included`}
                        </p>
                    </div>
                    {review.notes ? (
                        <details className="mt-4 text-sm text-slate-300">
                            <summary className="cursor-pointer">
                                Previous notes
                            </summary>
                            <p className="mt-3 whitespace-pre-wrap">
                                {review.notes}
                            </p>
                        </details>
                    ) : null}
                    {review.decision_reason ? (
                        <p className="mt-4 text-sm text-slate-300">
                            Reason kept: {review.decision_reason}
                        </p>
                    ) : null}
                    {review.files_pending ? (
                        <p className="mt-3 text-sm text-amber-300">
                            {review.files_pending} attachment objects awaiting
                            cleanup retry.
                        </p>
                    ) : null}
                    {review.status === "pending" ? (
                        <div className="mt-5 flex flex-wrap gap-3">
                            <Button
                                disabled={!review.can_approve || busy}
                                onClick={() => {
                                    setDecision({
                                        id: review.id,
                                        action: "approve",
                                    });
                                    setReason("");
                                }}
                            >
                                Review deletion
                            </Button>
                            <Button
                                disabled={!review.can_keep || busy}
                                onClick={() => {
                                    setDecision({
                                        id: review.id,
                                        action: "keep",
                                    });
                                    setReason("");
                                }}
                            >
                                Reject deletion / keep
                            </Button>
                        </div>
                    ) : null}
                    {decision?.id === review.id ? (
                        <div className="mt-5 border-t border-slate-700 pt-5">
                            {decision.action === "approve" ? (
                                <>
                                    <h3 className="font-semibold text-white">
                                        Approve deletion of this record?
                                    </h3>
                                    <p className="mt-2 text-sm text-slate-300">
                                        This removes the lead, its notes and the
                                        eligible conversations shown above,
                                        including their messages, notes and
                                        stored attachments. The server checks
                                        eligibility again before deleting. This
                                        action cannot be undone.
                                    </p>
                                </>
                            ) : (
                                <>
                                    <label className="block text-sm text-slate-300">
                                        Reason for keeping this record
                                        <textarea
                                            className="mt-2 block w-full rounded-lg border border-slate-700 bg-slate-900 p-3 text-white"
                                            value={reason}
                                            maxLength={2000}
                                            onChange={(event) =>
                                                setReason(event.target.value)
                                            }
                                        />
                                    </label>
                                    <label className="mt-3 block text-sm text-slate-300">
                                        Review again in{" "}
                                        <select
                                            className="ml-2 rounded-lg bg-slate-900 p-2 text-white"
                                            value={months}
                                            onChange={(event) =>
                                                setMonths(
                                                    Number(event.target.value),
                                                )
                                            }
                                        >
                                            {[3, 6, 12].map((value) => (
                                                <option
                                                    key={value}
                                                    value={value}
                                                >
                                                    {value} months
                                                </option>
                                            ))}
                                        </select>
                                    </label>
                                </>
                            )}
                            <div className="mt-4 flex gap-3">
                                <Button
                                    disabled={
                                        busy ||
                                        (decision.action === "keep" &&
                                            !reason.trim())
                                    }
                                    onClick={() => void act()}
                                >
                                    {busy
                                        ? "Saving…"
                                        : decision.action === "approve"
                                          ? "Approve and delete"
                                          : "Keep and set review date"}
                                </Button>
                                <Button
                                    disabled={busy}
                                    onClick={() => setDecision(null)}
                                >
                                    Cancel
                                </Button>
                            </div>
                        </div>
                    ) : null}
                </Card>
            ))}
            {data ? (
                <div className="flex items-center justify-between text-sm text-slate-400">
                    <span>
                        {data.total} records · Page {data.page} of{" "}
                        {data.total_pages}
                    </span>
                    <div className="flex gap-3">
                        <Button
                            disabled={page <= 1 || busy}
                            onClick={() => setPage(page - 1)}
                        >
                            Previous
                        </Button>
                        <Button
                            disabled={page >= data.total_pages || busy}
                            onClick={() => setPage(page + 1)}
                        >
                            Next
                        </Button>
                    </div>
                </div>
            ) : null}
        </div>
    );
}
