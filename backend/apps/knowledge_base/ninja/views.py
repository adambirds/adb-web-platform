from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest
from django.utils.text import slugify
from ninja import Router

from apps.access_control.policies import scope_clients_for_user
from apps.core.ownership import OwnershipType
from apps.credentials.models import StoredCredential
from apps.credentials.policies import scope_credentials_for_user
from apps.infrastructure.models import InfrastructureResource
from apps.infrastructure.policies import scope_infrastructure_resources_for_user
from apps.knowledge_base.models import (
    DocumentVersion,
    KnowledgeBaseCredentialLink,
    KnowledgeBaseDocument,
    KnowledgeBaseResourceLink,
    KnowledgeBaseSection,
    KnowledgeBaseTag,
)
from apps.knowledge_base.ninja.schemas import (
    KnowledgeAttachmentOut,
    KnowledgeContextsOut,
    KnowledgeCredentialLinkOut,
    KnowledgeDocumentCreateIn,
    KnowledgeDocumentDetailOut,
    KnowledgeDocumentSummaryOut,
    KnowledgeDocumentUpdateIn,
    KnowledgeOptionOut,
    KnowledgeOptionsOut,
    KnowledgeResourceLinkOut,
    KnowledgeSectionCreateIn,
    KnowledgeSectionOut,
    KnowledgeSectionUpdateIn,
    KnowledgeVersionDetailOut,
    KnowledgeVersionOut,
    KnowledgeWorkspaceOut,
)
from apps.knowledge_base.services import (
    DocumentWrite,
    archive_document,
    create_document,
    restore_document,
    update_document,
)
from authentication.models import User
from authentication.ninja.schemas import ProblemDetail

knowledge_base_router = Router(tags=["admin-knowledge-base"])
StaffProblem = tuple[int, dict[str, object]]


@dataclass(frozen=True)
class ResolvedScope:
    ownership_type: str
    client_id: int | None


@dataclass(frozen=True)
class WriteDependencies:
    section: KnowledgeBaseSection
    tags: list[str]
    resources: list[InfrastructureResource]
    credentials: list[StoredCredential]


def _problem(status: int, message: str, code: str) -> StaffProblem:
    return status, {"message": message, "success": False, "code": code}


def _permission_problem(request: HttpRequest, *permissions: str) -> StaffProblem | None:
    user = request.user
    if not user.is_authenticated:
        return _problem(401, "Authentication required.", "not_authenticated")
    if not user.is_staff:
        return _problem(403, "Staff access required.", "permission_denied")
    if not all(user.has_perm(permission) for permission in permissions):
        return _problem(403, "You do not have permission for this action.", "permission_denied")
    return None


def _editor(request: HttpRequest) -> User:
    return cast(User, request.user)


def _ownership_q(request: HttpRequest) -> Q:
    return Q(ownership_type=OwnershipType.INTERNAL) | Q(
        ownership_type=OwnershipType.CLIENT,
        client__in=scope_clients_for_user(request.user),
    )


def _visible_documents(request: HttpRequest) -> QuerySet[KnowledgeBaseDocument]:
    return (
        KnowledgeBaseDocument.objects.filter(_ownership_q(request))
        .select_related("client", "section", "section__parent", "created_by", "updated_by")
        .prefetch_related("tags")
    )


def _visible_sections(request: HttpRequest) -> QuerySet[KnowledgeBaseSection]:
    return KnowledgeBaseSection.objects.filter(_ownership_q(request)).select_related(
        "client",
        "parent",
    )


def _visible_document(
    request: HttpRequest,
    document_id: int,
) -> KnowledgeBaseDocument | None:
    return _visible_documents(request).filter(id=document_id).first()


def _sections_for_scope(
    request: HttpRequest,
    scope: ResolvedScope,
) -> QuerySet[KnowledgeBaseSection]:
    sections = _visible_sections(request).filter(ownership_type=scope.ownership_type)
    if scope.client_id is None:
        return sections.filter(client__isnull=True)
    return sections.filter(client_id=scope.client_id)


