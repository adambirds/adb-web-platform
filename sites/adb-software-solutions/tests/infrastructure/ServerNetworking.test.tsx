import "@testing-library/jest-dom";
import { ServerNetworkingCard } from "@/app/(admin)/admin/infrastructure/resources/[id]/ServerNetworkingCard";
import { fetchAPI } from "@/lib/api/fetch";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("@/lib/api/fetch", () => ({ fetchAPI: jest.fn() }));
const permission = jest.fn(() => true);
jest.mock("@/contexts/AuthContext", () => ({
    useAuth: () => ({ hasPermission: permission }),
}));
const api = jest.mocked(fetchAPI);

beforeEach(() => {
    permission.mockImplementation(() => true);
    api.mockReset();
    api.mockImplementation(async (url, init) => {
        if (init?.method === "POST") return { resource_id: 20 };
        if (String(url).endsWith("specialist-options"))
            return {
                clients: [{ id: 7, name: "Client seven" }],
                provider_accounts: [],
                networks: [
                    {
                        resource_id: 20,
                        name: "Office",
                        ownership_type: "client",
                        client_id: 7,
                    },
                ],
                subnets: [],
            };
        return {
            ownership_type: "client",
            client_id: 7,
            interfaces: [],
            direct_ip_addresses: [],
        };
    });
});

it("creates a network in the server context and returns to the preserved interface draft", async () => {
    render(<ServerNetworkingCard resourceId={1} onChanged={jest.fn()} />);
    fireEvent.click(
        await screen.findByRole("button", { name: "Add interface" }),
    );
    fireEvent.change(screen.getByLabelText("Interface name"), {
        target: { value: "eth0" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add network" }));
    const name = await screen.findByLabelText("Name");
    fireEvent.change(name, { target: { value: "Office" } });
    expect(screen.getByLabelText("Ownership")).toBeDisabled();
    expect(screen.getByLabelText("Client")).toHaveValue("7");
    fireEvent.change(screen.getByLabelText("CIDR"), {
        target: { value: "10.0.0.0/16" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create network" }));
    await waitFor(() =>
        expect(screen.getByLabelText("Interface name")).toHaveValue("eth0"),
    );
    expect(screen.getByLabelText("Network")).toHaveValue("20");
    const call = api.mock.calls.find(([, init]) => init?.method === "POST");
    expect(JSON.parse(String(call?.[1]?.body))).toMatchObject({
        ownership_type: "client",
        client_id: 7,
    });
    fireEvent.click(screen.getByRole("button", { name: "Add subnet" }));
    expect(await screen.findByLabelText("Parent network")).toHaveValue("20");
    expect(screen.getByLabelText("Parent network")).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.getByLabelText("Interface name")).toHaveValue("eth0");
});

it("hides related creation actions without add capabilities", async () => {
    permission.mockImplementation(
        (...args: unknown[]) =>
            args[0] !== "infrastructure.add_network" &&
            args[0] !== "infrastructure.add_subnet",
    );
    render(<ServerNetworkingCard resourceId={1} onChanged={jest.fn()} />);
    fireEvent.click(
        await screen.findByRole("button", { name: "Add interface" }),
    );
    expect(
        screen.queryByRole("button", { name: "Add network" }),
    ).not.toBeInTheDocument();
    expect(
        screen.queryByRole("button", { name: "Add subnet" }),
    ).not.toBeInTheDocument();
});
