from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.core.live.events import publish_change
from apps.core.live.signals import change_for
from apps.infrastructure.models import InfrastructureResource, SourceRepository

from .client import GitHubClient, GitHubError
from .models import Installation, Item, Repository


@transaction.atomic
def import_repository(installation: Installation, data: dict[str, Any]) -> Repository:
    existing = Repository.objects.select_for_update().filter(github_id=data["id"]).first()
    if existing and existing.source.resource.client_id != installation.client_id:
        raise GitHubError(
            "Repository ownership differs from its installation; review its resource ownership."
        )
    source = (
        existing.source
        if existing
        else SourceRepository.objects.filter(
            Q(provider_repository_id=str(data["id"]), web_url__startswith="https://github.com/")
            | Q(web_url__iexact=data["html_url"].rstrip("/"))
            | Q(web_url__iexact=data["html_url"].rstrip("/") + "/"),
            resource__client=installation.client,
            resource__ownership_type="client" if installation.client_id else "internal",
        ).first()
    )
    if source is not None and not existing and Repository.objects.filter(source=source).exists():
        # A deleted/recreated repository may reuse a URL but has a new remote identity.
        source = None
    if source is None:
        resource = InfrastructureResource.objects.create(
            name=data["full_name"][:200],
            resource_type="source_repository",
            ownership_type="client" if installation.client_id else "internal",
            client=installation.client,
        )
        source = SourceRepository(resource=resource)
    source.provider_repository_id = str(data["id"])
    source.web_url = data["html_url"]
    source.clone_url = data.get("clone_url", "")
    source.owner_name = data["owner"]["login"]
    source.repository_name = data["name"]
    source.default_branch = data.get("default_branch", "")
    source.visibility = data.get("visibility", "private")
    source.is_fork = data.get("fork", False)
    source.save()
    if existing and source.resource.name == existing.full_name[:200]:
        source.resource.name = data["full_name"][:200]
        source.resource.save(update_fields=["name", "updated_at"])
    repository, _ = Repository.objects.update_or_create(
        github_id=data["id"],
        defaults={
            "installation": installation,
            "source": source,
            "full_name": data["full_name"],
            "active": True,
        },
    )
    return repository


@transaction.atomic
def save_item(repository: Repository, kind: str, data: dict[str, Any]) -> Item:
    updated_at = parse_datetime(data.get("updated_at", "")) or timezone.now()
    existing = (
        Item.objects.select_for_update()
        .filter(repository=repository, kind=kind, github_id=data["id"])
        .first()
    )
    if existing and existing.updated_at > updated_at:
        return existing
    author = data.get("user") or data.get("actor") or {}
    login = author.get("login", "")
    state = data.get("status") or data.get("state", "")
    if kind == "pull_request" and data.get("merged_at"):
        state = "merged"
    item, _ = Item.objects.update_or_create(
        repository=repository,
        kind=kind,
        github_id=data["id"],
        defaults={
            "number": data.get("number"),
            "title": (data.get("title") or data.get("display_title") or data.get("name", ""))[:500],
            "url": data.get("html_url", ""),
            "author": login,
            "is_bot": author.get("type") == "Bot" or login.endswith("[bot]"),
            "is_dependabot": login in ("dependabot[bot]", "dependabot"),
            "assignees": [user["login"].lower() for user in data.get("assignees", [])],
            "reviewers": [user["login"].lower() for user in data.get("requested_reviewers", [])],
            "state": state,
            "conclusion": data.get("conclusion") or "",
            "branch": data.get("head_branch") or data.get("head", {}).get("ref", ""),
            "updated_at": updated_at,
        },
    )
    return item


def sync_repository(repository: Repository, *, has_issues: bool = True) -> None:
    if not repository.active or not repository.installation.enabled:
        return
    client = GitHubClient(repository.installation.github_id)
    root = f"/repos/{repository.full_name}"
    for kind, path, key in (
        ("issue", "/issues?state=open", None),
        ("pull_request", "/pulls?state=open", None),
        ("workflow", "/actions/workflows", "workflows"),
    ):
        if kind == "issue" and not has_issues:
            continue
        seen = []
        for data in client.pages(root + path, key):
            if kind == "issue" and "pull_request" in data:
                continue
            seen.append(save_item(repository, kind, data).pk)
        # Initial/resync fetches open work; webhook history remains available as closed.
        stale = Item.objects.filter(repository=repository, kind=kind).exclude(pk__in=seen)
        if kind == "workflow":
            stale.update(state="inactive")
        else:
            stale.filter(state="open").update(state="closed")
    runs = client.request("GET", root + "/actions/runs?per_page=30")["workflow_runs"]
    for data in runs:
        save_item(repository, "run", data)
    repository.last_synced_at = timezone.now()
    repository.sync_error = ""
    repository.save(update_fields=["last_synced_at", "sync_error"])


def sync_installation(installation_id: int) -> None:
    installation = Installation.objects.get(pk=installation_id)
    if not installation.enabled:
        return
    client = GitHubClient(installation.github_id)
    ids = []
    errors = 0
    for data in client.pages("/installation/repositories", "repositories"):
        repository = import_repository(installation, data)
        ids.append(repository.pk)
        try:
            sync_repository(repository, has_issues=data.get("has_issues", True))
        except GitHubError as exc:
            errors += 1
            Repository.objects.filter(pk=repository.pk).update(sync_error=str(exc)[:300])
    Repository.objects.filter(installation=installation).exclude(pk__in=ids).update(active=False)
    installation.last_synced_at = timezone.now()
    installation.sync_error = (
        f"{errors} repositories could not fully synchronise. Open Repositories for details."
        if errors
        else ""
    )
    installation.save(update_fields=["last_synced_at", "sync_error"])
    if errors:
        raise GitHubError(installation.sync_error)


def sync_workflows(repository: Repository) -> None:
    client = GitHubClient(repository.installation.github_id)
    seen = [
        save_item(repository, "workflow", data).pk
        for data in client.pages(f"/repos/{repository.full_name}/actions/workflows", "workflows")
    ]
    Item.objects.filter(repository=repository, kind="workflow").exclude(pk__in=seen).update(
        state="inactive"
    )

    change = change_for(repository, "github")
    if change is not None:
        publish_change(change)
