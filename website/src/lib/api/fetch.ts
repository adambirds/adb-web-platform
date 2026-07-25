import { useCallback } from "react";

export async function fetchAPI(url: string, options: RequestInit = {}) {
    const defaultOptions: RequestInit = {
        headers: {
            "Content-Type": "application/json",
        },
    };

    const mergedOptions: RequestInit = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };

    const response = await fetch(url, mergedOptions);

    if (!response.ok) {
        const error = await response
            .json()
            .catch(() => ({ detail: "Unknown error" }));
        throw new Error(error.detail || "API request failed");
    }

    return response.json();
}

export function useAPI<T>(url: string) {
    const fetch = useCallback(async () => {
        try {
            return await fetchAPI(url);
        } catch (error) {
            console.error("API Error:", error);
            throw error;
        }
    }, [url]);

    return { fetch };
}
