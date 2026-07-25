from django.contrib import admin

from .models import Task, TaskList, TaskStatus

# Register your models here.


@admin.register(TaskStatus)
class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "order")


@admin.register(TaskList)
class TaskListAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "task_list", "status", "priority", "due_date", "created_at")
    list_filter = ("status", "priority", "task_list", "due_date")
    search_fields = ("title", "description")
