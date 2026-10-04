import "@testing-library/jest-dom";
import { InfrastructureResourceWorkspace } from "@/app/(admin)/admin/infrastructure/resources/[id]/InfrastructureResourceWorkspace";
import { RESOURCE_TYPES } from "@/app/(admin)/admin/infrastructure/resources/resourceCreation";
import { fetchAPI } from "@/lib/api/fetch";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("@/app/(admin)/admin/credentials/CredentialVault", () => ({
    CredentialVault: () => null,
}));
jest.mock("@/lib/api/fetch", () => ({ fetchAPI: jest.fn() }));
const mockPermission = jest.fn(
    (permission: string) =>
        permission.startsWith("infrastructure.change_") ||
        permission === "infrastructure.view_infrastructureresource" ||
        permission === "infrastructure.view_provideraccount" ||
        permission === "infrastructure.view_serviceprovider",
);
jest.mock("@/contexts/AuthContext", () => ({
    useAuth: () => ({ hasPermission: mockPermission }),
}));
jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/StructuredInfrastructureForm",
    () => ({
        StructuredInfrastructureForm: ({
            allowedTypes,
            editResourceId,
        }: {
            allowedTypes: string[];
            editResourceId: number;
        }) => (
            <div>
                Edit form {allowedTypes[0]} #{editResourceId}
            </div>
        ),
    }),
);
jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/DataApplicationInfrastructureForm",
    () => ({
        DataApplicationInfrastructureForm: ({
            allowedTypes,
            editResourceId,
        }: {
            allowedTypes: string[];
            editResourceId: number;
        }) => (
            <div>
                Edit form {allowedTypes[0]} #{editResourceId}
            </div>
        ),
    }),
);
jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/WebDomainInfrastructureForm",
    () => ({
        WebDomainInfrastructureForm: ({
            allowedTypes,
            editResourceId,
        }: {
            allowedTypes: string[];
            editResourceId: number;
        }) => (
            <div>
                Edit form {allowedTypes[0]} #{editResourceId}
            </div>
        ),
    }),
);
jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/OperationalInfrastructureForm",
    () => ({
        OperationalInfrastructureForm: ({
            allowedTypes,
            editResourceId,
        }: {
            allowedTypes: string[];
            editResourceId: number;
        }) => (
            <div>
                Edit form {allowedTypes[0]} #{editResourceId}
            </div>
        ),
    }),
);
jest.mock(
    "@/app/(admin)/admin/infrastructure/resources/CatalogueResourceForm",
    () => ({
        CatalogueResourceForm: ({
            type,
            editResourceId,
        }: {
            type: string;
            editResourceId: number;
        }) => (
            <div>
                Edit form {type} #{editResourceId}
            </div>
        ),
    }),
);

const mockFetch = jest.mocked(fetchAPI);
const resource = {
    id: 42,
    name: "Example resource",
    resource_type: "other",
    lifecycle_status: "active",
    environment: "production",
    criticality: "normal",
    ownership_type: "internal",
    client_id: null,
    client_name: null,
    description: "",
    is_portal_visible: false,
    tags: [],
    relationships: [],
    specialist_fields: [],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
};
beforeEach(() => {
    mockFetch.mockReset();
    mockPermission.mockClear();
});

test.each(RESOURCE_TYPES)(
    "%s can be edited from its resource drawer",
    async (type) => {
        mockFetch.mockResolvedValue({ ...resource, resource_type: type });
        render(
            <InfrastructureResourceWorkspace
                resourceId={42}
                presentation="drawer"
            />,
        );
        fireEvent.click(
            await screen.findByRole("button", { name: "Edit resource" }),
        );
        expect(screen.getByText(`Edit form ${type} #42`)).toBeInTheDocument();
    },
);

test("editing an outgoing relationship preserves notes and targets outside the initial options", async () => {
    const relationship = {
        id: 5,
        direction: "outgoing",
        relationship_type: "depends_on",
        label: "Dependency",
        notes: "Keep notes",
        related_resource_id: 90,
        related_resource_name: "Existing target",
        related_resource_type: "other",
    };
    mockFetch.mockImplementation(async (url: string, request?: RequestInit) => {
        if (request?.method) return relationship;
        if (url.includes("relationship-options"))
            return {
                relationship_types: [
                    { value: "depends_on", label: "Depends on" },
                ],
                targets: [],
            };
        return { ...resource, relationships: [relationship] };
    });
    render(
        <InfrastructureResourceWorkspace
            resourceId={42}
            presentation="drawer"
        />,
    );
    fireEvent.click(await screen.findByRole("button", { name: "Edit" }));
    const notes = await screen.findByLabelText("Relationship notes");
    expect(notes).toHaveValue("Keep notes");
    await screen.findByRole("option", { name: "Existing target" });
    fireEvent.change(notes, { target: { value: "Updated notes" } });
    fireEvent.click(screen.getByRole("button", { name: "Save relationship" }));
    await waitFor(() =>
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining("/relationships/5"),
            expect.objectContaining({
                method: "PATCH",
                body: expect.stringContaining('"notes":"Updated notes"'),
            }),
        ),
    );
});
