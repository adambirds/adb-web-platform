"""Google OAuth and bounded official REST API transport. No provider secrets in errors."""

import base64
import hashlib
import secrets
from datetime import timedelta
from typing import Any
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from ninja.errors import HttpError

from apps.analytics.access import business_for
from apps.analytics.models import GoogleConnection
from apps.core.models import AuditEvent
from apps.credentials.models import StoredCredential
from apps.credentials.secrets import load_credential_secrets_for_service, store_credential_secrets
from authentication.custom_request import AuthenticatedHttpRequest

READ = "https://www.googleapis.com/auth/analytics.readonly"
EDIT = "https://www.googleapis.com/auth/analytics.edit"
SEARCH = "https://www.googleapis.com/auth/webmasters.readonly"
# Keep legacy mode names compatible; every new consent covers supported functionality.
REQUIRED_SCOPES = [READ, SEARCH, EDIT]
SCOPES = {"reporting": REQUIRED_SCOPES, "administration": REQUIRED_SCOPES}
ADMIN_URL = "https://analyticsadmin.googleapis.com/v1beta/"
DATA_URL = "https://analyticsdata.googleapis.com/v1beta/"
SEARCH_URL = "https://www.googleapis.com/webmasters/v3/"
TOKEN_URL = "https://oauth2.googleapis.com/token"


class ProviderError(Exception):
    def __init__(
        self, code: str, *, retryable: bool = False, retry_after: int | None = None
    ) -> None:
        self.code = code
        self.retryable = retryable
        self.retry_after = retry_after
        super().__init__(code)


def oauth_start(
    request: AuthenticatedHttpRequest,
    business_id: int,
    mode: str,
    connection_id: int | None = None,
    return_to: str = "onboarding",
) -> str:
    business_for(request.user, business_id, "change_googleconnection")
    if not settings.ANALYTICS_GOOGLE_CLIENT_ID or not settings.ANALYTICS_GOOGLE_CLIENT_SECRET:
        raise HttpError(503, "Google OAuth is not configured. Contact the platform administrator.")
    if (
        connection_id is not None
        and not GoogleConnection.objects.filter(pk=connection_id, business_id=business_id).exists()
    ):
        raise HttpError(404, "Google connection not found in this workspace.")
    verifier = secrets.token_urlsafe(64)
    state = secrets.token_urlsafe(32)
    request.session["analytics_oauth"] = {
        "state": state,
        "verifier": verifier,
        "business": business_id,
        "actor": str(request.user.pk),
        "mode": mode,
        "connection": connection_id,
        "return_to": return_to,
        "issued": timezone.now().timestamp(),
    }
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    )
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(
        {
            "client_id": settings.ANALYTICS_GOOGLE_CLIENT_ID,
            "redirect_uri": settings.ANALYTICS_GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join([*SCOPES[mode], "openid", "email"]),
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
        }
    )


def _json(response: requests.Response) -> dict[str, Any]:
    if response.status_code >= 400:
        status = response.status_code
        quota = status == 429
        if status == 403:
            try:
                error = response.json().get("error", {})
                quota = isinstance(error, dict) and (
                    error.get("status") == "RESOURCE_EXHAUSTED"
                    or any(
                        item.get("reason")
                        in {
                            "rateLimitExceeded",
                            "userRateLimitExceeded",
                            "quotaExceeded",
                            "dailyLimitExceeded",
                        }
                        for item in error.get("errors", [])
                    )
                )
            except (ValueError, AttributeError, TypeError):
                quota = False
        code = (
            "quota_exceeded"
            if quota
            else {
                400: "invalid_google_request",
                401: "credentials_revoked",
                403: "google_permission_denied",
            }.get(status, "google_unavailable")
        )
        try:
            retry_after = max(0, min(int(response.headers.get("Retry-After", "0")), 86400)) or None
        except (ValueError, TypeError):
            retry_after = None
        raise ProviderError(
            code, retryable=quota or status >= 500 or status in {408, 425}, retry_after=retry_after
        )
    if response.status_code == 204 or not response.content:
        return {}
    try:
        result = response.json()
    except ValueError:
        raise ProviderError("invalid_provider_response", retryable=True) from None
    if not isinstance(result, dict):
        raise ProviderError("invalid_provider_response")
    return result


