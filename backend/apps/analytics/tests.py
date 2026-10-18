"""Security and provider-contract regression tests; no Google credentials required."""

from datetime import date, timedelta
from typing import cast
from unittest.mock import MagicMock, patch

from cryptography.fernet import Fernet
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.http import Http404
from django.test import Client, RequestFactory, TestCase, TransactionTestCase, override_settings
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
        cache.clear()
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
        self.assertIn("analytics.edit", url)
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
        "apps.analytics.google.authorized_request",
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

    @patch("apps.analytics.linking.google_request", return_value={"timeZone": "Europe/London"})
    @patch("apps.analytics.linking.queue_sync")
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

    def test_long_range_trend_can_return_every_day(self) -> None:
        long_end = self.start + timedelta(days=119)
        rows = [
            {"date": str(self.start + timedelta(days=day)), "sessions": day + 1}
            for day in range(120)
        ]
        ReportSnapshot.objects.create(
            property=self.prop,
            report="trend",
            start=self.start,
            end=long_end,
            payload={"rows": rows},
        )
        response = self.client.get(
            f"/api/analytics/websites/{self.website.pk}/reports/ga4/trend?start={self.start}&end={long_end}&page_size=400"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["current"]["rows"]), 120)
        self.assertEqual(response.json()["current"]["rows"][-1]["sessions"], 120)

    def test_linked_ga_timezone_cannot_drift(self) -> None:
        self.prop.metadata = {"timeZone": "Europe/London"}
        self.prop.save()
        with self.assertRaises(HttpError):
            save_website(
                self.owner,
                self.business.pk,
                website=self.website,
                name=self.website.name,
                domain=self.website.domain,
                timezone="UTC",
            )

    def test_property_unlink_is_scoped_confirmed_and_keeps_google_account(self) -> None:
        path = f"/api/analytics/websites/{self.website.pk}/properties/ga4"
        self.client.force_login(self.viewer)
        self.assertEqual(
            self.client.delete(
                path, {"confirmed": True}, content_type="application/json"
            ).status_code,
            403,
        )
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.delete(
                path, {"confirmed": True}, content_type="application/json"
            ).status_code,
            404,
        )
        self.client.force_login(self.owner)
        self.assertEqual(
            self.client.delete(
                path, {"confirmed": False}, content_type="application/json"
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.delete(
                path, {"confirmed": True}, content_type="application/json"
            ).status_code,
            200,
        )
        self.assertFalse(ProviderProperty.objects.filter(pk=self.prop.pk).exists())
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.status, "connected")

    @patch("apps.analytics.linking.queue_sync")
    @patch("apps.analytics.linking.discover")
    def test_gsc_association_persists_metadata_and_search_type(
        self, discovery: MagicMock, queue: MagicMock
    ) -> None:
        discovery.return_value = {
            "gsc": [{"siteUrl": "sc-domain:example.com", "permissionLevel": "siteOwner"}]
        }
        response = self.client.put(
            f"/api/analytics/websites/{self.website.pk}/properties/gsc",
            {
                "connection_id": self.connection.pk,
                "external_id": "sc-domain:example.com",
                "search_type": "image",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        prop = self.website.provider_properties.get(provider="gsc")
        self.assertEqual(prop.metadata["siteUrl"], "sc-domain:example.com")
        self.assertEqual(prop.metadata["permissionLevel"], "siteOwner")
        self.assertEqual(prop.metadata["search_type"], "image")
        queue.assert_called_once()

    @patch("apps.analytics.linking.queue_sync")
    @patch("apps.analytics.linking.google_request", return_value={"timeZone": "America/New_York"})
    def test_ga4_link_detects_timezone(self, provider: MagicMock, queue: MagicMock) -> None:
        response = self.client.put(
            f"/api/analytics/websites/{self.website.pk}/properties/ga4",
            {"connection_id": self.connection.pk, "external_id": "properties/456"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.website.refresh_from_db()
        self.assertEqual(self.website.timezone, "America/New_York")

    @patch("apps.analytics.onboarding.google_request", return_value={"timeZone": "Europe/London"})
    @patch("apps.analytics.onboarding.paginated")
    @patch("apps.analytics.onboarding.discover")
    def test_website_discovery_matches_domains_not_display_names(
        self, discovery: MagicMock, streams: MagicMock, metadata: MagicMock
    ) -> None:
        discovery.return_value = {
            "ga4": [{"property": "properties/123", "displayName": "Unrelated display name"}],
            "gsc": [
                {"siteUrl": "sc-domain:example.com", "permissionLevel": "siteOwner"},
                {"siteUrl": "https://www.example.com/", "permissionLevel": "siteFullUser"},
                {"siteUrl": "https://example.com/blog/", "permissionLevel": "siteOwner"},
                {"siteUrl": "sc-domain:hidden.test", "permissionLevel": "siteUnverifiedUser"},
            ],
        }
        streams.return_value = [{"webStreamData": {"defaultUri": "https://www.example.com/"}}]
        response = self.client.get(f"/api/analytics/connections/{self.connection.pk}/websites")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(len(result["websites"]), 1)
        row = result["websites"][0]
        self.assertEqual(row["domain"], "example.com")
        self.assertEqual(row["ga4"][0]["timezone"], "Europe/London")
        self.assertEqual(row["gsc"][0]["id"], "sc-domain:example.com")
        self.assertEqual(len(row["gsc"]), 2)
        self.assertEqual(row["existing_id"], self.website.pk)
        self.assertTrue(result["warnings"])
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.get(
                f"/api/analytics/connections/{self.connection.pk}/websites"
            ).status_code,
            404,
        )
        self.client.force_login(self.viewer)
        self.assertEqual(
            self.client.get(
                f"/api/analytics/connections/{self.connection.pk}/websites"
            ).status_code,
            403,
        )

    @patch("apps.analytics.linking.queue_sync")
    @patch("apps.analytics.linking.discover")
    @patch("apps.analytics.linking.google_request", return_value={"timeZone": "America/New_York"})
    @patch("apps.analytics.onboarding.discover_websites")
    def test_website_import_is_scoped_idempotent_and_links_both(
        self, inventory: MagicMock, metadata: MagicMock, discovery: MagicMock, queue: MagicMock
    ) -> None:
        inventory.return_value = {
            "websites": [
                {
                    "domain": "new.example.com",
                    "ga4": [{"id": "properties/987", "timezone": "America/New_York"}],
                    "gsc": [{"id": "sc-domain:example.com"}],
                }
            ]
        }
        discovery.return_value = {
            "gsc": [{"siteUrl": "sc-domain:example.com", "permissionLevel": "siteOwner"}]
        }
        body = {
            "websites": [
                {
                    "domain": "new.example.com",
                    "ga4": "properties/987",
                    "gsc": "sc-domain:example.com",
                }
            ]
        }
        endpoint = f"/api/analytics/connections/{self.connection.pk}/websites"
        response = self.client.post(endpoint, body, content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        website = self.business.websites.get(domain="new.example.com")
        self.assertEqual(website.timezone, "America/New_York")
        self.assertEqual(website.provider_properties.count(), 2)
        response = self.client.post(endpoint, body, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(queue.call_count, 2)
        self.assertEqual(self.business.websites.filter(domain="new.example.com").count(), 1)
        body["websites"][0]["ga4"] = "properties/999"
        self.assertEqual(
            self.client.post(endpoint, body, content_type="application/json").status_code, 422
        )
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.post(endpoint, body, content_type="application/json").status_code, 404
        )
        self.client.force_login(self.viewer)
        self.assertEqual(
            self.client.post(endpoint, body, content_type="application/json").status_code, 403
        )

    @patch("apps.analytics.onboarding.discover_websites")
    @patch("apps.analytics.linking.discover")
    @patch("apps.analytics.linking.queue_sync")
    def test_search_only_import_uses_provider_timezone(
        self, queue: MagicMock, discovery: MagicMock, inventory: MagicMock
    ) -> None:
        inventory.return_value = {
            "websites": [
                {
                    "domain": "search.example.com",
                    "ga4": [],
                    "gsc": [{"id": "sc-domain:search.example.com"}],
                }
            ]
        }
        discovery.return_value = {
            "gsc": [{"siteUrl": "sc-domain:search.example.com", "permissionLevel": "siteFullUser"}]
        }
        response = self.client.post(
            f"/api/analytics/connections/{self.connection.pk}/websites",
            {"websites": [{"domain": "search.example.com", "gsc": "sc-domain:search.example.com"}]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.business.websites.get(domain="search.example.com").timezone, "America/Los_Angeles"
        )

    def test_first_workspace_is_automatic_idempotent_and_does_not_elevate_viewer(self) -> None:
        fresh = User.objects.create_user(
            email="fresh@example.test",
            password="test-password",
            first_name="Fresh",
            last_name="User",
        )
        self.client.force_login(fresh)
        first = self.client.post("/api/analytics/onboarding", content_type="application/json")
        second = self.client.post("/api/analytics/onboarding", content_type="application/json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(BusinessMembership.objects.filter(user=fresh).count(), 1)
        self.client.force_login(self.viewer)
        self.assertEqual(
            self.client.post(
                "/api/analytics/onboarding", content_type="application/json"
            ).status_code,
            403,
        )

    @override_settings(ANALYTICS_FRONTEND_URL="https://analytics.adbsoftwaresolutions.co.uk")
    @patch("apps.analytics.api.oauth_callback")
    def test_google_callback_returns_to_dashboard_with_authorized_context(
        self, callback: MagicMock
    ) -> None:
        callback.return_value = self.connection
        response = self.client.get(
            "/api/analytics/oauth/callback?state=bound-state&code=provider-code"
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            f"https://analytics.adbsoftwaresolutions.co.uk/dashboard?integration=connected&business={self.business.pk}&connection={self.connection.pk}",
        )
        self.assertIn("no-store", response["Cache-Control"])

    @patch("apps.analytics.reports.google_request")
    def test_realtime_uses_compatible_event_metrics_and_separate_user_totals(
        self, provider: MagicMock
    ) -> None:
        provider.side_effect = [
            {
                "dimensionHeaders": [
                    {"name": "eventName"},
                    {"name": "country"},
                    {"name": "deviceCategory"},
                ],
                "metricHeaders": [{"name": "eventCount", "type": "TYPE_INTEGER"}],
                "rows": [
                    {
                        "dimensionValues": [
                            {"value": "page_view"},
                            {"value": "United Kingdom"},
                            {"value": "desktop"},
                        ],
                        "metricValues": [{"value": "8"}],
                    }
                ],
            },
            {
                "metricHeaders": [
                    {"name": "activeUsers", "type": "TYPE_INTEGER"},
                    {"name": "eventCount", "type": "TYPE_INTEGER"},
                ],
                "rows": [{"metricValues": [{"value": "2"}, {"value": "8"}]}],
            },
        ]
        endpoint = f"/api/analytics/websites/{self.website.pk}/realtime"
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["rows"],
            [
                {
                    "eventName": "page_view",
                    "country": "United Kingdom",
                    "deviceCategory": "desktop",
                    "eventCount": 8,
                }
            ],
        )
        self.assertEqual(response.json()["totals"], [{"activeUsers": 2, "eventCount": 8}])
        breakdown = provider.call_args_list[0].kwargs["body"]
        self.assertIn({"name": "eventName"}, breakdown["dimensions"])
        self.assertEqual(breakdown["metrics"], [{"name": "eventCount"}])
        totals = provider.call_args_list[1].kwargs["body"]
        self.assertNotIn("dimensions", totals)
        self.assertEqual(totals["metrics"], [{"name": "activeUsers"}, {"name": "eventCount"}])
        self.assertEqual(self.client.get(endpoint).status_code, 200)
        self.assertEqual(provider.call_count, 2)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(endpoint).status_code, 404)

    def _experience_snapshot(
        self,
        report: str,
        data: list[dict[str, object]],
        *,
        previous: bool = False,
        prop: ProviderProperty | None = None,
        complete: bool = True,
    ) -> ReportSnapshot:
        start, end = previous_window(self.start, self.end) if previous else (self.start, self.end)
        return ReportSnapshot.objects.create(
            property=prop or self.prop,
            report=report,
            start=start,
            end=end,
            payload={"rows": data, "complete": complete},
        )

    def test_portfolio_uses_exact_period_visitors_and_safe_comparisons(self) -> None:
        self._experience_snapshot(
            "overview", [{"totalUsers": 1000, "sessions": 1500, "keyEvents": 40}]
        )
        self._experience_snapshot(
            "overview", [{"totalUsers": 800, "sessions": 1000, "keyEvents": 30}], previous=True
        )
        self._experience_snapshot(
            "trend",
            [{"date": "20260101", "totalUsers": 100}, {"date": "20260102", "totalUsers": 200}],
        )
        response = self.client.get("/api/analytics/portfolio?start=2026-01-01&end=2026-01-28")
        self.assertEqual(response.status_code, 200)
        value = response.json()
        self.assertEqual(value["metrics"]["visitors"]["current"], 1000)
        self.assertEqual(value["metrics"]["visitors"]["change"], 25)
        self.assertEqual(value["trend"][0]["visitors"], 100)
        self.assertIsNone(value["trend"][2]["visitors"])
        self.assertTrue(any(item["metric"] == "totalUsers" for item in value["insights"]))

    def test_experience_apis_preserve_business_scope_and_viewer_access(self) -> None:
        endpoint = (
            f"/api/analytics/websites/{self.website.pk}/dashboard?start=2026-01-01&end=2026-01-28"
        )
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(endpoint).status_code, 200)
        self.assertEqual(
            len(
                self.client.get("/api/analytics/portfolio?start=2026-01-01&end=2026-01-28").json()[
                    "sites"
                ]
            ),
            1,
        )
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(endpoint).status_code, 404)
        self.assertEqual(
            self.client.get("/api/analytics/portfolio?start=2026-01-01&end=2026-01-28").json()[
                "sites"
            ],
            [],
        )
        self.assertEqual(
            self.client.get(
                f"/api/analytics/portfolio?business_id={self.business.pk}&start=2026-01-01&end=2026-01-28"
            ).status_code,
            404,
        )
        self.client.logout()
        self.assertEqual(self.client.get(endpoint).status_code, 401)

    def test_portfolio_missing_data_remains_unavailable(self) -> None:
        response = self.client.get("/api/analytics/portfolio?start=2026-01-01&end=2026-01-28")
        metric = response.json()["metrics"]["visitors"]
        self.assertIsNone(metric["current"])
        self.assertIsNone(metric["change"])
        self.assertEqual(metric["covered"], 0)
        self.assertEqual(metric["expected"], 1)

    def test_portfolio_does_not_double_count_shared_google_properties(self) -> None:
        other = save_website(
            self.owner,
            self.business.pk,
            name="Another domain",
            domain="another.example.com",
            timezone="Europe/London",
        )
        prop = ProviderProperty.objects.create(
            website=other,
            connection=self.connection,
            provider="ga4",
            external_id=self.prop.external_id,
        )
        for item in (self.prop, prop):
            self._experience_snapshot("overview", [{"totalUsers": 100, "sessions": 120}], prop=item)
            self._experience_snapshot("trend", [{"date": "20260101", "totalUsers": 20}], prop=item)
        response = self.client.get("/api/analytics/portfolio?start=2026-01-01&end=2026-01-28")
        value = response.json()
        self.assertEqual(len(value["sites"]), 2)
        self.assertEqual(value["metrics"]["visitors"]["current"], 100)
        self.assertEqual(value["metrics"]["visitors"]["expected"], 1)
        self.assertEqual(value["trend"][0]["visitors"], 20)
        self.assertTrue(all(site["shared_providers"] == ["ga4"] for site in value["sites"]))

    def test_portfolio_with_incomplete_previous_coverage_does_not_invent_delta(self) -> None:
        other = save_website(
            self.owner,
            self.business.pk,
            name="New website",
            domain="new.example.com",
            timezone="Europe/London",
        )
        prop = ProviderProperty.objects.create(
            website=other, connection=self.connection, provider="ga4", external_id="properties/987"
        )
        self._experience_snapshot("overview", [{"totalUsers": 20}], prop=prop)
        self._experience_snapshot("overview", [{"totalUsers": 100}])
        self._experience_snapshot("overview", [{"totalUsers": 50}], previous=True)
        value = self.client.get("/api/analytics/portfolio?start=2026-01-01&end=2026-01-28").json()
        self.assertEqual(value["metrics"]["visitors"]["current"], 120)
        self.assertIsNone(value["metrics"]["visitors"]["previous"])
        self.assertIsNone(value["metrics"]["visitors"]["change"])

    def test_unified_dashboard_ranks_all_rows_and_groups_sources_before_limiting(self) -> None:
        pages = [{"pageLocation": f"https://example.com/{i}", "sessions": i} for i in range(20)]
        self._experience_snapshot("pages", pages)
        self._experience_snapshot(
            "acquisition",
            [
                {
                    "sessionDefaultChannelGroup": "Organic Search",
                    "sessionSourceMedium": "google / organic",
                    "sessionCampaignName": str(i),
                    "sessions": 10,
                    "engagedSessions": 5,
                }
                for i in range(20)
            ],
        )
        value = self.client.get(
            f"/api/analytics/websites/{self.website.pk}/dashboard?start=2026-01-01&end=2026-01-28"
        ).json()
        self.assertEqual(value["reports"]["ga4"]["pages"]["current"]["rows"][0]["sessions"], 19)
        self.assertEqual(value["reports"]["ga4"]["pages"]["current"]["total"], 20)
        channels = value["reports"]["ga4"]["channels"]["current"]["rows"]
        self.assertEqual(channels[0]["sessions"], 200)
        self.assertEqual(channels[0]["engagementRate"], 0.5)

    def test_experience_insights_do_not_treat_small_or_truncated_samples_as_anomalies(self) -> None:
        self._experience_snapshot("overview", [{"totalUsers": 1000}])
        self._experience_snapshot("overview", [{"totalUsers": 100}], previous=True, complete=False)
        value = self.client.get("/api/analytics/portfolio?start=2026-01-01&end=2026-01-28").json()
        self.assertEqual(value["insights"], [])
        self.assertIsNone(value["metrics"]["visitors"]["change"])
        ReportSnapshot.objects.all().delete()
        self._experience_snapshot("overview", [{"totalUsers": 10}])
        self._experience_snapshot("overview", [{"totalUsers": 2}], previous=True)
        value = self.client.get("/api/analytics/portfolio?start=2026-01-01&end=2026-01-28").json()
        self.assertEqual(value["insights"], [])

    def test_dashboard_event_parameters_are_scoped_report_metadata(self) -> None:
        from apps.analytics.models import EventDefinition

        EventDefinition.objects.create(
            property=self.prop,
            kind="dimensions",
            external_name="customDimensions/1",
            payload={
                "parameterName": "button_name",
                "displayName": "Button name",
                "scope": "EVENT",
            },
        )
        self.client.force_login(self.viewer)
        endpoint = (
            f"/api/analytics/websites/{self.website.pk}/dashboard?start=2026-01-01&end=2026-01-28"
        )
        value = self.client.get(endpoint).json()
        self.assertEqual(
            value["parameters"], [{"parameterName": "button_name", "displayName": "Button name"}]
        )
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(endpoint).status_code, 404)

    def test_source_insights_aggregate_campaigns_in_both_windows(self) -> None:
        for previous, counts in ((False, [80, 40]), (True, [40, 40])):
            self._experience_snapshot(
                "acquisition",
                [
                    {
                        "sessionSourceMedium": "google / organic",
                        "sessionCampaignName": str(i),
                        "sessions": count,
                    }
                    for i, count in enumerate(counts)
                ],
                previous=previous,
            )
        response = self.client.get(
            "/api/analytics/portfolio?start=2026-01-01&end=2026-01-28"
        ).json()
        insight = next(item for item in response["insights"] if item["id"].endswith(":source"))
        self.assertEqual(insight["current"], 120)
        self.assertEqual(insight["previous"], 80)
        self.assertEqual(insight["change"], 50)

    def test_search_opportunities_have_measured_evidence_and_thresholding_is_respected(
        self,
    ) -> None:
        from apps.analytics.models import ProviderProperty

        prop = ProviderProperty.objects.create(
            website=self.website,
            connection=self.prop.connection,
            provider="gsc",
            external_id="sc-domain:example.com",
        )
        self._experience_snapshot(
            "queries",
            [
                {
                    "query": "custom software",
                    "clicks": 10,
                    "impressions": 1000,
                    "ctr": 0.01,
                    "position": 8,
                }
            ],
            prop=prop,
        )
        endpoint = "/api/analytics/portfolio?start=2026-01-01&end=2026-01-28"
        insights = self.client.get(endpoint).json()["insights"]
        self.assertEqual(len(insights), 1)
        self.assertEqual(insights[0]["value"], "custom software")
        self.assertEqual(insights[0]["level"], "opportunity")
        stored = ReportSnapshot.objects.get(property=prop, report="queries")
        stored.payload["metadata"] = {"subjectToThresholding": True}
        stored.save(update_fields=["payload"])
        self.assertEqual(self.client.get(endpoint).json()["insights"], [])

    def test_daily_decline_requires_consecutive_complete_data(self) -> None:
        rows: list[dict[str, object]] = [
            {"date": f"202601{i:02d}", "totalUsers": 100 if i < 8 else 20} for i in range(1, 9)
        ]
        self._experience_snapshot("trend", rows)
        endpoint = "/api/analytics/portfolio?start=2026-01-01&end=2026-01-28"
        insights = self.client.get(endpoint).json()["insights"]
        self.assertEqual(len(insights), 1)
        self.assertIn("not seasonally adjusted", insights[0]["detail"])
        stored = ReportSnapshot.objects.get(property=self.prop, report="trend")
        stored.payload["rows"][3]["date"] = "20260120"
        stored.save(update_fields=["payload"])
        self.assertEqual(self.client.get(endpoint).json()["insights"], [])

    @patch(
        "apps.analytics.google.token_request",
        return_value={"access_token": "next-access", "expires_in": 3600},
    )
    def test_refresh_preserves_refresh_token_and_skips_fresh_credentials(
        self, token: MagicMock
    ) -> None:
        self.connection.expires_at = timezone.now() - timedelta(seconds=1)
        self.connection.save()
        self.assertEqual(access_token(self.connection), "next-access")
        self.assertEqual(access_token(self.connection), "next-access")
        token.assert_called_once()
        self.credential.refresh_from_db()
        self.assertEqual(
            load_credential_secrets_for_service(self.credential)["refresh_token"], "refresh-test"
        )
        self.connection.refresh_from_db()
        self.assertIsNotNone(self.connection.last_refreshed_at)
        self.assertEqual(self.connection.refresh_failures, 0)

    @patch(
        "apps.analytics.google.token_request",
        side_effect=ProviderError("quota_exceeded", retryable=True),
    )
    def test_transient_refresh_failure_persists_shared_backoff(self, token: MagicMock) -> None:
        self.connection.expires_at = timezone.now() - timedelta(seconds=1)
        self.connection.save()
        for _ in range(2):
            with self.assertRaises(ProviderError):
                access_token(self.connection)
        token.assert_called_once()
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.status, "connected")
        self.assertEqual(self.connection.refresh_failures, 1)
        assert self.connection.refresh_retry_at is not None
        self.assertGreater(self.connection.refresh_retry_at, timezone.now())
        self.connection.refresh_retry_at = timezone.now() - timedelta(seconds=1)
        self.connection.save()
        with self.assertRaises(ProviderError):
            access_token(self.connection)
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.refresh_failures, 2)
        self.assertGreater((self.connection.refresh_retry_at - timezone.now()).total_seconds(), 110)

    @patch("apps.analytics.google.token_request", side_effect=ProviderError("credentials_revoked"))
    def test_permanent_refresh_failure_stops_further_requests(self, token: MagicMock) -> None:
        self.connection.expires_at = timezone.now() - timedelta(seconds=1)
        self.connection.save()
        for _ in range(2):
            with self.assertRaises(ProviderError):
                access_token(self.connection)
        token.assert_called_once()
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.status, "reconnect")
        self.assertIsNone(self.connection.refresh_retry_at)

    @patch("apps.analytics.tasks.refresh_google_token.delay")
    def test_beat_enqueues_only_due_connected_accounts_without_a_session(
        self, enqueue: MagicMock
    ) -> None:
        from adbsoftwaresolutions.celery import app
        from apps.analytics.tasks import enqueue_token_refreshes

        self.assertEqual(app.conf.beat_schedule["analytics-token-refresh"]["schedule"], 300)
        self.connection.expires_at = timezone.now() + timedelta(minutes=5)
        self.connection.save()
        enqueue_token_refreshes()
        enqueue.assert_called_once_with(self.connection.pk)
        enqueue.reset_mock()
        for updates in (
            {"refresh_retry_at": timezone.now() + timedelta(minutes=2)},
            {"refresh_retry_at": None, "status": "reconnect"},
            {"status": "connected", "expires_at": timezone.now() + timedelta(hours=1)},
        ):
            GoogleConnection.objects.filter(pk=self.connection.pk).update(**updates)
            enqueue_token_refreshes()
        enqueue.assert_not_called()

    @patch(
        "apps.analytics.tasks.access_token",
        side_effect=ProviderError("google_unavailable", retryable=True),
    )
    def test_background_refresh_retries_transient_failures_only(self, token: MagicMock) -> None:
        from celery.exceptions import Retry

        from apps.analytics.tasks import refresh_google_token

        with patch.object(refresh_google_token, "retry", side_effect=Retry()) as retry:
            with self.assertRaises(Retry):
                refresh_google_token.run(self.connection.pk)
            self.assertGreaterEqual(retry.call_args.kwargs["countdown"], 60)
        token.side_effect = ProviderError("credentials_revoked")
        with patch.object(refresh_google_token, "retry") as retry:
            refresh_google_token.run(self.connection.pk)
            retry.assert_not_called()

    @patch(
        "apps.analytics.google.authorized_request",
        return_value={"email": "reconnected@example.test", "sub": "same-google-sub"},
    )
    @patch(
        "apps.analytics.google.token_request",
        return_value={
            "access_token": "recovered-access",
            "refresh_token": "recovered-refresh",
            "scope": READ + " " + SEARCH + " " + EDIT,
            "expires_in": 3600,
        },
    )
    def test_reauthorization_recovers_same_connection_and_preserves_links(
        self, token: MagicMock, identity: MagicMock
    ) -> None:
        self.connection.subject = "same-google-sub"
        self.connection.status = "reconnect"
        self.connection.error_code = "credentials_revoked"
        self.connection.refresh_failures = 5
        self.connection.save()
        request = self._request()
        oauth_start(request, self.business.pk, "administration", self.connection.pk, "settings")
        recovered = oauth_callback(request, request.session["analytics_oauth"]["state"], "code")
        self.assertEqual(recovered.pk, self.connection.pk)
        self.prop.refresh_from_db()
        self.assertEqual(self.prop.connection_id, recovered.pk)
        self.assertEqual(recovered.status, "connected")
        self.assertEqual(recovered.refresh_failures, 0)
        self.assertEqual(recovered.error_code, "")
        self.assertEqual(
            load_credential_secrets_for_service(recovered.credential)["refresh_token"],
            "recovered-refresh",
        )
        self.assertIn(EDIT, recovered.scopes)

    @patch(
        "apps.analytics.google.authorized_request",
        return_value={"email": "different@example.test", "sub": "different-google-sub"},
    )
    @patch(
        "apps.analytics.google.token_request",
        return_value={"access_token": "wrong-account", "refresh_token": "wrong-refresh"},
    )
    def test_reauthorization_refuses_account_substitution_without_changing_tokens(
        self, token: MagicMock, identity: MagicMock
    ) -> None:
        self.connection.subject = "original-sub"
        self.connection.save()
        request = self._request()
        oauth_start(request, self.business.pk, "administration", self.connection.pk)
        with self.assertRaises(ProviderError):
            oauth_callback(request, request.session["analytics_oauth"]["state"], "code")
        self.credential.refresh_from_db()
        self.assertEqual(
            load_credential_secrets_for_service(self.credential)["refresh_token"], "refresh-test"
        )

    def test_reauthorization_cannot_target_another_business_connection(self) -> None:
        foreign = create_business(self.other, "Other workspace")
        request = self._request()
        with self.assertRaises((HttpError, Http404)):
            oauth_start(request, foreign.pk, "administration", self.connection.pk)
        self.client.force_login(self.viewer)
        self.assertEqual(
            self.client.post(
                f"/api/analytics/businesses/{self.business.pk}/oauth",
                {"connection_id": self.connection.pk},
                content_type="application/json",
            ).status_code,
            403,
        )

    @patch("apps.analytics.google.token_request", return_value={"unexpected": "response"})
    def test_malformed_refresh_response_does_not_destroy_credentials(
        self, token: MagicMock
    ) -> None:
        self.connection.expires_at = timezone.now() - timedelta(seconds=1)
        self.connection.save()
        with self.assertRaises(ProviderError) as caught:
            access_token(self.connection)
        self.assertTrue(caught.exception.retryable)
        self.credential.refresh_from_db()
        self.assertEqual(
            load_credential_secrets_for_service(self.credential)["refresh_token"], "refresh-test"
        )

    def test_connection_health_never_serializes_credentials(self) -> None:
        response = self.client.get(f"/api/analytics/businesses/{self.business.pk}/connections")
        self.assertEqual(response.status_code, 200)
        self.assertIn("refresh_retry_at", response.json()[0])
        self.assertNotIn("refresh-test", response.content.decode())
        self.assertNotIn("access-test", response.content.decode())
        self.assertNotIn("credential", response.json()[0])

    @patch("apps.analytics.google.requests.post")
    def test_token_endpoint_failures_are_classified_without_leaking_bodies(
        self, post: MagicMock
    ) -> None:
        import requests

        from apps.analytics.google import token_request

        for status, body, expected, retryable in (
            (
                400,
                '{"error":"invalid_grant", "error_description":"sensitive-provider-detail"}',
                "credentials_revoked",
                False,
            ),
            (400, '{"error":"invalid_client"}', "oauth_client_configuration", False),
            (400, '{"error":"temporarily_unavailable"}', "google_unavailable", True),
            (429, '{"error":"rate_limited"}', "quota_exceeded", True),
            (503, '{"error":"server_error"}', "google_unavailable", True),
        ):
            response = requests.Response()
            response.status_code, response._content = status, body.encode()
            response.headers["Retry-After"] = "300"
            post.return_value = response
            with self.assertRaises(ProviderError) as caught:
                token_request({"grant_type": "refresh_token", "refresh_token": "private-refresh"})
            self.assertEqual(caught.exception.code, expected)
            self.assertEqual(caught.exception.retryable, retryable)
            self.assertNotIn("private-refresh", str(caught.exception))
            self.assertNotIn("sensitive-provider-detail", str(caught.exception))
            if status == 429:
                self.assertEqual(caught.exception.retry_after, 300)

    @patch("apps.analytics.api.definitions", side_effect=ProviderError("google_permission_denied"))
    def test_google_property_permission_denial_is_distinct_from_oauth_consent(
        self, definitions: MagicMock
    ) -> None:
        response = self.client.get(
            f"/api/analytics/websites/{self.website.pk}/definitions/key-events"
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "google_permission_denied")
        self.assertIn("Editor or Administrator", response.json()["detail"])
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.status, "connected")

    @patch(
        "apps.analytics.google.authorized_request",
        side_effect=[ProviderError("credentials_revoked"), {"rows": []}],
    )
    @patch(
        "apps.analytics.google.token_request",
        return_value={"access_token": "recovered-access", "expires_in": 3600},
    )
    def test_api_401_recovers_once_without_requiring_interactive_login(
        self, token: MagicMock, transport: MagicMock
    ) -> None:
        from apps.analytics.google import DATA_URL, google_request

        result = google_request(self.connection, "GET", DATA_URL + "properties/1")
        self.assertEqual(result, {"rows": []})
        token.assert_called_once()
        self.assertEqual(transport.call_count, 2)
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.status, "connected")

    @patch("apps.analytics.google.token_request")
    def test_rejected_token_reuses_an_already_rotated_concurrent_token(
        self, token: MagicMock
    ) -> None:
        self.assertEqual(access_token(self.connection, rejected_token="old-access"), "access-test")
        token.assert_not_called()

    @patch(
        "apps.analytics.google.authorized_request", side_effect=ProviderError("credentials_revoked")
    )
    @patch(
        "apps.analytics.google.token_request",
        return_value={"access_token": "still-rejected", "expires_in": 3600},
    )
    def test_repeated_api_401_stops_after_one_refresh(
        self, token: MagicMock, transport: MagicMock
    ) -> None:
        from apps.analytics.google import DATA_URL, google_request

        with self.assertRaises(ProviderError):
            google_request(self.connection, "GET", DATA_URL + "properties/1")
        token.assert_called_once()
        self.assertEqual(transport.call_count, 2)
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.status, "reconnect")

    @patch(
        "apps.analytics.google.authorized_request",
        return_value={"email": "same@example.test", "sub": "same-sub"},
    )
    @patch(
        "apps.analytics.google.token_request",
        return_value={"access_token": "new-access", "scope": READ + " " + SEARCH + " " + EDIT},
    )
    def test_reauthorization_preserves_valid_offline_grant_when_no_replacement_is_returned(
        self, token: MagicMock, identity: MagicMock
    ) -> None:
        request = self._request()
        oauth_start(request, self.business.pk, "administration", self.connection.pk)
        result = oauth_callback(request, request.session["analytics_oauth"]["state"], "code")
        self.assertEqual(result.pk, self.connection.pk)
        self.assertEqual(
            load_credential_secrets_for_service(result.credential)["refresh_token"], "refresh-test"
        )

    @patch(
        "apps.analytics.google.authorized_request",
        return_value={"email": "same@example.test", "sub": "same-sub"},
    )
    @patch(
        "apps.analytics.google.token_request",
        return_value={"access_token": "new-access", "scope": READ + " " + SEARCH + " " + EDIT},
    )
    def test_reauthorization_requires_a_new_offline_grant_if_the_old_one_was_revoked(
        self, token: MagicMock, identity: MagicMock
    ) -> None:
        self.connection.status, self.connection.error_code = "reconnect", "credentials_revoked"
        self.connection.save()
        request = self._request()
        oauth_start(request, self.business.pk, "administration", self.connection.pk)
        with self.assertRaises(ProviderError) as caught:
            oauth_callback(request, request.session["analytics_oauth"]["state"], "code")
        self.assertEqual(caught.exception.code, "offline_access_required")
        self.connection.refresh_from_db()
        self.assertEqual(self.connection.status, "reconnect")


