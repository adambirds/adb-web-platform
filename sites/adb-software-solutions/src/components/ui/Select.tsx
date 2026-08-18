import { cn } from "@/lib/utils/cn";
import { SelectHTMLAttributes, forwardRef } from "react";

export const Select = forwardRef<
    HTMLSelectElement,
    SelectHTMLAttributes<HTMLSelectElement>
>(({ className, ...props }, ref) => (
    <select
        ref={ref}
        className={cn(
            "border-adb-navy-200 dark:border-adb-navy-800 dark:bg-adb-navy-900 dark:text-adb-navy-100 text-adb-navy focus-visible:ring-adb-cyan w-full rounded-lg border bg-white px-3 py-2 text-sm focus-visible:ring-2 focus-visible:outline-none",
            className,
        )}
        {...props}
    />
));

Select.displayName = "Select";
