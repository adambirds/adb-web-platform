from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class CanonicalMessage:
    """Provider-neutral inbound message produced by a source adapter."""

    provider: str
    provider_message_id: str
    provider_conversation_id: str
    internet_message_id: str
    in_reply_to: str
    references: tuple[str, ...]
    sender_name: str
    sender_address: str
    to_recipients: tuple[str, ...]
    cc_recipients: tuple[str, ...]
    bcc_recipients: tuple[str, ...]
    subject: str
    body_html: str
    body_text: str
    sent_or_received_at: datetime
    has_attachments: bool = False
