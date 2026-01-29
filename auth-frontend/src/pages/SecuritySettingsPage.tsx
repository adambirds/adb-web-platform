import Alert from "@/components/Alert";
import {useAuth} from "@/contexts/AuthContext";
import {authApi, Session} from "@/utils/api";
import {getDefaultAppUrl, getRedirectUrl} from "@/utils/config";
import {createPasskey, isWebAuthnSupported} from "@/utils/webauthn";
import {
    ComputerDesktopIcon,
    DevicePhoneMobileIcon,
    DeviceTabletIcon,
    FingerPrintIcon,
    KeyIcon,
    ShieldCheckIcon,
    TrashIcon,
} from "@heroicons/react/24/outline";
import {useEffect, useState} from "react";

interface Passkey {
    id: string;
    name: string;
    deviceType: string;
    createdAt: string;
    lastUsedAt: string | null;
    backedUp: boolean;
}

export default function SecuritySettingsPage() {
    useAuth(); // Ensure user is authenticated
    const [activeSection, setActiveSection] = useState<
        "passkeys" | "2fa" | "password" | "sessions"
    >("passkeys");

    // Passkey state
    const [passkeys, setPasskeys] = useState<Passkey[]>([]);
    const [isLoadingPasskeys, setIsLoadingPasskeys] = useState(true);
    const [passkeyName, setPasskeyName] = useState("");
    const [isRegistering, setIsRegistering] = useState(false);
    const [passkeyError, setPasskeyError] = useState<string | null>(null);
    const [passkeySuccess, setPasskeySuccess] = useState<string | null>(null);

    // 2FA state
    const [has2fa, setHas2fa] = useState(false);
    const [twoFaError, setTwoFaError] = useState<string | null>(null);

    // Password state
    const [currentPassword, setCurrentPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [isChangingPassword, setIsChangingPassword] = useState(false);
    const [passwordError, setPasswordError] = useState<string | null>(null);
    const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);

    // Session state
    const [sessions, setSessions] = useState<Session[]>([]);
    const [isLoadingSessions, setIsLoadingSessions] = useState(true);
    const [sessionError, setSessionError] = useState<string | null>(null);
    const [sessionSuccess, setSessionSuccess] = useState<string | null>(null);
    const [isRevokingAll, setIsRevokingAll] = useState(false);

    const supportsPasskey = isWebAuthnSupported();

    // Load passkeys
    useEffect(() => {
        const loadPasskeys = async () => {
            try {
                const data = await authApi.getPasskeys();
                if (data.success && data.passkeys) {
                    setPasskeys(data.passkeys);
                }
            } catch {
                setPasskeyError("Failed to load passkeys");
            } finally {
                setIsLoadingPasskeys(false);
            }
        };
        loadPasskeys();
    }, []);

    // Load 2FA status
    useEffect(() => {
        const load2faStatus = async () => {
            try {
                const data = await authApi.get2FAStatus();
                if (data.success) {
                    setHas2fa(data.enabled);
                }
            } catch {
                setTwoFaError("Failed to load 2FA status");
            }
        };
        load2faStatus();
    }, []);

    // Load sessions
    useEffect(() => {
        const loadSessions = async () => {
            try {
                const data = await authApi.getSessions();
                if (data.success && data.sessions) {
                    setSessions(data.sessions);
                }
            } catch {
                setSessionError("Failed to load sessions");
            } finally {
                setIsLoadingSessions(false);
            }
        };
        loadSessions();
    }, []);

    const handleAddPasskey = async () => {
        if (!passkeyName.trim()) {
            setPasskeyError("Please enter a name for your passkey");
            return;
        }

        setIsRegistering(true);
        setPasskeyError(null);
        setPasskeySuccess(null);

        try {
            const beginData = await authApi.beginPasskeyRegistration(
                passkeyName.trim(),
            );
            if (!beginData.success || !beginData.options) {
                throw new Error(
                    beginData.message || "Failed to start registration",
                );
            }

            let options = beginData.options;
            if (typeof options === "string") {
                options = JSON.parse(options);
            }
            const credential = await createPasskey(options);

            const completeData =
                await authApi.completePasskeyRegistration(credential);
            if (!completeData.success) {
                throw new Error(
                    completeData.message || "Failed to register passkey",
                );
            }

            setPasskeySuccess("Passkey added successfully!");
            setPasskeyName("");
            // Reload passkeys
            const data = await authApi.getPasskeys();
            if (data.success && data.passkeys) {
                setPasskeys(data.passkeys);
            }
        } catch (err: unknown) {
            if (err instanceof Error && err.name !== "NotAllowedError") {
                setPasskeyError(err.message || "Failed to add passkey");
            }
        } finally {
            setIsRegistering(false);
        }
    };

    const handleDeletePasskey = async (passkeyId: string) => {
        if (!confirm("Are you sure you want to delete this passkey?")) {
            return;
        }

        try {
            const data = await authApi.deletePasskey(passkeyId);
            if (data.success) {
                setPasskeys(passkeys.filter((p) => p.id !== passkeyId));
                setPasskeySuccess("Passkey deleted");
            } else {
                throw new Error(data.message || "Failed to delete passkey");
            }
        } catch (err: unknown) {
            if (err instanceof Error) {
                setPasskeyError(err.message);
            }
        }
    };

    const handleChangePassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setPasswordError(null);
        setPasswordSuccess(null);

        if (newPassword !== confirmPassword) {
            setPasswordError("Passwords do not match");
            return;
        }

        if (newPassword.length < 12) {
            setPasswordError("Password must be at least 12 characters");
            return;
        }

        setIsChangingPassword(true);

        try {
            const data = await authApi.changePassword(
                currentPassword,
                newPassword,
            );
            if (data.success) {
                setPasswordSuccess("Password changed successfully");
                setCurrentPassword("");
                setNewPassword("");
                setConfirmPassword("");
            } else {
                throw new Error(data.message || "Failed to change password");
            }
        } catch (err: unknown) {
            if (err instanceof Error) {
                setPasswordError(err.message);
            }
        } finally {
            setIsChangingPassword(false);
        }
    };

    const handleRevokeSession = async (sessionId: string) => {
        if (!confirm("Are you sure you want to log out this device?")) {
            return;
        }

        setSessionError(null);
        setSessionSuccess(null);

        try {
            const data = await authApi.revokeSession(sessionId);
            if (data.success) {
                setSessions(sessions.filter((s) => s.id !== sessionId));
                setSessionSuccess("Device logged out successfully");
            } else {
                throw new Error(data.message || "Failed to log out device");
            }
        } catch (err: unknown) {
            if (err instanceof Error) {
                setSessionError(err.message);
            }
        }
    };

    const handleRevokeAllSessions = async () => {
        if (
            !confirm(
                "Are you sure you want to log out all other devices? This will end all sessions except your current one.",
            )
        ) {
            return;
        }

        setIsRevokingAll(true);
        setSessionError(null);
        setSessionSuccess(null);

        try {
            const data = await authApi.revokeAllSessions();
            if (data.success) {
                // Keep only the current session
                setSessions(sessions.filter((s) => s.is_current));
                setSessionSuccess(
                    `Logged out ${data.revoked_count || 0} device(s) successfully`,
                );
            } else {
                throw new Error(data.message || "Failed to log out devices");
            }
        } catch (err: unknown) {
            if (err instanceof Error) {
                setSessionError(err.message);
            }
        } finally {
            setIsRevokingAll(false);
        }
    };

    const getDeviceIcon = (deviceType: string) => {
        switch (deviceType) {
            case "mobile":
                return <DevicePhoneMobileIcon className="h-6 w-6" />;
            case "tablet":
                return <DeviceTabletIcon className="h-6 w-6" />;
            default:
                return <ComputerDesktopIcon className="h-6 w-6" />;
        }
    };

    const formatLastActivity = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return "Just now";
        if (diffMins < 60)
            return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`;
        if (diffHours < 24)
            return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
        if (diffDays < 7)
            return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
        return date.toLocaleDateString();
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Security Settings
                </h1>
                <a
                    href={getRedirectUrl() || getDefaultAppUrl()}
                    className="text-brand text-sm hover:underline"
                >
                    ← Back to app
                </a>
            </div>

            {/* Navigation tabs */}
            <div className="border-b border-slate-200 dark:border-slate-700">
                <nav className="-mb-px flex space-x-8">
                    <button
                        onClick={() => setActiveSection("passkeys")}
                        className={`border-b-2 px-1 py-4 text-sm font-medium ${
                            activeSection === "passkeys"
                                ? "border-brand text-brand"
                                : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700"
                        }`}
                    >
                        <FingerPrintIcon className="mr-2 inline h-5 w-5" />
                        Passkeys
                    </button>
                    <button
                        onClick={() => setActiveSection("2fa")}
                        className={`border-b-2 px-1 py-4 text-sm font-medium ${
                            activeSection === "2fa"
                                ? "border-brand text-brand"
                                : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700"
                        }`}
                    >
                        <ShieldCheckIcon className="mr-2 inline h-5 w-5" />
                        Two-Factor Auth
                    </button>
                    <button
                        onClick={() => setActiveSection("password")}
                        className={`border-b-2 px-1 py-4 text-sm font-medium ${
                            activeSection === "password"
                                ? "border-brand text-brand"
                                : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700"
                        }`}
                    >
                        <KeyIcon className="mr-2 inline h-5 w-5" />
                        Password
                    </button>
                    <button
                        onClick={() => setActiveSection("sessions")}
                        className={`border-b-2 px-1 py-4 text-sm font-medium ${
                            activeSection === "sessions"
                                ? "border-brand text-brand"
                                : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700"
                        }`}
                    >
                        <ComputerDesktopIcon className="mr-2 inline h-5 w-5" />
                        Devices
                    </button>
                </nav>
            </div>

            {/* Passkeys section */}
            {activeSection === "passkeys" && (
                <div className="space-y-6">
                    {passkeyError && <Alert type="error">{passkeyError}</Alert>}
                    {passkeySuccess && (
                        <Alert type="success">{passkeySuccess}</Alert>
                    )}

                    {/* Existing passkeys */}
                    <div className="rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800">
                        <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-700">
                            <h3 className="text-sm font-medium text-slate-900 dark:text-white">
                                Your Passkeys
                            </h3>
                        </div>
                        <div className="divide-y divide-slate-200 dark:divide-slate-700">
                            {isLoadingPasskeys ? (
                                <div className="px-4 py-8 text-center text-slate-500">
                                    Loading...
                                </div>
                            ) : passkeys.length === 0 ? (
                                <div className="px-4 py-8 text-center text-slate-500">
                                    No passkeys registered yet
                                </div>
                            ) : (
                                passkeys.map((passkey) => (
                                    <div
                                        key={passkey.id}
                                        className="flex items-center justify-between px-4 py-3"
                                    >
                                        <div>
                                            <p className="font-medium text-slate-900 dark:text-white">
                                                {passkey.name}
                                            </p>
                                            <p className="text-sm text-slate-500">
                                                Added{" "}
                                                {new Date(
                                                    passkey.createdAt,
                                                ).toLocaleDateString()}
                                                {passkey.lastUsedAt &&
                                                    ` • Last used ${new Date(passkey.lastUsedAt).toLocaleDateString()}`}
                                            </p>
                                        </div>
                                        <button
                                            onClick={() =>
                                                handleDeletePasskey(passkey.id)
                                            }
                                            className="text-red-600 hover:text-red-700"
                                        >
                                            <TrashIcon className="h-5 w-5" />
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Add passkey */}
                    {supportsPasskey && (
                        <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
                            <h3 className="mb-4 text-sm font-medium text-slate-900 dark:text-white">
                                Add New Passkey
                            </h3>
                            <div className="flex gap-3">
                                <input
                                    type="text"
                                    placeholder="Passkey name (e.g., MacBook Pro)"
                                    value={passkeyName}
                                    onChange={(e) =>
                                        setPasskeyName(e.target.value)
                                    }
                                    className="flex-1"
                                />
                                <button
                                    onClick={handleAddPasskey}
                                    disabled={isRegistering}
                                    className="btn btn-passkey"
                                >
                                    {isRegistering
                                        ? "Adding..."
                                        : "Add Passkey"}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* 2FA section */}
            {activeSection === "2fa" && (
                <div className="space-y-6">
                    {twoFaError && <Alert type="error">{twoFaError}</Alert>}

                    <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
                        <div className="flex items-center justify-between">
                            <div>
                                <h3 className="text-lg font-medium text-slate-900 dark:text-white">
                                    Two-Factor Authentication
                                </h3>
                                <p className="mt-1 text-sm text-slate-500">
                                    {has2fa
                                        ? "Your account is protected with 2FA"
                                        : "Add an extra layer of security to your account"}
                                </p>
                            </div>
                            <div className="flex items-center gap-2">
                                <span
                                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                        has2fa
                                            ? "bg-green-100 text-green-800"
                                            : "bg-slate-100 text-slate-800"
                                    }`}
                                >
                                    {has2fa ? "Enabled" : "Disabled"}
                                </span>
                            </div>
                        </div>

                        <div className="mt-4">
                            {has2fa ? (
                                <a
                                    href="/setup-2fa?action=disable"
                                    className="btn btn-secondary"
                                >
                                    Manage 2FA
                                </a>
                            ) : (
                                <a
                                    href="/setup-2fa"
                                    className="btn btn-primary"
                                >
                                    Enable 2FA
                                </a>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Password section */}
            {activeSection === "password" && (
                <div className="space-y-6">
                    {passwordError && (
                        <Alert type="error">{passwordError}</Alert>
                    )}
                    {passwordSuccess && (
                        <Alert type="success">{passwordSuccess}</Alert>
                    )}

                    <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
                        <h3 className="mb-4 text-lg font-medium text-slate-900 dark:text-white">
                            Change Password
                        </h3>

                        <form
                            onSubmit={handleChangePassword}
                            className="space-y-4"
                        >
                            <div>
                                <label
                                    htmlFor="currentPassword"
                                    className="block text-sm font-medium text-slate-900 dark:text-white"
                                >
                                    Current password
                                </label>
                                <input
                                    id="currentPassword"
                                    type="password"
                                    value={currentPassword}
                                    onChange={(e) =>
                                        setCurrentPassword(e.target.value)
                                    }
                                    className="mt-1"
                                    required
                                />
                            </div>

                            <div>
                                <label
                                    htmlFor="newPassword"
                                    className="block text-sm font-medium text-slate-900 dark:text-white"
                                >
                                    New password
                                </label>
                                <input
                                    id="newPassword"
                                    type="password"
                                    value={newPassword}
                                    onChange={(e) =>
                                        setNewPassword(e.target.value)
                                    }
                                    className="mt-1"
                                    required
                                />
                            </div>

                            <div>
                                <label
                                    htmlFor="confirmPassword"
                                    className="block text-sm font-medium text-slate-900 dark:text-white"
                                >
                                    Confirm new password
                                </label>
                                <input
                                    id="confirmPassword"
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) =>
                                        setConfirmPassword(e.target.value)
                                    }
                                    className="mt-1"
                                    required
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={isChangingPassword}
                                className="btn btn-primary"
                            >
                                {isChangingPassword
                                    ? "Changing..."
                                    : "Change Password"}
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* Sessions/Devices section */}
            {activeSection === "sessions" && (
                <div className="space-y-6">
                    {sessionError && <Alert type="error">{sessionError}</Alert>}
                    {sessionSuccess && (
                        <Alert type="success">{sessionSuccess}</Alert>
                    )}

                    <div className="rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800">
                        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700">
                            <div>
                                <h3 className="text-sm font-medium text-slate-900 dark:text-white">
                                    Active Sessions
                                </h3>
                                <p className="text-xs text-slate-500">
                                    Devices where you&apos;re currently logged
                                    in
                                </p>
                            </div>
                            {sessions.filter((s) => !s.is_current).length >
                                0 && (
                                <button
                                    onClick={handleRevokeAllSessions}
                                    disabled={isRevokingAll}
                                    className="text-sm text-red-600 hover:text-red-700 dark:text-red-400"
                                >
                                    {isRevokingAll
                                        ? "Logging out..."
                                        : "Log out all other devices"}
                                </button>
                            )}
                        </div>
                        <div className="divide-y divide-slate-200 dark:divide-slate-700">
                            {isLoadingSessions ? (
                                <div className="px-4 py-8 text-center text-slate-500">
                                    Loading...
                                </div>
                            ) : sessions.length === 0 ? (
                                <div className="px-4 py-8 text-center text-slate-500">
                                    No active sessions found
                                </div>
                            ) : (
                                sessions.map((session) => (
                                    <div
                                        key={session.id}
                                        className={`flex items-center justify-between px-4 py-4 ${
                                            session.is_current
                                                ? "bg-green-50 dark:bg-green-900/20"
                                                : ""
                                        }`}
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="text-slate-400">
                                                {getDeviceIcon(
                                                    session.device_type,
                                                )}
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className="font-medium text-slate-900 dark:text-white">
                                                        {session.device_name}
                                                    </span>
                                                    {session.is_current && (
                                                        <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900 dark:text-green-300">
                                                            This device
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="text-sm text-slate-500">
                                                    {session.ip_address ||
                                                        "Unknown IP"}{" "}
                                                    • {session.location}
                                                </div>
                                                <div className="text-xs text-slate-400">
                                                    Last active:{" "}
                                                    {formatLastActivity(
                                                        session.last_activity,
                                                    )}{" "}
                                                    • Signed in via{" "}
                                                    {session.auth_method}
                                                </div>
                                            </div>
                                        </div>
                                        {!session.is_current && (
                                            <button
                                                onClick={() =>
                                                    handleRevokeSession(
                                                        session.id,
                                                    )
                                                }
                                                className="rounded-md p-2 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                                                title="Log out this device"
                                            >
                                                <TrashIcon className="h-5 w-5" />
                                            </button>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-700 dark:bg-amber-900/20">
                        <h4 className="text-sm font-medium text-amber-800 dark:text-amber-200">
                            Security tip
                        </h4>
                        <p className="mt-1 text-sm text-amber-700 dark:text-amber-300">
                            If you see a device you don&apos;t recognize, log it
                            out immediately and change your password. Consider
                            enabling two-factor authentication for added
                            security.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}
