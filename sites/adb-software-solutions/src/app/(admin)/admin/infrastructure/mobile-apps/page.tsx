import { AdminAPI } from "@/lib/api/endpoints";
import { InfrastructureRegisterPage } from "../InfrastructureRegisterPage";

export const metadata = { title: "Mobile Apps" };

export default function MobileAppsPage() {
    return (
        <InfrastructureRegisterPage
            title="Mobile Apps"
            description="Mobile application inventory covering platform, framework and release state."
            endpoint={AdminAPI.infrastructure.mobileApps()}
            columns={[
                { key: "name", label: "App" },
                { key: "platform", label: "Platform" },
                { key: "framework", label: "Framework" },
                { key: "current_version", label: "Version" },
                { key: "release_status", label: "Status" },
                { key: "bundle_id", label: "Bundle ID" },
            ]}
            emptyTitle="No mobile apps tracked"
            emptyDescription="Mobile applications will appear here once they are added to the inventory."
            loadingLabel="Loading mobile apps..."
        />
    );
}
