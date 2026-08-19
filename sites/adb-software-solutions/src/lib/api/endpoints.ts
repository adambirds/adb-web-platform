const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const AdminAPI = {
    dashboard: {
        summary: () => `${API_BASE_URL}/admin/dashboard`,
    },
    brands: {
        list: () => `${API_BASE_URL}/admin/brands`,
    },
    clients: {
        list: () => `${API_BASE_URL}/admin/clients`,
        get: (id: number) => `${API_BASE_URL}/admin/clients/${id}`,
        create: () => `${API_BASE_URL}/admin/clients`,
        update: (id: number) => `${API_BASE_URL}/admin/clients/${id}`,
        delete: (id: number) => `${API_BASE_URL}/admin/clients/${id}`,
        contacts: {
            create: (clientId: number) =>
                `${API_BASE_URL}/admin/clients/${clientId}/contacts`,
            get: (clientId: number, contactId: number) =>
                `${API_BASE_URL}/admin/clients/${clientId}/contacts/${contactId}`,
            update: (clientId: number, contactId: number) =>
                `${API_BASE_URL}/admin/clients/${clientId}/contacts/${contactId}`,
        },
    },
    projects: {
        list: () => `${API_BASE_URL}/admin/projects`,
        get: (id: number) => `${API_BASE_URL}/admin/projects/${id}`,
    },
    tasks: {
        list: () => `${API_BASE_URL}/admin/tasks`,
    },
    timeEntries: {
        list: () => `${API_BASE_URL}/admin/time-entries`,
        create: () => `${API_BASE_URL}/admin/time-entries`,
    },
    leads: {
        list: () => `${API_BASE_URL}/admin/leads`,
        get: (id: number) => `${API_BASE_URL}/admin/leads/${id}`,
        create: () => `${API_BASE_URL}/admin/leads`,
        update: (id: number) => `${API_BASE_URL}/admin/leads/${id}`,
        options: () => `${API_BASE_URL}/admin/lead-options`,
        assignment: (id: number) => `${API_BASE_URL}/admin/leads/${id}/assignment`,
        convert: (id: number) => `${API_BASE_URL}/admin/leads/${id}/convert`,
    },
    tickets: {
        list: (query = "") =>
            `${API_BASE_URL}/admin/tickets${query ? `?${query}` : ""}`,
        get: (id: number) => `${API_BASE_URL}/admin/tickets/${id}`,
        reply: (id: number) => `${API_BASE_URL}/admin/tickets/${id}/reply`,
        notes: (id: number) => `${API_BASE_URL}/admin/tickets/${id}/notes`,
        queues: () => `${API_BASE_URL}/admin/ticket-queues`,
        attachments: {
            download: (id: number) =>
                `${API_BASE_URL}/admin/ticket-attachments/${id}/download`,
        },
        operations: {
            options: (id: number) =>
                `${API_BASE_URL}/admin/tickets/${id}/operations`,
            assignment: (id: number) =>
                `${API_BASE_URL}/admin/tickets/${id}/assignment`,
            status: (id: number) =>
                `${API_BASE_URL}/admin/tickets/${id}/status`,
            priority: (id: number) =>
                `${API_BASE_URL}/admin/tickets/${id}/priority`,
            queue: (id: number) => `${API_BASE_URL}/admin/tickets/${id}/queue`,
        },
        settings: {
            runtime: () => `${API_BASE_URL}/admin/settings/ticketing/runtime`,
            graphConnections: () =>
                `${API_BASE_URL}/admin/settings/ticketing/graph-connections`,
            mailboxes: () =>
                `${API_BASE_URL}/admin/settings/ticketing/mailboxes`,
            vendors: () => `${API_BASE_URL}/admin/settings/ticketing/vendors`,
            vendorEnabled: (id: number) =>
                `${API_BASE_URL}/admin/settings/ticketing/vendors/${id}/enabled`,
            vendorRules: () =>
                `${API_BASE_URL}/admin/settings/ticketing/vendor-sender-rules`,
            vendorRuleEnabled: (id: number) =>
                `${API_BASE_URL}/admin/settings/ticketing/vendor-sender-rules/${id}/enabled`,
        },
    },
    credentials: {
        list: () => `${API_BASE_URL}/admin/credentials`,
    },
    knowledgeBase: {
        list: () => `${API_BASE_URL}/admin/knowledge-base`,
    },
    infrastructure: {
        summary: () => `${API_BASE_URL}/admin/infrastructure/summary`,
        servers: () => `${API_BASE_URL}/admin/infrastructure/servers`,
        databases: () => `${API_BASE_URL}/admin/infrastructure/databases`,
        websites: () => `${API_BASE_URL}/admin/infrastructure/websites`,
        domains: () => `${API_BASE_URL}/admin/infrastructure/domains`,
        licences: () => `${API_BASE_URL}/admin/infrastructure/licences`,
        sslCertificates: () =>
            `${API_BASE_URL}/admin/infrastructure/ssl-certificates`,
        applications: () => `${API_BASE_URL}/admin/infrastructure/applications`,
        mobileApps: () => `${API_BASE_URL}/admin/infrastructure/mobile-apps`,
        apis: () => `${API_BASE_URL}/admin/infrastructure/apis`,
        bots: () => `${API_BASE_URL}/admin/infrastructure/bots`,
        emailSystems: () =>
            `${API_BASE_URL}/admin/infrastructure/email-systems`,
        techStack: () => `${API_BASE_URL}/admin/infrastructure/tech-stack`,
    },
    website: {
        portfolio: {
            list: () => `${API_BASE_URL}/admin/website/portfolio`,
            get: (id: number) =>
                `${API_BASE_URL}/admin/website/portfolio/${id}`,
            create: () => `${API_BASE_URL}/admin/website/portfolio`,
            update: (id: number) =>
                `${API_BASE_URL}/admin/website/portfolio/${id}`,
            delete: (id: number) =>
                `${API_BASE_URL}/admin/website/portfolio/${id}`,
        },
        testimonials: {
            list: () => `${API_BASE_URL}/admin/website/testimonials`,
            get: (id: number) =>
                `${API_BASE_URL}/admin/website/testimonials/${id}`,
            create: () => `${API_BASE_URL}/admin/website/testimonials`,
            update: (id: number) =>
                `${API_BASE_URL}/admin/website/testimonials/${id}`,
            delete: (id: number) =>
                `${API_BASE_URL}/admin/website/testimonials/${id}`,
        },
        blog: {
            posts: {
                list: () => `${API_BASE_URL}/admin/website/blog/posts`,
                get: (id: number) =>
                    `${API_BASE_URL}/admin/website/blog/posts/${id}`,
                create: () => `${API_BASE_URL}/admin/website/blog/posts`,
                update: (id: number) =>
                    `${API_BASE_URL}/admin/website/blog/posts/${id}`,
                delete: (id: number) =>
                    `${API_BASE_URL}/admin/website/blog/posts/${id}`,
            },
            categories: {
                list: () => `${API_BASE_URL}/admin/website/blog/categories`,
                create: () => `${API_BASE_URL}/admin/website/blog/categories`,
                update: (id: number) =>
                    `${API_BASE_URL}/admin/website/blog/categories/${id}`,
                delete: (id: number) =>
                    `${API_BASE_URL}/admin/website/blog/categories/${id}`,
            },
            tags: {
                list: () => `${API_BASE_URL}/admin/website/blog/tags`,
                create: () => `${API_BASE_URL}/admin/website/blog/tags`,
                update: (id: number) =>
                    `${API_BASE_URL}/admin/website/blog/tags/${id}`,
                delete: (id: number) =>
                    `${API_BASE_URL}/admin/website/blog/tags/${id}`,
            },
        },
        faqs: {
            list: () => `${API_BASE_URL}/admin/website/faqs`,
            create: () => `${API_BASE_URL}/admin/website/faqs`,
            update: (id: number) => `${API_BASE_URL}/admin/website/faqs/${id}`,
            delete: (id: number) => `${API_BASE_URL}/admin/website/faqs/${id}`,
            categories: {
                list: () => `${API_BASE_URL}/admin/website/faqs/categories`,
                create: () => `${API_BASE_URL}/admin/website/faqs/categories`,
                update: (id: number) =>
                    `${API_BASE_URL}/admin/website/faqs/categories/${id}`,
                delete: (id: number) =>
                    `${API_BASE_URL}/admin/website/faqs/categories/${id}`,
            },
        },
    },
};
