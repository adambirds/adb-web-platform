import "@testing-library/jest-dom";
import { MonitoringHistoryChart } from "@/app/(admin)/admin/monitoring/checks/[id]/MonitoringHistoryChart";
import { fireEvent, render, screen } from "@testing-library/react";

const sample = (id: number, outcome: string, duration_ms: number) => ({
    id,
    outcome,
    duration_ms,
    started_at: `2026-10-05T01:0${id}:00Z`,
    message: outcome === "failure" ? "No reply" : "Reply received",
});

it("breaks the success line across failures and supports keyboard inspection", () => {
    render(
        <MonitoringHistoryChart
            results={[
                sample(3, "success", 15),
                sample(2, "failure", 10000),
                sample(1, "success", 10),
            ]}
            total={210}
        />,
    );
    expect(screen.getAllByTestId("successful-timing-segment")).toHaveLength(2);
    expect(
        screen.getByText(/Latest 3 of 210 observations/),
    ).toBeInTheDocument();
    const failed = screen.getByRole("button", { name: /failure, 10000 ms/ });
    expect(failed).toHaveAttribute("cy", "270");
    fireEvent.focus(failed);
    expect(
        screen.getByText(/failure · 10000 ms · No reply/),
    ).toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: /success, 15 ms/ }),
    ).not.toHaveAttribute("cy", "270");
});

it("renders a useful failure-only history without inventing successful timings", () => {
    render(
        <MonitoringHistoryChart
            results={[sample(1, "error", 0), sample(2, "failure", 5000)]}
            total={2}
        />,
    );
    expect(
        screen.queryByTestId("successful-timing-segment"),
    ).not.toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: /error, 0 ms/ }),
    ).toBeInTheDocument();
});

it("handles empty history", () => {
    render(<MonitoringHistoryChart results={[]} total={0} />);
    expect(screen.getByText("No timing history yet")).toBeInTheDocument();
    expect(screen.queryByRole("group")).not.toBeInTheDocument();
});
