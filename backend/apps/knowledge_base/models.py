from django.db import models


class KnowledgeBaseSection(models.Model):
    """Section of knowledge base (Setup, Deployments, Maintenance, Notes)"""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class KnowledgeBaseDocument(models.Model):
    """Documentation page in knowledge base"""

    title = models.CharField(max_length=200)
    section = models.ForeignKey(KnowledgeBaseSection, on_delete=models.CASCADE, related_name="documents")
    content = models.TextField(help_text="Markdown content")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class DocumentVersion(models.Model):
    """Version history for a document"""

    document = models.ForeignKey(KnowledgeBaseDocument, on_delete=models.CASCADE, related_name="versions")
    version_number = models.IntegerField()
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]

    def __str__(self):
        return f"{self.document} - v{self.version_number}"
