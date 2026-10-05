from __future__ import annotations

import base64
from collections.abc import Iterable
from email.policy import SMTP
from email.utils import parseaddr
from threading import RLock
from typing import Any
from urllib.parse import quote

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import EmailMessage
from django.core.mail.backends.base import BaseEmailBackend
from django.core.validators import validate_email

from apps.ticketing.services.graph import GRAPH_API_ROOT, MicrosoftGraphError
from apps.ticketing.services.graph_auth import (
    MicrosoftGraphAuthenticationError,
    MicrosoftGraphTokenProvider,
    environment_graph_connection,
)


class MicrosoftGraphEmailBackend(BaseEmailBackend):
    """Django application mail through the platform's Infisical Graph connection.

    MIME preserves plain/HTML alternatives, attachments, recipient types and
    reply-to. Account tokens/bodies never enter Tickets, task history or audits.
    """

    def __init__(self, fail_silently: bool = False, **kwargs: Any) -> None:
        super().__init__(fail_silently=fail_silently, **kwargs)
        self._session: requests.Session | None = None
        self._tokens: MicrosoftGraphTokenProvider | None = None
        self._lock = RLock()

    def open(self) -> bool:
        if self._session is not None:
            return False
        connection = environment_graph_connection()
        if connection is None or not connection.enabled:
            raise ImproperlyConfigured(
                "Application email requires an enabled Infisical-configured Microsoft Graph connection."
            )
        self._session = requests.Session()
        self._tokens = MicrosoftGraphTokenProvider(connection, session=self._session)
        return True

    def close(self) -> None:
        if self._session is not None:
            self._session.close()
        self._session = None
        self._tokens = None

    def send_messages(self, email_messages: Iterable[EmailMessage]) -> int:
        messages = [message for message in email_messages if message.recipients()]
        if not messages:
            return 0
        with self._lock:
            opened = False
            try:
                opened = self.open()
                sent = 0
                for message in messages:
                    try:
                        self._send(message)
                        sent += 1
                    except (
                        MicrosoftGraphError,
                        MicrosoftGraphAuthenticationError,
                        ImproperlyConfigured,
                        ValueError,
                    ):
                        if not self.fail_silently:
                            raise
                return sent
            except (
                MicrosoftGraphError,
                MicrosoftGraphAuthenticationError,
                ImproperlyConfigured,
                ValueError,
            ):
                if not self.fail_silently:
                    raise
                return 0
            finally:
                if opened:
                    self.close()

    def _send(self, message: EmailMessage) -> None:
        sender = parseaddr(settings.DEFAULT_FROM_EMAIL)[1].strip().lower()
        try:
            validate_email(sender)
        except ValidationError as exc:
            raise ImproperlyConfigured(
                "DEFAULT_FROM_EMAIL must be a valid Microsoft 365 sending mailbox."
            ) from exc
        if parseaddr(message.from_email)[1].strip().lower() != sender:
            raise MicrosoftGraphError(
                "Application email must use the configured DEFAULT_FROM_EMAIL mailbox."
            )
        mime = message.message(policy=SMTP)
        # Respect Django's explicit recipient lists, including SMTP-envelope Bcc.
        # Do not allow extra_headers to change the authorised sender/recipients.
        for header, values in (
            ("From", [message.from_email]),
            ("To", message.to),
            ("Cc", message.cc),
            ("Bcc", message.bcc),
        ):
            if header in mime:
                del mime[header]
            if values:
                mime[header] = ", ".join(values)
        if "Sender" in mime:
            del mime["Sender"]
        if self._tokens is None or self._session is None:
            raise MicrosoftGraphError("Microsoft Graph email transport is not open.")
        token = self._tokens.get_access_token()
        encoded = base64.b64encode(mime.as_bytes()).decode("ascii")
        try:
            response = self._session.post(
                f"{GRAPH_API_ROOT}/users/{quote(sender, safe='')}/sendMail",
                data=encoded,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "text/plain"},
                timeout=30,
            )
        except requests.RequestException as exc:
            raise MicrosoftGraphError("Microsoft Graph application email request failed.") from exc
        if response.status_code != 202:
            # Response bodies can contain recipients or message data. Never copy them.
            raise MicrosoftGraphError(
                f"Microsoft Graph rejected application email with status {response.status_code}."
            )
