import type { ReactNode } from "react";
import { siteMetadata } from "@adb/ui/public/server";
import { site } from "@/content/site";
import "./globals.css";
import { Analytics } from "@/components/public/Analytics";
export const metadata = siteMetadata(site);
export default function RootLayout({ children }: { children: ReactNode }) {
    return (
        <html lang="en">
            <body>
                {children}
                <Analytics
                    measurementId={
                        process.env.GA4_WEB_DESIGNS_MEASUREMENT_ID || ""
                    }
                />
            </body>
        </html>
    );
}
