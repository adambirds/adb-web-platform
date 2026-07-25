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
import { getBlogPosts, getPortfolio, getTestimonials } from "@/lib/api/public";
import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Senior software engineer for agencies and founders",
    description:
        "ADB Software Solutions is a solo-led consultancy delivering agency-level engineering: web platforms, automation, and scalable systems.",
    alternates: {
        canonical: "/",
    },
    keywords: [
        "software consultant",
        "web development",
        "automation",
        "agency support",
        "fractional engineer",
    ],
    openGraph: {
        title: "ADB Software Solutions",
        description:
            "Solo-led consultancy delivering agency-level engineering for founders and teams.",
        url: "/",
    },
    twitter: {
        card: "summary_large_image",
        title: "ADB Software Solutions",
        description:
            "Solo-led consultancy delivering agency-level engineering for founders and teams.",
    },
};

const services = [
    {
        title: "Website design & builds",
        description:
            "Modern, responsive sites designed for conversion, speed, and SEO.",
    },
    {
        title: "Web apps & portals",
        description:
            "Production-grade web applications with clean architecture and clear delivery.",
    },
    {
        title: "Automation & ops",
        description:
            "Reduce manual work with automations, internal tools, and workflow improvements.",
    },
    {
        title: "Performance & SEO",
        description:
            "Optimise LCP, core web vitals, and technical SEO for measurable gains.",
    },
    {
        title: "Rescue & scale",
        description:
            "Audit, stabilise, and scale existing systems with pragmatic improvements.",
    },
    {
        title: "Ongoing support",
        description:
            "Reliable support and maintenance with clear SLAs and proactive monitoring.",
    },
];

const differentiators = [
    "Direct access to the engineer doing the work",
    "Low overheads, high leverage delivery",
    "Clear communication, documented decisions",
    "Automation-first mindset to save time and cost",
];

