import { MarketingLayout } from "@/components/layout/MarketingLayout";
import { ReactNode } from "react";

export default function Layout({ children }: { children: ReactNode }) {
    return <MarketingLayout>{children}</MarketingLayout>;
}
