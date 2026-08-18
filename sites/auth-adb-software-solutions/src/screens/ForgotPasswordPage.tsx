import Alert from "@/components/Alert";
import {authApi} from "@/utils/api";
import {useState} from "react";

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            const data = await authApi.requestPasswordReset(email);
            if (data.success) {
                setSuccess(true);
            } else {
                // Don't reveal if email exists or not
                setSuccess(true);
            }
        } catch {
            // Don't reveal if email exists or not
            setSuccess(true);
        } finally {
            setIsLoading(false);
        }
    };

    if (success) {
        return (
            <>
                <h2 className="text-center text-2xl leading-9 font-bold tracking-tight text-slate-900 dark:text-white">
                    Check your email
                </h2>
                <p className="mt-4 text-center text-sm text-slate-600 dark:text-slate-400">
                    If an account exists for {email}, we've sent a password
                    reset link.
                </p>
                <a href="/login" className="btn btn-primary mt-6 w-full">
                    Back to login
                </a>
            </>
        );
    }

    return (
        <>
            <h2 className="text-center text-2xl leading-9 font-bold tracking-tight text-slate-900 dark:text-white">
                Reset your password
            </h2>

            <p className="mt-2 text-center text-sm text-slate-600 dark:text-slate-400">
                Enter your email address and we'll send you a link to reset your
                password.
            </p>

            {error && (
                <Alert type="error" className="mt-6">
                    {error}
                </Alert>
            )}

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
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

                <button
                    type="submit"
                    disabled={isLoading}
                    className="btn btn-primary w-full"
                >
                    {isLoading ? "Sending..." : "Send reset link"}
                </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
                <a
                    href="/login"
                    className="font-semibold text-brand hover:underline"
                >
                    Back to login
                </a>
            </p>
        </>
    );
}
