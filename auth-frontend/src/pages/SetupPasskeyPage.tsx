import Alert from "@/components/Alert";
import {useAuth} from "@/contexts/AuthContext";
import {authApi} from "@/utils/api";
import {getRedirectUrl} from "@/utils/config";
import {createPasskey, isWebAuthnSupported} from "@/utils/webauthn";
import {CheckCircleIcon, FingerPrintIcon} from "@heroicons/react/24/solid";
import {useState} from "react";

export default function SetupPasskeyPage() {
    const {refreshUser} = useAuth();
    const [passkeyName, setPasskeyName] = useState("");
    const [isRegistering, setIsRegistering] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const supportsPasskey = isWebAuthnSupported();

    if (!supportsPasskey) {
        return (
            <div className="space-y-6">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Set Up Passkey
                </h1>
                <Alert type="warning">
                    Passkeys are not supported in this browser. Please use a
                    browser that supports WebAuthn, such as Chrome, Firefox,
                    Safari, or Edge.
                </Alert>
                <a
                    href={getRedirectUrl()}
                    className="btn btn-primary inline-block"
                >
                    Continue to app
                </a>
            </div>
        );
    }

    const handleRegister = async () => {
        if (!passkeyName.trim()) {
            setError("Please enter a name for your passkey");
            return;
        }

        setIsRegistering(true);
        setError(null);

        try {
            // Begin registration
            const beginData = await authApi.beginPasskeyRegistration(
                passkeyName.trim(),
            );
            if (!beginData.success || !beginData.options) {
                throw new Error(
                    beginData.message || "Failed to start registration",
                );
            }

            // Create credential
            let options = beginData.options;
            if (typeof options === "string") {
                options = JSON.parse(options);
            }
            const credential = await createPasskey(options);

            // Complete registration
            const completeData =
                await authApi.completePasskeyRegistration(credential);
            if (!completeData.success) {
                throw new Error(
                    completeData.message || "Failed to register passkey",
                );
            }

            setSuccess(true);
            await refreshUser();
        } catch (err: unknown) {
            if (err instanceof Error) {
                // Don't show error if user cancelled
                if (err.name !== "NotAllowedError") {
                    setError(err.message || "Failed to register passkey");
                }
            }
        } finally {
            setIsRegistering(false);
        }
    };

    if (success) {
        return (
            <div className="space-y-6 text-center">
                <CheckCircleIcon className="mx-auto h-16 w-16 text-green-500" />
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Passkey Added!
                </h1>
                <p className="text-slate-600 dark:text-slate-400">
                    You can now use this passkey to sign in without a password.
                </p>
                <div className="flex flex-col gap-3">
                    <a href="/setup-2fa" className="btn btn-secondary">
                        Set up 2FA (optional)
                    </a>
                    <a href={getRedirectUrl()} className="btn btn-primary">
                        Continue to app
                    </a>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="text-center">
                <FingerPrintIcon className="mx-auto h-16 w-16 text-brand" />
                <h1 className="mt-4 text-2xl font-bold text-slate-900 dark:text-white">
                    Set Up Passkey
                </h1>
                <p className="mt-2 text-slate-600 dark:text-slate-400">
                    Add a passkey for faster, more secure sign-in. You can use
                    Face ID, Touch ID, Windows Hello, or a security key.
                </p>
            </div>

            {error && <Alert type="error">{error}</Alert>}

            <div className="space-y-4">
                <div>
                    <label
                        htmlFor="passkeyName"
                        className="block text-sm leading-6 font-medium text-slate-900 dark:text-white"
                    >
                        Passkey name
                    </label>
                    <div className="mt-2">
                        <input
                            id="passkeyName"
                            name="passkeyName"
                            type="text"
                            placeholder="e.g., MacBook Pro, iPhone 15"
                            value={passkeyName}
                            onChange={(e) => setPasskeyName(e.target.value)}
                        />
                    </div>
                    <p className="mt-1 text-sm text-slate-500">
                        Give your passkey a name to identify it later
                    </p>
                </div>

                <button
                    onClick={handleRegister}
                    disabled={isRegistering}
                    className="btn btn-passkey w-full"
                >
                    {isRegistering ? "Registering..." : "Create passkey"}
                </button>
            </div>

            <div className="flex justify-center">
                <a
                    href={getRedirectUrl()}
                    className="text-sm text-slate-500 hover:text-slate-700"
                >
                    Skip for now
                </a>
            </div>
        </div>
    );
}
