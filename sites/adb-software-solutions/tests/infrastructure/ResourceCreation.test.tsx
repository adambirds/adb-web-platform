import "@testing-library/jest-dom";
import { CatalogueResourceForm } from "@/app/(admin)/admin/infrastructure/resources/CatalogueResourceForm";
import { InfrastructureCreateForm } from "@/app/(admin)/admin/infrastructure/resources/InfrastructureCreateForm";
import {
    RESOURCE_TYPES,
    RESOURCE_CREATION,
    canCreateResource,
} from "@/app/(admin)/admin/infrastructure/resources/resourceCreation";
import { InfrastructureResourcesWorkspace } from "@/app/(admin)/admin/infrastructure/resources/InfrastructureResourcesWorkspace";
import ProviderAccountsPage from "@/app/(admin)/admin/infrastructure/provider-accounts/page";
import { ServerNetworkingCard } from "@/app/(admin)/admin/infrastructure/resources/[id]/ServerNetworkingCard";
import { ResourceTagsCard } from "@/app/(admin)/admin/infrastructure/resources/[id]/ResourceTagsCard";
import { fetchAPI } from "@/lib/api/fetch";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("@/lib/api/fetch", () => ({ fetchAPI: jest.fn() }));
const mockPermission = jest.fn((permission: string) => Boolean(permission));
jest.mock("@/contexts/AuthContext", () => ({
    useAuth: () => ({ hasPermission: mockPermission }),
}));
jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/StructuredInfrastructureForm",
    () => ({
        StructuredInfrastructureForm: ({
            allowedTypes,
        }: {
            allowedTypes: string[];
        }) => <div>Compute form {allowedTypes[0]}</div>,
    }),
);
jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/DataApplicationInfrastructureForm",
    () => ({
        DataApplicationInfrastructureForm: ({
            allowedTypes,
        }: {
            allowedTypes: string[];
        }) => <div>Data form {allowedTypes[0]}</div>,
    }),
);
jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/WebDomainInfrastructureForm",
    () => ({
        WebDomainInfrastructureForm: ({
            allowedTypes,
        }: {
            allowedTypes: string[];
        }) => <div>Web form {allowedTypes[0]}</div>,
    }),
);
jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/OperationalInfrastructureForm",
    () => ({
        OperationalInfrastructureForm: ({
            allowedTypes,
        }: {
            allowedTypes: string[];
        }) => <div>Operational form {allowedTypes[0]}</div>,
    }),
);
jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/[id]/InfrastructureResourceWorkspace",
    () => ({
        InfrastructureResourceWorkspace: () => (
            <div>Created resource workspace</div>
        ),
    }),
);

const mockFetch = jest.mocked(fetchAPI);
const provider = {
    id: 7,
    name: "Example Cloud",
    slug: "example-cloud",
    category: "cloud",
    website_url: "",
    support_url: "",
    status_page_url: "",
    documentation_url: "",
    notes: "",
    is_active: true,
};
const options = {
    clients: [{ id: 3, name: "Example Client" }],
    providers: [provider],
};
const native = {
    id: 42,
    name: "Provider account",
    resource_type: "provider_account",
    lifecycle_status: "active",
    environment: "shared",
    ownership_type: "internal",
    client_id: null,
    client_name: null,
    criticality: "normal",
    tags: [],
};

beforeEach(() => {
    mockPermission.mockReset();
    mockPermission.mockReturnValue(true);
    mockFetch.mockReset();
    mockFetch.mockImplementation(async (url: string, request?: RequestInit) => {
        if (url.includes("/catalogue-options")) return options;
        if (url.includes("/service-providers") && request?.method === "POST")
            return { ...provider, id: 8, name: "New Cloud", slug: "new-cloud" };
        if (url.includes("/specialist-options"))
            return {
                networks: [{ resource_id: 10, name: "VPC" }],
                subnets: [
                    {
                        resource_id: 11,
                        network_resource_id: 10,
                        cidr: "10.0.0.0/24",
                    },
                ],
            };
        if (url.includes("/servers/42") && !request?.method)
            return {
                interfaces: [
                    { id: 12, name: "eth0", mac_address: "", ip_addresses: [] },
                ],
                direct_ip_addresses: [],
            };
        if (url.includes("/tags") && request?.method === "POST")
            return {
                id: 9,
                name: "Production",
                slug: "production",
                colour: "",
            };
        if (url.includes("/tags?") && !request?.method)
            return { items: [], total: 0 };
        if (request?.method) return { resource_id: 42 };
        return {
            items: [native],
            page: 1,
            page_size: 25,
            total: 1,
            total_pages: 1,
        };
    });
});

