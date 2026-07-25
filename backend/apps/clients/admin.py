from django.contrib import admin

from .models import Client, ClientContact, Project, ProjectNote, TimeEntry

# Register your models here.


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "company", "email")


@admin.register(ClientContact)
class ClientContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "client", "role")
    list_filter = ("client",)
    search_fields = ("name", "email")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "status", "start_date", "end_date")
    list_filter = ("status", "client", "start_date")
    search_fields = ("name", "description")


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "project", "duration_hours", "billable", "created_at")
    list_filter = ("billable", "project", "date")
    search_fields = ("description", "project__name")


@admin.register(ProjectNote)
class ProjectNoteAdmin(admin.ModelAdmin):
    list_display = ("project", "created_at", "updated_at")
    list_filter = ("project", "created_at")
    search_fields = ("content",)
