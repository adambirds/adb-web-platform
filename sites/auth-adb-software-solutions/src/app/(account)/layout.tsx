"use client";

import LogoComponent from "@/components/logo/LogoComponent";
import {useAuth} from "@/contexts/AuthContext";
import {usePathname, useRouter} from "next/navigation";
import {useEffect} from "react";

export default function AccountLayout({children}: {children: React.ReactNode}) {
    const {user, loading} = useAuth();
    const pathname = usePathname();
    const router = useRouter();

    useEffect(() => {
        if (loading || user) {
            return;
        }

        const search = window.location.search;
        const next = encodeURIComponent(`${pathname}${search}`);
        router.replace(`/login?next=${next}`);
    }, [loading, pathname, router, user]);

    if (loading || !user) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-white dark:bg-slate-900">
                <div className="border-brand h-8 w-8 animate-spin rounded-full border-4 border-t-transparent" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
            <header className="border-b border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800">
                <div className="mx-auto flex h-20 max-w-9/12 items-center justify-between px-4 sm:px-6 lg:px-8">
                    <LogoComponent className="h-16 w-auto" />
                    <div className="flex items-center gap-4">
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                            {user.email}
                        </span>
                        <a
                            href="/logout"
                            className="text-brand text-sm font-medium hover:underline"
                        >
                            Sign out
                        </a>
                    </div>
                </div>
            </header>

            <main className="mx-auto max-w-9/12 px-4 py-8 sm:px-6 lg:px-8">
                {children}
            </main>
        </div>
    );
}
