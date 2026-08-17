import Alert from "@/components/Alert";
import {authApi} from "@/utils/api";
import {useState} from "react";

interface ResetPasswordPageProps {
    token?: string;
}

export default function ResetPasswordPage({token}: ResetPasswordPageProps) {
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const validatePassword = (password: string): boolean => {
        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{12,}$/;
        return passwordRegex.test(password);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!token) {
            setError("Invalid reset link");
            return;
        }

        if (!validatePassword(password)) {
            setError(
                "Password must be 12+ characters with uppercase, lowercase, and number",
            );
            return;
        }

        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        setIsLoading(true);

        try {
            const data = await authApi.resetPassword(token, password);
            if (data.success) {
                setSuccess(true);
            } else {
                setError(data.message || "Failed to reset password");
            }
        } catch (err: unknown) {
            if (err instanceof Error) {
                setError(err.message);
            } else {
                setError("An error occurred");
            }
        } finally {
            setIsLoading(false);
        }
    };

    if (success) {
        return (
            <>
                <h2 className="text-center text-2xl leading-9 font-bold tracking-tight text-slate-900 dark:text-white">
                    Password reset successful
                </h2>
                <p className="mt-4 text-center text-sm text-slate-600 dark:text-slate-400">
                    Your password has been reset. You can now sign in with your
                    new password.
                </p>
                <a href="/login" className="btn btn-primary mt-6 w-full">
                    Sign in
                </a>
            </>
        );
    }

    return (
        <>
            <h2 className="text-center text-2xl leading-9 font-bold tracking-tight text-slate-900 dark:text-white">
                Set new password
            </h2>

            {error && (
                <Alert type="error" className="mt-6">
                    {error}
                </Alert>
            )}

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                <div>
                    <label
                        htmlFor="password"
                        className="block text-sm leading-6 font-medium text-slate-900 dark:text-white"
                    >
                        New password
                    </label>
                    <div className="mt-2">
                        <input
                            id="password"
                            name="password"
                            type="password"
                            autoComplete="new-password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                        12+ characters with uppercase, lowercase, and number
                    </p>
                </div>

                <div>
                    <label
                        htmlFor="confirmPassword"
                        className="block text-sm leading-6 font-medium text-slate-900 dark:text-white"
                    >
                        Confirm password
                    </label>
                    <div className="mt-2">
                        <input
                            id="confirmPassword"
                            name="confirmPassword"
                            type="password"
                            autoComplete="new-password"
                            required
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                        />
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={isLoading}
                    className="btn btn-primary w-full"
                >
                    {isLoading ? "Resetting..." : "Reset password"}
                </button>
            </form>
        </>
    );
}
