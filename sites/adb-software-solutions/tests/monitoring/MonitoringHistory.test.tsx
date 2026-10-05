import "@testing-library/jest-dom";
import { MonitoringCheckWorkspace } from "@/app/(admin)/admin/monitoring/checks/[id]/MonitoringCheckWorkspace";
import { fetchAPI } from "@/lib/api/fetch";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("@/lib/api/fetch", () => ({ fetchAPI: jest.fn() }));
jest.mock("@/contexts/AuthContext", () => ({
    useAuth: () => ({ hasPermission: () => false }),
}));
const api = jest.mocked(fetchAPI);
const result = {
    id: 1,
    outcome: "success",
    started_at: "2026-10-05T01:00:00Z",
    finished_at: "2026-10-05T01:00:00Z",
    duration_ms: 2,
    status_code: null,
    observed_value: "",
    message: "Newest observation",
};
const detail = {
    id: 1,
    name: "Health check",
    resource_id: 7,
    resource_name: "Server",
    client_id: null,
    client_name: null,
    status: "healthy",
    check_type: "icmp",
    enabled: true,
    target: "127.0.0.1",
    port: null,
    severity: "error",
    last_checked_at: null,
    next_run_at: null,
    last_duration_ms: null,
    uptime_24h_percent: null,
    uptime_7d_percent: null,
    average_response_24h_ms: null,
    average_response_7d_ms: null,
    interval_seconds: 60,
    timeout_seconds: 5,
    failure_threshold: 1,
    recovery_threshold: 1,
    expiry_warning_days: 30,
    expected_value: "",
    forbidden_value: "",
    last_message: "",
    incidents: [],
    results: [result],
    results_page: 1,
    results_page_size: 10,
    results_total: 11,
};

it("loads the requested history page and navigates back to the newest observations", async () => {
    api.mockImplementation(async (url) =>
        url.includes("results_page=2")
            ? {
                  ...detail,
                  results_page: 2,
                  results: [
                      { ...result, id: 11, message: "Older observation" },
                  ],
              }
            : detail,
    );
    render(<MonitoringCheckWorkspace checkId={1} />);
    expect(await screen.findByText("Newest observation")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(await screen.findByText("Older observation")).toBeInTheDocument();
    expect(screen.getByText("Page 2 of 2")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
    expect(screen.queryByText("Newest observation")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Previous" }));
    await waitFor(() =>
        expect(screen.getByText("Newest observation")).toBeInTheDocument(),
    );
    expect(
        api.mock.calls.some(([url]) =>
            url.includes("results_page=2&results_page_size=10"),
        ),
    ).toBe(true);
});

it("shows empty history with disabled navigation", async () => {
    api.mockResolvedValue({ ...detail, results: [], results_total: 0 });
    render(<MonitoringCheckWorkspace checkId={1} />);
    expect(await screen.findByText("No observations yet")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
});
