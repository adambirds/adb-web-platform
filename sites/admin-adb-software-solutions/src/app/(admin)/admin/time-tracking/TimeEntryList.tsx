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

interface TimeEntrySummary {
    id: number;
    date: string;
    duration_hours: string;
    description: string;
    billable: boolean;
    ownership_type: string;
    client_name: string | null;
    project_name: string | null;
    user_name: string | null;
}

function formatDate(value: string) {
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    }).format(new Date(`${value}T00:00:00`));
}

export function TimeEntryList() {
    const [entries, setEntries] = useState<TimeEntrySummary[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadEntries = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const data = (await fetchAPI(
                AdminAPI.timeEntries.list(),
            )) as TimeEntrySummary[];
            setEntries(data);
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "An unexpected error occurred while loading time entries.",
            );
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        void loadEntries();
    }, [loadEntries]);

    if (isLoading) {
        return <DataLoading label="Loading time entries..." />;
    }

    if (error) {
        return <DataError message={error} onRetry={() => void loadEntries()} />;
    }

    if (entries.length === 0) {
        return (
            <EmptyState
                title="No time entries in your scope"
                description="Tracked project, client and internal time will appear here once entries have been recorded."
            />
        );
    }

    return (
        <Table>
            <TableHead>
                <tr>
                    <TableHeaderCell>Date</TableHeaderCell>
                    <TableHeaderCell>Description</TableHeaderCell>
                    <TableHeaderCell>Context</TableHeaderCell>
                    <TableHeaderCell>Staff</TableHeaderCell>
                    <TableHeaderCell>Billing</TableHeaderCell>
                    <TableHeaderCell className="text-right">
                        Hours
                    </TableHeaderCell>
                </tr>
            </TableHead>
            <TableBody>
                {entries.map((entry) => (
                    <TableRow key={entry.id}>
                        <TableCell className="whitespace-nowrap text-slate-400">
                            {formatDate(entry.date)}
                        </TableCell>
                        <TableCell>
                            <div className="max-w-xl font-medium text-slate-200">
                                {entry.description}
                            </div>
                        </TableCell>
                        <TableCell>
                            <div className="text-slate-300">
                                {entry.project_name ||
                                    entry.client_name ||
                                    "ADB Internal"}
                            </div>
                            <div className="mt-1 text-xs text-slate-500">
                                {entry.ownership_type === "internal"
                                    ? "Internal"
                                    : entry.project_name
                                      ? "Project"
                                      : "Client"}
                            </div>
                        </TableCell>
                        <TableCell className="text-slate-400">
                            {entry.user_name || "Unassigned"}
                        </TableCell>
                        <TableCell>
                            <Badge
                                className={
                                    entry.billable
                                        ? "border-emerald-900/70 bg-emerald-950/50 text-emerald-300"
                                        : "border-slate-700 bg-slate-900 text-slate-500"
                                }
                            >
                                {entry.billable ? "Billable" : "Non-billable"}
                            </Badge>
                        </TableCell>
                        <TableCell className="text-right font-semibold tabular-nums text-slate-200">
                            {Number(entry.duration_hours).toFixed(2)}
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
