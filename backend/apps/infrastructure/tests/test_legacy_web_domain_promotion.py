from datetime import date

from django.test import TestCase

from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.legacy_reconciliation import reconcile_legacy_resource
from apps.infrastructure.models import (
    Domain,
    DomainProfile,
    InfrastructureResource,
    SSLCertificate,
    TLSCertificate,
    TLSCertificateDomain,
    Website,
    WebsiteEndpoint,
    WebsiteProfile,
)


class LegacyWebDomainPromotionTests(TestCase):
    def setUp(self) -> None:
        self.client_record = Client.objects.create(
            name="Legacy Web Client",
            company="Legacy Web Client Ltd",
            email="legacy-web-client@example.com",
            status="active",
        )

    def _reconcile(
        self,
        legacy_type: str,
        legacy_id: int,
        *,
        ownership_type: str = OwnershipType.INTERNAL,
        client: Client | None = None,
        environment: str = InfrastructureResource.Environment.PRODUCTION,
        criticality: str = InfrastructureResource.Criticality.NORMAL,
    ) -> InfrastructureResource:
        return reconcile_legacy_resource(
            legacy_type=legacy_type,
            legacy_id=legacy_id,
            ownership_type=ownership_type,
            client=client,
            lifecycle_status=InfrastructureResource.LifecycleStatus.ACTIVE,
            environment=environment,
            criticality=criticality,
            name=None,
            linked_by=None,
        )

    def test_website_promotion_creates_profile_and_primary_endpoint_without_guessing(self) -> None:
        legacy = Website.objects.create(
            name="Legacy Client Website",
            primary_url="https://www.client-example.test",
            environment_type="production",
            admin_url="https://www.client-example.test/admin",
            has_cdn=True,
            cdn_provider="Cloudflare from legacy free text",
            aliases="client-example.test, old.client-example.test",
            notes="Potentially sensitive operational notes must remain legacy-only.",
        )

        resource = self._reconcile(
            "website",
            legacy.id,
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            environment=InfrastructureResource.Environment.PRODUCTION,
            criticality=InfrastructureResource.Criticality.HIGH,
        )

        website = WebsiteProfile.objects.get(resource=resource)
        endpoint = WebsiteEndpoint.objects.get(website=website)
        self.assertEqual(website.admin_url, legacy.admin_url)
        self.assertIsNone(website.hosting_provider_account_id)
        self.assertIsNone(website.cdn_provider_account_id)
        self.assertIsNone(website.waf_provider_account_id)
        self.assertEqual(endpoint.url, legacy.primary_url)
        self.assertTrue(endpoint.is_primary)
        self.assertEqual(endpoint.role, WebsiteEndpoint.Role.PRIMARY)
        self.assertEqual(endpoint.resource.ownership_type, OwnershipType.CLIENT)
        self.assertEqual(endpoint.resource.client_id, self.client_record.id)
        self.assertEqual(
            endpoint.resource.environment,
            InfrastructureResource.Environment.PRODUCTION,
        )
        self.assertEqual(
            endpoint.resource.criticality,
            InfrastructureResource.Criticality.HIGH,
        )
        self.assertEqual(website.endpoints.count(), 1)
        self.assertNotIn("old.client-example.test", endpoint.url)
        self.assertNotIn("sensitive operational notes", resource.description.lower())

    def test_domain_promotion_only_copies_deterministic_registration_fields(self) -> None:
        legacy = Domain.objects.create(
            domain_name="client-example.test",
            registrar="cloudflare",
            expiry_date=date(2027, 5, 17),
            auto_renew=False,
            nameservers="ns1.example.test,ns2.example.test",
        )

        resource = self._reconcile("domain", legacy.id)

        domain = DomainProfile.objects.get(resource=resource)
        self.assertEqual(domain.domain_name, "client-example.test")
        self.assertEqual(domain.expires_on, date(2027, 5, 17))
        self.assertFalse(domain.auto_renew)
        self.assertIsNone(domain.registrar_account_id)
        self.assertEqual(domain.provider_domain_id, "")

    def test_ssl_promotion_links_an_already_reconciled_domain(self) -> None:
        legacy_domain = Domain.objects.create(
            domain_name="secure.client-example.test",
            registrar="other",
            expiry_date=date(2027, 8, 1),
        )
        domain_resource = self._reconcile("domain", legacy_domain.id)
        domain = DomainProfile.objects.get(resource=domain_resource)
        legacy_certificate = SSLCertificate.objects.create(
            domain=legacy_domain,
            provider="letsencrypt",
            cert_type="Legacy free text type",
            expiry_date=date(2026, 11, 30),
        )

        certificate_resource = self._reconcile(
            "ssl_certificate",
            legacy_certificate.id,
        )

        certificate = TLSCertificate.objects.get(resource=certificate_resource)
        link = TLSCertificateDomain.objects.get(certificate=certificate)
        self.assertEqual(certificate.certificate_type, TLSCertificate.CertificateType.ACME)
        self.assertEqual(certificate.issuer, "Let's Encrypt")
        self.assertEqual(certificate.subject_common_name, legacy_domain.domain_name)
        expires_at = certificate.expires_at
        self.assertIsNotNone(expires_at)
        if expires_at is None:
            self.fail("Promoted TLS certificate expiry should be populated.")
        self.assertEqual(expires_at.date(), legacy_certificate.expiry_date)
        self.assertIsNone(certificate.provider_account_id)
        self.assertEqual(link.domain_id, domain.id)
        self.assertTrue(link.is_primary)

    def test_ssl_promotion_does_not_guess_unreconciled_domain_relationship(self) -> None:
        legacy_domain = Domain.objects.create(
            domain_name="unlinked.client-example.test",
            registrar="namecheap",
            expiry_date=date(2027, 9, 1),
        )
        legacy_certificate = SSLCertificate.objects.create(
            domain=legacy_domain,
            provider="cloudflare",
            cert_type="Universal SSL",
            expiry_date=date(2027, 1, 15),
        )

        certificate_resource = self._reconcile(
            "ssl_certificate",
            legacy_certificate.id,
        )

        certificate = TLSCertificate.objects.get(resource=certificate_resource)
        self.assertEqual(certificate.certificate_type, TLSCertificate.CertificateType.OTHER)
        self.assertEqual(certificate.issuer, "Cloudflare")
        self.assertEqual(certificate.domain_links.count(), 0)
