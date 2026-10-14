from __future__ import annotations

from dataclasses import replace
from typing import Any

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save

from .events import LiveChange, publish_change

# Only explicitly reviewed roots/parents participate; unknown models fail closed.
ROOTS = {
    "clients.Client": "clients",
    "clients.ClientContact": "clients",
    "clients.Project": "projects",
    "clients.ProjectNote": "projects",
    "clients.TimeEntry": "time",
    "clients.RunningTimer": "time",
    "tasks.Task": "tasks",
    "tasks.TaskList": "tasks",
    "tasks.TaskSection": "tasks",
    "tasks.TaskComment": "tasks",
    "tasks.CalendarEvent": "calendar",
    "crm.Lead": "leads",
    "crm.LeadRetentionReview": "retention",
    "crm.LeadSource": "leads",
    "crm.LeadStatus": "leads",
    "ticketing.Ticket": "tickets",
    "ticketing.TicketMessage": "tickets",
    "knowledge_base.KnowledgeBaseDocument": "knowledge",
    "knowledge_base.KnowledgeBaseSection": "knowledge",
    "credentials.StoredCredential": "credentials",
    "credentials.CredentialResourceLink": "credentials",
    "monitoring.MonitorCheck": "monitoring",
    "monitoring.MonitorIncident": "monitoring",
    "monitoring.MonitorResult": "monitoring",
    "github_integration.Repository": "github",
    "github_integration.Item": "github",
    "github_integration.Installation": "github",
    "core.AuditEvent": "activity",
    "core.Notification": "notifications",
    "access_control.StaffAccessProfile": "access",
    "access_control.ClientAccessGrant": "access",
    "access_control.TicketQueueAccessGrant": "access",
    "authentication.User": "access",
}
PARENTS = (
    "resource",
    "monitor_check",
    "credential",
    "ticket",
    "document",
    "task",
    "task_list",
    "project",
    "repository",
    "source",
    "installation",
    "profile",
    "source_resource",
    "target_resource",
    "server",
    "network",
    "subnet",
    "application",
)


def change_for(instance: Model, topic: str) -> LiveChange | None:
    label = instance._meta.label_lower
    if topic == "activity":
        actor_id = getattr(instance, "actor_id", None)
        return (
            LiveChange(topic, ("core.view_auditevent",), user_id=str(actor_id))
            if actor_id
            else None
        )
    if topic == "notifications":
        return LiveChange(topic, user_id=str(getattr(instance, "user_id", None)))
    if topic == "access":
        target: Any = instance
        if hasattr(instance, "profile_id"):
            target = getattr(instance, "profile", None)
        user_id = target.pk if label == "authentication.user" else getattr(target, "user_id", None)
        return LiveChange(topic, user_id=str(user_id)) if user_id else None
    permission = f"{instance._meta.app_label}.view_{instance._meta.model_name}"
    if topic == "github":
        permission = (
            "github_integration.manage_github"
            if label.endswith(".installation")
            else "github_integration.view_repository"
        )
    elif topic == "monitoring":
        permission = (
            "monitoring.view_monitorincident"
            if label.endswith(".monitorincident")
            else "monitoring.view_monitorcheck"
        )
    elif topic == "tickets":
        permission = "ticketing.view_ticket"
    elif topic == "credentials":
        permission = "credentials.view_storedcredential"
    elif topic == "tasks":
        permission = (
            "tasks.view_tasklist"
            if label.endswith((".tasklist", ".tasksection"))
            else "tasks.view_task"
        )
    elif topic == "leads":
        permission = "crm.view_lead"
    permissions = [permission]
    if topic == "retention":
        permissions.append("crm.view_lead")
    if topic in ("github", "monitoring"):
        permissions.append("infrastructure.view_infrastructureresource")
    context: Any = instance
    client_id = None
    queue_id = None
    internal = False
    global_scope = topic in (
        "leads",
        "retention",
    )  # CRM leads are staff-capability scoped, independent of Clients.
    for _ in range(7):
        if context._meta.label_lower == "clients.client":
            client_id = context.pk
            break
        current_client = getattr(context, "client_id", None)
        if current_client is not None:
            client_id = current_client
        current_queue = getattr(context, "queue_id", None)
        if current_queue is not None:
            queue_id = current_queue
        if getattr(context, "ownership_type", None) == "internal":
            internal = True
        # Installation ownership is explicit at approval; None is its Internal context.
        if context._meta.label_lower == "github_integration.installation":
            internal = context.client_id is None
            break
        parent = next(
            (
                getattr(context, field)
                for field in PARENTS
                if getattr(context, field + "_id", None) is not None
            ),
            None,
        )
        if parent is None:
            break
        context = parent
    user_id = (
        str(getattr(instance, "user_id", None))
        if topic == "time" and getattr(instance, "user_id", None)
        else None
    )
    if not any((client_id, queue_id, internal, global_scope, user_id)):
        # Catalogue records are intentionally shared; business records are never inferred global.
        global_scope = label in (
            "infrastructure.serviceprovider",
            "infrastructure.infrastructuretag",
        )
    return LiveChange(
        topic, tuple(permissions), client_id, queue_id, user_id, internal, global_scope
    )


