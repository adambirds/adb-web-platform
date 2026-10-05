from __future__ import annotations

import hashlib
import hmac
import json
import re
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Delivery, Installation, Repository


def enqueue(delivery_id: int) -> None:
    from .tasks import process_delivery

    try:
        process_delivery.delay(delivery_id)
    except Exception:
        # Durable delivery remains pending. Beat retries when the broker returns.
        Delivery.objects.filter(pk=delivery_id).update(error="Awaiting background worker.")


@csrf_exempt
@require_POST
def webhook(request: HttpRequest) -> JsonResponse:
    secret = settings.GITHUB_WEBHOOK_SECRET
    if not secret:
        return JsonResponse({"message": "GitHub webhook is not configured."}, status=503)
    if len(request.body) > 5_000_000:
        return JsonResponse({"message": "Payload too large."}, status=413)
    signature = "sha256=" + hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, request.headers.get("X-Hub-Signature-256", "")):
        return JsonResponse({"message": "Invalid signature."}, status=403)
    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    event = request.headers.get("X-GitHub-Event", "")
    if not re.fullmatch(r"[A-Za-z0-9-]{1,100}", delivery_id):
        return JsonResponse({"message": "Invalid delivery ID."}, status=400)
    try:
        data: dict[str, Any] = json.loads(request.body)
        installation = data.get("installation") or {}
        account = installation.get("account") or {}
        repository = data.get("repository") or {}
        kind = {"issues": "issue", "pull_request": "pull_request", "workflow_run": "run"}.get(event)
        item = (
            data.get(
                {"issue": "issue", "pull_request": "pull_request", "run": "workflow_run"}.get(
                    kind or "", ""
                )
            )
            or {}
        )
        # Store routing metadata only, never bodies, commits, logs or webhook secrets.
        payload: dict[str, Any] = {
            "installation_id": int(installation.get("id", 0)),
            "account": str(account.get("login", ""))[:200],
            "repository_id": int(repository.get("id", 0)),
            "action": str(data.get("action", ""))[:100],
            "kind": kind,
            "number": int(item.get("number", 0)),
            "item_id": int(item.get("id", 0)),
            "run_id": int((data.get("workflow_job") or {}).get("run_id", 0)),
            "removed": [int(repo["id"]) for repo in data.get("repositories_removed", [])],
        }
    except (ValueError, TypeError, AttributeError, KeyError):
        return JsonResponse({"message": "Invalid payload."}, status=400)
    delivery, created = Delivery.objects.get_or_create(
        delivery_id=delivery_id,
        defaults={"event": event[:100], "payload": payload},
    )
    # Revoke visibility before asynchronous work, including access tokens.
    if event == "installation" and payload["action"] in ("deleted", "suspend"):
        for installation in Installation.objects.filter(github_id=payload["installation_id"]):
            installation.enabled = False
            installation.save(update_fields=["enabled"])
        for repository in Repository.objects.filter(
            installation__github_id=payload["installation_id"]
        ):
            repository.active = False
            repository.save(update_fields=["active"])
        cache.delete(f"github-installation-token:{payload['installation_id']}")
    if event == "repository" and payload["action"] == "deleted":
        for repository in Repository.objects.filter(
            installation__github_id=payload["installation_id"], github_id=payload["repository_id"]
        ):
            repository.active = False
            repository.save(update_fields=["active"])
    if payload["removed"]:
        for repository in Repository.objects.filter(
            installation__github_id=payload["installation_id"], github_id__in=payload["removed"]
        ):
            repository.active = False
            repository.save(update_fields=["active"])
    if created:
        enqueue(delivery.pk)
    return JsonResponse({"accepted": True}, status=202 if created else 200)
