import {renderToStaticMarkup} from "react-dom/server";
import {cleanup, render, screen} from "@testing-library/react";
import {afterEach, describe, expect, it} from "vitest";
import PrivacyPage from "../src/app/privacy/page";
import TermsPage from "../src/app/terms/page";
import RootLayout from "../src/app/layout";
import {LegalLinks} from "../src/app/legal-page";

afterEach(cleanup);

describe("Public policy pages", () => {
    it("renders privacy without a session and explains revocation separately from deletion", () => {
        render(<PrivacyPage />);
        expect(
            screen.getByRole("heading", {level: 1, name: "Privacy notice"}),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/currently used only by its operator/),
        ).toBeInTheDocument();
        expect(
            screen.getByText(
                /does not automatically delete previously synced reports/,
            ),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("link", {name: "your Google account connections"}),
        ).toHaveAttribute("href", "https://myaccount.google.com/connections");
        expect(document.querySelector("script")).toBeNull();
    });
    it("describes the current private terms without offering a subscription", () => {
        render(<TermsPage />);
        expect(
            screen.getByRole("heading", {level: 1, name: "Terms of use"}),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/no public registration, paid plans/),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("link", {name: "privacy notice"}),
        ).toHaveAttribute("href", "/privacy");
    });
    it("links both policies from the shared application layout", () => {
        const html = renderToStaticMarkup(
            <RootLayout>
                <p>Workspace</p>
            </RootLayout>,
        );
        expect(html).toContain('href="/privacy"');
        expect(html).toContain('href="/terms"');
        render(<LegalLinks />);
        expect(
            screen.getByRole("navigation", {name: "Policies"}),
        ).toBeInTheDocument();
        expect(screen.getByRole("link", {name: "Privacy"})).toHaveAttribute(
            "href",
            "/privacy",
        );
        expect(screen.getByRole("link", {name: "Terms"})).toHaveAttribute(
            "href",
            "/terms",
        );
    });
});