def token_request(data: dict[str, str]) -> dict[str, Any]:
    try:
        response = requests.post(
            TOKEN_URL,
            data={
                **data,
                "client_id": settings.ANALYTICS_GOOGLE_CLIENT_ID,
                "client_secret": settings.ANALYTICS_GOOGLE_CLIENT_SECRET,
            },
            timeout=30,
            allow_redirects=False,
        )
        if response.status_code in {400, 401}:
            try:
                reason = response.json().get("error", "")
            except (ValueError, AttributeError):
                reason = ""
            if reason in {"invalid_grant", "access_denied"}:
                raise ProviderError("credentials_revoked")
            if reason in {"temporarily_unavailable", "server_error"}:
                raise ProviderError("google_unavailable", retryable=True)
            if reason in {"invalid_client", "unauthorized_client"}:
                raise ProviderError("oauth_client_configuration")
            raise ProviderError("oauth_request_rejected")
        return _json(response)
    except requests.RequestException:
        raise ProviderError("google_unavailable", retryable=True) from None


def token_lifetime(tokens: dict[str, Any]) -> int:
    try:
        lifetime = int(tokens.get("expires_in", 3600))
        if lifetime <= 0:
            raise ValueError
        return lifetime
    except (TypeError, ValueError, OverflowError):
        raise ProviderError("invalid_provider_response", retryable=True) from None


def consume_oauth_state(request: AuthenticatedHttpRequest, state: str) -> dict[str, Any]:
    pending = request.session.pop("analytics_oauth", None)
    # Persist consumption even when a provider call fails; state cannot be replayed.
    request.session.save()
    if (
        not pending
        or not secrets.compare_digest(pending["state"], state)
        or pending["actor"] != str(request.user.pk)
        or not 0 <= timezone.now().timestamp() - pending["issued"] <= 600
    ):
        raise HttpError(400, "OAuth state is invalid or expired. Start the connection again.")
    return pending


@transaction.atomic
def oauth_callback(request: AuthenticatedHttpRequest, state: str, code: str) -> GoogleConnection:
    pending = consume_oauth_state(request, state)
    business = business_for(request.user, pending["business"], "change_googleconnection")
    existing = None
    if pending.get("connection") is not None:
        existing = (
            GoogleConnection.objects.select_for_update()
            .select_related("credential")
            .filter(
                pk=pending["connection"],
                business=business,
            )
            .first()
        )
        if existing is None:
            raise HttpError(404, "Google connection no longer exists.")
    tokens = token_request(
        {
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": pending["verifier"],
            "redirect_uri": settings.ANALYTICS_GOOGLE_REDIRECT_URI,
        }
    )
    if not tokens.get("access_token"):
        raise ProviderError("google_access_not_granted")
    identity = authorized_request(
        str(tokens["access_token"]), "GET", "https://openidconnect.googleapis.com/v1/userinfo"
    )
    if not identity.get("sub") or not identity.get("email"):
        raise ProviderError("google_identity_unverified")
    if existing and (
        (existing.subject and existing.subject != identity["sub"])
        or (not existing.subject and existing.email and existing.email != identity["email"])
    ):
        raise ProviderError("google_account_mismatch")
    secrets_payload = load_credential_secrets_for_service(existing.credential) if existing else {}
    secrets_payload["access_token"] = str(tokens["access_token"])
    if tokens.get("refresh_token"):
        secrets_payload["refresh_token"] = str(tokens["refresh_token"])
    elif (
        existing and existing.status == "reconnect" and existing.error_code == "credentials_revoked"
    ):
        # A known revoked offline grant cannot be repaired with an access token
        # alone. Never claim unattended recovery while retaining that grant.
        secrets_payload.pop("refresh_token", None)
    if not secrets_payload.get("refresh_token"):
        raise ProviderError("offline_access_required")
    credential = (
        existing.credential
        if existing
        else StoredCredential.objects.create(
            name=f"Analytics Google OAuth — business {business.pk}",
            created_by=request.user,
            metadata={"service": "analytics-google"},
        )
    )
    store_credential_secrets(credential, secrets_payload)
    connection = existing or GoogleConnection(
        business=business, created_by=request.user, credential=credential
    )
    connection.scopes = str(tokens.get("scope", "")).split()
    connection.expires_at = timezone.now() + timedelta(seconds=token_lifetime(tokens))
    connection.email, connection.subject = identity["email"], identity["sub"]
    connection.status, connection.error_code = "connected", ""
    connection.refresh_failures, connection.refresh_retry_at = 0, None
    connection.last_validated_at = timezone.now()
    connection.save()
    if existing:
        connection.properties.filter(
            error_code__in=[
                "credentials_revoked",
                "reconnection_required",
                "disconnected",
                "token_refresh_backoff",
            ]
        ).update(error_code="")
    AuditEvent.record(
        action="analytics.google_reauthorized" if existing else "analytics.google_connected",
        actor=request.user,
        target=connection,
    )
    return connection


