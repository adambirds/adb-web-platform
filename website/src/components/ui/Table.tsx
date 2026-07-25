import { cn } from "@/lib/utils/cn";
import { HTMLAttributes } from "react";

export function Table({
    className,
    ...props
}: HTMLAttributes<HTMLTableElement>) {
    return (
        <div className="border-adb-navy-200 dark:border-adb-navy-800 overflow-hidden rounded-2xl border">
            <table
                className={cn(
                    "text-adb-navy dark:text-adb-navy-100 w-full border-collapse text-left text-sm",
                    className,
                )}
                {...props}
            />
        </div>
    );
}

export function TableHead({
    className,
    ...props
}: HTMLAttributes<HTMLTableSectionElement>) {
    return (
        <thead
            className={cn(
                "bg-adb-navy-50 dark:bg-adb-navy-900 text-xs uppercase",
                className,
            )}
            {...props}
        />
    );
}

export function TableRow({
    className,
    ...props
}: HTMLAttributes<HTMLTableRowElement>) {
    return (
        <tr
            className={cn(
                "border-adb-navy-200 dark:border-adb-navy-800 border-b last:border-b-0",
                className,
            )}
            {...props}
        />
    );
}

export function TableCell({
    className,
    ...props
}: HTMLAttributes<HTMLTableCellElement>) {
    return <td className={cn("px-4 py-3", className)} {...props} />;
}

export function TableHeaderCell({
    className,
    ...props
}: HTMLAttributes<HTMLTableCellElement>) {
    return (
        <th className={cn("px-4 py-3 font-semibold", className)} {...props} />
    );
}
