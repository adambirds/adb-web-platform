from django.db import models


class CredentialType(models.Model):
    """Type of credential such as SSH, database login or API key."""

    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True)

    def __str__(self) -> str:
        return self.name


class StoredCredential(models.Model):
    """Credential record.

    Secret fields are currently plaintext legacy storage and MUST NOT be used for
    production credentials until encrypted-at-rest storage is implemented.
    """

    name = models.CharField(max_length=200)
    credential_type = models.ForeignKey(
        CredentialType, on_delete=models.SET_NULL, null=True, blank=True
    )

    username = models.CharField(max_length=200, blank=True)
    password = models.CharField(max_length=500, blank=True)
    api_key = models.CharField(max_length=500, blank=True)
    secret_key = models.CharField(max_length=500, blank=True)
    private_key = models.TextField(blank=True)

    url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("reveal_storedcredential", "Can reveal stored credential secrets"),
            ("copy_storedcredential_secret", "Can copy stored credential secrets"),
        ]

    def __str__(self) -> str:
        return self.name
