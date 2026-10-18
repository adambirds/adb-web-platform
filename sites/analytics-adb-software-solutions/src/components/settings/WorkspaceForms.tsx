"use client";
import {useState} from "react";
import {api, type Business, type Website} from "../../app/client";
export function CreateBusiness({refresh}: {refresh: () => Promise<void>}) {
    const [error, setError] = useState("");
    return (
        <form
            onSubmit={async (e) => {
                e.preventDefault();
                const data = new FormData(e.currentTarget);
                try {
                    await api("/businesses", "POST", {name: data.get("name")});
                    await refresh();
                } catch (err) {
                    setError(String(err));
                }
            }}
        >
            <label>
                Business name
                <input name="name" required maxLength={255} />
            </label>
            <button className="primary">Create business</button>
            {error && <p role="alert">{error}</p>}
        </form>
    );
}

export function WebsiteForm({
    business,
    website,
    refresh,
}: {
    business: Business;
    website?: Website;
    refresh: () => Promise<void>;
}) {
    const [error, setError] = useState("");
    return (
        <form
            onSubmit={async (e) => {
                e.preventDefault();
                const data = new FormData(e.currentTarget);
                try {
                    await api(
                        website
                            ? `/websites/${website.id}`
                            : `/businesses/${business.id}/websites`,
                        website ? "PUT" : "POST",
                        {
                            name: data.get("name"),
                            domain: data.get("domain"),
                            timezone:
                                website?.timezone ??
                                Intl.DateTimeFormat().resolvedOptions()
                                    .timeZone,
                            is_active: data.get("active") === "on",
                        },
                    );
                    await refresh();
                } catch (err) {
                    setError(String(err));
                }
            }}
        >
            <label>
                Website name
                <input
                    name="name"
                    defaultValue={website?.name}
                    required
                    maxLength={255}
                />
            </label>
            <label>
                Domain
                <input
                    name="domain"
                    defaultValue={website?.domain}
                    placeholder="example.co.uk"
                    required
                />
            </label>
            <p className="muted">
                <small>
                    Timezone is detected from the linked Google Analytics
                    property{website ? ` · ${website.timezone}` : ""}.
                </small>
            </p>
            <label className="check">
                <input
                    type="checkbox"
                    name="active"
                    defaultChecked={website?.is_active ?? true}
                />
                Active
            </label>
            <button className="primary">
                {website ? "Save website" : "Add website"}
            </button>
            {error && <p role="alert">{error}</p>}
        </form>
    );
}
