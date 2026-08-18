import { Container, PageHeader } from "@/components/ui";
import { TimeEntryList } from "./TimeEntryList";

export const metadata = {
    title: "Time Tracking",
};

export default function TimeTrackingPage() {
    return (
        <Container className="py-8">
            <PageHeader
                title="Time tracking"
                description="Billable and internal time across the operational work visible to your account."
            />
            <div className="mt-6">
                <TimeEntryList />
            </div>
        </Container>
    );
}
