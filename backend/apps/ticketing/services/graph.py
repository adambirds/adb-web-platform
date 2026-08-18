from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone as datetime_timezone
from typing import Any, cast
from urllib.parse import quote, urlparse

import requests
from django.utils import timezone

from apps.ticketing.models import Mailbox
from apps.ticketing.services.contracts import CanonicalMessage

GRAPH_API_ROOT = "https://graph.microsoft.com/v1.0"
GRAPH_PROVIDER = "microsoft_graph"
GRAPH_PAGE_SIZE = 50
GRAPH_MESSAGE_SELECT = (
    "id",
    "conversationId",
    "subject",
    "body",
    "from",
    "sender",
    "toRecipients",
    "ccRecipients",
    "bccRecipients",
    "receivedDateTime",
    "sentDateTime",
    "internetMessageId",
    "internetMessageHeaders",
    "hasAttachments",
    "isDraft",
)


class MicrosoftGraphError(RuntimeError):
    """Base exception for Microsoft Graph mailbox operations."""


class MicrosoftGraphPayloadError(MicrosoftGraphError):
    """Microsoft Graph returned an unusable mailbox payload."""


@dataclass(frozen=True, slots=True)
class GraphDeltaPage:
    """One page in a Graph message delta round."""

    messages: tuple[CanonicalMessage, ...]
    next_link: str
    delta_link: str


AccessTokenProvider = Callable[[], str]
MessageConsumer = Callable[[Mailbox, CanonicalMessage], None]


