"use client";

import { ButtonLink } from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import Link from "next/link";

export function Header() {
    const { isAuthenticated, user } = useAuth();

    return (
        <header className="border-adb-navy-200/20 dark:border-adb-cyan-950 dark:bg-adb-navy-950/80 sticky top-0 z-50 border-b bg-white/80 backdrop-blur-lg">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between py-4">
                    <Link href="/" className="flex items-center space-x-2">
                        <div className="text-2xl font-bold">
                            <span className="text-adb-navy">ADB</span>
                        </div>
                    </Link>

                    <nav className="hidden space-x-8 md:flex">
                        <Link
                            href="/about"
                            className="text-adb-navy hover:text-adb-cyan dark:text-adb-navy-100 dark:hover:text-adb-cyan text-sm font-medium transition"
                        >
                            About
                        </Link>
                        <Link
                            href="/services"
                            className="text-adb-navy hover:text-adb-cyan dark:text-adb-navy-100 dark:hover:text-adb-cyan text-sm font-medium transition"
                        >
                            Services
                        </Link>
                        <Link
                            href="/portfolio"
                            className="text-adb-navy hover:text-adb-cyan dark:text-adb-navy-100 dark:hover:text-adb-cyan text-sm font-medium transition"
                        >
                            Portfolio
                        </Link>
                        <Link
                            href="/blog"
                            className="text-adb-navy hover:text-adb-cyan dark:text-adb-navy-100 dark:hover:text-adb-cyan text-sm font-medium transition"
                        >
                            Blog
                        </Link>
                        <Link
                            href="/faqs"
                            className="text-adb-navy hover:text-adb-cyan dark:text-adb-navy-100 dark:hover:text-adb-cyan text-sm font-medium transition"
                        >
                            FAQs
                        </Link>
                        <Link
                            href="/contact"
                            className="text-adb-navy hover:text-adb-cyan dark:text-adb-navy-100 dark:hover:text-adb-cyan text-sm font-medium transition"
                        >
                            Contact
                        </Link>
                    </nav>

                    <div className="flex items-center space-x-4">
                        {isAuthenticated ? (
                            <ButtonLink href="/admin" size="md">
                                Admin
                            </ButtonLink>
                        ) : (
                            <ButtonLink
                                href="http://localhost:5175/login"
                                size="md"
                            >
                                Login
                            </ButtonLink>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}
