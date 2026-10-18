"use client";
import {useCallback, useEffect, useState} from "react";
import {api, ApiError, loginUrl} from "../../app/client";

export function useResource<T>(
    path: string | null,
    interval: number | null = null,
) {
    const [result, setResult] = useState<{path: string; data: T} | null>(null);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(true);
    const [revision, setRevision] = useState(0);
    const reload = useCallback(() => setRevision((value) => value + 1), []);
    useEffect(() => {
        if (!path) {
            setLoading(false);
            return;
        }
        let active = true;
        setLoading(true);
        setError("");
        void api<T>(path)
            .then((data) => {
                if (active) setResult({path, data});
            })
            .catch((err: unknown) => {
                if (!active) return;
                if (err instanceof ApiError && err.status === 401)
                    window.location.replace(loginUrl(window.location.href));
                setError(
                    err instanceof Error
                        ? err.message
                        : "This report could not be loaded.",
                );
            })
            .finally(() => {
                if (active) setLoading(false);
            });
        return () => {
            active = false;
        };
    }, [path, revision]);
    useEffect(() => {
        if (!interval || !path) return;
        const timer = window.setInterval(reload, interval);
        return () => window.clearInterval(timer);
    }, [path, interval, reload]);
    return {
        data: result?.path === path ? result.data : null,
        error,
        loading,
        reload,
    };
}