export default async function HomePage() {
    let portfolio: Array<{
        id: number;
        title: string;
        slug: string;
        description: string;
        featured: boolean;
        featured_image_url?: string | null;
    }> = [];
    let blogPosts: Array<{
        id: number;
        title: string;
        slug: string;
        excerpt: string;
    }> = [];
    let testimonials: Array<{
        id: number;
        quote: string;
        client_name: string;
        company: string;
        featured: boolean;
    }> = [];

    try {
        [portfolio, testimonials, blogPosts] = await Promise.all([
            getPortfolio(true),
            getTestimonials(true),
            getBlogPosts(),
        ]);
    } catch (error) {
        console.error(error);
    }

    const jsonLd = {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        name: "ADB Software Solutions",
        url: "https://adbsoftwaresolutions.co.uk",
        description:
            "Solo-led consultancy delivering agency-level engineering for founders and teams.",
        areaServed: "United Kingdom",
        serviceType: ["Web Development", "Automation", "Technical Consulting"],
    };

    return (
        <div className="space-y-24 pb-24">
            <section className="relative overflow-hidden bg-adb-navy-950 py-24">
                <div className="absolute inset-0 opacity-60">
                    <div className="h-full w-full bg-[radial-gradient(circle_at_top_left,rgba(96,253,245,0.28),transparent_40%),radial-gradient(circle_at_top_right,rgba(103,144,191,0.35),transparent_55%)]" />
                </div>
                <Container className="relative">
                    <div className="grid gap-12 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
                        <div>
                            <Badge className="bg-white/10 text-white">
                                ADB Software Solutions
                            </Badge>
                            <h1 className="mt-6 text-4xl font-semibold leading-tight text-white md:text-6xl">
                                High-impact web delivery for agencies and ambitious teams.
                            </h1>
                            <p className="mt-5 text-lg text-adb-navy-100">
                                Design-led websites, scalable platforms, and automation that make your business feel premium and perform at speed.
                            </p>
                            <div className="mt-8 flex flex-wrap gap-3">
                                <ButtonLink href="/contact" size="lg">
                                    Start a project
                                </ButtonLink>
                                <ButtonLink href="/portfolio" variant="outline" size="lg">
                                    View work
                                </ButtonLink>
                            </div>
                            <div className="mt-10 grid gap-4 md:grid-cols-3">
                                {[
                                    { label: "Delivery model", value: "Senior-led" },
                                    { label: "Response time", value: "24–48 hrs" },
                                    { label: "Core focus", value: "Web + automation" },
                                ].map((item) => (
                                    <div key={item.label}>
                                        <p className="text-sm text-adb-navy-200">
                                            {item.label}
                                        </p>
                                        <p className="text-base font-semibold text-white">
                                            {item.value}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="space-y-4">
                            <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl backdrop-blur">
                                <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-adb-navy-900/70 via-adb-navy-800/50 to-adb-navy-900/70 p-6">
                                    <div className="flex items-center justify-between text-xs text-adb-navy-200">
                                        <span>ADB Delivery Console</span>
                                        <span>Live preview</span>
                                    </div>
                                    <div className="mt-6 grid gap-4">
                                        {[
                                            "Project status", "Sprint notes", "Quality checks", "Launch plan",
                                        ].map((item) => (
                                            <div
                                                key={item}
                                                className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-adb-navy-100"
                                            >
                                                {item}
                                            </div>
                                        ))}
                                    </div>
                                    <div className="mt-6 grid gap-4 md:grid-cols-2">
                                        <div className="rounded-xl bg-white/5 p-4">
                                            <p className="text-xs text-adb-navy-200">Launch time</p>
                                            <p className="text-white">4–6 weeks</p>
                                        </div>
                                        <div className="rounded-xl bg-white/5 p-4">
                                            <p className="text-xs text-adb-navy-200">Efficiency gain</p>
                                            <p className="text-white">+35% faster</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="flex flex-wrap gap-3">
                                {["Agency partners", "SaaS teams", "Service firms", "Startups"].map(
                                    (label) => (
                                        <span
                                            key={label}
                                            className="rounded-full border border-white/20 px-4 py-2 text-xs text-adb-navy-100"
                                        >
                                            {label}
                                        </span>
                                    ),
                                )}
                            </div>
                        </div>
                    </div>
                    <div className="mt-12 border-t border-white/10 pt-8">
                        <p className="text-xs uppercase tracking-[0.3em] text-adb-navy-300">
                            Trusted by teams like
                        </p>
                        <div className="mt-4 grid grid-cols-2 gap-4 text-sm text-adb-navy-100 md:grid-cols-4">
                            {[
                                "Growth agencies",
                                "Product studios",
                                "SaaS founders",
                                "Operations teams",
                            ].map((label) => (
                                <span
                                    key={label}
                                    className="rounded-full border border-white/10 px-3 py-2 text-center"
                                >
                                    {label}
                                </span>
                            ))}
                        </div>
                    </div>
                </Container>
            </section>

            <Container>
                <SectionHeader
                    eyebrow="Services"
                    title="Premium delivery, end to end"
                    subtitle="Design, development, and optimisation that make you look world-class."
                />
                <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {services.map((service) => (
                        <Card key={service.title}>
                            <CardHeader>
                                <CardTitle>{service.title}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                    {service.description}
                                </p>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </Container>

            <Container>
                <SectionHeader
                    eyebrow="Process"
                    title="A delivery system built for agencies"
                    subtitle="Transparent milestones, clear approvals, and a clean handover."
                />
                <div className="mt-10 grid gap-6 md:grid-cols-3">
                    {[
                        {
                            title: "Discover",
                            body: "Define goals, timeline, and the metrics that matter most.",
                        },
                        {
                            title: "Deliver",
                            body: "Weekly updates, visible milestones, and structured approvals.",
                        },
                        {
                            title: "Support",
                            body: "Ongoing improvements, monitoring, and optimisation.",
                        },
                    ].map((step) => (
                        <Card key={step.title}>
                            <CardHeader>
                                <CardTitle>{step.title}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                    {step.body}
                                </p>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </Container>

            <Container>
                <SectionHeader
                    eyebrow="Portfolio"
                    title="Featured projects"
                    subtitle="A snapshot of recent delivery work."
                />
                <div className="mt-10 grid gap-6 md:grid-cols-3">
                    {portfolio.length === 0 ? (
                        <Card>
                            <CardContent>
                                <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                    Portfolio highlights will appear here once
                                    published.
                                </p>
                            </CardContent>
                        </Card>
                    ) : (
                        portfolio.slice(0, 3).map((item) => (
                            <Card key={item.id}>
                                <CardHeader>
                                    <CardTitle className="mt-4">
                                        {item.title}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    {item.featured_image_url ? (
                                        <div
                                            className="mb-4 h-40 w-full rounded-xl bg-cover bg-center"
                                            style={{
                                                backgroundImage: `url(${item.featured_image_url})`,
                                            }}
                                        />
                                    ) : null}
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
                <SectionHeader
                    eyebrow="Testimonials"
                    title="Trusted delivery partners"
                    subtitle="Feedback from teams I’ve supported across product and agency work."
                />
                <div className="mt-10 grid gap-6 md:grid-cols-3">
                    {testimonials.length === 0 ? (
                        <Card>
                            <CardContent>
                                <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                    Testimonials will appear here once
                                    published.
                                </p>
                            </CardContent>
                        </Card>
                    ) : (
                        testimonials.slice(0, 3).map((item) => (
                            <Card key={item.id}>
                                <CardHeader>
                                    <CardTitle>{item.client_name}</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                        “{item.quote}”
                                    </p>
                                    <p className="text-adb-navy-500 dark:text-adb-navy-400 mt-3 text-xs">
                                        {item.company}
                                    </p>
                                </CardContent>
                            </Card>
                        ))
                    )}
                </div>
            </Container>

            <Container>
                <SectionHeader
                    eyebrow="Latest news"
                    title="Delivery insights & updates"
                    subtitle="Fresh posts on delivery, automation, and scaling software projects."
                />
                <div className="mt-10 grid gap-6 md:grid-cols-3">
                    {blogPosts.length === 0 ? (
                        <Card>
                            <CardContent>
                                <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                    Blog posts will appear here once published.
                                </p>
                            </CardContent>
                        </Card>
                    ) : (
                        blogPosts.slice(0, 3).map((post) => (
                            <Card key={post.id}>
                                <CardHeader>
                                    <CardTitle>{post.title}</CardTitle>
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
                <SectionHeader
                    eyebrow="Locations"
                    title="Areas covered"
                    subtitle="Remote delivery across the UK with flexible collaboration."
                />
                <div className="mt-8 grid gap-4 md:grid-cols-3">
                    {["London", "Manchester", "Birmingham", "Leeds", "Bristol", "Edinburgh"].map(
                        (city) => (
                            <Card key={city}>
                                <CardContent>
                                    <p className="text-adb-navy-700 dark:text-adb-navy-200 text-sm">
                                        {city}
                                    </p>
                                </CardContent>
                            </Card>
                        ),
                    )}
                </div>
            </Container>

            <Container>
                <SectionHeader
                    eyebrow="Next steps"
                    title="Tell me about your delivery goals"
                    subtitle="I’ll respond with a clear proposal and recommended path forward."
                />
                <div className="mt-6">
                    <ButtonLink href="/contact" size="lg">
                        Start a project
                    </ButtonLink>
                </div>
            </Container>

            <JsonLd data={jsonLd} />
        </div>
    );
}
