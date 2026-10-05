"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";

import { RecordDrawer } from "@/components/admin/RecordDrawer";
import {
    Badge,
    Button,
    DataError,
    DataLoading,
    EmptyState,
    Input,
    Pagination,
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
import { TicketFocusAPI } from "@/lib/api/ticketFocus";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { TicketControls } from "./[id]/TicketControls";
import { TicketTimePanel } from "./[id]/TicketTimePanel";
import { TicketWorkspace } from "./[id]/TicketWorkspace";

type TicketView =
    | "my"
    | "unassigned"
    | "active"
    | "waiting_customer"
    | "resolved"
    | "closed"
    | "all";
type TicketSort =
    | "operational"
    | "updated_desc"
    | "updated_asc"
    | "priority_desc"
    | "priority_asc"
    | "created_desc"
    | "created_asc"
    | "subject_asc"
    | "subject_desc";

interface TicketListItem {
    id: number;
    reference: string;
    subject: string;
    brand_name: string;
    queue_id: number;
    queue_name: string;
    client_name: string | null;
    primary_contact_name: string | null;
    vendor_name: string | null;
    status: string;
    priority: string;
    classification: string;
    source: string;
    assigned_to_name: string | null;
    message_count: number;
    last_message_at: string | null;
    created_at: string;
}

interface TicketPage {
    items: TicketListItem[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
}

interface TicketCounts {
    mine: number;
    unassigned: number;
    active: number;
    waiting_customer: number;
}

interface TicketQueueRow {
    id: number;
    name: string;
    brand_name: string | null;
    active_count: number;
    is_default: boolean;
}

interface TicketFocusPage extends TicketPage {
    view: TicketView;
    counts: TicketCounts;
    queues: TicketQueueRow[];
}

const workViews: Array<{ value: TicketView; label: string; description: string }> = [
    { value: "my", label: "My tickets", description: "Actionable work assigned to you" },
    { value: "unassigned", label: "Unassigned", description: "Tickets needing an owner" },
    { value: "active", label: "All active", description: "Current tickets across your queues" },
];

const historyViews: Array<{ value: TicketView; label: string; description: string }> = [
    { value: "resolved", label: "Resolved", description: "Recently resolved work" },
    { value: "closed", label: "Closed", description: "Closed ticket history" },
    { value: "all", label: "All tickets", description: "Full accessible ticket history" },
];

function label(value: string) {
    return value
        .split("_")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
}

function priorityClass(priority: string) {
    if (priority === "urgent") return "border-red-950 bg-red-950/30 text-red-300";
    if (priority === "high") return "border-amber-900/70 bg-amber-950/40 text-amber-300";
    if (priority === "low") return "border-slate-800 bg-slate-950 text-slate-500";
    return "border-slate-700 bg-slate-900 text-slate-300";
}

function statusClass(status: string) {
    if (status === "new") return "border-cyan-900/60 bg-cyan-950/40 text-cyan-300";
    if (status === "open") return "border-blue-900/60 bg-blue-950/40 text-blue-300";
    if (status === "waiting_internal") {
        return "border-amber-900/60 bg-amber-950/30 text-amber-300";
    }
    if (status === "waiting_customer") {
        return "border-slate-800 bg-slate-900/70 text-slate-500";
    }
    if (status === "resolved" || status === "closed") {
        return "border-emerald-900/50 bg-emerald-950/20 text-emerald-500";
    }
    if (status === "spam") return "border-red-950 bg-red-950/30 text-red-400";
    return "border-slate-700 bg-slate-900 text-slate-400";
}

function formatDate(value: string | null) {
    if (!value) return "No messages";
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
    }).format(new Date(value));
}

