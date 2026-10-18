import {afterEach, describe, expect, it, vi} from "vitest";
import {
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
} from "@testing-library/react";
import {
    AnalyticsApp,
    DataTable,
    Trend,
    compareRows,
} from "../src/app/workspace";
import {IntegrationSettings, TrackingSettings} from "../src/app/settings";
import {
    api,
    type Business,
    type Session,
    type Website,
} from "../src/app/client";

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
const session: Session = {
    email: "owner@example.com",
    businesses: [business],
    website_id: 1,
};

describe("analytics workspace", () => {
    it("shows first-run business onboarding without fabricated statistics", async () => {
        vi.mocked(api).mockResolvedValue({
            email: "new@example.com",
            businesses: [],
            website_id: null,
        });
        render(<AnalyticsApp />);
        expect(
            await screen.findByText("Start with your business."),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", {name: "Create business"}),
        ).toBeInTheDocument();
    });
    it("shows a useful connection empty state and business/website selectors", async () => {
        vi.mocked(api).mockResolvedValue(session);
        render(<AnalyticsApp />);
        expect(
            await screen.findByRole("heading", {
                name: "Connect Google Analytics",
            }),
        ).toBeInTheDocument();
        expect(screen.getByLabelText("Business")).toHaveValue("1");
        expect(screen.getByLabelText("Website")).toHaveValue("1");
    });
    it("does not offer privileged settings to a viewer", async () => {
        vi.mocked(api).mockResolvedValue({
            ...session,
            businesses: [{...business, role: "viewer"}],
        });
        render(<AnalyticsApp />);
        await screen.findByLabelText("Business");
        expect(
            screen.queryByRole("button", {name: "Integrations"}),
        ).not.toBeInTheDocument();
        expect(
            screen.queryByRole("button", {name: "Tracking configuration"}),
        ).not.toBeInTheDocument();
    });
    it("loads real backend report values and changes date filters", async () => {
        const linked = {
            ...website,
            providers: [
                {
                    provider: "ga4" as const,
                    external_id: "properties/123",
                    connection_id: 1,
                    last_synced_at: null,
                    error_code: "",
                    metadata: {},
                },
            ],
        };
        vi.mocked(api).mockImplementation(async (path) => {
            if (path === "/session")
                return {
                    ...session,
                    businesses: [{...business, websites: [linked]}],
                } as never;
            if (path.endsWith("/sync")) return [] as never;
            return {
                current: {
                    rows: [{sessions: 1234}],
                    updated_at: "2026-01-01T00:00:00Z",
                    complete: true,
                    measurement: "GA4",
                },
                previous: null,
                total: 1,
            } as never;
        });
        render(<AnalyticsApp />);
        expect(await screen.findByText("1,234")).toBeInTheDocument();
        fireEvent.change(screen.getByLabelText("From"), {
            target: {value: "2026-01-01"},
        });
        await waitFor(() =>
            expect(
                vi
                    .mocked(api)
                    .mock.calls.some(([path]) =>
                        path.includes("start=2026-01-01"),
                    ),
            ).toBe(true),
        );
    });
    it("surfaces report errors", async () => {
        vi.mocked(api).mockRejectedValue(new Error("Network unavailable"));
        render(<AnalyticsApp />);
        expect(await screen.findByRole("alert")).toHaveTextContent(
            "Network unavailable",
        );
    });
    it("switches businesses and resets website context", async () => {
        vi.mocked(api).mockResolvedValue({
            ...session,
            businesses: [
                business,
                {
                    ...business,
                    id: 2,
                    name: "Other business",
                    websites: [
                        {
                            ...website,
                            id: 2,
                            business_id: 2,
                            name: "Other website",
                        },
                    ],
                },
            ],
        });
        render(<AnalyticsApp />);
        await screen.findByLabelText("Business");
        fireEvent.change(screen.getByLabelText("Business"), {
            target: {value: "2"},
        });
        expect(screen.getByLabelText("Website")).toHaveValue("2");
    });
});

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
        expect(screen.getByRole("img")).toHaveAccessibleName(
            "Sessions trend, 1 reported dates",
        );
    });
});

describe("integration and event configuration", () => {
    it("distinguishes reporting consent from administration consent", async () => {
        vi.mocked(api).mockResolvedValue([]);
        render(
            <IntegrationSettings
                business={business}
                website={website}
                refresh={vi.fn()}
            />,
        );
        expect(
            screen.getByRole("button", {name: "Connect Google for reporting"}),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", {
                name: "Connect with GA4 administration",
            }),
        ).toBeInTheDocument();
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
