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
                "flex flex-col items-start gap-2 rounded-xl border border-dashed border-slate-700 bg-slate-900/40 p-6",
                className,
            )}
        >
            <h3 className="text-base font-semibold text-slate-100">{title}</h3>
            {description ? (
                <p className="max-w-2xl text-sm leading-6 text-slate-500">
                    {description}
                </p>
            ) : null}
            {action ? <div className="mt-3">{action}</div> : null}
        </div>
    );
}
