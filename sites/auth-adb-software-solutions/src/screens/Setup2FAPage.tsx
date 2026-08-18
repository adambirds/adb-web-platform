import Alert from "@/components/Alert";
import {useAuth} from "@/contexts/AuthContext";
import {authApi} from "@/utils/api";
import {getRedirectUrl} from "@/utils/config";
import {CheckCircleIcon, ShieldCheckIcon} from "@heroicons/react/24/solid";
import Image from "next/image";
import QRCode from "qrcode";
import {useState} from "react";

export default function Setup2FAPage() {
    const {refreshUser} = useAuth();
    const [step, setStep] = useState<"setup" | "verify" | "codes" | "complete">(
        "setup",
    );
    const [qrCodeDataUrl, setQrCodeDataUrl] = useState<string | null>(null);
    const [secret, setSecret] = useState<string | null>(null);
    const [code, setCode] = useState("");
    const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleBeginSetup = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const data = await authApi.begin2FASetup();
            if (!data.success) {
                throw new Error(data.message || "Failed to set up 2FA");
            }

            // Generate QR code
            if (data.qrCodeUri) {
                const qrDataUrl = await QRCode.toDataURL(data.qrCodeUri);
                setQrCodeDataUrl(qrDataUrl);
            }
            setSecret(data.secret || null);
            setStep("verify");
        } catch (err: unknown) {
            if (err instanceof Error) {
                setError(err.message);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleVerify = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!code.trim()) return;

        setIsLoading(true);
        setError(null);

        try {
            const data = await authApi.confirm2FASetup(code.trim());
            if (!data.success) {
                throw new Error(data.message || "Verification failed");
            }

            setRecoveryCodes(data.recoveryCodes || []);
            setStep("codes");
            await refreshUser();
        } catch (err: unknown) {
            if (err instanceof Error) {
                setError(err.message);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleContinue = () => {
        setStep("complete");
    };

    // Setup step
    if (step === "setup") {
        return (
            <div className="space-y-6">
                <div className="text-center">
                    <ShieldCheckIcon className="mx-auto h-16 w-16 text-brand" />
                    <h1 className="mt-4 text-2xl font-bold text-slate-900 dark:text-white">
                        Set Up Two-Factor Authentication
                    </h1>
                    <p className="mt-2 text-slate-600 dark:text-slate-400">
                        Add an extra layer of security to your account by using
                        an authenticator app.
                    </p>
                </div>

                {error && <Alert type="error">{error}</Alert>}

                <button
                    onClick={handleBeginSetup}
                    disabled={isLoading}
                    className="btn btn-primary w-full"
                >
                    {isLoading ? "Setting up..." : "Begin setup"}
                </button>

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

    // Verify step - show QR code and verify
    if (step === "verify") {
        return (
            <div className="space-y-6">
                <div className="text-center">
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                        Scan QR Code
                    </h1>
                    <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                        Scan this QR code with your authenticator app
                    </p>
                </div>

                {qrCodeDataUrl && (
                    <div className="flex justify-center">
                        <Image
                            src={qrCodeDataUrl}
                            alt="2FA QR Code"
                            width={192}
                            height={192}
                            unoptimized
                        />
                    </div>
                )}

                {secret && (
                    <div className="rounded-md bg-slate-100 p-4 text-center dark:bg-slate-700">
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                            Or enter this code manually:
                        </p>
                        <p className="mt-1 font-mono text-sm tracking-wide text-slate-900 dark:text-white">
                            {secret}
                        </p>
                    </div>
                )}

                {error && <Alert type="error">{error}</Alert>}

                <form onSubmit={handleVerify} className="space-y-4">
                    <div>
                        <label
                            htmlFor="code"
                            className="block text-sm leading-6 font-medium text-slate-900 dark:text-white"
                        >
                            Enter verification code
                        </label>
                        <div className="mt-2">
                            <input
                                id="code"
                                name="code"
                                type="text"
                                autoComplete="one-time-code"
                                placeholder="000000"
                                value={code}
                                onChange={(e) => setCode(e.target.value)}
                                className="text-center text-lg tracking-widest"
                                maxLength={6}
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading || code.length < 6}
                        className="btn btn-primary w-full"
                    >
                        {isLoading ? "Verifying..." : "Verify and enable"}
                    </button>
                </form>
            </div>
        );
    }

    // Recovery codes step
    if (step === "codes") {
        return (
            <div className="space-y-6">
                <div className="text-center">
                    <CheckCircleIcon className="mx-auto h-16 w-16 text-green-500" />
                    <h1 className="mt-4 text-2xl font-bold text-slate-900 dark:text-white">
                        2FA Enabled!
                    </h1>
                    <p className="mt-2 text-slate-600 dark:text-slate-400">
                        Save these recovery codes in a safe place. You can use
                        them if you lose access to your authenticator app.
                    </p>
                </div>

                <div className="rounded-md bg-slate-100 p-4 dark:bg-slate-700">
                    <div className="grid grid-cols-2 gap-2 font-mono text-sm">
                        {recoveryCodes.map((code, index) => (
                            <div
                                key={index}
                                className="text-center text-slate-900 dark:text-white"
                            >
                                {code}
                            </div>
                        ))}
                    </div>
                </div>

                <Alert type="warning">
                    Each code can only be used once. Store them securely!
                </Alert>

                <button
                    onClick={handleContinue}
                    className="btn btn-primary w-full"
                >
                    I've saved my codes
                </button>
            </div>
        );
    }

    // Complete step
    return (
        <div className="space-y-6 text-center">
            <CheckCircleIcon className="mx-auto h-16 w-16 text-green-500" />
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                You're all set!
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
                Your account is now protected with two-factor authentication.
            </p>
            <a href={getRedirectUrl()} className="btn btn-primary inline-block">
                Continue to app
            </a>
        </div>
    );
}
