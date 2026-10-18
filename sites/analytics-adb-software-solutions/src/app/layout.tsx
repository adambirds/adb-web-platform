import type {Metadata} from "next";
import "./globals.css";
import {LegalLinks} from "./legal-page";
export const metadata: Metadata = {
    title: "ADB Analytics",
    description: "Search visibility and website engagement, together.",
    robots: {index: false, follow: false},
};
export default function RootLayout({
    children,
}: Readonly<{children: React.ReactNode}>) {
    return (
        <html lang="en-GB">
            <body>
                {children}
                <LegalLinks />
            </body>
        </html>
    );
}
