"use client";

import { useAuth } from "@/contexts/AuthContext";
import Link from "next/link";

interface AdminLink {
    label: string;
    href: string;
    permissions?: string[];
}

const adminLinks: AdminLink[] = [
    { label: "Dashboard", href: "/admin" },
    {
        label: "Clients",
        href: "/admin/clients",
        permissions: ["clients.view_client"],
    },
    {
        label: "Projects",
        href: "/admin/projects",
        permissions: ["clients.view_project"],
    },
    {
        label: "Leads",
        href: "/admin/leads",
        permissions: ["crm.view_lead"],
    },
    {
        label: "Content",
        href: "/admin/content",
        permissions: [
            "website.view_blogpost",
            "website.view_testimonial",
            "website.view_faq",
            "website.view_portfolio",
        ],
    },
    {
        label: "Infrastructure",
        href: "/admin/infrastructure",
        permissions: [
            "infrastructure.view_server",
            "infrastructure.view_database",
            "infrastructure.view_website",
            "infrastructure.view_domain",
            "infrastructure.view_application",
        ],
    },
    {
        label: "Credentials",
        href: "/admin/credentials",
        permissions: ["credentials.view_storedcredential"],
    },
    {
        label: "Time tracking",
        href: "/admin/time-tracking",
        permissions: ["clients.view_timeentry"],
    },
];

export function Header() {
    const { isAuthenticated, hasPermission } = useAuth();

    const visibleLinks = adminLinks.filter(
        (link) =>
            !link.permissions ||
            link.permissions.some((permission) => hasPermission(permission)),
    );

    return (
        <header className="sticky top-0 z-50 border-b border-adb-navy-200/20 bg-white/90 backdrop-blur-lg dark:border-adb-cyan-950 dark:bg-adb-navy-950/90">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="flex min-h-16 items-center justify-between gap-6 py-3">
                    <Link
                        href="/admin"
                        className="shrink-0 text-lg font-bold text-adb-navy dark:text-white"
                    >
                        ADB Admin
                    </Link>

                    {isAuthenticated ? (
                        <nav className="flex flex-wrap justify-end gap-x-5 gap-y-2">
                            {visibleLinks.map((link) => (
                                <Link
                                    key={link.href}
                                    href={link.href}
                                    className="text-sm font-medium text-adb-navy transition hover:text-adb-cyan dark:text-adb-navy-100 dark:hover:text-adb-cyan"
                                >
                                    {link.label}
                                </Link>
                            ))}
                        </nav>
                    ) : null}
                </div>
            </div>
        </header>
    );
}
