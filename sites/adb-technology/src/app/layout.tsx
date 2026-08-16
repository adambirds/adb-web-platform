import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
    title: {
        default: "ADB Technology",
        template: "%s | ADB Technology",
    },
    description:
        "DevOps, IT consultancy, infrastructure, cloud, and technical support from ADB Technology.",
    metadataBase: new URL("https://adbtechnology.co.uk"),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
}
