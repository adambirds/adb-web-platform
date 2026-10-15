"""Workspace models for the analytics product.

These are not registered until the analytics app is added to INSTALLED_APPS.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q


class Business(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class BusinessMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        VIEWER = "viewer", "Viewer"

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="analytics_memberships",
    )
    role = models.CharField(max_length=12, choices=Role.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "user"],
                name="analytics_unique_business_user",
            )
        ]


class Website(models.Model):
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="websites"
    )
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=253)
    timezone = models.CharField(max_length=64, default="Europe/London")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "domain"],
                name="analytics_unique_business_domain",
            )
        ]

    def __str__(self) -> str:
        return self.name


class ProviderProperty(models.Model):
    class Provider(models.TextChoices):
        GA4 = "ga4", "Google Analytics 4"
        SEARCH_CONSOLE = "gsc", "Google Search Console"

    website = models.ForeignKey(
        Website, on_delete=models.CASCADE, related_name="provider_properties"
    )
    provider = models.CharField(max_length=8, choices=Provider.choices)
    external_id = models.CharField(max_length=512)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["website", "provider"],
                name="analytics_one_property_per_provider",
            ),
        ]
