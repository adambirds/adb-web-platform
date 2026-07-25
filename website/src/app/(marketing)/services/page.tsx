import { JsonLd } from "@/components/seo/JsonLd";
import {
    ButtonLink,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Container,
    SectionHeader,
} from "@/components/ui";
import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Services",
    description:
        "Web platforms, automation, and delivery support tailored for founders, teams, and agencies.",
    alternates: {
        canonical: "/services",
    },
    openGraph: {
        title: "Services | ADB Software Solutions",
        description:
            "Web platforms, automation, and delivery support tailored for founders, teams, and agencies.",
        url: "/services",
    },
};

const services = [
    {
        title: "Web platform delivery",
        description:
            "Design, build, and launch web products with clear architecture, scalable infrastructure, and reliable release processes.",
        outcomes: [
            "MVPs and rebuilds",
            "Performance optimisation",
            "SEO-ready launches",
        ],
    },
    {
        title: "Automation & internal tooling",
        description:
            "Automate repetitive work, integrate systems, and create internal tools that save teams hours every week.",
        outcomes: ["Workflow automation", "Internal dashboards", "Ops tooling"],
    },
    {
        title: "Delivery rescue",
        description:
            "Stabilise existing platforms, audit bottlenecks, and build a pragmatic delivery plan for long-term scale.",
        outcomes: ["Technical audits", "Refactors", "Stability improvements"],
    },
];

const engagementModels = [
    {
        title: "Direct delivery",
        description:
            "End-to-end project delivery with clear milestones and outcomes.",
    },
    {
        title: "White-label support",
        description: "Augment agency teams with reliable engineering capacity.",
    },
    {
        title: "Fractional or contract",
        description:
            "Embedded support for teams that need senior engineering leadership.",
    },
];

export default function ServicesPage() {
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
                name: "Services",
                item: "https://adbsoftwaresolutions.co.uk/services",
            },
        ],
    };

    const servicesSchema = {
        "@context": "https://schema.org",
        "@type": "Service",
        name: "Software engineering services",
        provider: {
            "@type": "Organization",
            name: "ADB Software Solutions",
            url: "https://adbsoftwaresolutions.co.uk",
        },
        serviceType: ["Web platform delivery", "Automation", "Delivery rescue"],
    };

    return (
        <div className="space-y-16 pt-10 pb-24">
            <Container>
                <SectionHeader
                    eyebrow="Services"
                    title="Engineering that keeps delivery moving"
                    subtitle="I help teams ship reliable, measurable outcomes with minimal overhead."
                />
                <div className="mt-10 grid gap-6 md:grid-cols-3">
                    {services.map((service) => (
                        <Card key={service.title}>
                            <CardHeader>
                                <CardTitle>{service.title}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                    {service.description}
                                </p>
                                <ul className="text-adb-navy-600 dark:text-adb-navy-300 mt-4 list-disc space-y-1 pl-4 text-sm">
                                    {service.outcomes.map((item) => (
                                        <li key={item}>{item}</li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </Container>

            <Container>
                <SectionHeader
                    eyebrow="Engagement"
                    title="Flexible ways to work"
                    subtitle="Choose the engagement model that fits your team and delivery needs."
                />
                <div className="mt-10 grid gap-6 md:grid-cols-3">
                    {engagementModels.map((model) => (
                        <Card key={model.title}>
                            <CardHeader>
                                <CardTitle>{model.title}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                    {model.description}
                                </p>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </Container>

            <Container>
                <div className="border-adb-navy-200 dark:border-adb-navy-800 dark:bg-adb-navy-900 flex flex-col gap-4 rounded-2xl border bg-white p-8 text-left">
                    <h3 className="text-adb-navy dark:text-adb-navy-100 text-2xl font-semibold">
                        Ready for a delivery plan?
                    </h3>
                    <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                        Share your goals and I’ll outline a clear scope and
                        timeline.
                    </p>
                    <div>
                        <ButtonLink href="/contact" size="lg">
                            Start a project
                        </ButtonLink>
                    </div>
                </div>
            </Container>
            <JsonLd data={[breadcrumbs, servicesSchema]} />
        </div>
    );
}
