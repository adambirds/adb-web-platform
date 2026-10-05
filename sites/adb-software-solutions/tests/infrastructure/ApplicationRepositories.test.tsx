import "@testing-library/jest-dom";
import { ApplicationRepositoriesCard } from "@/app/(admin)/admin/infrastructure/resources/[id]/ApplicationRepositoriesCard";
import { fetchAPI } from "@/lib/api/fetch";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("@/lib/api/fetch", () => ({ fetchAPI: jest.fn() }));
const permission = jest.fn(() => true);
jest.mock("@/contexts/AuthContext", () => ({
    useAuth: () => ({ hasPermission: permission }),
}));
const api = jest.mocked(fetchAPI);

it("creates a repository in context and selects it without losing the link draft", async () => {
    let created = false;
    api.mockImplementation(async (url, init) => {
        if (init?.method === "POST") {
            if (url.endsWith("source-repositories")) {
                created = true;
                return { resource_id: 20 };
            }
            return { id: 1 };
        }
        if (url.endsWith("data-application-options"))
            return {
                clients: [{ id: 7, name: "Client" }],
                provider_accounts: [],
                servers: [],
                database_instances: [],
                applications: [],
                source_repositories: created
                    ? [
                          {
                              resource_id: 20,
                              name: "Platform code",
                              repository_name: "platform",
                              ownership_type: "client",
                              client_id: 7,
                          },
                      ]
                    : [],
            };
        return [];
    });
    render(
        <ApplicationRepositoriesCard
            resourceId={1}
            ownershipType="client"
            clientId={7}
        />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Add repository" }));
    expect(
        await screen.findByText(/No source repositories are available/),
    ).toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: "Link repository" }),
    ).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Monorepo path"), {
        target: { value: "sites/app" },
    });
    fireEvent.click(
        screen.getByRole("button", { name: "Create source repository" }),
    );
    const name = await screen.findByLabelText("Name");
    expect(screen.getByLabelText("Ownership")).toBeDisabled();
    expect(screen.getByLabelText("Client")).toHaveValue("7");
    fireEvent.change(name, { target: { value: "Platform code" } });
    fireEvent.change(screen.getByLabelText("Repository name"), {
        target: { value: "platform" },
    });
    fireEvent.click(
        screen.getByRole("button", { name: "Create source repository" }),
    );
    await waitFor(() =>
        expect(screen.getByLabelText("Source repository")).toHaveValue("20"),
    );
    expect(screen.getByLabelText("Monorepo path")).toHaveValue("sites/app");
    fireEvent.click(screen.getByRole("button", { name: "Link repository" }));
    await waitFor(() =>
        expect(
            api.mock.calls.some(
                ([url, init]) =>
                    url.endsWith("applications/1/repositories") &&
                    init?.method === "POST",
            ),
        ).toBe(true),
    );
    const call = api.mock.calls.find(([url]) =>
        url.endsWith("applications/1/repositories"),
    );
    expect(JSON.parse(String(call?.[1]?.body))).toMatchObject({
        repository_resource_id: 20,
        path: "sites/app",
    });
});
