import { cn } from "@/lib/utils/cn";
import { HTMLAttributes } from "react";

export function Badge({
    className,
    ...props
}: HTMLAttributes<HTMLSpanElement>) {
    return (
        <span
            className={cn(
                "border-adb-navy-200 dark:border-adb-navy-800 dark:bg-adb-navy-900 text-adb-navy dark:text-adb-navy-100 inline-flex items-center rounded-full border bg-white px-3 py-1 text-xs font-medium",
                className,
            )}
            {...props}
        />
    );
}
