from __future__ import annotations

import logging
from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.crm.models import Lead
from apps.ticketing.services.contact_forms import ingest_website_contact_lead

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Lead, dispatch_uid="ticketing_ingest_contact_form_lead")
def ingest_contact_form_lead(
    sender: type[Lead],
    instance: Lead,
    created: bool,
    **kwargs: Any,
) -> None:
    """Feed newly persisted website contact leads into ticketing without risking lead capture."""
    del sender, kwargs
    if not created or instance.source_id is None:
        return

    source = instance.source
    if source is None or source.name.strip().casefold() != "contact form":
        return

    try:
        ingest_website_contact_lead(instance)
    except Exception:
        logger.exception(
            "Ticket ingestion failed for website contact Lead %s; the CRM Lead remains captured.",
            instance.pk,
        )
