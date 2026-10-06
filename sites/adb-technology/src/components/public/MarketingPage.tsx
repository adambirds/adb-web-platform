import { PublicPages } from "@adb/ui/public/PublicPages";
import { site } from "@/content/site";
export function MarketingPage({
    path,
    search,
}: {
    path: string[];
    search: Record<string, string | string[] | undefined>;
}) {
    return <PublicPages site={site} path={path} search={search} />;
}
