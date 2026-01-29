import {Navigate, Route, Routes} from "react-router-dom";
import {AuthProvider} from "./contexts/AuthContext";
import AuthLayout from "./layouts/AuthLayout";
import DashboardLayout from "./layouts/DashboardLayout";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import LoginPage from "./pages/LoginPage";
import LogoutPage from "./pages/LogoutPage";
import NotFoundPage from "./pages/NotFoundPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import SecuritySettingsPage from "./pages/SecuritySettingsPage";
import Setup2FAPage from "./pages/Setup2FAPage";
import SetupPasskeyPage from "./pages/SetupPasskeyPage";
import SignupPage from "./pages/SignupPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import ThemeProvider from "./providers/ThemeProvider";

export default function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <Routes>
                    {/* Public auth routes */}
                    <Route element={<AuthLayout />}>
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/signup" element={<SignupPage />} />
                        <Route
                            path="/verify-email/:token"
                            element={<VerifyEmailPage />}
                        />
                        <Route
                            path="/forgot-password"
                            element={<ForgotPasswordPage />}
                        />
                        <Route
                            path="/reset-password/:token"
                            element={<ResetPasswordPage />}
                        />
                        <Route path="/logout" element={<LogoutPage />} />
                    </Route>

                    {/* Protected routes for authenticated users */}
                    <Route element={<DashboardLayout />}>
                        <Route
                            path="/setup-passkey"
                            element={<SetupPasskeyPage />}
                        />
                        <Route path="/setup-2fa" element={<Setup2FAPage />} />
                        <Route
                            path="/account"
                            element={
                                <Navigate to="/account/security" replace />
                            }
                        />
                        <Route
                            path="/account/security"
                            element={<SecuritySettingsPage />}
                        />
                    </Route>

                    {/* Catch-all */}
                    <Route path="*" element={<NotFoundPage />} />
                </Routes>
            </AuthProvider>
        </ThemeProvider>
    );
}