def _resources_for_scope(
    request: HttpRequest,
    scope: ResolvedScope,
) -> QuerySet[InfrastructureResource]:
    resources = scope_infrastructure_resources_for_user(request.user).filter(
        ownership_type=scope.ownership_type
    )
    if scope.client_id is None:
        return resources.filter(client__isnull=True)
    return resources.filter(client_id=scope.client_id)


def _credentials_for_scope(
    request: HttpRequest,
    scope: ResolvedScope,
) -> QuerySet[StoredCredential]:
    credentials = scope_credentials_for_user(request.user).filter(
        ownership_type=scope.ownership_type
    )
    if scope.client_id is None:
        return credentials.filter(client__isnull=True)
    return credentials.filter(client_id=scope.client_id)


def _user_name(user: User | None) -> str | None:
    if user is None:
        return None
    return user.get_full_name() or user.email


def _section_out(section: KnowledgeBaseSection) -> KnowledgeSectionOut:
    return KnowledgeSectionOut(
        id=section.id,
        name=section.name,
        description=section.description,
        order=section.order,
        parent_id=section.parent_id,
        ownership_type=section.ownership_type,
        client_id=section.client_id,
        client_name=section.client.company if section.client else None,
        path=section.path,
    )


def _document_summary(document: KnowledgeBaseDocument) -> KnowledgeDocumentSummaryOut:
    annotated_count = getattr(document, "version_count", None)
    version_count = (
        annotated_count if isinstance(annotated_count, int) else document.versions.count()
    )
    return KnowledgeDocumentSummaryOut(
        id=document.id,
        title=document.title,
        summary=document.summary,
        ownership_type=document.ownership_type,
        client_id=document.client_id,
        client_name=document.client.company if document.client else None,
        section_id=document.section_id,
        section_path=document.section.path,
        tags=[tag.name for tag in document.tags.all()],
        archived=document.archived_at is not None,
        updated_at=document.updated_at,
        version_count=version_count,
    )


def _version_out(version: DocumentVersion) -> KnowledgeVersionOut:
    return KnowledgeVersionOut(
        version_number=version.version_number,
        title=version.title,
        section_path=version.section_path,
        change_summary=version.change_summary,
        editor_name=_user_name(version.editor),
        created_at=version.created_at,
    )


def _attachment_outputs(
    request: HttpRequest,
    document: KnowledgeBaseDocument,
) -> list[KnowledgeAttachmentOut]:
    if not request.user.has_perm("knowledge_base.view_knowledgebaseattachment"):
        return []
    attachments = document.attachments.select_related("uploaded_by").order_by(
        "original_name",
        "id",
    )
    return [
        KnowledgeAttachmentOut(
            id=attachment.id,
            original_name=attachment.original_name,
            content_type=attachment.content_type,
            detected_content_type=attachment.detected_content_type,
            size_bytes=attachment.size_bytes,
            scan_status=attachment.scan_status,
            uploaded_by_name=_user_name(attachment.uploaded_by),
            created_at=attachment.created_at,
        )
        for attachment in attachments
    ]


def _resource_outputs(
    request: HttpRequest,
    document: KnowledgeBaseDocument,
) -> list[KnowledgeResourceLinkOut]:
    if not request.user.has_perm("infrastructure.view_infrastructureresource"):
        return []
    visible_resources = scope_infrastructure_resources_for_user(request.user)
    links = (
        document.resource_links.filter(resource__in=visible_resources)
        .select_related("resource")
        .order_by("resource__name", "id")
    )
    return [
        KnowledgeResourceLinkOut(
            id=link.id,
            resource_id=link.resource_id,
            resource_name=link.resource.name,
            resource_type=link.resource.resource_type,
            purpose=link.purpose,
        )
        for link in links
    ]