function SidebarLink({
    active,
    label: itemLabel,
    description,
    count,
    onClick,
    quiet = false,
}: {
    active: boolean;
    label: string;
    description: string;
    count?: number;
    onClick: () => void;
    quiet?: boolean;
}) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={`w-full rounded-lg border px-3 py-2.5 text-left transition ${
                active
                    ? "border-adb-cyan-500/50 bg-adb-cyan-500/10"
                    : quiet
                      ? "border-transparent text-slate-500 hover:border-slate-800 hover:bg-slate-900/50 hover:text-slate-300"
                      : "border-transparent text-slate-400 hover:border-slate-800 hover:bg-slate-900/60 hover:text-slate-200"
            }`}
        >
            <div className="flex items-center justify-between gap-3">
                <span className={active ? "text-sm font-semibold text-white" : "text-sm font-medium"}>
                    {itemLabel}
                </span>
                {count !== undefined ? (
                    <span className="rounded-full bg-slate-950 px-2 py-0.5 text-xs tabular-nums text-slate-500">
                        {count}
                    </span>
                ) : null}
            </div>
            <div className="mt-1 text-xs text-slate-600">{description}</div>
        </button>
    );
}

function SortHeader({
    children,
    active,
    direction,
    onClick,
}: {
    children: React.ReactNode;
    active: boolean;
    direction?: "asc" | "desc";
    onClick: () => void;
}) {
    return (
        <TableHeaderCell>
            <button
                type="button"
                onClick={onClick}
                className="inline-flex items-center gap-1 text-left hover:text-slate-200"
            >
                {children}
                <span className={active ? "text-cyan-400" : "text-slate-700"}>
                    {active ? (direction === "asc" ? "↑" : "↓") : "↕"}
                </span>
            </button>
        </TableHeaderCell>
    );
}

