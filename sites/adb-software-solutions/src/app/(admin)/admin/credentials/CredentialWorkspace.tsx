"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";

import {
    Badge,
    Button,
    ButtonLink,
    Card,
    DataError,
    DataLoading,
    PageHeader,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import {
    copyCredentialSecret,
    CredentialDetail,
    CredentialField,
    CredentialVaultAPI,
    downloadCredentialSecret,
} from "@/lib/api/credentialVault";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { CredentialForm } from "./CredentialForm";

interface CredentialWorkspaceProps {
    credentialId: number;
    presentation?: "page" | "drawer";
    onChanged?: () => void;
}

function label(value: string): string {
    return `${value.charAt(0).toUpperCase()}${value.slice(1).replaceAll("_", " ")}`;
}

function dateTime(value: string | null): string {
    if (!value) return "—";
    return new Intl.DateTimeFormat("en-GB", {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(new Date(value));
}

function publicFieldValue(credential: CredentialDetail, field: CredentialField): string {
    if (field.storage === "username") return credential.username;
    if (field.storage === "url") return credential.url;
    if (field.storage === "metadata") return credential.metadata[field.key] ?? "";
    return "";
}

export function CredentialWorkspace({
    credentialId,
    presentation = "page",
    onChanged,
}: CredentialWorkspaceProps) {
    const { hasPermission } = useAuth();
    const canEdit = hasPermission("credentials.change_storedcredential");
    const canArchive = hasPermission("credentials.delete_storedcredential");
    const canReveal = hasPermission("credentials.reveal_storedcredential");
    const canCopy = hasPermission("credentials.copy_storedcredential_secret");
    const canDownload = hasPermission("credentials.download_storedcredential_secret");

    const [credential, setCredential] = useState<CredentialDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [revealed, setRevealed] = useState<Record<string, string>>({});
    const [secretAction, setSecretAction] = useState<string | null>(null);
    const [isRevealing, setIsRevealing] = useState(false);
    const [isMigrating, setIsMigrating] = useState(false);
    const [isArchiving, setIsArchiving] = useState(false);

    const load = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            setRevealed({});
            setCredential((await fetchAPI(CredentialVaultAPI.get(credentialId))) as CredentialDetail);
        } catch (loadError) {
            setError(loadError instanceof Error ? loadError.message : "Unable to load this credential.");
        } finally {
            setIsLoading(false);
        }
    }, [credentialId]);

    useLiveRefresh(["credentials"], async () => { if (!isEditing) await load(); });

    useEffect(() => {
        void load();
    }, [load]);

    useEffect(() => {
        setIsEditing(false);
        setRevealed({});
        setSecretAction(null);
    }, [credentialId]);

    const secretFields = useMemo(
        () => credential?.fields.filter((field) => field.storage === "secret") ?? [],
        [credential],
    );

    async function revealSecrets() {
        if (!credential) return;
        try {
            setIsRevealing(true);
            setSecretAction(null);
            const response = (await fetchAPI(CredentialVaultAPI.reveal(credential.id), {
                method: "POST",
                body: JSON.stringify({ fields: credential.secret_field_keys }),
            })) as { fields: Record<string, string> };
            setRevealed(response.fields);
        } catch (actionError) {
            setSecretAction(actionError instanceof Error ? actionError.message : "Unable to reveal credential secrets.");
        } finally {
            setIsRevealing(false);
        }
    }

    async function copySecret(fieldKey: string) {
        if (!credential) return;
        try {
            setSecretAction(null);
            await copyCredentialSecret(credential.id, fieldKey);
            setSecretAction(`${label(fieldKey)} copied to clipboard.`);
        } catch (actionError) {
            setSecretAction(actionError instanceof Error ? actionError.message : "Unable to copy credential secret.");
        }
    }

    async function downloadSecret(fieldKey: string) {
        if (!credential) return;
        try {
            setSecretAction(null);
            await downloadCredentialSecret(credential.id, fieldKey);
            setSecretAction(`${label(fieldKey)} download started.`);
        } catch (actionError) {
            setSecretAction(actionError instanceof Error ? actionError.message : "Unable to download credential secret.");
        }
    }

    async function migrateLegacy() {
        if (!credential) return;
        const confirmed = window.confirm(
            "Encrypt the legacy plaintext credential fields and permanently blank their old database columns?",
        );
        if (!confirmed) return;
        try {
            setIsMigrating(true);
            setSecretAction(null);
            const result = (await fetchAPI(CredentialVaultAPI.migrateLegacy(credential.id), {
                method: "POST",
            })) as { migrated_fields: string[] };
            setSecretAction(
                result.migrated_fields.length
                    ? `Encrypted legacy fields: ${result.migrated_fields.join(", ")}.`
                    : "No legacy plaintext fields remained to migrate.",
            );
            await load();
            onChanged?.();
        } catch (actionError) {
            setSecretAction(actionError instanceof Error ? actionError.message : "Unable to encrypt legacy credential data.");
        } finally {
            setIsMigrating(false);
        }
    }

    async function archiveCredential() {
        if (!credential) return;
        if (!window.confirm(`Archive ${credential.name}? It will leave the default active vault view.`)) return;
        try {
            setIsArchiving(true);
            setSecretAction(null);
            const archived = (await fetchAPI(CredentialVaultAPI.archive(credential.id), {
                method: "POST",
            })) as CredentialDetail;
            setCredential(archived);
            setRevealed({});
            onChanged?.();
        } catch (actionError) {
            setSecretAction(actionError instanceof Error ? actionError.message : "Unable to archive this credential.");
        } finally {
            setIsArchiving(false);
        }
    }

    if (isLoading && !credential) return <DataLoading label="Loading credential..." />;
    if (error || !credential) {
        return <DataError message={error || "Credential is unavailable."} onRetry={() => void load()} />;
    }

    if (isEditing) {
        return (
            <div className="space-y-5">
                <PageHeader
                    eyebrow="Credential Vault"
                    title={`Edit ${credential.name}`}
                    description="Secret inputs stay blank unless you are replacing an encrypted value."
                />
                <CredentialForm
                    credential={credential}
                    onCancel={() => setIsEditing(false)}
                    onSaved={(saved) => {
                        setCredential(saved);
                        setIsEditing(false);
                        setRevealed({});
                        onChanged?.();
                    }}
                />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <PageHeader
                eyebrow={credential.credential_type_name || "Credential"}
                title={credential.name}
                description={
                    credential.description ||
                    `${credential.client_name || "ADB Internal"} · ${label(credential.status)}`
                }
                actions={
                    <div className="flex flex-wrap gap-2">
                        {canEdit ? (
                            <Button type="button" variant="secondary" onClick={() => setIsEditing(true)}>
                                Edit
                            </Button>
                        ) : null}
                        {presentation === "page" ? (
                            <ButtonLink href="/admin/credentials" variant="ghost">
                                Back to vault
                            </ButtonLink>
                        ) : null}
                    </div>
                }
            />

            <div className="flex flex-wrap gap-2">
                <Badge>{credential.status}</Badge>
                <Badge>{credential.client_name || "ADB Internal"}</Badge>
                {credential.expires_at ? <Badge>Expires {dateTime(credential.expires_at)}</Badge> : null}
                {credential.has_legacy_plaintext ? (
                    <Badge className="border-amber-800 bg-amber-950/50 text-amber-200">Legacy plaintext detected</Badge>
                ) : null}
            </div>

            {credential.has_legacy_plaintext ? (
                <Card className="border-amber-900/70 bg-amber-950/25 p-5">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                            <h2 className="text-sm font-semibold text-amber-100">Legacy plaintext requires reconciliation</h2>
                            <p className="mt-1 max-w-3xl text-xs leading-5 text-amber-200/70">
                                This record predates the encrypted vault and still contains one or more values in legacy plaintext columns. The migration action encrypts those values into the vault payload and blanks the old columns atomically.
                            </p>
                        </div>
                        {canEdit ? (
                            <Button type="button" variant="secondary" disabled={isMigrating} onClick={() => void migrateLegacy()}>
                                {isMigrating ? "Encrypting..." : "Encrypt legacy values"}
                            </Button>
                        ) : null}
                    </div>
                </Card>
            ) : null}

            <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(18rem,1fr)]">
                <div className="space-y-6">
                    <Card className="p-5">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                                <h2 className="text-sm font-semibold text-white">Credential fields</h2>
                                <p className="mt-1 text-xs leading-5 text-slate-500">
                                    Reveals, clipboard copies and downloads are separate audited actions.
                                </p>
                            </div>
                            {credential.secret_field_keys.length > 0 && canReveal ? (
                                Object.keys(revealed).length > 0 ? (
                                    <Button type="button" variant="ghost" size="sm" onClick={() => setRevealed({})}>
                                        Hide secrets
                                    </Button>
                                ) : (
                                    <Button type="button" variant="secondary" size="sm" disabled={isRevealing} onClick={() => void revealSecrets()}>
                                        {isRevealing ? "Revealing..." : "Reveal secrets"}
                                    </Button>
                                )
                            ) : null}
                        </div>
                        <div className="mt-5 divide-y divide-slate-800">
                            {credential.fields.map((field) => {
                                const isSecret = field.storage === "secret";
                                const stored = credential.secret_field_keys.includes(field.key);
                                const revealedValue = revealed[field.key];
                                const publicValue = publicFieldValue(credential, field);
                                return (
                                    <div key={field.key} className="grid gap-3 py-4 sm:grid-cols-[11rem_minmax(0,1fr)_auto] sm:items-start">
                                        <div>
                                            <div className="text-xs font-medium text-slate-400">{field.label}</div>
                                            {isSecret ? <div className="mt-1 text-[11px] text-slate-600">Encrypted secret</div> : null}
                                        </div>
                                        <div className="min-w-0">
                                            {isSecret ? (
                                                revealedValue !== undefined ? (
                                                    <pre className="max-h-80 overflow-auto whitespace-pre-wrap break-all rounded-lg border border-slate-800 bg-slate-950 p-3 text-xs leading-5 text-slate-200">{revealedValue}</pre>
                                                ) : (
                                                    <span className={stored ? "font-mono text-sm text-slate-400" : "text-sm text-slate-600"}>
                                                        {stored ? "••••••••••••" : "Not stored"}
                                                    </span>
                                                )
                                            ) : field.kind === "url" && publicValue ? (
                                                <a href={publicValue} target="_blank" rel="noreferrer" className="break-all text-sm text-adb-cyan-300 hover:underline">{publicValue}</a>
                                            ) : (
                                                <span className="whitespace-pre-wrap break-all text-sm text-slate-300">{publicValue || "—"}</span>
                                            )}
                                        </div>
                                        {isSecret && stored ? (
                                            <div className="flex flex-wrap gap-1">
                                                {canCopy ? (
                                                    <Button type="button" variant="ghost" size="sm" onClick={() => void copySecret(field.key)}>Copy</Button>
                                                ) : null}
                                                {canDownload ? (
                                                    <Button type="button" variant="ghost" size="sm" onClick={() => void downloadSecret(field.key)}>Download</Button>
                                                ) : null}
                                            </div>
                                        ) : null}
                                    </div>
                                );
                            })}
                        </div>
                        {secretFields.length === 0 ? (
                            <p className="mt-4 text-sm text-slate-500">This credential template has no encrypted fields.</p>
                        ) : null}
                    </Card>

                    <Card className="p-5">
                        <div>
                            <h2 className="text-sm font-semibold text-white">Linked infrastructure</h2>
                            <p className="mt-1 text-xs leading-5 text-slate-500">Resources that use or depend on this credential.</p>
                        </div>
                        {credential.resource_links.length === 0 ? (
                            <p className="mt-4 text-sm text-slate-500">No infrastructure resources are linked.</p>
                        ) : (
                            <div className="mt-4 divide-y divide-slate-800">
                                {credential.resource_links.map((link) => (
                                    <div key={link.id} className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between">
                                        <div>
                                            <Link href={`/admin/infrastructure/resources/${link.resource_id}`} className="font-medium text-slate-200 hover:text-adb-cyan-300">
                                                {link.resource_name}
                                            </Link>
                                            <div className="mt-1 text-xs text-slate-500">
                                                {label(link.resource_type)} · {link.client_name || "ADB Internal"}
                                                {link.purpose ? ` · ${link.purpose}` : ""}
                                            </div>
                                        </div>
                                        {link.is_primary ? <Badge>Primary</Badge> : null}
                                    </div>
                                ))}
                            </div>
                        )}
                    </Card>
                </div>

                <div className="space-y-6">
                    <Card className="p-5">
                        <h2 className="text-sm font-semibold text-white">Vault metadata</h2>
                        <dl className="mt-4 space-y-4 text-sm">
                            <div><dt className="text-xs text-slate-500">Ownership</dt><dd className="mt-1 text-slate-300">{credential.client_name || "ADB Internal"}</dd></div>
                            <div><dt className="text-xs text-slate-500">Type</dt><dd className="mt-1 text-slate-300">{credential.credential_type_name || "Unclassified"}</dd></div>
                            <div><dt className="text-xs text-slate-500">Last rotated</dt><dd className="mt-1 text-slate-300">{dateTime(credential.last_rotated_at)}</dd></div>
                            <div><dt className="text-xs text-slate-500">Created</dt><dd className="mt-1 text-slate-300">{dateTime(credential.created_at)}</dd></div>
                            <div><dt className="text-xs text-slate-500">Created by</dt><dd className="mt-1 break-all text-slate-300">{credential.created_by || "—"}</dd></div>
                            <div><dt className="text-xs text-slate-500">Updated</dt><dd className="mt-1 text-slate-300">{dateTime(credential.updated_at)}</dd></div>
                            <div><dt className="text-xs text-slate-500">Updated by</dt><dd className="mt-1 break-all text-slate-300">{credential.updated_by || "—"}</dd></div>
                        </dl>
                    </Card>

                    {canArchive && credential.status !== "archived" ? (
                        <Card className="p-5">
                            <h2 className="text-sm font-semibold text-white">Lifecycle</h2>
                            <p className="mt-2 text-xs leading-5 text-slate-500">Archived credentials leave the default active vault without deleting audit history.</p>
                            <Button type="button" className="mt-4" variant="destructive" size="sm" disabled={isArchiving} onClick={() => void archiveCredential()}>
                                {isArchiving ? "Archiving..." : "Archive credential"}
                            </Button>
                        </Card>
                    ) : null}
                </div>
            </div>

            {secretAction ? (
                <div className="rounded-lg border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-slate-300">{secretAction}</div>
            ) : null}
        </div>
    );
}
