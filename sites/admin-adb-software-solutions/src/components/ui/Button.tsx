import { cn } from "@/lib/utils/cn";
import Link from "next/link";
import { AnchorHTMLAttributes, ButtonHTMLAttributes } from "react";

const baseStyles =
    "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-adb-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 disabled:pointer-events-none disabled:opacity-50";

const variantStyles = {
    primary:
        "bg-adb-cyan-500 text-slate-950 hover:bg-adb-cyan-400 active:bg-adb-cyan-300",
    secondary:
        "border border-slate-700 bg-slate-800 text-slate-100 hover:border-slate-600 hover:bg-slate-700",
    outline:
        "border border-slate-700 bg-transparent text-slate-200 hover:border-slate-600 hover:bg-slate-900 hover:text-white",
    ghost: "text-slate-400 hover:bg-slate-900 hover:text-slate-100",
    destructive:
        "border border-red-900/70 bg-red-950/60 text-red-200 hover:bg-red-900/70 hover:text-white",
};

const sizeStyles = {
    sm: "h-8 px-3 text-xs",
    md: "h-10 px-4 text-sm",
    lg: "h-11 px-5 text-sm",
    icon: "h-9 w-9 p-0",
};

type ButtonVariant = keyof typeof variantStyles;
type ButtonSize = keyof typeof sizeStyles;

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: ButtonVariant;
    size?: ButtonSize;
}

export function Button({
    className,
    variant = "primary",
    size = "md",
    ...props
}: ButtonProps) {
    return (
        <button
            className={cn(
                baseStyles,
                variantStyles[variant],
                sizeStyles[size],
                className,
            )}
            {...props}
        />
    );
}

interface ButtonLinkProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
    href: string;
    variant?: ButtonVariant;
    size?: ButtonSize;
}

export function ButtonLink({
    className,
    variant = "primary",
    size = "md",
    href,
    ...props
}: ButtonLinkProps) {
    return (
        <Link
            href={href}
            className={cn(
                baseStyles,
                variantStyles[variant],
                sizeStyles[size],
                className,
            )}
            {...props}
        />
    );
}
