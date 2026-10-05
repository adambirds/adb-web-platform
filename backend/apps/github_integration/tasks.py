from __future__ import annotations

from typing import Any

from celery import shared_task
from django.core.cache import cache
from django.utils import timezone

from .client import GitHubClient, GitHubError
from .models import Delivery, Installation, Repository
from .services import save_item, sync_installation, sync_workflows


@shared_task(
    name="github.sync_installation", autoretry_for=(GitHubError,), retry_backoff=True, max_retries=4
)
def synchronise(installation_id: int) -> None:
    try:
        sync_installation(installation_id)
    except GitHubError as exc:
        Installation.objects.filter(pk=installation_id).update(sync_error=str(exc)[:300])
        raise


@shared_task(
    name="github.process_delivery", autoretry_for=(GitHubError,), retry_backoff=True, max_retries=4
)
def process_delivery(delivery_id: int) -> None:
    lock = f"github-delivery:{delivery_id}"
    if not cache.add(lock, True, 600):
        return
    installation = None
    repository = None
    try:
        delivery = Delivery.objects.get(pk=delivery_id)
        if delivery.processed_at:
            return
        data: dict[str, Any] = delivery.payload
        installation = Installation.objects.filter(github_id=data["installation_id"]).first()
        if delivery.event == "installation" and data["action"] in ("created", "unsuspend"):
            # New/suspended installs require an explicit ownership approval before import.
            installation, _ = Installation.objects.get_or_create(
                github_id=data["installation_id"],
                defaults={"account": data["account"]},
            )
        if installation and installation.enabled:
            repository = Repository.objects.filter(
                installation=installation, github_id=data["repository_id"], active=True
            ).first()
            if delivery.event in ("installation_repositories", "repository") or repository is None:
                sync_installation(installation.pk)
            elif data["kind"]:
                kind = data["kind"]
                endpoint = {
                    "issue": f"issues/{data['number']}",
                    "pull_request": f"pulls/{data['number']}",
                    "run": f"actions/runs/{data['item_id']}",
                }[kind]
                remote = GitHubClient(installation.github_id).request(
                    "GET", f"/repos/{repository.full_name}/{endpoint}"
                )
                save_item(repository, kind, remote)
                if (
                    kind == "run"
                    and remote.get("workflow_id")
                    and not repository.item_set.filter(
                        kind="workflow", github_id=remote["workflow_id"]
                    ).exists()
                ):
                    sync_workflows(repository)
            elif delivery.event == "workflow_job" and data["run_id"]:
                remote = GitHubClient(installation.github_id).request(
                    "GET", f"/repos/{repository.full_name}/actions/runs/{data['run_id']}"
                )
                save_item(repository, "run", remote)
            elif delivery.event == "push":
                sync_workflows(repository)
            installation.last_synced_at = timezone.now()
            installation.save(update_fields=["last_synced_at"])
            if repository:
                repository.last_synced_at = timezone.now()
                repository.save(update_fields=["last_synced_at"])
        delivery.processed_at = timezone.now()
        delivery.error = ""
        delivery.save(update_fields=["processed_at", "error"])
    except GitHubError as exc:
        Delivery.objects.filter(pk=delivery_id).update(error=str(exc)[:300])
        if installation:
            Installation.objects.filter(pk=installation.pk).update(sync_error=str(exc)[:300])
        if repository:
            Repository.objects.filter(pk=repository.pk).update(sync_error=str(exc)[:300])
        raise
    finally:
        cache.delete(lock)


@shared_task(name="github.recover_deliveries")
def recover_deliveries() -> None:
    from .webhooks import enqueue

    for delivery_id in (
        Delivery.objects.filter(processed_at__isnull=True)
        .order_by("received_at")
        .values_list("pk", flat=True)[:100]
    ):
        enqueue(delivery_id)
