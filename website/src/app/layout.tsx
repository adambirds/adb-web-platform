import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
    title: "Project Template",
};

export default async function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="h-full" suppressHydrationWarning>
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
                    content="Project Template"
                />
                <link rel="manifest" href="/site.webmanifest" />
            </head>
            <body className="h-full bg-gray-900 text-gray-200">{children}</body>
        </html>
    );
}
