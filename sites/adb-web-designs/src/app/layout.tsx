import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
    title: {
        default: "ADB Web Designs",
        template: "%s | ADB Web Designs",
    },
    description:
        "Website design, development, hosting, rescue, and ongoing support from ADB Web Designs.",
    metadataBase: new URL("https://adbwebdesigns.co.uk"),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
}
