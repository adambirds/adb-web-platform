from __future__ import annotations

import re
from typing import Any, cast

from django.conf import settings
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.security import django_auth

from apps.access_control.policies import scope_clients_for_user
from apps.core.models import AuditEvent
from apps.github_integration.client import GitHubClient, GitHubError
from apps.github_integration.models import (
    Installation,
    Item,
    Preference,
    Repository,
    WorkflowAction,
)
from apps.github_integration.tasks import synchronise
from apps.infrastructure.policies import scope_infrastructure_resources_for_user
from authentication.models import User

github_router = Router(tags=["admin-github"], auth=django_auth)


class UsernameIn(Schema):
    username: str


class InstallationIn(Schema):
    github_id: int
    client_id: int | None = None


class DispatchIn(Schema):
    ref: str
    inputs: dict[str, str] = {}


def require(request: HttpRequest, permission: str = "view_repository") -> None:
    user = request.user
    if not user.is_authenticated:
        raise HttpError(401, "Authentication required.")
    if (
        not user.is_staff
        or not user.has_perm(f"github_integration.{permission}")
        or not user.has_perm("infrastructure.view_infrastructureresource")
    ):
        raise HttpError(403, "You do not have permission for this action.")


def visible(request: HttpRequest) -> QuerySet[Repository]:
    return Repository.objects.select_related("installation", "source", "source__resource").filter(
        active=True,
        installation__enabled=True,
        source__resource__in=scope_infrastructure_resources_for_user(request.user),
    )


def repo_for(request: HttpRequest, repository_id: int) -> Repository:
    require(request)
    repository = visible(request).filter(pk=repository_id).first()
    if not repository:
        raise HttpError(404, "Repository not found.")
    return repository


def remote(client: GitHubClient, method: str, path: str, data: dict[str, Any] | None = None) -> Any:
    try:
        return client.request(method, path, data)
    except GitHubError as exc:
        raise HttpError(502, str(exc)) from exc


