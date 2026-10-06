import { publicSitemap } from "@adb/ui/public/server";
import { site } from "@/content/site";
export const dynamic = "force-dynamic";
export default async function sitemap() {
    return publicSitemap(site);
}
