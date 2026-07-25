import {
    ButtonLink,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Container,
    PageHeader,
} from "@/components/ui";

export const metadata = {
    title: "Content",
};

const sections = [
    {
        title: "Portfolio",
        description: "Manage case studies, outcomes, and featured work.",
        href: "/admin/content/portfolio",
    },
    {
        title: "Testimonials",
        description: "Curate client quotes and featured testimonials.",
        href: "/admin/content/testimonials",
    },
    {
        title: "Blog",
        description: "Publish and organise blog content, categories, and tags.",
        href: "/admin/content/blog",
    },
    {
        title: "FAQs",
        description: "Maintain frequently asked questions and categories.",
        href: "/admin/content/faqs",
    },
];

export default function ContentOverviewPage() {
    return (
        <Container className="py-10">
            <PageHeader
                title="Content management"
                description="Create and update the content that powers the marketing site."
                actions={<ButtonLink href="/">View site</ButtonLink>}
            />

            <div className="mt-8 grid gap-6 md:grid-cols-2">
                {sections.map((section) => (
                    <Card key={section.title}>
                        <CardHeader>
                            <CardTitle>{section.title}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                {section.description}
                            </p>
                            <div className="mt-4">
                                <ButtonLink
                                    href={section.href}
                                    variant="outline"
                                >
                                    Manage {section.title}
                                </ButtonLink>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </Container>
    );
}
