import type {Metadata} from "next";
import "../index.css";
import Providers from "./providers";

export const metadata: Metadata = {
    title: {
        default: "ADB Software Solutions Account",
        template: "%s | ADB Software Solutions",
    },
    description: "Secure authentication and account management for ADB services.",
    robots: {
        index: false,
        follow: false,
        nocache: true,
    },
};

export default function RootLayout({children}: {children: React.ReactNode}) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body>
                <Providers>{children}</Providers>
            </body>
        </html>
    );
}
