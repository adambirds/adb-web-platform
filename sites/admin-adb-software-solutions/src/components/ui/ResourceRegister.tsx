"use client";

import { fetchAPI } from "@/lib/api/fetch";
import { ReactNode, useCallback, useEffect, useState } from "react";
import { DataError, DataLoading } from "./DataState";
import { EmptyState } from "./EmptyState";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeaderCell,
    TableRow,
} from "./Table";

export interface ResourceRegisterColumn {
    key: string;
    label: string;
    render?: (value: unknown, row: Record<string, unknown>) => ReactNode;
}

interface ResourceRegisterProps {
    endpoint: string;
    columns: ResourceRegisterColumn[];
    loadingLabel: string;
    emptyTitle: string;
    emptyDescription: string;
    rowKey?: string;
}

export function ResourceRegister({
    endpoint,
    columns,
    loadingLabel,
    emptyTitle,
    emptyDescription,
    rowKey = "id",
}: ResourceRegisterProps) {
    const [rows, setRows] = useState<Record<string, unknown>[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadRows = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            setRows((await fetchAPI(endpoint)) as Record<string, unknown>[]);
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
                    <TableRow key={String(row[rowKey])}>
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
