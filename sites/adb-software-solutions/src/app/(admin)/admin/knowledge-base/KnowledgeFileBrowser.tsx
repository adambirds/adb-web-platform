"use client";

import { DocumentTextIcon, FolderIcon } from "@heroicons/react/24/outline";
import { Badge } from "@/components/ui";
import Link from "next/link";
import type { KnowledgeDocumentSummary, KnowledgeSection } from "./types";

export type KnowledgeFileLayout = "list" | "grid";
interface FileItem {
    key: string;
    kind: "folder" | "article";
    href: string;
    name: string;
    location: string;
    summary?: string;
    updatedAt?: string;
    archived?: boolean;
    version?: number;
}
function formatDate(value: string): string {
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    }).format(new Date(value));
}
function ItemLink({
    item,
    layout,
    searching,
}: {
    item: FileItem;
    layout: KnowledgeFileLayout;
    searching: boolean;
}) {
    const Icon = item.kind === "folder" ? FolderIcon : DocumentTextIcon;
    const detail = searching
        ? item.location
        : layout === "grid"
          ? item.updatedAt
              ? `Article · ${formatDate(item.updatedAt)}`
              : "Folder"
          : item.summary;
    return (
        <Link
            href={item.href}
            className={
                layout === "grid"
                    ? "block rounded-xl border border-slate-800 bg-slate-950/40 p-5 transition hover:border-slate-600 hover:bg-slate-800/40"
                    : "flex items-start gap-3 text-slate-100"
            }
        >
            <Icon
                aria-hidden="true"
                className={`${layout === "grid" ? "mb-4 h-10 w-10" : "h-6 w-6 shrink-0"} ${item.kind === "folder" ? "text-amber-300" : "text-adb-cyan-300"}`}
            />
            <span className="min-w-0">
                <span className="font-medium text-slate-100">{item.name}</span>
                {item.archived ? (
                    <span className="ml-2">
                        <Badge variant="warning">Archived</Badge>
                    </span>
                ) : null}
                {detail ? (
                    <span className="mt-1 line-clamp-1 block text-xs font-normal text-slate-500">
                        {detail}
                    </span>
                ) : null}
            </span>
        </Link>
    );
}
export function KnowledgeFileBrowser({
    folders,
    documents,
    folderHref,
    layout,
    searching,
}: {
    folders: KnowledgeSection[];
    documents: KnowledgeDocumentSummary[];
    folderHref: (id: number) => string;
    layout: KnowledgeFileLayout;
    searching: boolean;
}) {
    const items: FileItem[] = [
        ...folders.map((folder) => ({
            key: `folder-${folder.id}`,
            kind: "folder" as const,
            href: folderHref(folder.id),
            name: folder.name,
            location: folder.path,
        })),
        ...documents.map((document) => ({
            key: `document-${document.id}`,
            kind: "article" as const,
            href: `/admin/knowledge-base/documents/${document.id}`,
            name: document.title,
            location: document.section_path,
            summary: document.summary,
            updatedAt: document.updated_at,
            archived: document.archived,
            version: document.version_count,
        })),
    ];
    if (layout === "grid")
        return (
            <div className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {items.map((item) => (
                    <ItemLink
                        key={item.key}
                        item={item}
                        layout={layout}
                        searching={searching}
                    />
                ))}
            </div>
        );
    return (
        <div className="overflow-x-auto">
            <table
                className="w-full text-left text-sm"
                aria-label="Folder contents"
            >
                <thead>
                    <tr className="border-b border-slate-800 text-xs text-slate-500">
                        <th className="px-5 py-3 font-medium">Name</th>
                        <th className="px-4 py-3 font-medium">Type</th>
                        <th className="px-4 py-3 font-medium">Updated</th>
                    </tr>
                </thead>
                <tbody>
                    {items.map((item) => (
                        <tr
                            key={item.key}
                            className="border-b border-slate-800/60 hover:bg-slate-800/40"
                        >
                            <td className="px-5 py-4">
                                <ItemLink
                                    item={item}
                                    layout={layout}
                                    searching={searching}
                                />
                            </td>
                            <td className="px-4 py-4 text-slate-500">
                                {item.kind === "folder"
                                    ? "Folder"
                                    : `Article · v${item.version}`}
                            </td>
                            <td className="px-4 py-4 whitespace-nowrap text-slate-500">
                                {item.updatedAt
                                    ? formatDate(item.updatedAt)
                                    : "—"}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
