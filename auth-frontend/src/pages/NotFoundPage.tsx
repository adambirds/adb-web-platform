export default function NotFoundPage() {
    return (
        <div className="flex min-h-screen items-center justify-center bg-white px-6 py-12 dark:bg-slate-900">
            <div className="text-center">
                <p className="text-sm font-semibold text-brand">404</p>
                <h1 className="mt-4 text-3xl font-bold tracking-tight text-slate-900 sm:text-5xl dark:text-white">
                    Page not found
                </h1>
                <p className="mt-6 text-base leading-7 text-slate-600 dark:text-slate-400">
                    Sorry, we couldn't find the page you're looking for.
                </p>
                <div className="mt-10">
                    <a
                        href="/login"
                        className="text-sm font-semibold text-brand hover:underline"
                    >
                        Go to login <span aria-hidden="true">&rarr;</span>
                    </a>
                </div>
            </div>
        </div>
    );
}
