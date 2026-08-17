"use client";

import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Container,
    EmptyState,
    PageHeader,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import Link from "next/link";

const sections = [
    {
        title: "Portfolio",
        description: "Manage case studies, outcomes, and featured work.",
        href: "/admin/content/portfolio",
        permission: "website.view_portfolio",
    },
    {
        title: "Testimonials",
        description: "Curate client quotes and featured testimonials.",
        href: "/admin/content/testimonials",
        permission: "website.view_testimonial",
    },
    {
        title: "Blog",
        description: "Publish and organise blog content, categories, and tags.",
        href: "/admin/content/blog",
        permission: "website.view_blogpost",
    },
    {
        title: "FAQs",
        description: "Maintain frequently asked questions and categories.",
        href: "/admin/content/faqs",
        permission: "website.view_faq",
    },
] as const;

export default function ContentOverviewPage() {
    const { hasPermission } = useAuth();
    const visibleSections = sections.filter((section) =>
        hasPermission(section.permission),
    );

    return (
        <Container className="py-10">
            <PageHeader
                title="Content management"
                description="Create and update brand-aware content for the public ADB websites."
            />

            {visibleSections.length === 0 ? (
                <div className="mt-8">
                    <EmptyState
                        title="No content access"
                        description="Your account does not currently have permission to view any CMS content areas."
                    />
                </div>
            ) : (
                <div className="mt-8 grid gap-6 md:grid-cols-2">
                    {visibleSections.map((section) => (
                        <Card key={section.title}>
                            <CardHeader>
                                <CardTitle>{section.title}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                    {section.description}
                                </p>
                                <Link
                                    href={section.href}
                                    className="border-adb-navy-200 text-adb-navy hover:bg-adb-navy-50 dark:border-adb-navy-700 dark:text-adb-navy-100 dark:hover:bg-adb-navy-900 mt-4 inline-flex rounded-lg border px-4 py-2 text-sm font-medium transition"
                                >
                                    Manage {section.title}
                                </Link>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </Container>
    );
}
