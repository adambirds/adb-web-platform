import { API_URL } from "@/lib/config";
import { useCallback } from "react";

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

function getCookie(name: string): string | null {
    if (typeof document === "undefined") {
        return null;
    }

    const prefix = `${name}=`;
    for (const cookie of document.cookie.split(";")) {
        const value = cookie.trim();
        if (value.startsWith(prefix)) {
            return decodeURIComponent(value.slice(prefix.length));
        }
    }
    return null;
}

async function ensureCsrfToken(): Promise<string | null> {
    const existing = getCookie("csrftoken");
    if (existing) {
        return existing;
    }

    const response = await fetch(`${API_URL}/api/auth/csrf`, {
        credentials: "include",
    });
    if (!response.ok) {
        throw new Error("Unable to initialise CSRF protection");
    }

    const payload = (await response.json()) as { token?: string };
    return getCookie("csrftoken") ?? payload.token ?? null;
}

export async function fetchAPI(url: string, options: RequestInit = {}) {
    const method = (options.method ?? "GET").toUpperCase();
    const headers = new Headers(options.headers);

    if (!headers.has("Content-Type") && options.body) {
        headers.set("Content-Type", "application/json");
    }

    if (!SAFE_METHODS.has(method)) {
        const csrfToken = await ensureCsrfToken();
        if (!csrfToken) {
            throw new Error("Unable to obtain a CSRF token");
        }
        headers.set("X-CSRFToken", csrfToken);
    }

    const response = await fetch(url, {
        ...options,
        method,
        headers,
        credentials: "include",
    });

    if (!response.ok) {
        const error = (await response.json().catch(() => ({
            message: "Unknown error",
        }))) as { detail?: string; message?: string };
        throw new Error(error.detail || error.message || "API request failed");
    }

    return response.json();
}

export function useAPI(url: string) {
    const fetchData = useCallback(async () => {
        try {
            return await fetchAPI(url);
        } catch (error) {
            console.error("API Error:", error);
            throw error;
        }
    }, [url]);

    return { fetch: fetchData };
}
