"""Security and provider-contract regression tests; no Google credentials required."""

from datetime import date, timedelta
from typing import cast
from unittest.mock import MagicMock, patch

from cryptography.fernet import Fernet
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError, transaction
from django.test import Client, RequestFactory, TestCase, override_settings
from django.utils import timezone
from ninja.errors import HttpError

from apps.analytics.access import business_for, website_for
from apps.analytics.administration import create_definition, definition_plan
from apps.analytics.google import (
    EDIT,
    READ,
    SEARCH,
    ProviderError,
    access_token,
    oauth_callback,
    oauth_start,
)
from apps.analytics.models import (
    BusinessMembership,
    GoogleConnection,
    ProviderProperty,
    ReportSnapshot,
    SyncJob,
)
from apps.analytics.reports import derive_metrics, gsc_report, opportunities, parse_ga
from apps.analytics.services import (
    create_business,
    date_window,
    normalize_domain,
    normalize_page,
    previous_window,
    save_website,
    set_membership,
)
from apps.analytics.synchronization import sync_job
from apps.credentials.models import StoredCredential
from apps.credentials.secrets import load_credential_secrets_for_service, store_credential_secrets
from authentication.custom_request import AuthenticatedHttpRequest
from authentication.models import User

CACHES = {
    name: {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": name}
    for name in ["default", "session"]
}


@override_settings(
    CACHES=CACHES,
    CREDENTIAL_ENCRYPTION_KEYS=[Fernet.generate_key().decode()],
    ANALYTICS_GOOGLE_CLIENT_ID="test-client",
    ANALYTICS_GOOGLE_CLIENT_SECRET="test-secret",
)
class AnalyticsTests(TestCase):
    def setUp(self) -> None:
        self.owner = User.objects.create_user(
            email="owner@example.test",
            password="test-password",
            first_name="Test",
            last_name="User",
        )
        self.viewer = User.objects.create_user(
            email="viewer@example.test",
            password="test-password",
            first_name="Test",
            last_name="User",
        )
        self.other = User.objects.create_user(
            email="other@example.test",
            password="test-password",
            first_name="Test",
            last_name="User",
        )
        self.business = create_business(self.owner, "Example")
        self.other_business = create_business(self.other, "Other")
        BusinessMembership.objects.create(business=self.business, user=self.viewer, role="viewer")
        self.website = save_website(
            self.owner,
            self.business.pk,
            name="Example",
            domain="EXAMPLE.com",
            timezone="Europe/London",
        )
        self.credential = StoredCredential.objects.create(name="Google analytics test")
        store_credential_secrets(
            self.credential, {"access_token": "access-test", "refresh_token": "refresh-test"}
        )
        self.connection = GoogleConnection.objects.create(
            business=self.business,
            created_by=self.owner,
            credential=self.credential,
            scopes=[READ, SEARCH, EDIT],
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.prop = ProviderProperty.objects.create(
            website=self.website,
            connection=self.connection,
            provider="ga4",
            external_id="properties/123",
        )
        self.start, self.end = date(2026, 1, 1), date(2026, 1, 28)
        self.client.force_login(self.owner)

    def test_business_creation_does_not_grant_staff(self) -> None:
        self.assertEqual(self.business.memberships.get(user=self.owner).role, "owner")
        self.assertFalse(self.owner.is_staff)
        self.assertFalse(self.owner.has_perm("credentials.reveal_storedcredential"))
        self.assertTrue(self.owner.has_perm("analytics.change_website", self.business))

    def test_role_and_tenant_boundaries(self) -> None:
        self.assertEqual(business_for(self.viewer, self.business.pk), self.business)
        with self.assertRaises(HttpError):
            business_for(self.viewer, self.business.pk, "change_website")
        from django.http import Http404

        with self.assertRaises(Http404):
            website_for(self.other, self.website.pk)
        with self.assertRaises(Http404):
            business_for(self.owner, self.other_business.pk)
        self.assertFalse(AnonymousUser().has_perm("analytics.view_business", self.business))

    def test_membership_unique_and_last_owner(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            BusinessMembership.objects.create(business=self.business, user=self.owner, role="admin")
        for role in [None, "admin", "viewer"]:
            with self.assertRaises(HttpError):
                set_membership(self.owner, self.business.pk, self.owner.pk, role)
        set_membership(self.owner, self.business.pk, self.viewer.pk, "owner")
        set_membership(self.owner, self.business.pk, self.owner.pk, "viewer")
        self.assertEqual(self.business.memberships.filter(role="owner").count(), 1)

    def test_domain_and_timezone_validation(self) -> None:
        self.assertEqual(normalize_domain("https://WWW.Example.COM/"), "www.example.com")
        self.assertEqual(normalize_domain("bücher.example"), "xn--bcher-kva.example")
        for value in [
            "localhost",
            "https://example.com/path",
            "https://user:pass@example.com",
            "https://example.com:8080",
            "bad_.example",
            "https://example.com?secret=1",
        ]:
            with self.assertRaises((HttpError, ValueError)):
                normalize_domain(value)
        with self.assertRaises(HttpError):
            save_website(
                self.owner,
                self.business.pk,
                name="bad",
                domain="other.example",
                timezone="invalid/zone",
            )
        with self.assertRaises(HttpError):
            save_website(
                self.owner, self.business.pk, name="duplicate", domain="example.com", timezone="UTC"
            )

    def test_url_join_is_conservative(self) -> None:
        self.assertEqual(
            normalize_page("https://EXAMPLE.com/a/?q=1#fragment", "example.com"),
            "https://example.com/a/?q=1",
        )
        self.assertNotEqual(
            normalize_page("/a", "example.com"), normalize_page("/a/", "example.com")
        )
        self.assertNotEqual(
            normalize_page("https://www.example.com/a", "example.com"),
            normalize_page("/a", "example.com"),
        )

    def test_date_windows(self) -> None:
        self.assertEqual(
            previous_window(self.start, self.end), (date(2025, 12, 4), date(2025, 12, 31))
        )
        for start, end in [
            (self.end, self.start),
            (date(2020, 1, 1), self.end),
            (timezone.now().date(), timezone.now().date() + timedelta(days=1)),
        ]:
            with self.assertRaises(HttpError):
                date_window(start, end)

    def test_api_authentication_and_csrf(self) -> None:
        anon = Client()
        self.assertEqual(anon.get("/api/analytics/session").status_code, 401)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.owner)
        self.assertEqual(
            csrf_client.post(
                "/api/analytics/businesses", {"name": "test"}, content_type="application/json"
            ).status_code,
            403,
        )
        session_response = self.client.get("/api/analytics/session")
        self.assertEqual(session_response.status_code, 200)
        self.assertEqual(session_response["Cache-Control"], "private, no-store")

    def test_viewer_write_forbidden_and_cross_business_idor(self) -> None:
        self.client.force_login(self.viewer)
        response = self.client.put(
            f"/api/analytics/websites/{self.website.pk}",
            {"name": "attack", "domain": "example.com"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.client.force_login(self.other)
        paths = [
            f"/api/analytics/websites/{self.website.pk}/sync",
            f"/api/analytics/connections/{self.connection.pk}/properties",
            f"/api/analytics/websites/{self.website.pk}/reports/ga4/overview?start=2026-01-01&end=2026-01-28",
        ]
        for path in paths:
            self.assertEqual(self.client.get(path).status_code, 404)

    def _request(self) -> AuthenticatedHttpRequest:
        request = cast(AuthenticatedHttpRequest, RequestFactory().get("/"))
        request.user = self.owner
        from django.contrib.sessions.backends.cache import SessionStore

        request.session = SessionStore()
        return request

    def test_oauth_state_pkce_and_replay(self) -> None:
        request = self._request()
        url = oauth_start(request, self.business.pk, "reporting")
        self.assertIn("code_challenge_method=S256", url)
        self.assertIn("access_type=offline", url)
        self.assertNotIn("analytics.edit", url)
        with self.assertRaises(HttpError):
            oauth_callback(request, "wrong", "code")
        self.assertNotIn("analytics_oauth", request.session)

    def test_oauth_expired_and_changed_actor(self) -> None:
        request = self._request()
        oauth_start(request, self.business.pk, "reporting")
        state = request.session["analytics_oauth"]["state"]
        request.session["analytics_oauth"]["issued"] -= 601
        with self.assertRaises(HttpError):
            oauth_callback(request, state, "code")
        oauth_start(request, self.business.pk, "reporting")
        request.user = self.viewer
        with self.assertRaises(HttpError):
            oauth_callback(request, request.session["analytics_oauth"]["state"], "code")

    @patch(
        "apps.analytics.google.google_request",
        return_value={"email": "google@example.test", "sub": "google-sub"},
    )
    @patch(
        "apps.analytics.google.token_request",
        return_value={
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "scope": READ + " " + SEARCH,
            "expires_in": 3600,
        },
    )
    def test_oauth_callback_encrypts_and_consumes(
        self, token: MagicMock, identity: MagicMock
    ) -> None:
        request = self._request()
        oauth_start(request, self.business.pk, "reporting")
        connection = oauth_callback(request, request.session["analytics_oauth"]["state"], "code")
        self.assertEqual(connection.email, "google@example.test")
        self.assertNotIn("new-refresh", connection.credential.encrypted_secret_payload)
        self.assertEqual(
            load_credential_secrets_for_service(connection.credential)["refresh_token"],
            "new-refresh",
        )
        self.assertNotIn("analytics_oauth", request.session)

    @patch("apps.analytics.google.token_request", side_effect=ProviderError("credentials_revoked"))
    def test_revoked_refresh_fails_closed(self, token: MagicMock) -> None:
        self.connection.expires_at = timezone.now() - timedelta(seconds=1)
        self.connection.save()
        with self.assertRaises(ProviderError):
            access_token(self.connection)
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.status, "reconnect")

    @patch(
        "apps.analytics.google.token_request",
        return_value={
            "access_token": "rotated-access",
            "refresh_token": "rotated-refresh",
            "expires_in": 3600,
        },
    )
    def test_refresh_rotation(self, token: MagicMock) -> None:
        self.connection.expires_at = timezone.now() - timedelta(seconds=1)
        self.connection.save()
        self.assertEqual(access_token(self.connection), "rotated-access")
        self.credential.refresh_from_db()
        self.assertEqual(
            load_credential_secrets_for_service(self.credential)["refresh_token"], "rotated-refresh"
        )

    def test_ga_parser_and_ratios(self) -> None:
        rows = parse_ga(
            {
                "dimensionHeaders": [{"name": "eventName"}],
                "metricHeaders": [{"name": "eventCount"}],
                "rows": [
                    {
                        "dimensionValues": [{"value": "button_click"}],
                        "metricValues": [{"value": "12"}],
                    }
                ],
            }
        )
        self.assertEqual(rows, [{"eventName": "button_click", "eventCount": 12}])
        self.assertEqual(
            derive_metrics({"sessions": 100, "engagedSessions": 75})["engagementRate"], 0.75
        )
        self.assertIsNone(derive_metrics({"sessions": 0, "engagedSessions": 0})["engagementRate"])

    @patch(
        "apps.analytics.reports.google_request",
        return_value={
            "rows": [
                {"keys": ["query"], "clicks": 5, "impressions": 100, "ctr": 0.05, "position": 12}
            ]
        },
    )
    def test_search_parser_and_domain_property_encoding(self, provider: MagicMock) -> None:
        self.prop.provider = "gsc"
        self.prop.external_id = "sc-domain:example.com"
        result = gsc_report(self.prop, "queries", self.start, self.end)
        self.assertEqual(result["rows"][0]["query"], "query")
        self.assertIn("sc-domain%3Aexample.com", provider.call_args.args[2])
        self.assertEqual(provider.call_args.kwargs["body"]["dataState"], "final")

    @patch("apps.analytics.synchronization.definitions", return_value=[])
    @patch(
        "apps.analytics.synchronization.ga_report",
        return_value={"rows": [{"totalUsers": 100}], "complete": True},
    )
    def test_sync_idempotency_and_exact_windows(
        self, provider: MagicMock, definitions: MagicMock
    ) -> None:
        job = SyncJob.objects.create(property=self.prop, start=self.start, end=self.end)
        sync_job(job.pk)
        count = ReportSnapshot.objects.count()
        sync_job(job.pk)
        self.assertEqual(ReportSnapshot.objects.count(), count)
        job.refresh_from_db()
        self.assertEqual(job.status, "complete")
        self.assertEqual(job.progress, 100)
        self.assertEqual(
            ReportSnapshot.objects.get(
                property=self.prop, report="overview", start=self.start, end=self.end
            ).payload["rows"][0]["totalUsers"],
            100,
        )

    @patch(
        "apps.analytics.administration.definitions",
        return_value=[{"parameterName": "button_id", "scope": "EVENT"}],
    )
    def test_wizard_missing_parameters(self, provider: MagicMock) -> None:
        plan = definition_plan(self.prop, ["button_id", "button_text"])
        self.assertEqual(plan["registered"], ["button_id"])
        self.assertEqual(plan["missing"], ["button_text"])

    def test_admin_requires_confirmation_and_google_edit_scope(self) -> None:
        with self.assertRaises(HttpError):
            create_definition(
                self.prop,
                "dimensions",
                {"parameterName": "button_id", "displayName": "Button ID"},
                self.owner,
                False,
            )
        self.connection.scopes = [READ]
        self.connection.save()
        with self.assertRaises(HttpError):
            create_definition(
                self.prop,
                "dimensions",
                {"parameterName": "button_id", "displayName": "Button ID"},
                self.owner,
                True,
            )

    @patch("apps.analytics.administration.definitions", return_value=[])
    @patch(
        "apps.analytics.administration.google_request",
        return_value={"name": "properties/123/customDimensions/1", "parameterName": "button_id"},
    )
    def test_definition_creation_and_verification(
        self, provider: MagicMock, existing: MagicMock
    ) -> None:
        row = create_definition(
            self.prop,
            "dimensions",
            {"parameterName": "button_id", "displayName": "Button ID"},
            self.owner,
            True,
        )
        self.assertEqual(provider.call_count, 2)
        self.assertEqual(row["parameterName"], "button_id")
        self.assertTrue(self.prop.definitions.exists())

    def test_missing_data_is_not_zero(self) -> None:
        response = self.client.get(
            f"/api/analytics/websites/{self.website.pk}/reports/ga4/overview?start=2026-01-01&end=2026-01-28"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["current"])
        self.assertEqual(response.json()["status"], "range_not_synchronized")

    def test_insight_threshold(self) -> None:
        row = {"query": "test", "clicks": 1, "impressions": 99, "ctr": 0.01, "position": 12}
        self.assertEqual(opportunities([row], [], "query"), [])
        row["impressions"] = 100
        self.assertTrue(opportunities([row], [], "query")[0]["heuristic"])

    @patch("apps.analytics.api.google_request", return_value={"timeZone": "Europe/London"})
    @patch("apps.analytics.api.queue_sync")
    def test_property_association_scope(self, queue: MagicMock, provider: MagicMock) -> None:
        response = self.client.put(
            f"/api/analytics/websites/{self.website.pk}/properties/ga4",
            {"connection_id": self.connection.pk, "external_id": "properties/456"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.prop.refresh_from_db()
        self.assertEqual(self.prop.external_id, "properties/456")
        self.client.force_login(self.other)
        response = self.client.put(
            f"/api/analytics/websites/{self.website.pk}/properties/ga4",
            {"connection_id": self.connection.pk, "external_id": "properties/456"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_oauth_start_survives_real_session_serialization(self) -> None:
        response = self.client.post(
            f"/api/analytics/businesses/{self.business.pk}/oauth",
            {"mode": "reporting"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session["analytics_oauth"]["actor"], str(self.owner.pk))

    @patch(
        "apps.analytics.tasks.sync_job", side_effect=ProviderError("quota_exceeded", retryable=True)
    )
    def test_quota_retries_with_backoff(self, worker: MagicMock) -> None:
        from celery.exceptions import Retry

        from apps.analytics.tasks import synchronize

        job = SyncJob.objects.create(property=self.prop, start=self.start, end=self.end)
        with (
            patch.object(synchronize, "retry", side_effect=Retry()) as retry,
            self.assertRaises(Retry),
        ):
            synchronize.run(job.pk)
        self.assertEqual(retry.call_args.kwargs["countdown"], 60)
        job.refresh_from_db()
        self.assertEqual(job.status, "retrying")
        self.assertEqual(job.error_code, "quota_exceeded")

    def test_provider_error_codes_are_safe_and_quota_aware(self) -> None:
        import requests

        from apps.analytics.google import _json

        for status, body, code, retryable in [
            (429, "{}", "quota_exceeded", True),
            (403, '{"error":{"errors":[{"reason":"rateLimitExceeded"}]}}', "quota_exceeded", True),
            (403, "{}", "google_permission_denied", False),
            (500, "{}", "google_unavailable", True),
            (400, "{}", "invalid_google_request", False),
        ]:
            response = requests.Response()
            response.status_code = status
            response._content = body.encode()
            with self.assertRaises(ProviderError) as caught:
                _json(response)
            self.assertEqual(caught.exception.code, code)
            self.assertEqual(caught.exception.retryable, retryable)

    def test_tenant_safe_csv_neutralizes_formulas(self) -> None:
        ReportSnapshot.objects.create(
            property=self.prop,
            report="events",
            start=self.start,
            end=self.end,
            payload={"rows": [{"eventName": "=CMD()", "eventCount": 1}]},
        )
        path = f"/api/analytics/websites/{self.website.pk}/reports/ga4/events?start={self.start}&end={self.end}&export=true"
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertIn("'=CMD()", response.content.decode())
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(path).status_code, 404)

    def test_configured_key_events_are_viewer_readable(self) -> None:
        from apps.analytics.models import EventDefinition

        EventDefinition.objects.create(
            property=self.prop,
            kind="key-events",
            external_name="properties/123/keyEvents/1",
            payload={"eventName": "button_click"},
        )
        self.client.force_login(self.viewer)
        response = self.client.get(f"/api/analytics/websites/{self.website.pk}/key-events")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [{"eventName": "button_click"}])

    def test_page_and_event_trends_are_scoped_local_reports(self) -> None:
        ReportSnapshot.objects.create(
            property=self.prop,
            report="events",
            start=self.start,
            end=self.end,
            payload={"rows": [{"eventName": "button_click", "eventCount": 2}]},
        )
        ReportSnapshot.objects.create(
            property=self.prop,
            report="event_trend",
            start=self.start,
            end=self.end,
            payload={
                "rows": [
                    {"date": "20260101", "eventName": "button_click", "eventCount": 2},
                    {"date": "20260101", "eventName": "other", "eventCount": 10},
                ]
            },
        )
        response = self.client.get(
            f"/api/analytics/websites/{self.website.pk}/events/button_click/trend?start={self.start}&end={self.end}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["rows"]), 1)
        self.assertEqual(response.json()["rows"][0]["eventCount"], 2)

    def test_combined_pages_preserve_scheme_and_show_provider_trends(self) -> None:
        url = "http://example.com/page?a=1"
        ReportSnapshot.objects.create(
            property=self.prop,
            report="pages",
            start=self.start,
            end=self.end,
            payload={
                "rows": [
                    {
                        "pageLocation": url,
                        "hostName": "example.com",
                        "pagePathPlusQueryString": "/page?a=1",
                        "sessions": 5,
                    }
                ]
            },
        )
        ReportSnapshot.objects.create(
            property=self.prop,
            report="page_trend",
            start=self.start,
            end=self.end,
            payload={"rows": [{"date": "20260101", "pageLocation": url, "sessions": 5}]},
        )
        response = self.client.get(
            f"/api/analytics/websites/{self.website.pk}/combined",
            {"start": str(self.start), "end": str(self.end), "page": url},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rows"][0]["url"], url)
        self.assertEqual(len(response.json()["rows"][0]["ga4_page_trend"]), 1)
