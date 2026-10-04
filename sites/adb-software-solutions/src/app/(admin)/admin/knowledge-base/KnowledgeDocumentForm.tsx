"use client";

import {
    Button,
    ButtonLink,
    Card,
    DataError,
    DataLoading,
    Input,
    Select,
    Textarea,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import { useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { MarkdownContent } from "./MarkdownContent";
import type {
    KnowledgeDocumentDetail,
    KnowledgeOption,
    KnowledgeOptionsResponse,
} from "./types";

import {
    knowledgeBaseHref,
    knowledgeContextParams,
    parseKnowledgeContext,
    type KnowledgeContext,
} from "./context";

const BASE = `${API_URL}/api/admin/knowledge-base`;

interface FormState {
    ownership_type: string;
    client_id: string;
    title: string;
    summary: string;
    section_id: string;
    content: string;
    tags: string;
    change_summary: string;
    resource_ids: number[];
    credential_ids: number[];
}

const EMPTY_FORM: FormState = {
    ownership_type: "internal",
    client_id: "",
    title: "",
    summary: "",
    section_id: "",
    content: "# ",
    tags: "",
    change_summary: "",
    resource_ids: [],
    credential_ids: [],
};

const labelClass = "space-y-1.5 text-sm font-medium text-slate-300";

function toggleId(values: number[], id: number): number[] {
    return values.includes(id)
        ? values.filter((value) => value !== id)
        : [...values, id];
}

function OptionChecklist({
    title,
    description,
    options,
    selected,
    onToggle,
}: {
    title: string;
    description: string;
    options: KnowledgeOption[];
    selected: number[];
    onToggle: (id: number) => void;
}) {
    if (!options.length) return null;
    return (
        <Card className="p-4">
            <h3 className="text-sm font-semibold text-slate-100">{title}</h3>
            <p className="mt-1 text-xs text-slate-500">{description}</p>
            <div className="mt-3 max-h-48 space-y-1 overflow-y-auto pr-1">
                {options.map((option) => (
                    <label
                        key={option.id}
                        className="flex cursor-pointer items-start gap-3 rounded-lg px-2 py-2 text-sm text-slate-300 hover:bg-slate-900"
                    >
                        <input
                            type="checkbox"
                            checked={selected.includes(option.id)}
                            onChange={() => onToggle(option.id)}
                            className="text-adb-cyan-500 focus:ring-adb-cyan-500 mt-0.5 rounded border-slate-600 bg-slate-900"
                        />
                        <span>
                            <span className="block">{option.label}</span>
                            {option.kind ? (
                                <span className="mt-0.5 block text-xs text-slate-500">
                                    {option.kind.replaceAll("_", " ")}
                                </span>
                            ) : null}
                        </span>
                    </label>
                ))}
            </div>
        </Card>
    );
}

export function KnowledgeDocumentForm({
    documentId,
    initialContext,
    initialSectionId,
}: {
    documentId?: number;
    initialContext?: KnowledgeContext;
    initialSectionId?: number;
}) {
    const router = useRouter();
    const { hasPermission } = useAuth();
    const canSave = hasPermission(
        documentId
            ? "knowledge_base.change_knowledgebasedocument"
            : "knowledge_base.add_knowledgebasedocument",
    );
    const [form, setForm] = useState<FormState>({
        ...EMPTY_FORM,
        ownership_type: initialContext?.ownership_type ?? "",
        client_id: initialContext?.client_id
            ? String(initialContext.client_id)
            : "",
        section_id: initialSectionId ? String(initialSectionId) : "",
    });
    const [options, setOptions] = useState<KnowledgeOptionsResponse | null>(
        null,
    );
    const [original, setOriginal] = useState<KnowledgeDocumentDetail | null>(
        null,
    );
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        if (!canSave || (!documentId && !initialContext)) {
            setIsLoading(false);
            return;
        }
        try {
            setIsLoading(true);
            setError(null);
            let context = initialContext;
            if (documentId) {
                const document = (await fetchAPI(
                    `${BASE}/documents/${documentId}`,
                )) as KnowledgeDocumentDetail;
                context =
                    parseKnowledgeContext(
                        document.ownership_type,
                        document.client_id === null
                            ? undefined
                            : String(document.client_id),
                    ) ?? undefined;
                setOriginal(document);
                setForm({
                    ownership_type: document.ownership_type,
                    client_id: document.client_id
                        ? String(document.client_id)
                        : "",
                    title: document.title,
                    summary: document.summary,
                    section_id: String(document.section_id),
                    content: document.content,
                    tags: document.tags.join(", "),
                    change_summary: "",
                    resource_ids: document.resources.map(
                        (resource) => resource.resource_id,
                    ),
                    credential_ids: document.credentials.map(
                        (credential) => credential.credential_id,
                    ),
                });
            }
            if (!context)
                throw new Error(
                    "Choose a Client or Internal Knowledge Base first.",
                );
            const loadedOptions = (await fetchAPI(
                `${BASE}/options?${knowledgeContextParams(context)}`,
            )) as KnowledgeOptionsResponse;
            setOptions(loadedOptions);
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load Knowledge Base document configuration.",
            );
        } finally {
            setIsLoading(false);
        }
    }, [canSave, documentId, initialContext]);

    useEffect(() => {
        void load();
    }, [load]);

    const scopeClientId = form.client_id ? Number(form.client_id) : null;
    const sections = useMemo(
        () =>
            (options?.sections ?? []).filter(
                (section) =>
                    section.ownership_type === form.ownership_type &&
                    section.client_id === scopeClientId,
            ),
        [form.ownership_type, options?.sections, scopeClientId],
    );
    const resources = useMemo(
        () =>
            (options?.resources ?? []).filter(
                (option) =>
                    option.ownership_type === form.ownership_type &&
                    option.client_id === scopeClientId,
            ),
        [form.ownership_type, options?.resources, scopeClientId],
    );
    const credentials = useMemo(
        () =>
            (options?.credentials ?? []).filter(
                (option) =>
                    option.ownership_type === form.ownership_type &&
                    option.client_id === scopeClientId,
            ),
        [form.ownership_type, options?.credentials, scopeClientId],
    );

    function update<K extends keyof FormState>(key: K, value: FormState[K]) {
        setForm((current) => ({ ...current, [key]: value }));
    }

    async function save(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!canSave || (!documentId && !initialContext)) return;
        if (!form.title.trim()) {
            setError("Document title is required.");
            return;
        }
        if (!form.section_id) {
            setError("Choose a Knowledge Base folder.");
            return;
        }
        if (form.ownership_type === "client" && !form.client_id) {
            setError("Client documentation requires a client.");
            return;
        }

        const common = {
            title: form.title.trim(),
            summary: form.summary.trim(),
            section_id: Number(form.section_id),
            content: form.content,
            tag_names: form.tags
                .split(",")
                .map((tag) => tag.trim())
                .filter(Boolean),
        };
        const canManageResources =
            (options?.resources.length ?? 0) > 0 || !documentId;
        const canManageCredentials =
            (options?.credentials.length ?? 0) > 0 || !documentId;
        const payload = documentId
            ? {
                  ...common,
                  change_summary: form.change_summary.trim(),
                  ...(canManageResources
                      ? { resource_ids: form.resource_ids }
                      : {}),
                  ...(canManageCredentials
                      ? { credential_ids: form.credential_ids }
                      : {}),
              }
            : {
                  ...common,
                  ownership_type: form.ownership_type,
                  client_id: form.client_id ? Number(form.client_id) : null,
                  resource_ids: form.resource_ids,
                  credential_ids: form.credential_ids,
              };

        try {
            setIsSaving(true);
            setError(null);
            const saved = (await fetchAPI(
                documentId
                    ? `${BASE}/documents/${documentId}`
                    : `${BASE}/documents`,
                {
                    method: documentId ? "PUT" : "POST",
                    body: JSON.stringify(payload),
                },
            )) as KnowledgeDocumentDetail;
            router.push(`/admin/knowledge-base/documents/${saved.id}`);
            router.refresh();
        } catch (saveError) {
            setError(
                saveError instanceof Error
                    ? saveError.message
                    : "Unable to save document.",
            );
        } finally {
            setIsSaving(false);
        }
    }

    if (!documentId && !initialContext)
        return (
            <Card className="space-y-3 p-5">
                <p>
                    Choose a Client or Internal Knowledge Base before creating a
                    document.
                </p>
                <ButtonLink href="/admin/knowledge-base">
                    Choose Knowledge Base
                </ButtonLink>
            </Card>
        );
    if (!canSave) {
        return (
            <DataError message="You do not have permission to save Knowledge Base documents." />
        );
    }
    if (isLoading) return <DataLoading />;

    return (
        <form className="space-y-5" onSubmit={save}>
            {error ? <DataError message={error} /> : null}
            <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
                <div className="space-y-5">
                    <Card className="space-y-4 p-5">
                        <div className="grid gap-4 md:grid-cols-2">
                            <label className={labelClass}>
                                Ownership
                                <Select value={form.ownership_type} disabled>
                                    <option value="internal">
                                        ADB Internal
                                    </option>
                                    <option value="client">Client</option>
                                </Select>
                            </label>
                            <label className={labelClass}>
                                Client
                                <Select value={form.client_id} disabled>
                                    <option value="">Select client</option>
                                    {options?.clients.map((client) => (
                                        <option
                                            key={client.id}
                                            value={client.id}
                                        >
                                            {client.label}
                                        </option>
                                    ))}
                                </Select>
                            </label>
                        </div>
                        {documentId ? (
                            <p className="text-xs text-slate-500">
                                Ownership is immutable in normal edits. Moving
                                documentation between scopes requires an
                                explicit migration.
                            </p>
                        ) : null}
                        <label className={labelClass}>
                            Title
                            <Input
                                value={form.title}
                                onChange={(event) =>
                                    update("title", event.target.value)
                                }
                                maxLength={200}
                                required
                            />
                        </label>
                        <label className={labelClass}>
                            Summary
                            <Textarea
                                value={form.summary}
                                onChange={(event) =>
                                    update("summary", event.target.value)
                                }
                                rows={3}
                                placeholder="Short operational summary…"
                            />
                        </label>
                        {sections.length === 0 ? (
                            <p className="text-sm text-slate-400">
                                Create a folder in this Knowledge Base before
                                adding an article.{" "}
                                <ButtonLink
                                    variant="secondary"
                                    href={knowledgeBaseHref(
                                        parseKnowledgeContext(
                                            form.ownership_type,
                                            form.client_id || undefined,
                                        ) ?? {
                                            ownership_type: "internal",
                                            client_id: null,
                                        },
                                    )}
                                >
                                    Open folders
                                </ButtonLink>
                            </p>
                        ) : null}
                        <div className="grid gap-4 md:grid-cols-2">
                            <label className={labelClass}>
                                Folder
                                <Select
                                    value={form.section_id}
                                    onChange={(event) =>
                                        update("section_id", event.target.value)
                                    }
                                    required
                                >
                                    <option value="">Select folder</option>
                                    {sections.map((section) => (
                                        <option
                                            key={section.id}
                                            value={section.id}
                                        >
                                            {section.path}
                                        </option>
                                    ))}
                                </Select>
                            </label>
                            <label className={labelClass}>
                                Tags
                                <Input
                                    value={form.tags}
                                    onChange={(event) =>
                                        update("tags", event.target.value)
                                    }
                                    placeholder="deployment, nginx, runbook"
                                />
                            </label>
                        </div>
                    </Card>

                    <Card className="p-5">
                        <div className="mb-3 flex items-center justify-between gap-3">
                            <div>
                                <h2 className="font-semibold text-slate-100">
                                    Markdown
                                </h2>
                                <p className="mt-1 text-xs text-slate-500">
                                    GitHub-flavoured Markdown; raw HTML is not
                                    rendered.
                                </p>
                            </div>
                        </div>
                        <Textarea
                            value={form.content}
                            onChange={(event) =>
                                update("content", event.target.value)
                            }
                            rows={24}
                            className="font-mono text-sm"
                        />
                    </Card>

                    {documentId ? (
                        <Card className="p-5">
                            <label className={labelClass}>
                                Version change summary
                                <Input
                                    value={form.change_summary}
                                    onChange={(event) =>
                                        update(
                                            "change_summary",
                                            event.target.value,
                                        )
                                    }
                                    maxLength={500}
                                    placeholder="What changed in this revision?"
                                />
                            </label>
                        </Card>
                    ) : null}
                </div>

                <div className="space-y-5">
                    <Card className="p-5">
                        <h2 className="mb-4 font-semibold text-slate-100">
                            Live preview
                        </h2>
                        <div className="max-h-[34rem] overflow-y-auto pr-2">
                            <MarkdownContent content={form.content} />
                        </div>
                    </Card>
                    <OptionChecklist
                        title="Infrastructure"
                        description="Backlink this document to structured resources in the same ownership scope."
                        options={resources}
                        selected={form.resource_ids}
                        onToggle={(id) =>
                            update(
                                "resource_ids",
                                toggleId(form.resource_ids, id),
                            )
                        }
                    />
                    <OptionChecklist
                        title="Credential Vault"
                        description="Link credential metadata only. Secret values are never copied into documentation."
                        options={credentials}
                        selected={form.credential_ids}
                        onToggle={(id) =>
                            update(
                                "credential_ids",
                                toggleId(form.credential_ids, id),
                            )
                        }
                    />
                </div>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-3">
                <ButtonLink
                    href={
                        documentId
                            ? `/admin/knowledge-base/documents/${documentId}`
                            : initialContext
                              ? `${knowledgeBaseHref(initialContext)}${initialSectionId ? `&section_id=${initialSectionId}` : ""}`
                              : "/admin/knowledge-base"
                    }
                    variant="secondary"
                >
                    Cancel
                </ButtonLink>
                <Button type="submit" disabled={isSaving}>
                    {isSaving
                        ? "Saving…"
                        : original
                          ? "Save revision"
                          : "Create document"}
                </Button>
            </div>
        </form>
    );
}
