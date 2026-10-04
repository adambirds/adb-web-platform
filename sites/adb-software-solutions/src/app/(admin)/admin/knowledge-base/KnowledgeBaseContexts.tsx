"use client";

import {
    ButtonLink,
    Card,
    DataError,
    DataLoading,
    EmptyState,
    Input,
    Pagination,
} from "@/components/ui";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import Link from "next/link";
import { useEffect, useState } from "react";
import type { KnowledgeOption } from "./types";
import { knowledgeBaseHref } from "./context";

interface ContextPage {
    items: KnowledgeOption[];
    page: number;
    page_size: number;
    total: number;
}

export function KnowledgeBaseContexts() {
    const [search, setSearch] = useState("");
    const [page, setPage] = useState(1);
    const [data, setData] = useState<ContextPage | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [retry, setRetry] = useState(0);
    useEffect(() => {
        let active = true;
        setLoading(true);
        setError(null);
        setData(null);
        void fetchAPI(
            `${API_URL}/api/admin/knowledge-base/contexts?${new URLSearchParams({ q: search, page: String(page), page_size: "25" })}`,
        )
            .then((response: ContextPage) => {
                if (active) setData(response);
            })
            .catch((failure: unknown) => {
                if (active)
                    setError(
                        failure instanceof Error
                            ? failure.message
                            : "Unable to load Knowledge Bases.",
                    );
            })
            .finally(() => {
                if (active) setLoading(false);
            });
        return () => {
            active = false;
        };
    }, [page, search, retry]);
    return (
        <div className="space-y-5">
            <p className="text-sm text-slate-400">
                Choose Internal or a Client to open its folders and articles.
                Each has its own folder structure.
            </p>
            <Card className="flex flex-wrap items-center justify-between gap-4 p-5">
                <div>
                    <h2 className="font-semibold text-white">ADB Internal</h2>
                    <p className="mt-1 text-sm text-slate-400">
                        Internal runbooks and operational documentation.
                    </p>
                </div>
                <ButtonLink
                    href={knowledgeBaseHref({
                        ownership_type: "internal",
                        client_id: null,
                    })}
                >
                    Open Internal Knowledge Base
                </ButtonLink>
            </Card>
            <Input
                aria-label="Search Client Knowledge Bases"
                placeholder="Search Clients..."
                value={search}
                onChange={(event) => {
                    setSearch(event.target.value);
                    setPage(1);
                }}
            />
            {error ? (
                <DataError
                    message={error}
                    onRetry={() => setRetry((value) => value + 1)}
                />
            ) : null}
            {loading ? (
                <DataLoading label="Loading Client Knowledge Bases..." />
            ) : null}
            {data?.items.length ? (
                <>
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                        {data.items.map((client) => (
                            <Link
                                key={client.id}
                                href={knowledgeBaseHref({
                                    ownership_type: "client",
                                    client_id: client.id,
                                })}
                                className="rounded-xl border border-slate-800 bg-slate-900/70 p-5 transition hover:border-slate-600"
                            >
                                <h2 className="font-semibold text-white">
                                    {client.label}
                                </h2>
                                <p className="mt-2 text-sm text-slate-400">
                                    Open folders and articles
                                </p>
                            </Link>
                        ))}
                    </div>
                    <Pagination
                        page={data.page}
                        pageSize={data.page_size}
                        totalItems={data.total}
                        onPageChange={setPage}
                        disabled={loading}
                    />
                </>
            ) : data && !loading ? (
                <EmptyState
                    title="No Client Knowledge Bases found"
                    description="Only Clients in your access scope appear here."
                />
            ) : null}
        </div>
    );
}
