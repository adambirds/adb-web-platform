import { Providers } from "@/providers";
import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
    title: {
        default: "ADB Business Platform",
        template: "%s | ADB Business Platform",
    },
    description: "Internal administration platform for the ADB businesses.",
    robots: {
        index: false,
        follow: false,
        nocache: true,
    },
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="dark" suppressHydrationWarning>
            <body className="min-h-screen bg-slate-950 text-slate-200 antialiased">
                <Providers>{children}</Providers>
            </body>
        </html>
    );
}
