from django.conf import settings
from django.db import models


class LeadSource(models.Model):
    """Where a sales lead originated, such as a contact form or referral."""

    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class LeadStatus(models.Model):
    """Configurable sales-pipeline status for a lead."""

    name = models.CharField(max_length=100, unique=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "Lead Statuses"

    def __str__(self) -> str:
        return self.name


class Lead(models.Model):
    """Sales lead, kept separate from future support/ticket conversations."""

    brand = models.ForeignKey(
        "core.Brand",
        on_delete=models.PROTECT,
        related_name="leads",
        null=True,
        blank=True,
        help_text="ADB brand through which this lead originated.",
    )

    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=200, blank=True)

    status = models.ForeignKey(LeadStatus, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_leads",
        null=True,
        blank=True,
    )

    message = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text="Internal notes")

    converted_client = models.ForeignKey(
        "clients.Client",
        on_delete=models.SET_NULL,
        related_name="originating_leads",
        null=True,
        blank=True,
    )
    converted_contact = models.ForeignKey(
        "clients.ClientContact",
        on_delete=models.SET_NULL,
        related_name="originating_leads",
        null=True,
        blank=True,
    )
    converted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="converted_leads",
        null=True,
        blank=True,
    )
    converted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("assign_lead", "Can assign leads"),
            ("convert_lead", "Can convert leads to clients"),
        ]

    def __str__(self) -> str:
        return self.name
