from __future__ import annotations

from typing import Any, cast
from urllib.parse import quote

import requests

from apps.ticketing.models import MicrosoftGraphConnection
from apps.ticketing.services.graph import (
    GRAPH_API_ROOT,
    MicrosoftGraphError,
    MicrosoftGraphPayloadError,
)
from apps.ticketing.services.graph_auth import (
    MicrosoftGraphAuthenticationError,
    MicrosoftGraphTokenProvider,
)


def verify_graph_mailbox_access(
    connection: MicrosoftGraphConnection,
    email_address: str,
    *,
    session: requests.Session | None = None,
    timeout_seconds: int = 30,
) -> None:
    """Verify that the configured Graph application can read a mailbox Inbox."""
    normalised_address = email_address.strip().lower()
    if not normalised_address:
        raise MicrosoftGraphError("Shared mailbox email address is required.")

    graph_session = session or requests.Session()
    token_provider = MicrosoftGraphTokenProvider(
        connection,
        session=graph_session,
        timeout_seconds=timeout_seconds,
    )
    try:
        access_token = token_provider.get_access_token().strip()
    except MicrosoftGraphAuthenticationError as exc:
        raise MicrosoftGraphError("Microsoft Graph application authentication failed.") from exc

    if not access_token:
        raise MicrosoftGraphError("Microsoft Graph access token provider returned no token.")

    mailbox_identifier = quote(normalised_address, safe="")
    request_url = f"{GRAPH_API_ROOT}/users/{mailbox_identifier}/mailFolders/inbox"
    try:
        response = graph_session.get(
            request_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            params={"$select": "id"},
            timeout=timeout_seconds,
        )
    except requests.RequestException as exc:
        raise MicrosoftGraphError("Microsoft Graph mailbox verification request failed.") from exc

    if response.status_code >= 400:
        request_id = response.headers.get("request-id", "unknown")
        raise MicrosoftGraphError(
            f"Microsoft Graph mailbox verification failed with status {response.status_code} "
            f"(request ID {request_id})."
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise MicrosoftGraphPayloadError(
            "Microsoft Graph returned a non-JSON mailbox verification response."
        ) from exc
    if not isinstance(payload, dict):
        raise MicrosoftGraphPayloadError(
            "Microsoft Graph returned an invalid mailbox verification response."
        )

    typed_payload = cast(dict[str, Any], payload)
    if not str(typed_payload.get("id") or "").strip():
        raise MicrosoftGraphPayloadError(
            "Microsoft Graph mailbox verification did not return the Inbox folder."
        )
