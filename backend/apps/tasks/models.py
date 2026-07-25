from django.db import models


class TaskStatus(models.Model):
    """Task status options"""

    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default="#808080", help_text="Hex color code")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "Task Statuses"

    def __str__(self):
        return self.name


class TaskList(models.Model):
    """Collection of tasks (project-specific or general)"""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Task(models.Model):
    """Individual task"""

    PRIORITY_CHOICES = [
        (1, "Low"),
        (2, "Medium"),
        (3, "High"),
        (4, "Critical"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Markdown content")

    task_list = models.ForeignKey(TaskList, on_delete=models.CASCADE, related_name="tasks")
    status = models.ForeignKey(TaskStatus, on_delete=models.SET_NULL, null=True, blank=True)

    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    due_date = models.DateField(blank=True, null=True)

    # Optional links
    # project = models.ForeignKey('clients.Project', on_delete=models.SET_NULL, null=True, blank=True)
    # client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
