import "@testing-library/jest-dom";
import { fireEvent, render, screen } from "@testing-library/react";
import { Analytics } from "@adb/ui/public/Analytics";
import { PrivacyPreferences } from "@adb/ui/public/PrivacyPreferences";
import { ThemeToggle } from "@adb/ui/public/ThemeToggle";
import { savePrivacyPreferences } from "@adb/ui/public/privacy";

jest.mock("next/navigation", () => ({ usePathname: () => "/contact/" }));
const id = "G-DEMO1234";
type Browser = Window & {
    dataLayer?: unknown[][];
    gtag?: (...arguments_: unknown[]) => void;
};
const browser = window as Browser;
function events() {
    return browser.dataLayer || [];
}
beforeEach(() => {
    savePrivacyPreferences({ rememberTheme: true, analytics: true });
    localStorage.clear();
    document.getElementById("adb-ga4")?.remove();
    browser.dataLayer = [];
    browser.gtag = undefined;
    document.cookie = "_ga=; Max-Age=0; Path=/";
    document.cookie = "_ga_DEMO=; Max-Age=0; Path=/";
});

it("loads standard GA4 by default with advertising denied and sanitised page locations", () => {
    history.replaceState(null, "", "/contact/?email=private@example.com");
    render(<Analytics measurementId={id} />);
    expect(document.getElementById("adb-ga4")).toHaveAttribute(
        "src",
        `https://www.googletagmanager.com/gtag/js?id=${id}`,
    );
    expect(events()).toContainEqual([
        "consent",
        "default",
        {
            analytics_storage: "granted",
            ad_storage: "denied",
            ad_user_data: "denied",
            ad_personalization: "denied",
        },
    ]);
    const pageView = events().find((event) => event[0] === "event");
    expect(pageView?.[2]).toHaveProperty(
        "page_location",
        `${location.origin}/contact/`,
    );
    expect(JSON.stringify(pageView)).not.toContain("private@example.com");
});

it("honours saved objection before loading any Google script and can re-enable collection", () => {
    savePrivacyPreferences({ rememberTheme: true, analytics: false });
    render(
        <>
            <Analytics measurementId={id} />
            <PrivacyPreferences />
        </>,
    );
    expect(document.getElementById("adb-ga4")).toBeNull();
    const analytics = screen.getByRole("checkbox", {
        name: /Google Analytics/,
    });
    expect(analytics).not.toBeChecked();
    fireEvent.click(analytics);
    fireEvent.click(
        screen.getByRole("button", { name: "Save privacy choices" }),
    );
    expect(document.getElementById("adb-ga4")).not.toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent("saved");
});

it("stops collection immediately and deletes analytics cookies while preserving security cookies", () => {
    render(
        <>
            <Analytics measurementId={id} />
            <PrivacyPreferences />
        </>,
    );
    document.cookie = "_ga=sample; Path=/";
    document.cookie = "_ga_DEMO=sample; Path=/";
    document.cookie = "csrftoken=keep; Path=/";
    const count = events().filter((event) => event[0] === "event").length;
    fireEvent.click(screen.getByRole("checkbox", { name: /Google Analytics/ }));
    fireEvent.click(
        screen.getByRole("button", { name: "Save privacy choices" }),
    );
    expect(
        (window as unknown as Record<string, unknown>)[`ga-disable-${id}`],
    ).toBe(true);
    expect(document.cookie).not.toContain("_ga=");
    expect(document.cookie).not.toContain("_ga_DEMO=");
    expect(document.cookie).toContain("csrftoken=keep");
    expect(events().filter((event) => event[0] === "event")).toHaveLength(
        count,
    );
});

it("removes the saved theme and keeps the theme switch usable without saving again", () => {
    localStorage.setItem("adb-public-theme", "light");
    render(
        <>
            <PrivacyPreferences />
            <ThemeToggle />
        </>,
    );
    fireEvent.click(screen.getByRole("checkbox", { name: /Remember my/ }));
    fireEvent.click(
        screen.getByRole("button", { name: "Save privacy choices" }),
    );
    expect(localStorage.getItem("adb-public-theme")).toBeNull();
    fireEvent.click(
        screen.getByRole("button", { name: "Switch to dark mode" }),
    );
    expect(localStorage.getItem("adb-public-theme")).toBeNull();
    expect(
        screen.getByRole("button", { name: "Switch to light mode" }),
    ).toBeInTheDocument();
});

it("does not load an invalid or missing measurement ID", () => {
    render(<Analytics measurementId="" />);
    expect(document.getElementById("adb-ga4")).toBeNull();
});
