from typing import cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import (
    ApplicationProfile,
    ApplicationRepositoryLink,
    DatabaseInstance,
    InfrastructureResource,
    ProviderAccount,
    ServerProfile,
    ServiceProvider,
    SourceRepository,
)
from apps.infrastructure.ninja.application_repository_views import list_application_repository_links
from apps.infrastructure.ninja.data_application_schemas import (
    ApplicationCreateIn,
    ApplicationEnvironmentCreateIn,
    ApplicationEnvironmentOut,
    ApplicationOut,
    ApplicationRepositoryLinkCreateIn,
    ApplicationRepositoryLinkOut,
    DataApplicationSpecialistOptionsOut,
    DatabaseInstanceCreateIn,
    DatabaseInstanceOut,
    SourceRepositoryCreateIn,
    SourceRepositoryOut,
)
from apps.infrastructure.ninja.data_application_views import (
    create_application,
    create_application_environment,
    create_application_repository_link,
    create_database_instance,
    create_source_repository,
    data_application_options,
    delete_application_repository_link,
)
from authentication.models import User


class DataApplicationSpecialistApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.client_a = Client.objects.create(
            name="Client A",
            company="Client A Ltd",
            email="client-a-data-api@example.com",
            status="active",
        )
        self.client_b = Client.objects.create(
            name="Client B",
            company="Client B Ltd",
            email="client-b-data-api@example.com",
            status="active",
        )
        provider = ServiceProvider.objects.create(
            name="DigitalOcean Data API",
            slug="digitalocean-data-api",
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
            "ADB Shared Server",
            InfrastructureResource.ResourceType.SERVER,
        )
        self.internal_server = ServerProfile.objects.create(
            resource=server_resource,
            hostname="adb-shared-data01",
        )

    def _resource(
        self,
        name: str,
        resource_type: str,
        *,
        client: Client | None = None,
    ) -> InfrastructureResource:
        return InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT if client else OwnershipType.INTERNAL,
            client=client,
            name=name,
            resource_type=resource_type,
        )

    def _request(self, user: User) -> HttpRequest:
        request = self.factory.get("/api/admin/infrastructure/data-application-options")
        request.user = user
        return request

    def _user(self, email: str, codenames: list[str]) -> User:
        user = User.objects.create_user(
            email=email,
            password="test-password",
            first_name="Data",
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

    def test_options_only_return_accessible_current_resources(self) -> None:
        client_a_database_resource = self._resource(
            "Client A PostgreSQL",
            InfrastructureResource.ResourceType.DATABASE_INSTANCE,
            client=self.client_a,
        )
        DatabaseInstance.objects.create(
            resource=client_a_database_resource,
            engine=DatabaseInstance.Engine.POSTGRESQL,
        )
        client_b_repository_resource = self._resource(
            "Client B Repo",
            InfrastructureResource.ResourceType.SOURCE_REPOSITORY,
            client=self.client_b,
        )
        SourceRepository.objects.create(
            resource=client_b_repository_resource,
            repository_name="client-b",
        )
        user = self._user("data-options@example.com", ["view_infrastructureresource"])
        self._grant_client(user, self.client_a)

        result = cast(
            DataApplicationSpecialistOptionsOut,
            data_application_options(self._request(user)),
        )

        self.assertEqual([item.id for item in result.clients], [self.client_a.id])
        self.assertEqual(
            [item.resource_id for item in result.database_instances],
            [client_a_database_resource.id],
        )
        self.assertEqual(result.source_repositories, [])
        self.assertIn(
            self.internal_provider.resource_id,
            {item.resource_id for item in result.provider_accounts},
        )

    def test_create_client_database_with_shared_internal_hosting(self) -> None:
        user = self._user(
            "database-create@example.com",
            ["add_infrastructureresource", "add_databaseinstance"],
        )
        self._grant_client(user, self.client_a)

        status, result = create_database_instance(
            self._request(user),
            DatabaseInstanceCreateIn(
                ownership_type="client",
                client_id=self.client_a.id,
                name="Client A PostgreSQL",
                engine="postgresql",
                hosting_type="self_hosted",
                server_resource_id=self.internal_server.resource_id,
                provider_account_resource_id=self.internal_provider.resource_id,
                endpoint="10.42.10.20",
                port=5432,
            ),
        )

        self.assertEqual(status, 201)
        database = cast(DatabaseInstanceOut, result)
        self.assertEqual(database.client_id, self.client_a.id)
        self.assertEqual(database.server_resource_id, self.internal_server.resource_id)
        self.assertEqual(database.provider_account_resource_id, self.internal_provider.resource_id)

    def test_invalid_cross_client_database_does_not_leave_orphan_resource(self) -> None:
        user = self._user(
            "database-cross-client@example.com",
            ["add_infrastructureresource", "add_databaseinstance"],
        )
        self._grant_client(user, self.client_a)
        self._grant_client(user, self.client_b)
        before = InfrastructureResource.objects.count()

        status, payload = create_database_instance(
            self._request(user),
            DatabaseInstanceCreateIn(
                ownership_type="client",
                client_id=self.client_a.id,
                name="Invalid Client A PostgreSQL",
                engine="postgresql",
                provider_account_resource_id=self.client_b_provider.resource_id,
            ),
        )

        self.assertEqual(status, 400)
        self.assertEqual(cast(dict[str, object], payload)["code"], "invalid_infrastructure")
        self.assertEqual(InfrastructureResource.objects.count(), before)

    def test_create_application_environment_with_shared_internal_server(self) -> None:
        user = self._user(
            "application-environment@example.com",
            [
                "add_infrastructureresource",
                "add_applicationprofile",
                "add_applicationenvironment",
            ],
        )
        self._grant_client(user, self.client_a)
        app_status, app_result = create_application(
            self._request(user),
            ApplicationCreateIn(
                ownership_type="client",
                client_id=self.client_a.id,
                name="Client A Portal",
                application_type="web_app",
            ),
        )
        self.assertEqual(app_status, 201)
        application_resource_id = cast(ApplicationOut, app_result).resource_id

        environment_status, environment_result = create_application_environment(
            self._request(user),
            ApplicationEnvironmentCreateIn(
                ownership_type="client",
                client_id=self.client_a.id,
                name="Client A Portal Production",
                environment="production",
                application_resource_id=application_resource_id,
                deployment_type="server",
                server_resource_id=self.internal_server.resource_id,
                runtime="python",
                runtime_version="3.12",
            ),
        )

        self.assertEqual(environment_status, 201)
        environment = cast(ApplicationEnvironmentOut, environment_result)
        self.assertEqual(environment.application_resource_id, application_resource_id)
        self.assertEqual(environment.server_resource_id, self.internal_server.resource_id)

    def test_application_repository_link_allows_shared_internal_repository(self) -> None:
        user = self._user(
            "application-repository@example.com",
            [
                "add_infrastructureresource",
                "add_applicationprofile",
                "add_sourcerepository",
                "view_infrastructureresource",
                "view_applicationprofile",
                "view_sourcerepository",
                "view_applicationrepositorylink",
                "add_applicationrepositorylink",
            ],
        )
        self._grant_client(user, self.client_a)
        app_status, app_result = create_application(
            self._request(user),
            ApplicationCreateIn(
                ownership_type="client",
                client_id=self.client_a.id,
                name="Client A Portal",
            ),
        )
        self.assertEqual(app_status, 201)
        application_resource_id = cast(ApplicationOut, app_result).resource_id
        repo_status, repo_result = create_source_repository(
            self._request(user),
            SourceRepositoryCreateIn(
                name="ADB Shared Infrastructure Repo",
                repository_name="shared-infrastructure",
                visibility="private",
            ),
        )
        self.assertEqual(repo_status, 201)
        repository = cast(SourceRepositoryOut, repo_result)

        link_status, link_result = create_application_repository_link(
            self._request(user),
            application_resource_id,
            ApplicationRepositoryLinkCreateIn(
                repository_resource_id=repository.resource_id,
                role="infrastructure",
            ),
        )

        self.assertEqual(link_status, 201)
        link = cast(ApplicationRepositoryLinkOut, link_result)
        self.assertEqual(link.repository_resource_id, repository.resource_id)
        self.assertEqual(link.role, "infrastructure")

    def test_repository_link_creation_requires_repository_view_capability(self) -> None:
        user = self._user(
            "application-repository-no-view@example.com",
            [
                "add_infrastructureresource",
                "add_applicationprofile",
                "add_sourcerepository",
                "add_applicationrepositorylink",
            ],
        )
        app_status, app_result = create_application(
            self._request(user),
            ApplicationCreateIn(name="Internal App"),
        )
        self.assertEqual(app_status, 201)
        repo_status, repo_result = create_source_repository(
            self._request(user),
            SourceRepositoryCreateIn(
                name="Internal Repo",
                repository_name="internal-repo",
            ),
        )
        self.assertEqual(repo_status, 201)

        status, payload = create_application_repository_link(
            self._request(user),
            cast(ApplicationOut, app_result).resource_id,
            ApplicationRepositoryLinkCreateIn(
                repository_resource_id=cast(SourceRepositoryOut, repo_result).resource_id,
            ),
        )

        self.assertEqual(status, 403)
        self.assertEqual(cast(dict[str, object], payload)["code"], "forbidden")

    def test_repository_link_list_hides_repository_outside_scope(self) -> None:
        application_resource = self._resource(
            "Internal Application",
            InfrastructureResource.ResourceType.APPLICATION,
        )
        application = ApplicationProfile.objects.create(resource=application_resource)
        repository_resource = self._resource(
            "Client B Private Repo",
            InfrastructureResource.ResourceType.SOURCE_REPOSITORY,
            client=self.client_b,
        )
        repository = SourceRepository.objects.create(
            resource=repository_resource,
            repository_name="client-b-private",
        )
        ApplicationRepositoryLink.objects.create(
            application=application,
            repository=repository,
        )
        user = self._user(
            "application-repository-scope@example.com",
            [
                "view_infrastructureresource",
                "view_applicationprofile",
                "view_sourcerepository",
                "view_applicationrepositorylink",
            ],
        )

        result = list_application_repository_links(
            self._request(user),
            application_resource.id,
        )

        self.assertEqual(result, [])

    def test_repository_link_delete_hides_repository_outside_scope(self) -> None:
        application_resource = self._resource(
            "Internal Application",
            InfrastructureResource.ResourceType.APPLICATION,
        )
        application = ApplicationProfile.objects.create(resource=application_resource)
        repository_resource = self._resource(
            "Client B Private Repo",
            InfrastructureResource.ResourceType.SOURCE_REPOSITORY,
            client=self.client_b,
        )
        repository = SourceRepository.objects.create(
            resource=repository_resource,
            repository_name="client-b-private",
        )
        link = ApplicationRepositoryLink.objects.create(
            application=application,
            repository=repository,
        )
        user = self._user(
            "application-repository-delete-scope@example.com",
            [
                "view_infrastructureresource",
                "view_applicationprofile",
                "view_sourcerepository",
                "view_applicationrepositorylink",
                "delete_applicationrepositorylink",
            ],
        )

        status, payload = delete_application_repository_link(
            self._request(user),
            application_resource.id,
            link.id,
        )

        self.assertEqual(status, 404)
        self.assertEqual(cast(dict[str, object], payload)["code"], "not_found")
        self.assertTrue(ApplicationRepositoryLink.objects.filter(id=link.id).exists())
