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

interface BlogCategoryItem {
    id: number;
    name: string;
    slug: string;
    description: string;
    brand_slugs: string[];
}

interface BlogTagItem {
    id: number;
    name: string;
    slug: string;
    brand_slugs: string[];
}

interface BlogPostItem {
    id: number;
    title: string;
    slug: string;
    excerpt: string;
    content: string;
    author: string;
    published: boolean;
    featured: boolean;
    categories: BlogCategoryItem[];
    tags: BlogTagItem[];
    brand_slugs: string[];
    meta_description: string;
    meta_keywords: string;
}

interface CategoryForm {
    name: string;
    slug: string;
    description: string;
    brand_ids: number[];
}

interface TagForm {
    name: string;
    slug: string;
    brand_ids: number[];
}

interface PostForm {
    title: string;
    slug: string;
    excerpt: string;
    content: string;
    author: string;
    published: boolean;
    featured: boolean;
    category_ids: number[];
    tag_ids: number[];
    brand_ids: number[];
    meta_description: string;
    meta_keywords: string;
}

const EMPTY_CATEGORY: CategoryForm = { name: "", slug: "", description: "", brand_ids: [] };
const EMPTY_TAG: TagForm = { name: "", slug: "", brand_ids: [] };
const EMPTY_POST: PostForm = {
    title: "",
    slug: "",
    excerpt: "",
    content: "",
    author: "",
    published: false,
    featured: false,
    category_ids: [],
    tag_ids: [],
    brand_ids: [],
    meta_description: "",
    meta_keywords: "",
};

function toggle(values: number[], id: number) {
    return values.includes(id) ? values.filter((value) => value !== id) : [...values, id];
}

