import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { RetentionWorkspace } from "../app/(admin)/admin/retention/RetentionWorkspace";
import { fetchAPI } from "@/lib/api/fetch";

jest.mock("@/contexts/LiveEventsContext", () => ({
    useLiveRefresh: jest.fn(),
}));
jest.mock("@/lib/api/fetch", () => ({ fetchAPI: jest.fn() }));
jest.mock("@/lib/config", () => ({ API_URL: "http://backend.test" }));
const request = jest.mocked(fetchAPI);
const review = {
    id: 1,
    lead_id: 10,
    name: "Old enquiry",
    email: "old@example.com",
    brand: "Web Designs",
    notes: "Previous discussion",
    status: "pending",
    due_at: "2026-10-01",
    last_activity_at: "2023-10-01",
    review_after: null,
    decision_reason: "",
    conversation_count: 1,
    can_approve: true,
    can_keep: true,
    files_pending: 0,
};
const response = {
    items: [review],
    page: 1,
    total: 1,
    total_pages: 1,
    can_scan: true,
    retention_months: 36,
};
beforeEach(() => {
    request.mockReset();
    request.mockResolvedValue(response);
});

test("deletion needs explicit second confirmation and refreshes the queue", async () => {
    render(<RetentionWorkspace />);
    fireEvent.click(
        await screen.findByRole("button", { name: "Review deletion" }),
    );
    expect(request).toHaveBeenCalledTimes(1);
    expect(
        screen.getByText(/This action cannot be undone/),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Approve and delete" }));
    await waitFor(() =>
        expect(request).toHaveBeenCalledWith(
            expect.stringContaining("/1/decision"),
            expect.objectContaining({
                method: "POST",
                body: JSON.stringify({
                    action: "approve",
                    reason: "",
                    months: 6,
                }),
            }),
        ),
    );
    await waitFor(() => expect(request).toHaveBeenCalledTimes(3));
});

test("keeping needs a reason and sends the chosen next review period", async () => {
    render(<RetentionWorkspace />);
    fireEvent.click(
        await screen.findByRole("button", { name: "Reject deletion / keep" }),
    );
    const save = screen.getByRole("button", {
        name: "Keep and set review date",
    });
    expect(save).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Reason for keeping this record"), {
        target: { value: "Discussing a return project" },
    });
    fireEvent.change(screen.getByLabelText(/Review again in/), {
        target: { value: "12" },
    });
    fireEvent.click(save);
    await waitFor(() =>
        expect(request).toHaveBeenCalledWith(
            expect.stringContaining("/1/decision"),
            expect.objectContaining({
                method: "POST",
                body: JSON.stringify({
                    action: "keep",
                    reason: "Discussing a return project",
                    months: 12,
                }),
            }),
        ),
    );
});

test("stale approval errors remain visible and do not imply deletion", async () => {
    render(<RetentionWorkspace />);
    fireEvent.click(
        await screen.findByRole("button", { name: "Review deletion" }),
    );
    request.mockRejectedValueOnce(
        new Error("This record has recent activity."),
    );
    fireEvent.click(screen.getByRole("button", { name: "Approve and delete" }));
    expect(
        await screen.findByText("This record has recent activity."),
    ).toBeInTheDocument();
    expect(screen.getByText("Previous notes")).toBeInTheDocument();
});
