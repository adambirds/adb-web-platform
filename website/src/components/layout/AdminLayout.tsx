"use client";

import { useAuth } from "@/contexts/AuthContext";
import { ReactNode } from "react";
import { Footer } from "./Footer";
import { Header } from "./Header";

export function AdminLayout({ children }: { children: ReactNode }) {
    const { isAuthenticated, isLoading, user } = useAuth();

    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="text-center">
                    <div className="border-adb-navy border-t-adb-cyan inline-block h-8 w-8 animate-spin rounded-full border-4"></div>
                    <p className="text-adb-navy mt-4">Loading...</p>
                </div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return (
            <div className="dark:bg-adb-navy-950 flex h-screen items-center justify-center bg-white">
                <div className="text-center">
                    <h1 className="text-adb-navy text-2xl font-bold">
                        Access Denied
                    </h1>
                    <p className="text-adb-navy-600 dark:text-adb-navy-300 mt-2">
                        You must be logged in to access this page.
                    </p>
                    <a
                        href="http://localhost:5175/login"
                        className="bg-adb-cyan text-adb-navy-950 hover:bg-adb-cyan-600 mt-4 inline-block rounded-lg px-6 py-2 font-medium transition"
                    >
                        Go to Login
                    </a>
                </div>
            </div>
        );
    }

    return (
        <div className="dark:bg-adb-navy-950 flex min-h-screen flex-col bg-white">
            <Header />
            <main className="flex-grow">{children}</main>
            <Footer />
        </div>
    );
}
