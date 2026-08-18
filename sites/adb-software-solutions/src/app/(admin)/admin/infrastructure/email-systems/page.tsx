import { AdminAPI } from "@/lib/api/endpoints";
import { InfrastructureRegisterPage } from "../InfrastructureRegisterPage";

export const metadata = { title: "Email Systems" };

export default function EmailSystemsPage() {
    return (
        <InfrastructureRegisterPage
            title="Email Systems"
            description="Tracked mail platforms and their SPF, DKIM and DMARC posture."
            endpoint={AdminAPI.infrastructure.emailSystems()}
            columns={[
                { key: "provider", label: "Provider" },
                { key: "domains", label: "Domains" },
                { key: "spf_status", label: "SPF" },
                { key: "dkim_status", label: "DKIM" },
                { key: "dmarc_status", label: "DMARC" },
            ]}
            emptyTitle="No email systems tracked"
            emptyDescription="Email platforms will appear here once they are added to the infrastructure inventory."
            loadingLabel="Loading email systems..."
        />
    );
}
