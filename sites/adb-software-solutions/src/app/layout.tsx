import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
    title: {
        default: "ADB Software Solutions",
        template: "%s | ADB Software Solutions",
    },
    description:
        "Bespoke software, integrations, automation, and digital products from ADB Software Solutions.",
    metadataBase: new URL("https://adbsoftwaresolutions.co.uk"),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
}
