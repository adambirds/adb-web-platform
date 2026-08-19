"use client";

import { Card, DataError, DataLoading, Select } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { useCallback, useEffect, useState } from "react";

interface TicketChoice {
    value: string;
    label: string;
}

interface TicketAgent {
    id: string;
    name: string;
    email: string;
}

interface TicketQueueOption {
    id: number;
    name: string;
    brand_id: number | null;
    brand_name: string | null;
}

interface TicketMutable {
    id: number;
    status: string;
    priority: string;
    queue_id: number;
    queue_name: string;
    assigned_to_id: string | null;
    assigned_to_name: string | null;
    resolved_at: string | null;
    closed_at: string | null;
    updated_at: string;
}

interface TicketOperationOptions {
    ticket: TicketMutable;
    can_assign: boolean;
    can_change: boolean;
    can_close: boolean;
    statuses: TicketChoice[];
    priorities: TicketChoice[];
    queues: TicketQueueOption[];
    assignees: TicketAgent[];
}

type OperationName = "status" | "priority" | "queue" | "assignment";

export function TicketControls({ ticketId }: { ticketId: number }) {
    const [options, setOptions] = useState<TicketOperationOptions | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [pendingOperation, setPendingOperation] = useState<OperationName | null>(null);
    const [error, setError] = useState<string | null>(null);

    const loadOptions = useCallback(async () => {
        try {
            setError(null);
            const payload = (await fetchAPI(
                AdminAPI.tickets.operations.options(ticketId),
            )) as TicketOperationOptions;
            setOptions(payload);
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load ticket workflow controls.",
            );
        } finally {
            setIsLoading(false);
        }
    }, [ticketId]);

    useEffect(() => {
        void loadOptions();
    }, [loadOptions]);

    async function updateOperation(
        operation: OperationName,
        payload: Record<string, string | number | null>,
    ) {
        if (pendingOperation) return;

        const endpoint = AdminAPI.tickets.operations[operation](ticketId);
        try {
            setPendingOperation(operation);
            setError(null);
            const ticket = (await fetchAPI(endpoint, {
                method: "POST",
                body: JSON.stringify(payload),
            })) as TicketMutable;
            setOptions((current) => (current ? { ...current, ticket } : current));

            const refreshed = (await fetchAPI(
                AdminAPI.tickets.operations.options(ticketId),
            )) as TicketOperationOptions;
            setOptions(refreshed);
            window.dispatchEvent(new Event("adb:ticket-updated"));
        } catch (updateError) {
            setError(
                updateError instanceof Error
                    ? updateError.message
                    : "Unable to update ticket workflow.",
            );
        } finally {
            setPendingOperation(null);
        }
    }

    if (isLoading) {
        return <DataLoading label="Loading ticket workflow controls..." />;
    }
    if (error && !options) {
        return <DataError message={error} onRetry={() => void loadOptions()} />;
    }
    if (!options) return null;

    const hasControls =
        options.can_assign ||
        options.can_change ||
        options.can_close ||
        options.statuses.length > 1;
    if (!hasControls) return null;

    const disabled = pendingOperation !== null;

    return (
        <Card className="p-4">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-end">
                <div className="min-w-48 xl:mr-auto">
                    <h2 className="text-sm font-semibold text-white">Ticket workflow</h2>
                    <p className="mt-1 text-xs text-slate-500">
                        Assignment, routing, priority and lifecycle controls.
                    </p>
                </div>

                {options.statuses.length > 1 ? (
                    <label className="min-w-44 text-xs text-slate-400">
                        Status
                        <Select
                            className="mt-1"
                            value={options.ticket.status}
                            disabled={disabled}
                            onChange={(event) =>
                                void updateOperation("status", {
                                    status: event.target.value,
                                })
                            }
                        >
                            {options.statuses.map((status) => (
                                <option key={status.value} value={status.value}>
                                    {status.label}
                                </option>
                            ))}
                        </Select>
                    </label>
                ) : null}

                {options.can_change && options.priorities.length ? (
                    <label className="min-w-36 text-xs text-slate-400">
                        Priority
                        <Select
                            className="mt-1"
                            value={options.ticket.priority}
                            disabled={disabled}
                            onChange={(event) =>
                                void updateOperation("priority", {
                                    priority: event.target.value,
                                })
                            }
                        >
                            {options.priorities.map((priority) => (
                                <option key={priority.value} value={priority.value}>
                                    {priority.label}
                                </option>
                            ))}
                        </Select>
                    </label>
                ) : null}

                {options.can_change && options.queues.length ? (
                    <label className="min-w-52 text-xs text-slate-400">
                        Queue
                        <Select
                            className="mt-1"
                            value={String(options.ticket.queue_id)}
                            disabled={disabled}
                            onChange={(event) =>
                                void updateOperation("queue", {
                                    queue_id: Number(event.target.value),
                                })
                            }
                        >
                            {options.queues.map((queue) => (
                                <option key={queue.id} value={queue.id}>
                                    {queue.name}
                                </option>
                            ))}
                        </Select>
                    </label>
                ) : null}

                {options.can_assign ? (
                    <label className="min-w-52 text-xs text-slate-400">
                        Assigned to
                        <Select
                            className="mt-1"
                            value={options.ticket.assigned_to_id ?? ""}
                            disabled={disabled}
                            onChange={(event) =>
                                void updateOperation("assignment", {
                                    assigned_to_id: event.target.value || null,
                                })
                            }
                        >
                            <option value="">Unassigned</option>
                            {options.assignees.map((agent) => (
                                <option key={agent.id} value={agent.id}>
                                    {agent.name}
                                </option>
                            ))}
                        </Select>
                    </label>
                ) : null}
            </div>

            {pendingOperation ? (
                <p className="mt-3 text-xs text-cyan-300">Updating ticket workflow...</p>
            ) : null}
            {error ? <p className="mt-3 text-xs text-red-300">{error}</p> : null}
        </Card>
    );
}
