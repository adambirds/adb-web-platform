import { JsonLd } from "@/components/seo/JsonLd";
import {
    Badge,
    ButtonLink,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Container,
    SectionHeader,
} from "@/components/ui";
import { getBlogPosts } from "@/lib/api/public";
import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Blog",
    description:
        "Technical insights on web delivery, automation, and agency operations from ADB Software Solutions.",
    alternates: {
        canonical: "/blog",
    },
    openGraph: {
        title: "Blog | ADB Software Solutions",
        description:
            "Technical insights on web delivery, automation, and agency operations.",
        url: "/blog",
    },
};

export default async function BlogPage() {
    let posts: Array<{
        id: number;
        title: string;
        slug: string;
        excerpt: string;
        categories: Array<{ name: string }>;
    }> = [];

    try {
        posts = await getBlogPosts();
    } catch (error) {
        console.error(error);
    }
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
        ],
    };

    const blogSchema = {
        "@context": "https://schema.org",
        "@type": "Blog",
        name: "ADB Software Solutions Blog",
        url: "https://adbsoftwaresolutions.co.uk/blog",
        description:
            "Technical insights on web delivery, automation, and agency operations.",
    };

    return (
        <div className="space-y-16 pt-10 pb-24">
            <Container>
                <SectionHeader
                    eyebrow="Insights"
                    title="Notes on delivery, automation, and scale"
                    subtitle="Short reads from the engineering work behind ADB Software Solutions."
                />
            </Container>

            <Container>
                <div className="grid gap-6 md:grid-cols-3">
                    {posts.length === 0 ? (
                        <Card>
                            <CardContent>
                                <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                    Blog posts will appear here once published.
                                </p>
                            </CardContent>
                        </Card>
                    ) : (
                        posts.map((post) => (
                            <Card key={post.id}>
                                <CardHeader>
                                    <Badge className="bg-adb-navy-100 text-adb-navy dark:bg-adb-navy-900 w-fit">
                                        {post.categories?.[0]?.name ||
                                            "Insight"}
                                    </Badge>
                                    <CardTitle className="mt-4">
                                        {post.title}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                        {post.excerpt}
                                    </p>
                                    <div className="mt-4">
                                        <ButtonLink
                                            href={`/blog/${post.slug}`}
                                            variant="outline"
                                            size="sm"
                                        >
                                            Read post
                                        </ButtonLink>
                                    </div>
                                </CardContent>
                            </Card>
                        ))
                    )}
                </div>
            </Container>

            <Container>
                <Card className="bg-adb-navy-950 text-white">
                    <CardHeader>
                        <CardTitle className="text-white">
                            Want updates?
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-adb-navy-200 text-sm">
                            New posts will land here as they’re published. Reach
                            out if there’s a topic you’d like covered.
                        </p>
                        <div className="mt-4">
                            <ButtonLink
                                href="/contact"
                                variant="outline"
                                size="lg"
                            >
                                Suggest a topic
                            </ButtonLink>
                        </div>
                    </CardContent>
                </Card>
            </Container>
            <JsonLd data={[breadcrumbs, blogSchema]} />
        </div>
    );
}
