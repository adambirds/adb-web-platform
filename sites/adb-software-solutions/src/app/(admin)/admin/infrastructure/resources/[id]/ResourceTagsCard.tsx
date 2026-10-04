"use client";

import { Button, Card, Input, Select } from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import { useEffect, useState, type FormEvent } from "react";

interface Tag {
    id: number;
    name: string;
    slug: string;
    colour: string;
}
export function ResourceTagsCard({
    resourceId,
    tags,
    onChanged,
}: {
    resourceId: number;
    tags: Tag[];
    onChanged: () => void;
}) {
    const { hasPermission } = useAuth();
    const canEdit =
        hasPermission("infrastructure.change_infrastructureresource") &&
        hasPermission("infrastructure.view_infrastructuretag");
    const [options, setOptions] = useState<Tag[]>([]);
    const [search, setSearch] = useState("");
    const [selected, setSelected] = useState("");
    const [editingId, setEditingId] = useState<number | null>(null);
    const [creating, setCreating] = useState(false);
    const [name, setName] = useState("");
    const [slug, setSlug] = useState("");
    const [colour, setColour] = useState("");
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    useEffect(() => {
        if (!canEdit) return;
        let active = true;
        void fetchAPI(
            `${API_URL}/api/admin/infrastructure/tags?${new URLSearchParams({ search, page_size: "100" })}`,
        )
            .then((response: { items: Tag[] }) => {
                if (active) {
                    setOptions(response.items);
                    setError(null);
                }
            })
            .catch((failure: unknown) => {
                if (active)
                    setError(
                        failure instanceof Error
                            ? failure.message
                            : "Unable to load tags.",
                    );
            });
        return () => {
            active = false;
        };
    }, [canEdit, search]);
    async function assign(id: number, remove = false) {
        setSaving(true);
        setError(null);
        try {
            await fetchAPI(
                `${API_URL}/api/admin/infrastructure/resources/${resourceId}/tags/${id}`,
                { method: remove ? "DELETE" : "PUT" },
            );
            setSelected("");
            onChanged();
        } catch (failure) {
            setError(
                failure instanceof Error
                    ? failure.message
                    : "Unable to update tags.",
            );
        } finally {
            setSaving(false);
        }
    }
    async function create(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setSaving(true);
        setError(null);
        try {
            const tag = (await fetchAPI(
                `${API_URL}/api/admin/infrastructure/tags${editingId === null ? "" : `/${editingId}`}`,
                {
                    method: editingId === null ? "POST" : "PATCH",
                    body: JSON.stringify({
                        name,
                        slug:
                            slug ||
                            name
                                .toLowerCase()
                                .replace(/[^a-z0-9]+/g, "-")
                                .replace(/^-|-$/g, ""),
                        colour,
                    }),
                },
            )) as Tag;
            setOptions((current) => [
                ...current.filter((item) => item.id !== tag.id),
                tag,
            ]);
            setCreating(false);
            setName("");
            setSlug("");
            setColour("");
            if (editingId === null) await assign(tag.id);
            else onChanged();
            setEditingId(null);
        } catch (failure) {
            setError(
                failure instanceof Error
                    ? failure.message
                    : "Unable to create tag.",
            );
        } finally {
            setSaving(false);
        }
    }
    if (!canEdit) return null;
    return (
        <Card className="space-y-4 p-5">
            <h2 className="font-semibold text-white">Resource tags</h2>
            {error ? (
                <p role="alert" className="text-sm text-red-300">
                    {error}
                </p>
            ) : null}
            <div className="flex flex-wrap gap-2">
                {tags.map((tag) => (
                    <div key={tag.id} className="flex gap-1">
                        <Button
                            key={tag.id}
                            type="button"
                            variant="secondary"
                            disabled={saving}
                            onClick={() => void assign(tag.id, true)}
                            aria-label={`Remove tag ${tag.name}`}
                        >
                            {tag.name} ×
                        </Button>
                        {hasPermission(
                            "infrastructure.change_infrastructuretag",
                        ) ? (
                            <Button
                                type="button"
                                variant="secondary"
                                disabled={saving}
                                aria-label={`Edit tag ${tag.name}`}
                                onClick={() => {
                                    setEditingId(tag.id);
                                    setName(tag.name);
                                    setSlug(tag.slug);
                                    setColour(tag.colour);
                                    setCreating(true);
                                }}
                            >
                                Edit
                            </Button>
                        ) : null}
                    </div>
                ))}
            </div>
            <div className="flex flex-wrap gap-2">
                <Input
                    aria-label="Search tags"
                    placeholder="Search tags..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
                <Select
                    aria-label="Tag to add"
                    value={selected}
                    onChange={(e) => setSelected(e.target.value)}
                >
                    <option value="">Choose a tag</option>
                    {options
                        .filter(
                            (tag) =>
                                !tags.some((current) => current.id === tag.id),
                        )
                        .map((tag) => (
                            <option key={tag.id} value={tag.id}>
                                {tag.name}
                            </option>
                        ))}
                </Select>
                <Button
                    type="button"
                    disabled={saving || !selected}
                    onClick={() => void assign(Number(selected))}
                >
                    Add tag
                </Button>
                {hasPermission("infrastructure.add_infrastructuretag") ? (
                    <Button
                        type="button"
                        variant="secondary"
                        disabled={saving}
                        onClick={() => {
                            setEditingId(null);
                            setName("");
                            setSlug("");
                            setColour("");
                            setCreating(true);
                        }}
                    >
                        Create new tag
                    </Button>
                ) : null}
            </div>
            {creating ? (
                <form
                    onSubmit={(event) => void create(event)}
                    className="space-y-3"
                >
                    {editingId !== null ? (
                        <p className="text-sm text-slate-400">
                            Changes update this shared tag on every resource
                            using it.
                        </p>
                    ) : null}
                    <fieldset disabled={saving} className="grid gap-3">
                        <label>
                            Tag name
                            <Input
                                required
                                maxLength={100}
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                            />
                        </label>
                        <label>
                            Tag slug
                            <Input
                                placeholder="Generated from the name"
                                value={slug}
                                onChange={(e) => setSlug(e.target.value)}
                            />
                        </label>
                        <label>
                            Tag colour
                            <Input
                                maxLength={32}
                                value={colour}
                                onChange={(e) => setColour(e.target.value)}
                            />
                        </label>
                    </fieldset>
                    <div className="flex gap-2">
                        <Button type="submit" disabled={saving}>
                            {editingId === null
                                ? "Create and add tag"
                                : "Save tag"}
                        </Button>
                        <Button
                            type="button"
                            variant="secondary"
                            disabled={saving}
                            onClick={() => setCreating(false)}
                        >
                            Cancel
                        </Button>
                    </div>
                </form>
            ) : null}
        </Card>
    );
}
