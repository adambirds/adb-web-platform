import { cn } from "@/lib/utils/cn";
import { ReactNode } from "react";

interface EmptyStateProps {
    title: string;
    description?: string;
    action?: ReactNode;
    className?: string;
}

export function EmptyState({
    title,
    description,
    action,
    className,
}: EmptyStateProps) {
    return (
        <div
            className={cn(
                "border-adb-navy-200 dark:border-adb-navy-800 dark:bg-adb-navy-900 flex flex-col items-start gap-2 rounded-2xl border bg-white p-6",
                className,
            )}
        >
            <h3 className="text-adb-navy dark:text-adb-navy-100 text-lg font-semibold">
                {title}
            </h3>
            {description ? (
                <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                    {description}
                </p>
            ) : null}
            {action ? <div className="mt-3">{action}</div> : null}
        </div>
    );
}
