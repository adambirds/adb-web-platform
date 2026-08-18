from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.ownership import OwnershipType, ownership_constraint, validate_ownership


class Client(models.Model):
    """Client organisation/account."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("archived", "Archived"),
    ]

    name = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)

    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.company or self.name


class ClientContact(models.Model):
    """Individual contact for a client."""

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g. CTO, Project Manager",
    )
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    is_billing = models.BooleanField(default=False)
    is_technical = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["client", "email"],
                name="unique_client_contact_email",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.client})"


class Project(models.Model):
    """Operational project that is either client-owned or internal."""

    STATUS_CHOICES = [
        ("planning", "Planning"),
        ("active", "Active"),
        ("paused", "Paused"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    ]

    ownership_type = models.CharField(
        max_length=20,
        choices=OwnershipType.choices,
        default=OwnershipType.CLIENT,
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="projects",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        constraints = [ownership_constraint("project_valid_ownership")]

    def clean(self) -> None:
        super().clean()
        validate_ownership(self)

    def __str__(self):
        owner = self.client if self.client_id else "Internal"
        return f"{self.name} ({owner})"


class TimeEntry(models.Model):
    """Time tracking entry for client-owned or internal work."""

    ownership_type = models.CharField(
        max_length=20,
        choices=OwnershipType.choices,
        default=OwnershipType.CLIENT,
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="time_entries",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="time_entries",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="time_entries",
        null=True,
        blank=True,
    )
    date = models.DateField()
    duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Hours worked",
    )
    description = models.TextField()
    billable = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        constraints = [ownership_constraint("timeentry_valid_ownership")]

    def apply_project_ownership(self) -> None:
        """Derive explicit ownership from a selected project for compatible callers."""
        if not self.project_id:
            return
        project = self.project
        if project is None:
            return
        self.ownership_type = project.ownership_type
        self.client_id = project.client_id

    def clean(self) -> None:
        super().clean()
        if self.project_id:
            self.apply_project_ownership()
        validate_ownership(self)
        if self.project_id and self.project:
            if self.project.ownership_type != self.ownership_type:
                raise ValidationError(
                    {"project": "Time entry ownership must match the selected project."}
                )
            if self.project.client_id != self.client_id:
                raise ValidationError(
                    {"client": "Time entry client must match the selected project."}
                )

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.project_id:
            self.apply_project_ownership()
        super().save(*args, **kwargs)

    def __str__(self):
        context = self.project or self.client or "Internal"
        return f"{context} - {self.date} ({self.duration_hours}h)"


class ProjectNote(models.Model):
    """Internal notes on a project."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="project_notes",
        null=True,
        blank=True,
    )
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.project} - {self.created_at}"
