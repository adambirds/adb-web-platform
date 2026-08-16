import { cn } from "@/lib/utils/cn";
import { HTMLAttributes } from "react";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
    return (
        <div
            className={cn(
                "border-adb-navy-200 dark:border-adb-navy-800 dark:bg-adb-navy-900 rounded-2xl border bg-white",
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
    return <div className={cn("p-6", className)} {...props} />;
}

export function CardContent({
    className,
    ...props
}: HTMLAttributes<HTMLDivElement>) {
    return <div className={cn("px-6 pb-6", className)} {...props} />;
}

export function CardFooter({
    className,
    ...props
}: HTMLAttributes<HTMLDivElement>) {
    return <div className={cn("px-6 pb-6", className)} {...props} />;
}

export function CardTitle({
    className,
    ...props
}: HTMLAttributes<HTMLHeadingElement>) {
    return (
        <h3
            className={cn(
                "text-adb-navy dark:text-adb-navy-100 text-lg font-semibold",
                className,
            )}
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
            className={cn(
                "text-adb-navy-600 dark:text-adb-navy-300 mt-2 text-sm",
                className,
            )}
            {...props}
        />
    );
}
