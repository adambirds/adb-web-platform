"use client";

import {
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
import { fetchAPI } from "@/lib/api/fetch";
import { useCallback, useEffect, useState } from "react";

export interface RegisterColumn {
    key: string;
    label: string;
    render?: (value: unknown, row: Record<string, unknown>) => React.ReactNode;
}

interface InfrastructureRegisterProps {
    endpoint: string;
    columns: RegisterColumn[];
    emptyTitle: string;
    emptyDescription: string;
    loadingLabel: string;
}

export function InfrastructureRegister({
    endpoint,
    columns,
    emptyTitle,
    emptyDescription,
    loadingLabel,
}: InfrastructureRegisterProps) {
    const [rows, setRows] = useState<Record<string, unknown>[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadRows = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const data = (await fetchAPI(endpoint)) as Record<string, unknown>[];
            setRows(data);
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "An unexpected error occurred while loading this register.",
            );
        } finally {
            setIsLoading(false);
        }
    }, [endpoint]);

    useEffect(() => {
        void loadRows();
    }, [loadRows]);

    if (isLoading) return <DataLoading label={loadingLabel} />;
    if (error) return <DataError message={error} onRetry={() => void loadRows()} />;
    if (rows.length === 0) {
        return <EmptyState title={emptyTitle} description={emptyDescription} />;
    }

    return (
        <Table>
            <TableHead>
                <tr>
                    {columns.map((column) => (
                        <TableHeaderCell key={column.key}>{column.label}</TableHeaderCell>
                    ))}
                </tr>
            </TableHead>
            <TableBody>
                {rows.map((row) => (
                    <TableRow key={String(row.id)}>
                        {columns.map((column) => {
                            const value = row[column.key];
                            return (
                                <TableCell key={column.key} className="text-slate-400">
                                    {column.render
                                        ? column.render(value, row)
                                        : value == null || value === ""
                                          ? "—"
                                          : String(value)}
                                </TableCell>
                            );
                        })}
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
