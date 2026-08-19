"use client";

import { Button, ButtonLink, DataLoading, Input, Select, Textarea } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

type ProjectOwnership = "client" | "internal";
type ProjectStatus = "planning" | "active" | "paused" | "completed" | "archived";

interface ClientOption {
    id: number;
    name: string;
    company: string;
    status: string;
}

interface ProjectFormState {
    name: string;
    description: string;
    status: ProjectStatus;
    ownership_type: ProjectOwnership;
    client_id: number | null;
    start_date: string;
    end_date: string;
    budget: string;
    hourly_rate: string;
}

interface ProjectResponse {
    id: number;
    name: string;
    description: string;
    status: ProjectStatus;
    ownership_type: ProjectOwnership;
    client_id: number | null;
    start_date: string;
    end_date: string | null;
    budget: string | null;
    hourly_rate: string | null;
}

const EMPTY_FORM: ProjectFormState = {
    name: "",
    description: "",
    status: "active",
    ownership_type: "client",
    client_id: null,
    start_date: "",
    end_date: "",
    budget: "",
    hourly_rate: "",
};

const labelClasses = "space-y-1.5 text-sm font-medium text-slate-300";

function optionalId(value: string) {
    return value ? Number(value) : null;
}

function optionalAmount(value: string) {
    return value.trim() ? Number(value) : null;
}

export function ProjectForm({ projectId }: { projectId?: number }) {
    const router = useRouter();
    const [form, setForm] = useState<ProjectFormState>(EMPTY_FORM);
    const [clients, setClients] = useState<ClientOption[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                setIsLoading(true);
                setError(null);
                const [clientRows, project] = await Promise.all([
                    fetchAPI(AdminAPI.clients.list()) as Promise<ClientOption[]>,
                    projectId
                        ? (fetchAPI(AdminAPI.projects.get(projectId)) as Promise<ProjectResponse>)
                        : Promise.resolve(null),
                ]);
                setClients(clientRows);
                if (project) {
                    setForm({
                        name: project.name,
                        description: project.description,
                        status: project.status,
                        ownership_type: project.ownership_type,
                        client_id: project.client_id,
                        start_date: project.start_date,
                        end_date: project.end_date ?? "",
                        budget: project.budget ?? "",
                        hourly_rate: project.hourly_rate ?? "",
                    });
                }
            } catch (loadError) {
                setError(
                    loadError instanceof Error
                        ? loadError.message
                        : "Unable to load project details.",
                );
            } finally {
                setIsLoading(false);
            }
        }

        void load();
    }, [projectId]);

    function update<K extends keyof ProjectFormState>(key: K, value: ProjectFormState[K]) {
        setForm((current) => ({ ...current, [key]: value }));
    }

    function updateOwnership(value: ProjectOwnership) {
        setForm((current) => ({
            ...current,
            ownership_type: value,
            client_id: value === "internal" ? null : current.client_id,
        }));
    }

    async function save(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsSaving(true);
        setError(null);

        try {
            const project = (await fetchAPI(
                projectId ? AdminAPI.projects.update(projectId) : AdminAPI.projects.create(),
                {
                    method: projectId ? "PUT" : "POST",
                    body: JSON.stringify({
                        ...form,
                        client_id: form.ownership_type === "client" ? form.client_id : null,
                        end_date: form.end_date || null,
                        budget: optionalAmount(form.budget),
                        hourly_rate: optionalAmount(form.hourly_rate),
                    }),
                },
            )) as ProjectResponse;
            router.push(`/admin/projects/${project.id}`);
            router.refresh();
        } catch (saveError) {
            setError(saveError instanceof Error ? saveError.message : "Unable to save the project.");
        } finally {
            setIsSaving(false);
        }
    }

    if (isLoading) return <DataLoading label="Loading project details..." />;

    return (
        <form onSubmit={(event) => void save(event)} className="space-y-6">
            {error ? (
                <div
                    role="alert"
                    className="rounded-lg border border-red-900/70 bg-red-950/40 px-4 py-3 text-sm text-red-200"
                >
                    {error}
                </div>
            ) : null}

            <div className="grid gap-5 md:grid-cols-2">
                <label className={`${labelClasses} md:col-span-2`}>
                    <span>Project name</span>
                    <Input
                        value={form.name}
                        onChange={(event) => update("name", event.target.value)}
                        required
                        maxLength={200}
                    />
                </label>
                <label className={labelClasses}>
                    <span>Ownership</span>
                    <Select
                        value={form.ownership_type}
                        onChange={(event) => updateOwnership(event.target.value as ProjectOwnership)}
                    >
                        <option value="client">Client project</option>
                        <option value="internal">ADB internal project</option>
                    </Select>
                </label>
                <label className={labelClasses}>
                    <span>Client</span>
                    <Select
                        value={form.client_id ?? ""}
                        onChange={(event) => update("client_id", optionalId(event.target.value))}
                        disabled={form.ownership_type === "internal"}
                        required={form.ownership_type === "client"}
                    >
                        <option value="">
                            {form.ownership_type === "internal" ? "Not applicable" : "Select a client"}
                        </option>
                        {clients.map((client) => (
                            <option key={client.id} value={client.id}>
                                {client.company || client.name}
                                {client.status === "active" ? "" : ` (${client.status})`}
                            </option>
                        ))}
                    </Select>
                </label>
                <label className={labelClasses}>
                    <span>Status</span>
                    <Select
                        value={form.status}
                        onChange={(event) => update("status", event.target.value as ProjectStatus)}
                    >
                        <option value="planning">Planning</option>
                        <option value="active">Active</option>
                        <option value="paused">Paused</option>
                        <option value="completed">Completed</option>
                        <option value="archived">Archived</option>
                    </Select>
                </label>
                <div />
                <label className={labelClasses}>
                    <span>Start date</span>
                    <Input
                        type="date"
                        value={form.start_date}
                        onChange={(event) => update("start_date", event.target.value)}
                        required
                    />
                </label>
                <label className={labelClasses}>
                    <span>End date</span>
                    <Input
                        type="date"
                        value={form.end_date}
                        min={form.start_date || undefined}
                        onChange={(event) => update("end_date", event.target.value)}
                    />
                </label>
                <label className={labelClasses}>
                    <span>Budget</span>
                    <Input
                        type="number"
                        min="0"
                        step="0.01"
                        value={form.budget}
                        onChange={(event) => update("budget", event.target.value)}
                        placeholder="0.00"
                    />
                </label>
                <label className={labelClasses}>
                    <span>Hourly rate</span>
                    <Input
                        type="number"
                        min="0"
                        step="0.01"
                        value={form.hourly_rate}
                        onChange={(event) => update("hourly_rate", event.target.value)}
                        placeholder="0.00"
                    />
                </label>
            </div>

            <div className="border-t border-slate-800 pt-6">
                <label className={labelClasses}>
                    <span>Description</span>
                    <Textarea
                        value={form.description}
                        onChange={(event) => update("description", event.target.value)}
                        rows={8}
                        placeholder="Scope, delivery notes and other operational project context."
                    />
                </label>
            </div>

            <div className="flex flex-wrap gap-3 border-t border-slate-800 pt-6">
                <Button type="submit" disabled={isSaving}>
                    {isSaving ? "Saving..." : projectId ? "Save changes" : "Create project"}
                </Button>
                <ButtonLink
                    href={projectId ? `/admin/projects/${projectId}` : "/admin/projects"}
                    variant="outline"
                >
                    Cancel
                </ButtonLink>
            </div>
        </form>
    );
}
