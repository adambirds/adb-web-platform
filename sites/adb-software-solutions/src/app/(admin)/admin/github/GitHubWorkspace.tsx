"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";

import {
    Button,
    Card,
    Input,
    Pagination,
    Select,
    Textarea,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { githubAPI, type GitHubRow, type GitHubItem } from "./contracts";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { GitHubConnections } from "./GitHubConnections";
import { GitHubRunJobs } from "./GitHubRunJobs";

interface Options {
    username: string;
    configured: boolean;
    install_url: string;
    accounts: { installation_id: number; installation__account: string }[];
}
interface Page {
    rows: GitHubRow[];
    page: number;
    pages: number;
    total: number;
}
const tabs = [
    ["pull_request", "Pull requests"],
    ["issue", "Issues"],
    ["repository", "Repositories"],
    ["workflow", "Workflows"],
    ["run", "Workflow runs"],
] as const;

export function GitHubWorkspace() {
    const { hasPermission } = useAuth();
    const canView =
        hasPermission("github_integration.view_repository") &&
        hasPermission("infrastructure.view_infrastructureresource");
    const canTrigger = hasPermission("github_integration.trigger_workflow");
    const [tab, setTab] = useState("pull_request");
    const [view, setView] = useState("my");
    const [account, setAccount] = useState("");
    const [search, setSearch] = useState("");
    const [state, setState] = useState("open");
    const [page, setPage] = useState(1);
    const [options, setOptions] = useState<Options | null>(null);
    const [username, setUsername] = useState("");
    const [data, setData] = useState<Page | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [notice, setNotice] = useState("");
    const [loading, setLoading] = useState(false);
    const [busy, setBusy] = useState(false);
    const [workflow, setWorkflow] = useState<GitHubItem | null>(null);
    const [run, setRun] = useState<GitHubItem | null>(null);
    const [ref, setRef] = useState("");
    const [inputs, setInputs] = useState("{}");
    const sequence = useRef(0);
    const loadOptions = useCallback(async () => {
        const result = (await fetchAPI(`${githubAPI}/options`)) as Options;
        setOptions(result);
        setUsername(result.username);
    }, []);
    useEffect(() => {
        if (!canView) return;
        let active = true;
        void loadOptions().catch((reason: Error) => {
            if (active) setError(reason.message);
        });
        return () => {
            active = false;
        };
    }, [canView, loadOptions]);
    const load = useCallback(async () => {
        if (!canView || tab === "connections") return;
        const request = ++sequence.current;
        const query = new URLSearchParams({
            page: String(page),
            account,
            search,
            kind: tab,
            view,
            state,
        });
        if (!account) query.delete("account");
        setLoading(true);
        try {
            const result = (await fetchAPI(
                `${githubAPI}/${tab === "repository" ? "repositories" : "items"}?${query}`,
            )) as Page;
            if (request === sequence.current) {
                setData(result);
                setError(null);
            }
        } catch (reason) {
            if (request === sequence.current)
                setError(
                    reason instanceof Error
                        ? reason.message
                        : "Unable to load GitHub.",
                );
        } finally {
            if (request === sequence.current) setLoading(false);
        }
    }, [canView, tab, page, account, search, view, state]);
    useEffect(() => {
        setData(null);
        void load();
        return () => {
            ++sequence.current;
        };
    }, [load]);
    useLiveRefresh(["github"], async () => {
        await load();
        if (canView) setOptions((await fetchAPI(`${githubAPI}/options`)) as Options);
    });
    function chooseTab(value: string) {
        setTab(value);
        setPage(1);
        setRun(null);
        setWorkflow(null);
        setView(value === "pull_request" || value === "issue" ? "my" : "all");
    }
    async function saveUsername() {
        setBusy(true);
        setError(null);
        try {
            await fetchAPI(`${githubAPI}/preference`, {
                method: "PUT",
                body: JSON.stringify({ username }),
            });
            await loadOptions();
            await load();
        } catch (reason) {
            setError(
                reason instanceof Error
                    ? reason.message
                    : "Unable to save username.",
            );
        } finally {
            setBusy(false);
        }
    }
    async function action(row: GitHubItem, dispatch: boolean) {
        if (
            !window.confirm(
                dispatch
                    ? `Start ${row.title} on ${ref}?`
                    : `Rerun failed jobs for ${row.title}?`,
            )
        )
            return;
        setBusy(true);
        setError(null);
        setNotice("");
        try {
            let payload:
                { ref: string; inputs: Record<string, string> } | undefined;
            if (dispatch) {
                const parsed: unknown = JSON.parse(inputs);
                if (
                    !parsed ||
                    typeof parsed !== "object" ||
                    Array.isArray(parsed) ||
                    Object.values(parsed).some(
                        (value) => typeof value !== "string",
                    )
                )
                    throw new Error(
                        "Workflow inputs must be a JSON object with text values.",
                    );
                payload = { ref, inputs: parsed as Record<string, string> };
            }
            await fetchAPI(
                `${githubAPI}/repositories/${row.repository_id}/${dispatch ? "workflows" : "runs"}/${row.github_id}/${dispatch ? "dispatch" : "rerun"}`,
                {
                    method: "POST",
                    body: payload ? JSON.stringify(payload) : undefined,
                },
            );
            setNotice(
                "GitHub accepted the request. The run will appear after GitHub sends its update.",
            );
            setWorkflow(null);
            await load();
        } catch (reason) {
            setError(
                reason instanceof Error
                    ? reason.message
                    : "The workflow request failed.",
            );
        } finally {
            setBusy(false);
        }
    }
    if (!canView)
        return (
            <p className="text-slate-400">
                You do not have permission to view GitHub repositories.
            </p>
        );
    return (
        <div className="space-y-5">
            <div>
                <h1 className="text-2xl font-semibold text-white">GitHub</h1>
                <p className="mt-2 text-sm text-slate-400">
                    Repositories, your work and GitHub Actions across connected
                    accounts. Updates appear automatically.
                </p>
            </div>
            {options && !options.configured ? (
                <Card className="p-4">
                    <p className="text-sm text-slate-300">
                        The GitHub App needs configuring before accounts can
                        synchronise. See the GitHub App setup guide in the
                        platform documentation.
                    </p>
                </Card>
            ) : null}
            <div
                className="flex flex-wrap gap-2"
                role="tablist"
                aria-label="GitHub views"
            >
                {tabs.map(([value, label]) => (
                    <Button
                        key={value}
                        role="tab"
                        aria-selected={tab === value}
                        variant={tab === value ? "primary" : "secondary"}
                        onClick={() => chooseTab(value)}
                    >
                        {label}
                    </Button>
                ))}
                {hasPermission("github_integration.manage_github") ? (
                    <Button
                        role="tab"
                        aria-selected={tab === "connections"}
                        variant="secondary"
                        onClick={() => chooseTab("connections")}
                    >
                        Connections
                    </Button>
                ) : null}
            </div>
            {error ? (
                <p role="alert" className="text-sm text-red-300">
                    {error}
                </p>
            ) : null}
            {notice ? (
                <p role="status" className="text-sm text-emerald-300">
                    {notice}
                </p>
            ) : null}
            {tab === "connections" ? (
                <GitHubConnections
                    installURL={options?.install_url ?? ""}
                    onChanged={() => void loadOptions()}
                />
            ) : (
                <>
                    <Card className="flex flex-wrap items-end gap-4 p-4">
                        <label className="text-sm text-slate-300">
                            Account
                            <Select
                                value={account}
                                onChange={(event) => {
                                    setAccount(event.target.value);
                                    setPage(1);
                                }}
                            >
                                <option value="">All accounts</option>
                                {options?.accounts.map((row) => (
                                    <option
                                        key={row.installation_id}
                                        value={row.installation_id}
                                    >
                                        {row.installation__account}
                                    </option>
                                ))}
                            </Select>
                        </label>
                        {tab === "repository" ? (
                            <label className="text-sm text-slate-300">
                                Search repositories
                                <Input
                                    value={search}
                                    onChange={(event) => {
                                        setSearch(event.target.value);
                                        setPage(1);
                                    }}
                                />
                            </label>
                        ) : (
                            <label className="text-sm text-slate-300">
                                Show
                                <Select
                                    value={view}
                                    onChange={(event) => {
                                        setView(event.target.value);
                                        setPage(1);
                                    }}
                                >
                                    <option value="my">My work</option>
                                    <option value="human">People</option>
                                    <option value="dependabot">
                                        Dependabot
                                    </option>
                                    <option value="all">Everything</option>
                                </Select>
                            </label>
                        )}
                        {tab === "issue" || tab === "pull_request" ? (
                            <label className="text-sm text-slate-300">
                                Status
                                <Select
                                    value={state}
                                    onChange={(event) => {
                                        setState(event.target.value);
                                        setPage(1);
                                    }}
                                >
                                    <option value="open">Open</option>
                                    <option value="all">
                                        All synced history
                                    </option>
                                    <option value="closed">Closed</option>
                                    {tab === "pull_request" ? (
                                        <option value="merged">Merged</option>
                                    ) : null}
                                </Select>
                            </label>
                        ) : null}
                        <Button
                            variant="secondary"
                            disabled={loading}
                            onClick={() => void load()}
                        >
                            Refresh
                        </Button>
                    </Card>
                    {view === "my" && tab !== "repository" ? (
                        <Card className="p-4">
                            <p className="mb-3 text-sm text-slate-400">
                                My work includes items you authored, are
                                assigned to, or are requested to review. Set
                                your GitHub username to filter this view.
                            </p>
                            <div className="flex items-end gap-3">
                                <label className="text-sm text-slate-300">
                                    GitHub username
                                    <Input
                                        value={username}
                                        onChange={(event) =>
                                            setUsername(event.target.value)
                                        }
                                    />
                                </label>
                                <Button
                                    disabled={busy}
                                    onClick={() => void saveUsername()}
                                >
                                    Save username
                                </Button>
                            </div>
                        </Card>
                    ) : null}
                    <Card
                        className="divide-y divide-slate-800"
                        aria-busy={loading}
                    >
                        {data?.rows.map((row) => (
                            <div
                                key={row.id}
                                className="flex flex-wrap items-center justify-between gap-4 p-4"
                            >
                                <div className="min-w-0">
                                    <a
                                        href={row.url || undefined}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="text-sm font-medium text-cyan-300"
                                    >
                                        {row.kind === "repository"
                                            ? row.name
                                            : row.title}
                                    </a>
                                    <p className="mt-1 text-xs text-slate-400">
                                        {row.kind === "repository"
                                            ? row.account
                                            : `${row.repository} · ${row.author} · ${row.conclusion || row.state}`}{" "}
                                        · {row.branch}
                                    </p>
                                    {row.kind === "repository" && row.error ? (
                                        <p className="text-xs text-red-300">
                                            {row.error}
                                        </p>
                                    ) : null}
                                </div>
                                <div className="flex gap-2">
                                    {row.kind === "repository" ? (
                                        <Link
                                            className="text-sm text-cyan-300"
                                            href={`/admin/infrastructure/resources/${row.resource_id}`}
                                        >
                                            Open resource
                                        </Link>
                                    ) : null}
                                    {row.kind === "workflow" &&
                                    canTrigger &&
                                    row.state === "active" ? (
                                        <Button
                                            size="sm"
                                            onClick={() => {
                                                setWorkflow(row);
                                                setRef(row.branch);
                                                setInputs("{}");
                                            }}
                                        >
                                            Start workflow
                                        </Button>
                                    ) : null}
                                    {row.kind === "run" ? (
                                        <Button
                                            size="sm"
                                            variant="secondary"
                                            onClick={() => setRun(row)}
                                        >
                                            Jobs and logs
                                        </Button>
                                    ) : null}
                                    {row.kind === "run" &&
                                    canTrigger &&
                                    row.state === "completed" &&
                                    ["failure", "timed_out"].includes(
                                        row.conclusion,
                                    ) ? (
                                        <Button
                                            size="sm"
                                            disabled={busy}
                                            onClick={() =>
                                                void action(row, false)
                                            }
                                        >
                                            Rerun failed jobs
                                        </Button>
                                    ) : null}
                                </div>
                            </div>
                        ))}
                        {data?.rows.length === 0 ? (
                            <p className="p-6 text-sm text-slate-400">
                                No matching GitHub items. Connect an account, or
                                change your filters.
                            </p>
                        ) : null}
                        {!data && loading ? (
                            <p className="p-6 text-sm text-slate-400">
                                Loading GitHub…
                            </p>
                        ) : null}
                        {data ? (
                            <Pagination
                                page={data.page}
                                pageSize={25}
                                totalItems={data.total}
                                onPageChange={setPage}
                                disabled={loading}
                            />
                        ) : null}
                    </Card>
                    {workflow ? (
                        <Card className="space-y-3 p-4">
                            <h2 className="font-semibold text-white">
                                Start {workflow.title}
                            </h2>
                            <p className="text-sm text-slate-400">
                                The workflow must allow manual runs in GitHub.
                                Enter any input names and values it requires.
                            </p>
                            <label className="block text-sm text-slate-300">
                                Branch or tag
                                <Input
                                    value={ref}
                                    onChange={(event) =>
                                        setRef(event.target.value)
                                    }
                                />
                            </label>
                            <label className="block text-sm text-slate-300">
                                Workflow inputs (JSON)
                                <Textarea
                                    value={inputs}
                                    onChange={(event) =>
                                        setInputs(event.target.value)
                                    }
                                />
                            </label>
                            <div className="flex gap-2">
                                <Button
                                    disabled={busy || !ref.trim()}
                                    onClick={() => void action(workflow, true)}
                                >
                                    Confirm start
                                </Button>
                                <Button
                                    variant="secondary"
                                    onClick={() => setWorkflow(null)}
                                >
                                    Cancel
                                </Button>
                            </div>
                        </Card>
                    ) : null}
                    {run ? (
                        <GitHubRunJobs
                            key={run.id}
                            run={run}
                            onClose={() => setRun(null)}
                        />
                    ) : null}
                </>
            )}
        </div>
    );
}
