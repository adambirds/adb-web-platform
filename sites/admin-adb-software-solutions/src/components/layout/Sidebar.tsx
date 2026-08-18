"use client";

import { useAuth } from "@/contexts/AuthContext";
import {
    BanknotesIcon,
    BuildingOffice2Icon,
    CircleStackIcon,
    CloudIcon,
    Cog6ToothIcon,
    DocumentTextIcon,
    FolderIcon,
    HomeIcon,
    KeyIcon,
    LifebuoyIcon,
    ListBulletIcon,
    MegaphoneIcon,
    RectangleGroupIcon,
    ServerStackIcon,
    UsersIcon,
    XMarkIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ComponentType, SVGProps } from "react";

interface NavigationItem {
    label: string;
    href: string;
    icon: ComponentType<SVGProps<SVGSVGElement>>;
    permissions?: string[];
}

interface NavigationGroup {
    label: string;
    items: NavigationItem[];
}

interface SidebarProps {
    collapsed: boolean;
    mobileOpen: boolean;
    onCloseMobile: () => void;
}

const navigation: NavigationGroup[] = [
    {
        label: "Overview",
        items: [{ label: "Dashboard", href: "/admin", icon: HomeIcon }],
    },
    {
        label: "Business",
        items: [
            {
                label: "Clients",
                href: "/admin/clients",
                icon: BuildingOffice2Icon,
                permissions: ["clients.view_client"],
            },
            {
                label: "Leads",
                href: "/admin/leads",
                icon: MegaphoneIcon,
                permissions: ["crm.view_lead"],
            },
            {
                label: "Projects",
                href: "/admin/projects",
                icon: FolderIcon,
                permissions: ["clients.view_project"],
            },
            {
                label: "Tasks",
                href: "/admin/tasks",
                icon: ListBulletIcon,
                permissions: ["tasks.view_task"],
            },
            {
                label: "Time tracking",
                href: "/admin/time-tracking",
                icon: BanknotesIcon,
                permissions: ["clients.view_timeentry"],
            },
        ],
    },
    {
        label: "Support",
        items: [
            {
                label: "Tickets",
                href: "/admin/tickets",
                icon: LifebuoyIcon,
                permissions: ["tickets.view_ticket"],
            },
        ],
    },
    {
        label: "Documentation",
        items: [
            {
                label: "Knowledge base",
                href: "/admin/knowledge-base",
                icon: DocumentTextIcon,
                permissions: ["knowledge_base.view_knowledgebasedocument"],
            },
            {
                label: "Credentials",
                href: "/admin/credentials",
                icon: KeyIcon,
                permissions: ["credentials.view_storedcredential"],
            },
        ],
    },
    {
        label: "Technology",
        items: [
            {
                label: "Infrastructure",
                href: "/admin/infrastructure",
                icon: ServerStackIcon,
                permissions: [
                    "infrastructure.view_server",
                    "infrastructure.view_database",
                    "infrastructure.view_website",
                    "infrastructure.view_domain",
                    "infrastructure.view_application",
                ],
            },
            {
                label: "Applications",
                href: "/admin/infrastructure/applications",
                icon: CloudIcon,
                permissions: ["infrastructure.view_application"],
            },
        ],
    },
    {
        label: "Publishing",
        items: [
            {
                label: "Content",
                href: "/admin/content",
                icon: RectangleGroupIcon,
                permissions: [
                    "website.view_blogpost",
                    "website.view_testimonial",
                    "website.view_faq",
                    "website.view_portfolio",
                ],
            },
        ],
    },
    {
        label: "Administration",
        items: [
            {
                label: "Users & access",
                href: "/admin/access",
                icon: UsersIcon,
                permissions: ["authentication.view_user"],
            },
            {
                label: "Settings",
                href: "/admin/settings",
                icon: Cog6ToothIcon,
                permissions: ["core.view_brand"],
            },
        ],
    },
];

function isActive(pathname: string, href: string) {
    if (href === "/admin") return pathname === href;
    return pathname === href || pathname.startsWith(`${href}/`);
}

