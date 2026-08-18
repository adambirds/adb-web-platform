"use client";

import { RelatedTicketList } from "@/components/ticketing/RelatedTicketList";
import { Badge, Card, DataError, DataLoading } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

interface Contact {
    id: number;
    name: string;
    email: string;
    phone: string;
    role: string;
    is_active: boolean;
    is_primary: boolean;
    is_billing: boolean;
    is_technical: boolean;
}

interface ClientDetail {
    id: number;
    name: string;
    company: string;
    contacts: Contact[];
}

export function ContactWorkspace({
    clientId,
    contactId,
}: {
    clientId: number;
    contactId: number;
}) {
    const [client, setClient] = useState<ClientDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadContact = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            setClient((await fetchAPI(AdminAPI.clients.get(clientId))) as ClientDetail);
        } catch (loadError) {
            setError(loadError instanceof Error ? loadError.message : "Unable to load contact.");
        } finally {
            setIsLoading(false);
        }
    }, [clientId]);

    useEffect(() => {
        void loadContact();
    }, [loadContact]);

    if (isLoading) return <DataLoading label="Loading contact workspace..." />;
    if (error || !client) {
        return (
            <DataError
                message={error ?? "Contact could not be loaded."}
                onRetry={() => void loadContact()}
            />
        );
    }

    const contact = client.contacts.find((item) => item.id === contactId);
    if (!contact) {
        return (
            <DataError
                message="Contact not found or outside your permission scope."
                onRetry={() => void loadContact()}
            />
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <Link
                    href={`/admin/clients/${client.id}`}
                    className="text-xs text-slate-500 hover:text-slate-300"
                >
                    ← {client.company || client.name}
                </Link>
                <div className="mt-2 flex flex-wrap items-center gap-3">
                    <h1 className="text-2xl font-semibold text-white">{contact.name}</h1>
                    {!contact.is_active ? <Badge>Inactive</Badge> : null}
                </div>
                <p className="mt-1 text-sm text-slate-400">
                    {contact.role || "Client contact"} at {client.company || client.name}
                </p>
            </div>

            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
                <Card className="p-5">
                    <h2 className="text-sm font-semibold text-white">Contact details</h2>
                    <dl className="mt-4 grid gap-4 text-sm sm:grid-cols-2">
                        <div>
                            <dt className="text-xs text-slate-500">Email</dt>
                            <dd className="mt-1">
                                <a
                                    href={`mailto:${contact.email}`}
                                    className="text-slate-300 hover:text-cyan-300"
                                >
                                    {contact.email}
                                </a>
                            </dd>
                        </div>
                        <div>
                            <dt className="text-xs text-slate-500">Phone</dt>
                            <dd className="mt-1 text-slate-300">{contact.phone || "—"}</dd>
                        </div>
                    </dl>
                </Card>

                <Card className="p-5">
                    <h2 className="text-sm font-semibold text-white">Responsibilities</h2>
                    <div className="mt-4 flex flex-wrap gap-2">
                        {contact.is_primary ? <Badge>Primary</Badge> : null}
                        {contact.is_billing ? <Badge>Billing</Badge> : null}
                        {contact.is_technical ? <Badge>Technical</Badge> : null}
                        {!contact.is_primary && !contact.is_billing && !contact.is_technical ? (
                            <span className="text-sm text-slate-500">No special responsibilities.</span>
                        ) : null}
                    </div>
                </Card>
            </div>

            <Card className="p-5">
                <div className="mb-4 flex items-start justify-between gap-4">
                    <div>
                        <h2 className="text-sm font-semibold text-white">Tickets</h2>
                        <p className="mt-1 text-xs text-slate-500">
                            Conversations where this person is the matched primary contact.
                        </p>
                    </div>
                    <Link
                        href={`/admin/tickets?client_id=${client.id}&primary_contact_id=${contact.id}`}
                        className="text-xs font-medium text-cyan-400 hover:text-cyan-300"
                    >
                        View all
                    </Link>
                </div>
                <RelatedTicketList clientId={client.id} contactId={contact.id} />
            </Card>
        </div>
    );
}
