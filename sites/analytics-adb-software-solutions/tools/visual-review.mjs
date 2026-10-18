// Isolated browser-review fixtures: never imported by the application.
import {chromium} from "playwright";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
const output =
    process.env.ANALYTICS_REVIEW_OUTPUT ||
    path.join(os.tmpdir(), "adb-analytics-review");
fs.mkdirSync(output, {recursive: true});
const domains = [
    "adbsoftwaresolutions.co.uk",
    "adbwebdesigns.co.uk",
    "adbtechnology.co.uk",
    "northstarstudio.co.uk",
    "theweekendjournal.com",
    "meadowandmoss.co.uk",
];
const ga = {
    totalUsers: 18420,
    sessions: 24960,
    engagementRate: 0.684,
    averageEngagementTime: 94,
    screenPageViews: 42680,
    keyEvents: 384,
};
const gsc = {clicks: 6340, impressions: 186200, ctr: 0.034, position: 8.4};
const dates = (prev = false) =>
    Array.from({length: 28}, (_, i) =>
        new Date(Date.UTC(2026, 8, prev ? -7 + i : 21 + i))
            .toISOString()
            .slice(0, 10),
    );
const trend = (factor = 1, prev = false) =>
    dates(prev).map((date, i) => ({
        date,
        totalUsers: Math.round(
            (580 + 120 * Math.sin(i * 0.52) + i * 9) * factor,
        ),
        sessions: Math.round(
            (790 + 180 * Math.sin(i * 0.52) + i * 11) * factor,
        ),
        clicks: Math.round((180 + 40 * Math.sin(i * 0.52) + i * 3) * factor),
        keyEvents: Math.round((9 + 3 * Math.sin(i * 0.52) + i * 0.15) * factor),
    }));
const sites = domains.map((domain, i) => ({
    id: i + 1,
    business_id: 1,
    name: domain.split(".")[0],
    domain,
    timezone: "Europe/London",
    providers: ["ga4", "gsc"],
    property_ids: {ga4: `properties/${i + 1}`, gsc: `sc-domain:${domain}`},
    shared_providers: [],
    ga4: {
        current: Object.fromEntries(
            Object.entries(ga).map(([k, v]) => [
                k,
                k === "engagementRate" ? v : Math.round(v / (i + 1)),
            ]),
        ),
        previous: {
            ...ga,
            totalUsers: Math.round(
                ga.totalUsers / (i + 1) / (i === 2 ? 0.68 : 1.24),
            ),
        },
    },
    gsc: {
        current: {...gsc, clicks: Math.round(gsc.clicks / (i + 1))},
        previous: {...gsc, clicks: Math.round(gsc.clicks / (i + 1) / 1.18)},
    },
    trends: {
        ga4: {
            current: trend(1 / (i + 1)),
            previous: trend(0.8 / (i + 1), true),
        },
        gsc: {
            current: trend(1 / (i + 1)),
            previous: trend(0.8 / (i + 1), true),
        },
    },
    insights: [],
    syncing: false,
    updated_at: "2026-10-18T13:20:00Z",
    issues: [],
}));
const insights = [
    {
        id: "drop",
        website_id: 3,
        domain: domains[2],
        title: "Visitors fell 32%",
        detail: "6,140 visitors compared with 9,029 in the previous 28 days. Review traffic sources and landing pages to find where the change is concentrated.",
        action: "Investigate the traffic change",
        level: "attention",
        report: "overview",
        metric: "totalUsers",
        current: 6140,
        previous: 9029,
        change: -32,
        dimension: "",
        value: "",
    },
    {
        id: "growth",
        website_id: 1,
        domain: domains[0],
        title: "Search clicks grew 24%",
        detail: "6,340 clicks compared with 5,113 in the previous period. Compare the queries and pages gaining visibility before drawing conclusions.",
        action: "Explore search performance",
        level: "positive",
        report: "search",
        metric: "clicks",
        current: 6340,
        previous: 5113,
        change: 24,
        dimension: "",
        value: "",
    },
    {
        id: "query",
        website_id: 2,
        domain: domains[1],
        title: "A search query worth a closer look",
        detail: "“bespoke web design” earned 1,240 impressions, a 1.2% click rate and an average position of 7.4. Review the matching page and search snippet.",
        action: "Review this query",
        level: "opportunity",
        report: "queries",
        metric: "ctr",
        current: 0.012,
        previous: null,
        change: null,
        dimension: "query",
        value: "bespoke web design",
    },
];
for (const site of sites)
    site.insights = insights.filter((x) => x.website_id === site.id);
