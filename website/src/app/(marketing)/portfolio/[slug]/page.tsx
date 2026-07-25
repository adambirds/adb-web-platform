import { JsonLd } from "@/components/seo/JsonLd";
import { ButtonLink, Container, SectionHeader } from "@/components/ui";
import { getPortfolioBySlug } from "@/lib/api/public";
import type { Metadata } from "next";

interface PortfolioItem {
    id: number;
    title: string;
    slug: string;
    description: string;
    challenge: string;
    solution: string;
    results: string;
    technologies: string[];
    project_url?: string | null;
    github_url?: string | null;
    featured_image_url?: string | null;
}

interface PageProps {
    params: { slug: string };
}

export async function generateMetadata({
    params,
}: PageProps): Promise<Metadata> {
    const item = await getPortfolioBySlug(params.slug);

    return {
        title: item.title,
        description: item.description,
        alternates: {
            canonical: `/portfolio/${item.slug}`,
        },
        openGraph: {
            title: item.title,
            description: item.description,
            url: `/portfolio/${item.slug}`,
        },
    };
}

export default async function PortfolioDetailPage({ params }: PageProps) {
    const item: PortfolioItem = await getPortfolioBySlug(params.slug);

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
            {
                "@type": "ListItem",
                position: 3,
                name: item.title,
                item: `https://adbsoftwaresolutions.co.uk/portfolio/${item.slug}`,
            },
        ],
    };

    const caseStudySchema = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        name: item.title,
        description: item.description,
        url: `https://adbsoftwaresolutions.co.uk/portfolio/${item.slug}`,
    };

    return (
        <div className="space-y-12 pt-10 pb-24">
            <Container>
                <SectionHeader
                    eyebrow="Case study"
                    title={item.title}
                    subtitle={item.description}
                />
            </Container>

            <Container>
                <div className="space-y-8">
                    <div>
                        <h2 className="text-adb-navy dark:text-adb-navy-100 text-2xl font-semibold">
                            Challenge
                        </h2>
                        <p className="text-adb-navy-600 dark:text-adb-navy-300 mt-3">
                            {item.challenge}
                        </p>
                    </div>
                    <div>
                        <h2 className="text-adb-navy dark:text-adb-navy-100 text-2xl font-semibold">
                            Solution
                        </h2>
                        <p className="text-adb-navy-600 dark:text-adb-navy-300 mt-3">
                            {item.solution}
                        </p>
                    </div>
                    <div>
                        <h2 className="text-adb-navy dark:text-adb-navy-100 text-2xl font-semibold">
                            Results
                        </h2>
                        <p className="text-adb-navy-600 dark:text-adb-navy-300 mt-3">
                            {item.results}
                        </p>
                    </div>
                    {item.technologies?.length ? (
                        <div>
                            <h3 className="text-adb-navy dark:text-adb-navy-100 text-xl font-semibold">
                                Technology
                            </h3>
                            <ul className="text-adb-navy-600 dark:text-adb-navy-300 mt-3 list-disc space-y-1 pl-4">
                                {item.technologies.map((tech) => (
                                    <li key={tech}>{tech}</li>
                                ))}
                            </ul>
                        </div>
                    ) : null}
                    <div className="flex flex-wrap gap-3">
                        {item.project_url ? (
                            <ButtonLink
                                href={item.project_url}
                                variant="outline"
                            >
                                View project
                            </ButtonLink>
                        ) : null}
                        {item.github_url ? (
                            <ButtonLink
                                href={item.github_url}
                                variant="outline"
                            >
                                View repository
                            </ButtonLink>
                        ) : null}
                    </div>
                </div>
            </Container>

            <JsonLd data={[breadcrumbs, caseStudySchema]} />
        </div>
    );
}
