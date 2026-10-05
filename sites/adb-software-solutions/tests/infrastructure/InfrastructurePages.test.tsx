import "@testing-library/jest-dom";
import {
    INFRASTRUCTURE_CATEGORIES,
    InfrastructureCategoryPage,
} from "@/app/(admin)/admin/infrastructure/InfrastructureCategoryPage";
import { RESOURCE_TYPES } from "@/app/(admin)/admin/infrastructure/resources/resourceCreation";
import ServersPage from "@/app/(admin)/admin/infrastructure/servers/page";
import DatabasesPage from "@/app/(admin)/admin/infrastructure/databases/page";
import WebsitesPage from "@/app/(admin)/admin/infrastructure/websites/page";
import DomainsPage from "@/app/(admin)/admin/infrastructure/domains/page";
import CertificatesPage from "@/app/(admin)/admin/infrastructure/ssl-certificates/page";
import ApplicationsPage from "@/app/(admin)/admin/infrastructure/applications/page";
import LicencesPage from "@/app/(admin)/admin/infrastructure/licences/page";
import MobileAppsPage from "@/app/(admin)/admin/infrastructure/mobile-apps/page";
import APIsPage from "@/app/(admin)/admin/infrastructure/apis/page";
import BotsPage from "@/app/(admin)/admin/infrastructure/bots/page";
import EmailSystemsPage from "@/app/(admin)/admin/infrastructure/email-systems/page";
import { InfrastructureResourcesWorkspace } from "@/app/(admin)/admin/infrastructure/resources/InfrastructureResourcesWorkspace";
import { TechnologyWorkspace } from "@/app/(admin)/admin/infrastructure/tech-stack/TechnologyWorkspace";
import { InfrastructureOverview } from "@/app/(admin)/admin/infrastructure/InfrastructureOverview";
import { SpecialistOperationsWorkspace } from "@/app/(admin)/admin/infrastructure/operations/SpecialistOperationsWorkspace";
import { TopologyWorkspace } from "@/app/(admin)/admin/infrastructure/topology/TopologyWorkspace";
import { fetchAPI } from "@/lib/api/fetch";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("@/lib/api/fetch", () => ({ fetchAPI: jest.fn() }));
jest.mock("@/contexts/AuthContext", () => ({
    useAuth: () => ({ hasPermission: () => true }),
}));
jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/[id]/InfrastructureResourceWorkspace",
    () => ({
        InfrastructureResourceWorkspace: ({
            resourceId,
        }: {
            resourceId: number;
        }) => <div>Resource detail {resourceId}</div>,
    }),
);
jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/StructuredInfrastructureForm",
    () => ({
        StructuredInfrastructureForm: () => <div>Compute form</div>,
    }),
);
jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/DataApplicationInfrastructureForm",
    () => ({
        DataApplicationInfrastructureForm: () => <div>Data form</div>,
    }),
);
jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/WebDomainInfrastructureForm",
    () => ({
        WebDomainInfrastructureForm: ({
            allowedTypes,
        }: {
            allowedTypes: string[];
        }) => <div>Web form: {allowedTypes.join(",")}</div>,
    }),
);

jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/OperationalInfrastructureForm",
    () => ({
        OperationalInfrastructureForm: () => <div>Operational form</div>,
    }),
);

const mockFetch = jest.mocked(fetchAPI);
const resource = {
    id: 42,
    name: "Tracked resource",
    resource_type: "domain",
    lifecycle_status: "active",
    environment: "production",
    criticality: "normal",
    ownership_type: "internal",
    client_id: null,
    client_name: null,
    tags: [],
    updated_at: "2026-10-01T12:00:00Z",
    expires_on: "2026-11-01",
    expires_at: null,
    auto_renew: true,
};
const inventory = {
    items: [resource],
    page: 1,
    page_size: 25,
    total: 1,
    total_pages: 1,
};

beforeEach(() => {
    mockFetch.mockReset();
    mockFetch.mockResolvedValue(inventory);
});

const categories = [
    ["server", "Servers", ServersPage],
    ["database_instance", "Databases", DatabasesPage],
    ["website", "Websites", WebsitesPage],
    ["domain", "Domains", DomainsPage],
    ["tls_certificate", "SSL Certificates", CertificatesPage],
    ["application", "Applications", ApplicationsPage],
    ["licence", "Licences", LicencesPage],
    ["mobile_app", "Mobile Apps", MobileAppsPage],
    ["api", "APIs", APIsPage],
    ["bot", "Bots", BotsPage],
    ["email_system", "Email Systems", EmailSystemsPage],
] as const;

test.each(categories)(
    "%s category loads native resources and opens their details",
    async (resourceType, title, Page) => {
        mockFetch.mockResolvedValue({
            ...inventory,
            items: [{ ...resource, resource_type: resourceType }],
        });
        render(<Page />);
        const button = await screen.findByRole("button", {
            name: "Tracked resource",
        });
        expect(
            screen.getByRole("heading", { name: title, level: 1 }),
        ).toBeInTheDocument();
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining(`/infrastructure/resources?`),
        );
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining(`resource_type=${resourceType}`),
        );
        expect(
            screen.getByRole("combobox", { name: "Resource type" }),
        ).toBeDisabled();
        expect(
            screen.queryByRole("link", { name: /reconcil/i }),
        ).not.toBeInTheDocument();
        fireEvent.click(button);
        expect(
            await screen.findByText("Resource detail 42"),
        ).toBeInTheDocument();
    },
);

