import "@testing-library/jest-dom";
import { GitHubWorkspace } from "@/app/(admin)/admin/github/GitHubWorkspace";
import { fetchAPI } from "@/lib/api/fetch";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
jest.mock("@/lib/api/fetch", () => ({ fetchAPI: jest.fn() }));
const permissions = jest.fn(() => true);
jest.mock("@/contexts/AuthContext", () => ({
    useAuth: () => ({ hasPermission: permissions }),
}));
const api = jest.mocked(fetchAPI);
const workflow = {
    kind: "workflow",
    id: 1,
    github_id: 99,
    repository_id: 5,
    repository: "adb/platform",
    title: "Deploy",
    state: "active",
    branch: "main",
    url: "https://github.com/adb/platform",
};
beforeEach(() => {
    permissions.mockImplementation(() => true);
    api.mockReset();
    api.mockImplementation(async (url) => {
        if (url.endsWith("options"))
            return {
                username: "adambirds",
                configured: true,
                accounts: [],
                install_url: "",
            };
        if (url.includes("items"))
            return {
                rows: url.includes("kind=workflow") ? [workflow] : [],
                total: 0,
                page: 1,
                pages: 1,
            };
        return {};
    });
});
test("defaults to my pull requests and supports a separate Dependabot view", async () => {
    render(<GitHubWorkspace />);
    await waitFor(() =>
        expect(api).toHaveBeenCalledWith(
            expect.stringContaining("kind=pull_request&view=my"),
        ),
    );
    fireEvent.change(screen.getByRole("combobox", { name: "Show" }), {
        target: { value: "dependabot" },
    });
    await waitFor(() =>
        expect(api).toHaveBeenCalledWith(
            expect.stringContaining("view=dependabot"),
        ),
    );
    expect(screen.getByRole("tab", { name: "Pull requests" })).toHaveAttribute(
        "aria-selected",
        "true",
    );
});
test("dispatches a workflow with a chosen branch and inputs after confirmation", async () => {
    const confirm = jest.spyOn(window, "confirm").mockReturnValue(true);
    render(<GitHubWorkspace />);
    fireEvent.click(screen.getByRole("tab", { name: "Workflows" }));
    fireEvent.click(
        await screen.findByRole("button", { name: "Start workflow" }),
    );
    fireEvent.change(screen.getByLabelText("Branch or tag"), {
        target: { value: "release" },
    });
    fireEvent.change(screen.getByLabelText("Workflow inputs (JSON)"), {
        target: { value: '{"environment":"staging"}' },
    });
    fireEvent.click(screen.getByRole("button", { name: "Confirm start" }));
    await waitFor(() =>
        expect(api).toHaveBeenCalledWith(
            expect.stringContaining("repositories/5/workflows/99/dispatch"),
            {
                method: "POST",
                body: JSON.stringify({
                    ref: "release",
                    inputs: { environment: "staging" },
                }),
            },
        ),
    );
    expect(await screen.findByRole("status")).toHaveTextContent(
        "GitHub accepted",
    );
    confirm.mockRestore();
});
test("view permission alone does not show workflow trigger controls", async () => {
    permissions.mockImplementation(
        (permission?: string) =>
            permission !== "github_integration.trigger_workflow",
    );
    render(<GitHubWorkspace />);
    fireEvent.click(screen.getByRole("tab", { name: "Workflows" }));
    await screen.findByText("Deploy");
    expect(
        screen.queryByRole("button", { name: "Start workflow" }),
    ).not.toBeInTheDocument();
});
test("supports paged repository lists", async () => {
    api.mockImplementation(async (url) => {
        if (url.endsWith("options"))
            return {
                username: "adam",
                configured: true,
                accounts: [],
                install_url: "",
            };
        return { rows: [], total: 30, page: 1, pages: 2 };
    });
    render(<GitHubWorkspace />);
    fireEvent.click(screen.getByRole("tab", { name: "Repositories" }));
    fireEvent.click(await screen.findByRole("button", { name: "Next" }));
    await waitFor(() =>
        expect(api).toHaveBeenCalledWith(
            expect.stringContaining("repositories?page=2"),
        ),
    );
});
