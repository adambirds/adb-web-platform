import { ContactForm } from "@/components/marketing/ContactForm";
import { JsonLd } from "@/components/seo/JsonLd";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Container,
    SectionHeader,
} from "@/components/ui";
import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Contact",
    description:
        "Contact ADB Software Solutions to discuss web delivery, automation, or engineering support.",
    alternates: {
        canonical: "/contact",
    },
    openGraph: {
        title: "Contact | ADB Software Solutions",
        description:
            "Contact ADB Software Solutions to discuss web delivery, automation, or engineering support.",
        url: "/contact",
    },
};

export default function ContactPage() {
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
                name: "Contact",
                item: "https://adbsoftwaresolutions.co.uk/contact",
            },
        ],
    };

    const contactSchema = {
        "@context": "https://schema.org",
        "@type": "ContactPage",
        name: "Contact ADB Software Solutions",
        url: "https://adbsoftwaresolutions.co.uk/contact",
    };

    return (
        <div className="space-y-16 pt-10 pb-24">
            <Container>
                <SectionHeader
                    eyebrow="Contact"
                    title="Tell me about your project"
                    subtitle="I’ll reply with a clear plan and next steps."
                />
            </Container>

            <Container>
                <div className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
                    <Card>
                        <CardHeader>
                            <CardTitle>Start a conversation</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ContactForm />
                        </CardContent>
                    </Card>
                    <Card className="bg-adb-navy-950 text-white">
                        <CardHeader>
                            <CardTitle className="text-white">
                                What happens next
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ol className="text-adb-navy-200 space-y-3 text-sm">
                                <li>1. I review your goals and context.</li>
                                <li>2. We schedule a short discovery call.</li>
                                <li>
                                    3. You receive a delivery plan and timeline.
                                </li>
                            </ol>
                        </CardContent>
                    </Card>
                </div>
            </Container>
            <JsonLd data={[breadcrumbs, contactSchema]} />
        </div>
    );
}
