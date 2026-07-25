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
import { getPortfolio } from "@/lib/api/public";
import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Portfolio",
    description:
        "Selected delivery outcomes across web platforms, automation, and operational tooling.",
    alternates: {
        canonical: "/portfolio",
    },
    openGraph: {
        title: "Portfolio | ADB Software Solutions",
        description:
            "Selected delivery outcomes across web platforms, automation, and operational tooling.",
        url: "/portfolio",
    },
};

export default async function PortfolioPage() {
    let portfolio: Array<{
        id: number;
        title: string;
        slug: string;
        description: string;
        technologies: string[];
    }> = [];

    try {
        portfolio = await getPortfolio();
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
                name: "Portfolio",
                item: "https://adbsoftwaresolutions.co.uk/portfolio",
            },
        ],
    };

    const portfolioSchema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        name: "ADB Software Solutions portfolio",
        itemListElement: portfolio.map((item, index) => ({
            "@type": "ListItem",
            position: index + 1,
            name: item.title,
        })),
    };

    return (
        <div className="space-y-16 pt-10 pb-24">
            <Container>
                <SectionHeader
                    eyebrow="Portfolio"
                    title="Delivery outcomes you can measure"
                    subtitle="A selection of recent engagements focused on measurable business results."
                />
            </Container>

            <Container>
                <div className="grid gap-6 md:grid-cols-3">
                    {portfolio.length === 0 ? (
                        <Card>
                            <CardContent>
                                <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                    Portfolio items will appear once published.
                                </p>
                            </CardContent>
                        </Card>
                    ) : (
                        portfolio.map((item) => (
                            <Card key={item.id}>
                                <CardHeader>
                                    <Badge className="bg-adb-cyan/10 text-adb-cyan w-fit">
                                        {item.technologies?.[0] || "Case study"}
                                    </Badge>
                                    <CardTitle className="mt-4">
                                        {item.title}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                        {item.description}
                                    </p>
                                    <div className="mt-4">
                                        <ButtonLink
                                            href={`/portfolio/${item.slug}`}
                                            variant="outline"
                                            size="sm"
                                        >
                                            View case study
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
                            Need a similar outcome?
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-adb-navy-200 text-sm">
                            Share your goals and I’ll respond with a plan that
                            fits your timeline.
                        </p>
                        <div className="mt-4">
                            <ButtonLink href="/contact" size="lg">
                                Discuss a project
                            </ButtonLink>
                        </div>
                    </CardContent>
                </Card>
            </Container>
            <JsonLd data={[breadcrumbs, portfolioSchema]} />
        </div>
    );
}
