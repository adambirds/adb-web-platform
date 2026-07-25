"use client";

import {
    Button,
    ButtonLink,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Container,
    EmptyState,
    Input,
    PageHeader,
    Table,
    TableCell,
    TableHead,
    TableHeaderCell,
    TableRow,
    Textarea,
} from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { useEffect, useState } from "react";

interface PortfolioItem {
    id: number;
    title: string;
    slug: string;
    description?: string;
    challenge?: string;
    solution?: string;
    results?: string;
    technologies?: string[];
    project_url?: string | null;
    github_url?: string | null;
    featured: boolean;
}

export default function AdminPortfolioPage() {
    const [items, setItems] = useState<PortfolioItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [editing, setEditing] = useState<PortfolioItem | null>(null);
    const [editForm, setEditForm] = useState({
        title: "",
        slug: "",
        description: "",
        challenge: "",
        solution: "",
        results: "",
        technologies: "",
        project_url: "",
        github_url: "",
        featured: false,
    });

    useEffect(() => {
        async function load() {
            try {
                const data = await fetchAPI(AdminAPI.website.portfolio.list(), {
                    credentials: "include",
                });
                setItems(data);
            } catch (error) {
                console.error(error);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setSaving(true);
        const formData = new FormData(event.currentTarget);
        const technologies = String(formData.get("technologies") || "")
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean);

        const payload = {
            title: formData.get("title"),
            slug: formData.get("slug"),
            description: formData.get("description"),
            challenge: formData.get("challenge"),
            solution: formData.get("solution"),
            results: formData.get("results"),
            technologies,
            project_url: formData.get("project_url") || null,
            github_url: formData.get("github_url") || null,
            featured: Boolean(formData.get("featured")),
        };

        try {
            const created = await fetchAPI(
                AdminAPI.website.portfolio.create(),
                {
                    method: "POST",
                    credentials: "include",
                    body: JSON.stringify(payload),
                },
            );
            setItems((prev) => [created, ...prev]);
            event.currentTarget.reset();
        } catch (error) {
            console.error(error);
        } finally {
            setSaving(false);
        }
    }

    async function handleDelete(id: number) {
        try {
            await fetchAPI(AdminAPI.website.portfolio.delete(id), {
                method: "DELETE",
                credentials: "include",
            });
            setItems((prev) => prev.filter((item) => item.id !== id));
        } catch (error) {
            console.error(error);
        }
    }

    async function handleUpdate(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!editing) {
            return;
        }
        setSaving(true);
        const payload = {
            title: editForm.title,
            slug: editForm.slug,
            description: editForm.description,
            challenge: editForm.challenge,
            solution: editForm.solution,
            results: editForm.results,
            technologies: editForm.technologies
                .split(",")
                .map((item) => item.trim())
                .filter(Boolean),
            project_url: editForm.project_url || null,
            github_url: editForm.github_url || null,
            featured: editForm.featured,
        };

        try {
            const updated = await fetchAPI(
                AdminAPI.website.portfolio.update(editing.id),
                {
                    method: "PUT",
                    credentials: "include",
                    body: JSON.stringify(payload),
                },
            );
            setItems((prev) =>
                prev.map((item) => (item.id === editing.id ? updated : item)),
            );
            setEditing(null);
        } catch (error) {
            console.error(error);
        } finally {
            setSaving(false);
        }
    }

    return (
        <Container className="py-10">
            <PageHeader
                title="Portfolio"
                description="Manage portfolio case studies and featured work."
                actions={
                    <ButtonLink href="/admin/content">
                        Back to content
                    </ButtonLink>
                }
            />

            <div className="mt-8">
                <Card>
                    <CardHeader>
                        <CardTitle>Create portfolio item</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleCreate} className="space-y-4">
                            <div className="grid gap-4 md:grid-cols-2">
                                <Input
                                    name="title"
                                    placeholder="Title"
                                    required
                                />
                                <Input
                                    name="slug"
                                    placeholder="Slug"
                                    required
                                />
                            </div>
                            <Textarea
                                name="description"
                                placeholder="Short description"
                                rows={3}
                                required
                            />
                            <Textarea
                                name="challenge"
                                placeholder="Challenge"
                                rows={3}
                                required
                            />
                            <Textarea
                                name="solution"
                                placeholder="Solution"
                                rows={3}
                                required
                            />
                            <Textarea
                                name="results"
                                placeholder="Results"
                                rows={3}
                                required
                            />
                            <Input
                                name="technologies"
                                placeholder="Technologies (comma separated)"
                                required
                            />
                            <div className="grid gap-4 md:grid-cols-2">
                                <Input
                                    name="project_url"
                                    placeholder="Project URL"
                                />
                                <Input
                                    name="github_url"
                                    placeholder="GitHub URL"
                                />
                            </div>
                            <label className="text-adb-navy-600 dark:text-adb-navy-300 flex items-center gap-2 text-sm">
                                <input type="checkbox" name="featured" />
                                Featured
                            </label>
                            <Button type="submit" disabled={saving}>
                                {saving ? "Creating..." : "Create item"}
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                {editing ? (
                    <Card className="mt-6">
                        <CardHeader>
                            <CardTitle>Edit portfolio item</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleUpdate} className="space-y-4">
                                <div className="grid gap-4 md:grid-cols-2">
                                    <Input
                                        name="title"
                                        value={editForm.title}
                                        onChange={(event) =>
                                            setEditForm((prev) => ({
                                                ...prev,
                                                title: event.target.value,
                                            }))
                                        }
                                        placeholder="Title"
                                        required
                                    />
                                    <Input
                                        name="slug"
                                        value={editForm.slug}
                                        onChange={(event) =>
                                            setEditForm((prev) => ({
                                                ...prev,
                                                slug: event.target.value,
                                            }))
                                        }
                                        placeholder="Slug"
                                        required
                                    />
                                </div>
                                <Textarea
                                    name="description"
                                    value={editForm.description}
                                    onChange={(event) =>
                                        setEditForm((prev) => ({
                                            ...prev,
                                            description: event.target.value,
                                        }))
                                    }
                                    rows={3}
                                    placeholder="Short description"
                                    required
                                />
                                <Textarea
                                    name="challenge"
                                    value={editForm.challenge}
                                    onChange={(event) =>
                                        setEditForm((prev) => ({
                                            ...prev,
                                            challenge: event.target.value,
                                        }))
                                    }
                                    rows={3}
                                    placeholder="Challenge"
                                    required
                                />
                                <Textarea
                                    name="solution"
                                    value={editForm.solution}
                                    onChange={(event) =>
                                        setEditForm((prev) => ({
                                            ...prev,
                                            solution: event.target.value,
                                        }))
                                    }
                                    rows={3}
                                    placeholder="Solution"
                                    required
                                />
                                <Textarea
                                    name="results"
                                    value={editForm.results}
                                    onChange={(event) =>
                                        setEditForm((prev) => ({
                                            ...prev,
                                            results: event.target.value,
                                        }))
                                    }
                                    rows={3}
                                    placeholder="Results"
                                    required
                                />
                                <Input
                                    name="technologies"
                                    value={editForm.technologies}
                                    onChange={(event) =>
                                        setEditForm((prev) => ({
                                            ...prev,
                                            technologies: event.target.value,
                                        }))
                                    }
                                    placeholder="Technologies (comma separated)"
                                    required
                                />
                                <div className="grid gap-4 md:grid-cols-2">
                                    <Input
                                        name="project_url"
                                        value={editForm.project_url}
                                        onChange={(event) =>
                                            setEditForm((prev) => ({
                                                ...prev,
                                                project_url: event.target.value,
                                            }))
                                        }
                                        placeholder="Project URL"
                                    />
                                    <Input
                                        name="github_url"
                                        value={editForm.github_url}
                                        onChange={(event) =>
                                            setEditForm((prev) => ({
                                                ...prev,
                                                github_url: event.target.value,
                                            }))
                                        }
                                        placeholder="GitHub URL"
                                    />
                                </div>
                                <label className="text-adb-navy-600 dark:text-adb-navy-300 flex items-center gap-2 text-sm">
                                    <input
                                        type="checkbox"
                                        checked={editForm.featured}
                                        onChange={(event) =>
                                            setEditForm((prev) => ({
                                                ...prev,
                                                featured: event.target.checked,
                                            }))
                                        }
                                    />
                                    Featured
                                </label>
                                <div className="flex gap-3">
                                    <Button type="submit" disabled={saving}>
                                        {saving ? "Updating..." : "Update item"}
                                    </Button>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        onClick={() => setEditing(null)}
                                    >
                                        Cancel
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                ) : null}

                {loading ? (
                    <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                        Loading...
                    </p>
                ) : items.length === 0 ? (
                    <EmptyState
                        title="No portfolio items yet"
                        description="Create your first case study to showcase delivery outcomes."
                    />
                ) : (
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableHeaderCell>Title</TableHeaderCell>
                                <TableHeaderCell>Slug</TableHeaderCell>
                                <TableHeaderCell>Featured</TableHeaderCell>
                                <TableHeaderCell>Actions</TableHeaderCell>
                            </TableRow>
                        </TableHead>
                        <tbody>
                            {items.map((item) => (
                                <TableRow key={item.id}>
                                    <TableCell>{item.title}</TableCell>
                                    <TableCell>{item.slug}</TableCell>
                                    <TableCell>
                                        {item.featured ? "Yes" : "No"}
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex gap-2">
                                            <Button
                                                type="button"
                                                variant="outline"
                                                size="sm"
                                                onClick={() => {
                                                    setEditing(item);
                                                    setEditForm({
                                                        title: item.title,
                                                        slug: item.slug,
                                                        description:
                                                            item.description ??
                                                            "",
                                                        challenge:
                                                            item.challenge ??
                                                            "",
                                                        solution:
                                                            item.solution ?? "",
                                                        results:
                                                            item.results ?? "",
                                                        technologies:
                                                            Array.isArray(
                                                                item.technologies,
                                                            )
                                                                ? item.technologies.join(
                                                                      ", ",
                                                                  )
                                                                : String(
                                                                      item.technologies ||
                                                                          "",
                                                                  ),
                                                        project_url:
                                                            item.project_url ??
                                                            "",
                                                        github_url:
                                                            item.github_url ??
                                                            "",
                                                        featured: item.featured,
                                                    });
                                                }}
                                            >
                                                Edit
                                            </Button>
                                            <Button
                                                type="button"
                                                variant="destructive"
                                                size="sm"
                                                onClick={() =>
                                                    handleDelete(item.id)
                                                }
                                            >
                                                Delete
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </tbody>
                    </Table>
                )}
            </div>
        </Container>
    );
}
