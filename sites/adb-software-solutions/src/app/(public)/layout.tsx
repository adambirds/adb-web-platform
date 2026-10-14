import { connection } from "next/server";
import { Analytics } from "@adb/ui/public/Analytics";
import { SiteHeader } from "@adb/ui/public/SiteHeader";
import { SiteFooter } from "@adb/ui/public/SiteFooter";
import { JsonLd } from "@adb/ui/public/JsonLd";
import { homeContent, businessSchema } from "@adb/ui/public/server";
import { site } from "@/content/site";
import type { ReactNode } from "react";
import "@/styles/public.css";

export default async function PublicLayout({
    children,
}: {
    children: ReactNode;
}) {
    // Read runtime configuration after the request boundary, not during image builds.
    await connection();
    const content = await homeContent(site);
    return (
        <div
            className={`marketing brand-${site.kind} brand-family`}
            data-theme="dark"
            suppressHydrationWarning
        >
            <JsonLd data={businessSchema(site)} />
            <Analytics
                measurementId={
                    process.env.GA4_SOFTWARE_SOLUTIONS_MEASUREMENT_ID || ""
                }
            />
            <SiteHeader
                site={site}
                hasWork={Boolean(content.work.total)}
                hasBlog={Boolean(content.articles.total)}
            />
            <main id="main">{children}</main>
            <SiteFooter
                site={site}
                hasWork={Boolean(content.work.total)}
                hasBlog={Boolean(content.articles.total)}
                hasFAQs={Boolean(content.faqs.total)}
                hasTestimonials={Boolean(content.testimonials.total)}
            />
        </div>
    );
}
