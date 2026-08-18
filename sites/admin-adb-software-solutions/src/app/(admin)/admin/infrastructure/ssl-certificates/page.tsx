import { AdminAPI } from "@/lib/api/endpoints";
import { InfrastructureRegisterPage } from "../InfrastructureRegisterPage";

export const metadata = { title: "SSL Certificates" };

export default function SSLCertificatesPage() {
    return (
        <InfrastructureRegisterPage
            title="SSL Certificates"
            description="Certificate inventory ordered by expiry date for proactive renewal monitoring."
            endpoint={AdminAPI.infrastructure.sslCertificates()}
            columns={[
                { key: "domain", label: "Domain" },
                { key: "provider", label: "Provider" },
                { key: "cert_type", label: "Certificate type" },
                { key: "expiry_date", label: "Expiry" },
            ]}
            emptyTitle="No SSL certificates tracked"
            emptyDescription="Certificates will appear here once they are added to the infrastructure inventory."
            loadingLabel="Loading SSL certificates..."
        />
    );
}
