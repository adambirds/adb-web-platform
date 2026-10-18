import {afterEach, beforeEach, expect, it, vi} from "vitest";
import {
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
} from "@testing-library/react";
import {api, type Session} from "../src/app/client";
import {SettingsPage} from "../src/components/experience/SettingsPage";
import {useExperience} from "../src/components/experience/ExperienceProvider";
const navigation = vi.hoisted(() => ({query: "tab=accounts", push: vi.fn()}));
vi.mock("next/navigation", () => ({
    useSearchParams: () => new URLSearchParams(navigation.query),
    useRouter: () => navigation,
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
const period = {start: "2026-10-01", end: "2026-10-15"};
const website = {
    id: 1,
    business_id: 1,
    name: "Example",
    domain: "example.com",
    timezone: "Europe/London",
    is_active: true,
    providers: [
        {
            provider: "ga4" as const,
            connection_id: 1,
            external_id: "properties/123",
            last_synced_at: null,
            error_code: "",
            metadata: {},
        },
    ],
};
const business = {
    id: 1,
    name: "My sites",
    slug: "sites",
    role: "owner" as const,
    websites: [website],
};
const session: Session = {
    email: "owner@example.test",
    website_id: 1,
    businesses: [business],
};
const scopes = [
    "analytics.readonly",
    "webmasters.readonly",
    "analytics.edit",
].map((value) => "https://www.googleapis.com/auth/" + value);
const accounts = [
    {
        id: 1,
        email: "healthy@example.test",
        status: "connected",
        scopes,
        error_code: "",
        last_refreshed_at: "2026-10-18T12:00:00Z",
    },
    {
        id: 2,
        email: "limited@example.test",
        status: "connected",
        scopes: scopes.slice(0, 2),
        error_code: "",
    },
    {
        id: 3,
        email: "revoked@example.test",
        status: "reconnect",
        scopes,
        error_code: "credentials_revoked",
    },
    {
        id: 4,
        email: "retry@example.test",
        status: "connected",
        scopes,
        error_code: "google_unavailable",
        refresh_retry_at: "2026-10-18T13:00:00Z",
    },
];
beforeEach(() => {
    navigation.query = "tab=accounts";
    vi.mocked(useExperience).mockReturnValue({
        session,
        period,
        comparison: true,
        refreshSession: vi.fn(),
    });
    vi.mocked(api).mockImplementation(
        async (path) =>
            (path.endsWith("/connections")
                ? accounts
                : path.endsWith("/members")
                  ? [{email: session.email, role: "owner"}]
                  : path.includes("/definitions/")
                    ? {items: [], can_edit: true}
                    : path.includes("/reports/")
                      ? {
                            current: {
                                rows: [
                                    {
                                        eventName: "generate_lead",
                                        eventCount: 12,
                                        keyEvents: 0,
                                    },
                                ],
                            },
                        }
                      : []) as never,
    );
});
afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.resetAllMocks();
});
it("separates four settings areas and explains account health without exposing credentials", async () => {
    render(<SettingsPage />);
    expect(await screen.findByText("healthy@example.test")).toBeInTheDocument();
    for (const label of [
        "Websites",
        "Google accounts",
        "Events & conversions",
        "Workspace",
    ])
        expect(
            screen.getByRole("link", {name: new RegExp(label)}),
        ).toBeInTheDocument();
    for (const status of [
        "Permissions incomplete",
        "Reconnect required",
        "Retry scheduled",
    ])
        expect(screen.getByText(status)).toBeInTheDocument();
    expect(
        screen.getByRole("button", {name: "Connect Google"}),
    ).toBeInTheDocument();
    expect(
        screen.queryByText("Connect with GA4 administration"),
    ).not.toBeInTheDocument();
    expect(screen.getAllByText(/OAuth consent allows/)[0]).toHaveTextContent(
        "Google also checks your role",
    );
});
it("reauthorises an existing connection with its identity-bound id", async () => {
    vi.mocked(api).mockImplementation(async (path) => {
        if (path.endsWith("/oauth"))
            throw new Error("Provider temporarily unavailable");
        return accounts as never;
    });
    render(<SettingsPage />);
    fireEvent.click(
        await screen.findByRole("button", {name: "Reauthorise account"}),
    );
    await waitFor(() =>
        expect(api).toHaveBeenCalledWith("/businesses/1/oauth", "POST", {
            connection_id: 2,
            return_to: "settings",
        }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
        "Provider temporarily unavailable",
    );
});
it("does not disconnect an account without explicit confirmation", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<SettingsPage />);
    fireEvent.click(
        (
            await screen.findAllByRole("button", {
                name: "Disconnect",
            })
        )[0],
    );
    expect(
        vi.mocked(api).mock.calls.some(([, method]) => method === "POST"),
    ).toBe(false);
});
it("keeps portfolio website cards and individual property settings distinct", async () => {
    navigation.query = "tab=websites";
    const {rerender} = render(<SettingsPage />);
    expect(screen.getByRole("link", {name: "Manage website"})).toHaveAttribute(
        "href",
        "/dashboard/websites/1/settings?start=2026-10-01&end=2026-10-15",
    );
    rerender(<SettingsPage websiteId={1} />);
    expect(
        await screen.findByRole("heading", {name: "Property connected"}),
    ).toBeInTheDocument();
    expect(screen.getByText("properties/123")).toBeInTheDocument();
    expect(
        screen.getAllByText(/Timezone|Europe\/London/i)[0],
    ).toBeInTheDocument();
    expect(screen.getByRole("link", {name: /Workspace/})).toHaveAttribute(
        "href",
        "/dashboard/settings?tab=workspace&business=1",
    );
});
it("offers workspace membership management without requiring a website", async () => {
    navigation.query = "tab=workspace";
    vi.mocked(useExperience).mockReturnValue({
        session: {...session, businesses: [{...business, websites: []}]},
        period,
        comparison: true,
        refreshSession: vi.fn(),
    });
    render(<SettingsPage />);
    expect(
        screen.getByRole("heading", {name: "People & access"}),
    ).toBeInTheDocument();
    expect(await screen.findByText(session.email)).toBeInTheDocument();
    expect(screen.getByLabelText("Workspace name")).toHaveValue("My sites");
});
it("never issues a configuration write when its confirmation is declined", async () => {
    navigation.query = "tab=events";
    vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<SettingsPage websiteId={1} />);
    fireEvent.change(await screen.findByLabelText("Event name to configure"), {
        target: {value: "generate_lead"},
    });
    await waitFor(() =>
        expect(
            screen.getByRole("button", {name: "Review and create"}),
        ).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", {name: "Review and create"}));
    expect(
        vi.mocked(api).mock.calls.some(([, method]) => method === "POST"),
    ).toBe(false);
});
it("retains viewer boundaries even when a settings URL is entered directly", () => {
    vi.mocked(useExperience).mockReturnValue({
        session: {...session, businesses: [{...business, role: "viewer"}]},
        period,
        comparison: true,
        refreshSession: vi.fn(),
    });
    render(<SettingsPage />);
    expect(
        screen.getByText(/administrator manages connections/),
    ).toBeInTheDocument();
    expect(api).not.toHaveBeenCalled();
});

it("does not silently switch to another workspace for an unavailable workspace URL", () => {
    navigation.query = "tab=accounts&business=999";
    render(<SettingsPage />);
    expect(screen.getByRole("alert")).toHaveTextContent(
        "not available to your account",
    );
    expect(api).not.toHaveBeenCalled();
});
it("shows revoked account health on the individual website’s property", async () => {
    navigation.query = "tab=websites";
    vi.mocked(api).mockImplementation(
        async (path) =>
            (path.endsWith("/connections")
                ? [{...accounts[0], status: "reconnect"}]
                : []) as never,
    );
    render(<SettingsPage websiteId={1} />);
    expect(await screen.findByText("Reconnect required")).toBeInTheDocument();
});
it("prefills an observed event as a proposal without writing to Google", async () => {
    navigation.query = "tab=events";
    render(<SettingsPage websiteId={1} />);
    fireEvent.click(await screen.findByRole("button", {name: "generate_lead"}));
    expect(screen.getByLabelText("Event name to configure")).toHaveValue(
        "generate_lead",
    );
    expect(
        vi.mocked(api).mock.calls.some(([, method]) => method === "POST"),
    ).toBe(false);
});
