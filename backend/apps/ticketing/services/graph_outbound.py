from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import quote

import requests

from apps.ticketing.models import Mailbox
from apps.ticketing.services.graph import (
    GRAPH_API_ROOT,
    MicrosoftGraphError,
    MicrosoftGraphPayloadError,
)

AccessTokenProvider = Callable[[], str]


@dataclass(frozen=True, slots=True)
class GraphReplyReceipt:
    provider_message_id: str
    internet_message_id: str
    provider_conversation_id: str


class MicrosoftGraphOutboundAdapter:
    """Create, update and send threaded Microsoft Graph reply drafts."""

    def __init__(
        self,
        access_token_provider: AccessTokenProvider,
        *,
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self._access_token_provider = access_token_provider
        self._session = session or requests.Session()
        self._timeout_seconds = timeout_seconds

    def send_reply(
        self,
        mailbox: Mailbox,
        source_provider_message_id: str,
        *,
        ticket_reference: str,
        ticket_subject: str,
        body_html: str = "",
        body_text: str = "",
        cc_recipients: Sequence[str] = (),
        bcc_recipients: Sequence[str] = (),
    ) -> GraphReplyReceipt:
        """Reply to an existing Graph message while retaining provider threading."""
        source_message_id = source_provider_message_id.strip()
        if not source_message_id:
            raise MicrosoftGraphError("A provider message ID is required to send a Graph reply.")

        body_content = body_html.strip() or body_text.strip()
        if not body_content:
            raise MicrosoftGraphError("A reply body is required.")
        content_type = "HTML" if body_html.strip() else "Text"

        mailbox_identifier = quote(mailbox.graph_user_id or mailbox.email_address, safe="")
        encoded_message_id = quote(source_message_id, safe="")
        message_root = f"{GRAPH_API_ROOT}/users/{mailbox_identifier}/messages"
        draft = self._request_json(
            "post",
            f"{message_root}/{encoded_message_id}/createReply",
            json={
                "message": {
                    "body": {
                        "contentType": content_type,
                        "content": body_content,
                    }
                }
            },
            expected_statuses=(200, 201),
        )
        draft_id = str(draft.get("id") or "").strip()
        if not draft_id:
            raise MicrosoftGraphPayloadError("Microsoft Graph reply draft contained no message ID.")

        patch_payload: dict[str, Any] = {
            "subject": self._reply_subject(ticket_reference, ticket_subject),
        }
        normalised_cc = self._normalise_recipients(cc_recipients)
        normalised_bcc = self._normalise_recipients(bcc_recipients)
        if normalised_cc:
            patch_payload["ccRecipients"] = self._recipient_payload(normalised_cc)
        if normalised_bcc:
            patch_payload["bccRecipients"] = self._recipient_payload(normalised_bcc)

        encoded_draft_id = quote(draft_id, safe="")
        self._request_json(
            "patch",
            f"{message_root}/{encoded_draft_id}",
            json=patch_payload,
            expected_statuses=(200,),
        )
        self._request_no_content(
            "post",
            f"{message_root}/{encoded_draft_id}/send",
            expected_statuses=(202,),
        )

        return GraphReplyReceipt(
            provider_message_id=draft_id,
            internet_message_id=str(draft.get("internetMessageId") or "").strip(),
            provider_conversation_id=str(draft.get("conversationId") or "").strip(),
        )

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any],
        expected_statuses: tuple[int, ...],
    ) -> dict[str, Any]:
        response = self._request(method, url, json=json)
        if response.status_code not in expected_statuses:
            self._raise_response_error(response)
        try:
            payload = response.json()
        except ValueError as exc:
            raise MicrosoftGraphPayloadError(
                "Microsoft Graph returned a non-JSON outbound mail response."
            ) from exc
        if not isinstance(payload, dict):
            raise MicrosoftGraphPayloadError(
                "Microsoft Graph returned an invalid outbound mail response."
            )
        return cast(dict[str, Any], payload)

    def _request_no_content(
        self,
        method: str,
        url: str,
        *,
        expected_statuses: tuple[int, ...],
    ) -> None:
        response = self._request(method, url)
        if response.status_code not in expected_statuses:
            self._raise_response_error(response)

    def _request(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> requests.Response:
        access_token = self._access_token_provider().strip()
        if not access_token:
            raise MicrosoftGraphError("Microsoft Graph access token provider returned no token.")
        try:
            return self._session.request(
                method,
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Prefer": 'IdType="ImmutableId"',
                },
                json=json,
                timeout=self._timeout_seconds,
            )
        except requests.RequestException as exc:
            raise MicrosoftGraphError("Microsoft Graph outbound mail request failed.") from exc

    @staticmethod
    def _raise_response_error(response: requests.Response) -> None:
        request_id = response.headers.get("request-id", "unknown")
        raise MicrosoftGraphError(
            f"Microsoft Graph outbound mail request failed with status {response.status_code} "
            f"(request ID {request_id})."
        )

    @staticmethod
    def _reply_subject(ticket_reference: str, ticket_subject: str) -> str:
        reference = ticket_reference.strip()
        subject = ticket_subject.strip()
        if not reference or not subject:
            raise MicrosoftGraphError(
                "Ticket reference and subject are required for a Graph reply."
            )
        lowered = subject.lower()
        while lowered.startswith("re:"):
            subject = subject[3:].strip()
            lowered = subject.lower()
        return f"Re: [{reference}] {subject}"

    @staticmethod
    def _normalise_recipients(recipients: Sequence[str]) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(address.strip().lower() for address in recipients if address.strip())
        )

    @staticmethod
    def _recipient_payload(recipients: Sequence[str]) -> list[dict[str, dict[str, str]]]:
        return [{"emailAddress": {"address": address}} for address in recipients]
