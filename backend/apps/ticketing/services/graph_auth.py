from __future__ import annotations

import base64
import json
import time
import uuid
from typing import Any
from urllib.parse import quote

import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from django.utils import timezone

from apps.core.ownership import OwnershipType
from apps.credentials.secrets import CredentialEncryptionError, load_credential_secrets_for_service
from apps.ticketing.models import MicrosoftGraphConnection

GRAPH_SCOPE = "https://graph.microsoft.com/.default"
CLIENT_ASSERTION_TYPE = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
ASSERTION_LIFETIME_SECONDS = 300
TOKEN_EXPIRY_SKEW_SECONDS = 60


class MicrosoftGraphAuthenticationError(RuntimeError):
    """Microsoft Graph application authentication could not be completed safely."""


class MicrosoftGraphTokenProvider:
    """Acquire and cache app-only Microsoft Graph tokens for one connection."""

    def __init__(
        self,
        connection: MicrosoftGraphConnection,
        *,
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.connection = connection
        self._session = session or requests.Session()
        self._timeout_seconds = timeout_seconds
        self._access_token = ""
        self._expires_at = 0.0

    def __call__(self) -> str:
        return self.get_access_token()

    def get_access_token(self) -> str:
        """Return a cached token or acquire a fresh app-only Graph token."""
        if self._access_token and time.time() < self._expires_at - TOKEN_EXPIRY_SKEW_SECONDS:
            return self._access_token

        try:
            token, expires_in = self._acquire_access_token()
        except Exception as exc:
            self._record_error(exc)
            raise

        self._access_token = token
        self._expires_at = time.time() + expires_in
        self.connection.last_verified_at = timezone.now()
        self.connection.last_error = ""
        self.connection.save(update_fields=["last_verified_at", "last_error", "updated_at"])
        return token

    def _acquire_access_token(self) -> tuple[str, int]:
        if not self.connection.enabled:
            raise MicrosoftGraphAuthenticationError("Microsoft Graph connection is disabled.")
        if self.connection.credential is None:
            raise MicrosoftGraphAuthenticationError(
                "Microsoft Graph connection has no authentication credential."
            )
        if self.connection.credential.ownership_type != OwnershipType.INTERNAL:
            raise MicrosoftGraphAuthenticationError(
                "Microsoft Graph authentication requires an internal credential."
            )

        try:
            secrets = load_credential_secrets_for_service(self.connection.credential)
        except CredentialEncryptionError as exc:
            raise MicrosoftGraphAuthenticationError(
                "Microsoft Graph credential could not be decrypted."
            ) from exc

        token_url = _token_url(self.connection.tenant_id)
        data: dict[str, str] = {
            "client_id": self.connection.client_id,
            "scope": GRAPH_SCOPE,
            "grant_type": "client_credentials",
        }
        if (
            self.connection.authentication_method
            == MicrosoftGraphConnection.AuthenticationMethod.CLIENT_SECRET
        ):
            client_secret = secrets.get("client_secret", "")
            if not client_secret:
                raise MicrosoftGraphAuthenticationError(
                    "Microsoft Graph client-secret credential has no client_secret value."
                )
            data["client_secret"] = client_secret
        elif (
            self.connection.authentication_method
            == MicrosoftGraphConnection.AuthenticationMethod.CERTIFICATE
        ):
            data["client_assertion_type"] = CLIENT_ASSERTION_TYPE
            data["client_assertion"] = _build_certificate_assertion(
                token_url=token_url,
                client_id=self.connection.client_id,
                secrets=secrets,
            )
        else:
            raise MicrosoftGraphAuthenticationError(
                "Delegated Microsoft Graph authentication is not supported by background mailbox sync."
            )

        try:
            response = self._session.post(
                token_url,
                data=data,
                headers={"Accept": "application/json"},
                timeout=self._timeout_seconds,
            )
        except requests.RequestException as exc:
            raise MicrosoftGraphAuthenticationError(
                "Microsoft identity platform token request failed."
            ) from exc

        if response.status_code >= 400:
            request_id = response.headers.get("x-ms-request-id", "unknown")
            raise MicrosoftGraphAuthenticationError(
                f"Microsoft identity platform rejected Graph authentication with status "
                f"{response.status_code} (request ID {request_id})."
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise MicrosoftGraphAuthenticationError(
                "Microsoft identity platform returned a non-JSON token response."
            ) from exc
        if not isinstance(payload, dict):
            raise MicrosoftGraphAuthenticationError(
                "Microsoft identity platform returned an invalid token response."
            )

        token = str(payload.get("access_token") or "").strip()
        if not token:
            raise MicrosoftGraphAuthenticationError(
                "Microsoft identity platform token response contained no access token."
            )
        try:
            expires_in = max(
                int(payload.get("expires_in", 3600)),
                TOKEN_EXPIRY_SKEW_SECONDS + 1,
            )
        except (TypeError, ValueError) as exc:
            raise MicrosoftGraphAuthenticationError(
                "Microsoft identity platform token response contained an invalid expiry."
            ) from exc
        return token, expires_in

    def _record_error(self, exc: Exception) -> None:
        self.connection.last_error = f"{type(exc).__name__}: {exc}"[:2000]
        self.connection.save(update_fields=["last_error", "updated_at"])


def _build_certificate_assertion(
    *,
    token_url: str,
    client_id: str,
    secrets: dict[str, str],
) -> str:
    private_key_pem = secrets.get("private_key", "")
    certificate_pem = secrets.get("certificate", "")
    if not private_key_pem or not certificate_pem:
        raise MicrosoftGraphAuthenticationError(
            "Microsoft Graph certificate credential requires private_key and certificate values."
        )

    passphrase = secrets.get("passphrase", "")
    try:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode("utf-8"),
            password=passphrase.encode("utf-8") if passphrase else None,
        )
        certificate = x509.load_pem_x509_certificate(certificate_pem.encode("utf-8"))
    except (TypeError, ValueError) as exc:
        raise MicrosoftGraphAuthenticationError(
            "Microsoft Graph certificate credential contains invalid PEM material."
        ) from exc
    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise MicrosoftGraphAuthenticationError(
            "Microsoft Graph certificate authentication requires an RSA private key."
        )

    now = int(time.time())
    header = {
        "alg": "PS256",
        "typ": "JWT",
        "x5t#S256": _base64url(certificate.fingerprint(hashes.SHA256())),
    }
    claims = {
        "aud": token_url,
        "exp": now + ASSERTION_LIFETIME_SECONDS,
        "iss": client_id,
        "jti": str(uuid.uuid4()),
        "nbf": now - 5,
        "sub": client_id,
    }
    signing_input = (f"{_base64url(_json_bytes(header))}.{_base64url(_json_bytes(claims))}").encode(
        "ascii"
    )
    signature = private_key.sign(
        signing_input,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=hashes.SHA256().digest_size,
        ),
        hashes.SHA256(),
    )
    return f"{signing_input.decode('ascii')}.{_base64url(signature)}"


def _token_url(tenant_id: str) -> str:
    tenant = tenant_id.strip()
    if not tenant:
        raise MicrosoftGraphAuthenticationError("Microsoft Graph tenant ID is required.")
    return f"https://login.microsoftonline.com/{quote(tenant, safe='')}/oauth2/v2.0/token"


def _json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")
