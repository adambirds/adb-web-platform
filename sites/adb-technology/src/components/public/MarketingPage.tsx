import { BusinessPages } from "@adb/ui/public/BusinessPages";
import { site } from "@/content/site";
import { pageCopy } from "@/content/page-design";
import { websitePolicies, policyDetails } from "@/content/policies";
export function MarketingPage({
    path,
    search,
}: {
    path: string[];
    search: Record<string, string | string[] | undefined>;
}) {
    return (
        <BusinessPages
            site={site}
            pageCopy={pageCopy}
            policies={websitePolicies}
            policyDetails={policyDetails}
            path={path}
            search={search}
        />
    );
}
