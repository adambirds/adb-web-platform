export interface KnowledgeSection {
    id: number;
    name: string;
    description: string;
    order: number;
    parent_id: number | null;
    ownership_type: string;
    client_id: number | null;
    client_name: string | null;
    path: string;
}

export interface KnowledgeDocumentSummary {
    id: number;
    title: string;
    summary: string;
    ownership_type: string;
    client_id: number | null;
    client_name: string | null;
    section_id: number;
    section_path: string;
    tags: string[];
    archived: boolean;
    updated_at: string;
    version_count: number;
}

export interface KnowledgeVersion {
    version_number: number;
    title: string;
    section_path: string;
    change_summary: string;
    editor_name: string | null;
    created_at: string;
}

export interface KnowledgeVersionDetail extends KnowledgeVersion {
    content: string;
}

export interface KnowledgeAttachment {
    id: number;
    original_name: string;
    content_type: string;
    detected_content_type: string;
    size_bytes: number;
    scan_status: string;
    uploaded_by_name: string | null;
    created_at: string;
}

export interface KnowledgeResourceLink {
    id: number;
    resource_id: number;
    resource_name: string;
    resource_type: string;
    purpose: string;
}

export interface KnowledgeCredentialLink {
    id: number;
    credential_id: number;
    credential_name: string;
    credential_type: string | null;
    status: string;
    purpose: string;
}

export interface KnowledgeDocumentDetail extends KnowledgeDocumentSummary {
    content: string;
    is_portal_visible: boolean;
    created_by_name: string | null;
    updated_by_name: string | null;
    created_at: string;
    versions: KnowledgeVersion[];
    attachments: KnowledgeAttachment[];
    resources: KnowledgeResourceLink[];
    credentials: KnowledgeCredentialLink[];
}

export interface KnowledgeWorkspaceResponse {
    ownership_type: "internal" | "client";
    client_id: number | null;
    client_name: string | null;
    sections: KnowledgeSection[];
    documents: KnowledgeDocumentSummary[];
    total_documents: number;
    page: number;
    page_size: number;
}

export interface KnowledgeOption {
    id: number;
    label: string;
    ownership_type: string | null;
    client_id: number | null;
    kind: string | null;
}

export interface KnowledgeOptionsResponse {
    clients: KnowledgeOption[];
    sections: KnowledgeSection[];
    resources: KnowledgeOption[];
    credentials: KnowledgeOption[];
}
