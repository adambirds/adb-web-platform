"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";

import { Badge, Button, Card, DataError, DataLoading, EmptyState } from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

type CalendarKind = "task" | "project" | "event";
type CalendarFilter = "all" | CalendarKind;

interface CalendarItem {
    kind: CalendarKind;
    id: number;
    title: string;
    start_date: string;
    end_date: string;
    status: string;
    completed: boolean;
    client_id: number | null;
    client_name: string | null;
    project_id: number | null;
    project_name: string | null;
    starts_at: string | null;
    ends_at: string | null;
    all_day: boolean;
    event_type: string | null;
    location: string;
    meeting_url: string;
}

interface CalendarResponse {
    date_from: string;
    date_to: string;
    items: CalendarItem[];
    task_count: number;
    project_count: number;
    event_count: number;
}

const weekdayLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function localDate(year: number, month: number, day: number) {
    return new Date(year, month, day, 12, 0, 0, 0);
}

function isoDate(value: Date) {
    const year = value.getFullYear();
    const month = String(value.getMonth() + 1).padStart(2, "0");
    const day = String(value.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

function addDays(value: Date, days: number) {
    const next = new Date(value);
    next.setDate(next.getDate() + days);
    return next;
}

function monthGrid(anchor: Date) {
    const first = localDate(anchor.getFullYear(), anchor.getMonth(), 1);
    const mondayOffset = (first.getDay() + 6) % 7;
    const start = addDays(first, -mondayOffset);
    return Array.from({ length: 42 }, (_, index) => addDays(start, index));
}

function itemHref(item: CalendarItem) {
    if (item.kind === "task") return `/admin/tasks/${item.id}`;
    if (item.kind === "project") return `/admin/projects/${item.id}`;
    return null;
}

function itemContext(item: CalendarItem) {
    if (item.kind === "task" && item.project_name) return item.project_name;
    if (item.kind === "event" && item.location) return item.location;
    return item.client_name || "ADB Internal";
}

function itemClasses(item: CalendarItem) {
    if (item.kind === "project") return "border-indigo-900/70 bg-indigo-950/35 text-indigo-200";
    if (item.kind === "event") return "border-adb-cyan-900/70 bg-adb-cyan-950/30 text-adb-cyan-200";
    if (item.completed) return "border-emerald-900/50 bg-emerald-950/20 text-emerald-400 line-through";
    return "border-slate-700 bg-slate-900 text-slate-300";
}

function itemPrefix(item: CalendarItem) {
    if (item.kind === "project") return "P";
    if (item.kind === "event") return "E";
    return "T";
}

export function CalendarWorkspace() {
    const { hasPermission } = useAuth();
    const [anchor, setAnchor] = useState(() => new Date());
    const [filter, setFilter] = useState<CalendarFilter>("all");
    const [data, setData] = useState<CalendarResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreate, setShowCreate] = useState(false);
    const [creating, setCreating] = useState(false);
    const [eventTitle, setEventTitle] = useState("");
    const [eventType, setEventType] = useState("meeting");
    const [eventStart, setEventStart] = useState("");
    const [eventEnd, setEventEnd] = useState("");
    const [eventLocation, setEventLocation] = useState("");
    const [eventMeetingUrl, setEventMeetingUrl] = useState("");

    const days = useMemo(() => monthGrid(anchor), [anchor]);
    const dateFrom = isoDate(days[0]);
    const dateTo = isoDate(days[days.length - 1]);
    const currentMonth = anchor.getMonth();
    const today = isoDate(new Date());

    const load = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const query = new URLSearchParams({ date_from: dateFrom, date_to: dateTo });
            setData(
                (await fetchAPI(`${API_URL}/api/admin/calendar?${query.toString()}`)) as CalendarResponse,
            );
        } catch (loadError) {
            setError(loadError instanceof Error ? loadError.message : "Unable to load the calendar.");
        } finally {
            setLoading(false);
        }
    }, [dateFrom, dateTo]);

    useLiveRefresh(["calendar"], load);

    useEffect(() => {
        void load();
    }, [load]);

    const visibleItems = useMemo(
        () => data?.items.filter((item) => filter === "all" || item.kind === filter) ?? [],
        [data, filter],
    );
    const upcomingEvents = useMemo(
        () =>
            (data?.items ?? [])
                .filter((item) => item.kind === "event" && item.ends_at && new Date(item.ends_at) >= new Date())
                .sort((left, right) => (left.starts_at || "").localeCompare(right.starts_at || ""))
                .slice(0, 8),
        [data],
    );

    function moveMonth(offset: number) {
        setAnchor((current) => localDate(current.getFullYear(), current.getMonth() + offset, 1));
    }

    async function createEvent(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!eventTitle.trim() || !eventStart || !eventEnd) return;
        try {
            setCreating(true);
            setError(null);
            await fetchAPI(`${API_URL}/api/admin/calendar/events`, {
                method: "POST",
                body: JSON.stringify({
                    ownership_type: "internal",
                    title: eventTitle.trim(),
                    event_type: eventType,
                    starts_at: new Date(eventStart).toISOString(),
                    ends_at: new Date(eventEnd).toISOString(),
                    location: eventLocation.trim(),
                    meeting_url: eventMeetingUrl.trim(),
                }),
            });
            setEventTitle("");
            setEventStart("");
            setEventEnd("");
            setEventLocation("");
            setEventMeetingUrl("");
            setShowCreate(false);
            await load();
        } catch (createError) {
            setError(createError instanceof Error ? createError.message : "Unable to create the Event.");
        } finally {
            setCreating(false);
        }
    }

    if (loading && !data) return <DataLoading label="Loading work calendar..." />;
    if (error && !data) return <DataError message={error} onRetry={() => void load()} />;

    return (
        <div className="space-y-5">
            {error ? (
                <div className="rounded-lg border border-red-900/70 bg-red-950/40 px-4 py-3 text-sm text-red-200">
                    {error}
                </div>
            ) : null}

            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                <div className="flex flex-wrap items-center gap-3">
                    <Button variant="outline" onClick={() => moveMonth(-1)} aria-label="Previous month">
                        ←
                    </Button>
                    <div className="min-w-48 text-center text-xl font-semibold text-white">
                        {new Intl.DateTimeFormat("en-GB", { month: "long", year: "numeric" }).format(anchor)}
                    </div>
                    <Button variant="outline" onClick={() => moveMonth(1)} aria-label="Next month">
                        →
                    </Button>
                    <Button variant="ghost" onClick={() => setAnchor(new Date())}>
                        Today
                    </Button>
                    {hasPermission("tasks.add_calendarevent") ? (
                        <Button onClick={() => setShowCreate((value) => !value)}>
                            {showCreate ? "Cancel" : "New event"}
                        </Button>
                    ) : null}
                </div>

                <div className="flex flex-wrap items-center gap-2">
                    {(
                        [
                            ["all", "All work"],
                            ["event", `Events (${data?.event_count ?? 0})`],
                            ["task", `Tasks (${data?.task_count ?? 0})`],
                            ["project", `Projects (${data?.project_count ?? 0})`],
                        ] as Array<[CalendarFilter, string]>
                    ).map(([value, label]) => (
                        <button
                            key={value}
                            type="button"
                            onClick={() => setFilter(value)}
                            className={`rounded-lg border px-3 py-2 text-xs font-medium transition ${
                                filter === value
                                    ? "border-adb-cyan-700 bg-adb-cyan-950/30 text-adb-cyan-200"
                                    : "border-slate-800 bg-slate-900 text-slate-500 hover:text-slate-300"
                            }`}
                        >
                            {label}
                        </button>
                    ))}
                </div>
            </div>

            {showCreate ? (
                <Card className="p-5">
                    <form onSubmit={(event) => void createEvent(event)} className="space-y-4">
                        <div>
                            <p className="font-semibold text-white">Create Internal Event</p>
                            <p className="mt-1 text-xs text-slate-500">
                                Client-owned Events remain available through the same scoped API; this quick-create intentionally defaults to Internal to avoid accidental Client association.
                            </p>
                        </div>
                        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                            <input
                                value={eventTitle}
                                onChange={(event) => setEventTitle(event.target.value)}
                                placeholder="Event title"
                                required
                                className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                            />
                            <select
                                value={eventType}
                                onChange={(event) => setEventType(event.target.value)}
                                className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                            >
                                <option value="event">Event</option>
                                <option value="meeting">Meeting</option>
                                <option value="milestone">Milestone</option>
                                <option value="reminder">Reminder</option>
                            </select>
                            <input
                                type="datetime-local"
                                value={eventStart}
                                onChange={(event) => setEventStart(event.target.value)}
                                required
                                className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                            />
                            <input
                                type="datetime-local"
                                value={eventEnd}
                                onChange={(event) => setEventEnd(event.target.value)}
                                required
                                className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                            />
                            <input
                                value={eventLocation}
                                onChange={(event) => setEventLocation(event.target.value)}
                                placeholder="Location (optional)"
                                className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                            />
                            <input
                                type="url"
                                value={eventMeetingUrl}
                                onChange={(event) => setEventMeetingUrl(event.target.value)}
                                placeholder="Meeting URL (optional)"
                                className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                            />
                        </div>
                        <Button type="submit" disabled={creating}>
                            {creating ? "Creating..." : "Create event"}
                        </Button>
                    </form>
                </Card>
            ) : null}

            <Card className="overflow-hidden">
                <div className="grid grid-cols-7 border-b border-slate-800 bg-slate-900/70">
                    {weekdayLabels.map((label) => (
                        <div
                            key={label}
                            className="border-r border-slate-800 px-3 py-2 text-center text-[11px] font-semibold uppercase tracking-wide text-slate-500 last:border-r-0"
                        >
                            {label}
                        </div>
                    ))}
                </div>

                <div className="grid grid-cols-7">
                    {days.map((day, index) => {
                        const dateKey = isoDate(day);
                        const items = visibleItems.filter(
                            (item) => item.start_date <= dateKey && item.end_date >= dateKey,
                        );
                        const inMonth = day.getMonth() === currentMonth;
                        const isToday = dateKey === today;
                        return (
                            <div
                                key={dateKey}
                                className={`min-h-36 border-b border-r border-slate-800 p-2 ${
                                    index % 7 === 6 ? "border-r-0" : ""
                                } ${index >= 35 ? "border-b-0" : ""} ${
                                    inMonth ? "bg-slate-950" : "bg-slate-950/45"
                                }`}
                            >
                                <div className="mb-2 flex items-center justify-between">
                                    <span
                                        className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
                                            isToday
                                                ? "bg-adb-cyan-500 text-slate-950"
                                                : inMonth
                                                  ? "text-slate-300"
                                                  : "text-slate-700"
                                        }`}
                                    >
                                        {day.getDate()}
                                    </span>
                                </div>
                                <div className="space-y-1">
                                    {items.slice(0, 4).map((item) => {
                                        const href = itemHref(item);
                                        const className = `block truncate rounded-md border px-2 py-1.5 text-[11px] transition hover:brightness-125 ${itemClasses(item)}`;
                                        const content = (
                                            <>
                                                <span className="mr-1 text-[9px] font-bold uppercase opacity-60">
                                                    {itemPrefix(item)}
                                                </span>
                                                {item.title}
                                            </>
                                        );
                                        return href ? (
                                            <Link
                                                key={`${item.kind}-${item.id}`}
                                                href={href}
                                                title={`${item.title} · ${itemContext(item)}`}
                                                className={className}
                                            >
                                                {content}
                                            </Link>
                                        ) : (
                                            <div
                                                key={`${item.kind}-${item.id}`}
                                                title={`${item.title} · ${itemContext(item)}`}
                                                className={className}
                                            >
                                                {content}
                                            </div>
                                        );
                                    })}
                                    {items.length > 4 ? (
                                        <div className="px-2 py-1 text-[10px] text-slate-600">+{items.length - 4} more</div>
                                    ) : null}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </Card>

            {upcomingEvents.length > 0 ? (
                <Card>
                    <div className="border-b border-slate-800 px-5 py-4">
                        <h2 className="font-semibold text-white">Upcoming Events & Meetings</h2>
                        <p className="mt-1 text-xs text-slate-500">Time-aware Event details complement the month grid.</p>
                    </div>
                    <div className="divide-y divide-slate-800">
                        {upcomingEvents.map((item) => (
                            <div key={item.id} className="flex flex-col gap-3 px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
                                <div>
                                    <p className="font-medium text-slate-200">{item.title}</p>
                                    <p className="mt-1 text-xs text-slate-500">
                                        {item.event_type?.replaceAll("_", " ")} · {item.starts_at ? new Intl.DateTimeFormat("en-GB", { dateStyle: "medium", timeStyle: "short" }).format(new Date(item.starts_at)) : item.start_date}
                                        {item.location ? ` · ${item.location}` : ""}
                                    </p>
                                </div>
                                {item.meeting_url ? (
                                    <a
                                        href={item.meeting_url}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="text-sm font-medium text-adb-cyan-300 hover:text-adb-cyan-200"
                                    >
                                        Join meeting ↗
                                    </a>
                                ) : null}
                            </div>
                        ))}
                    </div>
                </Card>
            ) : null}

            {!loading && visibleItems.length === 0 ? (
                <EmptyState
                    title="Nothing scheduled in this view"
                    description="Dated Tasks, Projects and first-class Events will appear here. Change month or filter to inspect another part of the schedule."
                />
            ) : null}

            <div className="flex flex-wrap gap-2 text-xs text-slate-600">
                <Badge>Event</Badge>
                <Badge>Task</Badge>
                <Badge>Project</Badge>
                <span>Events carry exact times, locations and meeting links; Tasks and Projects retain their existing date-span semantics.</span>
            </div>
        </div>
    );
}