test.each(RESOURCE_TYPES)(
    "the create chooser opens the correct %s form",
    async (type) => {
        render(
            <InfrastructureCreateForm
                allowedTypes={RESOURCE_TYPES}
                onCancel={jest.fn()}
                onCreated={jest.fn()}
            />,
        );
        fireEvent.change(
            screen.getByRole("combobox", { name: "Resource to create" }),
            { target: { value: type } },
        );
        const family = RESOURCE_CREATION[type].family;
        if (family === "catalogue")
            expect(
                await screen.findByRole("heading", {
                    name: `Create ${RESOURCE_CREATION[type].label.toLowerCase()}`,
                }),
            ).toBeInTheDocument();
        else
            expect(
                await screen.findByText(
                    `${family === "compute" ? "Compute" : family === "data" ? "Data" : family === "web" ? "Web" : "Operational"} form ${type}`,
                ),
            ).toBeInTheDocument();
    },
);

test("creation requires resource and specialist capabilities", () => {
    expect(
        canCreateResource(
            "server",
            (permission) => permission !== "infrastructure.add_serverprofile",
        ),
    ).toBe(false);
    expect(
        canCreateResource(
            "provider_account",
            (permission) =>
                permission !== "infrastructure.view_serviceprovider",
        ),
    ).toBe(false);
    expect(
        canCreateResource(
            "api",
            (permission) =>
                permission !== "infrastructure.add_infrastructureresource",
        ),
    ).toBe(false);
});

test("Provider Accounts has an obvious creation action and opens the newly created resource", async () => {
    render(<ProviderAccountsPage />);
    fireEvent.click(
        await screen.findByRole("button", { name: "Add resource" }),
    );
    fireEvent.change(
        await screen.findByRole("textbox", { name: "Resource name" }),
        { target: { value: "ADB cloud account" } },
    );
    fireEvent.change(
        screen.getByRole("combobox", { name: "Service provider" }),
        { target: { value: "7" } },
    );
    fireEvent.change(screen.getByRole("textbox", { name: "Tenant ID" }), {
        target: { value: "tenant-123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create resource" }));
    await waitFor(() =>
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining("/provider-accounts"),
            expect.objectContaining({
                method: "POST",
                body: expect.stringContaining('"tenant_id":"tenant-123"'),
            }),
        ),
    );
    expect(
        await screen.findByText("Created resource workspace"),
    ).toBeInTheDocument();
});

test("a service provider can be created inline and selected without losing the account form", async () => {
    render(
        <CatalogueResourceForm
            type="provider_account"
            onCancel={jest.fn()}
            onCreated={jest.fn()}
        />,
    );
    fireEvent.change(
        await screen.findByRole("textbox", { name: "Resource name" }),
        { target: { value: "Unsaved account" } },
    );
    fireEvent.click(
        screen.getByRole("button", { name: "Add service provider" }),
    );
    fireEvent.change(screen.getByRole("textbox", { name: "Provider name" }), {
        target: { value: "New Cloud" },
    });
    fireEvent.click(
        screen.getByRole("button", { name: "Create service provider" }),
    );
    expect(
        await screen.findByRole("option", { name: "New Cloud" }),
    ).toBeInTheDocument();
    expect(
        screen.getByRole("combobox", { name: "Service provider" }),
    ).toHaveValue("8");
    expect(screen.getByRole("textbox", { name: "Resource name" })).toHaveValue(
        "Unsaved account",
    );
});

test.each([
    "api",
    "bot",
    "mobile_app",
    "licence",
    "email_system",
    "network_device",
    "other",
] as const)(
    "creates a client-owned %s using the native basic resource API",
    async (type) => {
        const created = jest.fn();
        render(
            <CatalogueResourceForm
                type={type}
                onCancel={jest.fn()}
                onCreated={created}
            />,
        );
        fireEvent.change(
            await screen.findByRole("textbox", { name: "Resource name" }),
            { target: { value: "Client resource" } },
        );
        fireEvent.change(screen.getByRole("combobox", { name: "Ownership" }), {
            target: { value: "client" },
        });
        fireEvent.change(screen.getByRole("combobox", { name: "Client" }), {
            target: { value: "3" },
        });
        fireEvent.click(
            screen.getByRole("button", { name: "Create resource" }),
        );
        await waitFor(() => expect(created).toHaveBeenCalledWith(42));
        const call = mockFetch.mock.calls.find(
            ([, request]) => request?.method === "POST",
        );
        expect(JSON.parse(String(call?.[1]?.body))).toMatchObject({
            resource_type: type,
            ownership_type: "client",
            client_id: 3,
        });
    },
);

