"use client";
import {useState} from "react";
import {UsersIcon, ShieldCheckIcon} from "@heroicons/react/24/outline";
import {api, type Business} from "../../app/client";
import {useResource} from "../experience/useResource";
import {CreateBusiness} from "./WorkspaceForms";
export function WorkspaceSettings({
    business,
    refresh,
}: {
    business: Business;
    refresh: () => Promise<void>;
}) {
    const {
        data: members,
        error: loadError,
        reload,
    } = useResource<{email: string; role: string}[]>(
        business.role === "owner" ? `/businesses/${business.id}/members` : null,
    );
    const [error, setError] = useState(""),
        [message, setMessage] = useState(""),
        [busy, setBusy] = useState(false);
    return (
        <div className="settings-sections">
            {(error || loadError) && (
                <p className="error-state" role="alert">
                    {error || loadError}
                </p>
            )}
            {message && (
                <p className="data-notice" role="status">
                    {message}
                </p>
            )}
            <section className="settings-card">
                <div className="settings-card-title">
                    <span className="settings-symbol">
                        <ShieldCheckIcon />
                    </span>
                    <div>
                        <h2>{business.name}</h2>
                        <p>
                            Your role: <strong>{business.role}</strong>.
                            Workspace membership grants access only to this
                            business’s analytics.
                        </p>
                    </div>
                </div>
                {business.role === "owner" ? (
                    <form
                        className="settings-inline-form"
                        onSubmit={async (event) => {
                            event.preventDefault();
                            const name = new FormData(event.currentTarget).get(
                                "name",
                            );
                            setBusy(true);
                            setError("");
                            try {
                                await api(`/businesses/${business.id}`, "PUT", {
                                    name,
                                });
                                await refresh();
                                setMessage("Workspace details saved.");
                            } catch (err) {
                                setError(String(err));
                            } finally {
                                setBusy(false);
                            }
                        }}
                    >
                        <label>
                            Workspace name
                            <input
                                name="name"
                                required
                                maxLength={255}
                                defaultValue={business.name}
                            />
                        </label>
                        <button className="button" disabled={busy}>
                            Save changes
                        </button>
                    </form>
                ) : (
                    <p>
                        The workspace owner manages business details and
                        membership.
                    </p>
                )}
            </section>
            <section className="settings-card">
                <div className="settings-card-title">
                    <span className="settings-symbol">
                        <UsersIcon />
                    </span>
                    <div>
                        <h2>People & access</h2>
                        <p>
                            Give each person the access they need. The final
                            owner cannot be removed.
                        </p>
                    </div>
                </div>
                <div className="role-explanations">
                    <div>
                        <strong>Viewer</strong>
                        <span>Read reports and explore evidence.</span>
                    </div>
                    <div>
                        <strong>Admin</strong>
                        <span>
                            Manage websites, connections and confirmed Google
                            configuration.
                        </span>
                    </div>
                    <div>
                        <strong>Owner</strong>
                        <span>
                            All admin actions, plus business details and access
                            management.
                        </span>
                    </div>
                </div>
                {members?.map((member) => (
                    <div className="member-row" key={member.email}>
                        <span className="account-initial">
                            {member.email.slice(0, 1).toUpperCase()}
                        </span>
                        <span>{member.email}</span>
                        <span className="health-pill">{member.role}</span>
                    </div>
                ))}
                {business.role === "owner" && (
                    <details className="settings-disclosure">
                        <summary>Add a member or change access</summary>
                        <p>
                            Use an existing ADB account email. Removing
                            membership removes access to this workspace, without
                            deleting the person’s account.
                        </p>
                        <form
                            className="settings-member-form"
                            onSubmit={async (event) => {
                                event.preventDefault();
                                const form = new FormData(event.currentTarget);
                                const role = form.get("role");
                                if (
                                    !window.confirm(
                                        `Apply ${role || "removal of"} access for ${form.get("email")}?`,
                                    )
                                )
                                    return;
                                setBusy(true);
                                setError("");
                                try {
                                    await api(
                                        `/businesses/${business.id}/members`,
                                        "PUT",
                                        {
                                            email: form.get("email"),
                                            role: role || null,
                                        },
                                    );
                                    reload();
                                    await refresh();
                                    setMessage("Workspace access updated.");
                                } catch (err) {
                                    setError(String(err));
                                } finally {
                                    setBusy(false);
                                }
                            }}
                        >
                            <label>
                                Account email
                                <input type="email" name="email" required />
                            </label>
                            <label>
                                Role
                                <select name="role">
                                    <option value="viewer">Viewer</option>
                                    <option value="admin">Admin</option>
                                    <option value="owner">Owner</option>
                                    <option value="">Remove membership</option>
                                </select>
                            </label>
                            <button className="button" disabled={busy}>
                                Review access change
                            </button>
                        </form>
                    </details>
                )}
            </section>
            {business.role === "owner" && (
                <details className="settings-card settings-disclosure">
                    <summary>Create another workspace</summary>
                    <p>
                        Keep a separate portfolio and membership list for
                        another business.
                    </p>
                    <div className="advanced-tools">
                        <CreateBusiness refresh={refresh} />
                    </div>
                </details>
            )}
        </div>
    );
}
