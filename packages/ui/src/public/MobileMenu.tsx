"use client";
import Link from "next/link";
export function MobileMenu({links}: {links: {title: string; href: string}[]}) {
    return (
        <details className="mobile-menu">
            <summary>
                Menu <span aria-hidden="true">☰</span>
            </summary>
            <nav aria-label="Mobile navigation">
                {[
                    ...links,
                    {title: "Contact", href: "/contact/"},
                    {title: "Working together", href: "/working-together/"},
                ].map((link) => (
                    <Link
                        key={link.href}
                        href={link.href}
                        onClick={(event) => {
                            const menu = event.currentTarget.closest("details");
                            if (menu) menu.open = false;
                        }}
                    >
                        {link.title}
                    </Link>
                ))}
            </nav>
        </details>
    );
}