@override_settings(CREDENTIAL_ENCRYPTION_KEYS=[Fernet.generate_key().decode()])
class GoogleRefreshConcurrencyTests(TransactionTestCase):
    def test_simultaneous_background_and_sync_refresh_share_one_exchange(self) -> None:
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event

        from django.db import close_old_connections, connection, connections

        from apps.analytics.models import Business

        if not connection.features.has_select_for_update:
            self.skipTest("This concurrency contract requires database row locks.")
        user = User.objects.create_user(
            email="concurrency@example.test",
            password="test-password",
            first_name="Test",
            last_name="User",
        )
        business = Business.objects.create(name="Concurrency", slug="concurrency")
        credential = StoredCredential.objects.create(name="Concurrent OAuth", created_by=user)
        store_credential_secrets(
            credential, {"access_token": "expired-access", "refresh_token": "original-refresh"}
        )
        account = GoogleConnection.objects.create(
            business=business,
            credential=credential,
            created_by=user,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        refreshing, release, second_started = Event(), Event(), Event()

        def exchange(data: dict[str, str]) -> dict[str, object]:
            refreshing.set()
            if not release.wait(10):
                raise AssertionError("Concurrent refresh did not reach the release gate")
            return {
                "access_token": "shared-access",
                "refresh_token": "rotated-refresh",
                "expires_in": 3600,
            }

        def refresh(background: bool) -> str:
            close_old_connections()
            if not background:
                second_started.set()
            try:
                return access_token(
                    account,
                    refresh_before=timedelta(minutes=10) if background else timedelta(seconds=90),
                )
            finally:
                connections.close_all()

        with patch("apps.analytics.google.token_request", side_effect=exchange) as token:
            with ThreadPoolExecutor(max_workers=2) as workers:
                first = workers.submit(refresh, True)
                try:
                    self.assertTrue(refreshing.wait(10))
                    second = workers.submit(refresh, False)
                    self.assertTrue(second_started.wait(10))
                finally:
                    release.set()
                self.assertEqual(first.result(timeout=15), "shared-access")
                self.assertEqual(second.result(timeout=15), "shared-access")
            token.assert_called_once()
        credential.refresh_from_db()
        self.assertEqual(
            load_credential_secrets_for_service(credential)["refresh_token"], "rotated-refresh"
        )
