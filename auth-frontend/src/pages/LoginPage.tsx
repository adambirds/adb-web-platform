import Alert from "@/components/Alert";
import TwoFactorVerification from "@/components/TwoFactorVerification";
import {useAuth} from "@/contexts/AuthContext";
import {getRedirectUrl} from "@/utils/config";
import {isWebAuthnSupported} from "@/utils/webauthn";
import {
    EyeIcon,
    EyeSlashIcon,
    FingerPrintIcon,
} from "@heroicons/react/24/solid";
import {useEffect, useState} from "react";

export default function LoginPage() {
    const {user, login, loginWithPasskey, requires2fa, verify2fa, cancel2fa} =
        useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isPasskeyLoading, setIsPasskeyLoading] = useState(false);
    const [is2faLoading, setIs2faLoading] = useState(false);
    const [isRedirecting, setIsRedirecting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [supportsPasskey, setSupportsPasskey] = useState(false);

    useEffect(() => {
        setSupportsPasskey(isWebAuthnSupported());
    }, []);

    // Redirect if already authenticated
    useEffect(() => {
        if (user) {
            setIsRedirecting(true);
            const redirectUrl = getRedirectUrl();
            window.location.href = redirectUrl;
        }
    }, [user]);

    const handleLogin = async (e: React.FormEvent) => {
        console.log("[LoginPage] handleLogin called");
        e.preventDefault();
        console.log("[LoginPage] preventDefault called");
        setIsLoading(true);
        setError(null);

        try {
            console.log("[LoginPage] About to call login with email:", email);
            await login(email, password);
            console.log("[LoginPage] Login completed");
            // If 2FA is required, the UI will update to show 2FA form
            // Otherwise, the useEffect will handle the redirect
        } catch (err: unknown) {
            console.error("[LoginPage] Login error:", err);
            if (err instanceof Error) {
                setError(err.message);
            } else {
                setError("An error occurred during login");
            }
        } finally {
            console.log("[LoginPage] Setting isLoading to false");
            setIsLoading(false);
        }
    };

    const handlePasskeyLogin = async () => {
        setIsPasskeyLoading(true);
        setError(null);

        try {
            await loginWithPasskey();
            // Redirect will happen via useEffect
        } catch (err: unknown) {
            if (err instanceof Error) {
                // Don't show error if user cancelled
                if (err.name !== "NotAllowedError") {
                    setError(err.message || "Passkey authentication failed");
                }
            }
        } finally {
            setIsPasskeyLoading(false);
        }
    };

    const handle2faVerify = async (code: string, isRecoveryCode: boolean) => {
        setIs2faLoading(true);
        setError(null);

        try {
            await verify2fa(code, isRecoveryCode);
            // Redirect will happen via useEffect
        } catch (err: unknown) {
            if (err instanceof Error) {
                setError(err.message || "Verification failed");
            }
        } finally {
            setIs2faLoading(false);
        }
    };

    const handle2faCancel = () => {
        setError(null);
        cancel2fa();
    };

    // Show 2FA verification if required
    if (requires2fa) {
        return (
            <>
                <h2 className="text-center text-2xl leading-9 font-bold tracking-tight text-slate-900 dark:text-white">
                    Two-Factor Authentication
                </h2>
                <div className="mt-6">
                    <TwoFactorVerification
                        onVerify={handle2faVerify}
                        onCancel={handle2faCancel}
                        isLoading={is2faLoading}
                        error={error}
                    />
                </div>
            </>
        );
    }

    // Show redirecting state
    if (isRedirecting) {
        return (
            <div className="text-center">
                <h2 className="text-2xl leading-9 font-bold tracking-tight text-slate-900 dark:text-white">
                    Redirecting...
                </h2>
                <p className="mt-4 text-slate-600 dark:text-slate-400">
                    Please wait while we redirect you.
                </p>
            </div>
        );
    }

    return (
        <>
            <h2 className="text-center text-2xl leading-9 font-bold tracking-tight text-slate-900 dark:text-white">
                Sign in to your account
            </h2>

            {error && (
                <Alert type="error" className="mt-6">
                    {error}
                </Alert>
            )}

            <div className="mt-6 space-y-6">
                {/* Passkey login button - prominent position */}
                {supportsPasskey && (
                    <button
                        type="button"
                        onClick={handlePasskeyLogin}
                        disabled={isPasskeyLoading || isLoading}
                        className="btn btn-passkey flex w-full gap-2"
                    >
                        <FingerPrintIcon className="h-5 w-5" />
                        {isPasskeyLoading
                            ? "Authenticating..."
                            : "Sign in with Passkey"}
                    </button>
                )}

                {supportsPasskey && (
                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-slate-300 dark:border-slate-600" />
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="bg-white px-2 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                                or continue with password
                            </span>
                        </div>
                    </div>
                )}

                {/* Password login form */}
                <form onSubmit={handleLogin} className="space-y-4">
                    <div>
                        <label
                            htmlFor="email"
                            className="block text-sm leading-6 font-medium text-slate-900 dark:text-white"
                        >
                            Email address
                        </label>
                        <div className="mt-2">
                            <input
                                id="email"
                                name="email"
                                type="email"
                                autoComplete="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <div className="flex items-center justify-between">
                            <label
                                htmlFor="password"
                                className="block text-sm leading-6 font-medium text-slate-900 dark:text-white"
                            >
                                Password
                            </label>
                            <a
                                href="/forgot-password"
                                className="text-brand text-sm font-semibold hover:underline"
                            >
                                Forgot password?
                            </a>
                        </div>
                        <div className="relative mt-2">
                            <input
                                id="password"
                                name="password"
                                type={showPassword ? "text" : "password"}
                                autoComplete="current-password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="pr-10"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute inset-y-0 right-0 flex items-center pr-3"
                            >
                                {showPassword ? (
                                    <EyeSlashIcon className="h-5 w-5 text-slate-400" />
                                ) : (
                                    <EyeIcon className="h-5 w-5 text-slate-400" />
                                )}
                            </button>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading || isPasskeyLoading}
                        className="btn btn-primary w-full"
                    >
                        {isLoading ? "Signing in..." : "Sign in"}
                    </button>
                </form>

                <p className="text-center text-sm text-slate-500 dark:text-slate-400">
                    Don't have an account?{" "}
                    <a
                        href="/signup"
                        className="text-brand font-semibold hover:underline"
                    >
                        Sign up
                    </a>
                </p>
            </div>
        </>
    );
}
