import { cn } from "@/lib/utils/cn";
import { HTMLAttributes } from "react";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
    return (
        <div
            className={cn(
                "rounded-xl border border-slate-800 bg-slate-900/70 shadow-sm shadow-black/10",
                className,
            )}
            {...props}
        />
    );
}

export function CardHeader({
    className,
    ...props
}: HTMLAttributes<HTMLDivElement>) {
    return <div className={cn("p-5", className)} {...props} />;
}

export function CardContent({
    className,
    ...props
}: HTMLAttributes<HTMLDivElement>) {
    return <div className={cn("px-5 pb-5", className)} {...props} />;
}

export function CardFooter({
    className,
    ...props
}: HTMLAttributes<HTMLDivElement>) {
    return (
        <div
            className={cn("border-t border-slate-800 px-5 py-4", className)}
            {...props}
        />
    );
}

export function CardTitle({
    className,
    ...props
}: HTMLAttributes<HTMLHeadingElement>) {
    return (
        <h3
            className={cn("text-sm font-semibold text-slate-100", className)}
            {...props}
        />
    );
}

export function CardDescription({
    className,
    ...props
}: HTMLAttributes<HTMLParagraphElement>) {
    return (
        <p
            className={cn("mt-1 text-sm text-slate-500", className)}
            {...props}
        />
    );
}
