import { AdminLayout } from "@/components/layout/AdminLayout";
import { Providers } from "@/providers";
import type { Metadata } from "next";
import type { ReactNode } from "react";
export const metadata: Metadata = {
    title: {
        default: "ADB Business Platform",
        template: "%s | ADB Business Platform",
    },
    description: "Internal operations workspace for the ADB businesses.",
    alternates: { canonical: null },
    openGraph: null,
    twitter: null,
    robots: { index: false, follow: false, nocache: true },
};
export default function Layout({ children }: { children: ReactNode }) {
    return (
        <Providers>
            <AdminLayout>{children}</AdminLayout>
        </Providers>
    );
}
