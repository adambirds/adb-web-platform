"use client";

import { useAuth } from "@/contexts/AuthContext";
import Link from "next/link";

const adminLinks = [
    ["Dashboard", "/admin"],
    ["Clients", "/admin/clients"],
    ["Projects", "/admin/projects"],
    ["Leads", "/admin/leads"],
    ["Content", "/admin/content"],
    ["Infrastructure", "/admin/infrastructure"],
    ["Credentials", "/admin/credentials"],
    ["Time tracking", "/admin/time-tracking"],
] as const;

export function Header() {
    const { isAuthenticated } = useAuth();

    return (
        <header className="sticky top-0 z-50 border-b border-adb-navy-200/20 bg-white/90 backdrop-blur-lg dark:border-adb-cyan-950 dark:bg-adb-navy-950/90">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="flex min-h-16 items-center justify-between gap-6 py-3">
                    <Link href="/admin" className="shrink-0 text-lg font-bold text-adb-navy dark:text-white">
                        ADB Admin
                    </Link>

                    {isAuthenticated ? (
                        <nav className="flex flex-wrap justify-end gap-x-5 gap-y-2">
                            {adminLinks.map(([label, href]) => (
                                <Link
                                    key={href}
                                    href={href}
                                    className="text-sm font-medium text-adb-navy transition hover:text-adb-cyan dark:text-adb-navy-100 dark:hover:text-adb-cyan"
                                >
                                    {label}
                                </Link>
                            ))}
                        </nav>
                    ) : null}
                </div>
            </div>
        </header>
    );
}