def access_token(
    connection: GoogleConnection,
    *,
    refresh_before: timedelta = timedelta(seconds=90),
    rejected_token: str | None = None,
) -> str:
    """Serialize every refresh path, persisting failures before raising sanitized errors."""
    failure: ProviderError | None = None
    with transaction.atomic():
        locked = (
            GoogleConnection.objects.select_for_update()
            .select_related("credential")
            .get(pk=connection.pk)
        )
        if locked.status != "connected":
            raise ProviderError("reconnection_required")
        tokens = load_credential_secrets_for_service(locked.credential)
        now = timezone.now()
        if (
            locked.expires_at
            and locked.expires_at > now + refresh_before
            and tokens.get("access_token")
            and tokens["access_token"] != rejected_token
        ):
            return tokens["access_token"]
        if locked.refresh_retry_at and locked.refresh_retry_at > now:
            if (
                locked.expires_at
                and locked.expires_at > now + timedelta(seconds=90)
                and tokens.get("access_token")
                and tokens["access_token"] != rejected_token
            ):
                return tokens["access_token"]
            raise ProviderError("token_refresh_backoff", retryable=True)
        try:
            if not tokens.get("refresh_token"):
                raise ProviderError("credentials_revoked")
            refreshed = token_request(
                {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]}
            )
            if not isinstance(refreshed.get("access_token"), str) or not refreshed["access_token"]:
                raise ProviderError("invalid_provider_response", retryable=True)
            lifetime = token_lifetime(refreshed)
            if refreshed.get("refresh_token") is not None and not isinstance(
                refreshed["refresh_token"], str
            ):
                raise ProviderError("invalid_provider_response", retryable=True)

        except ProviderError as exc:
            failure = exc
            locked.error_code = exc.code
            locked.refresh_failures = min(locked.refresh_failures + 1, 10)
            locked.refresh_retry_at = (
                now
                + timedelta(
                    seconds=max(
                        min(60 * 2 ** (locked.refresh_failures - 1), 3600), exc.retry_after or 0
                    )
                    + secrets.randbelow(30)
                )
                if exc.retryable
                else None
            )
            if not exc.retryable:
                locked.status = "reconnect"
            locked.save(
                update_fields=[
                    "status",
                    "error_code",
                    "refresh_failures",
                    "refresh_retry_at",
                    "updated_at",
                ]
            )
        else:
            tokens["access_token"] = refreshed["access_token"]
            if refreshed.get("refresh_token"):
                tokens["refresh_token"] = str(refreshed["refresh_token"])
            store_credential_secrets(locked.credential, tokens)
            locked.expires_at = now + timedelta(seconds=lifetime)
            locked.last_validated_at = locked.last_refreshed_at = now
            locked.refresh_failures, locked.refresh_retry_at, locked.error_code = 0, None, ""
            locked.save(
                update_fields=[
                    "expires_at",
                    "last_validated_at",
                    "last_refreshed_at",
                    "refresh_failures",
                    "refresh_retry_at",
                    "error_code",
                    "updated_at",
                ]
            )
            return tokens["access_token"]
    # Raise after commit so permanent status and shared retry gates survive callers.
    assert failure is not None
    raise failure