def changed(sender: type[Model], instance: Model, **kwargs: Any) -> None:
    if kwargs.get("raw"):
        return
    topic = ROOTS.get(sender._meta.label)
    if sender._meta.app_label == "infrastructure":
        topic = "infrastructure"
    if topic:
        try:
            change = change_for(instance, topic)
        except ObjectDoesNotExist:
            return  # Cascaded deletion of an already-removed parent; reconciliation catches up.
        if change:
            publish_change(change)
            previous = getattr(instance, "_live_previous_scope", None)
            if previous:
                publish_change(
                    replace(
                        change,
                        client_id=previous.get("client_id", change.client_id),
                        queue_id=previous.get("queue_id", change.queue_id),
                        internal=previous.get(
                            "ownership_type", "internal" if change.internal else "client"
                        )
                        == "internal",
                    )
                )


def membership_changed(sender: type[Model], instance: Any, action: str, **kwargs: Any) -> None:
    if action not in ("post_add", "post_remove", "post_clear"):
        return
    if instance._meta.label_lower == "authentication.user":
        publish_change(LiveChange("access", user_id=str(instance.pk)))
    else:
        # Control-only hint: refresh one's own permissions; no user/group details leave Redis.
        publish_change(LiveChange("access", global_scope=True))


def previous_scope(sender: type[Model], instance: Model, **kwargs: Any) -> None:
    if kwargs.get("raw") or not instance.pk:
        return
    names = {field.attname for field in sender._meta.concrete_fields}
    fields = list(names.intersection({"client_id", "queue_id", "ownership_type"}))
    if not fields:
        return
    old = sender._default_manager.filter(pk=instance.pk).values(*fields).first()
    if old and any(old[field] != getattr(instance, field) for field in fields):
        instance.__dict__["_live_previous_scope"] = old
    else:
        instance.__dict__["_live_previous_scope"] = None


def register() -> None:
    for model in apps.get_models():
        if model._meta.label in ROOTS or model._meta.app_label == "infrastructure":
            pre_save.connect(
                previous_scope, sender=model, dispatch_uid=f"live-before:{model._meta.label}"
            )
            post_save.connect(changed, sender=model, dispatch_uid=f"live-save:{model._meta.label}")
            post_delete.connect(
                changed, sender=model, dispatch_uid=f"live-delete:{model._meta.label}"
            )
    from django.contrib.auth.models import Group

    from authentication.models import User

    for through in (User.user_permissions.through, User.groups.through, Group.permissions.through):
        m2m_changed.connect(
            membership_changed, sender=through, dispatch_uid=f"live-m2m:{through._meta.label}"
        )
