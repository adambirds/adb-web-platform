import {afterEach, beforeEach, describe, expect, it, vi} from "vitest";
import {
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
} from "@testing-library/react";
import {api, type Session} from "../src/app/client";
import {PortfolioPage} from "../src/components/experience/PortfolioPage";
import {WebsiteDashboard} from "../src/components/experience/WebsiteDashboard";
import {SettingsPage} from "../src/components/experience/SettingsPage";
import {useExperience} from "../src/components/experience/ExperienceProvider";
import {
    compact,
    series,
    type DashboardData,
    type Portfolio,
    type SiteSummary,
} from "../src/lib/experience";

const navigation = vi.hoisted(() => ({replace: vi.fn(), push: vi.fn()}));
vi.mock("next/navigation", () => ({
    useRouter: () => navigation,
    usePathname: () => "/dashboard",
    useSearchParams: () => new URLSearchParams(),
}));
vi.mock("../src/app/client", async (original) => ({
    ...(await original<typeof import("../src/app/client")>()),
    api: vi.fn(),
}));
vi.mock(
    "../src/components/experience/ExperienceProvider",
    async (original) => ({
        ...(await original<
            typeof import("../src/components/experience/ExperienceProvider")
        >()),
        useExperience: vi.fn(),
    }),
);
const period = {start: "2026-10-01", end: "2026-10-02"};
const site: SiteSummary = {
    id: 1,
    business_id: 1,
    name: "Example",
    domain: "example.com",
    timezone: "Europe/London",
    providers: ["ga4", "gsc"],
    property_ids: {ga4: "properties/1"},
    shared_providers: [],
    ga4: {
        current: {totalUsers: 1200, sessions: 1800, keyEvents: 20},
        previous: {totalUsers: 1000},
    },
    gsc: {current: {clicks: 300}, previous: {clicks: 200}},
    trends: {
        ga4: {current: [{date: "20261001", totalUsers: 600}], previous: null},
        gsc: {current: null, previous: null},
    },
    insights: [],
    syncing: false,
    updated_at: null,
    issues: [],
};
const session: Session = {
    email: "test@example.com",
    website_id: 1,
    businesses: [
        {
            id: 1,
            name: "My sites",
            slug: "sites",
            role: "owner",
            websites: [{...site, is_active: true, providers: []}],
        },
    ],
};
const portfolio: Portfolio = {
    ...period,
    sites: [site],
    metrics: {
        visitors: {
            current: 1200,
            previous: 1000,
            change: 20,
            covered: 1,
            expected: 1,
        },
        clicks: {
            current: 300,
            previous: 200,
            change: 50,
            covered: 1,
            expected: 1,
        },
    },
    trend: [
        {
            date: "2026-10-01",
            visitors: 600,
            previous_visitors: 500,
            clicks: 100,
        },
    ],
    insights: [],
    notice: "Shared properties count once.",
};
const snapshot = (rows: Record<string, string | number>[]) => ({
    current: {
        rows,
        total: rows.length,
        updated_at: "2026-10-18T00:00:00Z",
        measurement: "GA4",
        complete: true,
    },
    previous: null,
});
const dashboard: DashboardData = {
    ...period,
    site,
    parameters: [
        {parameterName: "button_location", displayName: "Button location"},
    ],
    insights: [],
    reports: {
        ga4: {
            channels: snapshot([
                {sessionDefaultChannelGroup: "Organic Search", sessions: 800},
            ]),
            pages: snapshot([
                {pageLocation: "https://example.com/services", sessions: 450},
            ]),
            events: snapshot([{eventName: "button_click", eventCount: 75}]),
            countries: snapshot([
                {country: "United Kingdom", activeUsers: 800},
            ]),
        },
        gsc: {
            queries: snapshot([
                {query: "custom software", clicks: 120, impressions: 4000},
            ]),
        },
    },
};
beforeEach(() => {
    vi.mocked(useExperience).mockReturnValue({
        session,
        period,
        comparison: true,
        refreshSession: vi.fn(),
    });
});
afterEach(() => {
    cleanup();
    vi.resetAllMocks();
});

