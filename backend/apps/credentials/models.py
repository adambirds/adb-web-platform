from django.db import models


class CredentialType(models.Model):
    """Type of credential (e.g., SSH, MySQL, API Key)"""

    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class StoredCredential(models.Model):
    """Encrypted credential storage"""

    # This should be encrypted in production using django-encrypted-model-fields
    # For now, we'll store it plainly but mark where encryption should happen

    name = models.CharField(max_length=200)
    credential_type = models.ForeignKey(CredentialType, on_delete=models.SET_NULL, null=True, blank=True)

    username = models.CharField(max_length=200, blank=True)
    password = models.CharField(max_length=500, blank=True)  # TODO: Encrypt this field
    api_key = models.CharField(max_length=500, blank=True)  # TODO: Encrypt this field
    secret_key = models.CharField(max_length=500, blank=True)  # TODO: Encrypt this field
    private_key = models.TextField(blank=True)  # TODO: Encrypt this field (SSH keys, etc)

    # Additional metadata
    url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
