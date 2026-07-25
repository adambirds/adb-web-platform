import {
    ButtonLink,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Container,
    PageHeader,
    StatCard,
} from "@/components/ui";

export const metadata = {
    title: "Admin Dashboard",
};

const quickLinks = [
    {
        title: "Manage Clients",
        description: "View and manage all clients",
        href: "/admin/clients",
    },
    {
        title: "Manage Projects",
        description: "View and manage all projects",
        href: "/admin/projects",
    },
    {
        title: "Time Tracking",
        description: "Track and log time entries",
        href: "/admin/time-tracking",
    },
    {
        title: "Leads",
        description: "Manage sales leads",
        href: "/admin/leads",
    },
    {
        title: "Infrastructure",
        description: "Manage servers and assets",
        href: "/admin/infrastructure",
    },
    {
        title: "Credentials",
        description: "Manage secure credentials",
        href: "/admin/credentials",
    },
    {
        title: "Content",
        description: "Manage portfolio, blog, FAQs, and testimonials",
        href: "/admin/content",
    },
];

export default function AdminDashboard() {
    return (
        <Container className="py-10">
            <PageHeader
                title="Dashboard"
                description="Operational overview for ADB Software Solutions."
                actions={
                    <ButtonLink href="/admin/content">
                        Manage content
                    </ButtonLink>
                }
            />

            <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                <StatCard label="Clients" value="—" />
                <StatCard label="Projects" value="—" />
                <StatCard label="Hours tracked" value="—" />
                <StatCard label="Leads" value="—" />
            </div>

            <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {quickLinks.map((item) => (
                    <Card key={item.title}>
                        <CardHeader>
                            <CardTitle>{item.title}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-adb-navy-600 dark:text-adb-navy-300 text-sm">
                                {item.description}
                            </p>
                            <div className="mt-4">
                                <ButtonLink href={item.href} variant="outline">
                                    Open
                                </ButtonLink>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </Container>
    );
}
