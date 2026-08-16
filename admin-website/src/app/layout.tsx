import { Providers } from "@/providers";
import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
    title: {
        default: "ADB Software Solutions",
        template: "%s | ADB Software Solutions",
    },
    description:
        "Senior software engineer delivering agency-level work with direct collaboration.",
    metadataBase: new URL("https://adbsoftwaresolutions.co.uk"),
    openGraph: {
        type: "website",
        locale: "en_GB",
        url: "https://adbsoftwaresolutions.co.uk",
        title: "ADB Software Solutions",
        description: "Senior software engineer delivering agency-level work",
        siteName: "ADB Software Solutions",
    },
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" suppressHydrationWarning>
            <head>
                <link
                    rel="icon"
                    type="image/png"
                    href="/favicon-96x96.png"
                    sizes="96x96"
                />
                <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
                <link rel="shortcut icon" href="/favicon.ico" />
                <link
                    rel="apple-touch-icon"
                    sizes="180x180"
                    href="/apple-touch-icon.png"
                />
                <meta
                    name="apple-mobile-web-app-title"
                    content="ADB Software Solutions"
                />
                <link rel="manifest" href="/site.webmanifest" />
            </head>
            <body className="text-adb-navy dark:bg-adb-navy-950 dark:text-adb-navy-100 min-h-screen bg-white">
                <Providers>{children}</Providers>
            </body>
        </html>
    );
}
