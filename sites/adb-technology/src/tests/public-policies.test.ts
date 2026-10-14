/** @jest-environment node */
import { site } from "@/content/site";
import { websitePolicies, policyDetails } from "@/content/policies";
import { pageMetadata } from "@adb/ui/public/server";

test("policies describe this Brand and the approved enquiry review period", () => {
    expect(websitePolicies.map((policy) => policy.slug)).toEqual([
        "privacy-policy",
        "cookie-policy",
        "terms",
    ]);
    const text = JSON.stringify(websitePolicies);
    expect(text).toContain(new URL(site.domain).hostname);
    expect(text).toContain(policyDetails.operator);
    expect(text).toContain("36 months");
    expect(text).toContain("manual review and approval");
    expect(text).not.toContain("no analytics");
    expect(text).not.toContain("need approval before launch");
    const terms = websitePolicies.find((policy) => policy.slug === "terms")!;
    expect(terms.introduction).not.toContain(
        "website design, hosting, maintenance",
    );
    for (const policy of websitePolicies) {
        expect(
            pageMetadata(
                site,
                policy.title,
                policy.description,
                `/${policy.slug}/`,
            ).alternates?.canonical,
        ).toBe(`${site.domain}/${policy.slug}/`);
    }
});
test("public areas only reference offered services", () => {
    for (const area of site.areas)
        for (const slug of area.services)
            expect(site.services.some((service) => service.slug === slug)).toBe(
                true,
            );
    expect(
        site.services.some(
            (service) => service.slug === "software-consultancy",
        ),
    ).toBe(false);
});
