"use client";

import {
    Badge,
    Card,
    DataError,
    DataLoading,
    EmptyState,
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

interface Project {
    id: number;
    name: string;
    status: string;
    start_date: string;
    end_date: string | null;
    budget: string | null;
}

interface ClientDetail {
    id: number;
    name: string;
    company: string;
    email: string;
    phone: string;
    address: string;
    city: string;
    state: string;
    country: string;
    postal_code: string;
    status: string;
    notes: string;
    contacts: Contact[];
    projects: Project[];
}

export function ClientWorkspace({ clientId }: { clientId: number }) {
    const [client, setClient] = useState<ClientDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadClient = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            setClient((await fetchAPI(AdminAPI.clients.get(clientId))) as ClientDetail);
        } catch (loadError) {
            setError(loadError instanceof Error ? loadError.message : "Unable to load client workspace.");
        } finally {
            setIsLoading(false);
        }
    }, [clientId]);

    useEffect(() => {
        void loadClient();
    }, [loadClient]);

    if (isLoading) return <DataLoading label="Loading client workspace..." />;
    if (error || !client) {
        return <DataError message={error ?? "Client could not be loaded."} onRetry={() => void loadClient()} />;
    }

    const location = [client.address, client.city, client.state, client.postal_code, client.country]
        .filter(Boolean)
        .join(", ");

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                    <Link href="/admin/clients" className="text-xs text-slate-500 hover:text-slate-300">
                        ← Clients
                    </Link>
                    <div className="mt-2 flex items-center gap-3">
                        <h1 className="text-2xl font-semibold text-white">{client.company || client.name}</h1>
                        <Badge>{client.status}</Badge>
                    </div>
                    {client.company && client.name ? (
                        <p className="mt-1 text-sm text-slate-400">Primary account contact: {client.name}</p>
                    ) : null}
                </div>
                <div className="flex gap-2 text-sm">
                    <a href={`mailto:${client.email}`} className="rounded-lg border border-slate-700 px-3 py-2 text-slate-300 hover:bg-slate-900">
                        Email
                    </a>
                    {client.phone ? (
                        <a href={`tel:${client.phone}`} className="rounded-lg border border-slate-700 px-3 py-2 text-slate-300 hover:bg-slate-900">
                            Call
                        </a>
                    ) : null}
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
                <Card className="p-5 md:col-span-2">
                    <h2 className="text-sm font-semibold text-white">Account</h2>
                    <dl className="mt-4 grid gap-4 text-sm sm:grid-cols-2">
                        <div><dt className="text-xs text-slate-500">Email</dt><dd className="mt-1 text-slate-300">{client.email}</dd></div>
                        <div><dt className="text-xs text-slate-500">Phone</dt><dd className="mt-1 text-slate-300">{client.phone || "—"}</dd></div>
                        <div className="sm:col-span-2"><dt className="text-xs text-slate-500">Address</dt><dd className="mt-1 text-slate-300">{location || "—"}</dd></div>
                    </dl>
                </Card>
                <Card className="p-5">
                    <h2 className="text-sm font-semibold text-white">Notes</h2>
                    <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-400">{client.notes || "No account notes recorded."}</p>
                </Card>
            </div>

            <Card className="p-5">
                <div className="mb-4">
                    <h2 className="text-sm font-semibold text-white">Contacts</h2>
                    <p className="mt-1 text-xs text-slate-500">People associated with this client account.</p>
                </div>
                {client.contacts.length === 0 ? (
                    <EmptyState title="No visible contacts" description="No contacts are available in your current permission scope." />
                ) : (
                    <Table>
                        <TableHead><tr><TableHeaderCell>Name</TableHeaderCell><TableHeaderCell>Role</TableHeaderCell><TableHeaderCell>Contact</TableHeaderCell><TableHeaderCell>Responsibilities</TableHeaderCell></tr></TableHead>
                        <TableBody>
                            {client.contacts.map((contact) => (
                                <TableRow key={contact.id}>
                                    <TableCell><div className="font-medium text-slate-200">{contact.name}</div>{!contact.is_active ? <div className="text-xs text-slate-600">Inactive</div> : null}</TableCell>
                                    <TableCell className="text-slate-400">{contact.role || "—"}</TableCell>
                                    <TableCell><a href={`mailto:${contact.email}`} className="text-slate-300 hover:text-cyan-300">{contact.email}</a><div className="mt-1 text-xs text-slate-500">{contact.phone}</div></TableCell>
                                    <TableCell className="text-xs text-slate-400">{[contact.is_primary && "Primary", contact.is_billing && "Billing", contact.is_technical && "Technical"].filter(Boolean).join(" · ") || "—"}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                )}
            </Card>

            <Card className="p-5">
                <div className="mb-4">
                    <h2 className="text-sm font-semibold text-white">Projects</h2>
                    <p className="mt-1 text-xs text-slate-500">Current and historical work for this account.</p>
                </div>
                {client.projects.length === 0 ? (
                    <EmptyState title="No visible projects" description="No projects are available in your current permission scope." />
                ) : (
                    <Table>
                        <TableHead><tr><TableHeaderCell>Project</TableHeaderCell><TableHeaderCell>Status</TableHeaderCell><TableHeaderCell>Start</TableHeaderCell><TableHeaderCell>Budget</TableHeaderCell></tr></TableHead>
                        <TableBody>
                            {client.projects.map((project) => (
                                <TableRow key={project.id}>
                                    <TableCell><Link href={`/admin/projects/${project.id}`} className="font-medium text-slate-200 hover:text-cyan-300">{project.name}</Link></TableCell>
                                    <TableCell><Badge>{project.status}</Badge></TableCell>
                                    <TableCell className="text-slate-400">{project.start_date}</TableCell>
                                    <TableCell className="text-slate-400">{project.budget ? `£${Number(project.budget).toLocaleString("en-GB")}` : "—"}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                )}
            </Card>
        </div>
    );
}
