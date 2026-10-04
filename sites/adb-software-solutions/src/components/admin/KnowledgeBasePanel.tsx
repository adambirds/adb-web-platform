"use client";

import { ButtonLink, Card, DataError, DataLoading } from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

interface KnowledgeDocumentSummary {
    id: number;
    title: string;
    summary: string;
    section_path: string;
    client_name: string | null;
    updated_at: string;
}

interface KnowledgeWorkspaceResponse {
    ownership_type: "internal" | "client";
    client_id: number | null;
    documents: KnowledgeDocumentSummary[];
    total_documents: number;
}

export function KnowledgeBasePanel({
    clientId,
    resourceId,
    title = "Knowledge Base",
    description = "Relevant operational documentation for this context.",
}: {
    clientId?: number;
    resourceId?: number;
    title?: string;
    description?: string;
}) {
    const { hasPermission } = useAuth();
    const canView = hasPermission("knowledge_base.view_knowledgebasedocument");
    const canAdd = hasPermission("knowledge_base.add_knowledgebasedocument");
    const contextKey = `${clientId ?? ""}:${resourceId ?? ""}`;
    const [loaded, setLoaded] = useState<{
        key: string;
        value: KnowledgeWorkspaceResponse;
    } | null>(null);
    const data = loaded?.key === contextKey ? loaded.value : null;
    const requestRef = useRef(0);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const contextQuery = data
        ? new URLSearchParams({
              ownership_type: data.ownership_type,
              ...(data.client_id !== null
                  ? { client_id: String(data.client_id) }
                  : {}),
          }).toString()
        : clientId
          ? new URLSearchParams({
                ownership_type: "client",
                client_id: String(clientId),
            }).toString()
          : "";

    const load = useCallback(async () => {
        const requestId = ++requestRef.current;
        if (!canView) {
            setIsLoading(false);
            return;
        }
        try {
            setLoaded(null);
            setIsLoading(true);
            setError(null);
            const params = new URLSearchParams({
                view: "current",
                page_size: "5",
            });
            if (clientId) params.set("client_id", String(clientId));
            if (resourceId) params.set("resource_id", String(resourceId));
            const response = (await fetchAPI(
                `${API_URL}/api/admin/knowledge-base/workspace?${params.toString()}`,
            )) as KnowledgeWorkspaceResponse;
            if (requestId === requestRef.current)
                setLoaded({ key: contextKey, value: response });
        } catch (loadError) {
            if (requestId !== requestRef.current) return;
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load contextual Knowledge Base documents.",
            );
        } finally {
            if (requestId === requestRef.current) setIsLoading(false);
        }
    }, [canView, clientId, contextKey, resourceId]);

    useEffect(() => {
        void load();
        return () => {
            requestRef.current += 1;
        };
    }, [load]);

    if (!canView) return null;

    return (
        <Card className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                    <h2 className="font-semibold text-slate-100">{title}</h2>
                    <p className="mt-1 text-sm text-slate-500">{description}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                    {contextQuery && canAdd ? (
                        <ButtonLink
                            size="sm"
                            href={`/admin/knowledge-base/documents/new?${contextQuery}`}
                        >
                            Add document
                        </ButtonLink>
                    ) : null}
                    <ButtonLink
                        size="sm"
                        variant="secondary"
                        href={`/admin/knowledge-base${contextQuery ? `?${contextQuery}${resourceId ? `&resource_id=${resourceId}` : ""}` : ""}`}
                    >
                        Open Knowledge Base
                    </ButtonLink>
                </div>
            </div>

            <div className="mt-4">
                {isLoading ? (
                    <DataLoading label="Loading documentation…" />
                ) : null}
                {error ? (
                    <DataError message={error} onRetry={() => void load()} />
                ) : null}
                {!isLoading && !error && data?.documents.length === 0 ? (
                    <p className="rounded-lg border border-dashed border-slate-800 p-5 text-sm text-slate-500">
                        No current documentation is linked to this context yet.
                    </p>
                ) : null}
                {!isLoading && !error && data?.documents.length ? (
                    <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
                        {data.documents.map((document) => (
                            <Link
                                key={document.id}
                                href={`/admin/knowledge-base/documents/${document.id}`}
                                className="rounded-lg border border-slate-800 p-3 transition hover:border-slate-700 hover:bg-slate-900"
                            >
                                <p className="text-sm font-medium text-slate-200">
                                    {document.title}
                                </p>
                                <p className="text-adb-cyan-300 mt-1 text-xs">
                                    {document.section_path}
                                </p>
                                {document.summary ? (
                                    <p className="mt-2 line-clamp-2 text-xs leading-5 text-slate-500">
                                        {document.summary}
                                    </p>
                                ) : null}
                            </Link>
                        ))}
                    </div>
                ) : null}
                {data && data.total_documents > data.documents.length ? (
                    <p className="mt-3 text-xs text-slate-600">
                        Showing {data.documents.length} of{" "}
                        {data.total_documents} matching documents.
                    </p>
                ) : null}
            </div>
        </Card>
    );
}
