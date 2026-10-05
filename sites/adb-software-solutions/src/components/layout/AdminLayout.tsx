"use client";

import { TaskDrawerProvider } from "@/components/admin/TaskDrawerProvider";
import { LiveEventsProvider } from "@/contexts/LiveEventsContext";
import { useAuth } from "@/contexts/AuthContext";
import { usePathname } from "next/navigation";
import { ReactNode, useState } from "react";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { WorkManagementSidebar } from "./WorkManagementSidebar";

const workManagementPrefixes = [
    "/admin/projects",
    "/admin/tasks",
    "/admin/task-lists",
    "/admin/time-tracking",
    "/admin/calendar",
];

export function AdminLayout({ children }: { children: ReactNode }) {
    const { isAuthenticated, isLoading, login } = useAuth();
    const pathname = usePathname();
    const [collapsed, setCollapsed] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);
    const showWorkManagement = workManagementPrefixes.some(
        (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
    );

    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-200">
                <div className="text-center">
                    <div className="border-t-adb-cyan-400 inline-block h-8 w-8 animate-spin rounded-full border-4 border-slate-800" />
                    <p className="mt-4 text-sm text-slate-500">
                        Loading operations console...
                    </p>
                </div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6">
                <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center shadow-2xl shadow-black/30">
                    <div className="bg-adb-cyan-500 mx-auto flex h-12 w-12 items-center justify-center rounded-xl text-lg font-black text-slate-950">
                        A
                    </div>
                    <h1 className="mt-5 text-xl font-semibold text-white">
                        Sign in required
                    </h1>
                    <p className="mt-2 text-sm leading-6 text-slate-400">
                        Sign in with an authorised ADB staff account to access
                        the business platform.
                    </p>
                    <button
                        type="button"
                        onClick={login}
                        className="bg-adb-cyan-500 hover:bg-adb-cyan-400 mt-6 inline-flex h-10 items-center justify-center rounded-lg px-5 text-sm font-semibold text-slate-950 transition"
                    >
                        Continue to sign in
                    </button>
                </div>
            </div>
        );
    }

    return (
        <LiveEventsProvider>
            <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-200">
                <Sidebar
                    collapsed={collapsed}
                    mobileOpen={mobileOpen}
                    onCloseMobile={() => setMobileOpen(false)}
                />
                <div className="flex min-w-0 flex-1 flex-col">
                    <TopBar
                        collapsed={collapsed}
                        onToggleSidebar={() => setCollapsed((value) => !value)}
                        onOpenMobileNavigation={() => setMobileOpen(true)}
                    />
                    <div className="flex min-h-0 flex-1">
                        {showWorkManagement ? <WorkManagementSidebar /> : null}
                        <main className="min-h-0 min-w-0 flex-1 overflow-y-auto bg-slate-950">
                            <TaskDrawerProvider>{children}</TaskDrawerProvider>
                        </main>
                    </div>
                </div>
            </div>
        </LiveEventsProvider>
    );
}
