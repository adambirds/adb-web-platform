import {Suspense} from "react";
import {
    ExperienceProvider,
    LoadingExperience,
} from "../../components/experience/ExperienceProvider";
export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <Suspense fallback={<LoadingExperience />}>
            <ExperienceProvider>{children}</ExperienceProvider>
        </Suspense>
    );
}