def _credential_outputs(
    request: HttpRequest,
    document: KnowledgeBaseDocument,
) -> list[KnowledgeCredentialLinkOut]:
    if not request.user.has_perm("credentials.view_storedcredential"):
        return []
    visible_credentials = scope_credentials_for_user(request.user)
    links = (
        document.credential_links.filter(credential__in=visible_credentials)
        .select_related("credential", "credential__credential_type")
        .order_by("credential__name", "id")
    )
    return [
        KnowledgeCredentialLinkOut(
            id=link.id,
            credential_id=link.credential_id,
            credential_name=link.credential.name,
            credential_type=(
                link.credential.credential_type.name
                if link.credential.credential_type is not None
                else None
            ),
            status=link.credential.status,
            purpose=link.purpose,
        )
        for link in links
    ]


def _document_detail(
    request: HttpRequest,
    document: KnowledgeBaseDocument,
) -> KnowledgeDocumentDetailOut:
    versions = document.versions.select_related("editor").order_by(
        "-version_number",
        "-id",
    )[:50]
    summary = _document_summary(document)
    return KnowledgeDocumentDetailOut(
        **summary.model_dump(),
        content=document.content,
        is_portal_visible=document.is_portal_visible,
        created_by_name=_user_name(document.created_by),
        updated_by_name=_user_name(document.updated_by),
        created_at=document.created_at,
        versions=[_version_out(version) for version in versions],
        attachments=_attachment_outputs(request, document),
        resources=_resource_outputs(request, document),
        credentials=_credential_outputs(request, document),
    )


def _resolve_scope(
    request: HttpRequest,
    ownership_type: str,
    client_id: int | None,
) -> ResolvedScope | StaffProblem:
    if ownership_type == OwnershipType.INTERNAL:
        if client_id is not None:
            return _problem(
                400,
                "Internal documentation cannot reference a client.",
                "validation_error",
            )
        return ResolvedScope(OwnershipType.INTERNAL, None)
    if ownership_type != OwnershipType.CLIENT:
        return _problem(400, "Unknown Knowledge Base ownership type.", "validation_error")
    if client_id is None:
        return _problem(
            400,
            "Client-owned documentation requires a client.",
            "validation_error",
        )
    if not scope_clients_for_user(request.user).filter(id=client_id).exists():
        return _problem(404, "Client not found.", "not_found")
    return ResolvedScope(OwnershipType.CLIENT, client_id)


def _read_scope(
    request: HttpRequest,
    ownership_type: str | None,
    client_id: int | None,
    resource_id: int | None = None,
) -> ResolvedScope | StaffProblem:
    scope: ResolvedScope | None = None
    if ownership_type is not None or client_id is not None:
        resolved = _resolve_scope(request, ownership_type or OwnershipType.CLIENT, client_id)
        if isinstance(resolved, tuple):
            return resolved
        scope = resolved
    if resource_id is not None:
        problem = _permission_problem(request, "infrastructure.view_infrastructureresource")
        if problem:
            return problem
        resource = (
            scope_infrastructure_resources_for_user(request.user).filter(id=resource_id).first()
        )
        if resource is None:
            return _problem(404, "Infrastructure resource not found.", "not_found")
        resource_scope = ResolvedScope(resource.ownership_type, resource.client_id)
        if scope is not None and scope != resource_scope:
            return _problem(
                400, "The resource must belong to the selected Knowledge Base.", "validation_error"
            )
        scope = resource_scope
    if scope is None:
        return _problem(
            400, "Choose a Client or Internal Knowledge Base first.", "knowledge_context_required"
        )
    return scope


def _resolve_section(
    request: HttpRequest,
    section_id: int,
    scope: ResolvedScope,
) -> KnowledgeBaseSection | StaffProblem:
    section = _sections_for_scope(request, scope).filter(id=section_id).first()
    if section is None:
        return _problem(404, "Knowledge Base section not found.", "not_found")
    return section


