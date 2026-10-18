import type {Metadata} from "next";
import "./globals.css";
import "./advanced.css";
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
        <html lang="en-GB" suppressHydrationWarning>
            <body>
                <script
                    dangerouslySetInnerHTML={{
                        __html: `try{var t=localStorage.getItem('adb-analytics-theme');document.documentElement.dataset.theme=t==='dark'||(!t&&matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light'}catch(e){}`,
                    }}
                />
                {children}
                <LegalLinks />
            </body>
        </html>
    );
}
