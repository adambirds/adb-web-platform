"use client";

import {
    ArrowUpIcon,
    Bars3Icon,
    ChevronRightIcon,
    FolderIcon,
    Squares2X2Icon,
} from "@heroicons/react/24/outline";
import {
    Button,
    ButtonLink,
    Card,
    DataError,
    DataLoading,
    Input,
    Pagination,
    Select,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import Link from "next/link";
import {
    type FormEvent,
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState,
} from "react";
import { KnowledgeBaseContexts } from "./KnowledgeBaseContexts";
import { knowledgeContextParams, type KnowledgeContext } from "./context";
import type { KnowledgeSection, KnowledgeWorkspaceResponse } from "./types";

import {
    KnowledgeFileBrowser,
    type KnowledgeFileLayout,
} from "./KnowledgeFileBrowser";

const BASE = `${API_URL}/api/admin/knowledge-base`;
type Layout = KnowledgeFileLayout;

function breadcrumbs(
    sections: KnowledgeSection[],
    sectionId: number | null,
): KnowledgeSection[] {
    const byId = new Map(sections.map((section) => [section.id, section]));
    const trail: KnowledgeSection[] = [];
    const visited = new Set<number>();
    let current = sectionId === null ? undefined : byId.get(sectionId);
    while (current && !visited.has(current.id)) {
        visited.add(current.id);
        trail.unshift(current);
        current =
            current.parent_id === null
                ? undefined
                : byId.get(current.parent_id);
    }
    return trail;
}

function subtree(
    sections: KnowledgeSection[],
    sectionId: number | null,
): Set<number> {
    const ids = new Set<number>();
    if (sectionId === null)
        return new Set(sections.map((section) => section.id));
    ids.add(sectionId);
    let changed = true;
    while (changed) {
        changed = false;
        for (const section of sections) {
            if (
                section.parent_id !== null &&
                ids.has(section.parent_id) &&
                !ids.has(section.id)
            ) {
                ids.add(section.id);
                changed = true;
            }
        }
    }
    return ids;
}

export function KnowledgeBaseWorkspace({
    context = null,
    resourceId,
    sectionId = null,
}: {
    context?: KnowledgeContext | null;
    resourceId?: number;
    sectionId?: number | null;
}) {
    const [layout, setLayout] = useState<Layout>("list");
    if (!context) return <KnowledgeBaseContexts />;
    return (
        <ScopedKnowledgeBaseWorkspace
            key={`${context.ownership_type}:${context.client_id}:${sectionId}:${resourceId ?? ""}`}
            context={context}
            resourceId={resourceId}
            sectionId={sectionId}
            layout={layout}
            onLayoutChange={setLayout}
        />
    );
}

function ScopedKnowledgeBaseWorkspace({
    context,
    resourceId,
    sectionId,
    layout,
    onLayoutChange,
}: {
    context: KnowledgeContext;
    resourceId?: number;
    sectionId: number | null;
    layout: Layout;
    onLayoutChange: (layout: Layout) => void;
}) {
    const { hasPermission } = useAuth();
    const canAddDocument = hasPermission(
        "knowledge_base.add_knowledgebasedocument",
    );
    const canAddSection = hasPermission(
        "knowledge_base.add_knowledgebasesection",
    );
    const [workspace, setWorkspace] =
        useState<KnowledgeWorkspaceResponse | null>(null);
    const [query, setQuery] = useState("");
    const [view, setView] = useState("current");
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showFolderForm, setShowFolderForm] = useState(false);
    const [folderName, setFolderName] = useState("");
    const [savingFolder, setSavingFolder] = useState(false);
    const requestRef = useRef(0);
    const contextQuery = knowledgeContextParams(context).toString();

    const folderHref = (id: number | null) => {
        const params = knowledgeContextParams(context);
        if (id !== null) params.set("section_id", String(id));
        if (resourceId) params.set("resource_id", String(resourceId));
        return `/admin/knowledge-base?${params}`;
    };
    const load = useCallback(async () => {
        const requestId = ++requestRef.current;
        setLoading(true);
        setError(null);
        const params = new URLSearchParams(contextQuery);
        params.set("browse", "true");
        params.set("view", view);
        params.set("page", String(page));
        params.set("page_size", "30");
        if (query.trim()) params.set("q", query.trim());
        if (sectionId !== null) params.set("section_id", String(sectionId));
        if (resourceId) params.set("resource_id", String(resourceId));
        try {
            const response = (await fetchAPI(
                `${BASE}/workspace?${params}`,
            )) as KnowledgeWorkspaceResponse;
            if (requestId === requestRef.current) setWorkspace(response);
        } catch (failure) {
            if (requestId === requestRef.current)
                setError(
                    failure instanceof Error
                        ? failure.message
                        : "Unable to load this folder.",
                );
        } finally {
            if (requestId === requestRef.current) setLoading(false);
        }
    }, [contextQuery, page, query, resourceId, sectionId, view]);
    useEffect(() => {
        const timer = window.setTimeout(() => void load(), 250);
        return () => {
            window.clearTimeout(timer);
            requestRef.current += 1;
        };
    }, [load]);

    const sections = useMemo(
        () =>
            workspace?.sections.filter(
                (section) =>
                    section.ownership_type === context.ownership_type &&
                    section.client_id === context.client_id,
            ) ?? [],
        [context, workspace],
    );
    const trail = breadcrumbs(sections, sectionId);
    const currentFolder = trail.at(-1);
    const searching = Boolean(query.trim());
    const matchingFolders = useMemo(() => {
        if (!query.trim())
            return sections.filter(
                (section) => section.parent_id === sectionId,
            );
        const ids = subtree(sections, sectionId);
        const term = query.trim().toLowerCase();
        return sections.filter(
            (section) =>
                section.id !== sectionId &&
                ids.has(section.id) &&
                (section.name.toLowerCase().includes(term) ||
                    section.description.toLowerCase().includes(term)),
        );
    }, [query, sectionId, sections]);
    const ownerName =
        context.ownership_type === "internal"
            ? "ADB Internal"
            : (workspace?.client_name ?? "Client");
    const documents = workspace?.documents ?? [];

    async function createFolder(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!canAddSection || !folderName.trim()) return;
        try {
            setSavingFolder(true);
            setError(null);
            await fetchAPI(`${BASE}/sections`, {
                method: "POST",
                body: JSON.stringify({
                    ownership_type: context.ownership_type,
                    client_id: context.client_id,
                    parent_id: sectionId,
                    name: folderName.trim(),
                    description: "",
                    order: sections.filter(
                        (section) => section.parent_id === sectionId,
                    ).length,
                }),
            });
            setFolderName("");
            setShowFolderForm(false);
            await load();
        } catch (failure) {
            setError(
                failure instanceof Error
                    ? failure.message
                    : "Unable to create folder.",
            );
        } finally {
            setSavingFolder(false);
        }
    }

    return (
        <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-lg font-semibold text-white">
                    {ownerName} Knowledge Base
                </h2>
                <ButtonLink href="/admin/knowledge-base" variant="secondary">
                    Choose another Knowledge Base
                </ButtonLink>
            </div>
            <Card className="overflow-hidden">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 p-4">
                    <nav
                        aria-label="Folder breadcrumbs"
                        className="flex min-w-0 flex-wrap items-center gap-2 text-sm"
                    >
                        <Link
                            href={folderHref(null)}
                            aria-current={
                                sectionId === null ? "page" : undefined
                            }
                            className="hover:text-adb-cyan-300 font-medium text-slate-200"
                        >
                            {ownerName}
                        </Link>
                        {trail.map((folder, index) => (
                            <span
                                key={folder.id}
                                className="flex items-center gap-2"
                            >
                                <ChevronRightIcon
                                    aria-hidden="true"
                                    className="h-4 w-4 text-slate-600"
                                />
                                {index === trail.length - 1 ? (
                                    <span
                                        aria-current="page"
                                        className="font-medium text-white"
                                    >
                                        {folder.name}
                                    </span>
                                ) : (
                                    <Link
                                        href={folderHref(folder.id)}
                                        className="hover:text-adb-cyan-300 text-slate-400"
                                    >
                                        {folder.name}
                                    </Link>
                                )}
                            </span>
                        ))}
                    </nav>
                    <div className="flex flex-wrap gap-2">
                        {currentFolder ? (
                            <ButtonLink
                                size="sm"
                                variant="secondary"
                                href={folderHref(currentFolder.parent_id)}
                            >
                                <ArrowUpIcon
                                    aria-hidden="true"
                                    className="h-4 w-4"
                                />
                                Up one level
                            </ButtonLink>
                        ) : null}
                        {canAddSection ? (
                            <Button
                                size="sm"
                                variant="secondary"
                                disabled={
                                    loading || savingFolder || Boolean(error)
                                }
                                onClick={() =>
                                    setShowFolderForm((value) => !value)
                                }
                            >
                                New folder
                            </Button>
                        ) : null}
                        {canAddDocument ? (
                            <ButtonLink
                                size="sm"
                                href={`/admin/knowledge-base/documents/new?${contextQuery}${sectionId !== null ? `&section_id=${sectionId}` : ""}`}
                            >
                                New document
                            </ButtonLink>
                        ) : null}
                    </div>
                </div>
                <div className="flex flex-wrap items-center gap-3 border-b border-slate-800 p-4">
                    <Input
                        aria-label="Search Knowledge Base"
                        placeholder={
                            currentFolder
                                ? `Search ${currentFolder.name} and its subfolders...`
                                : "Search this Knowledge Base..."
                        }
                        value={query}
                        onChange={(event) => {
                            setQuery(event.target.value);
                            setPage(1);
                        }}
                        className="min-w-48 flex-1"
                    />
                    <Select
                        aria-label="Article status"
                        value={view}
                        onChange={(event) => {
                            setView(event.target.value);
                            setPage(1);
                        }}
                        className="w-36"
                    >
                        <option value="current">Current</option>
                        <option value="archived">Archived</option>
                        <option value="all">All statuses</option>
                    </Select>
                    <div
                        className="flex gap-1"
                        role="group"
                        aria-label="View layout"
                    >
                        <Button
                            variant="secondary"
                            size="sm"
                            aria-label="List view"
                            aria-pressed={layout === "list"}
                            onClick={() => onLayoutChange("list")}
                        >
                            <Bars3Icon aria-hidden="true" className="h-4 w-4" />
                        </Button>
                        <Button
                            variant="secondary"
                            size="sm"
                            aria-label="Grid view"
                            aria-pressed={layout === "grid"}
                            onClick={() => onLayoutChange("grid")}
                        >
                            <Squares2X2Icon
                                aria-hidden="true"
                                className="h-4 w-4"
                            />
                        </Button>
                    </div>
                </div>
                {showFolderForm ? (
                    <form
                        onSubmit={(event) => void createFolder(event)}
                        className="space-y-3 border-b border-slate-800 bg-slate-950/50 p-4"
                    >
                        <p className="text-sm text-slate-400">
                            Create a folder in{" "}
                            {currentFolder?.name ?? ownerName}.
                        </p>
                        <div className="flex flex-wrap gap-2">
                            <Input
                                autoFocus
                                required
                                maxLength={100}
                                aria-label="Folder name"
                                placeholder="Folder name"
                                value={folderName}
                                disabled={savingFolder}
                                onChange={(event) =>
                                    setFolderName(event.target.value)
                                }
                                className="min-w-48 flex-1"
                            />
                            <Button
                                type="submit"
                                size="sm"
                                disabled={savingFolder}
                            >
                                {savingFolder ? "Creating…" : "Create folder"}
                            </Button>
                            <Button
                                type="button"
                                size="sm"
                                variant="secondary"
                                disabled={savingFolder}
                                onClick={() => {
                                    setShowFolderForm(false);
                                    setFolderName("");
                                }}
                            >
                                Cancel
                            </Button>
                        </div>
                    </form>
                ) : null}
                {error ? (
                    <div className="p-4">
                        <DataError
                            message={error}
                            onRetry={() => void load()}
                        />
                    </div>
                ) : null}
                {loading ? (
                    <DataLoading label="Loading folder contents..." />
                ) : null}
                {!loading && !error ? (
                    <>
                        {searching ? (
                            <p className="px-4 pt-4 text-sm text-slate-400">
                                Search results in{" "}
                                {currentFolder?.name ?? ownerName} and its
                                subfolders
                            </p>
                        ) : null}
                        <KnowledgeFileBrowser
                            folders={matchingFolders}
                            documents={documents}
                            folderHref={folderHref}
                            layout={layout}
                            searching={searching}
                        />
                        {!matchingFolders.length && !documents.length ? (
                            <div className="p-10 text-center">
                                <FolderIcon
                                    aria-hidden="true"
                                    className="mx-auto mb-3 h-10 w-10 text-slate-600"
                                />
                                <p className="text-sm font-medium text-slate-300">
                                    {searching
                                        ? "No matching folders or articles"
                                        : "This folder is empty"}
                                </p>
                                <p className="mt-2 text-xs text-slate-500">
                                    {searching
                                        ? "Try a different search."
                                        : sectionId === null
                                          ? "Create a folder to organise this Knowledge Base."
                                          : "Create a subfolder or add an article here."}
                                </p>
                            </div>
                        ) : null}
                        <div className="border-t border-slate-800 px-4 py-3 text-xs text-slate-500">
                            {matchingFolders.length} folder
                            {matchingFolders.length === 1 ? "" : "s"} ·{" "}
                            {workspace?.total_documents ?? 0} article
                            {workspace?.total_documents === 1 ? "" : "s"}
                        </div>
                        {workspace &&
                        workspace.total_documents > workspace.page_size ? (
                            <Pagination
                                page={workspace.page}
                                pageSize={workspace.page_size}
                                totalItems={workspace.total_documents}
                                onPageChange={setPage}
                                disabled={loading}
                            />
                        ) : null}
                    </>
                ) : null}
            </Card>
        </div>
    );
}
