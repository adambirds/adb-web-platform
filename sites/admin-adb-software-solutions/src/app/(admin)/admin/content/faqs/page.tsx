"use client";

import { BrandSelector, type BrandOption } from "@/components/content/BrandSelector";
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
import { useEffect, useMemo, useState } from "react";

interface FAQCategory {
    id: number;
    name: string;
    slug: string;
    description: string;
    order: number;
    brand_slugs: string[];
}

interface FAQItem {
    id: number;
    question: string;
    answer: string;
    category: FAQCategory;
    order: number;
    brand_slugs: string[];
}

interface CategoryForm {
    name: string;
    slug: string;
    description: string;
    order: number;
    brand_ids: number[];
}

interface FAQForm {
    question: string;
    answer: string;
    category_id: string;
    order: number;
    brand_ids: number[];
}

const EMPTY_CATEGORY: CategoryForm = {
    name: "",
    slug: "",
    description: "",
    order: 0,
    brand_ids: [],
};

const EMPTY_FAQ: FAQForm = {
    question: "",
    answer: "",
    category_id: "",
    order: 0,
    brand_ids: [],
};

export default function AdminFAQsPage() {
    const [items, setItems] = useState<FAQItem[]>([]);
    const [categories, setCategories] = useState<FAQCategory[]>([]);
    const [brands, setBrands] = useState<BrandOption[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [brandFilter, setBrandFilter] = useState("all");
    const [createCategory, setCreateCategory] = useState<CategoryForm>(EMPTY_CATEGORY);
    const [createFaq, setCreateFaq] = useState<FAQForm>(EMPTY_FAQ);
    const [editingCategory, setEditingCategory] = useState<FAQCategory | null>(null);
    const [editingCategoryForm, setEditingCategoryForm] = useState<CategoryForm>(EMPTY_CATEGORY);
    const [editingFaq, setEditingFaq] = useState<FAQItem | null>(null);
    const [editingFaqForm, setEditingFaqForm] = useState<FAQForm>(EMPTY_FAQ);

    useEffect(() => {
        async function load() {
            try {
                const [faqData, categoryData, brandData] = await Promise.all([
                    fetchAPI(AdminAPI.website.faqs.list(), { credentials: "include" }),
                    fetchAPI(AdminAPI.website.faqs.categories.list(), { credentials: "include" }),
                    fetchAPI(AdminAPI.brands.list(), { credentials: "include" }),
                ]);
                setItems(faqData as FAQItem[]);
                setCategories(categoryData as FAQCategory[]);
                setBrands(brandData as BrandOption[]);
            } catch (error) {
                console.error(error);
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
                : items.filter((item) => item.brand_slugs.includes(brandFilter)),
        [brandFilter, items],
    );

    const visibleCategories = useMemo(
        () =>
            brandFilter === "all"
                ? categories
                : categories.filter((category) => category.brand_slugs.includes(brandFilter)),
        [brandFilter, categories],
    );

    async function saveCategory(event: React.FormEvent<HTMLFormElement>, editing = false) {
        event.preventDefault();
        const form = editing ? editingCategoryForm : createCategory;
        if (form.brand_ids.length === 0 || (editing && !editingCategory)) return;
        setSaving(true);
        try {
            const category = (await fetchAPI(
                editing
                    ? AdminAPI.website.faqs.categories.update(editingCategory!.id)
                    : AdminAPI.website.faqs.categories.create(),
                {
                    method: editing ? "PUT" : "POST",
                    credentials: "include",
                    body: JSON.stringify(form),
                },
            )) as FAQCategory;
            setCategories((current) =>
                editing
                    ? current.map((item) => (item.id === category.id ? category : item))
                    : [...current, category],
            );
            if (editing) setEditingCategory(null);
            else setCreateCategory(EMPTY_CATEGORY);
        } catch (error) {
            console.error(error);
        } finally {
            setSaving(false);
        }
    }

    async function saveFaq(event: React.FormEvent<HTMLFormElement>, editing = false) {
        event.preventDefault();
        const form = editing ? editingFaqForm : createFaq;
        if (form.brand_ids.length === 0 || !form.category_id || (editing && !editingFaq)) return;
        setSaving(true);
        try {
            const payload = { ...form, category_id: Number(form.category_id) };
            const faq = (await fetchAPI(
                editing
                    ? AdminAPI.website.faqs.update(editingFaq!.id)
                    : AdminAPI.website.faqs.create(),
                {
                    method: editing ? "PUT" : "POST",
                    credentials: "include",
                    body: JSON.stringify(payload),
                },
            )) as FAQItem;
            setItems((current) =>
                editing
                    ? current.map((item) => (item.id === faq.id ? faq : item))
                    : [faq, ...current],
            );
            if (editing) setEditingFaq(null);
            else setCreateFaq(EMPTY_FAQ);
        } catch (error) {
            console.error(error);
        } finally {
            setSaving(false);
        }
    }

    async function removeFaq(id: number) {
        await fetchAPI(AdminAPI.website.faqs.delete(id), { method: "DELETE", credentials: "include" });
        setItems((current) => current.filter((item) => item.id !== id));
    }

    async function removeCategory(id: number) {
        await fetchAPI(AdminAPI.website.faqs.categories.delete(id), { method: "DELETE", credentials: "include" });
        setCategories((current) => current.filter((item) => item.id !== id));
    }

    function idsFor(slugs: string[]) {
        return slugs
            .map((slug) => brandIdBySlug.get(slug))
            .filter((id): id is number => id !== undefined);
    }

    function startCategoryEdit(category: FAQCategory) {
        setEditingCategory(category);
        setEditingCategoryForm({
            name: category.name,
            slug: category.slug,
            description: category.description,
            order: category.order,
            brand_ids: idsFor(category.brand_slugs),
        });
    }

    function startFaqEdit(faq: FAQItem) {
        setEditingFaq(faq);
        setEditingFaqForm({
            question: faq.question,
            answer: faq.answer,
            category_id: String(faq.category.id),
            order: faq.order,
            brand_ids: idsFor(faq.brand_slugs),
        });
    }

    return (
        <Container className="py-10">
            <PageHeader
                title="FAQs"
                description="Manage brand-aware FAQ categories and questions."
                actions={<ButtonLink href="/admin/content">Back to content</ButtonLink>}
            />

            <div className="mt-8 space-y-8">
                <div className="flex items-center gap-3">
                    <label htmlFor="faq-brand-filter" className="text-sm font-medium">Brand</label>
                    <select
                        id="faq-brand-filter"
                        value={brandFilter}
                        onChange={(event) => setBrandFilter(event.target.value)}
                        className="border-adb-navy-200 dark:border-adb-navy-700 rounded-md border bg-transparent px-3 py-2 text-sm"
                    >
                        <option value="all">All brands</option>
                        {brands.filter((brand) => brand.is_active).map((brand) => (
                            <option key={brand.id} value={brand.slug}>{brand.name}</option>
                        ))}
                    </select>
                </div>

                <div className="grid gap-6 lg:grid-cols-2">
                    <Card>
                        <CardHeader><CardTitle>Create FAQ category</CardTitle></CardHeader>
                        <CardContent>
                            <form onSubmit={(event) => void saveCategory(event)} className="space-y-4">
                                <Input value={createCategory.name} onChange={(event) => setCreateCategory((form) => ({ ...form, name: event.target.value }))} placeholder="Category name" required />
                                <Input value={createCategory.slug} onChange={(event) => setCreateCategory((form) => ({ ...form, slug: event.target.value }))} placeholder="Slug" required />
                                <Textarea value={createCategory.description} onChange={(event) => setCreateCategory((form) => ({ ...form, description: event.target.value }))} rows={3} placeholder="Description" />
                                <Input type="number" value={createCategory.order} onChange={(event) => setCreateCategory((form) => ({ ...form, order: Number(event.target.value) }))} />
                                <BrandSelector selectedIds={createCategory.brand_ids} onChange={(brand_ids) => setCreateCategory((form) => ({ ...form, brand_ids }))} disabled={saving} />
                                <Button type="submit" disabled={saving || createCategory.brand_ids.length === 0}>Create category</Button>
                            </form>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader><CardTitle>Create FAQ</CardTitle></CardHeader>
                        <CardContent>
                            <form onSubmit={(event) => void saveFaq(event)} className="space-y-4">
                                <Input value={createFaq.question} onChange={(event) => setCreateFaq((form) => ({ ...form, question: event.target.value }))} placeholder="Question" required />
                                <Textarea value={createFaq.answer} onChange={(event) => setCreateFaq((form) => ({ ...form, answer: event.target.value }))} rows={4} placeholder="Answer" required />
                                <Select value={createFaq.category_id} onChange={(event) => setCreateFaq((form) => ({ ...form, category_id: event.target.value }))} required>
                                    <option value="">Select category</option>
                                    {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
                                </Select>
                                <Input type="number" value={createFaq.order} onChange={(event) => setCreateFaq((form) => ({ ...form, order: Number(event.target.value) }))} />
                                <BrandSelector selectedIds={createFaq.brand_ids} onChange={(brand_ids) => setCreateFaq((form) => ({ ...form, brand_ids }))} disabled={saving} />
                                <Button type="submit" disabled={saving || createFaq.brand_ids.length === 0 || !createFaq.category_id}>Create FAQ</Button>
                            </form>
                        </CardContent>
                    </Card>
                </div>

                {editingCategory ? (
                    <Card>
                        <CardHeader><CardTitle>Edit FAQ category</CardTitle></CardHeader>
                        <CardContent>
                            <form onSubmit={(event) => void saveCategory(event, true)} className="space-y-4">
                                <Input value={editingCategoryForm.name} onChange={(event) => setEditingCategoryForm((form) => ({ ...form, name: event.target.value }))} required />
                                <Input value={editingCategoryForm.slug} onChange={(event) => setEditingCategoryForm((form) => ({ ...form, slug: event.target.value }))} required />
                                <Textarea value={editingCategoryForm.description} onChange={(event) => setEditingCategoryForm((form) => ({ ...form, description: event.target.value }))} rows={3} />
                                <Input type="number" value={editingCategoryForm.order} onChange={(event) => setEditingCategoryForm((form) => ({ ...form, order: Number(event.target.value) }))} />
                                <BrandSelector selectedIds={editingCategoryForm.brand_ids} onChange={(brand_ids) => setEditingCategoryForm((form) => ({ ...form, brand_ids }))} disabled={saving} />
                                <div className="flex gap-3"><Button type="submit" disabled={saving || editingCategoryForm.brand_ids.length === 0}>Update category</Button><Button type="button" variant="outline" onClick={() => setEditingCategory(null)}>Cancel</Button></div>
                            </form>
                        </CardContent>
                    </Card>
                ) : null}

                {editingFaq ? (
                    <Card>
                        <CardHeader><CardTitle>Edit FAQ</CardTitle></CardHeader>
                        <CardContent>
                            <form onSubmit={(event) => void saveFaq(event, true)} className="space-y-4">
                                <Input value={editingFaqForm.question} onChange={(event) => setEditingFaqForm((form) => ({ ...form, question: event.target.value }))} required />
                                <Textarea value={editingFaqForm.answer} onChange={(event) => setEditingFaqForm((form) => ({ ...form, answer: event.target.value }))} rows={4} required />
                                <Select value={editingFaqForm.category_id} onChange={(event) => setEditingFaqForm((form) => ({ ...form, category_id: event.target.value }))} required>
                                    <option value="">Select category</option>
                                    {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
                                </Select>
                                <Input type="number" value={editingFaqForm.order} onChange={(event) => setEditingFaqForm((form) => ({ ...form, order: Number(event.target.value) }))} />
                                <BrandSelector selectedIds={editingFaqForm.brand_ids} onChange={(brand_ids) => setEditingFaqForm((form) => ({ ...form, brand_ids }))} disabled={saving} />
                                <div className="flex gap-3"><Button type="submit" disabled={saving || editingFaqForm.brand_ids.length === 0}>Update FAQ</Button><Button type="button" variant="outline" onClick={() => setEditingFaq(null)}>Cancel</Button></div>
                            </form>
                        </CardContent>
                    </Card>
                ) : null}

                <div>
                    <h3 className="text-adb-navy dark:text-adb-navy-100 mb-3 text-lg font-semibold">Categories</h3>
                    {visibleCategories.length === 0 ? <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">No categories found.</p> : (
                        <Table>
                            <TableHead><TableRow><TableHeaderCell>Name</TableHeaderCell><TableHeaderCell>Brands</TableHeaderCell><TableHeaderCell>Actions</TableHeaderCell></TableRow></TableHead>
                            <tbody>{visibleCategories.map((category) => (
                                <TableRow key={category.id}><TableCell>{category.name}</TableCell><TableCell>{category.brand_slugs.join(", ") || "—"}</TableCell><TableCell><div className="flex gap-2"><Button type="button" variant="outline" size="sm" onClick={() => startCategoryEdit(category)}>Edit</Button><Button type="button" variant="destructive" size="sm" onClick={() => void removeCategory(category.id)}>Delete</Button></div></TableCell></TableRow>
                            ))}</tbody>
                        </Table>
                    )}
                </div>

                {loading ? <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">Loading...</p> : visibleItems.length === 0 ? (
                    <EmptyState title="No FAQs found" description="Create an FAQ or change the selected brand filter." />
                ) : (
                    <Table>
                        <TableHead><TableRow><TableHeaderCell>Question</TableHeaderCell><TableHeaderCell>Category</TableHeaderCell><TableHeaderCell>Brands</TableHeaderCell><TableHeaderCell>Order</TableHeaderCell><TableHeaderCell>Actions</TableHeaderCell></TableRow></TableHead>
                        <tbody>{visibleItems.map((item) => (
                            <TableRow key={item.id}><TableCell>{item.question}</TableCell><TableCell>{item.category.name}</TableCell><TableCell>{item.brand_slugs.join(", ") || "—"}</TableCell><TableCell>{item.order}</TableCell><TableCell><div className="flex gap-2"><Button type="button" variant="outline" size="sm" onClick={() => startFaqEdit(item)}>Edit</Button><Button type="button" variant="destructive" size="sm" onClick={() => void removeFaq(item.id)}>Delete</Button></div></TableCell></TableRow>
                        ))}</tbody>
                    </Table>
                )}
            </div>
        </Container>
    );
}
