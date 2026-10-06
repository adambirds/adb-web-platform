import Link from "next/link";
import { site } from "@/content/site";
export default function NotFound() {
    return (
        <main className="standalone-not-found">
            <p>{site.name}</p>
            <h1>Page not found</h1>
            <p>
                This address may have changed. You can browse the services or
                start from the homepage.
            </p>
            <nav>
                <Link href="/">Home</Link>
                <Link href="/services/">Services</Link>
                <Link href="/contact/">Contact</Link>
            </nav>
        </main>
    );
}
