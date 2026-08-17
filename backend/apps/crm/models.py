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

    message = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text="Internal notes")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name