describe("portfolio experience", () => {
    it("shows cross-site metrics and website links with the selected dates", async () => {
        vi.mocked(api).mockResolvedValue(portfolio);
        render(<PortfolioPage />);
        expect(
            await screen.findByRole("heading", {
                name: "Every website. One clear view.",
            }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", {name: /Visitors across sites: 1,200/}),
        ).toHaveAttribute("aria-pressed", "true");
        expect(
            screen.getByRole("link", {name: /example.com Analytics/}),
        ).toHaveAttribute(
            "href",
            "/dashboard/websites/1?start=2026-10-01&end=2026-10-02",
        );
        fireEvent.click(
            screen.getByRole("button", {name: /Search clicks: 300/}),
        );
        expect(
            screen.getByLabelText("Search clicks over time"),
        ).toBeInTheDocument();
        fireEvent.change(screen.getByLabelText("Find a website"), {
            target: {value: "missing"},
        });
        expect(
            screen.getByText("No websites match that search"),
        ).toBeInTheDocument();
    });
    it("shows unavailable metrics and incomplete coverage without manufacturing zeros", async () => {
        vi.mocked(api).mockResolvedValue({
            ...portfolio,
            metrics: {
                visitors: {
                    current: null,
                    previous: null,
                    change: null,
                    covered: 0,
                    expected: 2,
                },
            },
        });
        render(<PortfolioPage />);
        const card = await screen.findByRole("button", {
            name: /Visitors across sites: —/,
        });
        expect(card).toHaveTextContent("0 of 2 reporting properties covered");
        expect(card).toHaveTextContent("No comparison");
    });
    it("offers a retry on fetch errors", async () => {
        vi.mocked(api)
            .mockRejectedValueOnce(new Error("Connection interrupted"))
            .mockResolvedValue(portfolio);
        render(<PortfolioPage />);
        expect(await screen.findByRole("alert")).toHaveTextContent(
            "Connection interrupted",
        );
        fireEvent.click(screen.getByRole("button", {name: "Try again"}));
        expect(
            await screen.findByRole("heading", {name: /Your websites/}),
        ).toBeInTheDocument();
    });
    it("keeps date and comparison changes in the route", async () => {
        vi.mocked(api).mockResolvedValue(portfolio);
        render(<PortfolioPage />);
        await screen.findByRole("heading", {name: /Your websites/});
        fireEvent.click(screen.getByLabelText("Compare previous period"));
        expect(navigation.replace).toHaveBeenCalledWith("/dashboard?compare=0");
        fireEvent.change(screen.getByLabelText("From"), {
            target: {value: "2026-09-28"},
        });
        fireEvent.click(screen.getByRole("button", {name: "Apply dates"}));
        expect(navigation.replace).toHaveBeenCalledWith(
            "/dashboard?start=2026-09-28&end=2026-10-02",
        );
    });
});

describe("unified website dashboard", () => {
    it("brings sources, content, events, search and audience together with event parameter investigation", async () => {
        vi.mocked(api).mockImplementation(
            async (path) =>
                (path.includes("/dashboard?")
                    ? dashboard
                    : path.includes("/parameters?")
                      ? {
                            rows: [
                                {
                                    "customEvent:button_location": "hero",
                                    eventCount: 42,
                                },
                            ],
                        }
                      : {rows: [{date: "20261001", eventCount: 75}]}) as never,
        );
        render(<WebsiteDashboard websiteId={1} />);
        for (const name of [
            "Traffic sources",
            "Top content",
            "Events & key actions",
            "Search discovery",
            "Your audience",
        ])
            expect(
                await screen.findByRole("heading", {name}),
            ).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", {name: /button_click/}));
        expect(screen.getByRole("dialog")).toHaveAccessibleName("button_click");
        fireEvent.change(await screen.findByLabelText("Event parameter"), {
            target: {value: "button_location"},
        });
        expect(await screen.findByText("hero")).toBeInTheDocument();
        expect(
            vi
                .mocked(api)
                .mock.calls.some(
                    ([path]) =>
                        path.includes("/events/button_click/parameters?") &&
                        path.includes("parameter=button_location"),
                ),
        ).toBe(true);
        fireEvent.click(screen.getByRole("button", {name: "Close detail"}));
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
    it("keeps administration out of a viewer's reporting journey", async () => {
        vi.mocked(useExperience).mockReturnValue({
            session: {
                ...session,
                businesses: [{...session.businesses[0], role: "viewer"}],
            },
            period,
            comparison: true,
            refreshSession: vi.fn(),
        });
        vi.mocked(api).mockResolvedValue(dashboard);
        render(<WebsiteDashboard websiteId={1} />);
        await screen.findByRole("heading", {name: "Traffic sources"});
        expect(
            screen.queryByRole("link", {name: "Manage website"}),
        ).not.toBeInTheDocument();
        expect(
            screen.queryByRole("button", {name: "Sync date range"}),
        ).not.toBeInTheDocument();
        expect(
            screen.getByRole("link", {name: /Open explorer/}),
        ).toBeInTheDocument();
    });
    it("does not fetch a website outside the session scope", async () => {
        render(<WebsiteDashboard websiteId={99} />);
        expect(screen.getByRole("alert")).toHaveTextContent(
            "not available in your workspace",
        );
        await waitFor(() => expect(api).not.toHaveBeenCalled());
    });
    it("guards settings for viewers", () => {
        vi.mocked(useExperience).mockReturnValue({
            session: {
                ...session,
                businesses: [{...session.businesses[0], role: "viewer"}],
            },
            period,
            comparison: true,
            refreshSession: vi.fn(),
        });
        render(<SettingsPage websiteId={1} />);
        expect(
            screen.getByText(
                /Your workspace administrator manages connections/,
            ),
        ).toBeInTheDocument();
        expect(
            screen.queryByRole("button", {name: "Events & configuration"}),
        ).not.toBeInTheDocument();
    });
});

describe("honest chart comparisons", () => {
    it("aligns previous dates by calendar offset, preserving missing days", () => {
        expect(
            series(
                [{date: "20261002", totalUsers: 12}],
                [{date: "20260929", totalUsers: 8}],
                "totalUsers",
                period,
            ),
        ).toEqual([
            {
                date: "2026-10-01",
                previous_date: "2026-09-29",
                value: null,
                previous: 8,
            },
            {
                date: "2026-10-02",
                previous_date: "2026-09-30",
                value: 12,
                previous: null,
            },
        ]);
    });
    it("distinguishes real zero activity from absent or nonfinite data", () => {
        expect(compact(0)).toBe("0");
        expect(compact(null)).toBe("—");
        expect(compact(Infinity)).toBe("—");
    });
});
