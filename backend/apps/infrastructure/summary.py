"""Current inventory counts using the resource capability and Client scope."""

from __future__ import annotations

from datetime import timedelta

from django.db.models import Count
from django.http import HttpRequest
from django.utils import timezone

from .models import DomainProfile, InfrastructureResource, TLSCertificate
from .policies import scope_infrastructure_resources_for_user

INVENTORY_FAMILIES: tuple[tuple[str, str], ...] = (
    ("server_count", "server"),
    ("database_count", "database_instance"),
    ("website_count", "website"),
    ("domain_count", "domain"),
    ("ssl_certificate_count", "tls_certificate"),
    ("licence_count", "licence"),
    ("application_count", "application"),
    ("mobile_app_count", "mobile_app"),
    ("api_count", "api"),
    ("bot_count", "bot"),
    ("email_system_count", "email_system"),
)


def inventory_summary(request: HttpRequest) -> dict[str, int]:
    resources = scope_infrastructure_resources_for_user(request.user).exclude(
        lifecycle_status__in=[
            InfrastructureResource.LifecycleStatus.RETIRED,
            InfrastructureResource.LifecycleStatus.ARCHIVED,
        ]
    )
    if not request.user.has_perm("infrastructure.view_infrastructureresource"):
        resources = resources.none()
    totals = {
        row["resource_type"]: row["total"]
        for row in resources.order_by().values("resource_type").annotate(total=Count("id"))
    }
    summary: dict[str, int] = {}
    for key, resource_type in INVENTORY_FAMILIES:
        summary[key] = totals.get(resource_type, 0)

    today = timezone.localdate()
    warning_date = today + timedelta(days=45)
    summary["expiring_domain_count"] = DomainProfile.objects.filter(
        resource__in=resources, expires_on__gte=today, expires_on__lte=warning_date
    ).count()
    summary["expiring_certificate_count"] = TLSCertificate.objects.filter(
        resource__in=resources, expires_at__gte=timezone.now(), expires_at__date__lte=warning_date
    ).count()
    summary["renewing_licence_count"] = 0
    return summary
