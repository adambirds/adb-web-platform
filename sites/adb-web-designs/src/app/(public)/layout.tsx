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
    const content = await homeContent(site);
    return (
        <div
            className={`marketing brand-${site.kind}`}
            data-theme="dark"
            suppressHydrationWarning
        >
            <JsonLd data={businessSchema(site)} />
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