test("Domains shows expiry and limits creation to domain profiles", async () => {
    render(<DomainsPage />);
    await screen.findByRole("button", { name: "Tracked resource" });
    expect(
        screen.getByRole("columnheader", { name: "Expires" }),
    ).toBeInTheDocument();
    expect(screen.getByText("1 Nov 2026")).toBeInTheDocument();
    expect(screen.getByText("Yes")).toBeInTheDocument();
    expect(
        screen.queryByRole("button", { name: "Add compute / network" }),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Add resource" }));
    expect(screen.getByText("Web form: domain")).toBeInTheDocument();
});

test("category search and pagination retain the fixed resource type", async () => {
    mockFetch.mockResolvedValue({ ...inventory, total: 26, total_pages: 2 });
    render(<DomainsPage />);
    await screen.findByRole("button", { name: "Tracked resource" });
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() =>
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringMatching(/page=2.*resource_type=domain/),
        ),
    );
    fireEvent.change(
        screen.getByRole("textbox", { name: "Search resources" }),
        { target: { value: "example" } },
    );
    await waitFor(() =>
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringMatching(
                /page=1.*search=example.*resource_type=domain/,
            ),
        ),
    );
});

test("Resources keeps the unfiltered native register", async () => {
    render(<InfrastructureResourcesWorkspace />);
    await screen.findByRole("button", { name: "Tracked resource" });
    expect(
        screen.getByRole("combobox", { name: "Resource type" }),
    ).not.toBeDisabled();
    expect(mockFetch.mock.calls[0][0]).not.toContain("resource_type=");
});

test("a failed inventory request displays the error and retries", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Permission denied"));
    render(<DomainsPage />);
    expect(await screen.findByText("Permission denied")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /try again|retry/i }));
    expect(
        await screen.findByRole("button", { name: "Tracked resource" }),
    ).toBeInTheDocument();
});

test("Technology Stack loads native metadata with resource deep links and search", async () => {
    mockFetch.mockResolvedValue({
        ...inventory,
        items: [
            {
                id: "42:cms",
                resource_id: 42,
                resource_name: "Example Website",
                technology: "WordPress",
                category: "CMS",
                version: "6.8",
            },
        ],
    });
    render(<TechnologyWorkspace />);
    expect(await screen.findByText("WordPress")).toBeInTheDocument();
    expect(
        screen.getByRole("link", { name: "Example Website" }),
    ).toHaveAttribute("href", "/admin/infrastructure/resources/42");
    expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/infrastructure/technology?"),
    );
    fireEvent.change(
        screen.getByRole("textbox", { name: "Search technology resources" }),
        { target: { value: "Website" } },
    );
    await waitFor(() =>
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining("search=Website"),
        ),
    );
});

test("overview shows native domain counts and links to the domain register", async () => {
    mockFetch.mockResolvedValue({
        server_count: 0,
        database_count: 0,
        website_count: 0,
        domain_count: 2,
        expiring_domain_count: 1,
        ssl_certificate_count: 0,
        expiring_certificate_count: 0,
        licence_count: 0,
        application_count: 0,
        mobile_app_count: 0,
        api_count: 0,
        bot_count: 0,
        email_system_count: 0,
    });
    render(<InfrastructureOverview />);
    expect(
        await screen.findByText("1 expire within 45 days"),
    ).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(
        screen.getByRole("link", { name: /Domains Registrations/ }),
    ).toHaveAttribute("href", "/admin/infrastructure/domains");
});

test("operational registers paginate and reset the page when changing type", async () => {
    mockFetch.mockImplementation(async (url: string) => {
        const query = new URL(url).searchParams;
        return {
            ...inventory,
            page: Number(query.get("page")),
            total: 26,
            total_pages: 2,
        };
    });
    render(<SpecialistOperationsWorkspace />);
    expect(await screen.findByRole("link", { name: "Open" })).toHaveAttribute(
        "href",
        "/admin/infrastructure/resources/42",
    );
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() =>
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining("page=2"),
        ),
    );
    fireEvent.change(
        screen.getByRole("combobox", { name: "Operational resource type" }),
        { target: { value: "storage" } },
    );
    await waitFor(() =>
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringMatching(/resource_type=storage.*page=1/),
        ),
    );
});

test("topology loads native resources and can search beyond the initial selection", async () => {
    mockFetch.mockImplementation(async (url: string) => {
        if (url.includes("/topology?"))
            return {
                root_id: 42,
                depth: 1,
                nodes: [],
                edges: [],
                truncated: false,
            };
        return inventory;
    });
    render(<TopologyWorkspace />);
    expect(
        await screen.findByRole("option", {
            name: "Tracked resource · Internal",
        }),
    ).toBeInTheDocument();
    await waitFor(() =>
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining("/resources/42/topology?depth=1"),
        ),
    );
    fireEvent.change(
        screen.getByRole("textbox", { name: "Search topology resources" }),
        { target: { value: "domain" } },
    );
    await waitFor(() =>
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining("search=domain"),
        ),
    );
});

test("every creatable resource type has an inventory category", () => {
    expect(
        Object.values(INFRASTRUCTURE_CATEGORIES)
            .map((category) => category.resourceType)
            .sort(),
    ).toEqual([...RESOURCE_TYPES].sort());
});

test.each(
    Object.keys(
        INFRASTRUCTURE_CATEGORIES,
    ) as (keyof typeof INFRASTRUCTURE_CATEGORIES)[],
)("%s inventory uses its native type filter", async (category) => {
    const configuration = INFRASTRUCTURE_CATEGORIES[category];
    render(<InfrastructureCategoryPage category={category} />);
    await screen.findByRole("button", { name: "Tracked resource" });
    expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(`resource_type=${configuration.resourceType}`),
    );
    expect(
        screen.getByRole("heading", { name: configuration.title, level: 1 }),
    ).toBeInTheDocument();
});
