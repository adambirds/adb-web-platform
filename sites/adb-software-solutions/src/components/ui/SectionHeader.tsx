import { cn } from "@/lib/utils/cn";

interface SectionHeaderProps {
    eyebrow?: string;
    title: string;
    subtitle?: string;
    className?: string;
}

export function SectionHeader({
    eyebrow,
    title,
    subtitle,
    className,
}: SectionHeaderProps) {
    return (
        <div className={cn("max-w-2xl", className)}>
            {eyebrow ? (
                <p className="text-adb-cyan text-sm font-semibold tracking-wide uppercase">
                    {eyebrow}
                </p>
            ) : null}
            <h2 className="text-adb-navy dark:text-adb-navy-100 mt-2 text-3xl font-semibold">
                {title}
            </h2>
            {subtitle ? (
                <p className="text-adb-navy-600 dark:text-adb-navy-300 mt-3 text-base">
                    {subtitle}
                </p>
            ) : null}
        </div>
    );
}
