from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client, ClientContact
from apps.crm.models import Lead, LeadStatus
from apps.ticketing.models import Ticket, TicketMessage
from authentication.models import User


class LeadOperationError(ValueError):
    """Raised when a lead operation cannot be completed safely."""


@dataclass(frozen=True)
class LeadConversionResult:
    client: Client
    contact: ClientContact
    linked_ticket_count: int


def assign_lead(lead: Lead, assignee: User | None) -> Lead:
    if lead.converted_at is not None:
        raise LeadOperationError("Converted leads cannot be reassigned.")
    lead.assigned_to = assignee
    lead.save(update_fields=["assigned_to", "updated_at"])
    return lead


def _grant_client_access(user: User, client: Client) -> None:
    if user.is_superuser:
        return

    profile, _ = StaffAccessProfile.objects.get_or_create(user=user)
    if profile.all_clients:
        return

    ClientAccessGrant.objects.get_or_create(
        profile=profile,
        client=client,
        defaults={"granted_by": user},
    )


def _matching_unlinked_ticket_ids(lead: Lead) -> list[int]:
    tickets = Ticket.objects.filter(client__isnull=True).filter(
        Q(messages__sender_address__iexact=lead.email)
        | Q(messages__to_recipients__contains=[lead.email])
    )
    if lead.brand_id is not None:
        tickets = tickets.filter(brand_id=lead.brand_id)
    return list(tickets.values_list("id", flat=True).distinct())


def _won_status(lead: Lead) -> LeadStatus:
    if lead.status is not None and lead.status.outcome == LeadStatus.Outcome.WON:
        return lead.status
    stage = (
        LeadStatus.objects.filter(outcome=LeadStatus.Outcome.WON).order_by("order", "id").first()
    )
    if stage is None:
        raise LeadOperationError("Configure a Won sales stage before converting this lead.")
    return stage


@transaction.atomic
def change_lead_stage(lead: Lead, stage: LeadStatus) -> Lead:
    locked = Lead.objects.select_for_update().get(pk=lead.pk)
    if locked.converted_at is not None and stage.outcome != LeadStatus.Outcome.WON:
        raise LeadOperationError("Converted leads must remain in a Won sales stage.")
    locked.status = stage
    locked.save(update_fields=["status", "updated_at"])
    lead.status = stage
    lead.updated_at = locked.updated_at
    return lead


@transaction.atomic
def convert_lead(lead: Lead, converted_by: User) -> LeadConversionResult:
    locked_lead = Lead.objects.select_for_update().get(pk=lead.pk)
    if locked_lead.converted_at is not None or locked_lead.converted_client_id is not None:
        raise LeadOperationError("This lead has already been converted.")

    won_status = _won_status(locked_lead)

    client = Client(
        name=locked_lead.name,
        company=locked_lead.company,
        email=locked_lead.email,
        phone=locked_lead.phone,
        notes=locked_lead.notes,
    )
    client.full_clean()
    client.save()

    contact = ClientContact(
        client=client,
        name=locked_lead.name,
        email=locked_lead.email,
        phone=locked_lead.phone,
        is_primary=True,
    )
    contact.full_clean()
    contact.save()

    _grant_client_access(converted_by, client)

    ticket_ids = _matching_unlinked_ticket_ids(locked_lead)
    if ticket_ids:
        Ticket.objects.filter(id__in=ticket_ids, client__isnull=True).update(
            client=client,
            primary_contact=contact,
        )
        TicketMessage.objects.filter(
            ticket_id__in=ticket_ids,
            matched_contact__isnull=True,
            sender_address__iexact=locked_lead.email,
        ).update(matched_contact=contact)

    locked_lead.status = won_status
    locked_lead.converted_client = client
    locked_lead.converted_contact = contact
    locked_lead.converted_by = converted_by
    locked_lead.converted_at = timezone.now()
    locked_lead.save(
        update_fields=[
            "status",
            "converted_client",
            "converted_contact",
            "converted_by",
            "converted_at",
            "updated_at",
        ]
    )

    lead.status = won_status
    lead.converted_client = client
    lead.converted_contact = contact
    lead.converted_by = converted_by
    lead.converted_at = locked_lead.converted_at
    lead.updated_at = locked_lead.updated_at

    return LeadConversionResult(
        client=client,
        contact=contact,
        linked_ticket_count=len(ticket_ids),
    )
