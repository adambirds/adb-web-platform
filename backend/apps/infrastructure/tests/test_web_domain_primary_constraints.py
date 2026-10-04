from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.core.ownership import OwnershipType
from apps.infrastructure.models import (
    DNSZone,
    DomainProfile,
    InfrastructureResource,
    TLSCertificate,
    TLSCertificateDomain,
    WebsiteEndpoint,
    WebsiteProfile,
)
from apps.infrastructure.ninja.web_domain_schemas import (
    DNSZoneCreateIn,
    TLSCertificateDomainCreateIn,
    WebsiteEndpointCreateIn,
)
from apps.infrastructure.ninja.web_domain_views import (
    archive_dns_zone,
    archive_website_endpoint,
    create_dns_zone,
    create_tls_certificate_domain,
    create_website_endpoint,
)
from authentication.models import User


class WebDomainPrimaryConstraintTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="web-primary@example.com",
            password="test-password",
            first_name="Web",
            last_name="Primary",
            is_staff=True,
            is_superuser=True,
        )

    def _resource(self, name: str, resource_type: str) -> InfrastructureResource:
        return InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name=name,
            resource_type=resource_type,
        )

    def _request(self) -> HttpRequest:
        request = self.factory.post("/api/admin/infrastructure")
        request.user = self.user
        return request

    def _domain(self, name: str) -> DomainProfile:
        resource = self._resource(name, InfrastructureResource.ResourceType.DOMAIN)
        return DomainProfile.objects.create(
            resource=resource,
            domain_name=name,
        )

    def test_domain_allows_only_one_primary_dns_zone(self) -> None:
        domain = self._domain("primary-zone.example")
        first_resource = self._resource(
            "Primary DNS zone",
            InfrastructureResource.ResourceType.DNS_ZONE,
        )
        first = DNSZone(
            resource=first_resource,
            domain=domain,
            zone_name="primary-zone.example",
            is_primary=True,
        )
        first.full_clean()
        first.save()
        second_resource = self._resource(
            "Second primary DNS zone",
            InfrastructureResource.ResourceType.DNS_ZONE,
        )
        second = DNSZone(
            resource=second_resource,
            domain=domain,
            zone_name="secondary.primary-zone.example",
            is_primary=True,
        )

        with self.assertRaises(ValidationError):
            second.full_clean()

    def test_certificate_allows_only_one_primary_domain(self) -> None:
        certificate_resource = self._resource(
            "Primary-name TLS",
            InfrastructureResource.ResourceType.TLS_CERTIFICATE,
        )
        certificate = TLSCertificate.objects.create(resource=certificate_resource)
        first_domain = self._domain("primary-tls.example")
        second_domain = self._domain("secondary-tls.example")
        first = TLSCertificateDomain(
            certificate=certificate,
            domain=first_domain,
            is_primary=True,
        )
        first.full_clean()
        first.save()
        second = TLSCertificateDomain(
            certificate=certificate,
            domain=second_domain,
            is_primary=True,
        )

        with self.assertRaises(ValidationError):
            second.full_clean()

    def test_second_primary_dns_zone_api_returns_validation_error(self) -> None:
        domain = self._domain("api-primary-zone.example")
        first_status, _ = create_dns_zone(
            self._request(),
            DNSZoneCreateIn(
                name="API primary DNS",
                domain_resource_id=domain.resource_id,
                zone_name=domain.domain_name,
                is_primary=True,
            ),
        )
        second_status, _ = create_dns_zone(
            self._request(),
            DNSZoneCreateIn(
                name="API second primary DNS",
                domain_resource_id=domain.resource_id,
                zone_name=f"secondary.{domain.domain_name}",
                is_primary=True,
            ),
        )

        self.assertEqual(first_status, 201)
        self.assertEqual(second_status, 400)

    def test_second_primary_tls_domain_api_returns_validation_error(self) -> None:
        certificate_resource = self._resource(
            "API primary-name TLS",
            InfrastructureResource.ResourceType.TLS_CERTIFICATE,
        )
        certificate = TLSCertificate.objects.create(resource=certificate_resource)
        first_domain = self._domain("api-primary-tls.example")
        second_domain = self._domain("api-secondary-tls.example")
        first_status, _ = create_tls_certificate_domain(
            self._request(),
            certificate.resource_id,
            TLSCertificateDomainCreateIn(
                domain_resource_id=first_domain.resource_id,
                is_primary=True,
            ),
        )
        second_status, _ = create_tls_certificate_domain(
            self._request(),
            certificate.resource_id,
            TLSCertificateDomainCreateIn(
                domain_resource_id=second_domain.resource_id,
                is_primary=True,
            ),
        )

        self.assertEqual(first_status, 201)
        self.assertEqual(second_status, 400)

    def test_archiving_primary_dns_zone_allows_replacement(self) -> None:
        domain = self._domain("replace-zone.example")
        first_resource = self._resource(
            "Retired primary DNS",
            InfrastructureResource.ResourceType.DNS_ZONE,
        )
        first = DNSZone.objects.create(
            resource=first_resource,
            domain=domain,
            zone_name=domain.domain_name,
            is_primary=True,
        )

        archive_dns_zone(self._request(), first_resource.id)

        first.refresh_from_db()
        first_resource.refresh_from_db()
        self.assertFalse(first.is_primary)
        self.assertEqual(
            first_resource.lifecycle_status,
            InfrastructureResource.LifecycleStatus.ARCHIVED,
        )
        status, _ = create_dns_zone(
            self._request(),
            DNSZoneCreateIn(
                name="Replacement primary DNS",
                domain_resource_id=domain.resource_id,
                zone_name=f"replacement.{domain.domain_name}",
                is_primary=True,
            ),
        )
        self.assertEqual(status, 201)

    def test_archiving_primary_website_endpoint_allows_replacement(self) -> None:
        website_resource = self._resource(
            "Replacement Website",
            InfrastructureResource.ResourceType.WEBSITE,
        )
        website = WebsiteProfile.objects.create(resource=website_resource)
        first_resource = self._resource(
            "Retired primary endpoint",
            InfrastructureResource.ResourceType.WEBSITE_ENDPOINT,
        )
        first = WebsiteEndpoint.objects.create(
            resource=first_resource,
            website=website,
            url="https://replacement.example",
            role=WebsiteEndpoint.Role.PRIMARY,
            is_primary=True,
        )

        archive_website_endpoint(self._request(), first_resource.id)

        first.refresh_from_db()
        first_resource.refresh_from_db()
        self.assertFalse(first.is_primary)
        self.assertEqual(
            first_resource.lifecycle_status,
            InfrastructureResource.LifecycleStatus.ARCHIVED,
        )
        status, _ = create_website_endpoint(
            self._request(),
            WebsiteEndpointCreateIn(
                name="Replacement primary endpoint",
                website_resource_id=website.resource_id,
                url="https://new.replacement.example",
                role=WebsiteEndpoint.Role.PRIMARY,
                is_primary=True,
            ),
        )
        self.assertEqual(status, 201)
