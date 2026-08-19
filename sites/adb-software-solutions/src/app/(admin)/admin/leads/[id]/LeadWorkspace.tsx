"use client";

import {
    Badge,
    Button,
    ButtonLink,
    Card,
    DataError,
    DataLoading,
    EmptyState,
    Select,
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

interface LeadAgent {
    id: string;
    name: string;
    email: string;
}

interface LeadOptions {
    assignees: LeadAgent[];
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
    assigned_to_id: string | null;
    assigned_to_name: string | null;
    converted_client_id: number | null;
    converted_contact_id: number | null;
    converted_by_name: string | null;
    converted_at: string | null;
    can_assign: boolean;
    can_convert: boolean;
    message: string;
    notes: string;
    created_at: string;
    updated_at: string;
    related_tickets: RelatedTicket[];
}

interface LeadConversionResponse {
    lead: LeadDetail;
    client_id: number;
    contact_id: number;
    linked_ticket_count: number;
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
    const [options, setOptions] = useState<LeadOptions>({ assignees: [] });
    const [isLoading, setIsLoading] = useState(true);
    const [isAssigning, setIsAssigning] = useState(false);
    const [isConverting, setIsConverting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [actionMessage, setActionMessage] = useState<string | null>(null);

    const loadLead = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const [leadRow, optionRows] = await Promise.all([
                fetchAPI(AdminAPI.leads.get(leadId)) as Promise<LeadDetail>,
                fetchAPI(AdminAPI.leads.options()) as Promise<LeadOptions>,
            ]);
            setLead(leadRow);
            setOptions(optionRows);
        } catch (loadError) {
            setError(loadError instanceof Error ? loadError.message : "Unable to load lead details.");
        } finally {
            setIsLoading(false);
        }
    }, [leadId]);

    useEffect(() => {
        void loadLead();
    }, [loadLead]);

    async function updateAssignment(assignedToId: string) {
        if (!lead) return;

        try {
            setIsAssigning(true);
            setError(null);
            setActionMessage(null);
            const updated = (await fetchAPI(AdminAPI.leads.assignment(lead.id), {
                method: "POST",
                body: JSON.stringify({ assigned_to_id: assignedToId || null }),
            })) as LeadDetail;
            setLead(updated);
            setActionMessage(
                updated.assigned_to_name
                    ? `Lead assigned to ${updated.assigned_to_name}.`
                    : "Lead assignment cleared.",
            );
        } catch (assignmentError) {
            setError(
                assignmentError instanceof Error
                    ? assignmentError.message
                    : "Unable to update lead assignment.",
            );
        } finally {
            setIsAssigning(false);
        }
    }

    async function convertToClient() {
        if (!lead) return;
        if (
            !window.confirm(
                `Convert ${lead.company || lead.name} into a client account and primary contact?`,
            )
        ) {
            return;
        }

        try {
            setIsConverting(true);
            setError(null);
            setActionMessage(null);
            const result = (await fetchAPI(AdminAPI.leads.convert(lead.id), {
                method: "POST",
            })) as LeadConversionResponse;
            setLead(result.lead);
            setActionMessage(
                `Lead converted. ${result.linked_ticket_count} existing conversation${
                    result.linked_ticket_count === 1 ? " was" : "s were"
                } linked to the new client.`,
            );
        } catch (conversionError) {
            setError(
                conversionError instanceof Error
                    ? conversionError.message
                    : "Unable to convert this lead.",
            );
        } finally {
            setIsConverting(false);
        }
    }

    if (isLoading) return <DataLoading label="Loading lead..." />;
    if (error && !lead) {
        return <DataError message={error} onRetry={() => void loadLead()} />;
    }
    if (!lead) {
        return (
            <DataError
                message="Lead could not be loaded."
                onRetry={() => void loadLead()}
            />
        );
    }

    return (
        <div className="space-y-6">
            {error ? (
                <div
                    role="alert"
                    className="rounded-lg border border-red-900/70 bg-red-950/40 px-4 py-3 text-sm text-red-200"
                >
                    {error}
                </div>
            ) : null}
            {actionMessage ? (
                <div className="rounded-lg border border-emerald-900/70 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-200">
                    {actionMessage}
                </div>
            ) : null}

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
                        {lead.converted_at ? <Badge>Converted</Badge> : null}
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
                    {lead.converted_client_id ? (
                        <ButtonLink href={`/admin/clients/${lead.converted_client_id}`}>
                            View client
                        </ButtonLink>
                    ) : null}
                    <ButtonLink href={`/admin/leads/${lead.id}/edit`} variant="secondary">
                        Edit lead
                    </ButtonLink>
                </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
                <Card className="p-5 lg:col-span-2">
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

                <div className="space-y-4">
                    <Card className="p-5">
                        <h2 className="text-sm font-semibold text-white">Ownership</h2>
                        {lead.can_assign ? (
                            <label className="mt-4 block space-y-1.5 text-sm font-medium text-slate-300">
                                <span>Assigned to</span>
                                <Select
                                    value={lead.assigned_to_id ?? ""}
                                    disabled={isAssigning}
                                    onChange={(event) => void updateAssignment(event.target.value)}
                                >
                                    <option value="">Unassigned</option>
                                    {options.assignees.map((assignee) => (
                                        <option key={assignee.id} value={assignee.id}>
                                            {assignee.name}
                                        </option>
                                    ))}
                                </Select>
                            </label>
                        ) : (
                            <p className="mt-3 text-sm text-slate-400">
                                {lead.assigned_to_name || "Unassigned"}
                            </p>
                        )}
                    </Card>

                    <Card className="p-5">
                        <h2 className="text-sm font-semibold text-white">Conversion</h2>
                        {lead.converted_at ? (
                            <div className="mt-3 space-y-3 text-sm text-slate-400">
                                <p>Converted {formatDate(lead.converted_at)}.</p>
                                {lead.converted_by_name ? <p>By {lead.converted_by_name}.</p> : null}
                                {lead.converted_client_id ? (
                                    <ButtonLink
                                        href={`/admin/clients/${lead.converted_client_id}`}
                                        variant="secondary"
                                        size="sm"
                                    >
                                        Open client account
                                    </ButtonLink>
                                ) : null}
                            </div>
                        ) : lead.can_convert ? (
                            <div className="mt-3 space-y-3">
                                <p className="text-sm leading-6 text-slate-400">
                                    Create the client account and primary contact, then attach unmatched
                                    conversations from this email address.
                                </p>
                                <Button
                                    type="button"
                                    onClick={() => void convertToClient()}
                                    disabled={isConverting}
                                >
                                    {isConverting ? "Converting..." : "Convert to client"}
                                </Button>
                            </div>
                        ) : (
                            <p className="mt-3 text-sm text-slate-500">
                                You do not have permission to convert this lead.
                            </p>
                        )}
                    </Card>

                    <Card className="p-5">
                        <h2 className="text-sm font-semibold text-white">Internal notes</h2>
                        <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-400">
                            {lead.notes || "No internal notes recorded."}
                        </p>
                    </Card>
                </div>
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
