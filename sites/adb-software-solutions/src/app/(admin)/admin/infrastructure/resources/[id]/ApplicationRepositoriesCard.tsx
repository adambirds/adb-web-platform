"use client";

import { Button, Card, Input, Select, Textarea } from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

interface RepositoryLink {
    id: number;
    repository_resource_id: number;
    repository_name: string;
    role: string;
    path: string;
    notes: string;
}

interface RepositoryOption {
    resource_id: number;
    name: string;
    repository_name: string;
    ownership_type: string;
    client_id: number | null;
    client_name: string | null;
}

interface DataApplicationOptions {
    source_repositories: RepositoryOption[];
}

interface ApplicationRepositoriesCardProps {
    resourceId: number;
    ownershipType: string;
    clientId: number | null;
}

function label(value: string): string {
    return `${value.charAt(0).toUpperCase()}${value.slice(1).replaceAll("_", " ")}`;
}

export function ApplicationRepositoriesCard({
    resourceId,
    ownershipType,
    clientId,
}: ApplicationRepositoriesCardProps) {
    const { hasPermission } = useAuth();
    const canView =
        hasPermission("infrastructure.view_applicationprofile") &&
        hasPermission("infrastructure.view_sourcerepository") &&
        hasPermission("infrastructure.view_applicationrepositorylink");
    const canAdd = hasPermission(
        "infrastructure.add_applicationrepositorylink",
    );
    const canDelete = hasPermission(
        "infrastructure.delete_applicationrepositorylink",
    );

    const [links, setLinks] = useState<RepositoryLink[]>([]);
    const [options, setOptions] = useState<DataApplicationOptions | null>(null);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [showForm, setShowForm] = useState(false);
    const [repositoryId, setRepositoryId] = useState("");
    const [role, setRole] = useState("primary");
    const [path, setPath] = useState("");
    const [notes, setNotes] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [deletingId, setDeletingId] = useState<number | null>(null);

    const loadLinks = useCallback(async () => {
        if (!canView) return;
        try {
            setError(null);
            setLinks(
                (await fetchAPI(
                    `${API_URL}/api/admin/infrastructure/applications/${resourceId}/repository-links`,
                )) as RepositoryLink[],
            );
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load application repositories.",
            );
        }
    }, [canView, resourceId]);

    useEffect(() => {
        void loadLinks();
    }, [loadLinks]);

    useEffect(() => {
        setShowForm(false);
        setOptions(null);
        setRepositoryId("");
        setRole("primary");
        setPath("");
        setNotes("");
        setError(null);
    }, [resourceId]);

    const repositoryOptions = useMemo(
        () =>
            options?.source_repositories.filter((repository) => {
                if (ownershipType === "internal") {
                    return repository.ownership_type === "internal";
                }
                return (
                    repository.ownership_type === "internal" ||
                    repository.client_id === clientId
                );
            }) ?? [],
        [clientId, options, ownershipType],
    );

    async function openForm(link?: RepositoryLink) {
        setEditingId(link?.id ?? null);
        setRepositoryId(link ? String(link.repository_resource_id) : "");
        setRole(link?.role ?? "primary");
        setPath(link?.path ?? "");
        setNotes(link?.notes ?? "");
        setShowForm(true);
        setError(null);
        if (options) return;
        try {
            setOptions(
                (await fetchAPI(
                    `${API_URL}/api/admin/infrastructure/data-application-options`,
                )) as DataApplicationOptions,
            );
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load source repository options.",
            );
        }
    }

    async function addRepository() {
        if (!repositoryId) {
            setError("Choose a Source Repository.");
            return;
        }
        try {
            setIsSaving(true);
            setError(null);
            await fetchAPI(
                `${API_URL}/api/admin/infrastructure/applications/${resourceId}/repositories${editingId === null ? "" : `/${editingId}`}`,
                {
                    method: editingId === null ? "POST" : "PUT",
                    body: JSON.stringify({
                        repository_resource_id: Number(repositoryId),
                        role,
                        path: path.trim(),
                        notes: notes.trim(),
                    }),
                },
            );
            setShowForm(false);
            setRepositoryId("");
            setRole("primary");
            setPath("");
            setNotes("");
            await loadLinks();
        } catch (saveError) {
            setError(
                saveError instanceof Error
                    ? saveError.message
                    : "Unable to link this source repository.",
            );
        } finally {
            setIsSaving(false);
        }
    }

    async function removeRepository(link: RepositoryLink) {
        if (
            !window.confirm(
                `Remove ${link.repository_name} from this application?`,
            )
        )
            return;
        try {
            setDeletingId(link.id);
            setError(null);
            await fetchAPI(
                `${API_URL}/api/admin/infrastructure/applications/${resourceId}/repositories/${link.id}`,
                { method: "DELETE" },
            );
            await loadLinks();
        } catch (deleteError) {
            setError(
                deleteError instanceof Error
                    ? deleteError.message
                    : "Unable to remove this repository link.",
            );
        } finally {
            setDeletingId(null);
        }
    }

    if (!canView) return null;

    return (
        <Card className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                    <h2 className="text-sm font-semibold text-white">
                        Source repositories
                    </h2>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                        Typed source-control links for this Application,
                        including repository role and optional monorepo path.
                    </p>
                </div>
                {canAdd ? (
                    <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => void openForm()}
                    >
                        Add repository
                    </Button>
                ) : null}
            </div>

            {showForm ? (
                <div className="mt-5 space-y-4 rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                    <div className="grid gap-3 md:grid-cols-2">
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                            Source repository
                            <Select
                                value={repositoryId}
                                onChange={(event) =>
                                    setRepositoryId(event.target.value)
                                }
                                disabled={isSaving || !options}
                            >
                                <option value="">Choose repository</option>
                                {repositoryOptions.map((repository) => (
                                    <option
                                        key={repository.resource_id}
                                        value={repository.resource_id}
                                    >
                                        {repository.name} ·{" "}
                                        {repository.repository_name}
                                    </option>
                                ))}
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Role
                            <Select
                                value={role}
                                onChange={(event) =>
                                    setRole(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="primary">Primary</option>
                                <option value="backend">Backend</option>
                                <option value="frontend">Frontend</option>
                                <option value="infrastructure">
                                    Infrastructure
                                </option>
                                <option value="mobile">Mobile</option>
                                <option value="documentation">
                                    Documentation
                                </option>
                                <option value="other">Other</option>
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Monorepo path
                            <Input
                                value={path}
                                onChange={(event) =>
                                    setPath(event.target.value)
                                }
                                placeholder="sites/customer-portal"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                            Operational notes
                            <Textarea
                                value={notes}
                                onChange={(event) =>
                                    setNotes(event.target.value)
                                }
                                rows={2}
                                placeholder="Do not store passwords, tokens or private keys here."
                                disabled={isSaving}
                            />
                        </label>
                    </div>
                    <div className="flex justify-end gap-2">
                        <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowForm(false)}
                            disabled={isSaving}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="button"
                            size="sm"
                            onClick={() => void addRepository()}
                            disabled={isSaving || !repositoryId}
                        >
                            {isSaving
                                ? "Saving..."
                                : editingId === null
                                  ? "Link repository"
                                  : "Save repository link"}
                        </Button>
                    </div>
                </div>
            ) : null}

            {error ? (
                <p className="mt-4 text-sm text-red-300">{error}</p>
            ) : null}

            {links.length === 0 ? (
                <p className="mt-5 text-sm text-slate-500">
                    No source repositories are linked to this Application yet.
                </p>
            ) : (
                <div className="mt-4 divide-y divide-slate-800">
                    {links.map((link) => (
                        <div
                            key={link.id}
                            className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between"
                        >
                            <Link
                                href={`/admin/infrastructure/resources/${link.repository_resource_id}`}
                                className="hover:text-adb-cyan-300 min-w-0 flex-1"
                            >
                                <div className="text-sm font-medium text-slate-200">
                                    {link.repository_name}
                                </div>
                                <div className="mt-0.5 text-xs text-slate-500">
                                    {label(link.role)}
                                    {link.path ? ` · ${link.path}` : ""}
                                </div>
                                {link.notes ? (
                                    <div className="mt-1 text-xs text-slate-600">
                                        {link.notes}
                                    </div>
                                ) : null}
                            </Link>
                            {hasPermission(
                                "infrastructure.change_applicationrepositorylink",
                            ) ? (
                                <Button
                                    type="button"
                                    variant="secondary"
                                    size="sm"
                                    onClick={() => void openForm(link)}
                                >
                                    Edit
                                </Button>
                            ) : null}
                            {canDelete ? (
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => void removeRepository(link)}
                                    disabled={deletingId === link.id}
                                >
                                    {deletingId === link.id
                                        ? "Removing..."
                                        : "Remove"}
                                </Button>
                            ) : null}
                        </div>
                    ))}
                </div>
            )}
        </Card>
    );
}
