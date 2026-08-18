"use client";

import { Badge, DataError, DataLoading, EmptyState } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

interface TicketListItem {
    id: number;
    reference: string;
    subject: string;
    queue_name: string;
    status: string;
    priority: string;
    last_message_at: string | null;
}

interface TicketPage {
    items: TicketListItem[];
    total: number;
}

interface RelatedTicketListProps {
    clientId?: number;
    contactId?: number;
    limit?: number;
}

function label(value: string) {
    return value
        .split("_")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
}

function formatDate(value: string | null) {
    if (!value) return "No activity";
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
    }).format(new Date(value));
}

export function RelatedTicketList({ clientId, contactId, limit = 8 }: RelatedTicketListProps) {
    const [data, setData] = useState<TicketPage | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const query = useMemo(() => {
        const params = new URLSearchParams({ page: "1", page_size: String(limit) });
        if (clientId) params.set("client_id", String(clientId));
        if (contactId) params.set("primary_contact_id", String(contactId));
        return params.toString();
    }, [clientId, contactId, limit]);

    const loadTickets = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            setData((await fetchAPI(AdminAPI.tickets.list(query))) as TicketPage);
        } catch (loadError) {
            setError(loadError instanceof Error ? loadError.message : "Unable to load related tickets.");
        } finally {
            setIsLoading(false);
        }
    }, [query]);

    useEffect(() => {
        void loadTickets();
    }, [loadTickets]);

    if (isLoading) return <DataLoading label="Loading tickets..." />;
    if (error) return <DataError message={error} onRetry={() => void loadTickets()} />;

    const tickets = data?.items ?? [];
    if (tickets.length === 0) {
        return (
            <EmptyState
                title="No visible tickets"
                description="Tickets linked to this account or contact will appear here."
            />
        );
    }

    return (
        <div className="divide-y divide-slate-800">
            {tickets.map((ticket) => (
                <Link
                    key={ticket.id}
                    href={`/admin/tickets/${ticket.id}`}
                    className="flex flex-col gap-2 px-1 py-4 transition hover:bg-slate-900/40 sm:flex-row sm:items-center sm:justify-between sm:px-3"
                >
                    <div className="min-w-0">
                        <div className="truncate text-sm font-medium text-slate-200">{ticket.subject}</div>
                        <div className="mt-1 flex flex-wrap gap-2 text-xs text-slate-500">
                            <span className="font-mono text-slate-400">{ticket.reference}</span>
                            <span>{ticket.queue_name}</span>
                            <span>{formatDate(ticket.last_message_at)}</span>
                        </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                        <Badge>{label(ticket.priority)}</Badge>
                        <Badge>{label(ticket.status)}</Badge>
                    </div>
                </Link>
            ))}
            {(data?.total ?? 0) > tickets.length ? (
                <div className="pt-4 text-right text-xs text-slate-500">
                    Showing {tickets.length} of {data?.total} tickets.
                </div>
            ) : null}
        </div>
    );
}
