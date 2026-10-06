import type { ReactNode } from "react";
import { siteMetadata } from "@adb/ui/public/server";
import { site } from "@/content/site";
import "./globals.css";
export const metadata = siteMetadata(site);
export default function RootLayout({ children }: { children: ReactNode }) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
}
