import { AdminAPI } from "@/lib/api/endpoints";
import { InfrastructureRegisterPage } from "../InfrastructureRegisterPage";

export const metadata = { title: "APIs" };

export default function APIsPage() {
    return (
        <InfrastructureRegisterPage
            title="APIs"
            description="Tracked service endpoints with their visibility and authentication model."
            endpoint={AdminAPI.infrastructure.apis()}
            columns={[
                { key: "name", label: "API" },
                { key: "api_type", label: "Type" },
                { key: "base_url", label: "Base URL" },
                { key: "visibility", label: "Visibility" },
                { key: "authentication", label: "Authentication" },
            ]}
            emptyTitle="No APIs tracked"
            emptyDescription="API services will appear here once they are added to the infrastructure inventory."
            loadingLabel="Loading APIs..."
        />
    );
}
