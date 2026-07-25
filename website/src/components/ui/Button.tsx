import { cn } from "@/lib/utils/cn";
import Link from "next/link";
import { AnchorHTMLAttributes, ButtonHTMLAttributes } from "react";

const baseStyles =
    "inline-flex items-center justify-center rounded-lg font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-adb-cyan focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ring-offset-white dark:ring-offset-adb-navy-950";

const variantStyles = {
    primary: "bg-adb-cyan text-adb-navy-950 hover:bg-adb-cyan-600",
    secondary:
        "bg-adb-navy-900 text-white hover:bg-adb-navy-800 dark:bg-adb-navy-800",
    outline:
        "border border-adb-navy-200 text-adb-navy hover:border-adb-cyan hover:text-adb-cyan dark:border-adb-navy-800 dark:text-adb-navy-100",
    ghost: "text-adb-navy hover:bg-adb-navy-100 dark:text-adb-navy-100 dark:hover:bg-adb-navy-900",
    destructive: "bg-red-600 text-white hover:bg-red-500",
};

const sizeStyles = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-sm",
    lg: "px-5 py-3 text-base",
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
