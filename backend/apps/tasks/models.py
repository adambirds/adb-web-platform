from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.ownership import OwnershipType, ownership_constraint, validate_ownership


class TaskStatus(models.Model):
    """Task status options."""

    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default="#808080", help_text="Hex color code")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "Task Statuses"

    def __str__(self):
        return self.name


class TaskList(models.Model):
    """Optional collection of client-owned or internal tasks."""

    ownership_type = models.CharField(
        max_length=20,
        choices=OwnershipType.choices,
        default=OwnershipType.INTERNAL,
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="task_lists",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "clients.Project",
        on_delete=models.CASCADE,
        related_name="task_lists",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [ownership_constraint("tasklist_valid_ownership")]

    def clean(self) -> None:
        super().clean()
        validate_ownership(self)
        if self.project_id and self.project:
            if self.project.ownership_type != self.ownership_type:
                raise ValidationError(
                    {"project": "Task-list ownership must match the selected project."}
                )
            if self.project.client_id != self.client_id:
                raise ValidationError(
                    {"client": "Task-list client must match the selected project."}
                )

    def __str__(self):
        return self.name


class Task(models.Model):
    """Standalone, client-owned or project-linked operational task."""

    PRIORITY_CHOICES = [
        (1, "Low"),
        (2, "Medium"),
        (3, "High"),
        (4, "Critical"),
    ]

    ownership_type = models.CharField(
        max_length=20,
        choices=OwnershipType.choices,
        default=OwnershipType.INTERNAL,
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "clients.Project",
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Markdown content")

    task_list = models.ForeignKey(
        TaskList,
        on_delete=models.SET_NULL,
        related_name="tasks",
        null=True,
        blank=True,
    )
    status = models.ForeignKey(
        TaskStatus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    due_date = models.DateField(blank=True, null=True)
    recurrence_rule = models.CharField(
        max_length=500,
        blank=True,
        help_text="Optional iCalendar RRULE for recurring tasks.",
    )
    next_occurrence_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_tasks",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [ownership_constraint("task_valid_ownership")]

    def clean(self) -> None:
        super().clean()
        validate_ownership(self)

        if self.project_id and self.project:
            if self.project.ownership_type != self.ownership_type:
                raise ValidationError(
                    {"project": "Task ownership must match the selected project."}
                )
            if self.project.client_id != self.client_id:
                raise ValidationError(
                    {"client": "Task client must match the selected project."}
                )

        if self.task_list_id and self.task_list:
            if self.task_list.ownership_type != self.ownership_type:
                raise ValidationError(
                    {"task_list": "Task ownership must match the selected task list."}
                )
            if self.task_list.client_id != self.client_id:
                raise ValidationError(
                    {"client": "Task client must match the selected task list."}
                )
            if (
                self.task_list.project_id
                and self.task_list.project_id != self.project_id
            ):
                raise ValidationError(
                    {"project": "Task project must match the selected project task list."}
                )

    def __str__(self):
        return self.title
