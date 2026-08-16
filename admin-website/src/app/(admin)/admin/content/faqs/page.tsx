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
    Select,
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

interface FAQItem {
    id: number;
    question: string;
    answer: string;
    category: { id: number; name: string };
    order: number;
}

interface FAQCategory {
    id: number;
    name: string;
    slug?: string;
    description?: string;
    order?: number;
}

export default function AdminFAQsPage() {
    const [items, setItems] = useState<FAQItem[]>([]);
    const [categories, setCategories] = useState<FAQCategory[]>([]);
    const [loading, setLoading] = useState(true);
    const [savingCategory, setSavingCategory] = useState(false);
    const [savingFaq, setSavingFaq] = useState(false);
    const [editingFaq, setEditingFaq] = useState<FAQItem | null>(null);
    const [editingCategory, setEditingCategory] = useState<FAQCategory | null>(
        null,
    );
    const [editFaqForm, setEditFaqForm] = useState({
        question: "",
        answer: "",
        category_id: "",
        order: 0,
    });
    const [editCategoryForm, setEditCategoryForm] = useState({
        name: "",
        slug: "",
        description: "",
        order: 0,
    });

    useEffect(() => {
        async function load() {
            try {
                const [faqData, categoryData] = await Promise.all([
                    fetchAPI(AdminAPI.website.faqs.list(), {
                        credentials: "include",
                    }),
                    fetchAPI(AdminAPI.website.faqs.categories.list(), {
                        credentials: "include",
                    }),
                ]);
                setItems(faqData);
                setCategories(categoryData);
            } catch (error) {
                console.error(error);
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    async function handleCreateCategory(
        event: React.FormEvent<HTMLFormElement>,
    ) {
        event.preventDefault();
        setSavingCategory(true);
        const formData = new FormData(event.currentTarget);
        const payload = {
            name: formData.get("name"),
            slug: formData.get("slug"),
            description: formData.get("description"),
            order: Number(formData.get("order") || 0),
        };

        try {
            const created = await fetchAPI(
                AdminAPI.website.faqs.categories.create(),
                {
                    method: "POST",
                    credentials: "include",
                    body: JSON.stringify(payload),
                },
            );
            setCategories((prev) => [...prev, created]);
            event.currentTarget.reset();
        } catch (error) {
            console.error(error);
        } finally {
            setSavingCategory(false);
        }
    }

    async function handleCreateFaq(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setSavingFaq(true);
        const formData = new FormData(event.currentTarget);
        const payload = {
            question: formData.get("question"),
            answer: formData.get("answer"),
            category_id: Number(formData.get("category_id")),
            order: Number(formData.get("order") || 0),
        };

        try {
            const created = await fetchAPI(AdminAPI.website.faqs.create(), {
                method: "POST",
                credentials: "include",
                body: JSON.stringify(payload),
            });
            setItems((prev) => [created, ...prev]);
            event.currentTarget.reset();
        } catch (error) {
            console.error(error);
        } finally {
            setSavingFaq(false);
        }
    }

    async function handleDeleteFaq(id: number) {
        try {
            await fetchAPI(AdminAPI.website.faqs.delete(id), {
                method: "DELETE",
                credentials: "include",
            });
            setItems((prev) => prev.filter((item) => item.id !== id));
        } catch (error) {
            console.error(error);
        }
    }

    async function handleDeleteCategory(id: number) {
        try {
            await fetchAPI(AdminAPI.website.faqs.categories.delete(id), {
                method: "DELETE",
                credentials: "include",
            });
            setCategories((prev) =>
                prev.filter((category) => category.id !== id),
            );
        } catch (error) {
            console.error(error);
        }
    }

    async function handleUpdateCategory(
        event: React.FormEvent<HTMLFormElement>,
    ) {
        event.preventDefault();
        if (!editingCategory) {
            return;
        }
        setSavingCategory(true);
        const payload = {
            name: editCategoryForm.name,
            slug: editCategoryForm.slug,
            description: editCategoryForm.description,
            order: editCategoryForm.order,
        };

        try {
            const updated = await fetchAPI(
                AdminAPI.website.faqs.categories.update(editingCategory.id),
                {
                    method: "PUT",
                    credentials: "include",
                    body: JSON.stringify(payload),
                },
            );
            setCategories((prev) =>
                prev.map((category) =>
                    category.id === editingCategory.id ? updated : category,
                ),
            );
            setEditingCategory(null);
        } catch (error) {
            console.error(error);
        } finally {
            setSavingCategory(false);
        }
    }

    async function handleUpdateFaq(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!editingFaq) {
            return;
        }
        setSavingFaq(true);
        const payload = {
            question: editFaqForm.question,
            answer: editFaqForm.answer,
            category_id: Number(editFaqForm.category_id),
            order: editFaqForm.order,
        };

        try {
            const updated = await fetchAPI(
                AdminAPI.website.faqs.update(editingFaq.id),
                {
                    method: "PUT",
                    credentials: "include",
                    body: JSON.stringify(payload),
                },
            );
            setItems((prev) =>
                prev.map((item) =>
                    item.id === editingFaq.id ? updated : item,
                ),
            );
            setEditingFaq(null);
        } catch (error) {
            console.error(error);
        } finally {
            setSavingFaq(false);
        }
    }

    return (
        <Container className="py-10">
            <PageHeader
                title="FAQs"
                description="Manage FAQ items and categories."
                actions={
                    <ButtonLink href="/admin/content">
                        Back to content
                    </ButtonLink>
                }
            />

            <div className="mt-8">
                <div className="grid gap-6 lg:grid-cols-2">
                    <Card>
                        <CardHeader>
                            <CardTitle>Create FAQ category</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form
                                onSubmit={handleCreateCategory}
                                className="space-y-4"
                            >
                                <div className="grid gap-4 md:grid-cols-2">
                                    <Input
                                        name="name"
                                        placeholder="Category name"
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
                                    rows={3}
                                    placeholder="Description"
                                />
                                <Input
                                    name="order"
                                    type="number"
                                    placeholder="Order"
                                    defaultValue={0}
                                />
                                <Button type="submit" disabled={savingCategory}>
                                    {savingCategory
                                        ? "Creating..."
                                        : "Create category"}
                                </Button>
                            </form>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader>
                            <CardTitle>Create FAQ</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form
                                onSubmit={handleCreateFaq}
                                className="space-y-4"
                            >
                                <Input
                                    name="question"
                                    placeholder="Question"
                                    required
                                />
                                <Textarea
                                    name="answer"
                                    rows={4}
                                    placeholder="Answer"
                                    required
                                />
                                <Select name="category_id" required>
                                    <option value="">Select category</option>
                                    {categories.map((category) => (
                                        <option
                                            key={category.id}
                                            value={category.id}
                                        >
                                            {category.name}
                                        </option>
                                    ))}
                                </Select>
                                <Input
                                    name="order"
                                    type="number"
                                    placeholder="Order"
                                    defaultValue={0}
                                />
                                <Button type="submit" disabled={savingFaq}>
                                    {savingFaq ? "Creating..." : "Create FAQ"}
                                </Button>
                            </form>
                        </CardContent>
                    </Card>
                </div>

                <div className="mt-8">
                    <h3 className="text-adb-navy dark:text-adb-navy-100 mb-3 text-lg font-semibold">
                        Categories
                    </h3>
                    {categories.length === 0 ? (
                        <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                            No categories yet.
                        </p>
                    ) : (
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableHeaderCell>Name</TableHeaderCell>
                                    <TableHeaderCell>Actions</TableHeaderCell>
                                </TableRow>
                            </TableHead>
                            <tbody>
                                {categories.map((category) => (
                                    <TableRow key={category.id}>
                                        <TableCell>{category.name}</TableCell>
                                        <TableCell>
                                            <div className="flex gap-2">
                                                <Button
                                                    type="button"
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => {
                                                        setEditingCategory(
                                                            category,
                                                        );
                                                        setEditCategoryForm({
                                                            name: category.name,
                                                            slug:
                                                                category.slug ||
                                                                "",
                                                            description:
                                                                category.description ||
                                                                "",
                                                            order:
                                                                category.order ??
                                                                0,
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
                                                        handleDeleteCategory(
                                                            category.id,
                                                        )
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

                {editingCategory ? (
                    <Card className="mt-6">
                        <CardHeader>
                            <CardTitle>Edit category</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form
                                onSubmit={handleUpdateCategory}
                                className="space-y-4"
                            >
                                <div className="grid gap-4 md:grid-cols-2">
                                    <Input
                                        value={editCategoryForm.name}
                                        onChange={(event) =>
                                            setEditCategoryForm((prev) => ({
                                                ...prev,
                                                name: event.target.value,
                                            }))
                                        }
                                        placeholder="Category name"
                                        required
                                    />
                                    <Input
                                        value={editCategoryForm.slug}
                                        onChange={(event) =>
                                            setEditCategoryForm((prev) => ({
                                                ...prev,
                                                slug: event.target.value,
                                            }))
                                        }
                                        placeholder="Slug"
                                        required
                                    />
                                </div>
                                <Textarea
                                    value={editCategoryForm.description}
                                    onChange={(event) =>
                                        setEditCategoryForm((prev) => ({
                                            ...prev,
                                            description: event.target.value,
                                        }))
                                    }
                                    rows={3}
                                    placeholder="Description"
                                />
                                <Input
                                    type="number"
                                    value={editCategoryForm.order}
                                    onChange={(event) =>
                                        setEditCategoryForm((prev) => ({
                                            ...prev,
                                            order: Number(event.target.value),
                                        }))
                                    }
                                    placeholder="Order"
                                />
                                <div className="flex gap-3">
                                    <Button
                                        type="submit"
                                        disabled={savingCategory}
                                    >
                                        {savingCategory
                                            ? "Updating..."
                                            : "Update category"}
                                    </Button>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        onClick={() => setEditingCategory(null)}
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
                        title="No FAQs yet"
                        description="Create FAQs to answer common questions on the marketing site."
                    />
                ) : (
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableHeaderCell>Question</TableHeaderCell>
                                <TableHeaderCell>Category</TableHeaderCell>
                                <TableHeaderCell>Order</TableHeaderCell>
                                <TableHeaderCell>Actions</TableHeaderCell>
                            </TableRow>
                        </TableHead>
                        <tbody>
                            {items.map((item) => (
                                <TableRow key={item.id}>
                                    <TableCell>{item.question}</TableCell>
                                    <TableCell>
                                        {item.category?.name || "—"}
                                    </TableCell>
                                    <TableCell>{item.order}</TableCell>
                                    <TableCell>
                                        <div className="flex gap-2">
                                            <Button
                                                type="button"
                                                variant="outline"
                                                size="sm"
                                                onClick={() => {
                                                    setEditingFaq(item);
                                                    setEditFaqForm({
                                                        question: item.question,
                                                        answer: item.answer,
                                                        category_id: String(
                                                            item.category?.id ||
                                                                "",
                                                        ),
                                                        order: item.order,
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
                                                    handleDeleteFaq(item.id)
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

                {editingFaq ? (
                    <Card className="mt-6">
                        <CardHeader>
                            <CardTitle>Edit FAQ</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form
                                onSubmit={handleUpdateFaq}
                                className="space-y-4"
                            >
                                <Input
                                    value={editFaqForm.question}
                                    onChange={(event) =>
                                        setEditFaqForm((prev) => ({
                                            ...prev,
                                            question: event.target.value,
                                        }))
                                    }
                                    placeholder="Question"
                                    required
                                />
                                <Textarea
                                    value={editFaqForm.answer}
                                    onChange={(event) =>
                                        setEditFaqForm((prev) => ({
                                            ...prev,
                                            answer: event.target.value,
                                        }))
                                    }
                                    rows={4}
                                    placeholder="Answer"
                                    required
                                />
                                <Select
                                    value={editFaqForm.category_id}
                                    onChange={(event) =>
                                        setEditFaqForm((prev) => ({
                                            ...prev,
                                            category_id: event.target.value,
                                        }))
                                    }
                                    required
                                >
                                    <option value="">Select category</option>
                                    {categories.map((category) => (
                                        <option
                                            key={category.id}
                                            value={category.id}
                                        >
                                            {category.name}
                                        </option>
                                    ))}
                                </Select>
                                <Input
                                    type="number"
                                    value={editFaqForm.order}
                                    onChange={(event) =>
                                        setEditFaqForm((prev) => ({
                                            ...prev,
                                            order: Number(event.target.value),
                                        }))
                                    }
                                    placeholder="Order"
                                />
                                <div className="flex gap-3">
                                    <Button type="submit" disabled={savingFaq}>
                                        {savingFaq
                                            ? "Updating..."
                                            : "Update FAQ"}
                                    </Button>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        onClick={() => setEditingFaq(null)}
                                    >
                                        Cancel
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                ) : null}
            </div>
        </Container>
    );
}
