from django.contrib import admin

from .models import Lead, LeadSource, LeadStatus

# Register your models here.


@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(LeadStatus)
class LeadStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "order")


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "status", "source", "created_at")
    list_filter = ("status", "source", "created_at")
    search_fields = ("name", "email", "company")
