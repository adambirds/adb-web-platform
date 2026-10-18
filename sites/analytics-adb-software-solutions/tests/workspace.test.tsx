import {afterEach, describe, expect, it, vi} from "vitest";
import {cleanup, fireEvent, render, screen} from "@testing-library/react";
import {DataTable, compareRows} from "../src/components/reports/ReportTable";
import {Trend} from "../src/components/experience/ActivityChart";
import {IntegrationSettings} from "../src/components/settings/IntegrationSettings";
import {TrackingSettings} from "../src/components/settings/TrackingSettings";
import {api, type Business, type Website} from "../src/app/client";

vi.mock("../src/app/client", async (importOriginal) => ({
    ...(await importOriginal<typeof import("../src/app/client")>()),
    api: vi.fn(),
}));
afterEach(() => {
    cleanup();
    vi.resetAllMocks();
});
const website: Website = {
    id: 1,
    business_id: 1,
    name: "Example",
    domain: "example.com",
    timezone: "Europe/London",
    is_active: true,
    providers: [],
};
const business: Business = {
    id: 1,
    name: "Example business",
    slug: "example",
    role: "owner",
    websites: [website],
};
describe("report rendering", () => {
    it("sorts table rows and retains a readable empty state", () => {
        const {rerender} = render(
            <DataTable
                rows={[
                    {page: "/b", clicks: 5},
                    {page: "/a", clicks: 20},
                ]}
            />,
        );
        fireEvent.click(screen.getByRole("button", {name: "Clicks"}));
        expect(screen.getAllByRole("row")[1]).toHaveTextContent("/a");
        rerender(<DataTable rows={[]} />);
        expect(
            screen.getByText(/No results for this period/),
        ).toBeInTheDocument();
    });
    it("provides an accessible chart label", () => {
        render(
            <Trend
                rows={[{date: "20260101", sessions: 12}]}
                metric="sessions"
            />,
        );
        expect(screen.getByLabelText("Sessions over time")).toBeInTheDocument();
    });
});

describe("integration and event configuration", () => {
    it("provides one Google consent for reporting and confirmed administration", async () => {
        vi.mocked(api).mockResolvedValue([]);
        render(<IntegrationSettings business={business} refresh={vi.fn()} />);
        expect(
            screen.getByRole("button", {name: "Connect Google"}),
        ).toBeInTheDocument();
        expect(
            screen.queryByRole("button", {
                name: "Connect with GA4 administration",
            }),
        ).not.toBeInTheDocument();
    });
    it("requires a reviewed plan and confirmation before creating custom dimensions", async () => {
        vi.mocked(api).mockImplementation(async (path) => {
            if (path.endsWith("/plan"))
                return {
                    registered: ["button_id"],
                    missing: ["button_text", "button_location"],
                    notice: "Not retroactive",
                    event_dimensions_used: 1,
                } as never;
            return {items: [], can_edit: true} as never;
        });
        render(
            <TrackingSettings
                website={{
                    ...website,
                    providers: [
                        {
                            provider: "ga4",
                            external_id: "properties/123",
                            connection_id: 1,
                            last_synced_at: null,
                            error_code: "",
                            metadata: {},
                        },
                    ],
                }}
            />,
        );
        fireEvent.click(screen.getByText("Tracking plans & implementation"));
        fireEvent.click(
            screen.getByRole("button", {name: "Review definitions"}),
        );
        const create = await screen.findByRole("button", {
            name: "Create missing definitions",
        });
        expect(create).toBeDisabled();
        fireEvent.click(
            screen.getByLabelText(
                "I confirm these event parameter registrations.",
            ),
        );
        expect(create).toBeEnabled();
    });
});

describe("previous-period row comparison", () => {
    it("matches dimension identities and leaves missing baselines unavailable", () => {
        const rows = compareRows(
            [
                {query: "one", clicks: 20},
                {query: "two", clicks: 10},
            ],
            [{query: "one", clicks: 10}],
        );
        expect(rows[0]["clicks change rate"]).toBe(1);
        expect(rows[1]["clicks change rate"]).toBeNull();
    });
});
