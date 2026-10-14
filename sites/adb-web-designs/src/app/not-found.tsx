import Link from "next/link";
import { SiteHeader } from "@adb/ui/public/SiteHeader";
import { SiteFooter } from "@adb/ui/public/SiteFooter";
import { site } from "@/content/site";
import "@/styles/public.css";

export default function NotFound() {
    return (
        <div
            className="marketing brand-web brand-family"
            data-theme="dark"
            suppressHydrationWarning
        >
            <SiteHeader site={site} hasWork={false} hasBlog={false} />
            <main id="main" className="shell web-thank-you">
                <p className="business-label">404 / Page not found</p>
                <h1>A different way back.</h1>
                <p>
                    This address may have changed. Browse the services or start
                    from the homepage.
                </p>
                <nav className="web-not-found-links" aria-label="Find your way">
                    <Link className="angled-button" href="/">
                        Home ↗
                    </Link>
                    <Link className="text-link" href="/services/">
                        Services ↗
                    </Link>
                    <Link className="text-link" href="/contact/">
                        Contact ↗
                    </Link>
                </nav>
            </main>
            <SiteFooter
                site={site}
                hasWork={false}
                hasBlog={false}
                hasFAQs={false}
                hasTestimonials={false}
            />
        </div>
    );
}
