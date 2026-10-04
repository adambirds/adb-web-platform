import "@testing-library/jest-dom";
import { ActivityWorkspace } from "@/app/(admin)/admin/activity/ActivityWorkspace";
import { fetchAPI } from "@/lib/api/fetch";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("@/lib/api/fetch", () => ({ fetchAPI: jest.fn() }));

const mockFetch = jest.mocked(fetchAPI);
const activity = {
    items: [],
    page: 1,
    page_size: 50,
    total: 0,
    total_pages: 0,
    metadata_visible: false,
};

function mockResponses(clientResponse: object | Error) {
    mockFetch.mockImplementation(async (url: string) => {
        if (url.includes("/api/admin/clients")) {
            if (clientResponse instanceof Error) throw clientResponse;
            return clientResponse;
        }
        if (url.includes("/infrastructure/resources")) {
            return {
                items: [
                    {
                        id: 10,
                        name: "Client server",
                        client_id: 1,
                        client_name: "Example Ltd",
                        resource_type: "server",
                    },
                    {
                        id: 20,
                        name: "Other server",
                        client_id: 2,
                        client_name: "Other Ltd",
                        resource_type: "server",
                    },
                ],
            };
        }
        return activity;
    });
}

beforeEach(() => {
    mockFetch.mockReset();
});

test("loads the Client array and applies Client context to resources and Activity", async () => {
    mockResponses([{ id: 1, name: "Example", company: "Example Ltd" }]);
    render(<ActivityWorkspace />);

    expect(
        await screen.findByRole("option", { name: "Example Ltd" }),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByRole("combobox", { name: "Client context" }), {
        target: { value: "1" },
    });

    expect(
        screen.getByRole("option", { name: "Client server · server" }),
    ).toBeInTheDocument();
    expect(
        screen.queryByRole("option", { name: "Other server · server" }),
    ).not.toBeInTheDocument();
    await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining("client_id=1"),
        );
    });
});

test("keeps Activity usable when Client access is denied", async () => {
    mockResponses(new Error("Permission denied"));
    render(<ActivityWorkspace />);

    expect(
        await screen.findByRole("option", { name: "Client server · server" }),
    ).toBeInTheDocument();
    expect(
        screen.getByRole("option", { name: "Platform-wide" }),
    ).toBeInTheDocument();
    expect(screen.getByText("No activity in scope")).toBeInTheDocument();
});
