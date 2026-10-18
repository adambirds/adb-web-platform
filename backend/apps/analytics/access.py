"""Business object permissions using Django's existing capability interface."""

from typing import Any

from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError

from apps.analytics.models import Business, BusinessMembership, Website


def business_has_perm(user: Any, perm: str, obj: Business) -> bool:
    """Grant analytics-only object capabilities; never grants staff/global access."""
    if not user.is_authenticated or not user.is_active or not perm.startswith("analytics."):
        return False
    role = (
        BusinessMembership.objects.filter(business=obj, user=user)
        .values_list("role", flat=True)
        .first()
    )
    if role is None:
        return False
    # Role bundles are standard Django Groups, not global user group membership.
    # Their permissions are applied only inside this explicitly checked Business.
    role_grants = Group.objects.filter(
        name=f"Analytics / {role.title()}",
        permissions__content_type__app_label="analytics",
        permissions__codename=perm.removeprefix("analytics."),
    ).exists()
    return role_grants or user.has_perm(perm)


def business_for(user: Any, business_id: int, capability: str = "view_business") -> Business:
    business = get_object_or_404(Business.objects.filter(memberships__user=user), pk=business_id)
    if not user.has_perm(f"analytics.{capability}", business):
        raise HttpError(403, "Your business role does not allow this action.")
    return business


def website_for(user: Any, website_id: int, capability: str = "view_report") -> Website:
    website = get_object_or_404(
        Website.objects.select_related("business").filter(business__memberships__user=user),
        pk=website_id,
    )
    business_for(user, website.business_id, capability)
    return website