def _resolve_resources(
    request: HttpRequest,
    resource_ids: list[int],
    scope: ResolvedScope,
) -> list[InfrastructureResource] | StaffProblem:
    ids = set(resource_ids)
    if not ids:
        return []
    problem = _permission_problem(request, "infrastructure.view_infrastructureresource")
    if problem:
        return problem
    resources = list(_resources_for_scope(request, scope).filter(id__in=ids).order_by("id"))
    if len(resources) != len(ids):
        return _problem(
            404,
            "One or more infrastructure resources were not found.",
            "not_found",
        )
    return resources


def _resolve_credentials(
    request: HttpRequest,
    credential_ids: list[int],
    scope: ResolvedScope,
) -> list[StoredCredential] | StaffProblem:
    ids = set(credential_ids)
    if not ids:
        return []
    problem = _permission_problem(request, "credentials.view_storedcredential")
    if problem:
        return problem
    credentials = list(
        _credentials_for_scope(request, scope)
        .filter(id__in=ids, status=StoredCredential.Status.ACTIVE)
        .order_by("id")
    )
    if len(credentials) != len(ids):
        return _problem(
            404,
            "One or more active credentials were not found.",
            "not_found",
        )
    return credentials


def _normalise_tag_names(tag_names: list[str]) -> list[str] | StaffProblem:
    names: list[str] = []
    seen: set[str] = set()
    for raw_name in tag_names:
        name = raw_name.strip()
        if not name:
            continue
        if len(name) > 100:
            return _problem(
                400,
                "Knowledge Base tag names are limited to 100 characters.",
                "validation_error",
            )
        key = name.casefold()
        if key not in seen:
            names.append(name)
            seen.add(key)
    if len(names) > 50:
        return _problem(400, "A document may have at most 50 tags.", "validation_error")
    return names


def _tag_for_name(name: str) -> KnowledgeBaseTag:
    existing = KnowledgeBaseTag.objects.filter(name__iexact=name).first()
    if existing is not None:
        return existing
    base = (slugify(name) or "tag")[:100]
    slug = base
    suffix = 2
    while KnowledgeBaseTag.objects.filter(slug=slug).exists():
        suffix_text = f"-{suffix}"
        slug = f"{base[: 100 - len(suffix_text)]}{suffix_text}"
        suffix += 1
    return KnowledgeBaseTag.objects.create(name=name, slug=slug)


def _sync_document_metadata(
    document: KnowledgeBaseDocument,
    *,
    tag_names: list[str],
    resources: list[InfrastructureResource] | None,
    credentials: list[StoredCredential] | None,
    editor: User,
) -> None:
    document.tags.set([_tag_for_name(name) for name in tag_names])
    if resources is not None:
        resource_ids = {resource.id for resource in resources}
        document.resource_links.exclude(resource_id__in=resource_ids).delete()
        for resource in resources:
            resource_link, created = KnowledgeBaseResourceLink.objects.get_or_create(
                document=document,
                resource=resource,
                defaults={"created_by": editor},
            )
            if created:
                resource_link.full_clean()
    if credentials is not None:
        credential_ids = {credential.id for credential in credentials}
        document.credential_links.exclude(credential_id__in=credential_ids).delete()
        for credential in credentials:
            credential_link, created = KnowledgeBaseCredentialLink.objects.get_or_create(
                document=document,
                credential=credential,
                defaults={"created_by": editor},
            )
            if created:
                credential_link.full_clean()


def _create_write_dependencies(
    request: HttpRequest,
    *,
    scope: ResolvedScope,
    section_id: int,
    tag_names: list[str],
    resource_ids: list[int],
    credential_ids: list[int],
) -> WriteDependencies | StaffProblem:
    section = _resolve_section(request, section_id, scope)
    if isinstance(section, tuple):
        return section
    tags = _normalise_tag_names(tag_names)
    if isinstance(tags, tuple):
        return tags
    resources = _resolve_resources(request, resource_ids, scope)
    if isinstance(resources, tuple):
        return resources
    credentials = _resolve_credentials(request, credential_ids, scope)
    if isinstance(credentials, tuple):
        return credentials
    return WriteDependencies(section, tags, resources, credentials)


