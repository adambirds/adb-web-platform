from __future__ import annotations

import ssl
from datetime import timedelta
from unittest.mock import MagicMock, patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from apps.core.models import AuditEvent
from apps.core.ownership import OwnershipType
from apps.infrastructure.metadata_refresh import (
    DomainMetadata,
    certificate_target,
    discover_certificate,
    discover_domain,
    ensure_expiry_check,
    refresh_metadata,
)
from apps.infrastructure.models import DomainProfile, InfrastructureResource, TLSCertificate
from apps.infrastructure.tasks import enqueue_metadata_refreshes, refresh_resource_metadata
from apps.monitoring.execution import execute_check
from apps.monitoring.models import MonitorCheck, MonitorIncident
from apps.monitoring.services import record_observation


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class RegistrationDiscoveryTests(SimpleTestCase):
    def setUp(self) -> None:
        cache.clear()
        self.bootstrap = {"services": [[["com"], ["https://registry.example/rdap/"]]]}
        self.events = [
            {"eventAction": "registration", "eventDate": "2020-01-01T00:00:00Z"},
            {"eventAction": "expiration", "eventDate": "2027-01-01T00:00:00Z"},
        ]
        self.response: dict[str, object] = {
            "objectClassName": "domain",
            "ldhName": "EXAMPLE.COM",
            "events": self.events,
            "status": ["client transfer prohibited"],
        }

    def test_authoritative_bootstrap_and_dates_are_used(self) -> None:
        with patch(
            "apps.infrastructure.metadata_refresh._rdap_json",
            side_effect=[self.bootstrap, self.response],
        ) as fetch:
            metadata = discover_domain("example.com")
        self.assertEqual(metadata.expires_on.isoformat(), "2027-01-01")
        assert metadata.registered_on is not None
        self.assertEqual(metadata.registered_on.isoformat(), "2020-01-01")
        self.assertTrue(metadata.transfer_lock_enabled)
        self.assertEqual(
            fetch.call_args.args[0], "https://registry.example/rdap/domain/example.com"
        )

    def test_unrelated_domain_response_is_rejected(self) -> None:
        self.response["ldhName"] = "other.com"
        with (
            patch(
                "apps.infrastructure.metadata_refresh._rdap_json",
                side_effect=[self.bootstrap, self.response],
            ),
            self.assertRaisesMessage(ValueError, "did not match"),
        ):
            discover_domain("example.com")

    def test_registry_without_expiration_does_not_guess(self) -> None:
        self.response["events"] = []
        with (
            patch(
                "apps.infrastructure.metadata_refresh._rdap_json",
                side_effect=[self.bootstrap, self.response],
            ),
            self.assertRaisesMessage(ValueError, "does not publish"),
        ):
            discover_domain("example.com")

    def test_unsupported_tld_is_reported(self) -> None:
        with (
            patch("apps.infrastructure.metadata_refresh._rdap_json", return_value=self.bootstrap),
            self.assertRaisesMessage(ValueError, "No HTTPS RDAP"),
        ):
            discover_domain("example.test")

    def test_conflicting_expirations_are_rejected(self) -> None:
        self.events.append({"eventAction": "expiration", "eventDate": "2028-01-01T00:00:00Z"})
        with (
            patch(
                "apps.infrastructure.metadata_refresh._rdap_json",
                side_effect=[self.bootstrap, self.response],
            ),
            self.assertRaisesMessage(ValueError, "conflicting"),
        ):
            discover_domain("example.com")

    def test_tls_der_metadata_includes_dates_and_fingerprint(self) -> None:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "example.com")])
        now = timezone.now().replace(microsecond=0)
        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(42)
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=60))
            .sign(key, hashes.SHA256())
        )
        context = MagicMock()
        context.wrap_socket.return_value.__enter__.return_value.getpeercert.return_value = (
            cert.public_bytes(serialization.Encoding.DER)
        )
        with (
            patch(
                "apps.infrastructure.metadata_refresh.ssl.create_default_context",
                return_value=context,
            ),
            patch("apps.infrastructure.metadata_refresh.socket.create_connection"),
        ):
            metadata = discover_certificate("https://example.com:8443/path")
        self.assertEqual(metadata["metadata_source"], "https://example.com:8443")
        self.assertEqual(metadata["subject_common_name"], "example.com")
        self.assertEqual(metadata["expires_at"], now + timedelta(days=60))
        self.assertEqual(metadata["fingerprint_sha256"], cert.fingerprint(hashes.SHA256()).hex())
        self.assertEqual(context.wrap_socket.call_args.kwargs["server_hostname"], "example.com")


