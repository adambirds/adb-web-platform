import {afterEach, describe, expect, it, vi} from "vitest";

async function config(appUrl?: string) {
    vi.resetModules();
    vi.stubEnv("NEXT_PUBLIC_APP_URL", appUrl);
    return import("../../src/utils/config");
}

afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
});

describe("combined public/admin redirect origin", () => {
    it("defaults to the Software Solutions app and allows its admin routes", async () => {
        const settings = await config();
        expect(settings.getDefaultAppUrl()).toBe("http://localhost:3000");
        expect(
            settings.isValidRedirectUrl("http://localhost:3000/admin/"),
        ).toBe(true);
        expect(settings.isValidRedirectUrl("/admin/leads/")).toBe(true);
        expect(
            settings.isValidRedirectUrl("http://localhost:3001/admin/"),
        ).toBe(false);
    });

    it("uses the configured combined origin for public and admin return URLs", async () => {
        const settings = await config("https://adbsoftwaresolutions.co.uk");
        expect(
            settings.isValidRedirectUrl("https://adbsoftwaresolutions.co.uk/"),
        ).toBe(true);
        expect(
            settings.isValidRedirectUrl(
                "https://adbsoftwaresolutions.co.uk/admin/",
            ),
        ).toBe(true);
        expect(
            settings.isValidRedirectUrl("http://localhost:3000/admin/"),
        ).toBe(false);
        expect(settings.getDefaultAppUrl()).toBe(
            "https://adbsoftwaresolutions.co.uk",
        );
    });

    it("preserves an admin return target and falls back for an untrusted target", async () => {
        const settings = await config("https://adbsoftwaresolutions.co.uk");
        try {
            window.history.replaceState(
                null,
                "",
                `/?next=${encodeURIComponent("https://adbsoftwaresolutions.co.uk/admin/leads/")}`,
            );
            expect(settings.getRedirectUrl()).toBe(
                "https://adbsoftwaresolutions.co.uk/admin/leads/",
            );
            window.history.replaceState(
                null,
                "",
                "/?next=https%3A%2F%2Fexample.com%2F",
            );
            expect(settings.getRedirectUrl()).toBe(
                "https://adbsoftwaresolutions.co.uk",
            );
        } finally {
            window.history.replaceState(null, "", "/");
        }
    });

    it("rejects external and lookalike origins", async () => {
        const settings = await config("https://adbsoftwaresolutions.co.uk");
        for (const target of [
            "https://example.com/admin/",
            "https://adbsoftwaresolutions.co.uk.example.com/admin/",
            "//example.com/admin/",
            "javascript:alert(1)",
            "",
        ]) {
            expect(settings.isValidRedirectUrl(target)).toBe(false);
        }
    });
});
