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
        <html lang="en" suppressHydrationWarning>
            <body className="text-adb-navy dark:bg-adb-navy-950 dark:text-adb-navy-100 min-h-screen bg-white">
                <Providers>{children}</Providers>
            </body>
        </html>
    );
}
