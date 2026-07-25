"use client";

import { ReactNode } from "react";
import { Footer } from "./Footer";
import { Header } from "./Header";

export function MarketingLayout({ children }: { children: ReactNode }) {
    return (
        <div className="dark:bg-adb-navy-950 flex min-h-screen flex-col bg-white">
            <Header />
            <main className="flex-grow">{children}</main>
            <Footer />
        </div>
    );
}
