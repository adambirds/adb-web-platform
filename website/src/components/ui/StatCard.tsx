import { Card, CardContent, CardHeader, CardTitle } from "./Card";

interface StatCardProps {
    label: string;
    value: string;
    helper?: string;
}

export function StatCard({ label, value, helper }: StatCardProps) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>{label}</CardTitle>
            </CardHeader>
            <CardContent>
                <p className="text-adb-cyan text-2xl font-semibold">{value}</p>
                {helper ? (
                    <p className="text-adb-navy-600 dark:text-adb-navy-300 mt-1 text-sm">
                        {helper}
                    </p>
                ) : null}
            </CardContent>
        </Card>
    );
}
