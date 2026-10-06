import type { MetadataRoute } from "next";
import { site } from "@/content/site";
export default function robots(): MetadataRoute.Robots {
    return {
        rules: {
            userAgent: "*",
            allow: "/",
            disallow: ["/admin", "/api/", "/contact/thank-you/"],
        },
        sitemap: `${site.domain}/sitemap.xml`,
    };
}
