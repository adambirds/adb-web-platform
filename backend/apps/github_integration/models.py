from django.conf import settings
from django.db import models


class Installation(models.Model):
    github_id = models.BigIntegerField(unique=True)
    account = models.CharField(max_length=200)
    enabled = models.BooleanField(default=False)
    client = models.ForeignKey("clients.Client", null=True, blank=True, on_delete=models.PROTECT)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    sync_error = models.CharField(max_length=300, blank=True)

    class Meta:
        permissions = [
            ("manage_github", "Can configure GitHub installations and synchronisation"),
            ("trigger_workflow", "Can dispatch GitHub workflows and rerun failed jobs"),
            ("view_workflow_logs", "Can view GitHub Actions logs"),
        ]


class Repository(models.Model):
    github_id = models.BigIntegerField(unique=True)
    installation = models.ForeignKey(Installation, on_delete=models.CASCADE)
    source = models.OneToOneField("infrastructure.SourceRepository", on_delete=models.PROTECT)
    full_name = models.CharField(max_length=400)
    active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    sync_error = models.CharField(max_length=300, blank=True)


class Item(models.Model):
    """Safe GitHub projections; tokens, issue bodies and logs are never stored here."""

    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    kind = models.CharField(
        max_length=20,
        choices=[
            ("issue", "Issue"),
            ("pull_request", "Pull request"),
            ("workflow", "Workflow"),
            ("run", "Workflow run"),
        ],
    )
    github_id = models.BigIntegerField()
    number = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000, blank=True)
    author = models.CharField(max_length=200, blank=True)
    is_bot = models.BooleanField(default=False)
    is_dependabot = models.BooleanField(default=False)
    assignees = models.JSONField(default=list)
    reviewers = models.JSONField(default=list)
    state = models.CharField(max_length=50, blank=True)
    conclusion = models.CharField(max_length=50, blank=True)
    branch = models.CharField(max_length=300, blank=True)
    updated_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["repository", "kind", "github_id"], name="github_item_identity"
            )
        ]
        indexes = [models.Index(fields=["kind", "-updated_at"])]


class Delivery(models.Model):
    delivery_id = models.CharField(max_length=100, unique=True)
    event = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    error = models.CharField(max_length=300, blank=True)


class Preference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    username = models.CharField(max_length=100, blank=True)


class WorkflowAction(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=30)
    remote_id = models.BigIntegerField()
    ref = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
