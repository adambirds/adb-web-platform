"use client";

import { API_URL } from "@/lib/config";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";

import { fetchAPI } from "@/lib/api/fetch";
import { Popover, PopoverButton, PopoverPanel } from "@headlessui/react";
import {
    BellIcon,
    CheckIcon,
    ExclamationTriangleIcon,
    XMarkIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const API_BASE_URL = `${API_URL}/api`;

interface NotificationItem {
    id: number;
    category: string;
    severity: "info" | "warning" | "critical";
    title: string;
    body: string;
    href: string;
    read_at: string | null;
    created_at: string;
}

interface NotificationResponse {
    items: NotificationItem[];
    unread_count: number;
}

function severityClasses(severity: NotificationItem["severity"]) {
    if (severity === "critical") {
        return "border-red-900/70 bg-red-950/30 text-red-300";
    }
    if (severity === "warning") {
        return "border-amber-900/70 bg-amber-950/20 text-amber-300";
    }
    return "border-slate-800 bg-slate-900/70 text-slate-300";
}

export function NotificationBell() {
    const [data, setData] = useState<NotificationResponse>({
        items: [],
        unread_count: 0,
    });
    const [loading, setLoading] = useState(true);

    const refresh = useCallback(async () => {
        try {
            const response = (await fetchAPI(
                `${API_BASE_URL}/admin/notifications?limit=30`,
            )) as NotificationResponse;
            setData(response);
        } catch (error) {
            console.error("Unable to refresh operational notifications", error);
        } finally {
            setLoading(false);
        }
    }, []);

    useLiveRefresh(["notifications"], refresh);

    useEffect(() => {
        void refresh();

    }, [refresh]);

    async function markRead(id: number) {
        await fetchAPI(`${API_BASE_URL}/admin/notifications/${id}/read`, {
            method: "POST",
        });
        setData((current) => ({
            ...current,
            unread_count: Math.max(
                0,
                current.unread_count -
                    (current.items.some(
                        (item) => item.id === id && item.read_at === null,
                    )
                        ? 1
                        : 0),
            ),
            items: current.items.map((item) =>
                item.id === id
                    ? { ...item, read_at: item.read_at ?? new Date().toISOString() }
                    : item,
            ),
        }));
    }

    async function dismiss(id: number) {
        await fetchAPI(`${API_BASE_URL}/admin/notifications/${id}/dismiss`, {
            method: "POST",
        });
        setData((current) => {
            const item = current.items.find((candidate) => candidate.id === id);
            return {
                unread_count: Math.max(
                    0,
                    current.unread_count - (item?.read_at === null ? 1 : 0),
                ),
                items: current.items.filter((candidate) => candidate.id !== id),
            };
        });
    }

    async function markAllRead() {
        await fetchAPI(`${API_BASE_URL}/admin/notifications/read-all`, {
            method: "POST",
        });
        setData((current) => ({
            unread_count: 0,
            items: current.items.map((item) => ({
                ...item,
                read_at: item.read_at ?? new Date().toISOString(),
            })),
        }));
    }

    return (
        <Popover className="relative">
            <PopoverButton
                className="relative flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-800 hover:text-white focus:outline-none"
                aria-label="Notifications"
                title="Notifications"
            >
                <BellIcon className="h-5 w-5" />
                {data.unread_count > 0 ? (
                    <span className="absolute -right-1 -top-1 min-w-4 rounded-full bg-red-500 px-1 text-center text-[10px] font-bold leading-4 text-white">
                        {data.unread_count > 99 ? "99+" : data.unread_count}
                    </span>
                ) : null}
            </PopoverButton>

            <PopoverPanel
                anchor="bottom end"
                className="z-[90] mt-2 w-[min(92vw,26rem)] overflow-hidden rounded-xl border border-slate-700 bg-slate-950 shadow-2xl shadow-black/50"
            >
                <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
                    <div>
                        <p className="text-sm font-semibold text-slate-100">
                            Notifications
                        </p>
                        <p className="text-xs text-slate-500">
                            {data.unread_count} unread operational alert
                            {data.unread_count === 1 ? "" : "s"}
                        </p>
                    </div>
                    {data.unread_count > 0 ? (
                        <button
                            type="button"
                            onClick={() => void markAllRead()}
                            className="text-xs font-medium text-adb-cyan-400 hover:text-adb-cyan-300"
                        >
                            Mark all read
                        </button>
                    ) : null}
                </div>

                <div className="max-h-[32rem] overflow-y-auto p-2">
                    {loading ? (
                        <div className="px-3 py-10 text-center text-sm text-slate-500">
                            Refreshing alerts…
                        </div>
                    ) : null}
                    {!loading && data.items.length === 0 ? (
                        <div className="px-3 py-10 text-center text-sm text-slate-500">
                            No active operational alerts.
                        </div>
                    ) : null}
                    {data.items.map((item) => (
                        <div
                            key={item.id}
                            className={`group mb-1 rounded-lg border p-3 last:mb-0 ${severityClasses(item.severity)} ${item.read_at ? "opacity-70" : ""}`}
                        >
                            <div className="flex gap-3">
                                <ExclamationTriangleIcon className="mt-0.5 h-4 w-4 shrink-0" />
                                <div className="min-w-0 flex-1">
                                    {item.href ? (
                                        <Link
                                            href={item.href}
                                            onClick={() => void markRead(item.id)}
                                            className="block text-sm font-medium hover:underline"
                                        >
                                            {item.title}
                                        </Link>
                                    ) : (
                                        <p className="text-sm font-medium">
                                            {item.title}
                                        </p>
                                    )}
                                    {item.body ? (
                                        <p className="mt-1 text-xs leading-5 opacity-80">
                                            {item.body}
                                        </p>
                                    ) : null}
                                    <p className="mt-1 text-[10px] uppercase tracking-wide opacity-50">
                                        {item.category}
                                    </p>
                                </div>
                                <div className="flex shrink-0 items-start gap-1">
                                    {!item.read_at ? (
                                        <button
                                            type="button"
                                            onClick={() => void markRead(item.id)}
                                            className="rounded p-1 opacity-60 hover:bg-white/10 hover:opacity-100"
                                            aria-label={`Mark ${item.title} read`}
                                            title="Mark read"
                                        >
                                            <CheckIcon className="h-4 w-4" />
                                        </button>
                                    ) : null}
                                    <button
                                        type="button"
                                        onClick={() => void dismiss(item.id)}
                                        className="rounded p-1 opacity-60 hover:bg-white/10 hover:opacity-100"
                                        aria-label={`Dismiss ${item.title}`}
                                        title="Dismiss"
                                    >
                                        <XMarkIcon className="h-4 w-4" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </PopoverPanel>
        </Popover>
    );
}
