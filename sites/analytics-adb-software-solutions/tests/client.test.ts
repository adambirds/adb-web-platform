import {afterEach, describe, expect, it, vi} from "vitest";
import {api, apiUrl, ApiError, initialDates, loginUrl} from "../src/app/client";
afterEach(() => vi.unstubAllGlobals());
describe("shared identity transport", () => {
    it("sends session credentials and gets CSRF before mutation", async () => {
        const fetcher = vi
            .fn()
            .mockResolvedValueOnce({
                ok: true,
                json: async () => ({csrf_token: "test-csrf"}),
            })
            .mockResolvedValueOnce({
                ok: true,
                json: async () => ({saved: true}),
            });
        vi.stubGlobal("fetch", fetcher);
        await api("/businesses", "POST", {name: "Example"});
        expect(fetcher.mock.calls[1][1]).toMatchObject({
            credentials: "include",
            headers: {"X-CSRFToken": "test-csrf"},
            method: "POST",
        });
    });
    it("preserves authentication failures", async () => {
        vi.stubGlobal(
            "fetch",
            vi.fn().mockResolvedValue({
                ok: false,
                status: 401,
                json: async () => ({detail: "Unauthorized"}),
            }),
        );
        await expect(api("/session")).rejects.toBeInstanceOf(ApiError);
    });
    it("builds the dedicated auth return URL", () => {
        const url = new URL(
            loginUrl("https://analytics.adbsoftwaresolutions.co.uk/"),
        );
        expect(url.pathname).toBe("/login");
        expect(url.searchParams.get("next")).toBe(
            "https://analytics.adbsoftwaresolutions.co.uk/",
        );
        expect(apiUrl("/session")).toContain("/api/analytics/session");
    });
    it("starts with a bounded period allowing for Search Console delay", () => {
        const {start, end} = initialDates();
        expect((Date.parse(end) - Date.parse(start)) / 86400000).toBe(27);
    });
});
