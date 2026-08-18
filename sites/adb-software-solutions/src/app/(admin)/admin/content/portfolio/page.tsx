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

interface PortfolioItem {
    id: number;
    title: string;
    slug: string;
    description: string;
    challenge: string;
    solution: string;
    results: string;
    technologies: string[];
    project_url: string | null;
    github_url: string | null;
    featured: boolean;
    brand_slugs: string[];
}

interface PortfolioForm {
    title: string;
    slug: string;
    description: string;
    challenge: string;
    solution: string;
    results: string;
    technologies: string;
    project_url: string;
    github_url: string;
    featured: boolean;
    brand_ids: number[];
}

const EMPTY_FORM: PortfolioForm = {
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
    brand_ids: [],
};

export default function AdminPortfolioPage() {
    const [items, setItems] = useState<PortfolioItem[]>([]);
    const [brands, setBrands] = useState<BrandOption[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [editing, setEditing] = useState<PortfolioItem | null>(null);
    const [createForm, setCreateForm] = useState<PortfolioForm>(EMPTY_FORM);
    const [editForm, setEditForm] = useState<PortfolioForm>(EMPTY_FORM);
    const [brandFilter, setBrandFilter] = useState("all");

    useEffect(() => {
        async function load() {
            try {
                const [portfolioData, brandData] = await Promise.all([
                    fetchAPI(AdminAPI.website.portfolio.list(), { credentials: "include" }),
                    fetchAPI(AdminAPI.brands.list(), { credentials: "include" }),
                ]);
                setItems(portfolioData as PortfolioItem[]);
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

    function payload(form: PortfolioForm) {
        return {
            ...form,
            technologies: form.technologies.split(",").map((item) => item.trim()).filter(Boolean),
            project_url: form.project_url || null,
            github_url: form.github_url || null,
        };
    }

    async function save(event: React.FormEvent<HTMLFormElement>, isEditing = false) {
        event.preventDefault();
        const form = isEditing ? editForm : createForm;
        if (form.brand_ids.length === 0 || (isEditing && !editing)) return;
        setSaving(true);
        try {
            const item = (await fetchAPI(
                isEditing ? AdminAPI.website.portfolio.update(editing!.id) : AdminAPI.website.portfolio.create(),
                {
                    method: isEditing ? "PUT" : "POST",
                    credentials: "include",
                    body: JSON.stringify(payload(form)),
                },
            )) as PortfolioItem;
            setItems((current) =>
                isEditing
                    ? current.map((existing) => (existing.id === item.id ? item : existing))
                    : [item, ...current],
            );
            if (isEditing) setEditing(null);
            else setCreateForm(EMPTY_FORM);
        } catch (error) {
            console.error(error);
        } finally {
            setSaving(false);
        }
    }

    async function remove(id: number) {
        try {
            await fetchAPI(AdminAPI.website.portfolio.delete(id), { method: "DELETE", credentials: "include" });
            setItems((current) => current.filter((item) => item.id !== id));
        } catch (error) {
            console.error(error);
        }
    }

    function beginEdit(item: PortfolioItem) {
        setEditing(item);
        setEditForm({
            title: item.title,
            slug: item.slug,
            description: item.description,
            challenge: item.challenge,
            solution: item.solution,
            results: item.results,
            technologies: item.technologies.join(", "),
            project_url: item.project_url ?? "",
            github_url: item.github_url ?? "",
            featured: item.featured,
            brand_ids: item.brand_slugs
                .map((slug) => brandIdBySlug.get(slug))
                .filter((id): id is number => id !== undefined),
        });
    }

    function fields(form: PortfolioForm, setForm: React.Dispatch<React.SetStateAction<PortfolioForm>>) {
        return (
            <>
                <div className="grid gap-4 md:grid-cols-2">
                    <Input value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} placeholder="Title" required />
                    <Input value={form.slug} onChange={(event) => setForm((current) => ({ ...current, slug: event.target.value }))} placeholder="Slug" required />
                </div>
                <Textarea value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} rows={3} placeholder="Short description" required />
                <Textarea value={form.challenge} onChange={(event) => setForm((current) => ({ ...current, challenge: event.target.value }))} rows={3} placeholder="Challenge" required />
                <Textarea value={form.solution} onChange={(event) => setForm((current) => ({ ...current, solution: event.target.value }))} rows={3} placeholder="Solution" required />
                <Textarea value={form.results} onChange={(event) => setForm((current) => ({ ...current, results: event.target.value }))} rows={3} placeholder="Results" required />
                <Input value={form.technologies} onChange={(event) => setForm((current) => ({ ...current, technologies: event.target.value }))} placeholder="Technologies (comma separated)" required />
                <div className="grid gap-4 md:grid-cols-2">
                    <Input value={form.project_url} onChange={(event) => setForm((current) => ({ ...current, project_url: event.target.value }))} placeholder="Project URL" />
                    <Input value={form.github_url} onChange={(event) => setForm((current) => ({ ...current, github_url: event.target.value }))} placeholder="GitHub URL" />
                </div>
                <BrandSelector selectedIds={form.brand_ids} onChange={(brand_ids) => setForm((current) => ({ ...current, brand_ids }))} disabled={saving} />
                <label className="text-adb-navy-600 dark:text-adb-navy-300 flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={form.featured} onChange={(event) => setForm((current) => ({ ...current, featured: event.target.checked }))} /> Featured
                </label>
            </>
        );
    }

    return (
        <Container className="py-10">
            <PageHeader title="Portfolio" description="Manage brand-aware public case studies and featured work." actions={<ButtonLink href="/admin/content">Back to content</ButtonLink>} />
            <div className="mt-8 space-y-6">
                <Card>
                    <CardHeader><CardTitle>Create portfolio item</CardTitle></CardHeader>
                    <CardContent>
                        <form onSubmit={(event) => void save(event)} className="space-y-4">
                            {fields(createForm, setCreateForm)}
                            <Button type="submit" disabled={saving || createForm.brand_ids.length === 0}>Create item</Button>
                        </form>
                    </CardContent>
                </Card>

                {editing ? (
                    <Card>
                        <CardHeader><CardTitle>Edit portfolio item</CardTitle></CardHeader>
                        <CardContent>
                            <form onSubmit={(event) => void save(event, true)} className="space-y-4">
                                {fields(editForm, setEditForm)}
                                <div className="flex gap-3"><Button type="submit" disabled={saving || editForm.brand_ids.length === 0}>Update item</Button><Button type="button" variant="outline" onClick={() => setEditing(null)}>Cancel</Button></div>
                            </form>
                        </CardContent>
                    </Card>
                ) : null}

                <div className="flex items-center gap-3">
                    <label htmlFor="portfolio-brand-filter" className="text-sm font-medium">Brand</label>
                    <select id="portfolio-brand-filter" value={brandFilter} onChange={(event) => setBrandFilter(event.target.value)} className="border-adb-navy-200 dark:border-adb-navy-700 rounded-md border bg-transparent px-3 py-2 text-sm">
                        <option value="all">All brands</option>
                        {brands.filter((brand) => brand.is_active).map((brand) => <option key={brand.id} value={brand.slug}>{brand.name}</option>)}
                    </select>
                </div>

                {loading ? <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">Loading...</p> : visibleItems.length === 0 ? (
                    <EmptyState title="No portfolio items found" description="Create a case study or change the selected brand filter." />
                ) : (
                    <Table>
                        <TableHead><TableRow><TableHeaderCell>Title</TableHeaderCell><TableHeaderCell>Slug</TableHeaderCell><TableHeaderCell>Brands</TableHeaderCell><TableHeaderCell>Featured</TableHeaderCell><TableHeaderCell>Actions</TableHeaderCell></TableRow></TableHead>
                        <tbody>{visibleItems.map((item) => (
                            <TableRow key={item.id}><TableCell>{item.title}</TableCell><TableCell>{item.slug}</TableCell><TableCell>{item.brand_slugs.join(", ") || "—"}</TableCell><TableCell>{item.featured ? "Yes" : "No"}</TableCell><TableCell><div className="flex gap-2"><Button type="button" variant="outline" size="sm" onClick={() => beginEdit(item)}>Edit</Button><Button type="button" variant="destructive" size="sm" onClick={() => void remove(item.id)}>Delete</Button></div></TableCell></TableRow>
                        ))}</tbody>
                    </Table>
                )}
            </div>
        </Container>
    );
}
