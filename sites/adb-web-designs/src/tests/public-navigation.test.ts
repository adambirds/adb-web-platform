/** @jest-environment node */
import { site as web } from "@/content/site";
import { site as software } from "../../../adb-software-solutions/src/content/site";
import { site as technology } from "../../../adb-technology/src/content/site";
import redirects from "../../redirects.json";
import { legacyAliases } from "@/content/legacy-aliases";
import { pageMetadata, businessSchema } from "@adb/ui/public/server";
import type { PublicSite } from "@adb/ui/public/types";

function routes(site: PublicSite) {
    return new Set([
        "/",
        "/services/",
        "/contact/",
        "/contact/thank-you/",
        "/portfolio/",
        "/blog/",
        "/testimonials/",
        "/faqs/",
        ...site.pages.map((page) => `/${page.slug}/`),
        ...site.services.map((service) => `/services/${service.slug}/`),
        ...site.areas.map((area) => `/${area.slug}/`),
    ]);
}
for (const site of [web, software, technology]) {
    it(`${site.name} has unique page slugs and valid service cross-links`, () => {
        const paths = routes(site);
        expect(new Set(site.services.map((service) => service.slug)).size).toBe(
            site.services.length,
        );
        for (const service of site.services) {
            for (const link of service.related) {
                if (link.href.startsWith("/"))
                    expect(paths.has(link.href)).toBe(true);
                else expect(link.href).toMatch(/^https:\/\/adb/);
            }
        }
        for (const area of site.areas) {
            expect(area.sections.length).toBeGreaterThanOrEqual(2);
            for (const slug of area.services)
                expect(
                    site.services.some((service) => service.slug === slug),
                ).toBe(true);
        }
    });
    it(`${site.name} has correct canonical and logo metadata without invented offices`, () => {
        const result = pageMetadata(site, "A page", "Description", "/about/");
        expect(result.alternates?.canonical).toBe(`${site.domain}/about/`);
        expect(result.openGraph).toHaveProperty("siteName", site.name);
        expect(businessSchema(site)).not.toHaveProperty("address");
        expect(businessSchema(site)).toHaveProperty(
            "logo",
            `${site.domain}/brand/logo-light.png`,
        );
    });
}
it("every static migration redirect has a real code-owned destination and no chain", () => {
    const paths = routes(web);
    for (const rule of redirects) {
        expect(paths.has(rule.destination)).toBe(true);
        expect(
            redirects.some(
                (other) => other.source === rule.destination.replace(/\/$/, ""),
            ),
        ).toBe(false);
        expect(rule.permanent).toBe(true);
    }
});
it("editorial aliases are gated separately from unconditional redirects", () => {
    for (const source of Object.keys(legacyAliases))
        expect(redirects.some((rule) => rule.source === source)).toBe(false);
    expect(legacyAliases["/wordpress-how-to-secure-your-website"]).toBe(
        "/blog/wordpress-how-to-secure-your-website/",
    );
});
it("unconfirmed consultancy and embedded contracting do not appear as software services", () => {
    expect(
        software.services.some(
            (service) => service.slug === "software-consultancy",
        ),
    ).toBe(false);
    expect(
        software.services.some((service) => service.slug === "ai-code-review"),
    ).toBe(true);
});

for (const brand of [web, software, technology]) {
    it(`${brand.name} leads its own About introduction without employment copy`, () => {
        const about = brand.pages.find((page) => page.slug === "about")!;
        expect(JSON.stringify(about)).not.toContain("full-time");
        const familyParagraph = about.sections
            .flatMap((section) => section.paragraphs)
            .find((paragraph) =>
                [web.name, software.name, technology.name].every((name) =>
                    paragraph.includes(name),
                ),
            );
        expect(familyParagraph?.startsWith(brand.name)).toBe(true);
    });
}
