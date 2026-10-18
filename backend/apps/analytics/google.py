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
SCOPES = {"reporting": [READ, SEARCH], "administration": [READ, SEARCH, EDIT]}
ADMIN_URL = "https://analyticsadmin.googleapis.com/v1beta/"
DATA_URL = "https://analyticsdata.googleapis.com/v1beta/"
SEARCH_URL = "https://www.googleapis.com/webmasters/v3/"
TOKEN_URL = "https://oauth2.googleapis.com/token"


class ProviderError(Exception):
    def __init__(self, code: str, *, retryable: bool = False) -> None:
        self.code = code
        self.retryable = retryable
        super().__init__(code)


def oauth_start(request: AuthenticatedHttpRequest, business_id: int, mode: str) -> str:
    business_for(request.user, business_id, "change_googleconnection")
    if not settings.ANALYTICS_GOOGLE_CLIENT_ID or not settings.ANALYTICS_GOOGLE_CLIENT_SECRET:
        raise HttpError(503, "Google OAuth is not configured. Contact the platform administrator.")
    verifier = secrets.token_urlsafe(64)
    state = secrets.token_urlsafe(32)
    request.session["analytics_oauth"] = {
        "state": state,
        "verifier": verifier,
        "business": business_id,
        "actor": str(request.user.pk),
        "mode": mode,
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
        raise ProviderError(code, retryable=quota or status >= 500)
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
        return _json(
            requests.post(
                TOKEN_URL,
                data={
                    **data,
                    "client_id": settings.ANALYTICS_GOOGLE_CLIENT_ID,
                    "client_secret": settings.ANALYTICS_GOOGLE_CLIENT_SECRET,
                },
                timeout=30,
            )
        )
    except ProviderError as exc:
        if exc.code == "invalid_google_request":
            raise ProviderError("credentials_revoked") from None
        raise
    except requests.RequestException:
        raise ProviderError("google_unavailable", retryable=True) from None


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
    tokens = token_request(
        {
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": pending["verifier"],
            "redirect_uri": settings.ANALYTICS_GOOGLE_REDIRECT_URI,
        }
    )
    if not tokens.get("refresh_token") or not tokens.get("access_token"):
        raise HttpError(400, "Google did not grant offline access. Reconnect with consent.")
    credential = StoredCredential.objects.create(
        name=f"Analytics Google OAuth — business {business.pk}",
        created_by=request.user,
        metadata={"service": "analytics-google"},
    )
    store_credential_secrets(
        credential, {key: str(tokens[key]) for key in ("access_token", "refresh_token")}
    )
    connection = GoogleConnection.objects.create(
        business=business,
        created_by=request.user,
        credential=credential,
        scopes=tokens.get("scope", "").split(),
        expires_at=timezone.now() + timedelta(seconds=int(tokens.get("expires_in", 3600))),
    )
    identity = google_request(connection, "GET", "https://openidconnect.googleapis.com/v1/userinfo")
    connection.email = identity.get("email", "")
    connection.subject = identity.get("sub", "")
    connection.last_validated_at = timezone.now()
    connection.save()
    AuditEvent.record(action="analytics.google_connected", actor=request.user, target=connection)
    return connection


def access_token(connection: GoogleConnection) -> str:
    with transaction.atomic():
        locked = (
            GoogleConnection.objects.select_for_update()
            .select_related("credential")
            .get(pk=connection.pk)
        )
        if locked.status != "connected":
            raise ProviderError("reconnection_required")
        tokens = load_credential_secrets_for_service(locked.credential)
        if locked.expires_at and locked.expires_at > timezone.now() + timedelta(seconds=90):
            return tokens["access_token"]
        try:
            refreshed = token_request(
                {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]}
            )
        except ProviderError as exc:
            failure = exc
        else:
            tokens["access_token"] = refreshed["access_token"]
            if refreshed.get("refresh_token"):
                tokens["refresh_token"] = refreshed["refresh_token"]
            store_credential_secrets(locked.credential, tokens)
            locked.expires_at = timezone.now() + timedelta(
                seconds=int(refreshed.get("expires_in", 3600))
            )
            locked.last_validated_at = timezone.now()
            locked.save(update_fields=["expires_at", "last_validated_at", "updated_at"])
            return tokens["access_token"]
    # Outside the transaction so failure status is not rolled back.
    if not failure.retryable:
        GoogleConnection.objects.filter(pk=connection.pk).update(
            status="reconnect", error_code=failure.code
        )
    raise failure


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
        response = requests.request(
            method,
            url,
            json=body,
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=45,
            allow_redirects=False,
        )
        return _json(response)
    except ProviderError as exc:
        if exc.code == "credentials_revoked":
            GoogleConnection.objects.filter(pk=connection.pk).update(
                status="reconnect", error_code=exc.code
            )
        raise
    except requests.RequestException:
        raise ProviderError("google_unavailable", retryable=True) from None


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
    tokens = load_credential_secrets_for_service(connection.credential)
    try:
        response = requests.post(
            "https://oauth2.googleapis.com/revoke",
            data={"token": tokens.get("refresh_token", tokens.get("access_token"))},
            timeout=30,
        )
    except requests.RequestException:
        raise ProviderError("revocation_unavailable", retryable=True) from None
    if response.status_code not in {200, 400}:
        raise ProviderError("revocation_unavailable", retryable=True)
    # Retain encrypted payload on failed revocation so the user can retry.
    from apps.credentials.secrets import clear_credential_secrets

    with transaction.atomic():
        clear_credential_secrets(connection.credential)
        connection.status = "disconnected"
        connection.save(update_fields=["status", "updated_at"])
        connection.properties.update(error_code="disconnected")
        AuditEvent.record(action="analytics.google_disconnected", actor=actor, target=connection)
