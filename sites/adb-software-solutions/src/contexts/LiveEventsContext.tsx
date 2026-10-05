"use client";

import { useAuth } from "@/contexts/AuthContext";
import { API_URL } from "@/lib/config";
import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useRef,
    useState,
    type ReactNode,
} from "react";

type Listener = (topics: string[] | null) => void;
interface LiveEvents {
    connected: boolean;
    subscribe: (listener: Listener) => () => void;
}
const LiveEventsContext = createContext<LiveEvents | null>(null);

export function LiveEventsProvider({ children }: { children: ReactNode }) {
    const { refreshUser } = useAuth();
    const [connected, setConnected] = useState(false);
    const listeners = useRef(new Set<Listener>());
    const subscribe = useCallback((listener: Listener) => {
        listeners.current.add(listener);
        return () => {
            listeners.current.delete(listener);
        };
    }, []);
    useEffect(() => {
        if (typeof EventSource === "undefined") return;
        const source = new EventSource(`${API_URL}/api/admin/events`, {
            withCredentials: true,
        });
        const emit = (topics: string[] | null) =>
            listeners.current.forEach((listener) => listener(topics));
        source.addEventListener("ready", () => {
            setConnected(true);
            emit(null);
        });
        source.addEventListener("change", (event) => {
            try {
                const payload: unknown = JSON.parse(
                    (event as MessageEvent<string>).data,
                );
                if (
                    !payload ||
                    typeof payload !== "object" ||
                    !("topics" in payload) ||
                    !Array.isArray(payload.topics) ||
                    !payload.topics.every(
                        (topic: unknown) => typeof topic === "string",
                    )
                )
                    return;
                const topics = payload.topics as string[];
                if (topics.includes("access")) {
                    void refreshUser(true);
                    emit(null);
                } else emit(topics);
            } catch {
                /* A malformed event does not disable subsequent updates. */
            }
        });
        source.onerror = () => setConnected(false);
        source.addEventListener("unavailable", () => setConnected(false));
        source.addEventListener("expired", () => {
            source.close();
            setConnected(false);
            void refreshUser(true);
        });
        const visible = () => {
            if (!document.hidden) emit(null);
        };
        document.addEventListener("visibilitychange", visible);
        return () => {
            source.close();
            document.removeEventListener("visibilitychange", visible);
        };
    }, [refreshUser]);
    return (
        <LiveEventsContext.Provider value={{ connected, subscribe }}>
            {children}
        </LiveEventsContext.Provider>
    );
}

/** Refresh read state only; callers retain forms, filters and pagination. */
export function useLiveRefresh(
    topics: readonly string[],
    refresh: () => void | Promise<void>,
) {
    const live = useContext(LiveEventsContext);
    const latest = useRef(refresh);
    useEffect(() => {
        latest.current = refresh;
    }, [refresh]);
    const key = [...topics].sort().join(",");
    const connected = live?.connected;
    const subscribe = live?.subscribe;
    useEffect(() => {
        if (!subscribe) return;
        let timer: ReturnType<typeof setTimeout> | undefined;
        let running = false;
        let pending = false;
        let active = true;
        async function invoke() {
            timer = undefined;
            if (!active || document.hidden) return;
            if (running) {
                pending = true;
                return;
            }
            running = true;
            try {
                await latest.current();
            } catch {
                /* Screens own their API error state. */
            } finally {
                running = false;
                if (pending && active) {
                    pending = false;
                    timer = setTimeout(() => void invoke(), 250);
                }
            }
        }
        function schedule(changed: string[] | null) {
            if (
                changed &&
                !changed.some((topic) => key.split(",").includes(topic))
            )
                return;
            if (timer === undefined)
                timer = setTimeout(() => void invoke(), 250);
        }
        const unsubscribe = subscribe(schedule);
        if (connected) schedule(null);
        // Slow reconciliation covers missed/bulk writes and time-driven notifications.
        // When disconnected, ordinary polling keeps the screens usable.
        const interval = setInterval(
            () => schedule(null),
            connected ? 120000 : 30000,
        );
        return () => {
            active = false;
            unsubscribe();
            clearInterval(interval);
            if (timer !== undefined) clearTimeout(timer);
        };
    }, [key, connected, subscribe]);
}
