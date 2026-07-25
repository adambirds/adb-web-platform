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

interface TestimonialItem {
    id: number;
    client_name: string;
    company: string;
    rating: number;
    featured: boolean;
    quote?: string;
    job_title?: string;
}

export default function AdminTestimonialsPage() {
    const [items, setItems] = useState<TestimonialItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [editing, setEditing] = useState<TestimonialItem | null>(null);
    const [editForm, setEditForm] = useState({
        quote: "",
        client_name: "",
        company: "",
        job_title: "",
        rating: 5,
        featured: false,
    });

    useEffect(() => {
        async function load() {
            try {
                const data = await fetchAPI(
                    AdminAPI.website.testimonials.list(),
                    {
                        credentials: "include",
                    },
                );
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
        const payload = {
            quote: formData.get("quote"),
            client_name: formData.get("client_name"),
            company: formData.get("company") || "",
            job_title: formData.get("job_title") || "",
            rating: Number(formData.get("rating") || 5),
            featured: Boolean(formData.get("featured")),
        };

        try {
            const created = await fetchAPI(
                AdminAPI.website.testimonials.create(),
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
            await fetchAPI(AdminAPI.website.testimonials.delete(id), {
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
            quote: editForm.quote,
            client_name: editForm.client_name,
            company: editForm.company,
            job_title: editForm.job_title,
            rating: editForm.rating,
            featured: editForm.featured,
        };

        try {
            const updated = await fetchAPI(
                AdminAPI.website.testimonials.update(editing.id),
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
                title="Testimonials"
                description="Manage client testimonials and featured quotes."
                actions={
                    <ButtonLink href="/admin/content">
                        Back to content
                    </ButtonLink>
                }
            />

            <div className="mt-8">
                <Card>
                    <CardHeader>
                        <CardTitle>Create testimonial</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleCreate} className="space-y-4">
                            <Textarea
                                name="quote"
                                rows={4}
                                placeholder="Quote"
                                required
                            />
                            <div className="grid gap-4 md:grid-cols-2">
                                <Input
                                    name="client_name"
                                    placeholder="Client name"
                                    required
                                />
                                <Input
                                    name="company"
                                    placeholder="Company (optional)"
                                />
                            </div>
                            <div className="grid gap-4 md:grid-cols-2">
                                <Input
                                    name="job_title"
                                    placeholder="Job title (optional)"
                                />
                                <Input
                                    name="rating"
                                    type="number"
                                    min={1}
                                    max={5}
                                    defaultValue={5}
                                />
                            </div>
                            <label className="text-adb-navy-600 dark:text-adb-navy-300 flex items-center gap-2 text-sm">
                                <input type="checkbox" name="featured" />
                                Featured
                            </label>
                            <Button type="submit" disabled={saving}>
                                {saving ? "Creating..." : "Create testimonial"}
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                {editing ? (
                    <Card className="mt-6">
                        <CardHeader>
                            <CardTitle>Edit testimonial</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleUpdate} className="space-y-4">
                                <Textarea
                                    name="quote"
                                    value={editForm.quote}
                                    onChange={(event) =>
                                        setEditForm((prev) => ({
                                            ...prev,
                                            quote: event.target.value,
                                        }))
                                    }
                                    rows={4}
                                    placeholder="Quote"
                                    required
                                />
                                <div className="grid gap-4 md:grid-cols-2">
                                    <Input
                                        name="client_name"
                                        value={editForm.client_name}
                                        onChange={(event) =>
                                            setEditForm((prev) => ({
                                                ...prev,
                                                client_name: event.target.value,
                                            }))
                                        }
                                        placeholder="Client name"
                                        required
                                    />
                                    <Input
                                        name="company"
                                        value={editForm.company}
                                        onChange={(event) =>
                                            setEditForm((prev) => ({
                                                ...prev,
                                                company: event.target.value,
                                            }))
                                        }
                                        placeholder="Company (optional)"
                                    />
                                </div>
                                <div className="grid gap-4 md:grid-cols-2">
                                    <Input
                                        name="job_title"
                                        value={editForm.job_title}
                                        onChange={(event) =>
                                            setEditForm((prev) => ({
                                                ...prev,
                                                job_title: event.target.value,
                                            }))
                                        }
                                        placeholder="Job title (optional)"
                                    />
                                    <Input
                                        name="rating"
                                        type="number"
                                        min={1}
                                        max={5}
                                        value={editForm.rating}
                                        onChange={(event) =>
                                            setEditForm((prev) => ({
                                                ...prev,
                                                rating: Number(
                                                    event.target.value,
                                                ),
                                            }))
                                        }
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
                                        {saving
                                            ? "Updating..."
                                            : "Update testimonial"}
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
                        title="No testimonials yet"
                        description="Add testimonials to build trust on the marketing site."
                    />
                ) : (
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableHeaderCell>Client</TableHeaderCell>
                                <TableHeaderCell>Company</TableHeaderCell>
                                <TableHeaderCell>Rating</TableHeaderCell>
                                <TableHeaderCell>Featured</TableHeaderCell>
                                <TableHeaderCell>Actions</TableHeaderCell>
                            </TableRow>
                        </TableHead>
                        <tbody>
                            {items.map((item) => (
                                <TableRow key={item.id}>
                                    <TableCell>{item.client_name}</TableCell>
                                    <TableCell>{item.company || "—"}</TableCell>
                                    <TableCell>{item.rating}</TableCell>
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
                                                        quote: item.quote || "",
                                                        client_name:
                                                            item.client_name,
                                                        company:
                                                            item.company || "",
                                                        job_title:
                                                            item.job_title ||
                                                            "",
                                                        rating: item.rating,
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
