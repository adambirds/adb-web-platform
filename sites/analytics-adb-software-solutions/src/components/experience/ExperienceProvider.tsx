"use client";
import {
    createContext,
    useContext,
    useEffect,
    useState,
    type ReactNode,
} from "react";
import Link from "next/link";
import {usePathname, useSearchParams} from "next/navigation";
import {
    ArrowUpRightIcon,
    ChartBarIcon,
    MoonIcon,
    PlusIcon,
    SunIcon,
} from "@heroicons/react/24/outline";
import {AUTH_URL, initialDates, type Session} from "../../app/client";
import type {Period} from "../../lib/experience";
import {useResource} from "./useResource";

type Experience = {
    session: Session;
    period: Period;
    comparison: boolean;
    refreshSession: () => void;
};
const Context = createContext<Experience | null>(null);
export function useExperience() {
    const value = useContext(Context);
    if (!value) throw new Error("Analytics context is missing");
    return value;
}
export function LoadingExperience() {
    return (
        <main className="experience-page">
            <div className="page-heading">
                <div className="skeleton skeleton-title" />
            </div>
            <div className="metric-grid">
                {[1, 2, 3, 4].map((key) => (
                    <div className="skeleton skeleton-metric" key={key} />
                ))}
            </div>
            <div className="skeleton skeleton-chart" />
            <span className="sr-only" role="status">
                Loading analytics
            </span>
        </main>
    );
}
export function ErrorState({
    message,
    retry,
}: {
    message: string;
    retry: () => void;
}) {
    return (
        <div className="error-state" role="alert">
            <strong>We couldn’t load this view</strong>
            <p>{message}</p>
            <button className="button" onClick={retry}>
                Try again
            </button>
        </div>
    );
}

export function ExperienceProvider({children}: {children: ReactNode}) {
    const pathname = usePathname(),
        search = useSearchParams();
    const {data: session, error, reload} = useResource<Session>("/session");
    const [dark, setDark] = useState(false);
    useEffect(
        () => setDark(document.documentElement.dataset.theme === "dark"),
        [],
    );
    const fallback = initialDates();
    const valid = (value: string | null) =>
        Boolean(
            value &&
            /^\d{4}-\d{2}-\d{2}$/.test(value) &&
            !Number.isNaN(Date.parse(value)),
        );
    const period = {
        start: valid(search.get("start"))
            ? search.get("start")!
            : fallback.start,
        end: valid(search.get("end")) ? search.get("end")! : fallback.end,
    };
    const query =
        "?" +
        new URLSearchParams({
            ...period,
            ...(search.get("compare") === "0" ? {compare: "0"} : {}),
        }).toString();
    return (
        <div className="analytics-experience">
            <header className="experience-topbar">
                <Link className="experience-brand" href="/dashboard">
                    <span className="brand-symbol">
                        <ChartBarIcon />
                    </span>
                    <span>
                        adb<span className="brand-divider">/</span>
                        <strong>analytics</strong>
                    </span>
                </Link>
                <nav
                    className="experience-navigation"
                    aria-label="Primary navigation"
                >
                    <Link
                        aria-current={
                            pathname === "/dashboard" ? "page" : undefined
                        }
                        href={"/dashboard" + query}
                    >
                        Portfolio
                    </Link>
                    <Link
                        aria-current={
                            pathname === "/dashboard/insights"
                                ? "page"
                                : undefined
                        }
                        href={"/dashboard/insights" + query}
                    >
                        Insights
                    </Link>
                </nav>
                <div className="topbar-actions">
                    <span className="private-badge">
                        <span />
                        Private workspace
                    </span>
                    <button
                        className="icon-button"
                        aria-label={
                            dark
                                ? "Switch to light mode"
                                : "Switch to dark mode"
                        }
                        onClick={() => {
                            const next = !dark;
                            setDark(next);
                            document.documentElement.dataset.theme = next
                                ? "dark"
                                : "light";
                            try {
                                localStorage.setItem(
                                    "adb-analytics-theme",
                                    next ? "dark" : "light",
                                );
                            } catch {
                                /* Storage is optional. */
                            }
                        }}
                    >
                        {dark ? <SunIcon /> : <MoonIcon />}
                    </button>
                    {session && (
                        <Link
                            className="button button-small"
                            href="/dashboard/settings?tab=websites"
                        >
                            <PlusIcon />
                            Add websites
                        </Link>
                    )}
                    <details className="account-menu">
                        <summary aria-label="Account menu" className="avatar">
                            {session?.email.slice(0, 1).toUpperCase() ?? "A"}
                        </summary>
                        <div className="account-popover">
                            <small>{session?.email}</small>
                            <Link href="/dashboard/settings">
                                Workspace settings
                            </Link>
                            <a href={AUTH_URL + "/account"}>
                                Account & security <ArrowUpRightIcon />
                            </a>
                        </div>
                    </details>
                </div>
            </header>
            {error && !session ? (
                <main className="experience-page">
                    <ErrorState message={error} retry={reload} />
                </main>
            ) : !session ? (
                <LoadingExperience />
            ) : (
                <Context
                    value={{
                        session,
                        period,
                        comparison: search.get("compare") !== "0",
                        refreshSession: reload,
                    }}
                >
                    {children}
                </Context>
            )}
        </div>
    );
}
