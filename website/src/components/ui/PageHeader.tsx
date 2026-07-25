import { cn } from "@/lib/utils/cn";
import { ReactNode } from "react";

interface PageHeaderProps {
    title: string;
    description?: string;
    actions?: ReactNode;
    className?: string;
}

export function PageHeader({
    title,
    description,
    actions,
    className,
}: PageHeaderProps) {
    return (
        <div
            className={cn(
                "flex flex-col gap-4 md:flex-row md:items-center md:justify-between",
                className,
            )}
        >
            <div>
                <h1 className="text-adb-navy dark:text-adb-navy-100 text-3xl font-semibold">
                    {title}
                </h1>
                {description ? (
                    <p className="text-adb-navy-600 dark:text-adb-navy-300 mt-2 text-sm">
                        {description}
                    </p>
                ) : null}
            </div>
            {actions ? (
                <div className="flex flex-wrap gap-3">{actions}</div>
            ) : null}
        </div>
    );
}
