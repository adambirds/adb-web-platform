import { cn } from "@/lib/utils/cn";
import { TextareaHTMLAttributes, forwardRef } from "react";

export const Textarea = forwardRef<
    HTMLTextAreaElement,
    TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
    <textarea
        ref={ref}
        className={cn(
            "border-adb-navy-200 dark:border-adb-navy-800 dark:bg-adb-navy-900 dark:text-adb-navy-100 text-adb-navy placeholder:text-adb-navy-400 focus-visible:ring-adb-cyan w-full rounded-lg border bg-white px-3 py-2 text-sm focus-visible:ring-2 focus-visible:outline-none",
            className,
        )}
        {...props}
    />
));

Textarea.displayName = "Textarea";
