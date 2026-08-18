from django.db import models

from apps.core.ownership import OwnershipType, ownership_constraint, validate_ownership


class CredentialType(models.Model):
    """Type of credential such as SSH, database login or API key."""

    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True)

    def __str__(self) -> str:
        return self.name


class StoredCredential(models.Model):
    """Client-owned or internal credential metadata and legacy secret storage.

    Secret fields remain plaintext legacy storage and MUST NOT be used for
    production credentials until encrypted-at-rest storage is implemented.
    """

    ownership_type = models.CharField(
        max_length=20,
        choices=OwnershipType.choices,
        default=OwnershipType.INTERNAL,
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="credentials",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)
    credential_type = models.ForeignKey(
        CredentialType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    username = models.CharField(max_length=200, blank=True)
    password = models.CharField(max_length=500, blank=True)
    api_key = models.CharField(max_length=500, blank=True)
    secret_key = models.CharField(max_length=500, blank=True)
    private_key = models.TextField(blank=True)

    url = models.URLField(blank=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    last_rotated_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [ownership_constraint("storedcredential_valid_ownership")]
        permissions = [
            ("reveal_storedcredential", "Can reveal stored credential secrets"),
            ("copy_storedcredential_secret", "Can copy stored credential secrets"),
        ]

    def clean(self) -> None:
        super().clean()
        validate_ownership(self)

    def __str__(self) -> str:
        return self.name
