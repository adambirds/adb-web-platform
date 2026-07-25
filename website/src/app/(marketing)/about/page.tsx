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
import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "About",
    description:
        "Meet the engineer behind ADB Software Solutions and how the solo-led model delivers agency-level results.",
    alternates: {
        canonical: "/about",
    },
    openGraph: {
        title: "About | ADB Software Solutions",
        description:
            "Learn how a solo-led consultancy delivers agency-level results with direct collaboration.",
        url: "/about",
    },
};

export default function AboutPage() {
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
                name: "About",
                item: "https://adbsoftwaresolutions.co.uk/about",
            },
        ],
    };

    return (
        <div className="space-y-16 pt-10 pb-24">
            <Container>
                <SectionHeader
                    eyebrow="About"
                    title="I deliver the work you hire me for"
                    subtitle="ADB Software Solutions is a solo-led consultancy. You collaborate directly with me, a senior software engineer who builds, ships, and supports the systems you rely on."
                />
            </Container>

            <Container>
                <div className="grid gap-6 md:grid-cols-2">
                    <Card>
                        <CardHeader>
                            <Badge className="w-fit">Who I am</Badge>
                            <CardTitle className="mt-4">
                                Senior engineer, hands-on builder
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                I design and deliver production systems,
                                internal tooling, and automation. My background
                                spans agency delivery, SaaS platforms, and
                                operational systems that need to be dependable
                                from day one.
                            </p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader>
                            <Badge className="w-fit">How I work</Badge>
                            <CardTitle className="mt-4">
                                Direct collaboration
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                You work directly with me. No handoffs, no
                                account managers, no busywork. Every decision is
                                documented and every milestone has clear
                                outcomes.
                            </p>
                        </CardContent>
                    </Card>
                </div>
            </Container>

            <Container>
                <div className="grid gap-6 md:grid-cols-3">
                    <Card>
                        <CardHeader>
                            <Badge className="w-fit">Why solo</Badge>
                            <CardTitle className="mt-4">
                                Lower overhead, higher output
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                Without large-team overheads, your budget goes
                                into delivery. The result is faster decisions,
                                tighter scope control, and a clear line of
                                accountability.
                            </p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader>
                            <Badge className="w-fit">Who I work with</Badge>
                            <CardTitle className="mt-4">
                                Founders, teams, agencies
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                I work with founders launching products,
                                established teams scaling systems, and agencies
                                that need white-label delivery support.
                            </p>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader>
                            <Badge className="w-fit">Engagement</Badge>
                            <CardTitle className="mt-4">
                                Flexible, outcome-focused
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                Short sprints, fractional engagements, or
                                ongoing support. Every engagement has a clear
                                plan, timeline, and definition of done.
                            </p>
                        </CardContent>
                    </Card>
                </div>
            </Container>

            <Container>
                <Card className="bg-adb-navy-950 text-white">
                    <CardHeader>
                        <CardTitle className="text-white">
                            Ready to work together?
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-adb-navy-200 text-sm">
                            Share your goals and I’ll reply with a clear
                            delivery plan and next steps.
                        </p>
                        <div className="mt-4">
                            <ButtonLink href="/contact" size="lg">
                                Book a call
                            </ButtonLink>
                        </div>
                    </CardContent>
                </Card>
            </Container>
            <JsonLd data={breadcrumbs} />
        </div>
    );
}