class InventoryMetadataRefreshTests(TestCase):
    def setUp(self) -> None:
        self.resource = InfrastructureResource.objects.create(
            name="example.com",
            resource_type=InfrastructureResource.ResourceType.DOMAIN,
            ownership_type=OwnershipType.INTERNAL,
        )
        self.profile = DomainProfile.objects.create(
            resource=self.resource, domain_name="example.com", auto_renew=False
        )
        self.expiry = timezone.localdate() + timedelta(days=365)

    def create_certificate(self) -> TLSCertificate:
        resource = InfrastructureResource.objects.create(
            name="Example TLS",
            resource_type=InfrastructureResource.ResourceType.TLS_CERTIFICATE,
            ownership_type=OwnershipType.INTERNAL,
        )
        return TLSCertificate.objects.create(
            resource=resource,
            subject_common_name="example.com",
            expires_at=timezone.now() + timedelta(days=10),
        )

    def test_refresh_populates_dates_and_preserves_operator_renewal_policy(self) -> None:
        with patch(
            "apps.infrastructure.metadata_refresh.discover_domain",
            return_value=DomainMetadata(timezone.localdate(), self.expiry, True),
        ):
            self.assertTrue(refresh_metadata(self.resource.id))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.expires_on, self.expiry)
        self.assertFalse(self.profile.auto_renew)
        self.assertIsNotNone(self.profile.last_metadata_checked_at)
        self.assertEqual(self.profile.metadata_refresh_error, "")
        event = AuditEvent.objects.get(action="infrastructure.metadata_refreshed")
        self.assertEqual(event.resource_id, self.resource.id)
        self.assertEqual(event.metadata["source"], "rdap")
        check = MonitorCheck.objects.get(resource=self.resource)
        self.assertEqual(check.failure_threshold, 1)

    def test_renewal_updates_expiry_and_resolves_incident(self) -> None:
        self.profile.expires_on = timezone.localdate() + timedelta(days=2)
        self.profile.save()
        check = ensure_expiry_check(self.profile)
        record_observation(check.id, execute_check(check))
        self.assertEqual(MonitorIncident.objects.get().status, MonitorIncident.Status.OPEN)
        with patch(
            "apps.infrastructure.metadata_refresh.discover_domain",
            return_value=DomainMetadata(None, self.expiry, None),
        ):
            refresh_metadata(self.resource.id)
        check.refresh_from_db()
        record_observation(check.id, execute_check(check))
        self.assertEqual(MonitorIncident.objects.get().status, MonitorIncident.Status.RESOLVED)

    def test_failed_refresh_retains_known_dates_and_reports_error(self) -> None:
        self.profile.expires_on = self.expiry
        self.profile.save()
        with patch(
            "apps.infrastructure.metadata_refresh.discover_domain",
            side_effect=ValueError("Registry does not publish expiry"),
        ):
            refresh_metadata(self.resource.id)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.expires_on, self.expiry)
        self.assertIn("does not publish", self.profile.metadata_refresh_error)
        observation = execute_check(MonitorCheck.objects.get(resource=self.resource))
        self.assertTrue(observation.execution_error)

    def test_invalid_registration_dates_leave_inventory_unchanged(self) -> None:
        with patch(
            "apps.infrastructure.metadata_refresh.discover_domain",
            return_value=DomainMetadata(self.expiry + timedelta(days=1), self.expiry, None),
        ):
            refresh_metadata(self.resource.id)
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.registered_on)
        self.assertIsNone(self.profile.expires_on)
        self.assertIn("conflicts", self.profile.metadata_refresh_error)

    def test_recent_success_is_not_fetched_again(self) -> None:
        self.profile.last_metadata_checked_at = timezone.now()
        self.profile.save()
        with patch("apps.infrastructure.metadata_refresh.discover_domain") as discover:
            self.assertFalse(refresh_metadata(self.resource.id))
        discover.assert_not_called()

    def test_existing_disabled_check_is_preserved(self) -> None:
        check = MonitorCheck.objects.create(
            resource=self.resource,
            name="Manual registration check",
            check_type="domain_expiry",
            target="example.com",
            enabled=False,
            expiry_warning_days=60,
        )
        self.assertEqual(ensure_expiry_check(self.profile).id, check.id)
        check.refresh_from_db()
        self.assertFalse(check.enabled)
        self.assertEqual(check.expiry_warning_days, 60)
        self.assertEqual(MonitorCheck.objects.count(), 1)

    def test_retired_resource_is_not_refreshed_or_enqueued(self) -> None:
        self.resource.lifecycle_status = InfrastructureResource.LifecycleStatus.RETIRED
        self.resource.save()
        with (
            patch("apps.infrastructure.metadata_refresh.discover_domain") as discover,
            patch("apps.infrastructure.tasks.refresh_resource_metadata.delay") as dispatch,
        ):
            self.assertFalse(refresh_metadata(self.resource.id))
            self.assertEqual(enqueue_metadata_refreshes(), 0)
        discover.assert_not_called()
        dispatch.assert_not_called()

    def test_enqueue_only_due_profiles(self) -> None:
        certificate = self.create_certificate()
        certificate.last_metadata_checked_at = timezone.now()
        certificate.save()
        with patch("apps.infrastructure.tasks.refresh_resource_metadata.delay") as dispatch:
            self.assertEqual(enqueue_metadata_refreshes(), 1)
        dispatch.assert_called_once_with(self.resource.id)

    def test_worker_obeys_resource_lock(self) -> None:
        with (
            patch("apps.infrastructure.tasks._metadata_lock") as lock,
            patch("apps.infrastructure.tasks.refresh_metadata") as refresh,
        ):
            lock.return_value.__enter__.return_value = False
            refresh_resource_metadata(self.resource.id)
        refresh.assert_not_called()

    def test_certificate_renewal_updates_non_secret_metadata(self) -> None:
        certificate = self.create_certificate()
        expiry = timezone.now() + timedelta(days=90)
        with patch(
            "apps.infrastructure.metadata_refresh.discover_certificate",
            return_value={
                "expires_at": expiry,
                "issuer": "CN=New issuer",
                "fingerprint_sha256": "a" * 64,
            },
        ):
            refresh_metadata(certificate.resource_id)
        certificate.refresh_from_db()
        self.assertEqual(certificate.expires_at, expiry)
        self.assertEqual(certificate.issuer, "CN=New issuer")
        self.assertEqual(certificate.fingerprint_sha256, "a" * 64)
        check = MonitorCheck.objects.get(resource=certificate.resource)
        self.assertEqual(check.check_type, MonitorCheck.CheckType.CERTIFICATE_EXPIRY)
        self.assertTrue(execute_check(check).successful)

    def test_certificate_tls_failure_retains_metadata(self) -> None:
        certificate = self.create_certificate()
        expiry = certificate.expires_at
        with patch(
            "apps.infrastructure.metadata_refresh.discover_certificate",
            side_effect=ssl.SSLCertVerificationError("TLS validation failed"),
        ):
            refresh_metadata(certificate.resource_id)
        certificate.refresh_from_db()
        self.assertEqual(certificate.expires_at, expiry)
        self.assertIn("TLS validation failed", certificate.metadata_refresh_error)

    def test_wildcard_without_endpoint_requires_explicit_target(self) -> None:
        certificate = self.create_certificate()
        certificate.subject_common_name = "*.example.com"
        certificate.save()
        self.assertIsNone(certificate_target(certificate))
        refresh_metadata(certificate.resource_id)
        certificate.refresh_from_db()
        self.assertIn("Link an HTTPS", certificate.metadata_refresh_error)

    def test_expired_stored_certificate_opens_incident(self) -> None:
        certificate = self.create_certificate()
        certificate.expires_at = timezone.now() - timedelta(days=1)
        certificate.save()
        check = ensure_expiry_check(certificate)
        observation = execute_check(check)
        self.assertFalse(observation.successful)
        self.assertFalse(observation.execution_error)
        record_observation(check.id, observation)
        self.assertEqual(MonitorIncident.objects.get().status, MonitorIncident.Status.OPEN)

    def test_failed_refresh_retries_after_an_hour(self) -> None:
        self.profile.last_metadata_checked_at = timezone.now() - timedelta(hours=2)
        self.profile.metadata_refresh_error = "Registry temporarily unavailable"
        self.profile.save()
        with patch("apps.infrastructure.tasks.refresh_resource_metadata.delay") as dispatch:
            self.assertEqual(enqueue_metadata_refreshes(), 1)
        dispatch.assert_called_once_with(self.resource.id)

    def test_inventory_identity_changed_during_lookup_is_not_overwritten(self) -> None:
        def lookup(domain_name: str) -> DomainMetadata:
            DomainProfile.objects.filter(pk=self.profile.pk).update(domain_name="other.com")
            return DomainMetadata(None, self.expiry, None)

        with patch("apps.infrastructure.metadata_refresh.discover_domain", side_effect=lookup):
            self.assertFalse(refresh_metadata(self.resource.id))
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.expires_on)
        self.assertIsNone(self.profile.last_metadata_checked_at)

    def test_discovered_wildcard_retains_concrete_endpoint_for_next_refresh(self) -> None:
        certificate = self.create_certificate()
        with patch(
            "apps.infrastructure.metadata_refresh.discover_certificate",
            return_value={
                "subject_common_name": "*.example.com",
                "metadata_source": "https://example.com",
            },
        ):
            refresh_metadata(certificate.resource_id)
        certificate.refresh_from_db()
        self.assertEqual(certificate.subject_common_name, "*.example.com")
        self.assertEqual(certificate_target(certificate), "https://example.com")
