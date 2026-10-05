import { API_URL } from "@/lib/config";
import { fetchAPI } from "./fetch";

export interface CeleryExecution {
    id: string;
    task_name: string;
    state: string;
    queue: string;
    worker: string;
    retries: number;
    error_type: string;
    published_at: string | null;
    started_at: string | null;
    finished_at: string | null;
    runtime_seconds: number | null;
    created_at: string;
    updated_at: string;
    revoke_requested_at: string | null;
}
export interface CeleryHistory {
    items: CeleryExecution[];
    total: number;
    page: number;
    page_size: number;
}
export interface CeleryHour {
    hour: string;
    succeeded: number;
    failed: number;
    average_runtime: number | null;
}
export interface CeleryOverview {
    snapshot: {
        checked_at: string;
        broker_available: boolean;
        warning: string;
        workers: {
            name: string;
            concurrency: number | null;
            processed: number;
            queues: string[];
            tasks: {
                id: string;
                task_name: string;
                state: string;
                eta: string;
            }[];
        }[];
        queues: { name: string; depth: number | null }[];
    };
    schedules: {
        name: string;
        task_name: string;
        schedule: string;
        queue: string;
        can_run: boolean;
    }[];
    counts: Record<string, number>;
    average_runtime: number | null;
    history_since: string | null;
    retention_days: number;
    hours: CeleryHour[];
}
interface CeleryActionResult {
    success: boolean;
    message: string;
    task_id: string;
}
export interface CeleryLogPage {
    items: {
        id: number;
        created_at: string;
        level: number;
        logger_name: string;
        message: string;
        attempt: number;
    }[];
    total: number;
    page: number;
    page_size: number;
    truncated: boolean;
}
const base = `${API_URL}/api/admin/celery`;
export const celeryAPI = {
    logs: async (
        id: string,
        page: number,
        level: string,
    ): Promise<CeleryLogPage> => {
        const params = new URLSearchParams({
            page: String(page),
            page_size: "100",
            level,
        });
        return fetchAPI(
            `${base}/tasks/${encodeURIComponent(id)}/logs?${params}`,
        );
    },
    overview: async (): Promise<CeleryOverview> => fetchAPI(`${base}/overview`),
    history: async (
        page: number,
        state: string,
        search: string,
    ): Promise<CeleryHistory> => {
        const params = new URLSearchParams({
            page: String(page),
            page_size: "25",
            state,
            search,
        });
        return fetchAPI(`${base}/tasks?${params}`);
    },
    revoke: async (id: string): Promise<CeleryActionResult> =>
        fetchAPI(`${base}/tasks/${encodeURIComponent(id)}/revoke`, {
            method: "POST",
        }),
    run: async (name: string): Promise<CeleryActionResult> =>
        fetchAPI(`${base}/schedules/${encodeURIComponent(name)}/run`, {
            method: "POST",
        }),
};
