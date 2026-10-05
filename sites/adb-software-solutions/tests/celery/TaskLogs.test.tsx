import "@testing-library/jest-dom";
import { TaskLogs } from "@/app/(admin)/admin/celery/TaskLogs";
import { celeryAPI } from "@/lib/api/celery";
import {
    act,
    fireEvent,
    render,
    screen,
    waitFor,
} from "@testing-library/react";

jest.mock("@/lib/api/celery", () => ({ celeryAPI: { logs: jest.fn() } }));
let refresh: (() => void | Promise<void>) | undefined;
jest.mock("@/contexts/LiveEventsContext", () => ({
    useLiveRefresh: (
        _topics: string[],
        callback: () => void | Promise<void>,
    ) => {
        refresh = callback;
    },
}));
const api = jest.mocked(celeryAPI);
beforeEach(() => {
    jest.clearAllMocks();
    api.logs.mockResolvedValue({
        items: [
            {
                id: 1,
                created_at: "2026-10-05T10:00:00Z",
                level: 40,
                logger_name: "test.worker",
                message: "Traceback\nValueError: request rejected",
                attempt: 1,
            },
        ],
        total: 230,
        page: 1,
        page_size: 100,
        truncated: false,
    });
});
test("shows per-task multiline diagnostics and severity, and updates through SSE", async () => {
    render(<TaskLogs taskId="task-one" />);
    expect(
        await screen.findByText(/ValueError: request rejected/),
    ).toBeInTheDocument();
    expect(screen.getByText(/attempt 2/)).toBeInTheDocument();
    expect(api.logs).toHaveBeenLastCalledWith("task-one", 1, "");
    await act(async () => {
        await refresh?.();
    });
    expect(api.logs).toHaveBeenCalledTimes(2);
    fireEvent.change(
        screen.getByRole("combobox", { name: "Minimum log severity" }),
        { target: { value: "ERROR" } },
    );
    await waitFor(() =>
        expect(api.logs).toHaveBeenLastCalledWith("task-one", 1, "ERROR"),
    );
});
test("browses older pages without live refresh moving the view", async () => {
    render(<TaskLogs taskId="task-one" />);
    await waitFor(() =>
        expect(screen.getByRole("button", { name: "Older" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Older" }));
    await waitFor(() =>
        expect(api.logs).toHaveBeenLastCalledWith("task-one", 2, ""),
    );
    expect(
        screen.getByRole("checkbox", { name: "Follow live" }),
    ).not.toBeChecked();
    const calls = api.logs.mock.calls.length;
    await act(async () => {
        await refresh?.();
    });
    expect(api.logs).toHaveBeenCalledTimes(calls);
    fireEvent.click(screen.getByRole("checkbox", { name: "Follow live" }));
    await waitFor(() =>
        expect(api.logs).toHaveBeenLastCalledWith("task-one", 1, ""),
    );
});
test("shows the capture limit and handles empty historical logs", async () => {
    api.logs.mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
        truncated: true,
    });
    render(<TaskLogs taskId="old-task" />);
    expect(
        await screen.findByText(/older executions cannot be backfilled/),
    ).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("capture limit");
});
test("keeps access failures visible and renders logs as text", async () => {
    api.logs.mockResolvedValueOnce({
        items: [
            {
                id: 1,
                created_at: "2026-10-05T10:00:00Z",
                level: 20,
                logger_name: "test",
                message: '<script>alert("test")</script>',
                attempt: 0,
            },
        ],
        total: 1,
        page: 1,
        page_size: 100,
        truncated: false,
    });
    render(<TaskLogs taskId="task-one" />);
    expect(
        await screen.findByText('<script>alert("test")</script>'),
    ).toBeInTheDocument();
    expect(document.querySelector("script")).toBeNull();
    api.logs.mockRejectedValueOnce(
        new Error("Full administrator access is required."),
    );
    fireEvent.click(screen.getByRole("button", { name: "Refresh logs" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
        "Full administrator access",
    );
});
