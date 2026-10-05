import "@testing-library/jest-dom";
import { CeleryWorkspace } from "@/app/(admin)/admin/celery/CeleryWorkspace";
import {
    celeryAPI,
    type CeleryExecution,
    type CeleryOverview,
} from "@/lib/api/celery";
import {
    act,
    fireEvent,
    render,
    screen,
    waitFor,
} from "@testing-library/react";

jest.mock("@/lib/api/celery", () => ({
    celeryAPI: {
        overview: jest.fn(),
        logs: jest.fn(),
        history: jest.fn(),
        revoke: jest.fn(),
        run: jest.fn(),
    },
}));
let fullAdmin = true;
jest.mock("@/contexts/AuthContext", () => ({
    useAuth: () => ({
        user: { isStaff: true, isSuperuser: fullAdmin },
        isLoading: false,
    }),
}));
let liveRefresh: (() => Promise<void> | void) | undefined;
jest.mock("@/contexts/LiveEventsContext", () => ({
    useLiveRefresh: (
        _topics: string[],
        refresh: () => Promise<void> | void,
    ) => {
        liveRefresh = refresh;
    },
}));
const api = jest.mocked(celeryAPI);
const execution: CeleryExecution = {
    id: "execution-one",
    task_name: "monitoring.run_check",
    state: "QUEUED",
    queue: "general",
    worker: "",
    retries: 0,
    error_type: "",
    published_at: "2026-10-05T10:00:00Z",
    started_at: null,
    finished_at: null,
    runtime_seconds: null,
    created_at: "2026-10-05T10:00:00Z",
    updated_at: "2026-10-05T10:00:00Z",
    revoke_requested_at: null,
};
const overview: CeleryOverview = {
    snapshot: {
        checked_at: "2026-10-05T10:00:00Z",
        broker_available: true,
        warning: "",
        workers: [
            {
                name: "worker@general",
                concurrency: 2,
                processed: 10,
                queues: ["general"],
                tasks: [],
            },
        ],
        queues: [{ name: "general", depth: 1 }],
    },
    schedules: [
        {
            name: "monitoring-dispatch",
            task_name: "monitoring.enqueue_due_checks",
            queue: "general",
            schedule: "every 30 seconds",
            can_run: true,
        },
    ],
    counts: { SUCCESS: 7, FAILURE: 1 },
    average_runtime: 0.23,
    history_since: "2026-10-05T10:00:00Z",
    retention_days: 14,
    hours: [
        {
            hour: "2026-10-05T10:00:00Z",
            succeeded: 7,
            failed: 1,
            average_runtime: 0.23,
        },
    ],
};
beforeEach(() => {
    fullAdmin = true;
    jest.clearAllMocks();
    api.logs.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 100, truncated: false });
    api.overview.mockResolvedValue(overview);
    api.history.mockResolvedValue({
        items: [execution],
        total: 30,
        page: 1,
        page_size: 25,
    });
    api.revoke.mockResolvedValue({
        success: true,
        message: "Revoke requested.",
        task_id: execution.id,
    });
    api.run.mockResolvedValue({
        success: true,
        message: "Scheduled job queued.",
        task_id: "new-execution",
    });
});
test("denies ordinary staff without fetching platform data", () => {
    fullAdmin = false;
    render(<CeleryWorkspace />);
    expect(screen.getByRole("alert")).toHaveTextContent(
        "Full administrator access",
    );
    expect(api.overview).not.toHaveBeenCalled();
    expect(api.history).not.toHaveBeenCalled();
});
test("shows worker and queue state, requests history pages and preserves filters during live refresh", async () => {
    render(<CeleryWorkspace />);
    await screen.findByRole("button", { name: "monitoring.run_check" });
    expect(
        screen.getByText("worker@general", { exact: false }),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByRole("combobox", { name: "Task state" }), {
        target: { value: "FAILURE" },
    });
    await waitFor(() =>
        expect(api.history).toHaveBeenLastCalledWith(1, "FAILURE", ""),
    );
    await waitFor(() =>
        expect(screen.getByRole("button", { name: "Next" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() =>
        expect(api.history).toHaveBeenLastCalledWith(2, "FAILURE", ""),
    );
    await act(async () => {
        await liveRefresh?.();
    });
    await waitFor(() =>
        expect(api.history).toHaveBeenLastCalledWith(2, "FAILURE", ""),
    );
    expect(screen.getByRole("combobox", { name: "Task state" })).toHaveValue(
        "FAILURE",
    );
});
test("requires confirmation for scheduled dispatch and cooperative revocation", async () => {
    render(<CeleryWorkspace />);
    await screen.findByRole("button", { name: "Run now" });
    fireEvent.click(screen.getByRole("button", { name: "Run now" }));
    expect(api.run).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    await waitFor(() =>
        expect(api.run).toHaveBeenCalledWith("monitoring-dispatch"),
    );
    await waitFor(() =>
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Revoke" }));
    expect(api.revoke).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    await waitFor(() =>
        expect(api.revoke).toHaveBeenCalledWith("execution-one"),
    );
});
test("shows safe execution details and failure classes", async () => {
    api.history.mockResolvedValue({
        items: [{ ...execution, state: "FAILURE", error_type: "TimeoutError" }],
        total: 1,
        page: 1,
        page_size: 25,
    });
    render(<CeleryWorkspace />);
    fireEvent.click(
        await screen.findByRole("button", { name: "monitoring.run_check" }),
    );
    expect(
        screen.getByRole("dialog", { name: "Task execution details" }),
    ).toBeInTheDocument();
    expect(screen.getByText("TimeoutError")).toBeInTheDocument();
    expect(
        screen.queryByRole("button", { name: "Revoke" }),
    ).not.toBeInTheDocument();
});
test("shows an unavailable broker as unknown rather than an empty queue", async () => {
    api.overview.mockResolvedValue({
        ...overview,
        snapshot: {
            ...overview.snapshot,
            broker_available: false,
            warning: "Celery broker inspection is unavailable.",
            workers: [],
            queues: [{ name: "general", depth: null }],
        },
    });
    render(<CeleryWorkspace />);
    expect(await screen.findByText("Unavailable")).toBeInTheDocument();
    expect(screen.getAllByText("Unknown")).toHaveLength(2);
    expect(
        screen.getByText("Celery broker inspection is unavailable."),
    ).toBeInTheDocument();
});
