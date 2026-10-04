from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import (
    ApplicationEnvironment,
    ApplicationProfile,
    ApplicationRepositoryLink,
    DatabaseInstance,
    DNSRecord,
    DNSZone,
    DomainProfile,
    InfrastructureResource,
    IPAddress,
    LogicalDatabase,
    Network,
    NetworkInterface,
    ProviderAccount,
    ServerProfile,
    ServiceProvider,
    SourceRepository,
    Subnet,
    TLSCertificate,
    TLSCertificateDomain,
    WebsiteEndpoint,
    WebsiteProfile,
)

DEMO_PREFIX = "[DEMO]"


class Command(BaseCommand):
    help = "Populate the extended infrastructure inventory with deterministic fake data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--reset", action="store_true")
        parser.add_argument("--scale", type=int, default=1)
        parser.add_argument("--force", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "seed_infrastructure_development is disabled when DEBUG=False. "
                "Use --force only in a disposable environment."
            )

        scale = max(1, options["scale"])
        with transaction.atomic():
            if options["reset"]:
                self._reset()
            self._seed_structured_compute()
            self._seed_structured_data_applications()
            self._seed_structured_web_domains()
            self._seed_additional_resources(scale)

        self.stdout.write(
            self.style.SUCCESS(f"Extended infrastructure development data ready (scale={scale}).")
        )

    def _reset(self) -> None:
        InfrastructureResource.objects.filter(
            name__startswith=DEMO_PREFIX,
            resource_type=InfrastructureResource.ResourceType.SYSTEM_SERVICE,
        ).delete()
        InfrastructureResource.objects.filter(
            name__startswith=DEMO_PREFIX,
            resource_type__in=[
                InfrastructureResource.ResourceType.LICENCE,
                InfrastructureResource.ResourceType.API,
                InfrastructureResource.ResourceType.BOT,
                InfrastructureResource.ResourceType.MOBILE_APP,
                InfrastructureResource.ResourceType.EMAIL_SYSTEM,
                InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
                InfrastructureResource.ResourceType.SERVER,
                InfrastructureResource.ResourceType.NETWORK,
                InfrastructureResource.ResourceType.SUBNET,
                InfrastructureResource.ResourceType.DATABASE_INSTANCE,
                InfrastructureResource.ResourceType.LOGICAL_DATABASE,
                InfrastructureResource.ResourceType.APPLICATION,
                InfrastructureResource.ResourceType.APPLICATION_ENVIRONMENT,
                InfrastructureResource.ResourceType.SOURCE_REPOSITORY,
                InfrastructureResource.ResourceType.WEBSITE,
                InfrastructureResource.ResourceType.WEBSITE_ENDPOINT,
                InfrastructureResource.ResourceType.DOMAIN,
                InfrastructureResource.ResourceType.DNS_ZONE,
                InfrastructureResource.ResourceType.TLS_CERTIFICATE,
            ],
        ).delete()

    def _resource(
        self,
        *,
        name: str,
        resource_type: str,
        ownership_type: str = OwnershipType.INTERNAL,
        client: Client | None = None,
        environment: str = InfrastructureResource.Environment.PRODUCTION,
        criticality: str = InfrastructureResource.Criticality.NORMAL,
        description: str = "",
    ) -> InfrastructureResource:
        resource, _ = InfrastructureResource.objects.update_or_create(
            name=name,
            resource_type=resource_type,
            defaults={
                "ownership_type": ownership_type,
                "client": client,
                "lifecycle_status": InfrastructureResource.LifecycleStatus.ACTIVE,
                "environment": environment,
                "criticality": criticality,
                "description": description,
            },
        )
        resource.full_clean()
        resource.save()
        return resource

    def _seed_structured_compute(self) -> None:
        provider, _ = ServiceProvider.objects.update_or_create(
            slug="digitalocean",
            defaults={
                "name": "DigitalOcean",
                "category": ServiceProvider.Category.CLOUD,
                "website_url": "https://www.digitalocean.com",
                "is_active": True,
            },
        )
        provider_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB DigitalOcean",
            resource_type=InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
            environment=InfrastructureResource.Environment.SHARED,
            description="Shared development provider account for structured infrastructure demos.",
        )
        provider_account, _ = ProviderAccount.objects.update_or_create(
            resource=provider_resource,
            defaults={
                "provider": provider,
                "account_identifier": "demo-adb-do",
                "default_region": "lon1",
            },
        )
        provider_account.full_clean()
        provider_account.save()

        network_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB Production VPC",
            resource_type=InfrastructureResource.ResourceType.NETWORK,
            description="Development VPC demonstrating native structured networking.",
        )
        network, _ = Network.objects.update_or_create(
            resource=network_resource,
            defaults={
                "network_type": Network.NetworkType.VPC,
                "provider_account": provider_account,
                "provider_network_id": "demo-vpc-lon1",
                "cidr": "10.42.0.0/16",
                "gateway": "10.42.0.1",
                "region": "lon1",
                "dns_servers": ["1.1.1.1", "1.0.0.1"],
            },
        )
        network.full_clean()
        network.save()

        subnet_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB Web Subnet",
            resource_type=InfrastructureResource.ResourceType.SUBNET,
            description="Development subnet for web workloads.",
        )
        subnet, _ = Subnet.objects.update_or_create(
            resource=subnet_resource,
            defaults={
                "network": network,
                "cidr": "10.42.10.0/24",
                "gateway": "10.42.10.1",
                "availability_zone": "lon1",
                "purpose": "Public-facing web workloads",
            },
        )
        subnet.full_clean()
        subnet.save()

        server_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB LON Web 01",
            resource_type=InfrastructureResource.ResourceType.SERVER,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Development structured server with native network and IP data.",
        )
        server, _ = ServerProfile.objects.update_or_create(
            resource=server_resource,
            defaults={
                "hostname": "demo-adb-lon-ws01",
                "fqdn": "demo-adb-lon-ws01.internal.example.test",
                "purpose": "Primary development web workload",
                "role": "Web server",
                "compute_type": ServerProfile.ComputeType.CLOUD_VM,
                "architecture": "x86_64",
                "cpu_model": "AMD EPYC",
                "cpu_cores": 4,
                "ram_mb": 8192,
                "root_disk_gb": 160,
                "os_family": ServerProfile.OSFamily.LINUX,
                "distribution": "Ubuntu",
                "os_version": "24.04",
                "provider_account": provider_account,
                "provider_resource_id": "demo-droplet-1001",
                "region": "lon1",
                "ssh_port": 22,
                "timezone": "Europe/London",
                "automatic_updates": True,
                "patch_window": "Sunday 03:00 Europe/London",
            },
        )
        server.full_clean()
        server.save()
        interface, _ = NetworkInterface.objects.update_or_create(
            server=server,
            name="eth0",
            defaults={
                "network": network,
                "subnet": subnet,
                "mac_address": "02:00:00:00:10:01",
                "mtu": 1500,
                "description": "Primary application interface",
            },
        )
        interface.full_clean()
        interface.save()
        internal_ip, _ = IPAddress.objects.update_or_create(
            resource=server_resource,
            address="10.42.10.10",
            defaults={
                "interface": interface,
                "scope": IPAddress.Scope.PRIVATE,
                "is_primary": True,
                "ptr_record": "demo-adb-lon-ws01.internal.example.test",
            },
        )
        internal_ip.full_clean()
        internal_ip.save()
        public_ip, _ = IPAddress.objects.update_or_create(
            resource=server_resource,
            address="203.0.113.10",
            defaults={
                "scope": IPAddress.Scope.PUBLIC,
                "is_primary": False,
                "description": "Reserved documentation address used for development data.",
            },
        )
        public_ip.full_clean()
        public_ip.save()

        client = Client.objects.filter(status="active").order_by("id").first()
        if client is None:
            return
        client_name = client.company or client.name
        client_server_resource = self._resource(
            name=f"{DEMO_PREFIX} {client_name} Web 01",
            resource_type=InfrastructureResource.ResourceType.SERVER,
            ownership_type=OwnershipType.CLIENT,
            client=client,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Client-owned development server using shared ADB infrastructure.",
        )
        client_server, _ = ServerProfile.objects.update_or_create(
            resource=client_server_resource,
            defaults={
                "hostname": "demo-client-web01",
                "purpose": "Client production web workload",
                "role": "Web server",
                "compute_type": ServerProfile.ComputeType.CLOUD_VM,
                "cpu_cores": 2,
                "ram_mb": 4096,
                "root_disk_gb": 80,
                "os_family": ServerProfile.OSFamily.LINUX,
                "distribution": "Ubuntu",
                "os_version": "24.04",
                "provider_account": provider_account,
                "provider_resource_id": "demo-droplet-client-01",
                "region": "lon1",
                "ssh_port": 22,
            },
        )
        client_server.full_clean()
        client_server.save()

    def _seed_structured_data_applications(self) -> None:
        shared_cloud_account = ProviderAccount.objects.select_related("resource").get(
            resource__name=f"{DEMO_PREFIX} ADB DigitalOcean"
        )
        internal_server = ServerProfile.objects.select_related("resource").get(
            resource__name=f"{DEMO_PREFIX} ADB LON Web 01"
        )

        github_provider, _ = ServiceProvider.objects.update_or_create(
            slug="github",
            defaults={
                "name": "GitHub",
                "category": ServiceProvider.Category.SOURCE_CONTROL,
                "website_url": "https://github.com",
                "is_active": True,
            },
        )
        github_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB GitHub",
            resource_type=InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
            environment=InfrastructureResource.Environment.SHARED,
            description="Shared source-control provider account used by development applications.",
        )
        github_account, _ = ProviderAccount.objects.update_or_create(
            resource=github_resource,
            defaults={
                "provider": github_provider,
                "account_identifier": "adb-software-solutions-demo",
                "portal_url": "https://github.com/adb-software-solutions",
            },
        )
        github_account.full_clean()
        github_account.save()

        database_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB PostgreSQL",
            resource_type=InfrastructureResource.ResourceType.DATABASE_INSTANCE,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Self-hosted PostgreSQL service for the structured application demo.",
        )
        database_instance, _ = DatabaseInstance.objects.update_or_create(
            resource=database_resource,
            defaults={
                "engine": DatabaseInstance.Engine.POSTGRESQL,
                "engine_version": "18",
                "hosting_type": DatabaseInstance.HostingType.SELF_HOSTED,
                "server": internal_server,
                "provider_account": shared_cloud_account,
                "endpoint": "10.42.10.10",
                "port": 5432,
                "region": "lon1",
                "tls_mode": DatabaseInstance.TLSMode.REQUIRED,
                "high_availability": False,
                "replica_count": 0,
                "backup_enabled": True,
                "maintenance_window": "Sunday 02:00 Europe/London",
            },
        )
        database_instance.full_clean()
        database_instance.save()

        logical_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB Platform Database",
            resource_type=InfrastructureResource.ResourceType.LOGICAL_DATABASE,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Primary logical database for the ADB Platform demo application.",
        )
        logical_database, _ = LogicalDatabase.objects.update_or_create(
            resource=logical_resource,
            defaults={
                "instance": database_instance,
                "database_name": "adb_platform_demo",
                "purpose": "Application data",
                "default_schema": "public",
                "charset": "UTF8",
            },
        )
        logical_database.full_clean()
        logical_database.save()

        application_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB Platform",
            resource_type=InfrastructureResource.ResourceType.APPLICATION,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Logical ADB Platform application used by structured infrastructure demos.",
        )
        application, _ = ApplicationProfile.objects.update_or_create(
            resource=application_resource,
            defaults={
                "application_type": ApplicationProfile.ApplicationType.SAAS,
                "owner_team": "ADB Software Solutions",
                "primary_language": "Python / TypeScript",
                "framework": "Django / Next.js",
            },
        )
        application.full_clean()
        application.save()

        environment_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB Platform Production",
            resource_type=InfrastructureResource.ResourceType.APPLICATION_ENVIRONMENT,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Production-like deployment context for the ADB Platform demo.",
        )
        application_environment, _ = ApplicationEnvironment.objects.update_or_create(
            resource=environment_resource,
            defaults={
                "application": application,
                "deployment_type": ApplicationEnvironment.DeploymentType.SERVER,
                "server": internal_server,
                "provider_account": shared_cloud_account,
                "provider_resource_id": "demo-adb-platform-production",
                "runtime": "Python / Node.js",
                "runtime_version": "3.12 / 22",
                "release_version": "demo-main",
                "region": "lon1",
                "branch_or_ref": "main",
                "automatic_deployments": True,
            },
        )
        application_environment.full_clean()
        application_environment.save()

        repository_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB Platform Repository",
            resource_type=InfrastructureResource.ResourceType.SOURCE_REPOSITORY,
            environment=InfrastructureResource.Environment.SHARED,
            description="Primary source repository for the structured ADB Platform demo.",
        )
        repository, _ = SourceRepository.objects.update_or_create(
            resource=repository_resource,
            defaults={
                "provider_account": github_account,
                "web_url": "https://github.com/adb-software-solutions/adb-web-platform",
                "clone_url": "git@github.com:adb-software-solutions/adb-web-platform.git",
                "provider_repository_id": "demo-adb-web-platform",
                "owner_name": "adb-software-solutions",
                "repository_name": "adb-web-platform",
                "default_branch": "main",
                "visibility": SourceRepository.Visibility.PRIVATE,
                "is_fork": False,
            },
        )
        repository.full_clean()
        repository.save()
        repository_link, _ = ApplicationRepositoryLink.objects.update_or_create(
            application=application,
            repository=repository,
            role=ApplicationRepositoryLink.Role.PRIMARY,
            path="",
            defaults={"notes": "Primary monorepo for the development application."},
        )
        repository_link.full_clean()
        repository_link.save()

        client = Client.objects.filter(status="active").order_by("id").first()
        if client is None:
            return
        client_name = client.company or client.name
        client_server = ServerProfile.objects.select_related("resource").get(
            resource__name=f"{DEMO_PREFIX} {client_name} Web 01"
        )
        client_database_resource = self._resource(
            name=f"{DEMO_PREFIX} {client_name} PostgreSQL",
            resource_type=InfrastructureResource.ResourceType.DATABASE_INSTANCE,
            ownership_type=OwnershipType.CLIENT,
            client=client,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Client-owned PostgreSQL service using the Client demo server.",
        )
        client_database, _ = DatabaseInstance.objects.update_or_create(
            resource=client_database_resource,
            defaults={
                "engine": DatabaseInstance.Engine.POSTGRESQL,
                "engine_version": "18",
                "hosting_type": DatabaseInstance.HostingType.SELF_HOSTED,
                "server": client_server,
                "provider_account": shared_cloud_account,
                "endpoint": "demo-client-web01",
                "port": 5432,
                "region": "lon1",
                "tls_mode": DatabaseInstance.TLSMode.REQUIRED,
                "high_availability": False,
                "backup_enabled": True,
                "maintenance_window": "Saturday 02:00 Europe/London",
            },
        )
        client_database.full_clean()
        client_database.save()

        client_logical_resource = self._resource(
            name=f"{DEMO_PREFIX} {client_name} Application Database",
            resource_type=InfrastructureResource.ResourceType.LOGICAL_DATABASE,
            ownership_type=OwnershipType.CLIENT,
            client=client,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Client-owned logical application database.",
        )
        client_logical, _ = LogicalDatabase.objects.update_or_create(
            resource=client_logical_resource,
            defaults={
                "instance": client_database,
                "database_name": "client_application_demo",
                "purpose": "Client application data",
                "default_schema": "public",
                "charset": "UTF8",
            },
        )
        client_logical.full_clean()
        client_logical.save()

        client_application_resource = self._resource(
            name=f"{DEMO_PREFIX} {client_name} Application",
            resource_type=InfrastructureResource.ResourceType.APPLICATION,
            ownership_type=OwnershipType.CLIENT,
            client=client,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Client-owned logical application in the structured infrastructure graph.",
        )
        client_application, _ = ApplicationProfile.objects.update_or_create(
            resource=client_application_resource,
            defaults={
                "application_type": ApplicationProfile.ApplicationType.WEB_APP,
                "owner_team": "ADB Software Solutions",
                "primary_language": "Python / TypeScript",
                "framework": "Django / Next.js",
            },
        )
        client_application.full_clean()
        client_application.save()

        client_environment_resource = self._resource(
            name=f"{DEMO_PREFIX} {client_name} Production",
            resource_type=InfrastructureResource.ResourceType.APPLICATION_ENVIRONMENT,
            ownership_type=OwnershipType.CLIENT,
            client=client,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Client-owned production deployment using the Client demo server.",
        )
        client_environment, _ = ApplicationEnvironment.objects.update_or_create(
            resource=client_environment_resource,
            defaults={
                "application": client_application,
                "deployment_type": ApplicationEnvironment.DeploymentType.SERVER,
                "server": client_server,
                "provider_account": shared_cloud_account,
                "provider_resource_id": "demo-client-production",
                "runtime": "Python / Node.js",
                "runtime_version": "3.12 / 22",
                "release_version": "demo-production",
                "region": "lon1",
                "branch_or_ref": "main",
                "automatic_deployments": True,
            },
        )
        client_environment.full_clean()
        client_environment.save()

        client_repository_resource = self._resource(
            name=f"{DEMO_PREFIX} {client_name} Repository",
            resource_type=InfrastructureResource.ResourceType.SOURCE_REPOSITORY,
            ownership_type=OwnershipType.CLIENT,
            client=client,
            environment=InfrastructureResource.Environment.SHARED,
            description="Client-owned source repository managed through the shared ADB GitHub account.",
        )
        client_repository, _ = SourceRepository.objects.update_or_create(
            resource=client_repository_resource,
            defaults={
                "provider_account": github_account,
                "web_url": "https://github.com/example/client-application-demo",
                "clone_url": "git@github.com:example/client-application-demo.git",
                "provider_repository_id": "demo-client-application",
                "owner_name": "example",
                "repository_name": "client-application-demo",
                "default_branch": "main",
                "visibility": SourceRepository.Visibility.PRIVATE,
                "is_fork": False,
            },
        )
        client_repository.full_clean()
        client_repository.save()
        client_repository_link, _ = ApplicationRepositoryLink.objects.update_or_create(
            application=client_application,
            repository=client_repository,
            role=ApplicationRepositoryLink.Role.PRIMARY,
            path="",
            defaults={"notes": "Primary Client application repository."},
        )
        client_repository_link.full_clean()
        client_repository_link.save()

    def _seed_structured_web_domains(self) -> None:
        shared_cloud_account = ProviderAccount.objects.select_related("resource").get(
            resource__name=f"{DEMO_PREFIX} ADB DigitalOcean"
        )
        internal_environment = ApplicationEnvironment.objects.select_related(
            "resource", "application__resource"
        ).get(resource__name=f"{DEMO_PREFIX} ADB Platform Production")

        cloudflare_provider, _ = ServiceProvider.objects.update_or_create(
            slug="cloudflare",
            defaults={
                "name": "Cloudflare",
                "category": ServiceProvider.Category.DNS,
                "website_url": "https://www.cloudflare.com",
                "is_active": True,
            },
        )
        cloudflare_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB Cloudflare",
            resource_type=InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
            environment=InfrastructureResource.Environment.SHARED,
            description="Shared DNS/CDN/WAF provider account for development web infrastructure.",
        )
        cloudflare_account, _ = ProviderAccount.objects.update_or_create(
            resource=cloudflare_resource,
            defaults={
                "provider": cloudflare_provider,
                "account_identifier": "demo-adb-cloudflare",
                "portal_url": "https://dash.cloudflare.com",
            },
        )
        cloudflare_account.full_clean()
        cloudflare_account.save()

        domain_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB Platform Domain",
            resource_type=InfrastructureResource.ResourceType.DOMAIN,
            environment=InfrastructureResource.Environment.SHARED,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Reserved example Domain for structured web infrastructure development.",
        )
        domain, _ = DomainProfile.objects.update_or_create(
            resource=domain_resource,
            defaults={
                "domain_name": "adb-platform.example.test",
                "registrar_account": cloudflare_account,
                "provider_domain_id": "demo-domain-adb-platform",
                "status": DomainProfile.Status.ACTIVE,
                "registered_on": timezone.localdate() - timedelta(days=500),
                "expires_on": timezone.localdate() + timedelta(days=140),
                "auto_renew": True,
                "transfer_lock_enabled": True,
                "privacy_enabled": True,
            },
        )
        domain.full_clean()
        domain.save()

        zone_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB Platform DNS",
            resource_type=InfrastructureResource.ResourceType.DNS_ZONE,
            environment=InfrastructureResource.Environment.SHARED,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Authoritative development DNS zone backed by the shared Cloudflare account.",
        )
        zone, _ = DNSZone.objects.update_or_create(
            resource=zone_resource,
            defaults={
                "domain": domain,
                "provider_account": cloudflare_account,
                "zone_name": domain.domain_name,
                "provider_zone_id": "demo-zone-adb-platform",
                "dnssec_enabled": True,
                "is_primary": True,
            },
        )
        zone.full_clean()
        zone.save()
        for record_name, record_type, value, proxied in (
            ("@", DNSRecord.RecordType.A, "203.0.113.10", True),
            ("www", DNSRecord.RecordType.CNAME, "adb-platform.example.test", True),
            ("api", DNSRecord.RecordType.CNAME, "adb-platform.example.test", True),
        ):
            record, _ = DNSRecord.objects.update_or_create(
                zone=zone,
                name=record_name,
                record_type=record_type,
                defaults={
                    "value": value,
                    "ttl": 300,
                    "proxied": proxied,
                    "provider_record_id": f"demo-{record_name}-{record_type.lower()}",
                },
            )
            record.full_clean()
            record.save()

        certificate_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB Platform TLS",
            resource_type=InfrastructureResource.ResourceType.TLS_CERTIFICATE,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Non-secret ACME certificate metadata for development web infrastructure.",
        )
        certificate, _ = TLSCertificate.objects.update_or_create(
            resource=certificate_resource,
            defaults={
                "provider_account": cloudflare_account,
                "certificate_type": TLSCertificate.CertificateType.ACME,
                "issuer": "Let's Encrypt (development metadata)",
                "subject_common_name": domain.domain_name,
                "provider_certificate_id": "demo-cert-adb-platform",
                "issued_at": timezone.now() - timedelta(days=20),
                "expires_at": timezone.now() + timedelta(days=70),
                "auto_renew": True,
            },
        )
        certificate.full_clean()
        certificate.save()
        coverage, _ = TLSCertificateDomain.objects.update_or_create(
            certificate=certificate,
            domain=domain,
            defaults={"is_primary": True},
        )
        coverage.full_clean()
        coverage.save()

        website_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB Platform Website",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Structured Website demonstrating application, Domain, DNS and TLS context.",
        )
        website, _ = WebsiteProfile.objects.update_or_create(
            resource=website_resource,
            defaults={
                "website_type": WebsiteProfile.WebsiteType.WEB_APP,
                "admin_url": "https://adb-platform.example.test/admin",
                "hosting_provider_account": shared_cloud_account,
                "cdn_provider_account": cloudflare_account,
                "waf_provider_account": cloudflare_account,
            },
        )
        website.full_clean()
        website.save()
        endpoint_resource = self._resource(
            name=f"{DEMO_PREFIX} ADB Platform Website Production",
            resource_type=InfrastructureResource.ResourceType.WEBSITE_ENDPOINT,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Primary development endpoint for the structured ADB Platform Website.",
        )
        endpoint, _ = WebsiteEndpoint.objects.update_or_create(
            resource=endpoint_resource,
            defaults={
                "website": website,
                "application_environment": internal_environment,
                "domain": domain,
                "tls_certificate": certificate,
                "url": "https://adb-platform.example.test",
                "role": WebsiteEndpoint.Role.PRIMARY,
                "is_primary": True,
            },
        )
        endpoint.full_clean()
        endpoint.save()

        client = Client.objects.filter(status="active").order_by("id").first()
        if client is None:
            return
        client_name = client.company or client.name
        client_environment = ApplicationEnvironment.objects.select_related(
            "resource", "application__resource"
        ).get(resource__name=f"{DEMO_PREFIX} {client_name} Production")
        client_domain_resource = self._resource(
            name=f"{DEMO_PREFIX} {client_name} Domain",
            resource_type=InfrastructureResource.ResourceType.DOMAIN,
            ownership_type=OwnershipType.CLIENT,
            client=client,
            environment=InfrastructureResource.Environment.SHARED,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Client-owned example Domain managed through shared ADB provider context.",
        )
        client_domain, _ = DomainProfile.objects.update_or_create(
            resource=client_domain_resource,
            defaults={
                "domain_name": "client-application.example.test",
                "registrar_account": cloudflare_account,
                "provider_domain_id": "demo-domain-client-application",
                "status": DomainProfile.Status.ACTIVE,
                "registered_on": timezone.localdate() - timedelta(days=300),
                "expires_on": timezone.localdate() + timedelta(days=55),
                "auto_renew": True,
                "transfer_lock_enabled": True,
                "privacy_enabled": True,
            },
        )
        client_domain.full_clean()
        client_domain.save()
        client_zone_resource = self._resource(
            name=f"{DEMO_PREFIX} {client_name} DNS",
            resource_type=InfrastructureResource.ResourceType.DNS_ZONE,
            ownership_type=OwnershipType.CLIENT,
            client=client,
            environment=InfrastructureResource.Environment.SHARED,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Client-owned DNS zone using the shared ADB Cloudflare Provider Account.",
        )
        client_zone, _ = DNSZone.objects.update_or_create(
            resource=client_zone_resource,
            defaults={
                "domain": client_domain,
                "provider_account": cloudflare_account,
                "zone_name": client_domain.domain_name,
                "provider_zone_id": "demo-zone-client-application",
                "dnssec_enabled": True,
                "is_primary": True,
            },
        )
        client_zone.full_clean()
        client_zone.save()
        client_record, _ = DNSRecord.objects.update_or_create(
            zone=client_zone,
            name="@",
            record_type=DNSRecord.RecordType.A,
            defaults={
                "value": "198.51.100.20",
                "ttl": 300,
                "proxied": True,
                "provider_record_id": "demo-client-root-a",
            },
        )
        client_record.full_clean()
        client_record.save()

        client_certificate_resource = self._resource(
            name=f"{DEMO_PREFIX} {client_name} TLS",
            resource_type=InfrastructureResource.ResourceType.TLS_CERTIFICATE,
            ownership_type=OwnershipType.CLIENT,
            client=client,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Client-owned non-secret TLS metadata with an intentionally nearer expiry.",
        )
        client_certificate, _ = TLSCertificate.objects.update_or_create(
            resource=client_certificate_resource,
            defaults={
                "provider_account": cloudflare_account,
                "certificate_type": TLSCertificate.CertificateType.MANAGED,
                "issuer": "Cloudflare (development metadata)",
                "subject_common_name": client_domain.domain_name,
                "provider_certificate_id": "demo-cert-client-application",
                "issued_at": timezone.now() - timedelta(days=35),
                "expires_at": timezone.now() + timedelta(days=25),
                "auto_renew": True,
            },
        )
        client_certificate.full_clean()
        client_certificate.save()
        client_coverage, _ = TLSCertificateDomain.objects.update_or_create(
            certificate=client_certificate,
            domain=client_domain,
            defaults={"is_primary": True},
        )
        client_coverage.full_clean()
        client_coverage.save()

        client_website_resource = self._resource(
            name=f"{DEMO_PREFIX} {client_name} Website",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
            ownership_type=OwnershipType.CLIENT,
            client=client,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Client-owned Website served through shared ADB hosting/CDN provider context.",
        )
        client_website, _ = WebsiteProfile.objects.update_or_create(
            resource=client_website_resource,
            defaults={
                "website_type": WebsiteProfile.WebsiteType.WEB_APP,
                "admin_url": "https://client-application.example.test/admin",
                "hosting_provider_account": shared_cloud_account,
                "cdn_provider_account": cloudflare_account,
                "waf_provider_account": cloudflare_account,
            },
        )
        client_website.full_clean()
        client_website.save()
        client_endpoint_resource = self._resource(
            name=f"{DEMO_PREFIX} {client_name} Website Production",
            resource_type=InfrastructureResource.ResourceType.WEBSITE_ENDPOINT,
            ownership_type=OwnershipType.CLIENT,
            client=client,
            criticality=InfrastructureResource.Criticality.HIGH,
            description="Primary Client Website endpoint linked to its application and web infrastructure.",
        )
        client_endpoint, _ = WebsiteEndpoint.objects.update_or_create(
            resource=client_endpoint_resource,
            defaults={
                "website": client_website,
                "application_environment": client_environment,
                "domain": client_domain,
                "tls_certificate": client_certificate,
                "url": "https://client-application.example.test",
                "role": WebsiteEndpoint.Role.PRIMARY,
                "is_primary": True,
            },
        )
        client_endpoint.full_clean()
        client_endpoint.save()

    def _seed_additional_resources(self, scale: int) -> None:
        for resource_type in ("mobile_app", "api", "bot", "email_system", "licence"):
            for index in range(1, scale * 3 + 1):
                InfrastructureResource.objects.update_or_create(
                    name=f"{DEMO_PREFIX} {resource_type.replace('_', ' ').title()} {index:02d}",
                    defaults={
                        "ownership_type": OwnershipType.INTERNAL,
                        "resource_type": resource_type,
                        "description": "Generated current development resource.",
                    },
                )
