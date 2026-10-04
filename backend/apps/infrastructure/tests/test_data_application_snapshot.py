from typing import cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.data_application_edit import data_application_edit_values
from apps.infrastructure.data_application_snapshot import data_application_resource_snapshot
from apps.infrastructure.models import (
    ApplicationEnvironment,
    ApplicationProfile,
    ApplicationRepositoryLink,
    DatabaseInstance,
    InfrastructureResource,
    LogicalDatabase,
    ProviderAccount,
    ServerProfile,
    ServiceProvider,
    SourceRepository,
)
from apps.infrastructure.ninja.specialist_edit_views import (
    InfrastructureSpecialistEditOut,
    get_infrastructure_specialist_edit_details,
)
from authentication.models import User


class DataApplicationSnapshotTests(TestCase):
    def setUp(self) -> None:
        provider = ServiceProvider.objects.create(
            name="GitHub Snapshot",
            slug="github-snapshot",
            category=ServiceProvider.Category.SAAS,
        )
        provider_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB GitHub",
            resource_type=InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
        )
        self.provider_account = ProviderAccount.objects.create(
            resource=provider_resource,
            provider=provider,
        )
        server_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB App Server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        self.server = ServerProfile.objects.create(
            resource=server_resource,
            hostname="adb-app01",
        )

    def test_database_snapshot_contains_operational_metadata_only(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB PostgreSQL",
            resource_type=InfrastructureResource.ResourceType.DATABASE_INSTANCE,
        )
        DatabaseInstance.objects.create(
            resource=resource,
            engine=DatabaseInstance.Engine.POSTGRESQL,
            engine_version="18",
            hosting_type=DatabaseInstance.HostingType.SELF_HOSTED,
            server=self.server,
            endpoint="10.42.10.20",
            port=5432,
            tls_mode=DatabaseInstance.TLSMode.REQUIRED,
        )

        fields = data_application_resource_snapshot(resource)
        by_key = {field.key: field.value for field in fields}

        self.assertEqual(by_key["engine"], "PostgreSQL")
        self.assertEqual(by_key["server"], "ADB App Server")
        self.assertEqual(by_key["endpoint"], "10.42.10.20")
        self.assertNotIn("password", by_key)
        self.assertNotIn("token", by_key)
        self.assertNotIn("secret", by_key)

    def test_application_snapshot_includes_explicit_repository_context(self) -> None:
        application_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB Platform",
            resource_type=InfrastructureResource.ResourceType.APPLICATION,
        )
        application = ApplicationProfile.objects.create(
            resource=application_resource,
            application_type=ApplicationProfile.ApplicationType.SAAS,
            primary_language="Python",
            framework="Django",
        )
        repository_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB Platform Repo",
            resource_type=InfrastructureResource.ResourceType.SOURCE_REPOSITORY,
        )
        repository = SourceRepository.objects.create(
            resource=repository_resource,
            provider_account=self.provider_account,
            repository_name="adb-web-platform",
        )
        ApplicationRepositoryLink.objects.create(
            application=application,
            repository=repository,
            role=ApplicationRepositoryLink.Role.PRIMARY,
        )

        fields = data_application_resource_snapshot(application_resource)
        by_key = {field.key: field.value for field in fields}

        self.assertEqual(by_key["application_type"], "SaaS")
        self.assertIn("ADB Platform Repo", by_key["repositories"])

    def test_exact_edit_values_keep_relation_ids_without_secrets(self) -> None:
        application_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB Platform",
            resource_type=InfrastructureResource.ResourceType.APPLICATION,
        )
        application = ApplicationProfile.objects.create(resource=application_resource)
        environment_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB Platform Production",
            resource_type=InfrastructureResource.ResourceType.APPLICATION_ENVIRONMENT,
            environment=InfrastructureResource.Environment.PRODUCTION,
        )
        ApplicationEnvironment.objects.create(
            resource=environment_resource,
            application=application,
            server=self.server,
            provider_account=self.provider_account,
            runtime="python",
            runtime_version="3.12",
        )

        values = data_application_edit_values(environment_resource)

        self.assertIsNotNone(values)
        assert values is not None
        self.assertEqual(values["application_resource_id"], application_resource.id)
        self.assertEqual(values["server_resource_id"], self.server.resource_id)
        self.assertEqual(
            values["provider_account_resource_id"],
            self.provider_account.resource_id,
        )
        self.assertNotIn("password", values)
        self.assertNotIn("token", values)
        self.assertNotIn("private_key", values)


class DataApplicationSharedEditEndpointTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.client_record = Client.objects.create(
            name="Client A",
            company="Client A Ltd",
            email="client-a-edit-data@example.com",
            status="active",
        )

    def _user(self) -> User:
        user = User.objects.create_user(
            email="data-edit@example.com",
            password="test-password",
            first_name="Data",
            last_name="Editor",
            is_staff=True,
        )
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="infrastructure",
                codename="view_infrastructureresource",
            )
        )
        return user

    def _request(self, user: User) -> HttpRequest:
        request = self.factory.get("/api/admin/infrastructure/resources/1/specialist-edit")
        request.user = user
        return request

    def test_shared_edit_endpoint_supports_logical_database(self) -> None:
        instance_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB PostgreSQL",
            resource_type=InfrastructureResource.ResourceType.DATABASE_INSTANCE,
        )
        instance = DatabaseInstance.objects.create(
            resource=instance_resource,
            engine=DatabaseInstance.Engine.POSTGRESQL,
        )
        database_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB Platform Database",
            resource_type=InfrastructureResource.ResourceType.LOGICAL_DATABASE,
        )
        LogicalDatabase.objects.create(
            resource=database_resource,
            instance=instance,
            database_name="adb_platform",
        )
        user = self._user()

        result = cast(
            InfrastructureSpecialistEditOut,
            get_infrastructure_specialist_edit_details(
                self._request(user),
                database_resource.id,
            ),
        )

        self.assertEqual(result.resource_type, "logical_database")
        self.assertEqual(result.values["instance_resource_id"], instance_resource.id)
        self.assertEqual(result.values["database_name"], "adb_platform")
