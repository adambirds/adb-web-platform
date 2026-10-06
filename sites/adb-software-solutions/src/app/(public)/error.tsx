"use client";
import Link from "next/link";
export default function PublicError({ reset }: { reset: () => void }) {
    return (
        <section className="shell public-error">
            <h1>This page could not be loaded</h1>
            <p>Please try again, or get in touch about your project.</p>
            <div className="hero-actions">
                <button className="angled-button" type="button" onClick={reset}>
                    Try again
                </button>
                <Link className="text-link" href="/contact/">
                    Contact →
                </Link>
            </div>
        </section>
    );
}
