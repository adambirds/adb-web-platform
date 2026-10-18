import {describe, expect, it, vi} from "vitest";
import {redirect} from "next/navigation";
import Page from "../src/app/page";
import {ANALYTICS_URL, AUTH_URL} from "../src/app/client";

vi.mock("next/navigation", () => ({redirect: vi.fn()}));
describe("Analytics entry route", () => {
    it("uses the existing login application and returns directly to dashboard", () => {
        Page();
        const target = new URL(vi.mocked(redirect).mock.calls[0][0]);
        expect(target.origin).toBe(AUTH_URL);
        expect(target.pathname).toBe("/login");
        expect(target.searchParams.get("next")).toBe(
            new URL("/dashboard", ANALYTICS_URL).toString(),
        );
    });
});
