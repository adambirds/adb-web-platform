from __future__ import annotations

from dataclasses import dataclass

from apps.ticketing.models import Vendor, VendorSenderRule


@dataclass(frozen=True, slots=True)
class VendorSenderMatch:
    vendor: Vendor
    rule: VendorSenderRule


def resolve_vendor_sender(sender_address: str) -> VendorSenderMatch | None:
    """Resolve an explicit vendor sender rule, preferring an exact address over a domain."""
    email = sender_address.strip().lower()
    if not email or "@" not in email:
        return None

    exact_rule = (
        VendorSenderRule.objects.select_related("vendor", "target_queue")
        .filter(
            enabled=True,
            vendor__enabled=True,
            match_type=VendorSenderRule.MatchType.EMAIL,
            match_value=email,
        )
        .order_by("ordering", "id")
        .first()
    )
    if exact_rule is not None:
        return VendorSenderMatch(vendor=exact_rule.vendor, rule=exact_rule)

    domain = email.rsplit("@", 1)[1]
    labels = domain.split(".")
    candidate_domains = [".".join(labels[index:]) for index in range(max(0, len(labels) - 1))]
    if not candidate_domains:
        return None

    rules = {
        rule.match_value: rule
        for rule in VendorSenderRule.objects.select_related("vendor", "target_queue")
        .filter(
            enabled=True,
            vendor__enabled=True,
            match_type=VendorSenderRule.MatchType.DOMAIN,
            match_value__in=candidate_domains,
        )
        .order_by("ordering", "id")
    }
    for candidate in candidate_domains:
        rule = rules.get(candidate)
        if rule is not None:
            return VendorSenderMatch(vendor=rule.vendor, rule=rule)
    return None
