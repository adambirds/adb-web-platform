"use client";

import { ContentImageEditor } from "@/components/content/ContentImageEditor";
import {
    BrandSelector,
    type BrandOption,
} from "@/components/content/BrandSelector";
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
import { useEffect, useMemo, useState } from "react";

interface TestimonialItem {
    published: boolean;
    image_alt: string;
    image_url: string | null;
    id: number;
    quote: string;
    client_name: string;
    company: string;
    job_title: string;
    rating: number;
    featured: boolean;
    brand_slugs: string[];
}

interface TestimonialForm {
    published: boolean;
    image_alt: string;
    quote: string;
    client_name: string;
    company: string;
    job_title: string;
    rating: number;
    featured: boolean;
    brand_ids: number[];
}

const EMPTY_FORM: TestimonialForm = {
    published: false,
    image_alt: "",
    quote: "",
    client_name: "",
    company: "",
    job_title: "",
    rating: 5,
    featured: false,
    brand_ids: [],
};

export default function AdminTestimonialsPage() {
    const [items, setItems] = useState<TestimonialItem[]>([]);
    const [brands, setBrands] = useState<BrandOption[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [editing, setEditing] = useState<TestimonialItem | null>(null);
    const [createForm, setCreateForm] = useState<TestimonialForm>(EMPTY_FORM);
    const [editForm, setEditForm] = useState<TestimonialForm>(EMPTY_FORM);
    const [brandFilter, setBrandFilter] = useState("all");

    useEffect(() => {
        async function load() {
            try {
                const [testimonialData, brandData] = await Promise.all([
                    fetchAPI(AdminAPI.website.testimonials.list(), {
                        credentials: "include",
                    }),
                    fetchAPI(AdminAPI.brands.list(), {
                        credentials: "include",
                    }),
                ]);
                setItems(testimonialData as TestimonialItem[]);
                setBrands(brandData as BrandOption[]);
            } catch (error) {
                setErrorMessage(
                    error instanceof Error
                        ? error.message
                        : "Unable to update content.",
                );
            } finally {
                setLoading(false);
            }
        }
        void load();
    }, []);

    const brandIdBySlug = useMemo(
        () => new Map(brands.map((brand) => [brand.slug, brand.id])),
        [brands],
    );

    const visibleItems = useMemo(
        () =>
            brandFilter === "all"
                ? items
                : items.filter((item) =>
                      item.brand_slugs.includes(brandFilter),
                  ),
        [brandFilter, items],
    );

    async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (createForm.brand_ids.length === 0) return;
        setSaving(true);
        setErrorMessage("");
        try {
            const created = await fetchAPI(
                AdminAPI.website.testimonials.create(),
                {
                    method: "POST",
                    credentials: "include",
                    body: JSON.stringify(createForm),
                },
            );
            setItems((previous) => [created as TestimonialItem, ...previous]);
            setCreateForm(EMPTY_FORM);
        } catch (error) {
            setErrorMessage(
                error instanceof Error
                    ? error.message
                    : "Unable to update content.",
            );
        } finally {
            setSaving(false);
        }
    }

    async function handleUpdate(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!editing || editForm.brand_ids.length === 0) return;
        setSaving(true);
        setErrorMessage("");
        try {
            const updated = await fetchAPI(
                AdminAPI.website.testimonials.update(editing.id),
                {
                    method: "PUT",
                    credentials: "include",
                    body: JSON.stringify(editForm),
                },
            );
            setItems((previous) =>
                previous.map((item) =>
                    item.id === editing.id
                        ? (updated as TestimonialItem)
                        : item,
                ),
            );
            setEditing(null);
        } catch (error) {
            setErrorMessage(
                error instanceof Error
                    ? error.message
                    : "Unable to update content.",
            );
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
            setItems((previous) => previous.filter((item) => item.id !== id));
        } catch (error) {
            setErrorMessage(
                error instanceof Error
                    ? error.message
                    : "Unable to update content.",
            );
        }
    }

    function beginEdit(item: TestimonialItem) {
        setEditing(item);
        setEditForm({
            published: item.published,
            image_alt: item.image_alt,
            quote: item.quote,
            client_name: item.client_name,
            company: item.company,
            job_title: item.job_title,
            rating: item.rating,
            featured: item.featured,
            brand_ids: item.brand_slugs
                .map((slug) => brandIdBySlug.get(slug))
                .filter((id): id is number => id !== undefined),
        });
    }

    return (
        <Container className="py-10">
            {errorMessage ? (
                <p
                    role="alert"
                    className="mb-6 border-l-4 border-red-500 p-4 text-sm"
                >
                    {errorMessage}
                </p>
            ) : null}
            <PageHeader
                title="Testimonials"
                description="Manage brand-aware client testimonials and featured quotes."
                actions={
                    <ButtonLink href="/admin/content">
                        Back to content
                    </ButtonLink>
                }
            />

            <div className="mt-8 space-y-6">
                <Card>
                    <CardHeader>
                        <CardTitle>Create testimonial</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleCreate} className="space-y-4">
                            <Textarea
                                value={createForm.quote}
                                onChange={(event) =>
                                    setCreateForm((form) => ({
                                        ...form,
                                        quote: event.target.value,
                                    }))
                                }
                                rows={4}
                                placeholder="Quote"
                                required
                            />
                            <div className="grid gap-4 md:grid-cols-2">
                                <Input
                                    value={createForm.client_name}
                                    onChange={(event) =>
                                        setCreateForm((form) => ({
                                            ...form,
                                            client_name: event.target.value,
                                        }))
                                    }
                                    placeholder="Client name"
                                    required
                                />
                                <Input
                                    value={createForm.company}
                                    onChange={(event) =>
                                        setCreateForm((form) => ({
                                            ...form,
                                            company: event.target.value,
                                        }))
                                    }
                                    placeholder="Company (optional)"
                                />
                                <Input
                                    value={createForm.job_title}
                                    onChange={(event) =>
                                        setCreateForm((form) => ({
                                            ...form,
                                            job_title: event.target.value,
                                        }))
                                    }
                                    placeholder="Job title (optional)"
                                />
                                <Input
                                    type="number"
                                    min={1}
                                    max={5}
                                    value={createForm.rating}
                                    onChange={(event) =>
                                        setCreateForm((form) => ({
                                            ...form,
                                            rating: Number(event.target.value),
                                        }))
                                    }
                                />
                            </div>
                            <Input
                                value={createForm.image_alt}
                                maxLength={300}
                                aria-label="Client image alternative text"
                                onChange={(event) =>
                                    setCreateForm((current) => ({
                                        ...current,
                                        image_alt: event.target.value,
                                    }))
                                }
                                placeholder="Client image alternative text"
                            />
                            <label className="flex items-center gap-2 text-sm">
                                <input
                                    type="checkbox"
                                    checked={createForm.published}
                                    onChange={(event) =>
                                        setCreateForm((current) => ({
                                            ...current,
                                            published: event.target.checked,
                                        }))
                                    }
                                />{" "}
                                Published on selected websites
                            </label>
                            <BrandSelector
                                selectedIds={createForm.brand_ids}
                                onChange={(brand_ids) =>
                                    setCreateForm((form) => ({
                                        ...form,
                                        brand_ids,
                                    }))
                                }
                                disabled={saving}
                            />
                            <label className="text-adb-navy-600 dark:text-adb-navy-300 flex items-center gap-2 text-sm">
                                <input
                                    type="checkbox"
                                    checked={createForm.featured}
                                    onChange={(event) =>
                                        setCreateForm((form) => ({
                                            ...form,
                                            featured: event.target.checked,
                                        }))
                                    }
                                />{" "}
                                Featured
                            </label>
                            <Button
                                type="submit"
                                disabled={
                                    saving || createForm.brand_ids.length === 0
                                }
                            >
                                {saving ? "Creating..." : "Create testimonial"}
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                {editing ? (
                    <Card>
                        <CardHeader>
                            <CardTitle>Edit testimonial</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleUpdate} className="space-y-4">
                                <ContentImageEditor
                                    key={editing.id}
                                    kind="testimonial"
                                    itemId={editing.id}
                                    field="image"
                                    label="Client image"
                                    initialUrl={editing.image_url}
                                />
                                <Textarea
                                    value={editForm.quote}
                                    onChange={(event) =>
                                        setEditForm((form) => ({
                                            ...form,
                                            quote: event.target.value,
                                        }))
                                    }
                                    rows={4}
                                    required
                                />
                                <div className="grid gap-4 md:grid-cols-2">
                                    <Input
                                        value={editForm.client_name}
                                        onChange={(event) =>
                                            setEditForm((form) => ({
                                                ...form,
                                                client_name: event.target.value,
                                            }))
                                        }
                                        required
                                    />
                                    <Input
                                        value={editForm.company}
                                        onChange={(event) =>
                                            setEditForm((form) => ({
                                                ...form,
                                                company: event.target.value,
                                            }))
                                        }
                                        placeholder="Company (optional)"
                                    />
                                    <Input
                                        value={editForm.job_title}
                                        onChange={(event) =>
                                            setEditForm((form) => ({
                                                ...form,
                                                job_title: event.target.value,
                                            }))
                                        }
                                        placeholder="Job title (optional)"
                                    />
                                    <Input
                                        type="number"
                                        min={1}
                                        max={5}
                                        value={editForm.rating}
                                        onChange={(event) =>
                                            setEditForm((form) => ({
                                                ...form,
                                                rating: Number(
                                                    event.target.value,
                                                ),
                                            }))
                                        }
                                    />
                                </div>
                                <Input
                                    value={editForm.image_alt}
                                    maxLength={300}
                                    aria-label="Client image alternative text"
                                    onChange={(event) =>
                                        setEditForm((current) => ({
                                            ...current,
                                            image_alt: event.target.value,
                                        }))
                                    }
                                    placeholder="Client image alternative text"
                                />
                                <label className="flex items-center gap-2 text-sm">
                                    <input
                                        type="checkbox"
                                        checked={editForm.published}
                                        onChange={(event) =>
                                            setEditForm((current) => ({
                                                ...current,
                                                published: event.target.checked,
                                            }))
                                        }
                                    />{" "}
                                    Published on selected websites
                                </label>
                                <BrandSelector
                                    selectedIds={editForm.brand_ids}
                                    onChange={(brand_ids) =>
                                        setEditForm((form) => ({
                                            ...form,
                                            brand_ids,
                                        }))
                                    }
                                    disabled={saving}
                                />
                                <label className="text-adb-navy-600 dark:text-adb-navy-300 flex items-center gap-2 text-sm">
                                    <input
                                        type="checkbox"
                                        checked={editForm.featured}
                                        onChange={(event) =>
                                            setEditForm((form) => ({
                                                ...form,
                                                featured: event.target.checked,
                                            }))
                                        }
                                    />{" "}
                                    Featured
                                </label>
                                <div className="flex gap-3">
                                    <Button
                                        type="submit"
                                        disabled={
                                            saving ||
                                            editForm.brand_ids.length === 0
                                        }
                                    >
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

                <div className="flex items-center gap-3">
                    <label
                        htmlFor="testimonial-brand-filter"
                        className="text-sm font-medium"
                    >
                        Brand
                    </label>
                    <select
                        id="testimonial-brand-filter"
                        value={brandFilter}
                        onChange={(event) => setBrandFilter(event.target.value)}
                        className="border-adb-navy-200 dark:border-adb-navy-700 rounded-md border bg-transparent px-3 py-2 text-sm"
                    >
                        <option value="all">All brands</option>
                        {brands
                            .filter((brand) => brand.is_active)
                            .map((brand) => (
                                <option key={brand.id} value={brand.slug}>
                                    {brand.name}
                                </option>
                            ))}
                    </select>
                </div>

                {loading ? (
                    <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                        Loading...
                    </p>
                ) : visibleItems.length === 0 ? (
                    <EmptyState
                        title="No testimonials found"
                        description="Add a testimonial or change the selected brand filter."
                    />
                ) : (
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableHeaderCell>Client</TableHeaderCell>
                                <TableHeaderCell>Company</TableHeaderCell>
                                <TableHeaderCell>Brands</TableHeaderCell>
                                <TableHeaderCell>Rating</TableHeaderCell>
                                <TableHeaderCell>Published</TableHeaderCell>
                                <TableHeaderCell>Featured</TableHeaderCell>
                                <TableHeaderCell>Actions</TableHeaderCell>
                            </TableRow>
                        </TableHead>
                        <tbody>
                            {visibleItems.map((item) => (
                                <TableRow key={item.id}>
                                    <TableCell>{item.client_name}</TableCell>
                                    <TableCell>{item.company || "—"}</TableCell>
                                    <TableCell>
                                        {item.brand_slugs.join(", ") || "—"}
                                    </TableCell>
                                    <TableCell>{item.rating}</TableCell>
                                    <TableCell>
                                        {item.published ? "Yes" : "Draft"}
                                    </TableCell>
                                    <TableCell>
                                        {item.featured ? "Yes" : "No"}
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex gap-2">
                                            <Button
                                                type="button"
                                                variant="outline"
                                                size="sm"
                                                onClick={() => beginEdit(item)}
                                            >
                                                Edit
                                            </Button>
                                            <Button
                                                type="button"
                                                variant="destructive"
                                                size="sm"
                                                onClick={() =>
                                                    void handleDelete(item.id)
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
