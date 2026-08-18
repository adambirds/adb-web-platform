from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from apps.core.models import AuditEvent
from apps.credentials.models import StoredCredential

SECRET_PAYLOAD_VERSION = 1


class CredentialEncryptionError(RuntimeError):
    """Base exception for encrypted credential-secret operations."""


class CredentialEncryptionNotConfiguredError(CredentialEncryptionError):
    """No valid credential encryption key is configured."""


class CredentialDecryptionError(CredentialEncryptionError):
    """A stored encrypted credential payload cannot be decrypted safely."""


def store_credential_secrets(
    credential: StoredCredential,
    secrets: Mapping[str, str],
    *,
    mark_rotated: bool = True,
) -> None:
    """Encrypt and persist secret material without touching legacy plaintext fields."""
    payload = _normalise_secrets(secrets)
    if not payload:
        raise CredentialEncryptionError("At least one non-empty credential secret is required.")

    encoded = json.dumps(
        {"version": SECRET_PAYLOAD_VERSION, "secrets": payload},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    credential.encrypted_secret_payload = _fernet().encrypt(encoded).decode("ascii")
    credential.secret_payload_version = SECRET_PAYLOAD_VERSION

    update_fields = ["encrypted_secret_payload", "secret_payload_version", "updated_at"]
    if mark_rotated:
        credential.last_rotated_at = timezone.now()
        update_fields.append("last_rotated_at")
    credential.save(update_fields=update_fields)


def load_credential_secrets_for_service(credential: StoredCredential) -> dict[str, str]:
    """Decrypt secret material for trusted backend integrations such as Graph."""
    return _decrypt_payload(credential)


def reveal_credential_secrets(
    credential: StoredCredential,
    *,
    actor: Any,
    ip_address: str | None = None,
    user_agent: str = "",
) -> dict[str, str]:
    """Reveal secret material to an authorised human and always audit the event."""
    if not getattr(actor, "is_authenticated", False) or not actor.has_perm(
        "credentials.reveal_storedcredential"
    ):
        raise PermissionDenied("You do not have permission to reveal credential secrets.")

    secrets = _decrypt_payload(credential)
    AuditEvent.record(
        action="credentials.secret_revealed",
        actor=actor,
        target=credential,
        metadata={"secret_fields": sorted(secrets)},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return secrets


def rotate_credential_encryption(credential: StoredCredential) -> None:
    """Re-encrypt an existing payload with the current primary encryption key."""
    secrets = _decrypt_payload(credential)
    store_credential_secrets(credential, secrets, mark_rotated=True)


def clear_credential_secrets(credential: StoredCredential) -> None:
    """Remove only the encrypted secret payload, leaving credential metadata intact."""
    credential.encrypted_secret_payload = ""
    credential.secret_payload_version = SECRET_PAYLOAD_VERSION
    credential.last_rotated_at = timezone.now()
    credential.save(
        update_fields=[
            "encrypted_secret_payload",
            "secret_payload_version",
            "last_rotated_at",
            "updated_at",
        ]
    )


def _decrypt_payload(credential: StoredCredential) -> dict[str, str]:
    if not credential.encrypted_secret_payload:
        raise CredentialDecryptionError("Credential has no encrypted secret payload.")
    try:
        plaintext = _fernet().decrypt(credential.encrypted_secret_payload.encode("ascii"))
    except (InvalidToken, UnicodeEncodeError) as exc:
        raise CredentialDecryptionError(
            "Credential secret payload could not be decrypted."
        ) from exc

    try:
        decoded = json.loads(plaintext.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CredentialDecryptionError("Credential secret payload is invalid.") from exc

    if not isinstance(decoded, dict) or decoded.get("version") != SECRET_PAYLOAD_VERSION:
        raise CredentialDecryptionError("Credential secret payload version is unsupported.")
    secrets = decoded.get("secrets")
    if not isinstance(secrets, dict):
        raise CredentialDecryptionError("Credential secret payload has no secrets object.")

    result = {
        key: value
        for key, value in secrets.items()
        if isinstance(key, str) and isinstance(value, str) and value
    }
    if not result:
        raise CredentialDecryptionError("Credential secret payload is empty.")
    return result


def _normalise_secrets(secrets: Mapping[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in secrets.items():
        normalised_key = key.strip()
        if normalised_key and value:
            result[normalised_key] = value
    return result


def _configured_keys() -> list[str]:
    configured = getattr(settings, "CREDENTIAL_ENCRYPTION_KEYS", None)
    if configured is None:
        configured = os.environ.get("CREDENTIAL_ENCRYPTION_KEYS", "")
    if isinstance(configured, str):
        return [item.strip() for item in configured.split(",") if item.strip()]
    return [str(item).strip() for item in configured if str(item).strip()]


def _fernet() -> MultiFernet:
    configured_keys = _configured_keys()
    if not configured_keys:
        raise CredentialEncryptionNotConfiguredError(
            "CREDENTIAL_ENCRYPTION_KEYS must contain at least one Fernet key."
        )

    try:
        fernets = [Fernet(key.encode("ascii")) for key in configured_keys]
    except (ValueError, UnicodeEncodeError) as exc:
        raise CredentialEncryptionNotConfiguredError(
            "CREDENTIAL_ENCRYPTION_KEYS contains an invalid Fernet key."
        ) from exc
    return MultiFernet(fernets)
