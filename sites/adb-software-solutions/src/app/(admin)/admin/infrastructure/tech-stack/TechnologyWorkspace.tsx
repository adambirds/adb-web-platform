"use client";

import {
    ButtonLink,
    Card,
    DataError,
    DataLoading,
    EmptyState,
    Input,
    PageHeader,
    Pagination,
} from "@/components/ui";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import { useCallback, useEffect, useState } from "react";

interface TechnologyPage {
    items: {
        id: string;
        resource_id: number;
        resource_name: string;
        technology: string;
        category: string;
        version: string;
    }[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
}

export function TechnologyWorkspace() {
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");
    const [data, setData] = useState<TechnologyPage | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const load = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const params = new URLSearchParams({
                page: String(page),
                page_size: "25",
                search,
            });
            setData(
                (await fetchAPI(
                    `${API_URL}/api/admin/infrastructure/technology?${params}`,
                )) as TechnologyPage,
            );
        } catch (failure) {
            setError(
                failure instanceof Error
                    ? failure.message
                    : "Unable to load technologies.",
            );
        } finally {
            setLoading(false);
        }
    }, [page, search]);
    useEffect(() => {
        void load();
    }, [load]);
    return (
        <div className="space-y-5">
            <PageHeader
                title="Technology Stack"
                description="Technologies and versions recorded on current infrastructure resources."
            />
            <Input
                aria-label="Search technology resources"
                placeholder="Search resource or Client..."
                value={search}
                onChange={(event) => {
                    setSearch(event.target.value);
                    setPage(1);
                }}
            />
            {error ? (
                <DataError message={error} onRetry={() => void load()} />
            ) : null}
            {loading && !data ? (
                <DataLoading label="Loading technologies..." />
            ) : null}
            {!loading && data?.items.length === 0 ? (
                <EmptyState
                    title="No technologies recorded"
                    description="Record CMS, framework, language, database, runtime or operating-system details in the resource workspace."
                />
            ) : null}
            {data?.items.length ? (
                <Card className="overflow-x-auto">
                    <table className="min-w-full text-left text-sm">
                        <thead>
                            <tr>
                                {[
                                    "Resource",
                                    "Technology",
                                    "Category",
                                    "Version",
                                ].map((name) => (
                                    <th
                                        key={name}
                                        className="px-4 py-3 text-slate-400"
                                    >
                                        {name}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {data.items.map((row) => (
                                <tr
                                    key={row.id}
                                    className="border-t border-slate-800"
                                >
                                    <td className="px-4 py-3">
                                        <ButtonLink
                                            href={`/admin/infrastructure/resources/${row.resource_id}`}
                                            variant="ghost"
                                        >
                                            {row.resource_name}
                                        </ButtonLink>
                                    </td>
                                    <td className="px-4 py-3">
                                        {row.technology}
                                    </td>
                                    <td className="px-4 py-3">
                                        {row.category}
                                    </td>
                                    <td className="px-4 py-3">
                                        {row.version || "Unknown"}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </Card>
            ) : null}
            {data ? (
                <>
                    <p className="text-sm text-slate-500">
                        {data.total} resources with recorded technologies
                    </p>
                    <Pagination
                        page={data.page}
                        pageSize={data.page_size}
                        totalItems={data.total}
                        onPageChange={setPage}
                        disabled={loading}
                    />
                </>
            ) : null}
        </div>
    );
}
