from django.conf import settings
from django.db import models

from apps.core.ownership import OwnershipType, ownership_constraint, validate_ownership


class KnowledgeBaseSection(models.Model):
    """Reusable organisational section for internal documentation."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class KnowledgeBaseDocument(models.Model):
    """Client-owned or internal private documentation page."""

    ownership_type = models.CharField(
        max_length=20,
        choices=OwnershipType.choices,
        default=OwnershipType.INTERNAL,
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="knowledge_base_documents",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    section = models.ForeignKey(
        KnowledgeBaseSection,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    content = models.TextField(help_text="Markdown content")
    is_portal_visible = models.BooleanField(
        default=False,
        help_text="Reserved for future client-portal visibility. Private by default.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="knowledge_base_documents_created",
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="knowledge_base_documents_updated",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [ownership_constraint("knowledge_document_valid_ownership")]

    def clean(self) -> None:
        super().clean()
        validate_ownership(self)

    def __str__(self):
        return self.title


class DocumentVersion(models.Model):
    """Immutable historical version of a knowledge-base document."""

    document = models.ForeignKey(
        KnowledgeBaseDocument,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version_number = models.IntegerField()
    content = models.TextField()
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="knowledge_base_versions",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "version_number"],
                name="unique_document_version_number",
            )
        ]

    def __str__(self):
        return f"{self.document} - v{self.version_number}"
