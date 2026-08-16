interface AlertProps {
    type: "success" | "error" | "warning" | "info";
    children: React.ReactNode;
    className?: string;
}

export default function Alert({type, children, className = ""}: AlertProps) {
    const baseClasses = "rounded-md p-4";
    const typeClasses = {
        success:
            "bg-green-50 text-green-800 dark:bg-green-900/30 dark:text-green-300",
        error: "bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-300",
        warning:
            "bg-yellow-50 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
        info: "bg-blue-50 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
    };

    return (
        <div className={`${baseClasses} ${typeClasses[type]} ${className}`}>
            <div className="text-sm">{children}</div>
        </div>
    );
}