test("failed account creation keeps entered values visible", async () => {
    mockFetch.mockImplementation(async (url: string, request?: RequestInit) => {
        if (request?.method) throw new Error("Provider is inactive");
        return options;
    });
    render(
        <CatalogueResourceForm
            type="provider_account"
            onCancel={jest.fn()}
            onCreated={jest.fn()}
        />,
    );
    fireEvent.change(
        await screen.findByRole("textbox", { name: "Resource name" }),
        { target: { value: "Keep this account" } },
    );
    fireEvent.change(
        screen.getByRole("combobox", { name: "Service provider" }),
        { target: { value: "7" } },
    );
    fireEvent.click(screen.getByRole("button", { name: "Create resource" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
        "Provider is inactive",
    );
    expect(screen.getByRole("textbox", { name: "Resource name" })).toHaveValue(
        "Keep this account",
    );
});

test("server workspace creates an interface and an IP address", async () => {
    const changed = jest.fn();
    render(<ServerNetworkingCard resourceId={42} onChanged={changed} />);
    await screen.findByText("eth0 · No MAC recorded");
    fireEvent.click(screen.getByRole("button", { name: "Add interface" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Interface name" }), {
        target: { value: "eth1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create interface" }));
    await waitFor(() => expect(changed).toHaveBeenCalledTimes(1));
    expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/servers/42/interfaces"),
        expect.objectContaining({
            method: "POST",
            body: expect.stringContaining('"name":"eth1"'),
        }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Add IP address" }));
    fireEvent.change(screen.getByRole("textbox", { name: "IP address" }), {
        target: { value: "10.0.0.5" },
    });
    fireEvent.change(screen.getByRole("combobox", { name: "Interface" }), {
        target: { value: "12" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create IP address" }));
    await waitFor(() => expect(changed).toHaveBeenCalledTimes(2));
    expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/servers/42/ip-addresses"),
        expect.objectContaining({
            method: "POST",
            body: expect.stringContaining('"interface_id":12'),
        }),
    );
});

test("resource tags can be created and attached from the resource workspace", async () => {
    const changed = jest.fn();
    render(<ResourceTagsCard resourceId={42} tags={[]} onChanged={changed} />);
    fireEvent.click(screen.getByRole("button", { name: "Create new tag" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Tag name" }), {
        target: { value: "Production" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create and add tag" }));
    await waitFor(() => expect(changed).toHaveBeenCalled());
    expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/resources/42/tags/9"),
        { method: "PUT" },
    );
});

test("read-only users do not see a resource creation action", async () => {
    mockPermission.mockImplementation(
        (permission: string) => !permission.includes(".add_"),
    );
    render(<ProviderAccountsPage />);
    await screen.findByRole("heading", { name: "Provider Accounts", level: 1 });
    expect(
        screen.queryByRole("button", { name: "Add resource" }),
    ).not.toBeInTheDocument();
});

test("the current resource filter selects the initial creation type", async () => {
    render(<InfrastructureResourcesWorkspace />);
    fireEvent.change(
        await screen.findByRole("combobox", { name: "Resource type" }),
        { target: { value: "provider_account" } },
    );
    fireEvent.click(screen.getByRole("button", { name: "Add resource" }));
    expect(
        screen.getByRole("combobox", { name: "Resource to create" }),
    ).toHaveValue("provider_account");
    expect(
        await screen.findByRole("heading", { name: "Create provider account" }),
    ).toBeInTheDocument();
});

test("provider account edits retain the current inactive vendor and use the scoped edit API", async () => {
    const saved = jest.fn();
    mockFetch.mockImplementation(async (url: string, request?: RequestInit) => {
        if (request?.method) return { resource_id: 42 };
        if (url.includes("/catalogue-options"))
            return { clients: [], providers: [] };
        return {
            name: "Existing account",
            ownership_type: "internal",
            client_id: null,
            lifecycle_status: "active",
            environment: "shared",
            criticality: "normal",
            description: "",
            provider_id: 7,
            provider_name: "Inactive vendor",
            tenant_id: "original",
        };
    });
    render(
        <CatalogueResourceForm
            type="provider_account"
            editResourceId={42}
            onCancel={jest.fn()}
            onSaved={saved}
        />,
    );
    expect(
        await screen.findByRole("option", { name: "Inactive vendor" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Ownership" })).toBeDisabled();
    fireEvent.change(screen.getByRole("textbox", { name: "Tenant ID" }), {
        target: { value: "updated" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save resource" }));
    await waitFor(() => expect(saved).toHaveBeenCalled());
    expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/provider-accounts/42"),
        expect.objectContaining({
            method: "PATCH",
            body: expect.stringContaining('"tenant_id":"updated"'),
        }),
    );
});

test("vendor editing opens populated fields and saves status without recreating it", async () => {
    const { ServiceProvidersWorkspace } =
        await import("@/app/(admin)/admin/infrastructure/service-providers/ServiceProvidersWorkspace");
    mockFetch.mockImplementation(async (_url: string, request?: RequestInit) =>
        request?.method
            ? provider
            : { items: [provider], page: 1, page_size: 25, total: 1 },
    );
    render(<ServiceProvidersWorkspace />);
    fireEvent.click(
        await screen.findByRole("button", { name: "Edit Example Cloud" }),
    );
    expect(screen.getByLabelText("Provider name")).toHaveValue("Example Cloud");
    fireEvent.change(screen.getByLabelText("Provider name"), {
        target: { value: "Updated Cloud" },
    });
    fireEvent.click(screen.getByLabelText("Active provider"));
    fireEvent.click(
        screen.getByRole("button", { name: "Save service provider" }),
    );
    await waitFor(() =>
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining("/service-providers/7"),
            expect.objectContaining({
                method: "PATCH",
                body: expect.stringContaining('"is_active":false'),
            }),
        ),
    );
    expect(
        mockFetch.mock.calls.find(
            ([, request]) => request?.method === "PATCH",
        )?.[1]?.body,
    ).toContain('"name":"Updated Cloud"');
});

test("vendor edit buttons require change permission", async () => {
    const { ServiceProvidersWorkspace } =
        await import("@/app/(admin)/admin/infrastructure/service-providers/ServiceProvidersWorkspace");
    mockPermission.mockImplementation(
        (permission) => permission !== "infrastructure.change_serviceprovider",
    );
    mockFetch.mockResolvedValue({
        items: [provider],
        page: 1,
        page_size: 25,
        total: 1,
    });
    render(<ServiceProvidersWorkspace />);
    await screen.findByText("Example Cloud");
    expect(
        screen.queryByRole("button", { name: "Edit Example Cloud" }),
    ).not.toBeInTheDocument();
});

test.each(["interface", "ip"])(
    "server %s editing retains existing fields and uses PUT",
    async (kind) => {
        const ip = {
            id: 21,
            address: "10.0.0.9",
            scope: "private",
            interface_id: 12,
            ptr_record: "server.example.test",
            is_primary: true,
            description: "Keep IP notes",
        };
        mockFetch.mockImplementation(
            async (url: string, request?: RequestInit) => {
                if (request?.method) return {};
                if (url.includes("specialist-options"))
                    return {
                        networks: [{ resource_id: 10, name: "VPC" }],
                        subnets: [
                            {
                                resource_id: 11,
                                network_resource_id: 10,
                                cidr: "10.0.0.0/24",
                            },
                        ],
                    };
                return {
                    interfaces: [
                        {
                            id: 12,
                            name: "eth0",
                            mac_address: "aa:bb:cc:dd:ee:ff",
                            network_resource_id: 10,
                            subnet_resource_id: 11,
                            mtu: 1500,
                            description: "Keep interface notes",
                            ip_addresses: [ip],
                        },
                    ],
                    direct_ip_addresses: [],
                };
            },
        );
        render(<ServerNetworkingCard resourceId={42} onChanged={jest.fn()} />);
        fireEvent.click(
            await screen.findByRole("button", {
                name:
                    kind === "interface"
                        ? "Edit interface eth0"
                        : "Edit IP 10.0.0.9",
            }),
        );
        expect(screen.getByLabelText("Network record description")).toHaveValue(
            kind === "interface" ? "Keep interface notes" : "Keep IP notes",
        );
        if (kind === "interface") {
            expect(screen.getByLabelText("MTU")).toHaveValue(1500);
            fireEvent.change(screen.getByLabelText("Interface name"), {
                target: { value: "eth1" },
            });
        } else {
            expect(screen.getByLabelText("Primary address")).toBeChecked();
            fireEvent.change(screen.getByLabelText("PTR record"), {
                target: { value: "new.example.test" },
            });
        }
        fireEvent.click(
            screen.getByRole("button", { name: "Save network record" }),
        );
        await waitFor(() =>
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining(
                    kind === "interface"
                        ? "/interfaces/12"
                        : "/ip-addresses/21",
                ),
                expect.objectContaining({ method: "PUT" }),
            ),
        );
    },
);

test("shared tag editing saves metadata without assigning a new tag", async () => {
    const tag = {
        id: 9,
        name: "Production",
        slug: "production",
        colour: "cyan",
    };
    mockFetch.mockImplementation(async (_url: string, request?: RequestInit) =>
        request?.method ? tag : { items: [tag] },
    );
    const changed = jest.fn();
    render(
        <ResourceTagsCard resourceId={42} tags={[tag]} onChanged={changed} />,
    );
    fireEvent.click(
        screen.getByRole("button", { name: "Edit tag Production" }),
    );
    expect(screen.getByLabelText("Tag slug")).toHaveValue("production");
    fireEvent.change(screen.getByLabelText("Tag name"), {
        target: { value: "Live" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save tag" }));
    await waitFor(() => expect(changed).toHaveBeenCalled());
    expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/tags/9"),
        expect.objectContaining({
            method: "PATCH",
            body: expect.stringContaining('"name":"Live"'),
        }),
    );
    expect(
        mockFetch.mock.calls.some(([, request]) => request?.method === "PUT"),
    ).toBe(false);
});

test("repository links can edit role, path and notes in place", async () => {
    const { ApplicationRepositoriesCard } =
        await import("@/app/(admin)/admin/infrastructure/resources/[id]/ApplicationRepositoriesCard");
    const link = {
        id: 5,
        repository_resource_id: 90,
        repository_name: "Repo",
        role: "primary",
        path: "apps/old",
        notes: "Keep notes",
    };
    mockFetch.mockImplementation(async (url: string, request?: RequestInit) => {
        if (request?.method) return link;
        if (url.includes("data-application-options"))
            return {
                source_repositories: [
                    {
                        resource_id: 90,
                        name: "Repo",
                        repository_name: "Repo",
                        ownership_type: "internal",
                        client_id: null,
                    },
                ],
            };
        return [link];
    });
    render(
        <ApplicationRepositoriesCard
            resourceId={42}
            ownershipType="internal"
            clientId={null}
        />,
    );
    fireEvent.click(await screen.findByRole("button", { name: "Edit" }));
    await waitFor(() =>
        expect(screen.getByLabelText("Source repository")).not.toBeDisabled(),
    );
    expect(screen.getByLabelText("Operational notes")).toHaveValue(
        "Keep notes",
    );
    fireEvent.change(screen.getByLabelText("Monorepo path"), {
        target: { value: "apps/new" },
    });
    fireEvent.click(
        screen.getByRole("button", { name: "Save repository link" }),
    );
    await waitFor(() =>
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining("/repositories/5"),
            expect.objectContaining({
                method: "PUT",
                body: expect.stringContaining('"path":"apps/new"'),
            }),
        ),
    );
});

test("certificate domain coverage edits its primary flag in place", async () => {
    const { TLSCertificateDomainsCard } =
        await import("@/app/(admin)/admin/infrastructure/resources/[id]/WebDomainNestedCards");
    const link = {
        id: 5,
        domain_resource_id: 90,
        domain_name: "example.test",
        is_primary: false,
    };
    mockFetch.mockImplementation(async (url: string, request?: RequestInit) => {
        if (request?.method) return link;
        if (url.includes("web-domain-options"))
            return {
                domains: [
                    {
                        resource_id: 90,
                        domain_name: "example.test",
                        ownership_type: "internal",
                        client_id: null,
                    },
                ],
            };
        return [link];
    });
    render(
        <TLSCertificateDomainsCard
            resourceId={42}
            ownershipType="internal"
            clientId={null}
        />,
    );
    fireEvent.click(await screen.findByRole("button", { name: "Edit" }));
    await waitFor(() =>
        expect(screen.getByLabelText("Domain")).not.toBeDisabled(),
    );
    expect(screen.getByLabelText("Domain")).toHaveValue("90");
    fireEvent.click(screen.getByLabelText("Primary certificate name"));
    fireEvent.click(
        screen.getByRole("button", { name: "Save domain coverage" }),
    );
    await waitFor(() =>
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining("/domains/5"),
            expect.objectContaining({
                method: "PUT",
                body: expect.stringContaining('"is_primary":true'),
            }),
        ),
    );
});
