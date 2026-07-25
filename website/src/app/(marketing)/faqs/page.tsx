import { JsonLd } from "@/components/seo/JsonLd";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Container,
    SectionHeader,
} from "@/components/ui";
import { getFaqCategories, getFaqs } from "@/lib/api/public";
import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "FAQs",
    description:
        "Frequently asked questions about working with ADB Software Solutions.",
    alternates: {
        canonical: "/faqs",
    },
    openGraph: {
        title: "FAQs | ADB Software Solutions",
        description:
            "Frequently asked questions about working with ADB Software Solutions.",
        url: "/faqs",
    },
};

export default async function FAQsPage() {
    let faqs: Array<{
        id: number;
        question: string;
        answer: string;
        category: { id: number; name: string; slug: string; order: number };
    }> = [];
    let categories: Array<{
        id: number;
        name: string;
        slug: string;
        order: number;
    }> = [];

    try {
        [faqs, categories] = await Promise.all([getFaqs(), getFaqCategories()]);
    } catch (error) {
        console.error(error);
    }

    const groupedFaqs = categories
        .slice()
        .sort((a, b) => a.order - b.order)
        .map((category) => ({
            category,
            items: faqs.filter((faq) => faq.category?.id === category.id),
        }))
        .filter((group) => group.items.length > 0);
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
                name: "FAQs",
                item: "https://adbsoftwaresolutions.co.uk/faqs",
            },
        ],
    };

    const faqSchema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        mainEntity: faqs.map((faq) => ({
            "@type": "Question",
            name: faq.question,
            acceptedAnswer: {
                "@type": "Answer",
                text: faq.answer,
            },
        })),
    };

    return (
        <div className="space-y-16 pt-10 pb-24">
            <Container>
                <SectionHeader
                    eyebrow="FAQs"
                    title="Clear answers before we start"
                    subtitle="If you have another question, just get in touch."
                />
            </Container>

            <Container>
                {groupedFaqs.length === 0 ? (
                    <Card>
                        <CardContent>
                            <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                FAQs will appear here once published.
                            </p>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="space-y-10">
                        {groupedFaqs.map((group) => (
                            <div key={group.category.id} className="space-y-4">
                                <h3 className="text-adb-navy dark:text-adb-navy-100 text-xl font-semibold">
                                    {group.category.name}
                                </h3>
                                <div className="grid gap-6 md:grid-cols-2">
                                    {group.items.map((faq) => (
                                        <Card key={faq.id}>
                                            <CardHeader>
                                                <CardTitle>
                                                    {faq.question}
                                                </CardTitle>
                                            </CardHeader>
                                            <CardContent>
                                                <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                                    {faq.answer}
                                                </p>
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </Container>
            <JsonLd data={[breadcrumbs, faqSchema]} />
        </div>
    );
}
