import { Metadata } from "next";

export const metadata: Metadata = {
    title: "Project Template",
    description: "A full-stack project template with authentication.",
};

export default function HomePage() {
    return (
        <div className="flex min-h-screen flex-col items-center justify-center">
            <main className="mx-auto max-w-4xl px-4 text-center">
                <h1 className="mb-6 text-5xl font-bold text-white">
                    Welcome to Your Project
                </h1>
                <p className="mb-8 text-xl text-gray-400">
                    A full-stack project template with Django backend and
                    Next.js frontend, including authentication.
                </p>
                <div className="flex flex-wrap justify-center gap-4">
                    <a
                        href="/api"
                        className="rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white transition-colors hover:bg-blue-700"
                    >
                        API Documentation
                    </a>
                    <a
                        href="https://github.com"
                        className="rounded-lg border border-gray-600 px-6 py-3 font-semibold text-gray-300 transition-colors hover:border-gray-500 hover:text-white"
                    >
                        View on GitHub
                    </a>
                </div>
            </main>
        </div>
    );
}