function SidebarContent({
    collapsed,
    onNavigate,
    showCloseButton = false,
}: {
    collapsed: boolean;
    onNavigate?: () => void;
    showCloseButton?: boolean;
}) {
    const pathname = usePathname();
    const { hasPermission } = useAuth();

    return (
        <>
            <div className="flex h-16 items-center border-b border-slate-800 px-4">
                <Link
                    href="/admin"
                    onClick={onNavigate}
                    className="flex min-w-0 flex-1 items-center gap-3 overflow-hidden"
                >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-adb-cyan-500 font-black text-slate-950">
                        A
                    </div>
                    {!collapsed && (
                        <div className="min-w-0">
                            <div className="truncate text-sm font-semibold text-white">
                                ADB Platform
                            </div>
                            <div className="truncate text-xs text-slate-500">
                                Operations Console
                            </div>
                        </div>
                    )}
                </Link>
                {showCloseButton && (
                    <button
                        type="button"
                        onClick={onNavigate}
                        className="ml-3 flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-800 hover:text-white"
                        aria-label="Close navigation"
                    >
                        <XMarkIcon className="h-5 w-5" />
                    </button>
                )}
            </div>

            <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
                {navigation.map((group) => {
                    const items = group.items.filter(
                        (item) =>
                            !item.permissions ||
                            item.permissions.some((permission) =>
                                hasPermission(permission),
                            ),
                    );
                    if (items.length === 0) return null;

                    return (
                        <div key={group.label}>
                            {!collapsed && (
                                <p className="mb-2 px-3 text-[10px] font-bold tracking-[0.18em] text-slate-600 uppercase">
                                    {group.label}
                                </p>
                            )}
                            <div className="space-y-1">
                                {items.map((item) => {
                                    const active = isActive(pathname, item.href);
                                    const Icon = item.icon;
                                    return (
                                        <Link
                                            key={`${group.label}-${item.label}`}
                                            href={item.href}
                                            onClick={onNavigate}
                                            title={collapsed ? item.label : undefined}
                                            className={`group flex h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium transition ${
                                                active
                                                    ? "bg-slate-800 text-white shadow-inner shadow-black/20"
                                                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-100"
                                            }`}
                                        >
                                            <Icon
                                                className={`h-5 w-5 shrink-0 ${
                                                    active
                                                        ? "text-adb-cyan-400"
                                                        : "text-slate-500 group-hover:text-slate-300"
                                                }`}
                                            />
                                            {!collapsed && (
                                                <span className="truncate">
                                                    {item.label}
                                                </span>
                                            )}
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>
                    );
                })}
            </nav>

            <div className="border-t border-slate-800 p-4">
                {!collapsed ? (
                    <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
                        <div className="text-xs font-medium text-slate-300">
                            ADB Business Platform
                        </div>
                        <div className="mt-1 text-[11px] leading-4 text-slate-600">
                            CRM, support, projects and infrastructure in one place.
                        </div>
                    </div>
                ) : (
                    <CircleStackIcon className="mx-auto h-5 w-5 text-slate-600" />
                )}
            </div>
        </>
    );
}

export function Sidebar({
    collapsed,
    mobileOpen,
    onCloseMobile,
}: SidebarProps) {
    return (
        <>
            <aside
                className={`hidden shrink-0 border-r border-slate-800 bg-slate-950 transition-[width] duration-200 lg:flex lg:flex-col ${collapsed ? "w-20" : "w-72"}`}
            >
                <SidebarContent collapsed={collapsed} />
            </aside>

            {mobileOpen && (
                <div className="fixed inset-0 z-50 lg:hidden">
                    <button
                        type="button"
                        aria-label="Close navigation"
                        onClick={onCloseMobile}
                        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                    />
                    <aside className="relative flex h-full w-[min(88vw,20rem)] flex-col border-r border-slate-800 bg-slate-950 shadow-2xl shadow-black/50">
                        <SidebarContent
                            collapsed={false}
                            onNavigate={onCloseMobile}
                            showCloseButton
                        />
                    </aside>
                </div>
            )}
        </>
    );
}
