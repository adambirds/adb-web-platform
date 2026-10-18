"use client";
import {useCallback, useEffect, useState} from "react";
import {api, type Business, type Website} from "../../app/client";
import {CreateBusiness, WebsiteForm} from "./WorkspaceForms";
export function WorkspaceSettings({
    business,
    website,
    refresh,
}: {
    business: Business;
    website: Website;
    refresh: () => Promise<void>;
}) {
    const [members, setMembers] = useState<{email: string; role: string}[]>([]);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const load = useCallback(async () => {
        if (business.role === "owner")
            setMembers(await api(`/businesses/${business.id}/members`));
    }, [business.id, business.role]);
    useEffect(() => {
        void load().catch((err) => setError(String(err)));
    }, [load]);
    return (
        <>
            {error && (
                <p className="notice error" role="alert">
                    {error}
                </p>
            )}
            {message && <p role="status">{message}</p>}
            {business.role === "owner" && (
                <section className="panel">
                    <h2>Business details</h2>
                    <form
                        onSubmit={async (e) => {
                            e.preventDefault();
                            try {
                                await api(`/businesses/${business.id}`, "PUT", {
                                    name: new FormData(e.currentTarget).get(
                                        "name",
                                    ),
                                });
                                await refresh();
                            } catch (err) {
                                setError(String(err));
                            }
                        }}
                    >
                        <label>
                            Name
                            <input
                                name="name"
                                defaultValue={business.name}
                                required
                            />
                        </label>
                        <button>Save business</button>
                    </form>
                    <h3>Members</h3>
                    {members.map((m) => (
                        <p key={m.email}>
                            {m.email} · {m.role}
                        </p>
                    ))}
                    <p>
                        Add an existing ADB account by email, change a role, or
                        remove access. The final owner cannot be removed.
                    </p>
                    <form
                        onSubmit={async (e) => {
                            e.preventDefault();
                            const form = new FormData(e.currentTarget);
                            try {
                                await api(
                                    `/businesses/${business.id}/members`,
                                    "PUT",
                                    {
                                        email: form.get("email"),
                                        role: form.get("role") || null,
                                    },
                                );
                                await load();
                                setMessage("Membership updated.");
                                await refresh();
                            } catch (err) {
                                setError(String(err));
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
                        <button>Update membership</button>
                    </form>
                </section>
            )}
            <section className="panel">
                <h2>Website settings</h2>
                <WebsiteForm
                    business={business}
                    website={website}
                    refresh={refresh}
                />
            </section>
            <section className="panel">
                <h2>Add another website</h2>
                <WebsiteForm business={business} refresh={refresh} />
            </section>
            <section className="panel">
                <h2>Create another business</h2>
                <CreateBusiness refresh={refresh} />
            </section>
        </>
    );
}
