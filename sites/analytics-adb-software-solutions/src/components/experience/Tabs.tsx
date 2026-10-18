"use client";
export function Tabs({
    values,
    value,
    onChange,
}: {
    values: [string, string][];
    value: string;
    onChange: (value: string) => void;
}) {
    return (
        <div className="report-tabs" role="group">
            {values.map(([key, label]) => (
                <button
                    key={key}
                    aria-pressed={value === key}
                    className={value === key ? "active" : ""}
                    onClick={() => onChange(key)}
                >
                    {label}
                </button>
            ))}
        </div>
    );
}
