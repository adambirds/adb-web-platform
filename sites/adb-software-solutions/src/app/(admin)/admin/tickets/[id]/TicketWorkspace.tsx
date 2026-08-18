"use client";

import { Badge, Button, Card, DataError, DataLoading, Input, Textarea } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import Link from "next/link";
import { type FormEvent, useCallback, useEffect, useState } from "react";

interface TicketMessage {
    id: number;
    direction: "inbound" | "outbound";
    sender_name: string;
    sender_address: string;
    to_recipients: string[];
    cc_recipients: string[];
    bcc_recipients: string[];
    matched_contact_id: number | null;
    matched_contact_name: string | null;
    subject: string;
    body_text: string;
    body_text_normalised: string;
    sent_or_received_at: string;
    delivery_status: string;
    created_by_name: string | null;
}

interface TicketNote {
    id: number;
    author_name: string | null;
    body: string;
    created_at: string;
}

interface TicketAttachment {
    id: number;
    original_filename: string;
    detected_content_type: string;
    declared_content_type: string;
    size: number;
    scan_status: string;
    scan_engine: string;
}

interface TicketDetail {
    id: number;
    reference: string;
    subject: string;
    brand_name: string;
    queue_name: string;
    client_id: number | null;
    client_name: string | null;
    primary_contact_id: number | null;
    primary_contact_name: string | null;
    status: string;
    priority: string;
    classification: string;
    source: string;
    assigned_to_name: string | null;
    first_response_at: string | null;
    last_message_at: string | null;
    created_at: string;
    messages: TicketMessage[];
    notes: TicketNote[];
    attachments: TicketAttachment[];
}

function label(value: string) {
    return value
        .split("_")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
}

function formatDate(value: string | null) {
    if (!value) return "—";
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    }).format(new Date(value));
}

