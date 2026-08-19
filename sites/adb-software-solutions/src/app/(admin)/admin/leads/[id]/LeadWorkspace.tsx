"use client";

import {
    Badge,
    ButtonLink,
    Card,
    DataError,
    DataLoading,
    EmptyState,
} from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

interface RelatedTicket {
    id: number;
    reference: string;
    subject: string;
    status: string;
    priority: string;
    queue_name: string;
    last_message_at: string | null;
}

interface LeadDetail {
    id: number;
    name: string;
    email: string;
    phone: string;
    company: string;
    brand_id: number | null;
    brand_name: string | null;
    status_id: number | null;
    status_name: string | null;
    source_id: number | null;
    source_name: string | null;
    message: string;
    notes: string;
    created_at: string;
    updated_at: string;
    related_tickets: RelatedTicket[];
}

function formatDate(value: string | null) {
    if (!value) return "No activity";
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    }).format(new Date(value));
}

function label(value: string) {
    return value
        .split("_")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
}

export function LeadWorkspace({ leadId }: { leadId: number }) {
    const [lead, setLead] = useState<LeadDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadLead = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            setLead((await fetchAPI(AdminAPI.leads.get(leadId))) as LeadDetail);
        } catch (loadError) {
            setError(loadError instanceof Error ? loadError.message : "Unable to load lead details.");
        } finally {
            setIsLoading(false);
        }
    }, [leadId]);

    useEffect(() => {
        void loadLead();
    }, [loadLead]);

    if (isLoading) return <DataLoading label="Loading lead..." />;
    if (error || !lead) {
        return (
            <DataError
                message={error ?? "Lead could not be loaded."}
                onRetry={() => void loadLead()}
            />
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                    <Link href="/admin/leads" className="text-xs text-slate-500 hover:text-slate-300">
                        ← Leads
                    </Link>
                    <div className="mt-2 flex flex-wrap items-center gap-3">
                        <h1 className="text-2xl font-semibold text-white">
                            {lead.company || lead.name}
                        </h1>
                        <Badge>{lead.status_name || "Unassigned"}</Badge>
                    </div>
                    {lead.company ? <p className="mt-1 text-sm text-slate-400">{lead.name}</p> : null}
                </div>
                <div className="flex flex-wrap gap-2">
                    <a
                        href={`mailto:${lead.email}`}
                        className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-900"
                    >
                        Email
                    </a>
                    {lead.phone ? (
                        <a
                            href={`tel:${lead.phone}`}
                            className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-900"
                        >
                            Call
                        </a>
                    ) : null}
                    <ButtonLink href={`/admin/leads/${lead.id}/edit`} variant="secondary">
                        Edit lead
                    </ButtonLink>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
                <Card className="p-5 md:col-span-2">
                    <h2 className="text-sm font-semibold text-white">Opportunity</h2>
                    <dl className="mt-4 grid gap-4 text-sm sm:grid-cols-2">
                        <div>
                            <dt className="text-xs text-slate-500">Email</dt>
                            <dd className="mt-1 text-slate-300">{lead.email}</dd>
                        </div>
                        <div>
                            <dt className="text-xs text-slate-500">Phone</dt>
                            <dd className="mt-1 text-slate-300">{lead.phone || "—"}</dd>
                        </div>
                        <div>
                            <dt className="text-xs text-slate-500">Brand</dt>
                            <dd className="mt-1 text-slate-300">{lead.brand_name || "Unassigned"}</dd>
                        </div>
                        <div>
                            <dt className="text-xs text-slate-500">Source</dt>
                            <dd className="mt-1 text-slate-300">{lead.source_name || "Unknown"}</dd>
                        </div>
                        <div>
                            <dt className="text-xs text-slate-500">Created</dt>
                            <dd className="mt-1 text-slate-300">{formatDate(lead.created_at)}</dd>
                        </div>
                        <div>
                            <dt className="text-xs text-slate-500">Last updated</dt>
                            <dd className="mt-1 text-slate-300">{formatDate(lead.updated_at)}</dd>
                        </div>
                    </dl>
                </Card>
                <Card className="p-5">
                    <h2 className="text-sm font-semibold text-white">Internal notes</h2>
                    <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-400">
                        {lead.notes || "No internal notes recorded."}
                    </p>
                </Card>
            </div>

            <Card className="p-5">
                <h2 className="text-sm font-semibold text-white">Original enquiry</h2>
                <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-300">
                    {lead.message || "No enquiry text was recorded for this lead."}
                </p>
            </Card>

            <Card className="p-5">
                <div className="mb-4">
                    <h2 className="text-sm font-semibold text-white">Related tickets and email</h2>
                    <p className="mt-1 text-xs text-slate-500">
                        Recent ticket conversations matched to {lead.email}.
                    </p>
                </div>
                {lead.related_tickets.length === 0 ? (
                    <EmptyState
                        title="No related conversations"
                        description="Ticket conversations from this lead's email address will appear here automatically."
                    />
                ) : (
                    <div className="divide-y divide-slate-800">
                        {lead.related_tickets.map((ticket) => (
                            <Link
                                key={ticket.id}
                                href={`/admin/tickets/${ticket.id}`}
                                className="flex flex-col gap-2 px-1 py-4 transition hover:bg-slate-900/40 sm:flex-row sm:items-center sm:justify-between sm:px-3"
                            >
                                <div className="min-w-0">
                                    <div className="truncate text-sm font-medium text-slate-200">
                                        {ticket.subject}
                                    </div>
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
                    </div>
                )}
            </Card>
        </div>
    );
}
