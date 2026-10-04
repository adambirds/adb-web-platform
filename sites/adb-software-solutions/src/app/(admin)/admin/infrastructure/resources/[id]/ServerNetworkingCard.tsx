"use client";

import {
    Button,
    Card,
    DataError,
    DataLoading,
    Input,
    Select,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import { useCallback, useEffect, useState, type FormEvent } from "react";

interface IP {
    id: number;
    address: string;
    scope: string;
    interface_id: number | null;
    ptr_record: string;
    is_primary: boolean;
    description: string;
}
interface Interface {
    id: number;
    name: string;
    mac_address: string;
    network_resource_id: number | null;
    subnet_resource_id: number | null;
    mtu: number | null;
    description: string;
    network_name: string | null;
    subnet_name: string | null;
    ip_addresses: IP[];
}
interface Server {
    interfaces: Interface[];
    direct_ip_addresses: IP[];
}
interface Options {
    networks: { resource_id: number; name: string }[];
    subnets: {
        resource_id: number;
        network_resource_id: number;
        cidr: string;
    }[];
}

export function ServerNetworkingCard({
    resourceId,
    onChanged,
}: {
    resourceId: number;
    onChanged: () => void;
}) {
    const { hasPermission } = useAuth();
    const canView =
        hasPermission("infrastructure.view_serverprofile") &&
        hasPermission("infrastructure.view_infrastructureresource");
    const [server, setServer] = useState<Server | null>(null);
    const [options, setOptions] = useState<Options>({
        networks: [],
        subnets: [],
    });
    const [error, setError] = useState<string | null>(null);
    const [saving, setSaving] = useState(false);
    const [form, setForm] = useState<"interface" | "ip" | null>(null);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [name, setName] = useState("");
    const [mac, setMac] = useState("");
    const [network, setNetwork] = useState("");
    const [subnet, setSubnet] = useState("");
    const [mtu, setMtu] = useState("");
    const [description, setDescription] = useState("");
    const [address, setAddress] = useState("");
    const [scope, setScope] = useState("private");
    const [interfaceId, setInterfaceId] = useState("");
    const [ptr, setPtr] = useState("");
    const [primary, setPrimary] = useState(false);
    const load = useCallback(async () => {
        if (!canView) return;
        try {
            setError(null);
            const [detail, choices] = await Promise.all([
                fetchAPI(
                    `${API_URL}/api/admin/infrastructure/servers/${resourceId}`,
                ) as Promise<Server>,
                fetchAPI(
                    `${API_URL}/api/admin/infrastructure/specialist-options`,
                ) as Promise<Options>,
            ]);
            setServer(detail);
            setOptions(choices);
        } catch (failure) {
            setError(
                failure instanceof Error
                    ? failure.message
                    : "Unable to load server networking.",
            );
        }
    }, [canView, resourceId]);
    useEffect(() => {
        void load();
    }, [load]);
    function resetForm(kind: "interface" | "ip" | null) {
        setForm(kind);
        setEditingId(null);
        setError(null);
        setName("");
        setMac("");
        setNetwork("");
        setSubnet("");
        setMtu("");
        setDescription("");
        setAddress("");
        setScope("private");
        setInterfaceId("");
        setPtr("");
        setPrimary(false);
    }
    function editInterface(item: Interface) {
        resetForm("interface");
        setEditingId(item.id);
        setName(item.name);
        setMac(item.mac_address);
        setNetwork(
            item.network_resource_id == null
                ? ""
                : String(item.network_resource_id),
        );
        setSubnet(
            item.subnet_resource_id == null
                ? ""
                : String(item.subnet_resource_id),
        );
        setMtu(item.mtu == null ? "" : String(item.mtu));
        setDescription(item.description);
    }
    function editIP(ip: IP) {
        resetForm("ip");
        setEditingId(ip.id);
        setAddress(ip.address);
        setScope(ip.scope);
        setInterfaceId(ip.interface_id == null ? "" : String(ip.interface_id));
        setPtr(ip.ptr_record);
        setPrimary(ip.is_primary);
        setDescription(ip.description);
    }
    function ipRow(ip: IP) {
        return (
            <div
                key={ip.id}
                className="flex items-center justify-between gap-2"
            >
                <p>
                    {ip.address} · {ip.scope}
                </p>
                {hasPermission("infrastructure.change_ipaddress") ? (
                    <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        disabled={saving}
                        aria-label={`Edit IP ${ip.address}`}
                        onClick={() => editIP(ip)}
                    >
                        Edit
                    </Button>
                ) : null}
            </div>
        );
    }
    async function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setSaving(true);
        setError(null);
        try {
            await fetchAPI(
                `${API_URL}/api/admin/infrastructure/servers/${resourceId}/${form === "interface" ? "interfaces" : "ip-addresses"}${editingId === null ? "" : `/${editingId}`}`,
                {
                    method: editingId === null ? "POST" : "PUT",
                    body: JSON.stringify(
                        form === "interface"
                            ? {
                                  name,
                                  mac_address: mac,
                                  network_resource_id: network
                                      ? Number(network)
                                      : null,
                                  subnet_resource_id: subnet
                                      ? Number(subnet)
                                      : null,
                                  mtu: mtu ? Number(mtu) : null,
                                  description,
                              }
                            : {
                                  address,
                                  scope,
                                  interface_id: interfaceId
                                      ? Number(interfaceId)
                                      : null,
                                  ptr_record: ptr,
                                  is_primary: primary,
                                  description,
                              },
                    ),
                },
            );
            setForm(null);
            setName("");
            setMac("");
            setNetwork("");
            setSubnet("");
            setMtu("");
            setDescription("");
            setAddress("");
            setInterfaceId("");
            setPtr("");
            setPrimary(false);
            await load();
            onChanged();
        } catch (failure) {
            setError(
                failure instanceof Error
                    ? failure.message
                    : "Unable to create network record.",
            );
        } finally {
            setSaving(false);
        }
    }
    if (!canView) return null;
    return (
        <Card className="space-y-4 p-5">
            <div className="flex flex-wrap justify-between gap-3">
                <h2 className="font-semibold text-white">
                    Interfaces and IP addresses
                </h2>
                <div className="flex gap-2">
                    {hasPermission("infrastructure.add_networkinterface") ? (
                        <Button
                            type="button"
                            variant="secondary"
                            onClick={() => {
                                resetForm("interface");
                            }}
                        >
                            Add interface
                        </Button>
                    ) : null}
                    {hasPermission("infrastructure.add_ipaddress") ? (
                        <Button
                            type="button"
                            variant="secondary"
                            onClick={() => {
                                resetForm("ip");
                            }}
                        >
                            Add IP address
                        </Button>
                    ) : null}
                </div>
            </div>
            {error ? (
                <DataError message={error} onRetry={() => void load()} />
            ) : null}
            {!server && !error ? (
                <DataLoading label="Loading interfaces and IP addresses..." />
            ) : null}
            {server ? (
                <div className="space-y-2 text-sm text-slate-400">
                    {server.interfaces.map((item) => (
                        <div
                            key={item.id}
                            className="rounded border border-slate-800 p-3"
                        >
                            <p className="text-slate-100">
                                {item.name} ·{" "}
                                {item.mac_address || "No MAC recorded"}
                            </p>
                            <p>
                                {[item.network_name, item.subnet_name]
                                    .filter(Boolean)
                                    .join(" · ")}
                            </p>
                            {hasPermission(
                                "infrastructure.change_networkinterface",
                            ) ? (
                                <Button
                                    type="button"
                                    size="sm"
                                    variant="secondary"
                                    disabled={saving}
                                    aria-label={`Edit interface ${item.name}`}
                                    onClick={() => editInterface(item)}
                                >
                                    Edit interface
                                </Button>
                            ) : null}
                            {item.ip_addresses.map(ipRow)}
                        </div>
                    ))}
                    {server.direct_ip_addresses.map(ipRow)}
                    {!server.interfaces.length &&
                    !server.direct_ip_addresses.length ? (
                        <p>No network records yet.</p>
                    ) : null}
                </div>
            ) : null}
            {form ? (
                <form
                    onSubmit={(event) => void submit(event)}
                    className="space-y-4"
                >
                    <fieldset
                        disabled={saving}
                        className="grid gap-3 sm:grid-cols-2"
                    >
                        {form === "interface" ? (
                            <>
                                <label>
                                    Interface name
                                    <Input
                                        required
                                        value={name}
                                        onChange={(e) =>
                                            setName(e.target.value)
                                        }
                                    />
                                </label>
                                <label>
                                    MAC address
                                    <Input
                                        value={mac}
                                        onChange={(e) => setMac(e.target.value)}
                                    />
                                </label>
                                <label>
                                    Network
                                    <Select
                                        value={network}
                                        onChange={(e) => {
                                            setNetwork(e.target.value);
                                            setSubnet("");
                                        }}
                                    >
                                        <option value="">No network</option>
                                        {options.networks.map((item) => (
                                            <option
                                                key={item.resource_id}
                                                value={item.resource_id}
                                            >
                                                {item.name}
                                            </option>
                                        ))}
                                    </Select>
                                </label>
                                <label>
                                    Subnet
                                    <Select
                                        value={subnet}
                                        onChange={(e) =>
                                            setSubnet(e.target.value)
                                        }
                                    >
                                        <option value="">No subnet</option>
                                        {options.subnets
                                            .filter(
                                                (item) =>
                                                    !network ||
                                                    item.network_resource_id ===
                                                        Number(network),
                                            )
                                            .map((item) => (
                                                <option
                                                    key={item.resource_id}
                                                    value={item.resource_id}
                                                >
                                                    {item.cidr}
                                                </option>
                                            ))}
                                    </Select>
                                </label>
                                <label>
                                    MTU
                                    <Input
                                        type="number"
                                        min={1}
                                        value={mtu}
                                        onChange={(e) => setMtu(e.target.value)}
                                    />
                                </label>
                            </>
                        ) : (
                            <>
                                <label>
                                    IP address
                                    <Input
                                        required
                                        value={address}
                                        onChange={(e) =>
                                            setAddress(e.target.value)
                                        }
                                    />
                                </label>
                                <label>
                                    Address scope
                                    <Select
                                        value={scope}
                                        onChange={(e) =>
                                            setScope(e.target.value)
                                        }
                                    >
                                        {[
                                            "public",
                                            "private",
                                            "floating",
                                            "virtual",
                                            "loopback",
                                            "other",
                                        ].map((value) => (
                                            <option key={value} value={value}>
                                                {value}
                                            </option>
                                        ))}
                                    </Select>
                                </label>
                                <label>
                                    Interface
                                    <Select
                                        value={interfaceId}
                                        onChange={(e) =>
                                            setInterfaceId(e.target.value)
                                        }
                                    >
                                        <option value="">
                                            Directly on server
                                        </option>
                                        {server?.interfaces.map((item) => (
                                            <option
                                                key={item.id}
                                                value={item.id}
                                            >
                                                {item.name}
                                            </option>
                                        ))}
                                    </Select>
                                </label>
                                <label>
                                    PTR record
                                    <Input
                                        value={ptr}
                                        onChange={(e) => setPtr(e.target.value)}
                                    />
                                </label>
                                <label>
                                    <input
                                        type="checkbox"
                                        checked={primary}
                                        onChange={(e) =>
                                            setPrimary(e.target.checked)
                                        }
                                    />{" "}
                                    Primary address
                                </label>
                            </>
                        )}
                        <label>
                            Network record description
                            <Input
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                            />
                        </label>
                    </fieldset>
                    <div className="flex gap-2">
                        <Button type="submit" disabled={saving}>
                            {saving
                                ? "Saving…"
                                : editingId !== null
                                  ? "Save network record"
                                  : form === "interface"
                                    ? "Create interface"
                                    : "Create IP address"}
                        </Button>
                        <Button
                            type="button"
                            variant="secondary"
                            disabled={saving}
                            onClick={() => setForm(null)}
                        >
                            Cancel
                        </Button>
                    </div>
                </form>
            ) : null}
        </Card>
    );
}
