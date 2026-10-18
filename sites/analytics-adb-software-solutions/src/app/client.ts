import {createApiUrl} from "@adb/api-client";

export const API_URL =
    process.env.NEXT_PUBLIC_API_URL ??
    (process.env.NODE_ENV === "production"
        ? "https://api.adbsoftwaresolutions.co.uk"
        : "http://localhost:8000");
export const AUTH_URL =
    process.env.NEXT_PUBLIC_AUTH_URL ??
    (process.env.NODE_ENV === "production"
        ? "https://auth.adbsoftwaresolutions.co.uk"
        : "http://localhost:3004");
export const ANALYTICS_URL =
    process.env.NEXT_PUBLIC_ANALYTICS_URL ??
    (process.env.NODE_ENV === "production"
        ? "https://analytics.adbsoftwaresolutions.co.uk"
        : "http://localhost:3005");
export class ApiError extends Error {
    constructor(
        public status: number,
        message: string,
    ) {
        super(message);
    }
}
export function apiUrl(path: string): string {
    return createApiUrl(`/api/analytics${path}`, {baseUrl: API_URL}).toString();
}
export async function api<T>(
    path: string,
    method = "GET",
    body?: unknown,
): Promise<T> {
    const headers: Record<string, string> = {};
    if (method !== "GET") {
        const csrf = await fetch(
            createApiUrl("/api/csrf", {baseUrl: API_URL}),
            {credentials: "include", cache: "no-store"},
        );
        if (!csrf.ok)
            throw new ApiError(
                csrf.status,
                "Could not establish a secure session.",
            );
        const token: {csrf_token: string} = await csrf.json();
        headers["X-CSRFToken"] = token.csrf_token;
        headers["Content-Type"] = "application/json";
    }
    const response = await fetch(apiUrl(path), {
        method,
        credentials: "include",
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
        cache: "no-store",
    });
    const result = await response.json();
    if (!response.ok)
        throw new ApiError(
            response.status,
            typeof result.detail === "string"
                ? result.detail
                : "The request could not be completed. Check the supplied values.",
        );
    return result as T;
}
export interface Provider {
    provider: "ga4" | "gsc";
    external_id: string;
    connection_id: number;
    last_synced_at: string | null;
    error_code: string;
    metadata: Record<string, unknown>;
}
export interface Website {
    id: number;
    business_id: number;
    name: string;
    domain: string;
    timezone: string;
    is_active: boolean;
    providers: Provider[];
}
export interface Business {
    id: number;
    name: string;
    slug: string;
    role: "owner" | "admin" | "viewer";
    websites: Website[];
}
export interface Session {
    email: string;
    businesses: Business[];
    website_id: number | null;
}
export type Row = Record<string, string | number | null>;
export interface Snapshot {
    rows: Row[];
    updated_at: string;
    complete: boolean;
    measurement: string;
    limitations?: string;
}
export interface Report {
    current: Snapshot | null;
    previous: Snapshot | null;
    total: number;
    status: string;
    error_code: string;
    last_synced_at: string | null;
}
export function initialDates(): {start: string; end: string} {
    const end = new Date();
    end.setUTCDate(end.getUTCDate() - 3);
    const start = new Date(end);
    start.setUTCDate(start.getUTCDate() - 27);
    return {
        start: start.toISOString().slice(0, 10),
        end: end.toISOString().slice(0, 10),
    };
}
export function loginUrl(returnTo: string): string {
    const url = new URL("/login", AUTH_URL);
    url.searchParams.set("next", returnTo);
    return url.toString();
}
