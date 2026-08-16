import Link from "next/link";

export default function HomePage() {
    return (
        <main className="flex min-h-screen items-center justify-center bg-white px-6 dark:bg-adb-navy-950">
            <div className="max-w-xl text-center">
                <h1 className="text-3xl font-semibold text-adb-navy dark:text-white">
                    ADB Software Solutions Admin
                </h1>
                <p className="mt-4 text-adb-navy-600 dark:text-adb-navy-300">
                    This application now serves the internal administration platform.
                </p>
                <div className="mt-8 flex justify-center gap-3">
                    <Link
                        href="/admin"
                        className="rounded-lg bg-adb-cyan px-5 py-3 font-medium text-adb-navy-950 transition hover:bg-adb-cyan-600"
                    >
                        Open admin
                    </Link>
                    <a
                        href="http://localhost:5175/login"
                        className="rounded-lg border border-adb-navy-200 px-5 py-3 font-medium text-adb-navy transition hover:border-adb-cyan dark:border-adb-navy-700 dark:text-white"
                    >
                        Sign in
                    </a>
                </div>
            </div>
        </main>
    );
}
