import { cn } from "@/lib/utils/cn";
import { HTMLAttributes } from "react";

export function Badge({
    className,
    ...props
}: HTMLAttributes<HTMLSpanElement>) {
    return (
        <span
            className={cn(
                "inline-flex items-center rounded-full border border-slate-700 bg-slate-800/70 px-2.5 py-1 text-xs font-medium text-slate-300",
                className,
            )}
            {...props}
        />
    );
}