@knowledge_base_router.get(
    "/knowledge-base/workspace",
    response={
        200: KnowledgeWorkspaceOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def knowledge_workspace(
    request: HttpRequest,
    q: str = "",
    ownership_type: str | None = None,
    client_id: int | None = None,
    section_id: int | None = None,
    resource_id: int | None = None,
    view: str = "current",
    page: int = 1,
    page_size: int = 50,
    browse: bool = False,
) -> KnowledgeWorkspaceOut | StaffProblem:
    problem = _permission_problem(request, "knowledge_base.view_knowledgebasedocument")
    if problem:
        return problem
    if view not in {"current", "archived", "all"}:
        return _problem(400, "Unknown Knowledge Base view.", "validation_error")
    scope = _read_scope(request, ownership_type, client_id, resource_id)
    if isinstance(scope, tuple):
        return scope
    documents = _visible_documents(request).filter(ownership_type=scope.ownership_type)
    documents = (
        documents.filter(client__isnull=True)
        if scope.client_id is None
        else documents.filter(client_id=scope.client_id)
    )
    documents = documents.annotate(version_count=Count("versions", distinct=True))
    sections = _sections_for_scope(request, scope)
    if section_id is not None:
        if not sections.filter(id=section_id).exists():
            return _problem(404, "Knowledge Base section not found.", "not_found")
        if not browse or not q.strip():
            documents = documents.filter(section_id=section_id)
        else:
            descendants = {section_id}
            tree = list(sections.values_list("id", "parent_id"))
            changed = True
            while changed:
                additions = {
                    folder_id for folder_id, parent_id in tree if parent_id in descendants
                }.difference(descendants)
                changed = bool(additions)
                descendants.update(additions)
            documents = documents.filter(section_id__in=descendants)
    elif browse and not q.strip():
        documents = documents.none()
    if resource_id is not None:
        documents = documents.filter(resource_links__resource_id=resource_id)

    if view == "current":
        documents = documents.filter(archived_at__isnull=True)
    elif view == "archived":
        documents = documents.filter(archived_at__isnull=False)

    query = q.strip()
    if query:
        documents = documents.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query)
            | Q(tags__name__icontains=query)
        )

    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    documents = documents.distinct().order_by("-updated_at", "-id")
    total = documents.count()
    start = (page - 1) * page_size
    rows = list(documents[start : start + page_size])
    client = (
        scope_clients_for_user(request.user).filter(id=scope.client_id).first()
        if scope.client_id
        else None
    )
    return KnowledgeWorkspaceOut(
        ownership_type=scope.ownership_type,
        client_id=scope.client_id,
        client_name=str(client) if client else None,
        sections=[_section_out(section) for section in sections.order_by("order", "name", "id")],
        documents=[_document_summary(document) for document in rows],
        total_documents=total,
        page=page,
        page_size=page_size,
    )


@knowledge_base_router.get(
    "/knowledge-base/contexts",
    response={200: KnowledgeContextsOut, 401: ProblemDetail, 403: ProblemDetail},
)
def knowledge_contexts(
    request: HttpRequest,
    q: str = "",
    page: int = 1,
    page_size: int = 25,
) -> KnowledgeContextsOut | StaffProblem:
    problem = _permission_problem(request, "knowledge_base.view_knowledgebasedocument")
    if problem:
        return problem
    clients = scope_clients_for_user(request.user)
    if q.strip():
        clients = clients.filter(Q(company__icontains=q.strip()) | Q(name__icontains=q.strip()))
    clients = clients.order_by("company", "name", "id")
    page, page_size = max(page, 1), min(max(page_size, 1), 100)
    return KnowledgeContextsOut(
        items=[
            KnowledgeOptionOut(
                id=client.id,
                label=str(client),
                ownership_type=OwnershipType.CLIENT,
                client_id=client.id,
                kind="client",
            )
            for client in clients[(page - 1) * page_size : page * page_size]
        ],
        total=clients.count(),
        page=page,
        page_size=page_size,
    )


