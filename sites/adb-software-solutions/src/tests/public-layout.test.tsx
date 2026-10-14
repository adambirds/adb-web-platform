/** @jest-environment node */
import { renderToStaticMarkup } from "react-dom/server";
import PublicLayout from "../app/(public)/layout";
import RootLayout from "../app/layout";
import { site } from "@/content/site";
jest.mock("next/server", () => ({
    connection: jest.fn().mockResolvedValue(undefined),
}));
jest.mock("@adb/ui/public/Analytics", () => ({
    Analytics: ({ measurementId }: { measurementId: string }) => (
        <span data-test-analytics={measurementId} />
    ),
}));
jest.mock("@adb/ui/public/server", () => ({
    homeContent: jest
        .fn()
        .mockResolvedValue({
            work: { total: 0 },
            articles: { total: 0 },
            faqs: { total: 0 },
            testimonials: { total: 0 },
        }),
    businessSchema: () => ({}),
    siteMetadata: () => ({}),
}));
jest.mock("@adb/ui/public/SiteHeader", () => ({ SiteHeader: () => null }));
jest.mock("@adb/ui/public/SiteFooter", () => ({ SiteFooter: () => null }));

test("the correct runtime measurement ID is confined to the public layout", async () => {
    const key =
        site.kind === "software"
            ? "GA4_SOFTWARE_SOLUTIONS_MEASUREMENT_ID"
            : "GA4_TECHNOLOGY_MEASUREMENT_ID";
    const prior = process.env[key];
    try {
        process.env[key] = "G-BRANDTEST";
        const publicHTML = renderToStaticMarkup(
            await PublicLayout({ children: <div>Public content</div> }),
        );
        expect(publicHTML).toContain('data-test-analytics="G-BRANDTEST"');
        expect(publicHTML).toContain("brand-family");
        const rootHTML = renderToStaticMarkup(
            RootLayout({ children: <div>Operations content</div> }),
        );
        expect(rootHTML).not.toContain("data-test-analytics");
    } finally {
        if (prior === undefined) delete process.env[key];
        else process.env[key] = prior;
    }
});
