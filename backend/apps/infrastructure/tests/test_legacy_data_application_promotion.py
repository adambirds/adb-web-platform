from django.test import TestCase

from apps.core.ownership import OwnershipType
from apps.infrastructure.legacy_reconciliation import reconcile_legacy_resource
from apps.infrastructure.models import (
    Application,
    ApplicationProfile,
    Database,
    DatabaseInstance,
    InfrastructureResource,
    Server,
)


class LegacyDataApplicationPromotionTests(TestCase):
    def test_database_reconciliation_promotes_safe_deterministic_fields(self) -> None:
        legacy_server = Server.objects.create(
            hostname="legacy-db-host",
            provider="do",
            os="ubuntu_24",
            notes="Do not infer this hosting relationship automatically.",
        )
        legacy = Database.objects.create(
            name="Legacy PostgreSQL",
            db_type="postgres",
            provider="self_hosted",
            server=legacy_server,
            version="16.4",
            backup_strategy="Contains operational free text that must not be promoted.",
        )

        resource = reconcile_legacy_resource(
            legacy_type="database",
            legacy_id=legacy.id,
            ownership_type=OwnershipType.INTERNAL,
            client=None,
            lifecycle_status=InfrastructureResource.LifecycleStatus.ACTIVE,
            environment=InfrastructureResource.Environment.PRODUCTION,
            criticality=InfrastructureResource.Criticality.HIGH,
            name=None,
            linked_by=None,
        )

        database = DatabaseInstance.objects.get(resource=resource)
        self.assertEqual(database.engine, DatabaseInstance.Engine.POSTGRESQL)
        self.assertEqual(database.engine_version, "16.4")
        self.assertEqual(
            database.hosting_type,
            DatabaseInstance.HostingType.SELF_HOSTED,
        )
        self.assertIsNone(database.server_id)
        self.assertIsNone(database.provider_account_id)
        self.assertNotIn("operational free text", resource.description.lower())

    def test_managed_legacy_database_does_not_guess_provider_account(self) -> None:
        legacy = Database.objects.create(
            name="Legacy Managed PostgreSQL",
            db_type="postgres",
            provider="do",
            version="17",
        )

        resource = reconcile_legacy_resource(
            legacy_type="database",
            legacy_id=legacy.id,
            ownership_type=OwnershipType.INTERNAL,
            client=None,
            lifecycle_status=InfrastructureResource.LifecycleStatus.ACTIVE,
            environment=InfrastructureResource.Environment.PRODUCTION,
            criticality=InfrastructureResource.Criticality.NORMAL,
            name=None,
            linked_by=None,
        )

        database = DatabaseInstance.objects.get(resource=resource)
        self.assertEqual(database.hosting_type, DatabaseInstance.HostingType.MANAGED)
        self.assertIsNone(database.provider_account_id)

    def test_application_reconciliation_promotes_type_only(self) -> None:
        legacy_server = Server.objects.create(
            hostname="legacy-app-host",
            provider="do",
            os="ubuntu_24",
        )
        legacy = Application.objects.create(
            name="Legacy SaaS",
            app_type="saas",
            description="The shared resource reconciliation owns the description.",
            status="active",
            notes="Do not promote potentially sensitive application notes.",
        )
        legacy.servers.add(legacy_server)

        resource = reconcile_legacy_resource(
            legacy_type="application",
            legacy_id=legacy.id,
            ownership_type=OwnershipType.INTERNAL,
            client=None,
            lifecycle_status=InfrastructureResource.LifecycleStatus.ACTIVE,
            environment=InfrastructureResource.Environment.PRODUCTION,
            criticality=InfrastructureResource.Criticality.NORMAL,
            name=None,
            linked_by=None,
        )

        application = ApplicationProfile.objects.get(resource=resource)
        self.assertEqual(application.application_type, ApplicationProfile.ApplicationType.SAAS)
        self.assertEqual(application.repository_links.count(), 0)
        self.assertEqual(application.environments.count(), 0)
        self.assertNotIn("sensitive application notes", resource.description.lower())
