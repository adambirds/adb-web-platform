from __future__ import annotations

from dataclasses import dataclass

from apps.clients.models import Client
from apps.ticketing.models import Mailbox, Ticket
from apps.ticketing.services.contracts import CanonicalMessage

_MONITORING_LOCAL_PARTS = {"alert", "alerts", "monitor", "monitoring", "status", "uptime"}
_AUTOMATED_LOCAL_PARTS = {
    "automated",
    "mailer-daemon",
    "no-reply",
    "noreply",
    "notification",
    "notifications",
}
_MONITORING_SUBJECT_PREFIXES = ("[alert]", "[incident]", "[recovery]", "[resolved]")
_SPAM_PHRASES = (
    "buy backlinks",
    "casino promotion",
    "crypto investment",
    "guest post",
    "link building",
    "payday loan",
    "seo services",
    "viagra",
)


@dataclass(frozen=True, slots=True)
class ClassificationDecision:
    classification: str
    score: int
    reasons: tuple[str, ...]
    suggested_priority: str | None = None


def classify_message(
    mailbox: Mailbox,
    canonical: CanonicalMessage,
    client: Client | None,
) -> ClassificationDecision:
    """Classify an inbound message using conservative, explainable deterministic rules."""
    if client is not None:
        if mailbox.purpose == Mailbox.Purpose.SALES:
            return ClassificationDecision(
                classification=Ticket.Classification.SALES,
                score=100,
                reasons=("known_client", "sales_mailbox"),
            )
        if mailbox.purpose == Mailbox.Purpose.ACCOUNTS:
            return ClassificationDecision(
                classification=Ticket.Classification.ACCOUNTS,
                score=100,
                reasons=("known_client", "accounts_mailbox"),
            )
        return ClassificationDecision(
            classification=Ticket.Classification.CLIENT_SUPPORT,
            score=100,
            reasons=("known_client",),
        )

    searchable = _searchable_text(canonical)
    spam_matches = tuple(phrase for phrase in _SPAM_PHRASES if phrase in searchable)
    if len(spam_matches) >= 2:
        return ClassificationDecision(
            classification=Ticket.Classification.PROBABLE_SPAM,
            score=min(95, 60 + (len(spam_matches) * 10)),
            reasons=tuple(f"spam_phrase:{phrase}" for phrase in spam_matches),
            suggested_priority=Ticket.Priority.LOW,
        )

    local_part = _sender_local_part(canonical.sender_address)
    subject = canonical.subject.strip().lower()
    if local_part in _MONITORING_LOCAL_PARTS or subject.startswith(_MONITORING_SUBJECT_PREFIXES):
        reasons: list[str] = []
        if local_part in _MONITORING_LOCAL_PARTS:
            reasons.append(f"monitoring_sender:{local_part}")
        if subject.startswith(_MONITORING_SUBJECT_PREFIXES):
            reasons.append("monitoring_subject")
        return ClassificationDecision(
            classification=Ticket.Classification.MONITORING,
            score=85,
            reasons=tuple(reasons),
        )

    if local_part in _AUTOMATED_LOCAL_PARTS:
        return ClassificationDecision(
            classification=Ticket.Classification.AUTOMATED_SYSTEM,
            score=80,
            reasons=(f"automated_sender:{local_part}",),
        )

    if "unsubscribe" in searchable and (
        "newsletter" in searchable or "view in browser" in searchable
    ):
        return ClassificationDecision(
            classification=Ticket.Classification.NEWSLETTER_MARKETING,
            score=75,
            reasons=("marketing_unsubscribe",),
            suggested_priority=Ticket.Priority.LOW,
        )

    if mailbox.purpose == Mailbox.Purpose.SALES:
        return ClassificationDecision(
            classification=Ticket.Classification.SALES,
            score=60,
            reasons=("sales_mailbox",),
        )
    if mailbox.purpose == Mailbox.Purpose.ACCOUNTS:
        return ClassificationDecision(
            classification=Ticket.Classification.ACCOUNTS,
            score=60,
            reasons=("accounts_mailbox",),
        )

    return ClassificationDecision(
        classification=Ticket.Classification.UNKNOWN,
        score=0,
        reasons=("no_rule_matched",),
    )


def _sender_local_part(sender_address: str) -> str:
    address = sender_address.strip().lower()
    if "@" not in address:
        return address
    return address.split("@", 1)[0]


def _searchable_text(canonical: CanonicalMessage) -> str:
    return f"{canonical.subject}\n{canonical.body_text}\n{canonical.body_html}".lower()
