const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const AdminAPI = {
    brands: {
        list: () => `${API_BASE_URL}/admin/brands`,
    },
    clients: {
        list: () => `${API_BASE_URL}/admin/clients/`,
        get: (id: number) => `${API_BASE_URL}/admin/clients/${id}/`,
        create: () => `${API_BASE_URL}/admin/clients/`,
        update: (id: number) => `${API_BASE_URL}/admin/clients/${id}/`,
        delete: (id: number) => `${API_BASE_URL}/admin/clients/${id}/`,
    },
    projects: {
        list: () => `${API_BASE_URL}/admin/projects/`,
        get: (id: number) => `${API_BASE_URL}/admin/projects/${id}/`,
    },
    timeEntries: {
        list: () => `${API_BASE_URL}/admin/time-entries/`,
        create: () => `${API_BASE_URL}/admin/time-entries/`,
    },
    leads: {
        list: () => `${API_BASE_URL}/admin/leads/`,
    },
    website: {
        portfolio: {
            list: () => `${API_BASE_URL}/admin/website/portfolio`,
            get: (id: number) => `${API_BASE_URL}/admin/website/portfolio/${id}`,
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
