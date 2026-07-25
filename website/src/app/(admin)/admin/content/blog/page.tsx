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

interface BlogPostItem {
    id: number;
    title: string;
    slug: string;
    excerpt?: string;
    content?: string;
    published: boolean;
    featured: boolean;
    categories?: Array<{ id: number }>;
    tags?: Array<{ id: number }>;
}

interface BlogCategoryItem {
    id: number;
    name: string;
    slug: string;
    description?: string;
}

interface BlogTagItem {
    id: number;
    name: string;
    slug: string;
}

export default function AdminBlogPage() {
    const [posts, setPosts] = useState<BlogPostItem[]>([]);
    const [categories, setCategories] = useState<BlogCategoryItem[]>([]);
    const [tags, setTags] = useState<BlogTagItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [savingCategory, setSavingCategory] = useState(false);
    const [savingTag, setSavingTag] = useState(false);
    const [editingPost, setEditingPost] = useState<BlogPostItem | null>(null);
    const [editingCategory, setEditingCategory] =
        useState<BlogCategoryItem | null>(null);
    const [editingTag, setEditingTag] = useState<BlogTagItem | null>(null);
    const [createCategoryIds, setCreateCategoryIds] = useState<number[]>([]);
    const [createTagIds, setCreateTagIds] = useState<number[]>([]);
    const [editPostForm, setEditPostForm] = useState({
        title: "",
        slug: "",
        excerpt: "",
        content: "",
        published: false,
        featured: false,
        category_ids: [] as number[],
        tag_ids: [] as number[],
    });
    const [editCategoryForm, setEditCategoryForm] = useState({
        name: "",
        slug: "",
        description: "",
    });
    const [editTagForm, setEditTagForm] = useState({
        name: "",
        slug: "",
    });

    useEffect(() => {
        async function load() {
            try {
                const [postData, categoryData, tagData] = await Promise.all([
                    fetchAPI(AdminAPI.website.blog.posts.list(), {
                        credentials: "include",
                    }),
                    fetchAPI(AdminAPI.website.blog.categories.list(), {
                        credentials: "include",
                    }),
                    fetchAPI(AdminAPI.website.blog.tags.list(), {
                        credentials: "include",
                    }),
                ]);
                setPosts(postData);
                setCategories(categoryData);
                setTags(tagData);
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
            description: formData.get("description") || "",
        };

        try {
            const created = await fetchAPI(
                AdminAPI.website.blog.categories.create(),
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

    async function handleCreateTag(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setSavingTag(true);
        const formData = new FormData(event.currentTarget);
        const payload = {
            name: formData.get("name"),
            slug: formData.get("slug"),
        };

        try {
            const created = await fetchAPI(
                AdminAPI.website.blog.tags.create(),
                {
                    method: "POST",
                    credentials: "include",
                    body: JSON.stringify(payload),
                },
            );
            setTags((prev) => [...prev, created]);
            event.currentTarget.reset();
        } catch (error) {
            console.error(error);
        } finally {
            setSavingTag(false);
        }
    }

    async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setSaving(true);
        const formData = new FormData(event.currentTarget);
        const payload = {
            title: formData.get("title"),
            slug: formData.get("slug"),
            excerpt: formData.get("excerpt"),
            content: formData.get("content"),
            published: Boolean(formData.get("published")),
            featured: Boolean(formData.get("featured")),
            category_ids: createCategoryIds,
            tag_ids: createTagIds,
        };

        try {
            const created = await fetchAPI(
                AdminAPI.website.blog.posts.create(),
                {
                    method: "POST",
                    credentials: "include",
                    body: JSON.stringify(payload),
                },
            );
            setPosts((prev) => [created, ...prev]);
            event.currentTarget.reset();
            setCreateCategoryIds([]);
            setCreateTagIds([]);
        } catch (error) {
            console.error(error);
        } finally {
            setSaving(false);
        }
    }

    async function handleDeletePost(id: number) {
        try {
            await fetchAPI(AdminAPI.website.blog.posts.delete(id), {
                method: "DELETE",
                credentials: "include",
            });
            setPosts((prev) => prev.filter((post) => post.id !== id));
        } catch (error) {
            console.error(error);
        }
    }

    async function handleDeleteCategory(id: number) {
        try {
            await fetchAPI(AdminAPI.website.blog.categories.delete(id), {
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

    async function handleDeleteTag(id: number) {
        try {
            await fetchAPI(AdminAPI.website.blog.tags.delete(id), {
                method: "DELETE",
                credentials: "include",
            });
            setTags((prev) => prev.filter((tag) => tag.id !== id));
        } catch (error) {
            console.error(error);
        }
    }

    async function handleUpdatePost(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!editingPost) {
            return;
        }
        setSaving(true);
        const payload = {
            title: editPostForm.title,
            slug: editPostForm.slug,
            excerpt: editPostForm.excerpt,
            content: editPostForm.content,
            published: editPostForm.published,
            featured: editPostForm.featured,
            category_ids: editPostForm.category_ids,
            tag_ids: editPostForm.tag_ids,
        };

        try {
            const updated = await fetchAPI(
                AdminAPI.website.blog.posts.update(editingPost.id),
                {
                    method: "PUT",
                    credentials: "include",
                    body: JSON.stringify(payload),
                },
            );
            setPosts((prev) =>
                prev.map((post) =>
                    post.id === editingPost.id ? updated : post,
                ),
            );
            setEditingPost(null);
        } catch (error) {
            console.error(error);
        } finally {
            setSaving(false);
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
        };

        try {
            const updated = await fetchAPI(
                AdminAPI.website.blog.categories.update(editingCategory.id),
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

    async function handleUpdateTag(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!editingTag) {
            return;
        }
        setSavingTag(true);
        const payload = {
            name: editTagForm.name,
            slug: editTagForm.slug,
        };

        try {
            const updated = await fetchAPI(
                AdminAPI.website.blog.tags.update(editingTag.id),
                {
                    method: "PUT",
                    credentials: "include",
                    body: JSON.stringify(payload),
                },
            );
            setTags((prev) =>
                prev.map((tag) => (tag.id === editingTag.id ? updated : tag)),
            );
            setEditingTag(null);
        } catch (error) {
            console.error(error);
        } finally {
            setSavingTag(false);
        }
    }

    return (
        <Container className="py-10">
            <PageHeader
                title="Blog"
                description="Create and manage blog posts, categories, and tags."
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
                            <CardTitle>Create blog category</CardTitle>
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
                            <CardTitle>Create blog tag</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form
                                onSubmit={handleCreateTag}
                                className="space-y-4"
                            >
                                <div className="grid gap-4 md:grid-cols-2">
                                    <Input
                                        name="name"
                                        placeholder="Tag name"
                                        required
                                    />
                                    <Input
                                        name="slug"
                                        placeholder="Slug"
                                        required
                                    />
                                </div>
                                <Button type="submit" disabled={savingTag}>
                                    {savingTag ? "Creating..." : "Create tag"}
                                </Button>
                            </form>
                        </CardContent>
                    </Card>
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

                {editingTag ? (
                    <Card className="mt-6">
                        <CardHeader>
                            <CardTitle>Edit tag</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form
                                onSubmit={handleUpdateTag}
                                className="space-y-4"
                            >
                                <div className="grid gap-4 md:grid-cols-2">
                                    <Input
                                        value={editTagForm.name}
                                        onChange={(event) =>
                                            setEditTagForm((prev) => ({
                                                ...prev,
                                                name: event.target.value,
                                            }))
                                        }
                                        placeholder="Tag name"
                                        required
                                    />
                                    <Input
                                        value={editTagForm.slug}
                                        onChange={(event) =>
                                            setEditTagForm((prev) => ({
                                                ...prev,
                                                slug: event.target.value,
                                            }))
                                        }
                                        placeholder="Slug"
                                        required
                                    />
                                </div>
                                <div className="flex gap-3">
                                    <Button type="submit" disabled={savingTag}>
                                        {savingTag
                                            ? "Updating..."
                                            : "Update tag"}
                                    </Button>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        onClick={() => setEditingTag(null)}
                                    >
                                        Cancel
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                ) : null}

                <Card>
                    <CardHeader>
                        <CardTitle>Create blog post</CardTitle>
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
                                name="excerpt"
                                rows={3}
                                placeholder="Excerpt"
                                required
                            />
                            <Textarea
                                name="content"
                                rows={8}
                                placeholder="Content"
                                required
                            />
                            <div className="grid gap-4 md:grid-cols-2">
                                <Select
                                    multiple
                                    value={createCategoryIds.map(String)}
                                    onChange={(event) => {
                                        const selected = Array.from(
                                            event.currentTarget.selectedOptions,
                                        ).map((option) => Number(option.value));
                                        setCreateCategoryIds(selected);
                                    }}
                                >
                                    {categories.map((category) => (
                                        <option
                                            key={category.id}
                                            value={category.id}
                                        >
                                            {category.name}
                                        </option>
                                    ))}
                                </Select>
                                <Select
                                    multiple
                                    value={createTagIds.map(String)}
                                    onChange={(event) => {
                                        const selected = Array.from(
                                            event.currentTarget.selectedOptions,
                                        ).map((option) => Number(option.value));
                                        setCreateTagIds(selected);
                                    }}
                                >
                                    {tags.map((tag) => (
                                        <option key={tag.id} value={tag.id}>
                                            {tag.name}
                                        </option>
                                    ))}
                                </Select>
                            </div>
                            <div className="flex flex-wrap gap-4">
                                <label className="text-adb-navy-600 dark:text-adb-navy-300 flex items-center gap-2 text-sm">
                                    <input type="checkbox" name="published" />
                                    Published
                                </label>
                                <label className="text-adb-navy-600 dark:text-adb-navy-300 flex items-center gap-2 text-sm">
                                    <input type="checkbox" name="featured" />
                                    Featured
                                </label>
                            </div>
                            <Button type="submit" disabled={saving}>
                                {saving ? "Creating..." : "Create post"}
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                {editingPost ? (
                    <Card className="mt-6">
                        <CardHeader>
                            <CardTitle>Edit blog post</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form
                                onSubmit={handleUpdatePost}
                                className="space-y-4"
                            >
                                <div className="grid gap-4 md:grid-cols-2">
                                    <Input
                                        value={editPostForm.title}
                                        onChange={(event) =>
                                            setEditPostForm((prev) => ({
                                                ...prev,
                                                title: event.target.value,
                                            }))
                                        }
                                        placeholder="Title"
                                        required
                                    />
                                    <Input
                                        value={editPostForm.slug}
                                        onChange={(event) =>
                                            setEditPostForm((prev) => ({
                                                ...prev,
                                                slug: event.target.value,
                                            }))
                                        }
                                        placeholder="Slug"
                                        required
                                    />
                                </div>
                                <Textarea
                                    value={editPostForm.excerpt}
                                    onChange={(event) =>
                                        setEditPostForm((prev) => ({
                                            ...prev,
                                            excerpt: event.target.value,
                                        }))
                                    }
                                    rows={3}
                                    placeholder="Excerpt"
                                    required
                                />
                                <Textarea
                                    value={editPostForm.content}
                                    onChange={(event) =>
                                        setEditPostForm((prev) => ({
                                            ...prev,
                                            content: event.target.value,
                                        }))
                                    }
                                    rows={8}
                                    placeholder="Content"
                                    required
                                />
                                <div className="grid gap-4 md:grid-cols-2">
                                    <Select
                                        multiple
                                        value={editPostForm.category_ids.map(
                                            String,
                                        )}
                                        onChange={(event) => {
                                            const selected = Array.from(
                                                event.currentTarget
                                                    .selectedOptions,
                                            ).map((option) =>
                                                Number(option.value),
                                            );
                                            setEditPostForm((prev) => ({
                                                ...prev,
                                                category_ids: selected,
                                            }));
                                        }}
                                    >
                                        {categories.map((category) => (
                                            <option
                                                key={category.id}
                                                value={category.id}
                                            >
                                                {category.name}
                                            </option>
                                        ))}
                                    </Select>
                                    <Select
                                        multiple
                                        value={editPostForm.tag_ids.map(String)}
                                        onChange={(event) => {
                                            const selected = Array.from(
                                                event.currentTarget
                                                    .selectedOptions,
                                            ).map((option) =>
                                                Number(option.value),
                                            );
                                            setEditPostForm((prev) => ({
                                                ...prev,
                                                tag_ids: selected,
                                            }));
                                        }}
                                    >
                                        {tags.map((tag) => (
                                            <option key={tag.id} value={tag.id}>
                                                {tag.name}
                                            </option>
                                        ))}
                                    </Select>
                                </div>
                                <div className="flex flex-wrap gap-4">
                                    <label className="text-adb-navy-600 dark:text-adb-navy-300 flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={editPostForm.published}
                                            onChange={(event) =>
                                                setEditPostForm((prev) => ({
                                                    ...prev,
                                                    published:
                                                        event.target.checked,
                                                }))
                                            }
                                        />
                                        Published
                                    </label>
                                    <label className="text-adb-navy-600 dark:text-adb-navy-300 flex items-center gap-2 text-sm">
                                        <input
                                            type="checkbox"
                                            checked={editPostForm.featured}
                                            onChange={(event) =>
                                                setEditPostForm((prev) => ({
                                                    ...prev,
                                                    featured:
                                                        event.target.checked,
                                                }))
                                            }
                                        />
                                        Featured
                                    </label>
                                </div>
                                <div className="flex gap-3">
                                    <Button type="submit" disabled={saving}>
                                        {saving ? "Updating..." : "Update post"}
                                    </Button>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        onClick={() => setEditingPost(null)}
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
                ) : posts.length === 0 ? (
                    <EmptyState
                        title="No blog posts yet"
                        description="Draft your first post to start sharing insights."
                    />
                ) : (
                    <div className="space-y-8">
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableHeaderCell>Title</TableHeaderCell>
                                    <TableHeaderCell>Published</TableHeaderCell>
                                    <TableHeaderCell>Featured</TableHeaderCell>
                                    <TableHeaderCell>Actions</TableHeaderCell>
                                </TableRow>
                            </TableHead>
                            <tbody>
                                {posts.map((post) => (
                                    <TableRow key={post.id}>
                                        <TableCell>{post.title}</TableCell>
                                        <TableCell>
                                            {post.published ? "Yes" : "No"}
                                        </TableCell>
                                        <TableCell>
                                            {post.featured ? "Yes" : "No"}
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex gap-2">
                                                <Button
                                                    type="button"
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => {
                                                        setEditingPost(post);
                                                        setEditPostForm({
                                                            title: post.title,
                                                            slug: post.slug,
                                                            excerpt:
                                                                post.excerpt ??
                                                                "",
                                                            content:
                                                                post.content ??
                                                                "",
                                                            published:
                                                                post.published,
                                                            featured:
                                                                post.featured,
                                                            category_ids:
                                                                post.categories?.map(
                                                                    (cat) =>
                                                                        cat.id,
                                                                ) || [],
                                                            tag_ids:
                                                                post.tags?.map(
                                                                    (tag) =>
                                                                        tag.id,
                                                                ) || [],
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
                                                        handleDeletePost(
                                                            post.id,
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

                        <div className="grid gap-6 lg:grid-cols-2">
                            <div>
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
                                                <TableHeaderCell>
                                                    Name
                                                </TableHeaderCell>
                                                <TableHeaderCell>
                                                    Slug
                                                </TableHeaderCell>
                                                <TableHeaderCell>
                                                    Actions
                                                </TableHeaderCell>
                                            </TableRow>
                                        </TableHead>
                                        <tbody>
                                            {categories.map((category) => (
                                                <TableRow key={category.id}>
                                                    <TableCell>
                                                        {category.name}
                                                    </TableCell>
                                                    <TableCell>
                                                        {category.slug}
                                                    </TableCell>
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
                                                                    setEditCategoryForm(
                                                                        {
                                                                            name: category.name,
                                                                            slug: category.slug,
                                                                            description:
                                                                                category.description ||
                                                                                "",
                                                                        },
                                                                    );
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
                            <div>
                                <h3 className="text-adb-navy dark:text-adb-navy-100 mb-3 text-lg font-semibold">
                                    Tags
                                </h3>
                                {tags.length === 0 ? (
                                    <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                        No tags yet.
                                    </p>
                                ) : (
                                    <Table>
                                        <TableHead>
                                            <TableRow>
                                                <TableHeaderCell>
                                                    Name
                                                </TableHeaderCell>
                                                <TableHeaderCell>
                                                    Slug
                                                </TableHeaderCell>
                                                <TableHeaderCell>
                                                    Actions
                                                </TableHeaderCell>
                                            </TableRow>
                                        </TableHead>
                                        <tbody>
                                            {tags.map((tag) => (
                                                <TableRow key={tag.id}>
                                                    <TableCell>
                                                        {tag.name}
                                                    </TableCell>
                                                    <TableCell>
                                                        {tag.slug}
                                                    </TableCell>
                                                    <TableCell>
                                                        <div className="flex gap-2">
                                                            <Button
                                                                type="button"
                                                                variant="outline"
                                                                size="sm"
                                                                onClick={() => {
                                                                    setEditingTag(
                                                                        tag,
                                                                    );
                                                                    setEditTagForm(
                                                                        {
                                                                            name: tag.name,
                                                                            slug: tag.slug,
                                                                        },
                                                                    );
                                                                }}
                                                            >
                                                                Edit
                                                            </Button>
                                                            <Button
                                                                type="button"
                                                                variant="destructive"
                                                                size="sm"
                                                                onClick={() =>
                                                                    handleDeleteTag(
                                                                        tag.id,
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
                        </div>
                    </div>
                )}
            </div>
        </Container>
    );
}
