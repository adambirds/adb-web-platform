"use client";

import {
    Badge,
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

interface ClientSummary {
    id: number;
    name: string;
    company: string;
    email: string;
    status: string;
    contact_count: number;
    project_count: number;
}

function statusClasses(status: string) {
    if (status === "active") {
        return "border-emerald-900/70 bg-emerald-950/50 text-emerald-300";
    }
    if (status === "archived") {
        return "border-slate-700 bg-slate-900 text-slate-500";
    }
    return "border-amber-900/70 bg-amber-950/40 text-amber-300";
}

export function ClientList() {
    const [clients, setClients] = useState<ClientSummary[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadClients = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const data = (await fetchAPI(AdminAPI.clients.list())) as ClientSummary[];
            setClients(data);
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "An unexpected error occurred while loading clients.",
            );
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        void loadClients();
    }, [loadClients]);

    if (isLoading) return <DataLoading label="Loading client accounts..." />;
    if (error) return <DataError message={error} onRetry={() => void loadClients()} />;
    if (clients.length === 0) {
        return (
            <EmptyState
                title="No client accounts in your scope"
                description="Client accounts will appear here once they exist and your staff access profile grants visibility to them."
            />
        );
    }

    return (
        <Table>
            <TableHead>
                <tr>
                    <TableHeaderCell>Client</TableHeaderCell>
                    <TableHeaderCell>Status</TableHeaderCell>
                    <TableHeaderCell>Contacts</TableHeaderCell>
                    <TableHeaderCell>Projects</TableHeaderCell>
                    <TableHeaderCell>Primary email</TableHeaderCell>
                </tr>
            </TableHead>
            <TableBody>
                {clients.map((client) => (
                    <TableRow key={client.id}>
                        <TableCell>
                            <Link
                                href={`/admin/clients/${client.id}`}
                                className="font-medium text-slate-100 transition hover:text-cyan-300"
                            >
                                {client.company || client.name}
                            </Link>
                            {client.company && client.name ? (
                                <div className="mt-1 text-xs text-slate-500">{client.name}</div>
                            ) : null}
                        </TableCell>
                        <TableCell>
                            <Badge className={statusClasses(client.status)}>{client.status}</Badge>
                        </TableCell>
                        <TableCell className="tabular-nums text-slate-400">
                            {client.contact_count}
                        </TableCell>
                        <TableCell className="tabular-nums text-slate-400">
                            {client.project_count}
                        </TableCell>
                        <TableCell className="text-slate-400">{client.email}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