function formatBytes(value: number) {
    if (value < 1024) return `${value} B`;
    if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
    return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function parseRecipients(value: string) {
    return [
        ...new Set(
            value
                .split(/[;,]/)
                .map((address) => address.trim().toLowerCase())
                .filter(Boolean),
        ),
    ];
}

export function TicketWorkspace({ ticketId }: { ticketId: number }) {
    const [ticket, setTicket] = useState<TicketDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [replyBody, setReplyBody] = useState("");
    const [ccRecipients, setCcRecipients] = useState("");
    const [bccRecipients, setBccRecipients] = useState("");
    const [showRecipients, setShowRecipients] = useState(false);
    const [isSubmittingReply, setIsSubmittingReply] = useState(false);
    const [replyError, setReplyError] = useState<string | null>(null);
    const [replyStatus, setReplyStatus] = useState<string | null>(null);

    const loadTicket = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            setTicket((await fetchAPI(AdminAPI.tickets.get(ticketId))) as TicketDetail);
        } catch (loadError) {
            setError(loadError instanceof Error ? loadError.message : "Unable to load ticket.");
        } finally {
            setIsLoading(false);
        }
    }, [ticketId]);

    useEffect(() => {
        void loadTicket();
    }, [loadTicket]);

    async function handleReply(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        const bodyText = replyBody.trim();
        if (!bodyText || isSubmittingReply) return;

        try {
            setIsSubmittingReply(true);
            setReplyError(null);
            setReplyStatus(null);

            const queuedMessage = (await fetchAPI(AdminAPI.tickets.reply(ticketId), {
                method: "POST",
                body: JSON.stringify({
                    body_text: bodyText,
                    cc_recipients: parseRecipients(ccRecipients),
                    bcc_recipients: parseRecipients(bccRecipients),
                }),
            })) as TicketMessage;

            setTicket((currentTicket) =>
                currentTicket
                    ? {
                          ...currentTicket,
                          messages: [...currentTicket.messages, queuedMessage],
                          last_message_at: queuedMessage.sent_or_received_at,
                      }
                    : currentTicket,
            );
            setReplyBody("");
            setCcRecipients("");
            setBccRecipients("");
            setShowRecipients(false);
            setReplyStatus("Reply queued for delivery through Microsoft 365.");
        } catch (submitError) {
            setReplyError(
                submitError instanceof Error ? submitError.message : "Unable to queue reply.",
            );
        } finally {
            setIsSubmittingReply(false);
        }
    }

    if (isLoading) return <DataLoading label="Loading ticket conversation..." />;
    if (error || !ticket) {
        return (
            <DataError
                message={error ?? "Ticket could not be loaded."}
                onRetry={() => void loadTicket()}
            />
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <Link href="/admin/tickets" className="text-xs text-slate-500 hover:text-slate-300">
                    ← Tickets
                </Link>
                <div className="mt-2 flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
                    <div>
                        <div className="flex flex-wrap items-center gap-2">
                            <span className="font-mono text-xs text-cyan-400">{ticket.reference}</span>
                            <Badge>{label(ticket.status)}</Badge>
                            <Badge>{label(ticket.priority)}</Badge>
                        </div>
                        <h1 className="mt-2 text-2xl font-semibold text-white">{ticket.subject}</h1>
                        <p className="mt-1 text-sm text-slate-500">
                            {ticket.queue_name} · {ticket.brand_name} · {label(ticket.classification)}
                        </p>
                    </div>
                    <div className="text-right text-xs text-slate-500">
                        <div>Opened {formatDate(ticket.created_at)}</div>
                        <div className="mt-1">Last activity {formatDate(ticket.last_message_at)}</div>
                    </div>
                </div>
            </div>

            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
                <div className="space-y-4">
                    {ticket.messages.map((message) => (
                        <Card
                            key={message.id}
                            className={
                                message.direction === "outbound"
                                    ? "border-cyan-900/50 bg-cyan-950/10 p-5"
                                    : "p-5"
                            }
                        >
                            <div className="flex flex-col gap-2 border-b border-slate-800 pb-3 sm:flex-row sm:items-start sm:justify-between">
                                <div>
                                    <div className="font-medium text-slate-200">
                                        {message.sender_name || message.sender_address}
                                    </div>
                                    <div className="mt-1 text-xs text-slate-500">
                                        {message.sender_address}
                                        {message.matched_contact_name
                                            ? ` · ${message.matched_contact_name}`
                                            : ""}
                                    </div>
                                </div>
                                <div className="text-xs text-slate-500">
                                    {formatDate(message.sent_or_received_at)}
                                </div>
                            </div>
                            <div className="mt-4 whitespace-pre-wrap text-sm leading-6 text-slate-300">
                                {message.body_text_normalised || message.body_text || "No message body."}
                            </div>
                            <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-600">
                                <span>{message.direction === "inbound" ? "Inbound" : "Outbound"}</span>
                                {message.delivery_status ? <span>· {label(message.delivery_status)}</span> : null}
                                {message.created_by_name ? <span>· {message.created_by_name}</span> : null}
                            </div>
                        </Card>
                    ))}

                    <Card className="p-5">
                        <form onSubmit={(event) => void handleReply(event)}>
                            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                                <div>
                                    <h2 className="text-sm font-semibold text-white">Reply</h2>
                                    <p className="mt-1 text-xs leading-5 text-slate-500">
                                        Replies are queued through the Microsoft 365 mailbox attached to this ticket.
                                    </p>
                                </div>
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setShowRecipients((value) => !value)}
                                >
                                    {showRecipients ? "Hide CC/BCC" : "Add CC/BCC"}
                                </Button>
                            </div>

                            {showRecipients ? (
                                <div className="mt-4 grid gap-3 md:grid-cols-2">
                                    <label className="text-xs text-slate-400">
                                        CC
                                        <Input
                                            value={ccRecipients}
                                            onChange={(event) => setCcRecipients(event.target.value)}
                                            placeholder="person@example.com, another@example.com"
                                            className="mt-1"
                                        />
                                    </label>
                                    <label className="text-xs text-slate-400">
                                        BCC
                                        <Input
                                            value={bccRecipients}
                                            onChange={(event) => setBccRecipients(event.target.value)}
                                            placeholder="person@example.com"
                                            className="mt-1"
                                        />
                                    </label>
                                </div>
                            ) : null}

                            <Textarea
                                value={replyBody}
                                onChange={(event) => setReplyBody(event.target.value)}
                                placeholder="Write your reply..."
                                rows={8}
                                className="mt-4 min-h-40 resize-y"
                            />

                            {replyError ? (
                                <p className="mt-3 text-sm text-red-300">{replyError}</p>
                            ) : null}
                            {replyStatus ? (
                                <p className="mt-3 text-sm text-emerald-300">{replyStatus}</p>
                            ) : null}

                            <div className="mt-4 flex justify-end">
                                <Button
                                    type="submit"
                                    disabled={!replyBody.trim() || isSubmittingReply}
                                >
                                    {isSubmittingReply ? "Queuing..." : "Queue reply"}
                                </Button>
                            </div>
                        </form>
                    </Card>
                </div>

                <aside className="space-y-4">
                    <Card className="p-5">
                        <h2 className="text-sm font-semibold text-white">Customer context</h2>
                        <dl className="mt-4 space-y-4 text-sm">
                            <div>
                                <dt className="text-xs text-slate-500">Client</dt>
                                <dd className="mt-1 text-slate-300">
                                    {ticket.client_id ? (
                                        <Link
                                            href={`/admin/clients/${ticket.client_id}`}
                                            className="hover:text-cyan-300"
                                        >
                                            {ticket.client_name}
                                        </Link>
                                    ) : (
                                        "Unmatched"
                                    )}
                                </dd>
                            </div>
                            <div>
                                <dt className="text-xs text-slate-500">Primary contact</dt>
                                <dd className="mt-1 text-slate-300">
                                    {ticket.primary_contact_name || "Unmatched"}
                                </dd>
                            </div>
                            <div>
                                <dt className="text-xs text-slate-500">Assigned to</dt>
                                <dd className="mt-1 text-slate-300">
                                    {ticket.assigned_to_name || "Unassigned"}
                                </dd>
                            </div>
                            <div>
                                <dt className="text-xs text-slate-500">Source</dt>
                                <dd className="mt-1 text-slate-300">{label(ticket.source)}</dd>
                            </div>
                        </dl>
                    </Card>

                    <Card className="p-5">
                        <h2 className="text-sm font-semibold text-white">Internal notes</h2>
                        <div className="mt-4 space-y-3">
                            {ticket.notes.length === 0 ? (
                                <p className="text-sm text-slate-500">No internal notes.</p>
                            ) : (
                                ticket.notes.map((note) => (
                                    <div key={note.id} className="rounded-lg bg-slate-900 p-3">
                                        <p className="whitespace-pre-wrap text-sm text-slate-300">
                                            {note.body}
                                        </p>
                                        <div className="mt-2 text-xs text-slate-600">
                                            {note.author_name || "System"} · {formatDate(note.created_at)}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </Card>

                    <Card className="p-5">
                        <h2 className="text-sm font-semibold text-white">Attachments</h2>
                        <div className="mt-4 space-y-3">
                            {ticket.attachments.length === 0 ? (
                                <p className="text-sm text-slate-500">
                                    No visible attachment metadata.
                                </p>
                            ) : (
                                ticket.attachments.map((attachment) => (
                                    <div key={attachment.id} className="rounded-lg border border-slate-800 p-3">
                                        <div className="text-sm font-medium text-slate-300">
                                            {attachment.original_filename}
                                        </div>
                                        <div className="mt-1 text-xs text-slate-500">
                                            {attachment.detected_content_type ||
                                                attachment.declared_content_type ||
                                                "Unknown type"}
                                            {" · "}
                                            {formatBytes(attachment.size)}
                                        </div>
                                        <div className="mt-2 text-xs text-slate-500">
                                            Scan: {label(attachment.scan_status)}
                                            {attachment.scan_engine ? ` · ${attachment.scan_engine}` : ""}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </Card>

                    <Card className="p-5">
                        <h2 className="text-sm font-semibold text-white">Client resources</h2>
                        <p className="mt-2 text-sm leading-6 text-slate-500">
                            Knowledge base, infrastructure and credential shortcuts will appear here as the
                            ticket workspace is connected to the wider client context.
                        </p>
                    </Card>
                </aside>
            </div>
        </div>
    );
}
