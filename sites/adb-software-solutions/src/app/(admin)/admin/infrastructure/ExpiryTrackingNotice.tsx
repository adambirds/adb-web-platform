import { ButtonLink, Card } from "@/components/ui";

export function ExpiryTrackingNotice() {
    return (
        <Card className="p-5">
            <p className="font-medium text-slate-100">
                Automatic expiry tracking and metadata updates
            </p>
            <p className="mt-2 text-sm text-slate-400">
                Manage Domain and TLS Certificate expiry tracking in Resources.
                Bring existing inventory records into their resource workspace
                through Reconciliation.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
                <ButtonLink href="/admin/infrastructure/resources">
                    Open Resources
                </ButtonLink>
                <ButtonLink href="/admin/infrastructure/reconciliation">
                    Open Reconciliation
                </ButtonLink>
            </div>
        </Card>
    );
}