function TicketRows({
    tickets,
    onOpen,
    sortable,
    sort,
    setSort,
}: {
    tickets: TicketListItem[];
    onOpen?: (id: number) => void;
    sortable: boolean;
    sort: TicketSort;
    setSort: (sort: TicketSort) => void;
}) {
    function toggle(field: "subject" | "priority" | "updated") {
        if (field === "subject") setSort(sort === "subject_asc" ? "subject_desc" : "subject_asc");
        if (field === "priority") {
            setSort(sort === "priority_desc" ? "priority_asc" : "priority_desc");
        }
        if (field === "updated") setSort(sort === "updated_desc" ? "updated_asc" : "updated_desc");
    }

    return (
        <Table>
            <TableHead>
                <tr>
                    {sortable ? (
                        <SortHeader
                            active={sort === "subject_asc" || sort === "subject_desc"}
                            direction={sort === "subject_asc" ? "asc" : "desc"}
                            onClick={() => toggle("subject")}
                        >
                            Ticket
                        </SortHeader>
                    ) : (
                        <TableHeaderCell>Ticket</TableHeaderCell>
                    )}
                    <TableHeaderCell>Queue</TableHeaderCell>
                    <TableHeaderCell>Customer / vendor</TableHeaderCell>
                    <TableHeaderCell>Status</TableHeaderCell>
                    {sortable ? (
                        <SortHeader
                            active={sort === "priority_asc" || sort === "priority_desc"}
                            direction={sort === "priority_asc" ? "asc" : "desc"}
                            onClick={() => toggle("priority")}
                        >
                            Priority
                        </SortHeader>
                    ) : (
                        <TableHeaderCell>Priority</TableHeaderCell>
                    )}
                    {sortable ? (
                        <SortHeader
                            active={sort === "updated_asc" || sort === "updated_desc"}
                            direction={sort === "updated_asc" ? "asc" : "desc"}
                            onClick={() => toggle("updated")}
                        >
                            Updated
                        </SortHeader>
                    ) : (
                        <TableHeaderCell>Updated</TableHeaderCell>
                    )}
                    <TableHeaderCell>Owner</TableHeaderCell>
                </tr>
            </TableHead>
            <TableBody>
                {tickets.map((ticket) => (
                    <TableRow
                        key={ticket.id}
                        className={ticket.status === "waiting_customer" ? "opacity-70" : undefined}
                    >
                        <TableCell>
                            {onOpen ? (
                                <button
                                    type="button"
                                    onClick={() => onOpen(ticket.id)}
                                    className="block text-left font-medium text-slate-100 transition hover:text-cyan-300"
                                >
                                    {ticket.subject}
                                </button>
                            ) : (
                                <Link
                                    href={`/admin/tickets/${ticket.id}`}
                                    className="block font-medium text-slate-100 transition hover:text-cyan-300"
                                >
                                    {ticket.subject}
                                </Link>
                            )}
                            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                                <span className="font-mono text-slate-400">{ticket.reference}</span>
                                <span>{label(ticket.classification)}</span>
                                <span>{ticket.message_count} messages</span>
                            </div>
                        </TableCell>
                        <TableCell>
                            <div className="text-slate-300">{ticket.queue_name}</div>
                            <div className="mt-1 text-xs text-slate-500">{ticket.brand_name}</div>
                        </TableCell>
                        <TableCell>
                            <div className="text-slate-300">
                                {ticket.client_name || ticket.vendor_name || "Unmatched sender"}
                            </div>
                            {ticket.primary_contact_name ? (
                                <div className="mt-1 text-xs text-slate-500">
                                    {ticket.primary_contact_name}
                                </div>
                            ) : ticket.vendor_name ? (
                                <div className="mt-1 text-xs text-slate-500">Vendor / service</div>
                            ) : null}
                        </TableCell>
                        <TableCell>
                            <Badge className={statusClass(ticket.status)}>{label(ticket.status)}</Badge>
                        </TableCell>
                        <TableCell>
                            <Badge className={priorityClass(ticket.priority)}>
                                {label(ticket.priority)}
                            </Badge>
                        </TableCell>
                        <TableCell className="text-slate-400">{formatDate(ticket.last_message_at)}</TableCell>
                        <TableCell className="text-slate-400">
                            {ticket.assigned_to_name || "Unassigned"}
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}

function ScopedTicketList({ clientId, contactId }: { clientId: string | null; contactId: string | null }) {
    const [data, setData] = useState<TicketPage | null>(null);
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");
    const [status, setStatus] = useState("");
    const [priority, setPriority] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const query = useMemo(() => {
        const params = new URLSearchParams({ page: String(page), page_size: "25" });
        if (clientId) params.set("client_id", clientId);
        if (contactId) params.set("primary_contact_id", contactId);
        if (search.trim()) params.set("search", search.trim());
        if (status) params.set("status", status);
        if (priority) params.set("priority", priority);
        return params.toString();
    }, [clientId, contactId, page, priority, search, status]);

    const load = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            setData((await fetchAPI(AdminAPI.tickets.list(query))) as TicketPage);
        } catch (loadError) {
            setError(loadError instanceof Error ? loadError.message : "Unable to load scoped tickets.");
        } finally {
            setIsLoading(false);
        }
    }, [query]);

    useEffect(() => {
        const timeout = window.setTimeout(() => void load(), 150);
        return () => window.clearTimeout(timeout);
    }, [load]);
    useLiveRefresh(["tickets"], load);

    useEffect(() => setPage(1), [priority, search, status]);

    if (isLoading && !data) return <DataLoading label="Loading scoped tickets..." />;
    if (error && !data) return <DataError message={error} onRetry={() => void load()} />;

    const tickets = data?.items ?? [];
    return (
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950/60">
            <div className="flex items-center justify-between gap-4 border-b border-slate-800 bg-cyan-950/10 px-4 py-3">
                <p className="text-xs text-cyan-300">
                    This view is scoped to a client{contactId ? " contact" : ""}.
                </p>
                <Link href="/admin/tickets" className="text-xs font-medium text-slate-400 hover:text-white">
                    Clear scope
                </Link>
            </div>
            <div className="grid gap-3 border-b border-slate-800 p-4 lg:grid-cols-[minmax(0,1fr)_220px_180px]">
                <Input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search reference, subject, client, contact or vendor..."
                    aria-label="Search tickets"
                />
                <Select value={status} onChange={(event) => setStatus(event.target.value)}>
                    <option value="">All statuses</option>
                    <option value="new">New</option>
                    <option value="open">Open</option>
                    <option value="waiting_customer">Waiting for customer</option>
                    <option value="waiting_internal">Waiting internally</option>
                    <option value="resolved">Resolved</option>
                    <option value="closed">Closed</option>
                    <option value="spam">Spam</option>
                </Select>
                <Select value={priority} onChange={(event) => setPriority(event.target.value)}>
                    <option value="">All priorities</option>
                    <option value="urgent">Urgent</option>
                    <option value="high">High</option>
                    <option value="normal">Normal</option>
                    <option value="low">Low</option>
                </Select>
            </div>
            {tickets.length === 0 ? (
                <EmptyState title="No tickets match this scope" description="Try changing the filters." />
            ) : (
                <TicketRows tickets={tickets} sortable={false} sort="operational" setSort={() => undefined} />
            )}
            <Pagination
                page={data?.page ?? page}
                pageSize={data?.page_size ?? 25}
                totalItems={data?.total ?? 0}
                onPageChange={setPage}
                disabled={isLoading}
            />
        </div>
    );
}

export function TicketList() {
    const searchParams = useSearchParams();
    const clientId = searchParams.get("client_id");
    const contactId = searchParams.get("primary_contact_id");
    const [data, setData] = useState<TicketFocusPage | null>(null);
    const [view, setView] = useState<TicketView>("my");
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");
    const [priority, setPriority] = useState("");
    const [sort, setSort] = useState<TicketSort>("operational");
    const [selectedQueueId, setSelectedQueueId] = useState<number | null>(null);
    const [selectedTicketId, setSelectedTicketId] = useState<number | null>(null);
    const [showQueuePreferences, setShowQueuePreferences] = useState(false);
    const [draftQueueIds, setDraftQueueIds] = useState<number[]>([]);
    const [isSavingQueues, setIsSavingQueues] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const query = useMemo(() => {
        const params = new URLSearchParams({
            view,
            page: String(page),
            page_size: "25",
            sort,
        });
        if (selectedQueueId) params.set("queue_id", String(selectedQueueId));
        if (search.trim()) params.set("search", search.trim());
        if (priority) params.set("priority", priority);
        return params.toString();
    }, [page, priority, search, selectedQueueId, sort, view]);

    const loadTickets = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const response = (await fetchAPI(TicketFocusAPI.list(query))) as TicketFocusPage;
            setData(response);
            if (!showQueuePreferences) {
                setDraftQueueIds(response.queues.filter((queue) => queue.is_default).map((queue) => queue.id));
            }
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "An unexpected error occurred while loading tickets.",
            );
        } finally {
            setIsLoading(false);
        }
    }, [query, showQueuePreferences]);

    useEffect(() => {
        if (clientId || contactId) return;
        const timeout = window.setTimeout(() => void loadTickets(), 150);
        return () => window.clearTimeout(timeout);
    }, [clientId, contactId, loadTickets]);
    useLiveRefresh(["tickets"], async () => { if (!clientId && !contactId) await loadTickets(); });

    useEffect(() => setPage(1), [priority, search, selectedQueueId, sort, view]);

    if (clientId || contactId) {
        return <ScopedTicketList clientId={clientId} contactId={contactId} />;
    }

    async function saveQueuePreferences() {
        if (!data || draftQueueIds.length === 0 || isSavingQueues) return;
        try {
            setIsSavingQueues(true);
            setError(null);
            await fetchAPI(TicketFocusAPI.queuePreferences(), {
                method: "PUT",
                body: JSON.stringify({ queue_ids: draftQueueIds }),
            });
            setSelectedQueueId(null);
            setView("my");
            setShowQueuePreferences(false);
            await loadTickets();
        } catch (saveError) {
            setError(
                saveError instanceof Error ? saveError.message : "Unable to save default ticket queues.",
            );
        } finally {
            setIsSavingQueues(false);
        }
    }

    if (isLoading && !data) return <DataLoading label="Loading your ticket work queue..." />;
    if (error && !data) return <DataError message={error} onRetry={() => void loadTickets()} />;

    const tickets = data?.items ?? [];
    const queues = data?.queues ?? [];
    const counts = data?.counts;
    const selectedQueue = queues.find((queue) => queue.id === selectedQueueId);
    const activeView = [...workViews, ...historyViews].find((item) => item.value === view);

    return (
        <div className="grid gap-6 xl:grid-cols-[250px_minmax(0,1fr)]">
            <aside className="space-y-5 xl:sticky xl:top-6 xl:self-start">
                <div>
                    <div className="px-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-600">
                        Work queue
                    </div>
                    <div className="mt-2 space-y-1">
                        {workViews.map((item) => (
                            <SidebarLink
                                key={item.value}
                                active={view === item.value && selectedQueueId === null}
                                label={item.label}
                                description={item.description}
                                count={
                                    item.value === "my"
                                        ? counts?.mine
                                        : item.value === "unassigned"
                                          ? counts?.unassigned
                                          : counts?.active
                                }
                                onClick={() => {
                                    setView(item.value);
                                    setSelectedQueueId(null);
                                    setSort("operational");
                                }}
                            />
                        ))}
                        <SidebarLink
                            active={view === "waiting_customer" && selectedQueueId === null}
                            label="Waiting on customer"
                            description="Current work paused for a customer response"
                            count={counts?.waiting_customer}
                            quiet
                            onClick={() => {
                                setView("waiting_customer");
                                setSelectedQueueId(null);
                                setSort("updated_desc");
                            }}
                        />
                    </div>
                </div>

                <div className="border-t border-slate-800 pt-4">
                    <div className="flex items-center justify-between gap-2 px-2">
                        <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-600">
                            Queues
                        </span>
                        <button
                            type="button"
                            onClick={() => setShowQueuePreferences((value) => !value)}
                            className="text-xs text-slate-600 hover:text-cyan-300"
                        >
                            Defaults
                        </button>
                    </div>
                    <div className="mt-2 space-y-1">
                        {queues.map((queue) => (
                            <SidebarLink
                                key={queue.id}
                                active={selectedQueueId === queue.id}
                                label={queue.name}
                                description={queue.brand_name || "Shared queue"}
                                count={queue.active_count}
                                onClick={() => {
                                    setSelectedQueueId(queue.id);
                                    setView("active");
                                    setSort("operational");
                                }}
                            />
                        ))}
                    </div>

                    {showQueuePreferences ? (
                        <div className="mt-3 rounded-lg border border-slate-800 bg-slate-950/80 p-3">
                            <div className="text-xs font-medium text-slate-300">Default ticket queues</div>
                            <p className="mt-1 text-xs leading-5 text-slate-600">
                                These queues feed My tickets, Unassigned and All active by default.
                            </p>
                            <div className="mt-3 space-y-2">
                                {queues.map((queue) => (
                                    <label
                                        key={queue.id}
                                        className="flex cursor-pointer items-center gap-2 text-xs text-slate-400"
                                    >
                                        <input
                                            type="checkbox"
                                            checked={draftQueueIds.includes(queue.id)}
                                            onChange={(event) =>
                                                setDraftQueueIds((current) =>
                                                    event.target.checked
                                                        ? [...current, queue.id]
                                                        : current.filter((id) => id !== queue.id),
                                                )
                                            }
                                            className="h-4 w-4 rounded border-slate-700 bg-slate-950"
                                        />
                                        <span>{queue.name}</span>
                                    </label>
                                ))}
                            </div>
                            {draftQueueIds.length === 0 ? (
                                <p className="mt-2 text-xs text-amber-400">Choose at least one queue.</p>
                            ) : null}
                            <div className="mt-3 flex gap-2">
                                <Button
                                    type="button"
                                    size="sm"
                                    disabled={draftQueueIds.length === 0 || isSavingQueues}
                                    onClick={() => void saveQueuePreferences()}
                                >
                                    {isSavingQueues ? "Saving..." : "Save defaults"}
                                </Button>
                                <Button
                                    type="button"
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => {
                                        setDraftQueueIds(
                                            queues.filter((queue) => queue.is_default).map((queue) => queue.id),
                                        );
                                        setShowQueuePreferences(false);
                                    }}
                                >
                                    Cancel
                                </Button>
                            </div>
                        </div>
                    ) : null}
                </div>

                <div className="border-t border-slate-800 pt-4">
                    <div className="px-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-700">
                        History
                    </div>
                    <div className="mt-2 space-y-1">
                        {historyViews.map((item) => (
                            <SidebarLink
                                key={item.value}
                                active={view === item.value && selectedQueueId === null}
                                label={item.label}
                                description={item.description}
                                quiet
                                onClick={() => {
                                    setView(item.value);
                                    setSelectedQueueId(null);
                                    setSort("updated_desc");
                                }}
                            />
                        ))}
                    </div>
                </div>
            </aside>

            <div className="min-w-0 space-y-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                        <h2 className="text-xl font-semibold text-white">
                            {selectedQueue ? selectedQueue.name : activeView?.label || "My tickets"}
                        </h2>
                        <p className="mt-1 text-sm text-slate-500">
                            {selectedQueue
                                ? `Active tickets in ${selectedQueue.name}`
                                : activeView?.description || "Actionable work assigned to you"}
                        </p>
                    </div>
                    <Select value={sort} onChange={(event) => setSort(event.target.value as TicketSort)}>
                        <option value="operational">Operational order</option>
                        <option value="updated_desc">Recently updated</option>
                        <option value="updated_asc">Oldest activity first</option>
                        <option value="priority_desc">Highest priority first</option>
                        <option value="priority_asc">Lowest priority first</option>
                        <option value="created_desc">Newest created</option>
                        <option value="created_asc">Oldest created</option>
                        <option value="subject_asc">Subject A–Z</option>
                        <option value="subject_desc">Subject Z–A</option>
                    </Select>
                </div>

                <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950/60">
                    <div className="grid gap-3 border-b border-slate-800 p-4 lg:grid-cols-[minmax(0,1fr)_200px]">
                        <Input
                            value={search}
                            onChange={(event) => setSearch(event.target.value)}
                            placeholder="Search reference, subject, client, contact or vendor..."
                            aria-label="Search tickets"
                        />
                        <Select value={priority} onChange={(event) => setPriority(event.target.value)}>
                            <option value="">All priorities</option>
                            <option value="urgent">Urgent</option>
                            <option value="high">High</option>
                            <option value="normal">Normal</option>
                            <option value="low">Low</option>
                        </Select>
                    </div>

                    {view === "resolved" || view === "closed" || view === "all" ? (
                        <div className="border-b border-slate-800 bg-slate-900/40 px-4 py-2 text-xs text-slate-500">
                            Historical tickets are only shown because you selected a history view.
                        </div>
                    ) : null}

                    {error ? (
                        <div className="border-b border-slate-800 p-4">
                            <DataError message={error} onRetry={() => void loadTickets()} />
                        </div>
                    ) : null}

                    {tickets.length === 0 ? (
                        <EmptyState
                            title="No tickets match this work queue"
                            description="Try another queue, view, search or priority."
                        />
                    ) : (
                        <TicketRows
                            tickets={tickets}
                            onOpen={setSelectedTicketId}
                            sortable
                            sort={sort}
                            setSort={setSort}
                        />
                    )}

                    <Pagination
                        page={data?.page ?? page}
                        pageSize={data?.page_size ?? 25}
                        totalItems={data?.total ?? 0}
                        onPageChange={setPage}
                        disabled={isLoading}
                    />
                </div>
            </div>

            {selectedTicketId ? (
                <RecordDrawer
                    fullPageHref={`/admin/tickets/${selectedTicketId}`}
                    onClose={() => {
                        setSelectedTicketId(null);
                        void loadTickets();
                    }}
                >
                    <div className="space-y-6">
                        <TicketControls ticketId={selectedTicketId} />
                        <TicketTimePanel ticketId={selectedTicketId} />
                        <TicketWorkspace ticketId={selectedTicketId} presentation="drawer" />
                    </div>
                </RecordDrawer>
            ) : null}
        </div>
    );
}
