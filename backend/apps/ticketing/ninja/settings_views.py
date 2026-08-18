from typing import Any

from django.http import HttpRequest
from ninja import Router, Schema

from apps.core.models import Brand
from apps.credentials.models import StoredCredential
from apps.ticketing.models import Mailbox, MicrosoftGraphConnection, TicketQueue
from authentication.ninja.schemas import ProblemDetail

from .schemas import GraphConnectionOut, MailboxOut

ticketing_settings_router = Router(tags=["admin-ticketing-settings"])

StaffProblem = tuple[int, dict[str, Any]]


class GraphConnectionIn(Schema):
    name: str
    tenant_id: str
    client_id: str
    authentication_method: str = MicrosoftGraphConnection.AuthenticationMethod.CERTIFICATE
    credential_id: int | None = None
    enabled: bool = True


class MailboxIn(Schema):
    graph_connection_id: int
    email_address: str
    display_name: str = ""
    graph_user_id: str = ""
    brand_id: int
    purpose: str = Mailbox.Purpose.SUPPORT
    default_queue_id: int
    enabled: bool = True


def _staff_problem(request: HttpRequest) -> StaffProblem | None:
    if not request.user.is_authenticated:
        return 401, {
            "message": "User not authenticated",
            "success": False,
            "code": "unauthenticated",
        }
    if not (request.user.is_staff or request.user.is_superuser):
        return 403, {
            "message": "You do not have permission to access this resource.",
            "success": False,
            "code": "forbidden",
        }
    return None


def _problem(message: str, code: str = "invalid") -> StaffProblem:
    return 400, {"message": message, "success": False, "code": code}


def _connection_out(connection: MicrosoftGraphConnection) -> GraphConnectionOut:
    return GraphConnectionOut(
        id=connection.id,
        name=connection.name,
        tenant_id=connection.tenant_id,
        client_id=connection.client_id,
        authentication_method=connection.authentication_method,
        credential_id=connection.credential_id,
        credential_name=connection.credential.name if connection.credential else None,
        enabled=connection.enabled,
        last_verified_at=connection.last_verified_at,
        last_error=connection.last_error,
    )


def _mailbox_out(mailbox: Mailbox) -> MailboxOut:
    return MailboxOut(
        id=mailbox.id,
        email_address=mailbox.email_address,
        display_name=mailbox.display_name,
        graph_connection_id=mailbox.graph_connection_id,
        graph_connection_name=mailbox.graph_connection.name,
        brand_id=mailbox.brand_id,
        brand_name=mailbox.brand.name,
        purpose=mailbox.purpose,
        default_queue_id=mailbox.default_queue_id,
        default_queue_name=mailbox.default_queue.name,
        enabled=mailbox.enabled,
        last_synced_at=mailbox.last_synced_at,
        last_successful_sync_at=mailbox.last_successful_sync_at,
        last_error=mailbox.last_error,
    )


def _resolve_credential(credential_id: int | None) -> StoredCredential | None | StaffProblem:
    if credential_id is None:
        return None
    credential = StoredCredential.objects.filter(id=credential_id).first()
    if credential is None:
        return _problem("Credential not found.", "credential_not_found")
    if credential.ownership_type != "internal":
        return _problem(
            "Microsoft Graph authentication credentials must be internal credentials.",
            "invalid_credential_scope",
        )
    return credential


def _resolve_mailbox_relations(data: MailboxIn) -> tuple[Any, ...] | StaffProblem:
    connection = MicrosoftGraphConnection.objects.filter(id=data.graph_connection_id).first()
    if connection is None:
        return _problem("Microsoft Graph connection not found.", "connection_not_found")
    brand = Brand.objects.filter(id=data.brand_id, is_active=True).first()
    if brand is None:
        return _problem("Active brand not found.", "brand_not_found")
    queue = TicketQueue.objects.filter(id=data.default_queue_id, enabled=True).first()
    if queue is None:
        return _problem("Enabled ticket queue not found.", "queue_not_found")
    if queue.brand_id is not None and queue.brand_id != brand.id:
        return _problem("The default queue must belong to the selected brand.", "queue_brand_mismatch")
    return connection, brand, queue


@ticketing_settings_router.get(
    "/settings/ticketing/graph-connections",
    response={200: list[GraphConnectionOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_graph_connections(request: HttpRequest) -> list[GraphConnectionOut] | StaffProblem:
    problem = _staff_problem(request)
    if problem:
        return problem
    if not request.user.has_perm("ticketing.view_microsoftgraphconnection"):
        return 403, {
            "message": "You do not have permission to view Graph connections.",
            "success": False,
            "code": "forbidden",
        }
    connections = MicrosoftGraphConnection.objects.select_related("credential").order_by("name")
    return [_connection_out(connection) for connection in connections]


@ticketing_settings_router.post(
    "/settings/ticketing/graph-connections",
    response={200: GraphConnectionOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail},
)
def create_graph_connection(
    request: HttpRequest,
    data: GraphConnectionIn,
) -> GraphConnectionOut | StaffProblem:
    problem = _staff_problem(request)
    if problem:
        return problem
    if not request.user.has_perm("ticketing.configure_graph_connections"):
        return 403, {
            "message": "You do not have permission to configure Graph connections.",
            "success": False,
            "code": "forbidden",
        }
    if data.authentication_method not in MicrosoftGraphConnection.AuthenticationMethod.values:
        return _problem("Unsupported Microsoft Graph authentication method.")

    credential = _resolve_credential(data.credential_id)
    if isinstance(credential, tuple):
        return credential

    connection = MicrosoftGraphConnection.objects.create(
        name=data.name.strip(),
        tenant_id=data.tenant_id.strip(),
        client_id=data.client_id.strip(),
        authentication_method=data.authentication_method,
        credential=credential,
        enabled=data.enabled,
    )
    return _connection_out(connection)


@ticketing_settings_router.get(
    "/settings/ticketing/mailboxes",
    response={200: list[MailboxOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_mailboxes(request: HttpRequest) -> list[MailboxOut] | StaffProblem:
    problem = _staff_problem(request)
    if problem:
        return problem
    if not request.user.has_perm("ticketing.view_mailbox"):
        return 403, {
            "message": "You do not have permission to view ticket mailboxes.",
            "success": False,
            "code": "forbidden",
        }
    mailboxes = Mailbox.objects.select_related(
        "graph_connection",
        "brand",
        "default_queue",
    ).order_by("brand__name", "email_address")
    return [_mailbox_out(mailbox) for mailbox in mailboxes]


@ticketing_settings_router.post(
    "/settings/ticketing/mailboxes",
    response={200: MailboxOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail},
)
def create_mailbox(request: HttpRequest, data: MailboxIn) -> MailboxOut | StaffProblem:
    problem = _staff_problem(request)
    if problem:
        return problem
    if not request.user.has_perm("ticketing.configure_mailboxes"):
        return 403, {
            "message": "You do not have permission to configure ticket mailboxes.",
            "success": False,
            "code": "forbidden",
        }
    if data.purpose not in Mailbox.Purpose.values:
        return _problem("Unsupported mailbox purpose.")

    relations = _resolve_mailbox_relations(data)
    if len(relations) == 2 and isinstance(relations[0], int):
        return relations  # type: ignore[return-value]
    connection, brand, queue = relations

    mailbox = Mailbox.objects.create(
        graph_connection=connection,
        email_address=data.email_address.strip().lower(),
        display_name=data.display_name.strip(),
        graph_user_id=data.graph_user_id.strip(),
        brand=brand,
        purpose=data.purpose,
        default_queue=queue,
        enabled=data.enabled,
    )
    return _mailbox_out(mailbox)
