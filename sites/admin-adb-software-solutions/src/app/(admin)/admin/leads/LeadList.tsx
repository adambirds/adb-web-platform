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
import { useCallback, useEffect, useState } from "react";

interface LeadSummary {
    id: number;
    name: string;
    company: string;
    email: string;
    status: string;
    source: string;
    brand: string;
    created_at: string;
}

function statusClasses(status: string) {
    const normalised = status.toLowerCase();
    if (normalised === "won") {
        return "border-emerald-900/70 bg-emerald-950/50 text-emerald-300";
    }
    if (normalised === "lost") {
        return "border-red-950 bg-red-950/30 text-red-300";
    }
    if (normalised === "proposal" || normalised === "qualified") {
        return "border-cyan-900/70 bg-cyan-950/40 text-cyan-300";
    }
    return "border-amber-900/70 bg-amber-950/40 text-amber-300";
}

function formatDate(value: string) {
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    }).format(new Date(value));
}

export function LeadList() {
    const [leads, setLeads] = useState<LeadSummary[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadLeads = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const data = (await fetchAPI(AdminAPI.leads.list())) as LeadSummary[];
            setLeads(data);
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "An unexpected error occurred while loading leads.",
            );
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        void loadLeads();
    }, [loadLeads]);

    if (isLoading) {
        return <DataLoading label="Loading sales pipeline..." />;
    }

    if (error) {
        return <DataError message={error} onRetry={() => void loadLeads()} />;
    }

    if (leads.length === 0) {
        return (
            <EmptyState
                title="No leads yet"
                description="New enquiries and sales opportunities will appear here as they enter the shared CRM."
            />
        );
    }

    return (
        <Table>
            <TableHead>
                <tr>
                    <TableHeaderCell>Lead</TableHeaderCell>
                    <TableHeaderCell>Status</TableHeaderCell>
                    <TableHeaderCell>Brand</TableHeaderCell>
                    <TableHeaderCell>Source</TableHeaderCell>
                    <TableHeaderCell>Received</TableHeaderCell>
                </tr>
            </TableHead>
            <TableBody>
                {leads.map((lead) => (
                    <TableRow key={lead.id}>
                        <TableCell>
                            <div className="font-medium text-slate-100">
                                {lead.company || lead.name}
                            </div>
                            <div className="mt-1 text-xs text-slate-500">
                                {lead.name} · {lead.email}
                            </div>
                        </TableCell>
                        <TableCell>
                            <Badge className={statusClasses(lead.status)}>
                                {lead.status}
                            </Badge>
                        </TableCell>
                        <TableCell className="text-slate-400">
                            {lead.brand}
                        </TableCell>
                        <TableCell className="text-slate-400">
                            {lead.source}
                        </TableCell>
                        <TableCell className="text-slate-400">
                            {formatDate(lead.created_at)}
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
