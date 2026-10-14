import Image from "next/image";
import Link from "next/link";
import {MobileMenu} from "./MobileMenu";
import {ThemeToggle} from "./ThemeToggle";
import type {PublicSite} from "./types";

export function SiteHeader({
    site,
    hasWork,
    hasBlog,
    darkLogoSrc = "/brand/logo-dark.png",
}: {
    site: PublicSite;
    hasWork: boolean;
    hasBlog: boolean;
    darkLogoSrc?: string;
}) {
    const links = [
        {title: "Services", href: "/services/"},
        ...(hasWork ? [{title: "Work", href: "/portfolio/"}] : []),
        {title: "About", href: "/about/"},
        ...(hasBlog ? [{title: "Blog", href: "/blog/"}] : []),
    ];
    return (
        <>
            <a href="#main" className="skip-link">
                Skip to content
            </a>
            <header className="site-header">
                <div className="shell header-inner">
                    <Link
                        href="/"
                        className="logo-link"
                        aria-label={`${site.name} home`}
                    >
                        <Image
                            className="logo-light"
                            src="/brand/logo-light.png"
                            alt={site.name}
                            width={132}
                            height={62}
                            priority
                        />
                        <Image
                            className="logo-dark"
                            src={darkLogoSrc}
                            alt={site.name}
                            width={132}
                            height={62}
                            priority
                        />
                    </Link>
                    <nav
                        className="desktop-navigation"
                        aria-label="Main navigation"
                    >
                        {links.map((link) => (
                            <Link href={link.href} key={link.href}>
                                {link.title}
                            </Link>
                        ))}
                    </nav>
                    <div className="header-controls">
                        <ThemeToggle />
                        <Link className="header-cta" href="/contact/">
                            Let’s talk <span aria-hidden="true">↗</span>
                        </Link>
                        <MobileMenu links={links} />
                    </div>
                </div>
            </header>
        </>
    );
}
