import type { ReactNode } from "react";
import { siteMetadata } from "@adb/ui/public/server";
import { site } from "@/content/site";
import "./globals.css";
export const metadata = siteMetadata(site);
export default function RootLayout({ children }: { children: ReactNode }) {
    return (
        <html lang="en" className="dark" suppressHydrationWarning>
            <body className="min-h-screen bg-slate-950 text-slate-200 antialiased">
                {children}
            </body>
        </html>
    );
}
