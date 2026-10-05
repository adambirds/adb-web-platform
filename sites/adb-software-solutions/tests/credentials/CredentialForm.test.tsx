import "@testing-library/jest-dom";
import { CredentialForm } from "@/app/(admin)/admin/credentials/CredentialForm";
import { fetchAPI } from "@/lib/api/fetch";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("@/lib/api/fetch", () => ({ fetchAPI: jest.fn() }));
const api = jest.mocked(fetchAPI);
const options = {
    types: [{ id: 1, name: "Custom", description: "", fields: [] }],
    clients: [],
    resources: [
        {
            id: 42,
            name: "Web server",
            resource_type: "server",
            ownership_type: "internal",
            client_id: null,
            client_name: null,
        },
    ],
};

it.each([
    "server",
    "website",
    "database",
    "application",
    "network",
    "provider_account",
])(
    "retains the originating %s link while loading options and includes it in creation",
    async (resourceType) => {
        let resolveOptions!: (value: typeof options) => void;
        api.mockReset();
        api.mockImplementation(async (_url, init) => {
            if (init?.method === "POST") return { id: 9 };
            return new Promise<typeof options>((resolve) => {
                resolveOptions = resolve;
            });
        });
        const saved = jest.fn();
        render(
            <CredentialForm
                initialResourceId={42}
                onSaved={saved}
                onCancel={jest.fn()}
            />,
        );
        await waitFor(() => expect(resolveOptions).toBeDefined());
        resolveOptions({
            ...options,
            resources: [
                { ...options.resources[0], resource_type: resourceType },
            ],
        });
        const linked = await screen.findByRole("checkbox", {
            name: /Web server/,
        });
        expect(linked).toBeChecked();
        fireEvent.change(screen.getAllByRole("textbox")[0], {
            target: { value: "Server login" },
        });
        fireEvent.click(
            screen.getByRole("button", { name: "Create credential" }),
        );
        await waitFor(() => expect(saved).toHaveBeenCalled());
        const call = api.mock.calls.find(([, init]) => init?.method === "POST");
        expect(JSON.parse(String(call?.[1]?.body)).resource_links).toEqual([
            { resource_id: 42 },
        ]);
    },
);

it("searches by name, type and client without dropping hidden selections", async () => {
    api.mockReset();
    api.mockImplementation(async (_url, init) =>
        init?.method === "POST"
            ? { id: 9 }
            : {
                  ...options,
                  resources: [
                      ...options.resources,
                      {
                          id: 43,
                          name: "Billing store",
                          resource_type: "database",
                          ownership_type: "client",
                          client_id: 7,
                          client_name: "Acme",
                      },
                  ],
              },
    );
    const saved = jest.fn();
    render(
        <CredentialForm
            initialResourceId={42}
            onSaved={saved}
            onCancel={jest.fn()}
        />,
    );
    expect(
        await screen.findByRole("checkbox", { name: /Web server/ }),
    ).toBeChecked();
    const search = screen.getByRole("textbox", {
        name: "Search infrastructure resources",
    });
    for (const query of ["Billing", "database", "Acme"]) {
        fireEvent.change(search, { target: { value: query } });
        expect(
            screen.getByRole("checkbox", { name: /Billing store/ }),
        ).toBeInTheDocument();
        expect(
            screen.queryByRole("checkbox", { name: /Web server/ }),
        ).not.toBeInTheDocument();
    }
    fireEvent.click(screen.getByRole("checkbox", { name: /Billing store/ }));
    fireEvent.change(search, { target: { value: "missing" } });
    expect(
        screen.getByText("No resources match your search."),
    ).toBeInTheDocument();
    fireEvent.change(search, { target: { value: "" } });
    expect(screen.getByRole("checkbox", { name: /Web server/ })).toBeChecked();
    expect(
        screen.getByRole("checkbox", { name: /Billing store/ }),
    ).toBeChecked();
    fireEvent.change(screen.getAllByRole("textbox")[0], {
        target: { value: "Shared login" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create credential" }));
    await waitFor(() => expect(saved).toHaveBeenCalled());
    const call = api.mock.calls.find(([, init]) => init?.method === "POST");
    expect(
        JSON.parse(String(call?.[1]?.body)).resource_links.map(
            (link: { resource_id: number }) => link.resource_id,
        ),
    ).toEqual([42, 43]);
});
