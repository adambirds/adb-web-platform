import {
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
} from "@testing-library/react";
import {afterEach, describe, expect, it, vi} from "vitest";
import {GoogleOnboarding} from "../src/app/onboarding";
import {api, type Business} from "../src/app/client";

vi.mock("../src/app/client", async (original) => ({
    ...(await original<typeof import("../src/app/client")>()),
    api: vi.fn(),
}));
afterEach(() => {
    cleanup();
    vi.resetAllMocks();
    window.history.replaceState(null, "", "/");
});
const business: Business = {
    id: 1,
    name: "My websites",
    slug: "my-websites",
    role: "owner",
    websites: [],
};
const site = {
    domain: "example.com",
    existing_id: null,
    ga4: [{id: "properties/123", name: "Example", timezone: "Europe/London"}],
    gsc: [{id: "sc-domain:example.com", name: "sc-domain:example.com"}],
};

function mockInventory(websites = [site]) {
    vi.mocked(api).mockImplementation(async (path, method) => {
        if (path.endsWith("/connections"))
            return [
                {id: 2, email: "owner@example.com", status: "connected"},
            ] as never;
        if (method === "POST") return {websites: [{id: 7}]} as never;
        return {websites, warnings: []} as never;
    });
}

describe("Google-first website onboarding", () => {
    it("discovers after connection, imports ticked websites and inferred providers without a timezone field", async () => {
        mockInventory();
        const complete = vi.fn().mockResolvedValue(undefined);
        render(<GoogleOnboarding business={business} onComplete={complete} />);
        expect(await screen.findByText("example.com")).toBeInTheDocument();
        expect(api).toHaveBeenCalledWith("/connections/2/websites");
        expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
        expect(
            screen.getByText(/Timezone · Europe\/London/),
        ).toBeInTheDocument();
        fireEvent.click(screen.getByRole("checkbox"));
        fireEvent.click(screen.getByRole("button", {name: "Add 1 website"}));
        await waitFor(() => expect(complete).toHaveBeenCalledOnce());
        expect(api).toHaveBeenCalledWith("/connections/2/websites", "POST", {
            websites: [
                {
                    domain: "example.com",
                    ga4: "properties/123",
                    gsc: "sc-domain:example.com",
                },
            ],
        });
        expect(api).toHaveBeenCalledWith("/preferences", "PUT", {
            website_id: 7,
        });
        expect(window.location.pathname).toBe("/dashboard");
    });
    it("requires a property choice when a domain has multiple GA4 properties", async () => {
        mockInventory([
            {
                ...site,
                ga4: [
                    ...site.ga4,
                    {
                        id: "properties/456",
                        name: "Old example",
                        timezone: "UTC",
                    },
                ],
            },
        ]);
        render(<GoogleOnboarding business={business} onComplete={vi.fn()} />);
        await screen.findByText("example.com");
        fireEvent.click(screen.getByRole("checkbox"));
        expect(
            screen.getByRole("button", {name: "Add 1 website"}),
        ).toBeDisabled();
        fireEvent.change(screen.getByLabelText("Analytics property"), {
            target: {value: "properties/456"},
        });
        expect(
            screen.getByRole("button", {name: "Add 1 website"}),
        ).toBeEnabled();
        expect(screen.getByText(/Timezone · UTC/)).toBeInTheDocument();
    });
    it("shows discovery failures with a usable retry and no manual website form", async () => {
        vi.mocked(api).mockImplementation(async (path) => {
            if (path.endsWith("/connections"))
                return [
                    {id: 2, email: "owner@example.com", status: "connected"},
                ] as never;
            throw new Error("Google permission denied");
        });
        render(<GoogleOnboarding business={business} onComplete={vi.fn()} />);
        expect(await screen.findByRole("alert")).toHaveTextContent(
            "Google permission denied",
        );
        expect(
            screen.getByRole("button", {name: "Refresh websites"}),
        ).toBeEnabled();
        expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    });
    it("explains an empty account and supports connecting another account", async () => {
        mockInventory([]);
        render(<GoogleOnboarding business={business} onComplete={vi.fn()} />);
        expect(
            await screen.findByRole("heading", {name: "No websites found"}),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", {
                name: "Connect another Google account",
            }),
        ).toBeEnabled();
    });
});
