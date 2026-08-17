from django.conf import settings
from django.db import models


class StaffAccessProfile(models.Model):
    """Object-scope settings that complement Django capability permissions."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="access_profile",
    )
    all_clients = models.BooleanField(
        default=False,
        help_text="Allow access to every client when the user also has the required capability permission.",
    )
    all_ticket_queues = models.BooleanField(
        default=False,
        help_text="Reserved for ticketing; selected queue grants will be added with the ticket domain.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ("manage_staff_access", "Can manage staff access scopes"),
        ]

    def __str__(self) -> str:
        return f"Access profile for {self.user.email}"


class ClientAccessGrant(models.Model):
    """Grant a staff user object-scope access to one client."""

    profile = models.ForeignKey(
        StaffAccessProfile,
        on_delete=models.CASCADE,
        related_name="client_grants",
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="access_grants",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client_access_grants_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "client"],
                name="unique_staff_client_access_grant",
            )
        ]
        ordering = ["client__name"]

    def __str__(self) -> str:
        return f"{self.profile.user.email} -> {self.client}"
