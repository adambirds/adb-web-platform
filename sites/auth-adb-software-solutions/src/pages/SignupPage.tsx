import Alert from "@/components/Alert";
import {authApi} from "@/utils/api";
import {useState} from "react";
import {useNavigate} from "react-router-dom";

export default function SignupPage() {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [firstName, setFirstName] = useState("");
    const [lastName, setLastName] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [passwordError, setPasswordError] = useState<string | null>(null);
    const [confirmPasswordError, setConfirmPasswordError] = useState<
        string | null
    >(null);

    const validatePassword = (password: string): boolean => {
        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{12,}$/;
        return passwordRegex.test(password);
    };

    const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setPassword(value);
        setPasswordError(
            validatePassword(value)
                ? null
                : "Password must be 12+ characters with uppercase, lowercase, and number",
        );
    };

    const handleConfirmPasswordChange = (
        e: React.ChangeEvent<HTMLInputElement>,
    ) => {
        const value = e.target.value;
        setConfirmPassword(value);
        setConfirmPasswordError(
            value === password ? null : "Passwords do not match",
        );
    };

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        if (!validatePassword(password)) {
            setPasswordError(
                "Password must be 12+ characters with uppercase, lowercase, and number",
            );
            setIsLoading(false);
            return;
        }

        if (password !== confirmPassword) {
            setConfirmPasswordError("Passwords do not match");
            setIsLoading(false);
            return;
        }

        try {
            const result = await authApi.register({
                email,
                password,
                firstName,
                lastName,
            });

            if (result.success) {
                // Redirect to a page telling them to check their email
                navigate("/login?message=verification-sent");
            } else {
                setError(result.message || "Registration failed");
            }
        } catch (err: unknown) {
            if (err instanceof Error) {
                setError(err.message);
            } else {
                setError("An error occurred during registration");
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            <h2 className="text-center text-2xl leading-9 font-bold tracking-tight text-slate-900 dark:text-white">
                Create your account
            </h2>

            {error && (
                <Alert type="error" className="mt-6">
                    {error}
                </Alert>
            )}

            <form onSubmit={handleSignup} className="mt-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label
                            htmlFor="firstName"
                            className="block text-sm leading-6 font-medium text-slate-900 dark:text-white"
                        >
                            First name
                        </label>
                        <div className="mt-2">
                            <input
                                id="firstName"
                                name="firstName"
                                type="text"
                                autoComplete="given-name"
                                required
                                value={firstName}
                                onChange={(e) => setFirstName(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <label
                            htmlFor="lastName"
                            className="block text-sm leading-6 font-medium text-slate-900 dark:text-white"
                        >
                            Last name
                        </label>
                        <div className="mt-2">
                            <input
                                id="lastName"
                                name="lastName"
                                type="text"
                                autoComplete="family-name"
                                required
                                value={lastName}
                                onChange={(e) => setLastName(e.target.value)}
                            />
                        </div>
                    </div>
                </div>

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
                    <label
                        htmlFor="password"
                        className="block text-sm leading-6 font-medium text-slate-900 dark:text-white"
                    >
                        Password
                    </label>
                    <div className="mt-2">
                        <input
                            id="password"
                            name="password"
                            type="password"
                            autoComplete="new-password"
                            required
                            value={password}
                            onChange={handlePasswordChange}
                        />
                    </div>
                    {passwordError && (
                        <p className="mt-1 text-sm text-red-600">
                            {passwordError}
                        </p>
                    )}
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
                            onChange={handleConfirmPasswordChange}
                        />
                    </div>
                    {confirmPasswordError && (
                        <p className="mt-1 text-sm text-red-600">
                            {confirmPasswordError}
                        </p>
                    )}
                </div>

                <button
                    type="submit"
                    disabled={isLoading}
                    className="btn btn-primary w-full"
                >
                    {isLoading ? "Creating account..." : "Create account"}
                </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
                Already have an account?{" "}
                <a
                    href="/login"
                    className="text-brand font-semibold hover:underline"
                >
                    Sign in
                </a>
            </p>
        </>
    );
}
