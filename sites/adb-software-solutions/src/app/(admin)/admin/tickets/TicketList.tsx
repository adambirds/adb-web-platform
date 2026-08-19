"use client";

import {
    Badge,
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
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

interface TicketListItem {
    id: number;
    reference: string;
    subject: string;
    brand_name: string;
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
    if (status === "waiting_customer") {
        return "border-violet-900/60 bg-violet-950/40 text-violet-300";
    }
    if (status === "resolved" || status === "closed") {
        return "border-emerald-900/50 bg-emerald-950/30 text-emerald-400";
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

export function TicketList() {
    const searchParams = useSearchParams();
    const clientId = searchParams.get("client_id");
    const contactId = searchParams.get("primary_contact_id");
    const [data, setData] = useState<TicketPage | null>(null);
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");
    const [status, setStatus] = useState("");
    const [priority, setPriority] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const query = useMemo(() => {
        const params = new URLSearchParams({
            page: String(page),
            page_size: "25",
        });
        if (clientId) params.set("client_id", clientId);
        if (contactId) params.set("primary_contact_id", contactId);
        if (search.trim()) params.set("search", search.trim());
        if (status) params.set("status", status);
        if (priority) params.set("priority", priority);
        return params.toString();
    }, [clientId, contactId, page, priority, search, status]);

    const loadTickets = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const response = (await fetchAPI(AdminAPI.tickets.list(query))) as TicketPage;
            setData(response);
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "An unexpected error occurred while loading tickets.",
            );
        } finally {
            setIsLoading(false);
        }
    }, [query]);

    useEffect(() => {
        const timeout = window.setTimeout(() => void loadTickets(), 150);
        return () => window.clearTimeout(timeout);
    }, [loadTickets]);

    useEffect(() => {
        setPage(1);
    }, [clientId, contactId, priority, search, status]);

    if (isLoading && !data) {
        return <DataLoading label="Loading ticket queues..." />;
    }

    if (error && !data) {
        return <DataError message={error} onRetry={() => void loadTickets()} />;
    }

    const tickets = data?.items ?? [];
    const scoped = Boolean(clientId || contactId);

    return (
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950/60">
            {scoped ? (
                <div className="flex items-center justify-between gap-4 border-b border-slate-800 bg-cyan-950/10 px-4 py-3">
                    <p className="text-xs text-cyan-300">
                        This view is scoped to a client{contactId ? " contact" : ""}.
                    </p>
                    <Link
                        href="/admin/tickets"
                        className="text-xs font-medium text-slate-400 hover:text-white"
                    >
                        Clear scope
                    </Link>
                </div>
            ) : null}
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

            {error ? (
                <div className="border-b border-slate-800 p-4">
                    <DataError message={error} onRetry={() => void loadTickets()} />
                </div>
            ) : null}

            {tickets.length === 0 ? (
                <EmptyState
                    title="No tickets match this view"
                    description="Try changing the filters, or seed development data to populate realistic support conversations."
                />
            ) : (
                <Table>
                    <TableHead>
                        <tr>
                            <TableHeaderCell>Ticket</TableHeaderCell>
                            <TableHeaderCell>Queue</TableHeaderCell>
                            <TableHeaderCell>Customer / vendor</TableHeaderCell>
                            <TableHeaderCell>Status</TableHeaderCell>
                            <TableHeaderCell>Priority</TableHeaderCell>
                            <TableHeaderCell>Updated</TableHeaderCell>
                            <TableHeaderCell>Owner</TableHeaderCell>
                        </tr>
                    </TableHead>
                    <TableBody>
                        {tickets.map((ticket) => (
                            <TableRow key={ticket.id}>
                                <TableCell>
                                    <Link
                                        href={`/admin/tickets/${ticket.id}`}
                                        className="block font-medium text-slate-100 transition hover:text-cyan-300"
                                    >
                                        {ticket.subject}
                                    </Link>
                                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                                        <span className="font-mono text-slate-400">
                                            {ticket.reference}
                                        </span>
                                        <span>{label(ticket.classification)}</span>
                                        <span>{ticket.message_count} messages</span>
                                    </div>
                                </TableCell>
                                <TableCell>
                                    <div className="text-slate-300">{ticket.queue_name}</div>
                                    <div className="mt-1 text-xs text-slate-500">
                                        {ticket.brand_name}
                                    </div>
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
                                    <Badge className={statusClass(ticket.status)}>
                                        {label(ticket.status)}
                                    </Badge>
                                </TableCell>
                                <TableCell>
                                    <Badge className={priorityClass(ticket.priority)}>
                                        {label(ticket.priority)}
                                    </Badge>
                                </TableCell>
                                <TableCell className="text-slate-400">
                                    {formatDate(ticket.last_message_at)}
                                </TableCell>
                                <TableCell className="text-slate-400">
                                    {ticket.assigned_to_name || "Unassigned"}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
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