export default function AdminBlogPage() {
    const [posts, setPosts] = useState<BlogPostItem[]>([]);
    const [categories, setCategories] = useState<BlogCategoryItem[]>([]);
    const [tags, setTags] = useState<BlogTagItem[]>([]);
    const [brands, setBrands] = useState<BrandOption[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [brandFilter, setBrandFilter] = useState("all");
    const [createCategory, setCreateCategory] = useState<CategoryForm>(EMPTY_CATEGORY);
    const [createTag, setCreateTag] = useState<TagForm>(EMPTY_TAG);
    const [createPost, setCreatePost] = useState<PostForm>(EMPTY_POST);
    const [editingCategory, setEditingCategory] = useState<BlogCategoryItem | null>(null);
    const [editingCategoryForm, setEditingCategoryForm] = useState<CategoryForm>(EMPTY_CATEGORY);
    const [editingTag, setEditingTag] = useState<BlogTagItem | null>(null);
    const [editingTagForm, setEditingTagForm] = useState<TagForm>(EMPTY_TAG);
    const [editingPost, setEditingPost] = useState<BlogPostItem | null>(null);
    const [editingPostForm, setEditingPostForm] = useState<PostForm>(EMPTY_POST);

    useEffect(() => {
        async function load() {
            try {
                const [postData, categoryData, tagData, brandData] = await Promise.all([
                    fetchAPI(AdminAPI.website.blog.posts.list(), { credentials: "include" }),
                    fetchAPI(AdminAPI.website.blog.categories.list(), { credentials: "include" }),
                    fetchAPI(AdminAPI.website.blog.tags.list(), { credentials: "include" }),
                    fetchAPI(AdminAPI.brands.list(), { credentials: "include" }),
                ]);
                setPosts(postData as BlogPostItem[]);
                setCategories(categoryData as BlogCategoryItem[]);
                setTags(tagData as BlogTagItem[]);
                setBrands(brandData as BrandOption[]);
            } catch (error) {
                console.error(error);
            } finally {
                setLoading(false);
            }
        }
        void load();
    }, []);

    const brandIdBySlug = useMemo(() => new Map(brands.map((brand) => [brand.slug, brand.id])), [brands]);
    const idsFor = (slugs: string[]) => slugs.map((slug) => brandIdBySlug.get(slug)).filter((id): id is number => id !== undefined);

    const visiblePosts = useMemo(
        () => brandFilter === "all" ? posts : posts.filter((post) => post.brand_slugs.includes(brandFilter)),
        [brandFilter, posts],
    );
    const visibleCategories = useMemo(
        () => brandFilter === "all" ? categories : categories.filter((category) => category.brand_slugs.includes(brandFilter)),
        [brandFilter, categories],
    );
    const visibleTags = useMemo(
        () => brandFilter === "all" ? tags : tags.filter((tag) => tag.brand_slugs.includes(brandFilter)),
        [brandFilter, tags],
    );

    async function saveCategory(event: React.FormEvent<HTMLFormElement>, editing = false) {
        event.preventDefault();
        const form = editing ? editingCategoryForm : createCategory;
        if (form.brand_ids.length === 0 || (editing && !editingCategory)) return;
        setSaving(true);
        try {
            const item = (await fetchAPI(
                editing ? AdminAPI.website.blog.categories.update(editingCategory!.id) : AdminAPI.website.blog.categories.create(),
                { method: editing ? "PUT" : "POST", credentials: "include", body: JSON.stringify(form) },
            )) as BlogCategoryItem;
            setCategories((current) => editing ? current.map((value) => value.id === item.id ? item : value) : [...current, item]);
            if (editing) setEditingCategory(null); else setCreateCategory(EMPTY_CATEGORY);
        } catch (error) { console.error(error); } finally { setSaving(false); }
    }

    async function saveTag(event: React.FormEvent<HTMLFormElement>, editing = false) {
        event.preventDefault();
        const form = editing ? editingTagForm : createTag;
        if (form.brand_ids.length === 0 || (editing && !editingTag)) return;
        setSaving(true);
        try {
            const item = (await fetchAPI(
                editing ? AdminAPI.website.blog.tags.update(editingTag!.id) : AdminAPI.website.blog.tags.create(),
                { method: editing ? "PUT" : "POST", credentials: "include", body: JSON.stringify(form) },
            )) as BlogTagItem;
            setTags((current) => editing ? current.map((value) => value.id === item.id ? item : value) : [...current, item]);
            if (editing) setEditingTag(null); else setCreateTag(EMPTY_TAG);
        } catch (error) { console.error(error); } finally { setSaving(false); }
    }

    async function savePost(event: React.FormEvent<HTMLFormElement>, editing = false) {
        event.preventDefault();
        const form = editing ? editingPostForm : createPost;
        if (form.brand_ids.length === 0 || (editing && !editingPost)) return;
        setSaving(true);
        try {
            const item = (await fetchAPI(
                editing ? AdminAPI.website.blog.posts.update(editingPost!.id) : AdminAPI.website.blog.posts.create(),
                { method: editing ? "PUT" : "POST", credentials: "include", body: JSON.stringify(form) },
            )) as BlogPostItem;
            setPosts((current) => editing ? current.map((value) => value.id === item.id ? item : value) : [item, ...current]);
            if (editing) setEditingPost(null); else setCreatePost(EMPTY_POST);
        } catch (error) { console.error(error); } finally { setSaving(false); }
    }

    async function remove(url: string, id: number, kind: "post" | "category" | "tag") {
        try {
            await fetchAPI(url, { method: "DELETE", credentials: "include" });
            if (kind === "post") setPosts((current) => current.filter((item) => item.id !== id));
            if (kind === "category") setCategories((current) => current.filter((item) => item.id !== id));
            if (kind === "tag") setTags((current) => current.filter((item) => item.id !== id));
        } catch (error) { console.error(error); }
    }

    function startPostEdit(post: BlogPostItem) {
        setEditingPost(post);
        setEditingPostForm({
            title: post.title,
            slug: post.slug,
            excerpt: post.excerpt,
            content: post.content,
            author: post.author,
            published: post.published,
            featured: post.featured,
            category_ids: post.categories.map((item) => item.id),
            tag_ids: post.tags.map((item) => item.id),
            brand_ids: idsFor(post.brand_slugs),
            meta_description: post.meta_description,
            meta_keywords: post.meta_keywords,
        });
    }

    function postFields(form: PostForm, setForm: React.Dispatch<React.SetStateAction<PostForm>>) {
        return <>
            <div className="grid gap-4 md:grid-cols-2"><Input value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} placeholder="Title" required /><Input value={form.slug} onChange={(event) => setForm((current) => ({ ...current, slug: event.target.value }))} placeholder="Slug" required /></div>
            <Textarea value={form.excerpt} onChange={(event) => setForm((current) => ({ ...current, excerpt: event.target.value }))} rows={3} placeholder="Excerpt" required />
            <Textarea value={form.content} onChange={(event) => setForm((current) => ({ ...current, content: event.target.value }))} rows={12} placeholder="Article content" required />
            <Input value={form.author} onChange={(event) => setForm((current) => ({ ...current, author: event.target.value }))} placeholder="Author (optional)" />
            <div className="grid gap-6 md:grid-cols-2">
                <fieldset className="space-y-2"><legend className="text-sm font-medium">Categories</legend>{categories.map((category) => <label key={category.id} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.category_ids.includes(category.id)} onChange={() => setForm((current) => ({ ...current, category_ids: toggle(current.category_ids, category.id) }))} />{category.name}</label>)}</fieldset>
                <fieldset className="space-y-2"><legend className="text-sm font-medium">Tags</legend>{tags.map((tag) => <label key={tag.id} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.tag_ids.includes(tag.id)} onChange={() => setForm((current) => ({ ...current, tag_ids: toggle(current.tag_ids, tag.id) }))} />{tag.name}</label>)}</fieldset>
            </div>
            <BrandSelector selectedIds={form.brand_ids} onChange={(brand_ids) => setForm((current) => ({ ...current, brand_ids }))} disabled={saving} />
            <Textarea value={form.meta_description} onChange={(event) => setForm((current) => ({ ...current, meta_description: event.target.value }))} rows={2} placeholder="Meta description" />
            <Input value={form.meta_keywords} onChange={(event) => setForm((current) => ({ ...current, meta_keywords: event.target.value }))} placeholder="Meta keywords" />
            <div className="flex gap-6"><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.published} onChange={(event) => setForm((current) => ({ ...current, published: event.target.checked }))} />Published</label><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.featured} onChange={(event) => setForm((current) => ({ ...current, featured: event.target.checked }))} />Featured</label></div>
        </>;
    }

    return (
        <Container className="py-10">
            <PageHeader title="Blog" description="Manage brand-aware blog posts, categories and tags." actions={<ButtonLink href="/admin/content">Back to content</ButtonLink>} />
            <div className="mt-8 space-y-8">
                <div className="flex items-center gap-3"><label htmlFor="blog-brand-filter" className="text-sm font-medium">Brand</label><select id="blog-brand-filter" value={brandFilter} onChange={(event) => setBrandFilter(event.target.value)} className="border-adb-navy-200 dark:border-adb-navy-700 rounded-md border bg-transparent px-3 py-2 text-sm"><option value="all">All brands</option>{brands.filter((brand) => brand.is_active).map((brand) => <option key={brand.id} value={brand.slug}>{brand.name}</option>)}</select></div>

                <div className="grid gap-6 lg:grid-cols-2">
                    <Card><CardHeader><CardTitle>Create category</CardTitle></CardHeader><CardContent><form onSubmit={(event) => void saveCategory(event)} className="space-y-4"><Input value={createCategory.name} onChange={(event) => setCreateCategory((form) => ({ ...form, name: event.target.value }))} placeholder="Name" required /><Input value={createCategory.slug} onChange={(event) => setCreateCategory((form) => ({ ...form, slug: event.target.value }))} placeholder="Slug" required /><Textarea value={createCategory.description} onChange={(event) => setCreateCategory((form) => ({ ...form, description: event.target.value }))} rows={2} placeholder="Description" /><BrandSelector selectedIds={createCategory.brand_ids} onChange={(brand_ids) => setCreateCategory((form) => ({ ...form, brand_ids }))} disabled={saving} /><Button type="submit" disabled={saving || createCategory.brand_ids.length === 0}>Create category</Button></form></CardContent></Card>
                    <Card><CardHeader><CardTitle>Create tag</CardTitle></CardHeader><CardContent><form onSubmit={(event) => void saveTag(event)} className="space-y-4"><Input value={createTag.name} onChange={(event) => setCreateTag((form) => ({ ...form, name: event.target.value }))} placeholder="Name" required /><Input value={createTag.slug} onChange={(event) => setCreateTag((form) => ({ ...form, slug: event.target.value }))} placeholder="Slug" required /><BrandSelector selectedIds={createTag.brand_ids} onChange={(brand_ids) => setCreateTag((form) => ({ ...form, brand_ids }))} disabled={saving} /><Button type="submit" disabled={saving || createTag.brand_ids.length === 0}>Create tag</Button></form></CardContent></Card>
                </div>

                <Card><CardHeader><CardTitle>Create blog post</CardTitle></CardHeader><CardContent><form onSubmit={(event) => void savePost(event)} className="space-y-4">{postFields(createPost, setCreatePost)}<Button type="submit" disabled={saving || createPost.brand_ids.length === 0}>Create post</Button></form></CardContent></Card>

                {editingCategory ? <Card><CardHeader><CardTitle>Edit category</CardTitle></CardHeader><CardContent><form onSubmit={(event) => void saveCategory(event, true)} className="space-y-4"><Input value={editingCategoryForm.name} onChange={(event) => setEditingCategoryForm((form) => ({ ...form, name: event.target.value }))} required /><Input value={editingCategoryForm.slug} onChange={(event) => setEditingCategoryForm((form) => ({ ...form, slug: event.target.value }))} required /><Textarea value={editingCategoryForm.description} onChange={(event) => setEditingCategoryForm((form) => ({ ...form, description: event.target.value }))} rows={2} /><BrandSelector selectedIds={editingCategoryForm.brand_ids} onChange={(brand_ids) => setEditingCategoryForm((form) => ({ ...form, brand_ids }))} disabled={saving} /><div className="flex gap-3"><Button type="submit" disabled={saving || editingCategoryForm.brand_ids.length === 0}>Update category</Button><Button type="button" variant="outline" onClick={() => setEditingCategory(null)}>Cancel</Button></div></form></CardContent></Card> : null}
                {editingTag ? <Card><CardHeader><CardTitle>Edit tag</CardTitle></CardHeader><CardContent><form onSubmit={(event) => void saveTag(event, true)} className="space-y-4"><Input value={editingTagForm.name} onChange={(event) => setEditingTagForm((form) => ({ ...form, name: event.target.value }))} required /><Input value={editingTagForm.slug} onChange={(event) => setEditingTagForm((form) => ({ ...form, slug: event.target.value }))} required /><BrandSelector selectedIds={editingTagForm.brand_ids} onChange={(brand_ids) => setEditingTagForm((form) => ({ ...form, brand_ids }))} disabled={saving} /><div className="flex gap-3"><Button type="submit" disabled={saving || editingTagForm.brand_ids.length === 0}>Update tag</Button><Button type="button" variant="outline" onClick={() => setEditingTag(null)}>Cancel</Button></div></form></CardContent></Card> : null}
                {editingPost ? <Card><CardHeader><CardTitle>Edit blog post</CardTitle></CardHeader><CardContent><form onSubmit={(event) => void savePost(event, true)} className="space-y-4">{postFields(editingPostForm, setEditingPostForm)}<div className="flex gap-3"><Button type="submit" disabled={saving || editingPostForm.brand_ids.length === 0}>Update post</Button><Button type="button" variant="outline" onClick={() => setEditingPost(null)}>Cancel</Button></div></form></CardContent></Card> : null}

                <div className="grid gap-6 lg:grid-cols-2">
                    <Card><CardHeader><CardTitle>Categories</CardTitle></CardHeader><CardContent>{visibleCategories.length === 0 ? <p className="text-sm">No categories found.</p> : <Table><TableHead><TableRow><TableHeaderCell>Name</TableHeaderCell><TableHeaderCell>Brands</TableHeaderCell><TableHeaderCell>Actions</TableHeaderCell></TableRow></TableHead><tbody>{visibleCategories.map((item) => <TableRow key={item.id}><TableCell>{item.name}</TableCell><TableCell>{item.brand_slugs.join(", ") || "—"}</TableCell><TableCell><div className="flex gap-2"><Button size="sm" variant="outline" onClick={() => { setEditingCategory(item); setEditingCategoryForm({ name: item.name, slug: item.slug, description: item.description, brand_ids: idsFor(item.brand_slugs) }); }}>Edit</Button><Button size="sm" variant="destructive" onClick={() => void remove(AdminAPI.website.blog.categories.delete(item.id), item.id, "category")}>Delete</Button></div></TableCell></TableRow>)}</tbody></Table>}</CardContent></Card>
                    <Card><CardHeader><CardTitle>Tags</CardTitle></CardHeader><CardContent>{visibleTags.length === 0 ? <p className="text-sm">No tags found.</p> : <Table><TableHead><TableRow><TableHeaderCell>Name</TableHeaderCell><TableHeaderCell>Brands</TableHeaderCell><TableHeaderCell>Actions</TableHeaderCell></TableRow></TableHead><tbody>{visibleTags.map((item) => <TableRow key={item.id}><TableCell>{item.name}</TableCell><TableCell>{item.brand_slugs.join(", ") || "—"}</TableCell><TableCell><div className="flex gap-2"><Button size="sm" variant="outline" onClick={() => { setEditingTag(item); setEditingTagForm({ name: item.name, slug: item.slug, brand_ids: idsFor(item.brand_slugs) }); }}>Edit</Button><Button size="sm" variant="destructive" onClick={() => void remove(AdminAPI.website.blog.tags.delete(item.id), item.id, "tag")}>Delete</Button></div></TableCell></TableRow>)}</tbody></Table>}</CardContent></Card>
                </div>

                {loading ? <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">Loading...</p> : visiblePosts.length === 0 ? <EmptyState title="No blog posts found" description="Create a post or change the selected brand filter." /> : <Table><TableHead><TableRow><TableHeaderCell>Title</TableHeaderCell><TableHeaderCell>Brands</TableHeaderCell><TableHeaderCell>Published</TableHeaderCell><TableHeaderCell>Featured</TableHeaderCell><TableHeaderCell>Actions</TableHeaderCell></TableRow></TableHead><tbody>{visiblePosts.map((post) => <TableRow key={post.id}><TableCell>{post.title}</TableCell><TableCell>{post.brand_slugs.join(", ") || "—"}</TableCell><TableCell>{post.published ? "Yes" : "No"}</TableCell><TableCell>{post.featured ? "Yes" : "No"}</TableCell><TableCell><div className="flex gap-2"><Button size="sm" variant="outline" onClick={() => startPostEdit(post)}>Edit</Button><Button size="sm" variant="destructive" onClick={() => void remove(AdminAPI.website.blog.posts.delete(post.id), post.id, "post")}>Delete</Button></div></TableCell></TableRow>)}</tbody></Table>}
            </div>
        </Container>
    );
}
