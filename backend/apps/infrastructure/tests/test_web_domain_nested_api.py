from typing import cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import (
    DNSRecord,
    DNSZone,
    DomainProfile,
    InfrastructureResource,
    TLSCertificate,
    TLSCertificateDomain,
    WebsiteEndpoint,
    WebsiteProfile,
)
from apps.infrastructure.ninja.web_domain_nested_views import (
    list_dns_records,
    list_tls_certificate_domains,
    list_website_endpoints,
)
from apps.infrastructure.ninja.web_domain_schemas import (
    DNSRecordOut,
    TLSCertificateDomainOut,
    WebsiteEndpointOut,
)
from authentication.models import User


class WebDomainNestedApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.client_a = Client.objects.create(
            name="Nested Client A",
            company="Nested Client A Ltd",
            email="nested-client-a@example.com",
            status="active",
        )
        self.client_b = Client.objects.create(
            name="Nested Client B",
            company="Nested Client B Ltd",
            email="nested-client-b@example.com",
            status="active",
        )

        website_resource = self._resource(
            "Client A Website",
            InfrastructureResource.ResourceType.WEBSITE,
            client=self.client_a,
        )
        self.website = WebsiteProfile.objects.create(resource=website_resource)
        active_endpoint_resource = self._resource(
            "Client A Production Endpoint",
            InfrastructureResource.ResourceType.WEBSITE_ENDPOINT,
            client=self.client_a,
        )
        self.active_endpoint = WebsiteEndpoint.objects.create(
            resource=active_endpoint_resource,
            website=self.website,
            url="https://client-a.example.com",
            is_primary=True,
        )
        archived_endpoint_resource = self._resource(
            "Client A Archived Endpoint",
            InfrastructureResource.ResourceType.WEBSITE_ENDPOINT,
            client=self.client_a,
            lifecycle_status=InfrastructureResource.LifecycleStatus.ARCHIVED,
        )
        WebsiteEndpoint.objects.create(
            resource=archived_endpoint_resource,
            website=self.website,
            url="https://old.client-a.example.com",
        )
        foreign_endpoint_resource = self._resource(
            "Client B Invalid Endpoint",
            InfrastructureResource.ResourceType.WEBSITE_ENDPOINT,
            client=self.client_b,
        )
        self.foreign_endpoint = WebsiteEndpoint.objects.create(
            resource=foreign_endpoint_resource,
            website=self.website,
            url="https://leak.client-b.example.com",
        )

        domain_resource = self._resource(
            "Client A Domain",
            InfrastructureResource.ResourceType.DOMAIN,
            client=self.client_a,
        )
        self.domain = DomainProfile.objects.create(
            resource=domain_resource,
            domain_name="client-a.example.com",
        )
        zone_resource = self._resource(
            "Client A DNS",
            InfrastructureResource.ResourceType.DNS_ZONE,
            client=self.client_a,
        )
        self.zone = DNSZone.objects.create(
            resource=zone_resource,
            domain=self.domain,
            zone_name="client-a.example.com",
        )
        self.record = DNSRecord.objects.create(
            zone=self.zone,
            name="@",
            record_type=DNSRecord.RecordType.A,
            value="203.0.113.10",
            ttl=300,
        )

        certificate_resource = self._resource(
            "Client A TLS",
            InfrastructureResource.ResourceType.TLS_CERTIFICATE,
            client=self.client_a,
        )
        self.certificate = TLSCertificate.objects.create(
            resource=certificate_resource,
            subject_common_name="client-a.example.com",
        )
        self.domain_link = TLSCertificateDomain.objects.create(
            certificate=self.certificate,
            domain=self.domain,
            is_primary=True,
        )
        foreign_domain_resource = self._resource(
            "Client B Invalid Domain",
            InfrastructureResource.ResourceType.DOMAIN,
            client=self.client_b,
        )
        self.foreign_domain = DomainProfile.objects.create(
            resource=foreign_domain_resource,
            domain_name="client-b.example.com",
        )
        self.foreign_domain_link = TLSCertificateDomain.objects.create(
            certificate=self.certificate,
            domain=self.foreign_domain,
        )

        other_website_resource = self._resource(
            "Client B Website",
            InfrastructureResource.ResourceType.WEBSITE,
            client=self.client_b,
        )
        self.other_website = WebsiteProfile.objects.create(resource=other_website_resource)

    def _resource(
        self,
        name: str,
        resource_type: str,
        *,
        client: Client,
        lifecycle_status: str = InfrastructureResource.LifecycleStatus.ACTIVE,
    ) -> InfrastructureResource:
        return InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=client,
            name=name,
            resource_type=resource_type,
            lifecycle_status=lifecycle_status,
        )

    def _request(self, user: User) -> HttpRequest:
        request = self.factory.get("/api/admin/infrastructure/nested")
        request.user = user
        return request

    def _user(self, email: str) -> User:
        user = User.objects.create_user(
            email=email,
            password="test-password",
            first_name="Nested",
            last_name="Operator",
            is_staff=True,
        )
        codenames = [
            "view_infrastructureresource",
            "view_websiteprofile",
            "view_websiteendpoint",
            "view_dnszone",
            "view_dnsrecord",
            "view_tlscertificate",
            "view_domainprofile",
            "view_tlscertificatedomain",
        ]
        permissions = Permission.objects.filter(
            content_type__app_label="infrastructure",
            codename__in=codenames,
        )
        user.user_permissions.add(*permissions)
        profile, _ = StaffAccessProfile.objects.get_or_create(user=user)
        ClientAccessGrant.objects.create(profile=profile, client=self.client_a)
        return user

    def test_website_endpoints_only_return_current_accessible_children(self) -> None:
        user = self._user("nested-web@example.com")

        result = cast(
            list[WebsiteEndpointOut],
            list_website_endpoints(self._request(user), self.website.resource_id),
        )

        self.assertEqual([item.resource_id for item in result], [self.active_endpoint.resource_id])
        self.assertNotIn(
            self.foreign_endpoint.resource_id,
            {item.resource_id for item in result},
        )

    def test_dns_records_return_for_visible_zone(self) -> None:
        user = self._user("nested-dns@example.com")

        result = cast(
            list[DNSRecordOut],
            list_dns_records(self._request(user), self.zone.resource_id),
        )

        self.assertEqual([item.id for item in result], [self.record.id])
        self.assertEqual(result[0].value, "203.0.113.10")

    def test_tls_domain_coverage_only_returns_accessible_domains(self) -> None:
        user = self._user("nested-tls@example.com")

        result = cast(
            list[TLSCertificateDomainOut],
            list_tls_certificate_domains(self._request(user), self.certificate.resource_id),
        )

        self.assertEqual([item.id for item in result], [self.domain_link.id])
        self.assertEqual(result[0].domain_resource_id, self.domain.resource_id)
        self.assertNotIn(self.foreign_domain_link.id, {item.id for item in result})

    def test_nested_api_hides_other_client_resources(self) -> None:
        user = self._user("nested-scope@example.com")

        status, payload = cast(
            tuple[int, dict[str, object]],
            list_website_endpoints(self._request(user), self.other_website.resource_id),
        )

        self.assertEqual(status, 404)
        self.assertEqual(payload["code"], "not_found")
