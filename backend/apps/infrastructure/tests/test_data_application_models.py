from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.clients.models import Client
from apps.core.ownership import OwnershipType
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


class DataApplicationSpecialistModelTests(TestCase):
    def setUp(self) -> None:
        self.client_a = Client.objects.create(
            name="Client A",
            company="Client A Ltd",
            email="client-a-data@example.com",
            status="active",
        )
        self.client_b = Client.objects.create(
            name="Client B",
            company="Client B Ltd",
            email="client-b-data@example.com",
            status="active",
        )
        provider = ServiceProvider.objects.create(
            name="DigitalOcean Data",
            slug="digitalocean-data",
            category=ServiceProvider.Category.CLOUD,
        )
        internal_provider_resource = self._resource(
            "ADB Cloud",
            InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
        )
        self.internal_provider = ProviderAccount.objects.create(
            resource=internal_provider_resource,
            provider=provider,
        )
        client_b_provider_resource = self._resource(
            "Client B Cloud",
            InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
            client=self.client_b,
        )
        self.client_b_provider = ProviderAccount.objects.create(
            resource=client_b_provider_resource,
            provider=provider,
        )
        server_resource = self._resource(
            "ADB Shared App Server",
            InfrastructureResource.ResourceType.SERVER,
        )
        self.internal_server = ServerProfile.objects.create(
            resource=server_resource,
            hostname="adb-shared-app01",
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

    def test_database_instance_requires_database_instance_resource(self) -> None:
        resource = self._resource(
            "Wrong database identity",
            InfrastructureResource.ResourceType.SERVER,
        )
        database = DatabaseInstance(
            resource=resource,
            engine=DatabaseInstance.Engine.POSTGRESQL,
        )

        with self.assertRaises(ValidationError):
            database.full_clean()

    def test_client_database_can_use_shared_internal_compute_and_provider(self) -> None:
        resource = self._resource(
            "Client A PostgreSQL",
            InfrastructureResource.ResourceType.DATABASE_INSTANCE,
            client=self.client_a,
        )
        database = DatabaseInstance(
            resource=resource,
            engine=DatabaseInstance.Engine.POSTGRESQL,
            hosting_type=DatabaseInstance.HostingType.SELF_HOSTED,
            server=self.internal_server,
            provider_account=self.internal_provider,
            endpoint="10.42.10.20",
            port=5432,
        )

        database.full_clean()

    def test_database_rejects_cross_client_provider(self) -> None:
        resource = self._resource(
            "Client A Managed PostgreSQL",
            InfrastructureResource.ResourceType.DATABASE_INSTANCE,
            client=self.client_a,
        )
        database = DatabaseInstance(
            resource=resource,
            engine=DatabaseInstance.Engine.POSTGRESQL,
            provider_account=self.client_b_provider,
        )

        with self.assertRaises(ValidationError) as error:
            database.full_clean()

        self.assertIn("provider_account", error.exception.message_dict)

    def test_managed_database_rejects_self_hosting_server(self) -> None:
        resource = self._resource(
            "Managed PostgreSQL",
            InfrastructureResource.ResourceType.DATABASE_INSTANCE,
        )
        database = DatabaseInstance(
            resource=resource,
            engine=DatabaseInstance.Engine.POSTGRESQL,
            hosting_type=DatabaseInstance.HostingType.MANAGED,
            server=self.internal_server,
        )

        with self.assertRaises(ValidationError) as error:
            database.full_clean()

        self.assertIn("server", error.exception.message_dict)

    def test_logical_database_enforces_parent_ownership(self) -> None:
        client_b_instance_resource = self._resource(
            "Client B PostgreSQL",
            InfrastructureResource.ResourceType.DATABASE_INSTANCE,
            client=self.client_b,
        )
        client_b_instance = DatabaseInstance.objects.create(
            resource=client_b_instance_resource,
            engine=DatabaseInstance.Engine.POSTGRESQL,
        )
        client_a_database_resource = self._resource(
            "Client A App DB",
            InfrastructureResource.ResourceType.LOGICAL_DATABASE,
            client=self.client_a,
        )
        logical_database = LogicalDatabase(
            resource=client_a_database_resource,
            instance=client_b_instance,
            database_name="app",
        )

        with self.assertRaises(ValidationError) as error:
            logical_database.full_clean()

        self.assertIn("instance", error.exception.message_dict)

    def test_internal_logical_database_cannot_belong_to_client_instance(self) -> None:
        instance_resource = self._resource(
            "Client A PostgreSQL",
            InfrastructureResource.ResourceType.DATABASE_INSTANCE,
            client=self.client_a,
        )
        instance = DatabaseInstance.objects.create(
            resource=instance_resource,
            engine=DatabaseInstance.Engine.POSTGRESQL,
        )
        logical_resource = self._resource(
            "ADB Internal DB",
            InfrastructureResource.ResourceType.LOGICAL_DATABASE,
        )
        logical_database = LogicalDatabase(
            resource=logical_resource,
            instance=instance,
            database_name="internal",
        )

        with self.assertRaises(ValidationError) as error:
            logical_database.full_clean()

        self.assertIn("instance", error.exception.message_dict)

    def test_client_environment_can_use_shared_internal_hosting(self) -> None:
        application_resource = self._resource(
            "Client A Portal",
            InfrastructureResource.ResourceType.APPLICATION,
            client=self.client_a,
        )
        application = ApplicationProfile.objects.create(
            resource=application_resource,
            application_type=ApplicationProfile.ApplicationType.WEB_APP,
        )
        environment_resource = self._resource(
            "Client A Portal Production",
            InfrastructureResource.ResourceType.APPLICATION_ENVIRONMENT,
            client=self.client_a,
            environment=InfrastructureResource.Environment.PRODUCTION,
        )
        environment = ApplicationEnvironment(
            resource=environment_resource,
            application=application,
            deployment_type=ApplicationEnvironment.DeploymentType.SERVER,
            server=self.internal_server,
            provider_account=self.internal_provider,
        )

        environment.full_clean()

    def test_environment_rejects_application_owned_by_another_client(self) -> None:
        application_resource = self._resource(
            "Client B App",
            InfrastructureResource.ResourceType.APPLICATION,
            client=self.client_b,
        )
        application = ApplicationProfile.objects.create(
            resource=application_resource,
            application_type=ApplicationProfile.ApplicationType.WEB_APP,
        )
        environment_resource = self._resource(
            "Client A Production",
            InfrastructureResource.ResourceType.APPLICATION_ENVIRONMENT,
            client=self.client_a,
            environment=InfrastructureResource.Environment.PRODUCTION,
        )
        environment = ApplicationEnvironment(
            resource=environment_resource,
            application=application,
        )

        with self.assertRaises(ValidationError) as error:
            environment.full_clean()

        self.assertIn("application", error.exception.message_dict)

    def test_repository_rejects_cross_client_provider(self) -> None:
        resource = self._resource(
            "Client A Source",
            InfrastructureResource.ResourceType.SOURCE_REPOSITORY,
            client=self.client_a,
        )
        repository = SourceRepository(
            resource=resource,
            provider_account=self.client_b_provider,
            repository_name="client-a-app",
        )

        with self.assertRaises(ValidationError) as error:
            repository.full_clean()

        self.assertIn("provider_account", error.exception.message_dict)

    def test_client_application_can_link_shared_internal_repository(self) -> None:
        application_resource = self._resource(
            "Client A App",
            InfrastructureResource.ResourceType.APPLICATION,
            client=self.client_a,
        )
        application = ApplicationProfile.objects.create(resource=application_resource)
        repository_resource = self._resource(
            "ADB Shared Deployment Repo",
            InfrastructureResource.ResourceType.SOURCE_REPOSITORY,
        )
        repository = SourceRepository.objects.create(
            resource=repository_resource,
            repository_name="shared-deployment",
        )
        link = ApplicationRepositoryLink(
            application=application,
            repository=repository,
            role=ApplicationRepositoryLink.Role.INFRASTRUCTURE,
        )

        link.full_clean()

    def test_application_repository_link_rejects_cross_client_repository(self) -> None:
        application_resource = self._resource(
            "Client A App",
            InfrastructureResource.ResourceType.APPLICATION,
            client=self.client_a,
        )
        application = ApplicationProfile.objects.create(resource=application_resource)
        repository_resource = self._resource(
            "Client B Source",
            InfrastructureResource.ResourceType.SOURCE_REPOSITORY,
            client=self.client_b,
        )
        repository = SourceRepository.objects.create(
            resource=repository_resource,
            repository_name="client-b-app",
        )
        link = ApplicationRepositoryLink(
            application=application,
            repository=repository,
        )

        with self.assertRaises(ValidationError) as error:
            link.full_clean()

        self.assertIn("repository", error.exception.message_dict)

    def test_specialists_do_not_add_secret_payload_fields(self) -> None:
        forbidden_fragments = ("password", "token", "secret", "private_key", "credential")
        for model in (
            DatabaseInstance,
            LogicalDatabase,
            ApplicationProfile,
            ApplicationEnvironment,
            SourceRepository,
            ApplicationRepositoryLink,
        ):
            field_names = {field.name for field in model._meta.get_fields()}
            for forbidden in forbidden_fragments:
                self.assertNotIn(forbidden, field_names)
