from typing import cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
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
    WebsiteProfile,
)
from apps.infrastructure.ninja.web_domain_schemas import (
    DNSRecordCreateIn,
    DomainCreateIn,
    DomainOut,
    TLSCertificateDomainCreateIn,
    TLSCertificateOut,
    WebDomainSpecialistOptionsOut,
    WebsiteCreateIn,
    WebsiteEndpointCreateIn,
    WebsiteEndpointOut,
    WebsiteOut,
)
from apps.infrastructure.ninja.web_domain_views import (
    _tls_certificate_out,
    create_dns_record,
    create_domain,
    create_tls_certificate_domain,
    create_website,
    create_website_endpoint,
    delete_tls_certificate_domain,
    web_domain_options,
)
from authentication.models import User


class WebDomainSpecialistApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.client_a = Client.objects.create(
            name="Client A",
            company="Client A Ltd",
            email="client-a-web-api@example.com",
            status="active",
        )
        self.client_b = Client.objects.create(
            name="Client B",
            company="Client B Ltd",
            email="client-b-web-api@example.com",
            status="active",
        )
        provider = ServiceProvider.objects.create(
            name="Cloudflare Web API",
            slug="cloudflare-web-api",
            category=ServiceProvider.Category.DNS,
        )
        internal_provider_resource = self._resource(
            "ADB Cloudflare",
            InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
        )
        self.internal_provider = ProviderAccount.objects.create(
            resource=internal_provider_resource,
            provider=provider,
        )
        client_b_provider_resource = self._resource(
            "Client B Cloudflare",
            InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
            client=self.client_b,
        )
        self.client_b_provider = ProviderAccount.objects.create(
            resource=client_b_provider_resource,
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

    def _request(self, user: User) -> HttpRequest:
        request = self.factory.get("/api/admin/infrastructure/web-domain-options")
        request.user = user
        return request

    def _user(self, email: str, codenames: list[str]) -> User:
        user = User.objects.create_user(
            email=email,
            password="test-password",
            first_name="Web",
            last_name="Operator",
            is_staff=True,
        )
        permissions = Permission.objects.filter(
            content_type__app_label="infrastructure",
            codename__in=codenames,
        )
        user.user_permissions.add(*permissions)
        return user

    def _grant_client(self, user: User, client: Client) -> None:
        profile, _ = StaffAccessProfile.objects.get_or_create(user=user)
        ClientAccessGrant.objects.create(profile=profile, client=client)

    def test_collection_routes_dispatch_get_and_post(self) -> None:
        user = self._user(
            "web-routing@example.com",
            [
                "view_domain",
                "view_website",
                "add_infrastructureresource",
                "add_domainprofile",
                "add_websiteprofile",
            ],
        )
        self.client.force_login(user)
        for collection, fields, model in (
            ("domains", {"domain_name": "routing.example"}, DomainProfile),
            ("websites", {}, WebsiteProfile),
        ):
            with self.subTest(collection=collection):
                url = f"/api/admin/infrastructure/{collection}"
                self.assertEqual(self.client.get(url).status_code, 200)
                response = self.client.post(
                    url,
                    data={"name": "Routing test", **fields},
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 201, response.content)
                self.assertTrue(
                    model.objects.filter(resource_id=response.json()["resource_id"]).exists()
                )

    def test_collection_posts_enforce_permissions_and_client_scope(self) -> None:
        user = self._user("web-routing-denied@example.com", [])
        self.client.force_login(user)
        for collection, fields in (
            ("domains", {"domain_name": "denied.example"}),
            ("websites", {}),
        ):
            with self.subTest(collection=collection):
                response = self.client.post(
                    f"/api/admin/infrastructure/{collection}",
                    data={"name": "Denied", **fields},
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 403)
        user.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="infrastructure",
                codename__in=[
                    "add_infrastructureresource",
                    "add_domainprofile",
                    "add_websiteprofile",
                ],
            )
        )
        for collection, fields in (
            ("domains", {"domain_name": "out-of-scope.example"}),
            ("websites", {}),
        ):
            with self.subTest(collection=collection):
                response = self.client.post(
                    f"/api/admin/infrastructure/{collection}",
                    data={
                        "name": "Outside scope",
                        "ownership_type": "client",
                        "client_id": self.client_b.id,
                        **fields,
                    },
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 404)
        self.assertFalse(DomainProfile.objects.exists())
        self.assertFalse(WebsiteProfile.objects.exists())

    def test_options_only_return_accessible_current_resources(self) -> None:
        client_a_domain_resource = self._resource(
            "Client A Domain",
            InfrastructureResource.ResourceType.DOMAIN,
            client=self.client_a,
        )
        DomainProfile.objects.create(
            resource=client_a_domain_resource,
            domain_name="client-a.example",
        )
        client_b_domain_resource = self._resource(
            "Client B Domain",
            InfrastructureResource.ResourceType.DOMAIN,
            client=self.client_b,
        )
        DomainProfile.objects.create(
            resource=client_b_domain_resource,
            domain_name="client-b.example",
        )
        user = self._user("web-options@example.com", ["view_infrastructureresource"])
        self._grant_client(user, self.client_a)

        result = cast(WebDomainSpecialistOptionsOut, web_domain_options(self._request(user)))

        self.assertEqual([item.id for item in result.clients], [self.client_a.id])
        self.assertEqual(
            [item.resource_id for item in result.domains],
            [client_a_domain_resource.id],
        )
        self.assertIn(
            self.internal_provider.resource_id,
            {item.resource_id for item in result.provider_accounts},
        )
        self.assertNotIn(
            self.client_b_provider.resource_id,
            {item.resource_id for item in result.provider_accounts},
        )

    def test_create_client_website_with_shared_internal_provider_accounts(self) -> None:
        user = self._user(
            "website-create@example.com",
            ["add_infrastructureresource", "add_websiteprofile"],
        )
        self._grant_client(user, self.client_a)

        status, result = create_website(
            self._request(user),
            WebsiteCreateIn(
                ownership_type="client",
                client_id=self.client_a.id,
                name="Client A Website",
                website_type="web_app",
                hosting_provider_account_resource_id=self.internal_provider.resource_id,
                cdn_provider_account_resource_id=self.internal_provider.resource_id,
                waf_provider_account_resource_id=self.internal_provider.resource_id,
            ),
        )

        self.assertEqual(status, 201)
        website = cast(WebsiteOut, result)
        self.assertEqual(website.client_id, self.client_a.id)
        self.assertEqual(
            website.hosting_provider_account_resource_id,
            self.internal_provider.resource_id,
        )
        self.assertEqual(
            website.cdn_provider_account_resource_id, self.internal_provider.resource_id
        )
        self.assertEqual(
            website.waf_provider_account_resource_id, self.internal_provider.resource_id
        )

    def test_invalid_cross_client_website_does_not_leave_orphan_resource(self) -> None:
        user = self._user(
            "website-cross-client@example.com",
            ["add_infrastructureresource", "add_websiteprofile"],
        )
        self._grant_client(user, self.client_a)
        self._grant_client(user, self.client_b)
        before = InfrastructureResource.objects.count()

        status, payload = create_website(
            self._request(user),
            WebsiteCreateIn(
                ownership_type="client",
                client_id=self.client_a.id,
                name="Invalid Client A Website",
                website_type="web_app",
                cdn_provider_account_resource_id=self.client_b_provider.resource_id,
            ),
        )

        self.assertEqual(status, 400)
        self.assertEqual(cast(dict[str, object], payload)["code"], "invalid_infrastructure")
        self.assertEqual(InfrastructureResource.objects.count(), before)

    def test_create_endpoint_links_application_domain_and_tls_by_resource_identity(self) -> None:
        user = self._user(
            "endpoint-create@example.com",
            ["add_infrastructureresource", "add_websiteendpoint"],
        )
        self._grant_client(user, self.client_a)
        website_resource = self._resource(
            "Client A Website",
            InfrastructureResource.ResourceType.WEBSITE,
            client=self.client_a,
        )
        website = WebsiteProfile.objects.create(resource=website_resource)
        application_resource = self._resource(
            "Client A App",
            InfrastructureResource.ResourceType.APPLICATION,
            client=self.client_a,
        )
        application = ApplicationProfile.objects.create(resource=application_resource)
        environment_resource = self._resource(
            "Client A App Production",
            InfrastructureResource.ResourceType.APPLICATION_ENVIRONMENT,
            client=self.client_a,
            environment=InfrastructureResource.Environment.PRODUCTION,
        )
        environment = ApplicationEnvironment.objects.create(
            resource=environment_resource,
            application=application,
        )
        domain_resource = self._resource(
            "Client A Domain",
            InfrastructureResource.ResourceType.DOMAIN,
            client=self.client_a,
        )
        domain = DomainProfile.objects.create(
            resource=domain_resource,
            domain_name="client-a.example",
        )
        certificate_resource = self._resource(
            "Client A TLS",
            InfrastructureResource.ResourceType.TLS_CERTIFICATE,
            client=self.client_a,
        )
        certificate = TLSCertificate.objects.create(resource=certificate_resource)

        status, result = create_website_endpoint(
            self._request(user),
            WebsiteEndpointCreateIn(
                ownership_type="client",
                client_id=self.client_a.id,
                name="Client A Production URL",
                environment="production",
                website_resource_id=website.resource_id,
                application_environment_resource_id=environment.resource_id,
                domain_resource_id=domain.resource_id,
                tls_certificate_resource_id=certificate.resource_id,
                url="https://client-a.example",
                role="primary",
                is_primary=True,
            ),
        )

        self.assertEqual(status, 201)
        endpoint = cast(WebsiteEndpointOut, result)
        self.assertEqual(endpoint.website_resource_id, website.resource_id)
        self.assertEqual(endpoint.application_environment_resource_id, environment.resource_id)
        self.assertEqual(endpoint.domain_resource_id, domain.resource_id)
        self.assertEqual(endpoint.tls_certificate_resource_id, certificate.resource_id)

    def test_create_domain_normalises_name_through_validation(self) -> None:
        user = self._user(
            "domain-create@example.com",
            ["add_infrastructureresource", "add_domainprofile"],
        )

        status, result = create_domain(
            self._request(user),
            DomainCreateIn(
                name="ADB Example Domain",
                domain_name="Example.COM.",
                registrar_account_resource_id=self.internal_provider.resource_id,
            ),
        )

        self.assertEqual(status, 201)
        domain = cast(DomainOut, result)
        self.assertEqual(domain.domain_name, "example.com")
        self.assertEqual(domain.registrar_account_resource_id, self.internal_provider.resource_id)

    def test_dns_record_creation_requires_zone_and_record_view_capabilities(self) -> None:
        domain_resource = self._resource("ADB Domain", InfrastructureResource.ResourceType.DOMAIN)
        domain = DomainProfile.objects.create(resource=domain_resource, domain_name="adb.example")
        zone_resource = self._resource("ADB DNS Zone", InfrastructureResource.ResourceType.DNS_ZONE)
        zone = DNSZone.objects.create(
            resource=zone_resource,
            domain=domain,
            zone_name="adb.example",
        )
        user = self._user("dns-no-view@example.com", ["add_dnsrecord"])

        status, payload = create_dns_record(
            self._request(user),
            zone.resource_id,
            DNSRecordCreateIn(name="www", record_type="A", value="192.0.2.10"),
        )

        self.assertEqual(status, 403)
        self.assertEqual(cast(dict[str, object], payload)["code"], "forbidden")
        self.assertFalse(DNSRecord.objects.filter(zone=zone).exists())

    def test_invalid_mx_record_is_not_saved(self) -> None:
        domain_resource = self._resource("Mail Domain", InfrastructureResource.ResourceType.DOMAIN)
        domain = DomainProfile.objects.create(resource=domain_resource, domain_name="mail.example")
        zone_resource = self._resource(
            "Mail DNS Zone", InfrastructureResource.ResourceType.DNS_ZONE
        )
        zone = DNSZone.objects.create(
            resource=zone_resource,
            domain=domain,
            zone_name="mail.example",
        )
        user = self._user(
            "dns-invalid@example.com",
            [
                "view_infrastructureresource",
                "view_dnszone",
                "view_dnsrecord",
                "add_dnsrecord",
            ],
        )

        status, payload = create_dns_record(
            self._request(user),
            zone.resource_id,
            DNSRecordCreateIn(name="@", record_type="MX", value="mx.mail.example"),
        )

        self.assertEqual(status, 400)
        self.assertEqual(cast(dict[str, object], payload)["code"], "invalid_infrastructure")
        self.assertFalse(DNSRecord.objects.filter(zone=zone).exists())

    def test_tls_domain_link_rejects_cross_client_resources(self) -> None:
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
            domain_name="client-b.example",
        )
        user = self._user(
            "tls-cross-client@example.com",
            [
                "view_infrastructureresource",
                "view_tlscertificate",
                "view_domainprofile",
                "view_tlscertificatedomain",
                "add_tlscertificatedomain",
            ],
        )
        self._grant_client(user, self.client_a)
        self._grant_client(user, self.client_b)

        status, payload = create_tls_certificate_domain(
            self._request(user),
            certificate.resource_id,
            TLSCertificateDomainCreateIn(domain_resource_id=domain.resource_id),
        )

        self.assertEqual(status, 400)
        self.assertEqual(cast(dict[str, object], payload)["code"], "invalid_infrastructure")
        self.assertFalse(TLSCertificateDomain.objects.exists())

    def test_tls_domain_delete_hides_link_when_domain_falls_outside_scope(self) -> None:
        certificate_resource = self._resource(
            "ADB Shared TLS",
            InfrastructureResource.ResourceType.TLS_CERTIFICATE,
        )
        certificate = TLSCertificate.objects.create(resource=certificate_resource)
        domain_resource = self._resource(
            "Client B Domain",
            InfrastructureResource.ResourceType.DOMAIN,
            client=self.client_b,
        )
        domain = DomainProfile.objects.create(
            resource=domain_resource,
            domain_name="private-client-b.example",
        )
        link = TLSCertificateDomain.objects.create(certificate=certificate, domain=domain)
        user = self._user(
            "tls-domain-scope@example.com",
            [
                "view_infrastructureresource",
                "view_tlscertificate",
                "view_domainprofile",
                "view_tlscertificatedomain",
                "delete_tlscertificatedomain",
            ],
        )

        status, payload = delete_tls_certificate_domain(
            self._request(user),
            certificate.resource_id,
            link.id,
        )

        self.assertEqual(status, 404)
        self.assertEqual(cast(dict[str, object], payload)["code"], "not_found")
        self.assertTrue(TLSCertificateDomain.objects.filter(id=link.id).exists())

    def test_tls_output_does_not_expose_secret_material(self) -> None:
        certificate_resource = self._resource(
            "ADB Managed TLS",
            InfrastructureResource.ResourceType.TLS_CERTIFICATE,
        )
        certificate = TLSCertificate.objects.create(
            resource=certificate_resource,
            certificate_type="managed",
            issuer="Let's Encrypt",
            subject_common_name="adb.example",
        )
        user = self._user(
            "tls-output@example.com",
            ["view_infrastructureresource", "view_tlscertificate"],
        )

        result = cast(TLSCertificateOut, _tls_certificate_out(self._request(user), certificate))
        fields = set(result.model_dump())

        self.assertNotIn("private_key", fields)
        self.assertNotIn("password", fields)
        self.assertNotIn("token", fields)
        self.assertNotIn("secret", fields)
