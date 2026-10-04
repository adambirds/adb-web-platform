from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import (
    ApplicationEnvironment,
    ApplicationProfile,
    DNSRecord,
    DNSZone,
    DomainProfile,
    InfrastructureResource,
    ProviderAccount,
    ServiceProvider,
    TLSCertificate,
    TLSCertificateDomain,
    WebsiteEndpoint,
    WebsiteProfile,
)


class WebDomainSpecialistModelTests(TestCase):
    def setUp(self) -> None:
        self.client_a = Client.objects.create(
            name="Client A",
            company="Client A Ltd",
            email="client-a-web@example.com",
            status="active",
        )
        self.client_b = Client.objects.create(
            name="Client B",
            company="Client B Ltd",
            email="client-b-web@example.com",
            status="active",
        )
        provider = ServiceProvider.objects.create(
            name="Cloudflare Web",
            slug="cloudflare-web",
            category=ServiceProvider.Category.DNS,
        )
        internal_account_resource = self._resource(
            "ADB Cloudflare",
            InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
        )
        self.internal_account = ProviderAccount.objects.create(
            resource=internal_account_resource,
            provider=provider,
        )
        client_b_account_resource = self._resource(
            "Client B Cloudflare",
            InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
            client=self.client_b,
        )
        self.client_b_account = ProviderAccount.objects.create(
            resource=client_b_account_resource,
            provider=provider,
        )

    def _resource(
        self,
        name: str,
        resource_type: str,
        *,
        client: Client | None = None,
        environment: str = InfrastructureResource.Environment.NOT_APPLICABLE,
    ) -> InfrastructureResource:
        return InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT if client else OwnershipType.INTERNAL,
            client=client,
            name=name,
            resource_type=resource_type,
            environment=environment,
        )

    def test_website_requires_website_resource(self) -> None:
        resource = self._resource(
            "Wrong website identity", InfrastructureResource.ResourceType.DOMAIN
        )
        website = WebsiteProfile(resource=resource)

        with self.assertRaises(ValidationError):
            website.full_clean()

    def test_client_website_can_use_shared_internal_provider_accounts(self) -> None:
        resource = self._resource(
            "Client A Website",
            InfrastructureResource.ResourceType.WEBSITE,
            client=self.client_a,
        )
        website = WebsiteProfile(
            resource=resource,
            hosting_provider_account=self.internal_account,
            cdn_provider_account=self.internal_account,
            waf_provider_account=self.internal_account,
        )

        website.full_clean()

    def test_website_rejects_cross_client_provider_account(self) -> None:
        resource = self._resource(
            "Client A Website",
            InfrastructureResource.ResourceType.WEBSITE,
            client=self.client_a,
        )
        website = WebsiteProfile(
            resource=resource,
            cdn_provider_account=self.client_b_account,
        )

        with self.assertRaises(ValidationError) as error:
            website.full_clean()

        self.assertIn("cdn_provider_account", error.exception.message_dict)

    def test_domain_normalises_dns_name_and_validates_dates(self) -> None:
        resource = self._resource("Example domain", InfrastructureResource.ResourceType.DOMAIN)
        domain = DomainProfile(
            resource=resource,
            domain_name="Example.COM.",
            registered_on=timezone.localdate(),
            expires_on=timezone.localdate() - timedelta(days=1),
        )

        with self.assertRaises(ValidationError) as error:
            domain.full_clean()

        self.assertEqual(domain.domain_name, "example.com")
        self.assertIn("expires_on", error.exception.message_dict)

    def test_domain_rejects_cross_client_registrar(self) -> None:
        resource = self._resource(
            "Client A Domain",
            InfrastructureResource.ResourceType.DOMAIN,
            client=self.client_a,
        )
        domain = DomainProfile(
            resource=resource,
            domain_name="client-a.example",
            registrar_account=self.client_b_account,
        )

        with self.assertRaises(ValidationError) as error:
            domain.full_clean()

        self.assertIn("registrar_account", error.exception.message_dict)

    def test_dns_zone_enforces_domain_parent_ownership(self) -> None:
        domain_resource = self._resource(
            "Client B Domain",
            InfrastructureResource.ResourceType.DOMAIN,
            client=self.client_b,
        )
        domain = DomainProfile.objects.create(
            resource=domain_resource,
            domain_name="client-b.example",
        )
        zone_resource = self._resource(
            "Client A DNS Zone",
            InfrastructureResource.ResourceType.DNS_ZONE,
            client=self.client_a,
        )
        zone = DNSZone(
            resource=zone_resource,
            domain=domain,
            zone_name="client-b.example",
        )

        with self.assertRaises(ValidationError) as error:
            zone.full_clean()

        self.assertIn("domain", error.exception.message_dict)

    def test_mx_record_requires_priority(self) -> None:
        domain_resource = self._resource("Mail domain", InfrastructureResource.ResourceType.DOMAIN)
        domain = DomainProfile.objects.create(resource=domain_resource, domain_name="mail.example")
        zone_resource = self._resource("Mail DNS", InfrastructureResource.ResourceType.DNS_ZONE)
        zone = DNSZone.objects.create(
            resource=zone_resource,
            domain=domain,
            zone_name="mail.example",
        )
        record = DNSRecord(
            zone=zone,
            name="@",
            record_type=DNSRecord.RecordType.MX,
            value="mail.example",
        )

        with self.assertRaises(ValidationError) as error:
            record.full_clean()

        self.assertIn("priority", error.exception.message_dict)

    def test_tls_certificate_rejects_cross_client_provider(self) -> None:
        resource = self._resource(
            "Client A TLS",
            InfrastructureResource.ResourceType.TLS_CERTIFICATE,
            client=self.client_a,
        )
        certificate = TLSCertificate(
            resource=resource,
            provider_account=self.client_b_account,
        )

        with self.assertRaises(ValidationError) as error:
            certificate.full_clean()

        self.assertIn("provider_account", error.exception.message_dict)

    def test_tls_domain_link_rejects_cross_client_domain(self) -> None:
        certificate_resource = self._resource(
            "Client A TLS",
            InfrastructureResource.ResourceType.TLS_CERTIFICATE,
            client=self.client_a,
        )
        certificate = TLSCertificate.objects.create(resource=certificate_resource)
        domain_resource = self._resource(
            "Client B Domain",
            InfrastructureResource.ResourceType.DOMAIN,
            client=self.client_b,
        )
        domain = DomainProfile.objects.create(
            resource=domain_resource,
            domain_name="client-b-tls.example",
        )
        link = TLSCertificateDomain(certificate=certificate, domain=domain)

        with self.assertRaises(ValidationError) as error:
            link.full_clean()

        self.assertIn("domain", error.exception.message_dict)

    def test_client_endpoint_can_link_shared_internal_domain_and_application_environment(
        self,
    ) -> None:
        website_resource = self._resource(
            "Client A Portal",
            InfrastructureResource.ResourceType.WEBSITE,
            client=self.client_a,
        )
        website = WebsiteProfile.objects.create(resource=website_resource)
        endpoint_resource = self._resource(
            "Client A Portal Production URL",
            InfrastructureResource.ResourceType.WEBSITE_ENDPOINT,
            client=self.client_a,
            environment=InfrastructureResource.Environment.PRODUCTION,
        )
        domain_resource = self._resource(
            "ADB Shared Preview Domain",
            InfrastructureResource.ResourceType.DOMAIN,
        )
        domain = DomainProfile.objects.create(
            resource=domain_resource,
            domain_name="preview.adb.example",
        )
        application_resource = self._resource(
            "Client A Portal App",
            InfrastructureResource.ResourceType.APPLICATION,
            client=self.client_a,
        )
        application = ApplicationProfile.objects.create(resource=application_resource)
        environment_resource = self._resource(
            "Client A Portal Production",
            InfrastructureResource.ResourceType.APPLICATION_ENVIRONMENT,
            client=self.client_a,
            environment=InfrastructureResource.Environment.PRODUCTION,
        )
        environment = ApplicationEnvironment.objects.create(
            resource=environment_resource,
            application=application,
        )
        endpoint = WebsiteEndpoint(
            resource=endpoint_resource,
            website=website,
            application_environment=environment,
            domain=domain,
            url="https://client-a.preview.adb.example",
            is_primary=True,
        )

        endpoint.full_clean()

    def test_endpoint_rejects_website_owned_by_another_client(self) -> None:
        website_resource = self._resource(
            "Client B Website",
            InfrastructureResource.ResourceType.WEBSITE,
            client=self.client_b,
        )
        website = WebsiteProfile.objects.create(resource=website_resource)
        endpoint_resource = self._resource(
            "Client A Endpoint",
            InfrastructureResource.ResourceType.WEBSITE_ENDPOINT,
            client=self.client_a,
        )
        endpoint = WebsiteEndpoint(
            resource=endpoint_resource,
            website=website,
            url="https://client-a.example",
        )

        with self.assertRaises(ValidationError) as error:
            endpoint.full_clean()

        self.assertIn("website", error.exception.message_dict)

    def test_web_domain_specialists_do_not_add_secret_payload_fields(self) -> None:
        forbidden_fragments = ("password", "token", "secret", "private_key", "credential")
        for model in (
            WebsiteProfile,
            WebsiteEndpoint,
            DomainProfile,
            DNSZone,
            DNSRecord,
            TLSCertificate,
            TLSCertificateDomain,
        ):
            field_names = {field.name for field in model._meta.get_fields()}
            for forbidden in forbidden_fragments:
                self.assertNotIn(forbidden, field_names)
