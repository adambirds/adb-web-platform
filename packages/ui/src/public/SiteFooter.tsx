import Link from "next/link";
import type {PublicSite} from "./types";

export function SiteFooter({
    site,
    hasWork,
    hasBlog,
    hasFAQs,
    hasTestimonials,
}: {
    site: PublicSite;
    hasWork: boolean;
    hasBlog: boolean;
    hasFAQs: boolean;
    hasTestimonials: boolean;
}) {
    const brands = [
        {name: "ADB Web Designs", url: "https://adbwebdesigns.co.uk"},
        {
            name: "ADB Software Solutions",
            url: "https://adbsoftwaresolutions.co.uk",
        },
        {name: "ADB Technology", url: "https://adbtechnology.co.uk"},
    ];
    return (
        <footer className="site-footer">
            <div className="shell">
                <div className="footer-grid">
                    <div>
                        <Link href="/" className="footer-name">
                            {site.name}
                        </Link>
                        <p>
                            Freelance. Manchester-based.
                            <br />
                            Working further afield.
                        </p>
                    </div>
                    <nav aria-label="More about the business">
                        <Link href="/working-together/">Working together</Link>
                        <Link href="/areas-served/">Areas served</Link>
                        {hasWork ? (
                            <Link href="/portfolio/">Portfolio</Link>
                        ) : null}
                        {hasBlog ? <Link href="/blog/">Blog</Link> : null}
                        {hasFAQs ? <Link href="/faqs/">FAQs</Link> : null}
                        {hasTestimonials ? (
                            <Link href="/testimonials/">Client feedback</Link>
                        ) : null}
                        <Link href="/contact/">Contact</Link>
                    </nav>
                    <nav aria-label="Related ADB businesses">
                        {brands
                            .filter((brand) => brand.url !== site.domain)
                            .map((brand) => (
                                <a key={brand.url} href={brand.url}>
                                    {brand.name} ↗
                                </a>
                            ))}
                    </nav>
                </div>
                <div className="footer-bottom">
                    <p>
                        © {new Date().getFullYear()} {site.name}
                    </p>
                    <nav aria-label="Policies">
                        <Link href="/privacy-policy/">Privacy</Link>
                        <Link href="/cookie-policy/">Cookies</Link>
                        <Link href="/terms/">Website terms</Link>
                    </nav>
                </div>
            </div>
        </footer>
    );
}