def paginate(queryset: QuerySet[Any], page: int) -> dict[str, Any]:
    total = queryset.count()
    page = max(1, min(page, max(1, (total + 24) // 25)))
    return {
        "total": total,
        "page": page,
        "pages": max(1, (total + 24) // 25),
        "rows": list(queryset[(page - 1) * 25 : page * 25]),
    }


@github_router.get("/github/options")
def options(request: HttpRequest) -> dict[str, Any]:
    require(request)
    preference = Preference.objects.filter(user=cast(User, request.user)).first()
    return {
        "username": preference.username if preference else "",
        "accounts": list(
            visible(request).values("installation_id", "installation__account").distinct()
        ),
        "configured": bool(
            settings.GITHUB_APP_ID
            and settings.GITHUB_APP_PRIVATE_KEY
            and settings.GITHUB_WEBHOOK_SECRET
        ),
        "install_url": f"https://github.com/apps/{settings.GITHUB_APP_SLUG}/installations/new"
        if settings.GITHUB_APP_SLUG
        else "",
    }


@github_router.put("/github/preference")
def preference(request: HttpRequest, payload: UsernameIn) -> dict[str, str]:
    require(request)
    username = payload.username.strip()
    if username and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", username):
        raise HttpError(422, "Enter a valid GitHub username.")
    Preference.objects.update_or_create(
        user=cast(User, request.user), defaults={"username": username}
    )
    return {"username": username}


@github_router.get("/github/repositories")
def repositories(
    request: HttpRequest, page: int = 1, account: int | None = None, search: str = ""
) -> dict[str, Any]:
    require(request)
    queryset = visible(request).order_by("full_name", "id")
    if account:
        queryset = queryset.filter(installation_id=account)
    if search:
        queryset = queryset.filter(full_name__icontains=search[:200])
    result = paginate(queryset, page)
    result["rows"] = [
        {
            "id": repo.pk,
            "name": repo.full_name,
            "kind": "repository",
            "resource_id": repo.source.resource_id,
            "url": repo.source.web_url,
            "branch": repo.source.default_branch,
            "account": repo.installation.account,
            "last_synced_at": repo.last_synced_at,
            "error": repo.sync_error,
        }
        for repo in result["rows"]
    ]
    return result


@github_router.get("/github/items")
def items(
    request: HttpRequest,
    kind: str = "pull_request",
    view: str = "my",
    page: int = 1,
    account: int | None = None,
    repository: int | None = None,
    state: str = "open",
) -> dict[str, Any]:
    require(request)
    if kind not in ("issue", "pull_request", "workflow", "run") or view not in (
        "my",
        "human",
        "dependabot",
        "all",
    ):
        raise HttpError(422, "Invalid filter.")
    repos = visible(request)
    if account:
        repos = repos.filter(installation_id=account)
    if repository:
        repos = repos.filter(pk=repository)
    queryset = Item.objects.select_related("repository", "repository__source").filter(
        repository__in=repos, kind=kind
    )
    if kind in ("issue", "pull_request") and state != "all":
        queryset = queryset.filter(state=state)
    if view == "my":
        pref = Preference.objects.filter(user=cast(User, request.user)).first()
        username = pref.username if pref else ""
        queryset = (
            queryset.filter(
                Q(author__iexact=username)
                | Q(assignees__contains=[username.lower()])
                | Q(reviewers__contains=[username.lower()]),
                is_bot=False,
            )
            if username
            else queryset.none()
        )
    elif view == "human":
        queryset = queryset.filter(is_bot=False)
    elif view == "dependabot":
        queryset = queryset.filter(is_dependabot=True)
    result = paginate(queryset.order_by("-updated_at", "-id"), page)
    result["rows"] = [
        {
            "id": item.pk,
            "github_id": item.github_id,
            "kind": item.kind,
            "repository_id": item.repository_id,
            "repository": item.repository.full_name,
            "title": item.title,
            "url": item.url,
            "author": item.author,
            "state": item.state,
            "conclusion": item.conclusion,
            "branch": item.branch or item.repository.source.default_branch,
            "is_dependabot": item.is_dependabot,
            "updated_at": item.updated_at,
        }
        for item in result["rows"]
    ]
    return result


@github_router.get("/github/installations")
def installations(request: HttpRequest) -> dict[str, Any]:
    require(request, "manage_github")
    clients = scope_clients_for_user(request.user)
    queryset = Installation.objects.filter(Q(client__isnull=True) | Q(client__in=clients)).order_by(
        "account"
    )
    return {
        "rows": list(
            queryset.values(
                "id", "github_id", "account", "enabled", "client_id", "last_synced_at", "sync_error"
            )
        ),
        "clients": [{"id": client.pk, "name": str(client)} for client in clients],
    }


@github_router.post("/github/installations")
def connect(request: HttpRequest, payload: InstallationIn) -> dict[str, int]:
    require(request, "manage_github")
    if not request.user.has_perms(
        ["infrastructure.add_infrastructureresource", "infrastructure.add_sourcerepository"]
    ):
        raise HttpError(403, "Repository creation permission required.")
    client = (
        scope_clients_for_user(request.user).filter(pk=payload.client_id).first()
        if payload.client_id
        else None
    )
    if payload.client_id and client is None:
        raise HttpError(404, "Client not found.")
    if payload.github_id <= 0:
        raise HttpError(422, "Enter a positive installation ID.")
    details = remote(GitHubClient(), "GET", f"/app/installations/{payload.github_id}")
    installation, _ = Installation.objects.get_or_create(
        github_id=payload.github_id, defaults={"account": details["account"]["login"]}
    )
    # Existing out-of-scope installation identifiers never permit reassignment.
    if (
        installation.client_id
        and not scope_clients_for_user(request.user).filter(pk=installation.client_id).exists()
    ):
        raise HttpError(404, "Installation not found.")
    if installation.repository_set.exists() and installation.client_id != payload.client_id:
        raise HttpError(409, "Ownership cannot change after repository import.")
    if details.get("suspended_at"):
        raise HttpError(409, "Unsuspend this installation in GitHub first.")
    installation.client = client
    installation.enabled = True
    installation.account = details["account"]["login"]
    installation.save()
    AuditEvent.record(
        action="github.installation_connected",
        actor=request.user,
        target=installation,
        client_id=installation.client_id,
        metadata={"github_id": installation.github_id},
    )
    synchronise.delay(installation.pk)
    return {"id": installation.pk}


@github_router.post("/github/installations/{installation_id}/sync")
def sync(request: HttpRequest, installation_id: int) -> dict[str, bool]:
    require(request, "manage_github")
    installation = Installation.objects.filter(pk=installation_id, enabled=True).first()
    if installation is None or (
        installation.client_id
        and not scope_clients_for_user(request.user).filter(pk=installation.client_id).exists()
    ):
        raise HttpError(404, "Installation not found.")
    synchronise.delay(installation.pk)
    return {"queued": True}


@github_router.post("/github/repositories/{repository_id}/workflows/{workflow_id}/dispatch")
def dispatch(
    request: HttpRequest, repository_id: int, workflow_id: int, payload: DispatchIn
) -> dict[str, bool]:
    repository = repo_for(request, repository_id)
    require(request, "trigger_workflow")
    if not Item.objects.filter(
        repository=repository, kind="workflow", github_id=workflow_id, state="active"
    ).exists():
        raise HttpError(404, "Active workflow not found.")
    if (
        not payload.ref.strip()
        or len(payload.ref) > 300
        or len(payload.inputs) > 25
        or any(len(key) > 100 or len(value) > 1000 for key, value in payload.inputs.items())
    ):
        raise HttpError(422, "A branch or tag and valid workflow inputs are required.")
    remote(
        GitHubClient(repository.installation.github_id),
        "POST",
        f"/repos/{repository.full_name}/actions/workflows/{workflow_id}/dispatches",
        {"ref": payload.ref, "inputs": payload.inputs},
    )
    WorkflowAction.objects.create(
        repository=repository,
        actor=cast(User, request.user),
        action="dispatch",
        remote_id=workflow_id,
        ref=payload.ref,
    )
    AuditEvent.record(
        action="github.workflow_started",
        actor=request.user,
        target=repository.source.resource,
        metadata={"github_id": workflow_id, "ref": payload.ref},
    )
    return {"started": True}


@github_router.post("/github/repositories/{repository_id}/runs/{run_id}/rerun")
def rerun(request: HttpRequest, repository_id: int, run_id: int) -> dict[str, bool]:
    repository = repo_for(request, repository_id)
    require(request, "trigger_workflow")
    if not Item.objects.filter(
        repository=repository,
        kind="run",
        github_id=run_id,
        state="completed",
        conclusion__in=["failure", "timed_out"],
    ).exists():
        raise HttpError(409, "Choose a completed failed run.")
    remote(
        GitHubClient(repository.installation.github_id),
        "POST",
        f"/repos/{repository.full_name}/actions/runs/{run_id}/rerun-failed-jobs",
    )
    WorkflowAction.objects.create(
        repository=repository,
        actor=cast(User, request.user),
        action="rerun_failed",
        remote_id=run_id,
    )
    AuditEvent.record(
        action="github.failed_jobs_rerun",
        actor=request.user,
        target=repository.source.resource,
        metadata={"github_id": run_id},
    )
    return {"started": True}


@github_router.get("/github/repositories/{repository_id}/runs/{run_id}/jobs")
def jobs(request: HttpRequest, repository_id: int, run_id: int, page: int = 1) -> dict[str, Any]:
    repository = repo_for(request, repository_id)
    if not Item.objects.filter(repository=repository, kind="run", github_id=run_id).exists():
        raise HttpError(404, "Run not found.")
    page = max(1, page)
    result = remote(
        GitHubClient(repository.installation.github_id),
        "GET",
        f"/repos/{repository.full_name}/actions/runs/{run_id}/jobs?per_page=25&page={page}",
    )
    rows = result["jobs"]
    return {
        "total": result["total_count"],
        "page": page,
        "rows": [
            {
                "id": row["id"],
                "name": row["name"],
                "status": row["status"],
                "conclusion": row.get("conclusion"),
                "url": row["html_url"],
            }
            for row in rows
        ],
    }


@github_router.get("/github/repositories/{repository_id}/runs/{run_id}/jobs/{job_id}/logs")
def logs(request: HttpRequest, repository_id: int, run_id: int, job_id: int) -> dict[str, Any]:
    repository = repo_for(request, repository_id)
    require(request, "view_workflow_logs")
    # Verify the job belongs to this visible run before retrieving its signed log URL.
    if not Item.objects.filter(repository=repository, kind="run", github_id=run_id).exists():
        raise HttpError(404, "Run not found.")
    client = GitHubClient(repository.installation.github_id)
    job = remote(client, "GET", f"/repos/{repository.full_name}/actions/jobs/{job_id}")
    if job["run_id"] != run_id:
        raise HttpError(404, "Job not found in this run.")
    try:
        text, truncated = client.job_logs(repository.full_name, job_id)
    except GitHubError as exc:
        raise HttpError(502, str(exc)) from exc
    WorkflowAction.objects.create(
        repository=repository, actor=cast(User, request.user), action="view_logs", remote_id=job_id
    )
    AuditEvent.record(
        action="github.logs_viewed",
        actor=request.user,
        target=repository.source.resource,
        metadata={"github_id": job_id},
    )
    return {"text": text, "truncated": truncated}