@knowledge_base_router.get(
    "/knowledge-base/options",
    response={
        200: KnowledgeOptionsOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def knowledge_options(
    request: HttpRequest,
    ownership_type: str | None = None,
    client_id: int | None = None,
) -> KnowledgeOptionsOut | StaffProblem:
    problem = _permission_problem(request, "knowledge_base.view_knowledgebasedocument")
    if problem:
        return problem
    scope = _read_scope(request, ownership_type, client_id)
    if isinstance(scope, tuple):
        return scope
    clients = (
        scope_clients_for_user(request.user).filter(id=scope.client_id)
        if scope.client_id is not None
        else scope_clients_for_user(request.user).none()
    )
    resources: list[KnowledgeOptionOut] = []
    if request.user.has_perm("infrastructure.view_infrastructureresource"):
        resources = [
            KnowledgeOptionOut(
                id=resource.id,
                label=resource.name,
                ownership_type=resource.ownership_type,
                client_id=resource.client_id,
                kind=resource.resource_type,
            )
            for resource in _resources_for_scope(request, scope).order_by("name", "id")[:1000]
        ]
    credentials: list[KnowledgeOptionOut] = []
    if request.user.has_perm("credentials.view_storedcredential"):
        credentials = [
            KnowledgeOptionOut(
                id=credential.id,
                label=credential.name,
                ownership_type=credential.ownership_type,
                client_id=credential.client_id,
                kind=credential.credential_type.name if credential.credential_type else None,
            )
            for credential in _credentials_for_scope(request, scope)
            .filter(status=StoredCredential.Status.ACTIVE)
            .select_related("credential_type")
            .order_by("name", "id")[:1000]
        ]
    return KnowledgeOptionsOut(
        clients=[
            KnowledgeOptionOut(
                id=client.id,
                label=str(client),
                ownership_type=OwnershipType.CLIENT,
                client_id=client.id,
                kind="client",
            )
            for client in clients
        ],
        sections=[
            _section_out(section)
            for section in _sections_for_scope(request, scope).order_by("order", "name", "id")
        ],
        resources=resources,
        credentials=credentials,
    )


@knowledge_base_router.get(
    "/knowledge-base/documents/{document_id}",
    response={
        200: KnowledgeDocumentDetailOut,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def knowledge_document_detail(
    request: HttpRequest,
    document_id: int,
) -> KnowledgeDocumentDetailOut | StaffProblem:
    problem = _permission_problem(request, "knowledge_base.view_knowledgebasedocument")
    if problem:
        return problem
    document = _visible_document(request, document_id)
    if document is None:
        return _problem(404, "Knowledge Base document not found.", "not_found")
    return _document_detail(request, document)


@knowledge_base_router.get(
    "/knowledge-base/documents/{document_id}/versions/{version_number}",
    response={
        200: KnowledgeVersionDetailOut,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def knowledge_document_version(
    request: HttpRequest,
    document_id: int,
    version_number: int,
) -> KnowledgeVersionDetailOut | StaffProblem:
    problem = _permission_problem(request, "knowledge_base.view_knowledgebasedocument")
    if problem:
        return problem
    document = _visible_document(request, document_id)
    if document is None:
        return _problem(404, "Knowledge Base document not found.", "not_found")
    version = (
        document.versions.select_related("editor").filter(version_number=version_number).first()
    )
    if version is None:
        return _problem(404, "Knowledge Base document version not found.", "not_found")
    base = _version_out(version)
    return KnowledgeVersionDetailOut(**base.model_dump(), content=version.content)


@knowledge_base_router.post(
    "/knowledge-base/sections",
    response={
        201: KnowledgeSectionOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_knowledge_section(
    request: HttpRequest,
    payload: KnowledgeSectionCreateIn,
) -> tuple[int, KnowledgeSectionOut | dict[str, object]]:
    problem = _permission_problem(request, "knowledge_base.add_knowledgebasesection")
    if problem:
        return problem
    scope = _resolve_scope(request, payload.ownership_type, payload.client_id)
    if isinstance(scope, tuple):
        return scope
    parent: KnowledgeBaseSection | None = None
    if payload.parent_id is not None:
        resolved_parent = _resolve_section(request, payload.parent_id, scope)
        if isinstance(resolved_parent, tuple):
            return resolved_parent
        parent = resolved_parent
    section = KnowledgeBaseSection(
        ownership_type=scope.ownership_type,
        client_id=scope.client_id,
        parent=parent,
        name=payload.name.strip(),
        description=payload.description.strip(),
        order=payload.order,
    )
    try:
        section.full_clean()
        section.save()
    except ValidationError as error:
        return _problem(400, "; ".join(error.messages), "validation_error")
    return 201, _section_out(section)


@knowledge_base_router.put(
    "/knowledge-base/sections/{section_id}",
    response={
        200: KnowledgeSectionOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_knowledge_section(
    request: HttpRequest,
    section_id: int,
    payload: KnowledgeSectionUpdateIn,
) -> KnowledgeSectionOut | StaffProblem:
    problem = _permission_problem(request, "knowledge_base.change_knowledgebasesection")
    if problem:
        return problem
    section = _visible_sections(request).filter(id=section_id).first()
    if section is None:
        return _problem(404, "Knowledge Base section not found.", "not_found")
    scope = ResolvedScope(section.ownership_type, section.client_id)
    parent: KnowledgeBaseSection | None = None
    if payload.parent_id is not None:
        resolved_parent = _resolve_section(request, payload.parent_id, scope)
        if isinstance(resolved_parent, tuple):
            return resolved_parent
        parent = resolved_parent
    section.parent = parent
    section.name = payload.name.strip()
    section.description = payload.description.strip()
    section.order = payload.order
    try:
        section.full_clean()
        section.save()
    except ValidationError as error:
        return _problem(400, "; ".join(error.messages), "validation_error")
    return _section_out(section)


@knowledge_base_router.post(
    "/knowledge-base/documents",
    response={
        201: KnowledgeDocumentDetailOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_knowledge_document(
    request: HttpRequest,
    payload: KnowledgeDocumentCreateIn,
) -> tuple[int, KnowledgeDocumentDetailOut | dict[str, object]]:
    problem = _permission_problem(request, "knowledge_base.add_knowledgebasedocument")
    if problem:
        return problem
    scope = _resolve_scope(request, payload.ownership_type, payload.client_id)
    if isinstance(scope, tuple):
        return scope
    dependencies = _create_write_dependencies(
        request,
        scope=scope,
        section_id=payload.section_id,
        tag_names=payload.tag_names,
        resource_ids=payload.resource_ids,
        credential_ids=payload.credential_ids,
    )
    if isinstance(dependencies, tuple):
        return dependencies

    editor = _editor(request)
    try:
        with transaction.atomic():
            document = create_document(
                write=DocumentWrite(
                    ownership_type=scope.ownership_type,
                    client_id=scope.client_id,
                    title=payload.title,
                    summary=payload.summary,
                    section=dependencies.section,
                    content=payload.content,
                ),
                editor=editor,
            )
            _sync_document_metadata(
                document,
                tag_names=dependencies.tags,
                resources=dependencies.resources,
                credentials=dependencies.credentials,
                editor=editor,
            )
    except ValidationError as error:
        return _problem(400, "; ".join(error.messages), "validation_error")
    refreshed = _visible_document(request, document.id)
    if refreshed is None:
        return _problem(404, "Knowledge Base document not found.", "not_found")
    return 201, _document_detail(request, refreshed)


@knowledge_base_router.put(
    "/knowledge-base/documents/{document_id}",
    response={
        200: KnowledgeDocumentDetailOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_knowledge_document(
    request: HttpRequest,
    document_id: int,
    payload: KnowledgeDocumentUpdateIn,
) -> KnowledgeDocumentDetailOut | StaffProblem:
    problem = _permission_problem(request, "knowledge_base.change_knowledgebasedocument")
    if problem:
        return problem
    current = _visible_document(request, document_id)
    if current is None:
        return _problem(404, "Knowledge Base document not found.", "not_found")
    scope = ResolvedScope(current.ownership_type, current.client_id)

    section = _resolve_section(request, payload.section_id, scope)
    if isinstance(section, tuple):
        return section
    tags = _normalise_tag_names(payload.tag_names)
    if isinstance(tags, tuple):
        return tags

    resources: list[InfrastructureResource] | None = None
    if payload.resource_ids is not None:
        resolved_resources = _resolve_resources(request, payload.resource_ids, scope)
        if isinstance(resolved_resources, tuple):
            return resolved_resources
        resources = resolved_resources

    credentials: list[StoredCredential] | None = None
    if payload.credential_ids is not None:
        resolved_credentials = _resolve_credentials(request, payload.credential_ids, scope)
        if isinstance(resolved_credentials, tuple):
            return resolved_credentials
        credentials = resolved_credentials

    editor = _editor(request)
    try:
        with transaction.atomic():
            document = update_document(
                document_id,
                write=DocumentWrite(
                    ownership_type=scope.ownership_type,
                    client_id=scope.client_id,
                    title=payload.title,
                    summary=payload.summary,
                    section=section,
                    content=payload.content,
                    is_portal_visible=current.is_portal_visible,
                    change_summary=payload.change_summary,
                ),
                editor=editor,
            )
            _sync_document_metadata(
                document,
                tag_names=tags,
                resources=resources,
                credentials=credentials,
                editor=editor,
            )
    except ValidationError as error:
        return _problem(400, "; ".join(error.messages), "validation_error")
    refreshed = _visible_document(request, document_id)
    if refreshed is None:
        return _problem(404, "Knowledge Base document not found.", "not_found")
    return _document_detail(request, refreshed)


@knowledge_base_router.post(
    "/knowledge-base/documents/{document_id}/archive",
    response={
        200: KnowledgeDocumentDetailOut,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def archive_knowledge_document(
    request: HttpRequest,
    document_id: int,
) -> KnowledgeDocumentDetailOut | StaffProblem:
    problem = _permission_problem(request, "knowledge_base.change_knowledgebasedocument")
    if problem:
        return problem
    document = _visible_document(request, document_id)
    if document is None:
        return _problem(404, "Knowledge Base document not found.", "not_found")
    archive_document(document.id, editor=_editor(request))
    refreshed = _visible_document(request, document_id)
    if refreshed is None:
        return _problem(404, "Knowledge Base document not found.", "not_found")
    return _document_detail(request, refreshed)


@knowledge_base_router.post(
    "/knowledge-base/documents/{document_id}/restore",
    response={
        200: KnowledgeDocumentDetailOut,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def restore_knowledge_document(
    request: HttpRequest,
    document_id: int,
) -> KnowledgeDocumentDetailOut | StaffProblem:
    problem = _permission_problem(request, "knowledge_base.change_knowledgebasedocument")
    if problem:
        return problem
    document = _visible_document(request, document_id)
    if document is None:
        return _problem(404, "Knowledge Base document not found.", "not_found")
    restore_document(document.id, editor=_editor(request))
    refreshed = _visible_document(request, document_id)
    if refreshed is None:
        return _problem(404, "Knowledge Base document not found.", "not_found")
    return _document_detail(request, refreshed)