class MicrosoftGraphAdapter:
    """Translate Microsoft Graph mailbox data into provider-neutral messages."""

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

    def fetch_delta_page(self, mailbox: Mailbox, *, url: str = "") -> GraphDeltaPage:
        """Fetch one Inbox delta page for a configured mailbox."""
        params: dict[str, str | int] | None = None
        if url:
            request_url = self._validated_graph_url(url)
        else:
            mailbox_identifier = quote(mailbox.graph_user_id or mailbox.email_address, safe="")
            request_url = (
                f"{GRAPH_API_ROOT}/users/{mailbox_identifier}/mailFolders/inbox/messages/delta"
            )
            params = {
                "$select": ",".join(GRAPH_MESSAGE_SELECT),
                "$top": GRAPH_PAGE_SIZE,
            }

        payload = self._get_json(request_url, params=params)
        rows = payload.get("value", [])
        if not isinstance(rows, list):
            raise MicrosoftGraphPayloadError("Microsoft Graph delta response has no message list.")

        messages: list[CanonicalMessage] = []
        for row in rows:
            if not isinstance(row, dict) or "@removed" in row:
                continue
            messages.append(self._canonical_message(cast(dict[str, Any], row)))

        next_link = self._optional_link(payload, "@odata.nextLink")
        delta_link = self._optional_link(payload, "@odata.deltaLink")
        if not next_link and not delta_link:
            raise MicrosoftGraphPayloadError(
                "Microsoft Graph delta response did not include a continuation or delta link."
            )

        return GraphDeltaPage(
            messages=tuple(messages),
            next_link=next_link,
            delta_link=delta_link,
        )

    def _get_json(
        self,
        url: str,
        *,
        params: dict[str, str | int] | None = None,
    ) -> dict[str, Any]:
        access_token = self._access_token_provider().strip()
        if not access_token:
            raise MicrosoftGraphError("Microsoft Graph access token provider returned no token.")

        try:
            response = self._session.get(
                self._validated_graph_url(url),
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                    "Prefer": (
                        'IdType="ImmutableId", outlook.body-content-type="html", '
                        f"odata.maxpagesize={GRAPH_PAGE_SIZE}"
                    ),
                },
                params=params,
                timeout=self._timeout_seconds,
            )
        except requests.RequestException as exc:
            raise MicrosoftGraphError("Microsoft Graph mailbox request failed.") from exc

        if response.status_code >= 400:
            request_id = response.headers.get("request-id", "unknown")
            raise MicrosoftGraphError(
                f"Microsoft Graph mailbox request failed with status {response.status_code} "
                f"(request ID {request_id})."
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise MicrosoftGraphPayloadError(
                "Microsoft Graph returned a non-JSON mailbox response."
            ) from exc
        if not isinstance(payload, dict):
            raise MicrosoftGraphPayloadError(
                "Microsoft Graph returned an invalid mailbox response."
            )
        return cast(dict[str, Any], payload)

    def _canonical_message(self, payload: dict[str, Any]) -> CanonicalMessage:
        provider_message_id = str(payload.get("id") or "").strip()
        if not provider_message_id:
            raise MicrosoftGraphPayloadError("Microsoft Graph message is missing its ID.")

        body_value = payload.get("body")
        body = cast(dict[str, Any], body_value) if isinstance(body_value, dict) else {}
        body_content = str(body.get("content") or "")
        body_content_type = str(body.get("contentType") or "").lower()
        body_html = body_content if body_content_type == "html" else ""
        body_text = body_content if body_content_type == "text" else ""

        header_map = self._internet_headers(payload.get("internetMessageHeaders"))
        in_reply_to = self._first_header(header_map, "in-reply-to")
        references = self._message_id_references(self._first_header(header_map, "references"))
        sender = self._email_address(payload.get("from") or payload.get("sender"))

        received_at = payload.get("receivedDateTime") or payload.get("sentDateTime")
        if not received_at:
            raise MicrosoftGraphPayloadError(
                f"Microsoft Graph message {provider_message_id} is missing a message timestamp."
            )

        return CanonicalMessage(
            provider=GRAPH_PROVIDER,
            provider_message_id=provider_message_id,
            provider_conversation_id=str(payload.get("conversationId") or "").strip(),
            internet_message_id=str(payload.get("internetMessageId") or "").strip(),
            in_reply_to=in_reply_to,
            references=references,
            sender_name=sender[0],
            sender_address=sender[1],
            to_recipients=self._recipient_addresses(payload.get("toRecipients")),
            cc_recipients=self._recipient_addresses(payload.get("ccRecipients")),
            bcc_recipients=self._recipient_addresses(payload.get("bccRecipients")),
            subject=str(payload.get("subject") or "").strip(),
            body_html=body_html,
            body_text=body_text,
            sent_or_received_at=self._parse_datetime(str(received_at)),
            has_attachments=bool(payload.get("hasAttachments", False)),
        )

    @staticmethod
    def _validated_graph_url(url: str) -> str:
        parsed = urlparse(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != "graph.microsoft.com"
            or parsed.port not in (None, 443)
            or not parsed.path.startswith("/v1.0/")
            or parsed.username
            or parsed.password
        ):
            raise MicrosoftGraphError("Refusing to send credentials to a non-Graph URL.")
        return url

    def _optional_link(self, payload: dict[str, Any], key: str) -> str:
        value = str(payload.get(key) or "").strip()
        return self._validated_graph_url(value) if value else ""

    @staticmethod
    def _internet_headers(value: Any) -> dict[str, list[str]]:
        headers: dict[str, list[str]] = {}
        if not isinstance(value, list):
            return headers
        for row in value:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip().lower()
            header_value = str(row.get("value") or "").strip()
            if name and header_value:
                headers.setdefault(name, []).append(header_value)
        return headers

    @staticmethod
    def _first_header(headers: dict[str, list[str]], name: str) -> str:
        values = headers.get(name, [])
        return values[0].strip() if values else ""

    @staticmethod
    def _message_id_references(value: str) -> tuple[str, ...]:
        if not value:
            return ()
        bracketed = re.findall(r"<[^>]+>", value)
        if bracketed:
            return tuple(dict.fromkeys(item.strip() for item in bracketed if item.strip()))
        return tuple(dict.fromkeys(item for item in value.split() if item))

    @classmethod
    def _recipient_addresses(cls, value: Any) -> tuple[str, ...]:
        if not isinstance(value, list):
            return ()
        addresses: list[str] = []
        for recipient in value:
            _name, address = cls._email_address(recipient)
            if address:
                addresses.append(address)
        return tuple(dict.fromkeys(addresses))

    @staticmethod
    def _email_address(value: Any) -> tuple[str, str]:
        if not isinstance(value, dict):
            return "", ""
        email_address = value.get("emailAddress")
        if not isinstance(email_address, dict):
            return "", ""
        return (
            str(email_address.get("name") or "").strip(),
            str(email_address.get("address") or "").strip().lower(),
        )

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        normalised = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalised)
        except ValueError as exc:
            raise MicrosoftGraphPayloadError(
                f"Microsoft Graph returned an invalid message timestamp: {value!r}."
            ) from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=datetime_timezone.utc)
        return parsed


def sync_graph_mailbox(
    mailbox: Mailbox,
    adapter: MicrosoftGraphAdapter,
    consume_message: MessageConsumer,
) -> int:
    """Complete one Graph delta round and checkpoint only after successful consumption."""
    if not mailbox.enabled:
        return 0

    processed = 0
    current_url = mailbox.delta_link
    completed_delta_link = ""

    try:
        while True:
            page = adapter.fetch_delta_page(mailbox, url=current_url)
            for message in page.messages:
                consume_message(mailbox, message)
                processed += 1

            if page.next_link:
                current_url = page.next_link
                continue

            completed_delta_link = page.delta_link
            break

        mailbox.delta_link = completed_delta_link
        mailbox.last_synced_at = timezone.now()
        mailbox.last_successful_sync_at = mailbox.last_synced_at
        mailbox.last_error = ""
        mailbox.save(
            update_fields=[
                "delta_link",
                "last_synced_at",
                "last_successful_sync_at",
                "last_error",
                "updated_at",
            ]
        )
        return processed
    except Exception as exc:
        mailbox.last_synced_at = timezone.now()
        mailbox.last_error = f"{type(exc).__name__}: {exc}"[:2000]
        mailbox.save(update_fields=["last_synced_at", "last_error", "updated_at"])
        raise
