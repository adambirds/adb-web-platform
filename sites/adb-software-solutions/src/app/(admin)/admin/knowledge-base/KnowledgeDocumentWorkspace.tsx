"use client";

import {
    Badge,
    Button,
    ButtonLink,
    Card,
    DataError,
    DataLoading,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI, fetchRawAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import Link from "next/link";
import { ChangeEvent, useCallback, useEffect, useState } from "react";
import { MarkdownContent } from "./MarkdownContent";
import type {
    KnowledgeAttachment,
    KnowledgeDocumentDetail,
    KnowledgeVersionDetail,
} from "./types";

import { knowledgeBaseHref, parseKnowledgeContext } from "./context";

const BASE = `${API_URL}/api/admin/knowledge-base`;

function formatDate(value: string): string {
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    }).format(new Date(value));
}

function formatBytes(value: number): string {
    if (value < 1024) return `${value} B`;
    if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
    return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function scanVariant(
    status: string,
): "neutral" | "info" | "success" | "warning" | "danger" {
    if (status === "safe") return "success";
    if (status === "infected" || status === "blocked") return "danger";
    if (status === "failed") return "warning";
    if (status === "scanning") return "info";
    return "neutral";
}

export function KnowledgeDocumentWorkspace({
    documentId,
}: {
    documentId: number;
}) {
    const { hasPermission } = useAuth();
    const canChange = hasPermission(
        "knowledge_base.change_knowledgebasedocument",
    );
    const canViewAttachments = hasPermission(
        "knowledge_base.view_knowledgebaseattachment",
    );
    const canAddAttachment =
        canChange &&
        hasPermission("knowledge_base.add_knowledgebaseattachment");
    const canDeleteAttachment =
        canChange &&
        hasPermission("knowledge_base.delete_knowledgebaseattachment");
    const [document, setDocument] = useState<KnowledgeDocumentDetail | null>(
        null,
    );
    const [historical, setHistorical] = useState<KnowledgeVersionDetail | null>(
        null,
    );
    const [isLoading, setIsLoading] = useState(true);
    const [isWorking, setIsWorking] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            setDocument(
                (await fetchAPI(
                    `${BASE}/documents/${documentId}`,
                )) as KnowledgeDocumentDetail,
            );
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load Knowledge Base document.",
            );
        } finally {
            setIsLoading(false);
        }
    }, [documentId]);

    useEffect(() => {
        void load();
    }, [load]);

    async function loadVersion(versionNumber: number) {
        try {
            setError(null);
            setHistorical(
                (await fetchAPI(
                    `${BASE}/documents/${documentId}/versions/${versionNumber}`,
                )) as KnowledgeVersionDetail,
            );
        } catch (versionError) {
            setError(
                versionError instanceof Error
                    ? versionError.message
                    : "Unable to load document version.",
            );
        }
    }

    async function changeArchiveState() {
        if (!document || !canChange) return;
        try {
            setIsWorking(true);
            setError(null);
            await fetchAPI(
                `${BASE}/documents/${document.id}/${document.archived ? "restore" : "archive"}`,
                { method: "POST" },
            );
            setHistorical(null);
            await load();
        } catch (actionError) {
            setError(
                actionError instanceof Error
                    ? actionError.message
                    : "Unable to update document state.",
            );
        } finally {
            setIsWorking(false);
        }
    }

    async function uploadAttachment(event: ChangeEvent<HTMLInputElement>) {
        const file = event.target.files?.[0];
        event.target.value = "";
        if (!file || !document || !canAddAttachment) return;
        try {
            setIsWorking(true);
            setError(null);
            const body = new FormData();
            body.append("file", file);
            await fetchAPI(`${BASE}/documents/${document.id}/attachments`, {
                method: "POST",
                body,
            });
            await load();
        } catch (uploadError) {
            setError(
                uploadError instanceof Error
                    ? uploadError.message
                    : "Unable to upload attachment.",
            );
        } finally {
            setIsWorking(false);
        }
    }

    async function downloadAttachment(attachment: KnowledgeAttachment) {
        try {
            setError(null);
            const response = await fetchRawAPI(
                `${BASE}/attachments/${attachment.id}/download`,
            );
            if (!response.ok) {
                const payload = (await response.json().catch(() => ({}))) as {
                    message?: string;
                };
                throw new Error(
                    payload.message ??
                        "Attachment is not available for download.",
                );
            }
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const anchor = window.document.createElement("a");
            anchor.href = url;
            anchor.download = attachment.original_name;
            anchor.click();
            URL.revokeObjectURL(url);
        } catch (downloadError) {
            setError(
                downloadError instanceof Error
                    ? downloadError.message
                    : "Unable to download attachment.",
            );
        }
    }

    async function removeAttachment(attachmentId: number) {
        if (!canDeleteAttachment) return;
        try {
            setIsWorking(true);
            setError(null);
            await fetchAPI(`${BASE}/attachments/${attachmentId}`, {
                method: "DELETE",
            });
            await load();
        } catch (deleteError) {
            setError(
                deleteError instanceof Error
                    ? deleteError.message
                    : "Unable to delete attachment.",
            );
        } finally {
            setIsWorking(false);
        }
    }

    if (isLoading && !document) return <DataLoading />;
    if (!document)
        return (
            <DataError
                message={error ?? "Knowledge Base document not found."}
            />
        );

    const displayTitle = historical?.title ?? document.title;
    const displayContent = historical?.content ?? document.content;
    const displaySection = historical?.section_path ?? document.section_path;

    return (
        <div className="space-y-5">
            <ButtonLink
                variant="secondary"
                href={`${knowledgeBaseHref(
                    parseKnowledgeContext(
                        document.ownership_type,
                        document.client_id === null
                            ? undefined
                            : String(document.client_id),
                    ) ?? { ownership_type: "internal", client_id: null },
                )}&section_id=${document.section_id}`}
            >
                Back to folder
            </ButtonLink>
            {error ? <DataError message={error} /> : null}
            <Card className="p-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                            <Badge
                                variant={
                                    document.archived ? "warning" : "success"
                                }
                            >
                                {document.archived ? "Archived" : "Current"}
                            </Badge>
                            <Badge>
                                {document.ownership_type === "internal"
                                    ? "ADB Internal"
                                    : (document.client_name ?? "Client")}
                            </Badge>
                            {historical ? (
                                <Badge variant="info">
                                    Historical v{historical.version_number}
                                </Badge>
                            ) : null}
                        </div>
                        <h1 className="mt-3 text-2xl font-semibold text-slate-100">
                            {displayTitle}
                        </h1>
                        <p className="text-adb-cyan-300 mt-2 text-sm">
                            {displaySection}
                        </p>
                        {!historical && document.summary ? (
                            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
                                {document.summary}
                            </p>
                        ) : null}
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                        {historical ? (
                            <Button
                                type="button"
                                variant="secondary"
                                onClick={() => setHistorical(null)}
                            >
                                Current version
                            </Button>
                        ) : null}
                        {!historical && canChange && !document.archived ? (
                            <ButtonLink
                                href={`/admin/knowledge-base/documents/${document.id}/edit`}
                            >
                                Edit
                            </ButtonLink>
                        ) : null}
                        {!historical && canChange ? (
                            <Button
                                type="button"
                                variant={
                                    document.archived
                                        ? "secondary"
                                        : "destructive"
                                }
                                disabled={isWorking}
                                onClick={() => void changeArchiveState()}
                            >
                                {document.archived ? "Restore" : "Archive"}
                            </Button>
                        ) : null}
                    </div>
                </div>
            </Card>

            <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
                <Card className="min-w-0 p-6">
                    <MarkdownContent content={displayContent} />
                </Card>

                <div className="space-y-5">
                    <Card className="p-4">
                        <h2 className="text-sm font-semibold text-slate-100">
                            Revision history
                        </h2>
                        <div className="mt-3 max-h-80 space-y-2 overflow-y-auto pr-1">
                            {document.versions.map((version) => (
                                <button
                                    key={version.version_number}
                                    type="button"
                                    onClick={() =>
                                        void loadVersion(version.version_number)
                                    }
                                    className="w-full rounded-lg border border-slate-800 p-3 text-left transition hover:border-slate-700 hover:bg-slate-900"
                                >
                                    <div className="flex items-center justify-between gap-3">
                                        <span className="text-sm font-medium text-slate-200">
                                            Version {version.version_number}
                                        </span>
                                        <span className="text-[11px] text-slate-600">
                                            {formatDate(version.created_at)}
                                        </span>
                                    </div>
                                    {version.change_summary ? (
                                        <p className="mt-1 text-xs text-slate-400">
                                            {version.change_summary}
                                        </p>
                                    ) : null}
                                    {version.editor_name ? (
                                        <p className="mt-1 text-[11px] text-slate-600">
                                            {version.editor_name}
                                        </p>
                                    ) : null}
                                </button>
                            ))}
                        </div>
                    </Card>

                    {document.resources.length ? (
                        <Card className="p-4">
                            <h2 className="text-sm font-semibold text-slate-100">
                                Infrastructure
                            </h2>
                            <div className="mt-3 space-y-2">
                                {document.resources.map((resource) => (
                                    <Link
                                        key={resource.id}
                                        href={`/admin/infrastructure/resources/${resource.resource_id}`}
                                        className="hover:text-adb-cyan-200 block rounded-lg border border-slate-800 p-3 text-sm text-slate-300 hover:border-slate-700"
                                    >
                                        {resource.resource_name}
                                        <span className="mt-1 block text-xs text-slate-600">
                                            {resource.resource_type.replaceAll(
                                                "_",
                                                " ",
                                            )}
                                        </span>
                                    </Link>
                                ))}
                            </div>
                        </Card>
                    ) : null}

                    {document.credentials.length ? (
                        <Card className="p-4">
                            <h2 className="text-sm font-semibold text-slate-100">
                                Credential Vault
                            </h2>
                            <p className="mt-1 text-xs text-slate-500">
                                Metadata links only; secrets are never embedded
                                here.
                            </p>
                            <div className="mt-3 space-y-2">
                                {document.credentials.map((credential) => (
                                    <div
                                        key={credential.id}
                                        className="rounded-lg border border-slate-800 p-3"
                                    >
                                        <p className="text-sm text-slate-300">
                                            {credential.credential_name}
                                        </p>
                                        <p className="mt-1 text-xs text-slate-600">
                                            {credential.credential_type ??
                                                "Credential"}{" "}
                                            · {credential.status}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </Card>
                    ) : null}

                    {canViewAttachments ? (
                        <Card className="p-4">
                            <div className="flex items-center justify-between gap-3">
                                <div>
                                    <h2 className="text-sm font-semibold text-slate-100">
                                        Attachments
                                    </h2>
                                    <p className="mt-1 text-xs text-slate-500">
                                        Private, quarantined files
                                    </p>
                                </div>
                                {canAddAttachment && !document.archived ? (
                                    <label className="inline-flex h-8 cursor-pointer items-center rounded-lg border border-slate-700 bg-slate-800 px-3 text-xs font-medium text-slate-100 hover:bg-slate-700">
                                        Upload
                                        <input
                                            type="file"
                                            className="sr-only"
                                            disabled={isWorking}
                                            onChange={(event) =>
                                                void uploadAttachment(event)
                                            }
                                        />
                                    </label>
                                ) : null}
                            </div>
                            <div className="mt-3 space-y-2">
                                {document.attachments.length === 0 ? (
                                    <p className="text-xs text-slate-600">
                                        No attachments.
                                    </p>
                                ) : null}
                                {document.attachments.map((attachment) => (
                                    <div
                                        key={attachment.id}
                                        className="rounded-lg border border-slate-800 p-3"
                                    >
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="min-w-0">
                                                <p className="truncate text-sm text-slate-300">
                                                    {attachment.original_name}
                                                </p>
                                                <p className="mt-1 text-xs text-slate-600">
                                                    {formatBytes(
                                                        attachment.size_bytes,
                                                    )}{" "}
                                                    ·{" "}
                                                    {
                                                        attachment.detected_content_type
                                                    }
                                                </p>
                                            </div>
                                            <Badge
                                                variant={scanVariant(
                                                    attachment.scan_status,
                                                )}
                                            >
                                                {attachment.scan_status}
                                            </Badge>
                                        </div>
                                        <div className="mt-3 flex gap-2">
                                            <Button
                                                type="button"
                                                size="sm"
                                                variant="secondary"
                                                disabled={
                                                    attachment.scan_status ===
                                                        "infected" ||
                                                    attachment.scan_status ===
                                                        "blocked" ||
                                                    attachment.scan_status ===
                                                        "scanning"
                                                }
                                                onClick={() =>
                                                    void downloadAttachment(
                                                        attachment,
                                                    )
                                                }
                                            >
                                                Download
                                            </Button>
                                            {canDeleteAttachment ? (
                                                <Button
                                                    type="button"
                                                    size="sm"
                                                    variant="destructive"
                                                    disabled={isWorking}
                                                    onClick={() =>
                                                        void removeAttachment(
                                                            attachment.id,
                                                        )
                                                    }
                                                >
                                                    Delete
                                                </Button>
                                            ) : null}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </Card>
                    ) : null}

                    <Card className="p-4 text-xs text-slate-500">
                        <p>Created {formatDate(document.created_at)}</p>
                        <p className="mt-1">
                            Updated {formatDate(document.updated_at)}
                        </p>
                        {document.updated_by_name ? (
                            <p className="mt-1">
                                Last editor: {document.updated_by_name}
                            </p>
                        ) : null}
                    </Card>
                </div>
            </div>
        </div>
    );
}