def authorized_request(
    token: str,
    method: str,
    url: str,
    *,
    body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        return _json(
            requests.request(
                method,
                url,
                json=body,
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=45,
                allow_redirects=False,
            )
        )
    except requests.RequestException:
        raise ProviderError("google_unavailable", retryable=True) from None


def google_request(
    connection: GoogleConnection,
    method: str,
    url: str,
    *,
    body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not url.startswith(
        (ADMIN_URL, DATA_URL, SEARCH_URL, "https://openidconnect.googleapis.com/v1/userinfo")
    ):
        raise ValueError("Untrusted provider endpoint")
    token = access_token(connection)
    try:
        return authorized_request(token, method, url, body=body, params=params)
    except ProviderError as exc:
        if exc.code != "credentials_revoked":
            raise
    # A rejected access token is not proof the offline grant is revoked. One
    # coordinated exchange (or a concurrent worker's newer token) may recover it.
    renewed = access_token(connection, rejected_token=token)
    try:
        return authorized_request(renewed, method, url, body=body, params=params)
    except ProviderError as exc:
        if exc.code == "credentials_revoked":
            with transaction.atomic():
                locked = (
                    GoogleConnection.objects.select_for_update()
                    .select_related("credential")
                    .get(pk=connection.pk)
                )
                if locked.status == "connected":
                    if (
                        load_credential_secrets_for_service(locked.credential).get("access_token")
                        != renewed
                    ):
                        raise ProviderError("google_unavailable", retryable=True) from None
                    locked.status, locked.error_code = "reconnect", "credentials_revoked"
                    locked.save(update_fields=["status", "error_code", "updated_at"])
        raise


def paginated(connection: GoogleConnection, url: str, key: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    page = ""
    for _ in range(100):
        result = google_request(connection, "GET", url, params={"pageSize": 200, "pageToken": page})
        rows.extend(result.get(key, []))
        page = result.get("nextPageToken", "")
        if not page:
            return rows
    raise ProviderError("provider_pagination_limit")


def discover(connection: GoogleConnection) -> dict[str, Any]:
    ga4: list[dict[str, Any]] = []
    search: list[dict[str, Any]] = []
    if READ in connection.scopes:
        accounts = paginated(connection, ADMIN_URL + "accountSummaries", "accountSummaries")
        ga4 = [prop for account in accounts for prop in account.get("propertySummaries", [])]
    if SEARCH in connection.scopes:
        search = google_request(connection, "GET", SEARCH_URL + "sites").get("siteEntry", [])
    return {"ga4": ga4, "gsc": search}


def disconnect(connection: GoogleConnection, actor: Any) -> None:
    from apps.credentials.secrets import clear_credential_secrets

    # Same lock ordering as refresh and reauthorisation; rotation cannot race revocation.
    with transaction.atomic():
        locked = (
            GoogleConnection.objects.select_for_update()
            .select_related("credential")
            .get(pk=connection.pk)
        )
        if locked.status == "disconnected":
            return
        tokens = load_credential_secrets_for_service(locked.credential)
        try:
            response = requests.post(
                "https://oauth2.googleapis.com/revoke",
                data={"token": tokens.get("refresh_token", tokens.get("access_token"))},
                timeout=30,
                allow_redirects=False,
            )
        except requests.RequestException:
            raise ProviderError("revocation_unavailable", retryable=True) from None
        if response.status_code not in {200, 400}:
            raise ProviderError("revocation_unavailable", retryable=True)
        clear_credential_secrets(locked.credential)
        locked.status, locked.refresh_retry_at, locked.error_code = "disconnected", None, ""
        locked.save(update_fields=["status", "refresh_retry_at", "error_code", "updated_at"])
        locked.properties.update(error_code="disconnected")
        AuditEvent.record(action="analytics.google_disconnected", actor=actor, target=locked)
