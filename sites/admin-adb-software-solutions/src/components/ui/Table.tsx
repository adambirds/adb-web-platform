import { cn } from "@/lib/utils/cn";
import { HTMLAttributes } from "react";

export function Table({
    className,
    ...props
}: HTMLAttributes<HTMLTableElement>) {
    return (
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
            <table
                className={cn(
                    "w-full min-w-[720px] border-collapse text-left text-sm text-slate-300",
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
                "border-b border-slate-800 bg-slate-950/70 text-[11px] tracking-wide text-slate-500 uppercase",
                className,
            )}
            {...props}
        />
    );
}

export function TableBody({
    className,
    ...props
}: HTMLAttributes<HTMLTableSectionElement>) {
    return <tbody className={cn("divide-y divide-slate-800", className)} {...props} />;
}

export function TableRow({
    className,
    ...props
}: HTMLAttributes<HTMLTableRowElement>) {
    return (
        <tr
            className={cn(
                "transition-colors hover:bg-slate-800/40",
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
    return <td className={cn("px-4 py-3.5 align-middle", className)} {...props} />;
}

export function TableHeaderCell({
    className,
    ...props
}: HTMLAttributes<HTMLTableCellElement>) {
    return (
        <th
            className={cn("px-4 py-3 font-semibold", className)}
            {...props}
        />
    );
}
