import { cn } from "@/lib/utils/cn";
import { ReactNode } from "react";
import { Card } from "./Card";

interface StatCardProps {
    label: string;
    value: string;
    helper?: string;
    icon?: ReactNode;
    accent?: "cyan" | "green" | "amber" | "red" | "slate";
}

const accentClasses = {
    cyan: "text-adb-cyan-400 bg-adb-cyan-500/10",
    green: "text-emerald-400 bg-emerald-500/10",
    amber: "text-yellow-400 bg-yellow-500/10",
    red: "text-red-400 bg-red-500/10",
    slate: "text-slate-400 bg-slate-800",
};

export function StatCard({
    label,
    value,
    helper,
    icon,
    accent = "cyan",
}: StatCardProps) {
    return (
        <Card className="p-5">
            <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                    <p className="text-xs font-medium text-slate-500">{label}</p>
                    <p className="mt-2 text-2xl font-semibold tracking-tight text-white">
                        {value}
                    </p>
                    {helper ? (
                        <p className="mt-1 truncate text-xs text-slate-600">
                            {helper}
                        </p>
                    ) : null}
                </div>
                {icon ? (
                    <div
                        className={cn(
                            "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
                            accentClasses[accent],
                        )}
                    >
                        {icon}
                    </div>
                ) : null}
            </div>
        </Card>
    );
}