const session = {
    email: "browser-fixture@example.test",
    businesses: [
        {
            id: 1,
            name: "ADB websites",
            slug: "adb",
            role: "owner",
            websites: sites.map((s) => ({
                ...s,
                is_active: true,
                providers: [
                    {
                        provider: "ga4",
                        external_id: s.property_ids.ga4,
                        connection_id: 1,
                        last_synced_at: s.updated_at,
                        error_code: "",
                        metadata: {},
                    },
                    {
                        provider: "gsc",
                        external_id: s.property_ids.gsc,
                        connection_id: 1,
                        last_synced_at: s.updated_at,
                        error_code: "",
                        metadata: {},
                    },
                ],
            })),
        },
    ],
    website_id: 1,
};
const snap = (rows) => ({
    current: {
        rows,
        total: rows.length,
        complete: true,
        updated_at: "2026-10-18T13:20:00Z",
        measurement: "Google",
    },
    previous: null,
});
const channels = [
    "Organic Search",
    "Direct",
    "Referral",
    "Organic Social",
    "Email",
    "Paid Search",
].map((s, i) => ({
    sessionDefaultChannelGroup: s,
    sessions: 9840 - i * 1480,
    engagedSessions: 6200 - i * 930,
    engagementRate: 0.63,
    keyEvents: 120 - i * 18,
}));
const pages = [
    "/",
    "/services/software-development",
    "/work",
    "/services/web-applications",
    "/about",
    "/insights",
    "/contact",
].map((s, i) => ({
    pageLocation: `https://${domains[0]}${s}`,
    hostName: domains[0],
    pagePathPlusQueryString: s,
    landingPagePlusQueryString: s,
    sessions: 6210 - i * 820,
    totalUsers: 4100 - i * 560,
    screenPageViews: 9400 - i * 1100,
    engagementRate: 0.68,
}));
const events = [
    "page_view",
    "user_engagement",
    "scroll",
    "button_click",
    "form_submit",
    "generate_lead",
    "file_download",
].map((s, i) => ({
    eventName: s,
    eventCount: 42680 - i * 6800,
    totalUsers: 18420 - i * 2900,
    keyEvents: i > 3 ? 128 : 0,
}));
const queries = [
    "bespoke software development",
    "software company uk",
    "custom business software",
    "adb software solutions",
    "web application development",
    "software consultancy",
].map((s, i) => ({
    query: s,
    clicks: 1240 - i * 180,
    impressions: 18500 - i * 2300,
    ctr: 0.024 + i * 0.005,
    position: 7.4 + i,
}));
const reports = {
    ga4: {
        overview: snap([ga]),
        trend: snap(trend()),
        channels: snap(channels),
        referrals: snap(
            channels.map((r, i) => ({
                ...r,
                sessionSourceMedium: [
                    "google / organic",
                    "(direct) / (none)",
                    "github.com / referral",
                    "linkedin / social",
                    "newsletter / email",
                    "google / cpc",
                ][i],
            })),
        ),
        acquisition: snap(channels),
        pages: snap(pages),
        landing: snap(pages),
        events: snap(events),
        countries: snap(
            [
                "United Kingdom",
                "United States",
                "Germany",
                "Netherlands",
                "France",
            ].map((country, i) => ({country, activeUsers: 12480 - i * 2700})),
        ),
        devices: snap([
            {deviceCategory: "desktop", activeUsers: 11480},
            {deviceCategory: "mobile", activeUsers: 6420},
            {deviceCategory: "tablet", activeUsers: 520},
        ]),
        browsers: snap([
            {browser: "Chrome", activeUsers: 11020},
            {browser: "Safari", activeUsers: 4800},
            {browser: "Edge", activeUsers: 2600},
        ]),
    },
    gsc: {
        overview: snap([gsc]),
        trend: snap(trend()),
        queries: snap(queries),
        pages: snap(
            pages.map((r, i) => ({
                page: r.pageLocation,
                clicks: 1240 - i * 170,
                impressions: 18000 - i * 2200,
                ctr: 0.034,
                position: 7.4 + i,
            })),
        ),
    },
};
reports.ga4.overview.previous = {
    ...reports.ga4.overview.current,
    rows: [{...ga, totalUsers: 14855, sessions: 21100, keyEvents: 310}],
};
reports.gsc.overview.previous = {
    ...reports.gsc.overview.current,
    rows: [{...gsc, clicks: 5113}],
};
reports.ga4.trend.previous = {
    ...reports.ga4.trend.current,
    rows: trend(0.8, true),
};
reports.gsc.trend.previous = {
    ...reports.gsc.trend.current,
    rows: trend(0.8, true),
};
const portfolio = {
    sites,
    insights,
    start: "2026-09-21",
    end: "2026-10-18",
    notice: "Browser review fixture. Visitors are summed across distinct properties; they are not deduplicated people.",
    metrics: Object.fromEntries(
        ["visitors", "sessions", "clicks", "keyEvents"].map((k, i) => [
            k,
            {
                current: [45129, 61152, 15533, 941][i],
                previous: [38164, 52717, 13163, 798][i],
                change: [18.3, 16, 18, 17.9][i],
                covered: 6,
                expected: 6,
            },
        ]),
    ),
    trend: trend(2.45).map((r, i) => ({
        date: r.date,
        visitors: r.totalUsers,
        sessions: r.sessions,
        clicks: r.clicks,
        keyEvents: r.keyEvents,
        previous_visitors: trend(2, true)[i].totalUsers,
        previous_sessions: trend(2, true)[i].sessions,
        previous_clicks: trend(2, true)[i].clicks,
        previous_keyEvents: trend(2, true)[i].keyEvents,
    })),
};
const consentScopes = [
    "analytics.readonly",
    "webmasters.readonly",
    "analytics.edit",
].map((scope) => "https://www.googleapis.com/auth/" + scope);
const settingsAccounts = [
    {
        id: 1,
        email: "owner@browser-fixture.test",
        status: "connected",
        scopes: consentScopes,
        error_code: "",
        last_refreshed_at: "2026-10-18T13:20:00Z",
    },
    {
        id: 2,
        email: "legacy@browser-fixture.test",
        status: "connected",
        scopes: consentScopes.slice(0, 2),
        error_code: "",
        last_refreshed_at: null,
    },
    {
        id: 3,
        email: "revoked@browser-fixture.test",
        status: "reconnect",
        scopes: consentScopes,
        error_code: "credentials_revoked",
        last_refreshed_at: "2026-10-10T10:00:00Z",
    },
    {
        id: 4,
        email: "retry@browser-fixture.test",
        status: "connected",
        scopes: consentScopes,
        error_code: "google_unavailable",
        last_refreshed_at: "2026-10-18T12:20:00Z",
        refresh_retry_at: "2026-10-18T13:25:00Z",
    },
];
const fixtureMutations = [];
(async () => {
    const browser = await chromium.launch({
        headless: true,
        args: ["--no-sandbox"],
    });
    const page = await browser.newPage({
        viewport: {width: 1440, height: 1100},
        reducedMotion: "reduce",
    });
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.route("**/api/**", async (route) => {
        const url = new URL(route.request().url()),
            p = url.pathname;
        let json;
        if (route.request().method() !== "GET" && p.includes("/api/analytics/"))
            fixtureMutations.push({
                path: p,
                body: route.request().postDataJSON(),
            });
        if (p.endsWith("/csrf"))
            json = {csrf_token: "isolated-browser-fixture"};
        else if (p.endsWith("/oauth")) {
            const body = route.request().postDataJSON();
            const account = settingsAccounts.find(
                (item) => item.id === body.connection_id,
            );
            if (account) {
                account.status = "connected";
                account.scopes = consentScopes;
                account.error_code = "";
            }
            json = {
                url: `${process.env.ANALYTICS_REVIEW_URL || "http://localhost:3105"}/dashboard/settings?tab=accounts&business=1&integration=connected`,
            };
        } else if (p.endsWith("/members"))
            json = [
                {email: session.email, role: "owner"},
                {email: "analyst@browser-fixture.test", role: "viewer"},
            ];
        else if (p.endsWith("/session")) json = session;
        else if (p.endsWith("/portfolio")) json = portfolio;
        else if (p.endsWith("/dashboard"))
            json = {
                site: sites[Number(p.match(/websites\/(\d+)/)[1]) - 1],
                reports,
                insights:
                    sites[Number(p.match(/websites\/(\d+)/)[1]) - 1].insights,
                parameters: [
                    {
                        parameterName: "button_location",
                        displayName: "Button location",
                    },
                ],
                start: portfolio.start,
                end: portfolio.end,
            };
        else if (p.endsWith("/combined"))
            json = {
                rows: [
                    {
                        url: url.searchParams.get("page"),
                        ga4: pages[0],
                        gsc: gsc,
                        ga4_page_trend: trend().map((r) => ({
                            ...r,
                            sessions: r.sessions,
                        })),
                        ga4_page_events: events.slice(3),
                    },
                ],
                notice: "Independent provider measurements.",
            };
        else if (p.endsWith("/parameters"))
            json = {
                rows: [
                    {"customEvent:button_location": "hero", eventCount: 128},
                    {"customEvent:button_location": "footer", eventCount: 64},
                ],
            };
        else if (p.endsWith("/trend"))
            json = {
                rows: trend().map((r) => ({
                    ...r,
                    eventCount: Math.round(r.sessions / 12),
                })),
            };
        else if (p.includes("/reports/"))
            json = {
                current: {
                    rows: events,
                    complete: true,
                    updated_at: sites[0].updated_at,
                    measurement: "GA4",
                },
                previous: null,
                total: events.length,
                status: "available",
            };
        else if (p.endsWith("/realtime"))
            json = {rows: [], totals: {activeUsers: 0, eventCount: 0}};
        else if (p.endsWith("/connections")) json = settingsAccounts;
        else if (p.endsWith("/websites"))
            json = {
                websites: sites.map((site) => ({
                    domain: site.domain,
                    existing_id: site.id,
                    ga4: [
                        {
                            id: site.property_ids.ga4,
                            name: site.name,
                            timezone: site.timezone,
                        },
                    ],
                    gsc: [{id: site.property_ids.gsc, name: site.domain}],
                })),
                warnings: [],
            };
        else if (p.endsWith("/sync")) json = [];
        else json = {items: [], can_edit: true};
        await route.fulfill({json});
    });
    const root = process.env.ANALYTICS_REVIEW_URL || "http://localhost:3105";
    await page.goto(root + "/dashboard?start=2026-09-21&end=2026-10-18");
    await page.getByText("45,129", {exact: true}).waitFor();
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(700);
    await page.screenshot({
        path: path.join(output, "analytics-portfolio-desktop.png"),
        fullPage: true,
    });
    await page.getByRole("button", {name: /Search clicks/}).click();
    assert(
        (await page.locator(".activity-chart").getAttribute("aria-label")) ===
            "Search clicks over time",
    );
    await page.locator('a.site-card[href*="/websites/1?"]').click();
    await page
        .getByRole("heading", {name: "Traffic sources", exact: true})
        .waitFor();
    await page.waitForTimeout(500);
    await page.screenshot({
        path: path.join(output, "analytics-website-desktop.png"),
        fullPage: true,
    });
    await page
        .locator(".site-activity .activity-chart")
        .hover({position: {x: 360, y: 120}});
    await page.locator(".chart-tooltip").waitFor();
    await page
        .locator(".site-activity .activity-chart")
        .click({position: {x: 360, y: 120}});
    await page.getByRole("dialog").waitFor();
    assert(
        (
            await page
                .getByRole("link", {name: /Investigate in explorer/})
                .getAttribute("href")
        ).includes("report=overview"),
    );
    await page.keyboard.press("Escape");
    await page.getByRole("button", {name: /Organic Search/}).click();
    await page.getByRole("heading", {name: "Follow the evidence"}).waitFor();
    await page.keyboard.press("Escape");
    await page
        .getByRole("button", {name: /\/services\/software-development/})
        .click();
    await page
        .getByRole("heading", {name: "Traffic & search, side by side"})
        .waitFor();
    await page.keyboard.press("Escape");
    await page.getByRole("button", {name: /button_click/}).click();
    await page.getByRole("dialog").waitFor();
    await page
        .getByLabel("Event parameter", {})
        .selectOption("button_location");
    await page.getByText("hero", {exact: true}).waitFor();
    await page.screenshot({
        path: path.join(output, "analytics-event-desktop.png"),
        fullPage: true,
    });
    await page.keyboard.press("Escape");
    assert((await page.getByRole("dialog").count()) === 0);
    await page.getByRole("link", {name: "Open explorer"}).click();
    await page.getByRole("heading", {name: "Follow your curiosity."}).waitFor();
    await page.getByText("button_click", {exact: true}).first().waitFor();
    await page.screenshot({
        path: path.join(output, "analytics-explorer-desktop.png"),
        fullPage: true,
    });
    await page
        .getByRole("link", {name: domains[0], exact: true})
        .first()
        .click();
    await page
        .getByRole("heading", {name: "Traffic sources", exact: true})
        .waitFor();
    await page.getByRole("button", {name: "Switch to dark mode"}).click();
    await page.screenshot({
        path: path.join(output, "analytics-website-dark.png"),
        fullPage: true,
    });
    await page.getByRole("button", {name: "Switch to light mode"}).click();
    await page.setViewportSize({width: 390, height: 844});
    await page.screenshot({
        path: path.join(output, "analytics-website-mobile.png"),
        fullPage: true,
    });
    await page.screenshot({
        path: path.join(output, "analytics-website-mobile-viewport.png"),
    });
    assert.equal(
        await page.evaluate(
            () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
        "website mobile overflow",
    );
    await page.getByRole("link", {name: "All websites", exact: true}).click();
    await page.getByText("45,129", {exact: true}).waitFor();
    await page.screenshot({
        path: path.join(output, "analytics-portfolio-mobile.png"),
        fullPage: true,
    });
    assert.equal(
        await page.evaluate(
            () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
        "portfolio mobile overflow",
    );
    for (const width of [768, 1920, 2560]) {
        await page.setViewportSize({width, height: 1100});
        assert.equal(
            await page.evaluate(
                () => document.documentElement.scrollWidth > innerWidth,
            ),
            false,
            `portfolio overflow at ${width}px`,
        );
    }

    await page.setViewportSize({width: 1440, height: 1100});
    await page.goto(root + "/dashboard/settings?tab=websites&business=1");
    await page
        .getByRole("heading", {name: "Your connected websites"})
        .waitFor();
    await page.screenshot({
        path: path.join(output, "analytics-settings-websites-desktop.png"),
        fullPage: true,
    });
    await page.goto(root + "/dashboard/settings?tab=accounts&business=1");
    await page.getByText("Permissions incomplete", {exact: true}).waitFor();
    await page.getByText("Reconnect required", {exact: true}).waitFor();
    await page.getByText("Retry scheduled", {exact: true}).waitFor();
    await page.screenshot({
        path: path.join(output, "analytics-settings-accounts-desktop.png"),
        fullPage: true,
    });
    await page.getByRole("button", {name: "Switch to dark mode"}).click();
    await page.screenshot({
        path: path.join(output, "analytics-settings-accounts-dark.png"),
        fullPage: true,
    });
    await page.setViewportSize({width: 390, height: 844});
    await page.screenshot({
        path: path.join(output, "analytics-settings-accounts-mobile-dark.png"),
        fullPage: true,
    });
    assert.equal(
        await page.evaluate(
            () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
        "settings mobile overflow",
    );
    await page.getByRole("button", {name: "Switch to light mode"}).click();
    await page.screenshot({
        path: path.join(output, "analytics-settings-accounts-mobile.png"),
        fullPage: true,
    });
    assert.equal(
        fixtureMutations.length,
        0,
        "settings browsing must never configure Google",
    );
    await page
        .getByRole("button", {name: "Reauthorise account", exact: true})
        .click();
    await page.getByText("Google account connected.", {exact: false}).waitFor();
    assert(
        fixtureMutations.some(
            (item) =>
                item.path.endsWith("/oauth") &&
                item.body.connection_id === 2 &&
                item.body.return_to === "settings",
        ),
    );
    await page.setViewportSize({width: 1440, height: 1100});
    await page.goto(root + "/dashboard/websites/1/settings?tab=websites");
    await page.getByRole("heading", {name: "Website details"}).waitFor();
    await page.screenshot({
        path: path.join(output, "analytics-settings-website-desktop.png"),
        fullPage: true,
    });
    await page.goto(root + "/dashboard/websites/1/settings?tab=events");
    await page.getByRole("heading", {name: "Events on your website"}).waitFor();
    await page
        .getByRole("button", {name: "generate_lead", exact: true})
        .click();
    assert.equal(
        await page
            .getByLabel("Event name to configure", {exact: true})
            .inputValue(),
        "generate_lead",
    );
    const create = page.getByRole("button", {name: "Review and create"});
    await create.waitFor();
    await page.screenshot({
        path: path.join(output, "analytics-settings-events-desktop.png"),
        fullPage: true,
    });
    page.once("dialog", (dialog) => dialog.accept());
    await create.click();
    await page
        .getByText("Definition created and verified with Google.", {
            exact: true,
        })
        .waitFor();
    assert(
        fixtureMutations.some(
            (item) =>
                item.path.endsWith("/definitions/key-events") &&
                item.body.confirmed === true,
        ),
    );
    await page.setViewportSize({width: 390, height: 844});
    await page.screenshot({
        path: path.join(output, "analytics-settings-events-mobile.png"),
        fullPage: true,
    });
    assert.equal(
        await page.evaluate(
            () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
        "events settings mobile overflow",
    );
    await page.goto(root + "/dashboard/settings?tab=workspace&business=1");
    await page.getByRole("heading", {name: "People & access"}).waitFor();
    await page
        .getByText("analyst@browser-fixture.test", {exact: true})
        .waitFor();
    await page.screenshot({
        path: path.join(output, "analytics-settings-workspace-mobile.png"),
        fullPage: true,
    });
    assert.equal(
        await page.evaluate(
            () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
        "workspace mobile overflow",
    );
    assert.deepEqual(errors, []);
    console.log(
        `Browser review passed: portfolio, unified dashboard, tooltips, day/source/page/event drawers, custom parameters, explorer, themes and 390/768/1440/1920/2560px layouts. Settings areas, account health, scoped reauthorisation and explicitly confirmed key-event configuration also passed. All analytics and Google actions are isolated fixtures. Screenshots: ${output}`,
    );
    await browser.close();
})().catch((e) => {
    console.error(e);
    process.exit(1);
});
