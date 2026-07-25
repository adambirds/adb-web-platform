import { JsonLd } from "@/components/seo/JsonLd";
import { Container, SectionHeader } from "@/components/ui";
import { getBlogPostBySlug } from "@/lib/api/public";
import type { Metadata } from "next";
import type { ComponentPropsWithoutRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface BlogPost {
    id: number;
    title: string;
    slug: string;
    excerpt: string;
    content: string;
    author: string;
    published_at?: string | null;
    categories: Array<{ name: string }>;
}

interface PageProps {
    params: { slug: string };
}

export async function generateMetadata({
    params,
}: PageProps): Promise<Metadata> {
    const post = await getBlogPostBySlug(params.slug);

    return {
        title: post.title,
        description: post.excerpt,
        alternates: {
            canonical: `/blog/${post.slug}`,
        },
        openGraph: {
            title: post.title,
            description: post.excerpt,
            url: `/blog/${post.slug}`,
        },
    };
}

export default async function BlogPostPage({ params }: PageProps) {
    const post: BlogPost = await getBlogPostBySlug(params.slug);

    const breadcrumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        itemListElement: [
            {
                "@type": "ListItem",
                position: 1,
                name: "Home",
                item: "https://adbsoftwaresolutions.co.uk/",
            },
            {
                "@type": "ListItem",
                position: 2,
                name: "Blog",
                item: "https://adbsoftwaresolutions.co.uk/blog",
            },
            {
                "@type": "ListItem",
                position: 3,
                name: post.title,
                item: `https://adbsoftwaresolutions.co.uk/blog/${post.slug}`,
            },
        ],
    };

    const articleSchema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        headline: post.title,
        description: post.excerpt,
        author: {
            "@type": "Person",
            name: post.author,
        },
        datePublished: post.published_at,
        url: `https://adbsoftwaresolutions.co.uk/blog/${post.slug}`,
    };

    return (
        <div className="space-y-12 pt-10 pb-24">
            <Container>
                <SectionHeader
                    eyebrow={post.categories?.[0]?.name || "Insight"}
                    title={post.title}
                    subtitle={post.excerpt}
                />
            </Container>

            <Container>
                <article className="text-adb-navy-600 dark:text-adb-navy-300 space-y-4 leading-relaxed">
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            h2: (props: ComponentPropsWithoutRef<"h2">) => (
                                <h2
                                    className="text-adb-navy dark:text-adb-navy-100 mt-8 text-2xl font-semibold"
                                    {...props}
                                />
                            ),
                            h3: (props: ComponentPropsWithoutRef<"h3">) => (
                                <h3
                                    className="text-adb-navy dark:text-adb-navy-100 mt-6 text-xl font-semibold"
                                    {...props}
                                />
                            ),
                            a: (props: ComponentPropsWithoutRef<"a">) => (
                                <a
                                    className="text-adb-cyan hover:text-adb-cyan-600 underline"
                                    {...props}
                                />
                            ),
                            ul: (props: ComponentPropsWithoutRef<"ul">) => (
                                <ul
                                    className="list-disc space-y-2 pl-5"
                                    {...props}
                                />
                            ),
                            ol: (props: ComponentPropsWithoutRef<"ol">) => (
                                <ol
                                    className="list-decimal space-y-2 pl-5"
                                    {...props}
                                />
                            ),
                        }}
                    >
                        {post.content}
                    </ReactMarkdown>
                </article>
            </Container>

            <JsonLd data={[breadcrumbs, articleSchema]} />
        </div>
    );
}
