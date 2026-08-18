from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class OwnershipType(models.TextChoices):
    INTERNAL = "internal", "Internal"
    CLIENT = "client", "Client"


def ownership_constraint(name: str) -> models.CheckConstraint:
    """Require internal records to have no client and client-owned records to have one."""
    return models.CheckConstraint(
        condition=(
            Q(ownership_type=OwnershipType.INTERNAL, client__isnull=True)
            | Q(ownership_type=OwnershipType.CLIENT, client__isnull=False)
        ),
        name=name,
    )


def validate_ownership(instance: Any) -> None:
    """Validate the shared client/internal ownership invariant on a model instance."""
    ownership_type = getattr(instance, "ownership_type", None)
    client_id = getattr(instance, "client_id", None)

    if ownership_type == OwnershipType.CLIENT and client_id is None:
        raise ValidationError({"client": "Client-owned records must reference a client."})
    if ownership_type == OwnershipType.INTERNAL and client_id is not None:
        raise ValidationError({"client": "Internal records must not reference a client."})
