"use client";

import { useAuth } from "@/contexts/AuthContext";
import { getAccountUrl } from "@/lib/config";
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";
import {
    Bars3Icon,
    BellIcon,
    ChevronLeftIcon,
    ChevronRightIcon,
    MagnifyingGlassIcon,
} from "@heroicons/react/24/outline";

interface TopBarProps {
    collapsed: boolean;
    onToggleSidebar: () => void;
    onOpenMobileNavigation: () => void;
}

function initials(firstName?: string, lastName?: string) {
    const value = `${firstName?.[0] ?? ""}${lastName?.[0] ?? ""}`.trim();
    return value || "A";
}

export function TopBar({
    collapsed,
    onToggleSidebar,
    onOpenMobileNavigation,
}: TopBarProps) {
    const { user, logout } = useAuth();
    const displayName =
        [user?.firstName, user?.lastName].filter(Boolean).join(" ") ||
        user?.email ||
        "User";

    return (
        <header className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b border-slate-800 bg-slate-900/95 px-4 backdrop-blur lg:px-6">
            <button
                type="button"
                onClick={onToggleSidebar}
                className="hidden h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-800 hover:text-white lg:flex"
                aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
                {collapsed ? (
                    <ChevronRightIcon className="h-5 w-5" />
                ) : (
                    <ChevronLeftIcon className="h-5 w-5" />
                )}
            </button>

            <button
                type="button"
                onClick={onOpenMobileNavigation}
                className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white lg:hidden"
                aria-label="Open navigation"
            >
                <Bars3Icon className="h-5 w-5" />
            </button>

            <button
                type="button"
                className="group flex h-9 min-w-0 flex-1 items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/70 px-3 text-left text-sm text-slate-500 transition hover:border-slate-700 hover:text-slate-300 md:max-w-xl"
                title="Global search will search clients, tickets, projects, tasks and documentation"
            >
                <MagnifyingGlassIcon className="h-4 w-4 shrink-0" />
                <span className="truncate">Search the platform...</span>
                <kbd className="ml-auto hidden rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-[10px] text-slate-600 sm:block">
                    ⌘K
                </kbd>
            </button>

            <div className="ml-auto flex items-center gap-2">
                <button
                    type="button"
                    className="relative flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-800 hover:text-white"
                    aria-label="Notifications"
                >
                    <BellIcon className="h-5 w-5" />
                </button>

                <Menu as="div" className="relative">
                    <MenuButton className="flex items-center gap-2 rounded-lg p-1.5 transition hover:bg-slate-800">
                        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-adb-cyan-500 text-xs font-black text-slate-950">
                            {initials(user?.firstName, user?.lastName)}
                        </span>
                        <span className="hidden min-w-0 text-left xl:block">
                            <span className="block max-w-40 truncate text-sm font-medium text-slate-200">
                                {displayName}
                            </span>
                            <span className="block max-w-40 truncate text-[11px] text-slate-500">
                                {user?.email}
                            </span>
                        </span>
                    </MenuButton>
                    <MenuItems
                        anchor="bottom end"
                        className="z-50 mt-2 w-56 rounded-xl border border-slate-800 bg-slate-950 p-1.5 shadow-2xl shadow-black/40 focus:outline-none"
                    >
                        <div className="border-b border-slate-800 px-3 py-2 xl:hidden">
                            <p className="truncate text-sm font-medium text-slate-200">
                                {displayName}
                            </p>
                            <p className="truncate text-xs text-slate-500">
                                {user?.email}
                            </p>
                        </div>
                        <MenuItem>
                            <a
                                href={getAccountUrl()}
                                className="block rounded-lg px-3 py-2 text-sm text-slate-300 data-[focus]:bg-slate-800 data-[focus]:text-white"
                            >
                                Account & security
                            </a>
                        </MenuItem>
                        <MenuItem>
                            <button
                                type="button"
                                onClick={() => void logout()}
                                className="block w-full rounded-lg px-3 py-2 text-left text-sm text-red-300 data-[focus]:bg-red-950/40"
                            >
                                Sign out
                            </button>
                        </MenuItem>
                    </MenuItems>
                </Menu>
            </div>
        </header>
    );
}
