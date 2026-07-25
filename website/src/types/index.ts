// Website Types
export interface Portfolio {
    id: number;
    title: string;
    slug: string;
    description: string;
    challenge: string;
    solution: string;
    results: string;
    image?: string;
    featured: boolean;
    featured_image?: string;
    technologies: string;
    project_url?: string;
    github_url?: string;
    created_at: string;
    updated_at: string;
}

export interface Testimonial {
    id: number;
    quote: string;
    client_name: string;
    company: string;
    job_title: string;
    rating: 1 | 2 | 3 | 4 | 5;
    image?: string;
    featured: boolean;
    created_at: string;
}

export interface BlogPost {
    id: number;
    title: string;
    slug: string;
    excerpt: string;
    content: string;
    featured_image?: string;
    author: string;
    published: boolean;
    featured: boolean;
    categories: BlogCategory[];
    tags: BlogTag[];
    meta_description: string;
    meta_keywords: string;
    created_at: string;
    published_at?: string;
    updated_at: string;
}

export interface BlogCategory {
    id: number;
    name: string;
    slug: string;
    description: string;
}

export interface BlogTag {
    id: number;
    name: string;
    slug: string;
}

export interface FAQ {
    id: number;
    question: string;
    answer: string;
    category: FAQCategory;
    order: number;
}

export interface FAQCategory {
    id: number;
    name: string;
    slug: string;
    description: string;
    order: number;
}

// Client Management Types
export interface Client {
    id: number;
    name: string;
    company: string;
    email: string;
    phone: string;
    address: string;
    city: string;
    state: string;
    country: string;
    postal_code: string;
    status: "active" | "inactive" | "archived";
    notes: string;
    created_at: string;
    updated_at: string;
}

export interface Project {
    id: number;
    client_id: number;
    name: string;
    description: string;
    status: "planning" | "active" | "paused" | "completed" | "archived";
    start_date: string;
    end_date?: string;
    budget?: number;
    hourly_rate?: number;
    created_at: string;
    updated_at: string;
}

export interface TimeEntry {
    id: number;
    project_id: number;
    date: string;
    duration_hours: number;
    description: string;
    billable: boolean;
    created_at: string;
    updated_at: string;
}

// Lead Types
export interface Lead {
    id: number;
    name: string;
    email: string;
    phone: string;
    company: string;
    status_id?: number;
    source_id?: number;
    message: string;
    notes: string;
    created_at: string;
    updated_at: string;
}
