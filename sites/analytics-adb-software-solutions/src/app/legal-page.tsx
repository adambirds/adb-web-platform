import Link from "next/link";
import type {ReactNode} from "react";

export function LegalLinks() {
    return (
        <nav className="legal-links" aria-label="Policies">
            <Link href="/privacy">Privacy</Link>
            <Link href="/terms">Terms</Link>
        </nav>
    );
}

export function LegalPage({
    title,
    children,
}: {
    title: string;
    children: ReactNode;
}) {
    return (
        <main className="legal-page">
            <Link href="/">ADB Analytics</Link>
            <article>
                <p className="eyebrow">Personal-use workspace</p>
                <h1>{title}</h1>
                <p>Last updated: 18 October 2026</p>
                {children}
            </article>
        </main>
    );
}
