"use client";

import { API_URL } from "@/lib/config";

import { fetchAPI } from "@/lib/api/fetch";
import { Dialog, DialogPanel, DialogTitle } from "@headlessui/react";
import { MagnifyingGlassIcon, XMarkIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

const API_BASE_URL = `${API_URL}/api`;

interface SearchResult {
    kind: string;
    id: number;
    title: string;
    subtitle: string;
    context: string;
    href: string;
    client_id: number | null;
    client_name: string | null;
    updated_at: string | null;
}

interface SearchGroup {
    kind: string;
    label: string;
    results: SearchResult[];
}

interface SearchResponse {
    query: string;
    client_id: number | null;
    client_name: string | null;
    total_results: number;
    groups: SearchGroup[];
}

function currentClientId(pathname: string) {
    const match = pathname.match(/^\/admin\/clients\/(\d+)(?:\/|$)/);
    return match ? Number(match[1]) : null;
}

export function GlobalSearch() {
    const pathname = usePathname();
    const clientId = useMemo(() => currentClientId(pathname), [pathname]);
    const [open, setOpen] = useState(false);
    const [query, setQuery] = useState("");
    const [clientOnly, setClientOnly] = useState(Boolean(clientId));
    const [data, setData] = useState<SearchResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        function onKeyDown(event: KeyboardEvent) {
            if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
                event.preventDefault();
                setClientOnly(Boolean(clientId));
                setOpen(true);
            }
        }
        window.addEventListener("keydown", onKeyDown);
        return () => window.removeEventListener("keydown", onKeyDown);
    }, [clientId]);

    useEffect(() => {
        const trimmedQuery = query.trim();
        if (!open || trimmedQuery.length < 2) {
            setData(null);
            setError(null);
            setLoading(false);
            return;
        }

        const controller = new AbortController();
        setLoading(true);
        const timer = window.setTimeout(() => {
            const run = async () => {
                try {
                    setError(null);
                    const response = (await fetchAPI(`${API_BASE_URL}/admin/search`, {
                        method: "POST",
                        body: JSON.stringify({
                            q: trimmedQuery,
                            client_id: clientOnly && clientId ? clientId : null,
                            per_type: 6,
                        }),
                        signal: controller.signal,
                    })) as SearchResponse;
                    if (!controller.signal.aborted) setData(response);
                } catch (reason) {
                    if (controller.signal.aborted) return;
                    setData(null);
                    setError(reason instanceof Error ? reason.message : "Search failed.");
                } finally {
                    if (!controller.signal.aborted) setLoading(false);
                }
            };
            void run();
        }, 180);

        return () => {
            window.clearTimeout(timer);
            controller.abort();
        };
    }, [clientId, clientOnly, open, query]);

    function show() {
        setQuery("");
        setData(null);
        setError(null);
        setClientOnly(Boolean(clientId));
        setOpen(true);
    }

    return (
        <>
            <button
                type="button"
                onClick={show}
                className="group flex h-9 min-w-0 flex-1 items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/70 px-3 text-left text-sm text-slate-500 transition hover:border-slate-700 hover:text-slate-300 md:max-w-xl"
                title="Search Clients, Tickets, Projects, Tasks, Knowledge and technical operations"
            >
                <MagnifyingGlassIcon className="h-4 w-4 shrink-0" />
                <span className="truncate">
                    {clientId ? "Search this Client or the platform..." : "Search the platform..."}
                </span>
                <kbd className="ml-auto hidden rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-[10px] text-slate-600 sm:block">
                    ⌘K
                </kbd>
            </button>

            <Dialog open={open} onClose={setOpen} className="relative z-[80]">
                <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm" aria-hidden="true" />
                <div className="fixed inset-0 overflow-y-auto p-4 sm:p-8">
                    <div className="mx-auto flex min-h-full max-w-3xl items-start justify-center pt-[8vh]">
                        <DialogPanel className="w-full overflow-hidden rounded-2xl border border-slate-700 bg-slate-950 shadow-2xl shadow-black/60">
                            <div className="flex items-center gap-3 border-b border-slate-800 px-4 py-3">
                                <MagnifyingGlassIcon className="h-5 w-5 shrink-0 text-adb-cyan-400" />
                                <DialogTitle className="sr-only">Search the platform</DialogTitle>
                                <input
                                    autoFocus
                                    value={query}
                                    onChange={(event) => setQuery(event.target.value)}
                                    placeholder="Search clients, tickets, projects, tasks, documentation..."
                                    className="h-10 min-w-0 flex-1 bg-transparent text-base text-slate-100 outline-none placeholder:text-slate-600"
                                />
                                <button
                                    type="button"
                                    onClick={() => setOpen(false)}
                                    className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-800 hover:text-slate-200"
                                    aria-label="Close search"
                                >
                                    <XMarkIcon className="h-5 w-5" />
                                </button>
                            </div>

                            {clientId ? (
                                <div className="flex items-center justify-between gap-4 border-b border-slate-800 bg-slate-900/40 px-4 py-2.5">
                                    <p className="text-xs text-slate-500">
                                        {clientOnly
                                            ? `Searching this Client${data?.client_name ? `: ${data.client_name}` : ""}`
                                            : "Searching all records you can access"}
                                    </p>
                                    <button
                                        type="button"
                                        onClick={() => setClientOnly((value) => !value)}
                                        className="text-xs font-medium text-adb-cyan-400 hover:text-adb-cyan-300"
                                    >
                                        {clientOnly ? "Search everywhere" : "Search this Client"}
                                    </button>
                                </div>
                            ) : null}

                            <div className="max-h-[65vh] overflow-y-auto p-2">
                                {query.trim().length < 2 ? (
                                    <div className="px-4 py-12 text-center text-sm text-slate-600">
                                        Type at least two characters to search your authorised workspaces.
                                    </div>
                                ) : null}

                                {loading ? (
                                    <div className="px-4 py-12 text-center text-sm text-slate-500">
                                        Searching…
                                    </div>
                                ) : null}

                                {error ? (
                                    <div className="m-2 rounded-xl border border-red-900/60 bg-red-950/30 px-4 py-3 text-sm text-red-300">
                                        {error}
                                    </div>
                                ) : null}

                                {!loading && data && data.total_results === 0 ? (
                                    <div className="px-4 py-12 text-center text-sm text-slate-600">
                                        No authorised results found for “{data.query}”.
                                    </div>
                                ) : null}

                                {!loading && data
                                    ? data.groups.map((group) => (
                                          <section key={group.kind} className="mb-2 last:mb-0">
                                              <div className="px-3 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wider text-slate-600">
                                                  {group.label}
                                              </div>
                                              <div className="space-y-1">
                                                  {group.results.map((result) => (
                                                      <Link
                                                          key={`${result.kind}-${result.id}`}
                                                          href={result.href}
                                                          onClick={() => setOpen(false)}
                                                          className="block rounded-xl px-3 py-3 transition hover:bg-slate-900"
                                                      >
                                                          <div className="flex items-start justify-between gap-4">
                                                              <div className="min-w-0">
                                                                  <p className="truncate text-sm font-medium text-slate-100">
                                                                      {result.title}
                                                                  </p>
                                                                  {result.subtitle ? (
                                                                      <p className="mt-1 truncate text-xs text-slate-500">
                                                                          {result.subtitle}
                                                                      </p>
                                                                  ) : null}
                                                              </div>
                                                              {result.context ? (
                                                                  <span className="max-w-48 shrink-0 truncate rounded-md border border-slate-800 bg-slate-900 px-2 py-1 text-[11px] text-slate-500">
                                                                      {result.context}
                                                                  </span>
                                                              ) : null}
                                                          </div>
                                                      </Link>
                                                  ))}
                                              </div>
                                          </section>
                                      ))
                                    : null}
                            </div>

                            <div className="border-t border-slate-800 px-4 py-2.5 text-[11px] text-slate-600">
                                Results are filtered by your live permissions, Client scope and Ticket Queue scope.
                            </div>
                        </DialogPanel>
                    </div>
                </div>
            </Dialog>
        </>
    );
}
