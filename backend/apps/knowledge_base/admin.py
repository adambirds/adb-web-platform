from django.contrib import admin

from .models import DocumentVersion, KnowledgeBaseDocument, KnowledgeBaseSection

# Register your models here.


@admin.register(KnowledgeBaseSection)
class KnowledgeBaseSectionAdmin(admin.ModelAdmin):
    list_display = ("name", "order")


@admin.register(KnowledgeBaseDocument)
class KnowledgeBaseDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "created_at", "updated_at")
    list_filter = ("section", "created_at")
    search_fields = ("title", "content")


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ("document", "version_number", "created_at")
    list_filter = ("document", "created_at")
