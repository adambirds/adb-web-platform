from datetime import datetime

from ninja import Schema
from pydantic import Field


class KnowledgeSectionOut(Schema):
    id: int
    name: str
    description: str
    order: int
    parent_id: int | None
    ownership_type: str
    client_id: int | None
    client_name: str | None
    path: str


class KnowledgeDocumentSummaryOut(Schema):
    id: int
    title: str
    summary: str
    ownership_type: str
    client_id: int | None
    client_name: str | None
    section_id: int
    section_path: str
    tags: list[str]
    archived: bool
    updated_at: datetime
    version_count: int


class KnowledgeVersionOut(Schema):
    version_number: int
    title: str
    section_path: str
    change_summary: str
    editor_name: str | None
    created_at: datetime


class KnowledgeVersionDetailOut(KnowledgeVersionOut):
    content: str


class KnowledgeAttachmentOut(Schema):
    id: int
    original_name: str
    content_type: str
    detected_content_type: str
    size_bytes: int
    scan_status: str
    uploaded_by_name: str | None
    created_at: datetime


class KnowledgeResourceLinkOut(Schema):
    id: int
    resource_id: int
    resource_name: str
    resource_type: str
    purpose: str


class KnowledgeCredentialLinkOut(Schema):
    id: int
    credential_id: int
    credential_name: str
    credential_type: str | None
    status: str
    purpose: str


class KnowledgeDocumentDetailOut(KnowledgeDocumentSummaryOut):
    content: str
    is_portal_visible: bool
    created_by_name: str | None
    updated_by_name: str | None
    created_at: datetime
    versions: list[KnowledgeVersionOut]
    attachments: list[KnowledgeAttachmentOut]
    resources: list[KnowledgeResourceLinkOut]
    credentials: list[KnowledgeCredentialLinkOut]


class KnowledgeWorkspaceOut(Schema):
    ownership_type: str
    client_id: int | None
    client_name: str | None
    sections: list[KnowledgeSectionOut]
    documents: list[KnowledgeDocumentSummaryOut]
    total_documents: int
    page: int
    page_size: int


class KnowledgeSectionCreateIn(Schema):
    ownership_type: str
    client_id: int | None = None
    parent_id: int | None = None
    name: str
    description: str = ""
    order: int = 0


class KnowledgeSectionUpdateIn(Schema):
    parent_id: int | None = None
    name: str
    description: str = ""
    order: int = 0


class KnowledgeDocumentCreateIn(Schema):
    ownership_type: str
    client_id: int | None = None
    title: str
    summary: str = ""
    section_id: int
    content: str = ""
    tag_names: list[str] = Field(default_factory=list)
    resource_ids: list[int] = Field(default_factory=list)
    credential_ids: list[int] = Field(default_factory=list)


class KnowledgeDocumentUpdateIn(Schema):
    title: str
    summary: str = ""
    section_id: int
    content: str
    change_summary: str = ""
    tag_names: list[str] = Field(default_factory=list)
    resource_ids: list[int] | None = None
    credential_ids: list[int] | None = None


class KnowledgeOptionOut(Schema):
    id: int
    label: str
    ownership_type: str | None = None
    client_id: int | None = None
    kind: str | None = None


class KnowledgeOptionsOut(Schema):
    clients: list[KnowledgeOptionOut]
    sections: list[KnowledgeSectionOut]
    resources: list[KnowledgeOptionOut]
    credentials: list[KnowledgeOptionOut]


class KnowledgeContextsOut(Schema):
    items: list[KnowledgeOptionOut]
    total: int
    page: int
    page_size: int
