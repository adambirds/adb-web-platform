import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";

export function DataLoading({ label = "Loading data..." }: { label?: string }) {
    return (
        <div className="flex min-h-48 items-center justify-center rounded-xl border border-slate-800 bg-slate-900/40">
            <div className="text-center">
                <div className="inline-block h-7 w-7 animate-spin rounded-full border-4 border-slate-800 border-t-adb-cyan-400" />
                <p className="mt-3 text-sm text-slate-500">{label}</p>
            </div>
        </div>
    );
}

export function DataError({
    message,
    onRetry,
}: {
    message: string;
    onRetry?: () => void;
}) {
    return (
        <div className="rounded-xl border border-red-950 bg-red-950/20 p-5">
            <div className="flex items-start gap-3">
                <ExclamationTriangleIcon className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
                <div>
                    <h3 className="text-sm font-semibold text-red-200">
                        Unable to load data
                    </h3>
                    <p className="mt-1 text-sm text-red-300/70">{message}</p>
                    {onRetry ? (
                        <button
                            type="button"
                            onClick={onRetry}
                            className="mt-3 text-sm font-medium text-red-200 underline decoration-red-700 underline-offset-4 hover:text-white"
                        >
                            Try again
                        </button>
                    ) : null}
                </div>
            </div>
        </div>
    );
}
