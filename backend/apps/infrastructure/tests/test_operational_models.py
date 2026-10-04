from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import (
    BackupPlanProfile,
    BackupSource,
    ContainerService,
    ContainerStackProfile,
    InfrastructureResource,
    KubernetesClusterProfile,
    KubernetesIngress,
    KubernetesNamespaceProfile,
    KubernetesService,
    KubernetesWorkloadProfile,
    ScheduledJobProfile,
    StorageProfile,
    SystemServiceProfile,
)


class OperationalSpecialistModelTests(TestCase):
    def setUp(self) -> None:
        self.client_record = Client.objects.create(
            name="Client",
            company="Client Ltd",
            email="client@example.test",
        )
        self.other_client = Client.objects.create(
            name="Other",
            company="Other Ltd",
            email="other@example.test",
        )

    def _resource(
        self,
        resource_type: str,
        name: str,
        *,
        client: Client | None = None,
    ) -> InfrastructureResource:
        return InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT if client else OwnershipType.INTERNAL,
            client=client,
            name=name,
            resource_type=resource_type,
        )

    def test_storage_profile_requires_storage_resource(self) -> None:
        server = self._resource(InfrastructureResource.ResourceType.SERVER, "Server")
        profile = StorageProfile(resource=server, storage_type=StorageProfile.StorageType.BLOCK)

        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_backup_sources_must_share_plan_scope(self) -> None:
        plan_resource = self._resource(
            InfrastructureResource.ResourceType.BACKUP_PLAN,
            "Client backups",
            client=self.client_record,
        )
        source_resource = self._resource(
            InfrastructureResource.ResourceType.SERVER,
            "Other server",
            client=self.other_client,
        )
        plan = BackupPlanProfile.objects.create(
            resource=plan_resource,
            backup_type=BackupPlanProfile.BackupType.SNAPSHOT,
        )
        source = BackupSource(backup_plan=plan, source_resource=source_resource)

        with self.assertRaises(ValidationError):
            source.full_clean()

    def test_container_stack_host_must_be_server_in_same_scope(self) -> None:
        stack_resource = self._resource(
            InfrastructureResource.ResourceType.CONTAINER_STACK,
            "Website containers",
            client=self.client_record,
        )
        host = self._resource(
            InfrastructureResource.ResourceType.SERVER,
            "Other client host",
            client=self.other_client,
        )
        stack = ContainerStackProfile(
            resource=stack_resource,
            orchestrator=ContainerStackProfile.Orchestrator.DOCKER_COMPOSE,
            host_resource=host,
        )

        with self.assertRaises(ValidationError):
            stack.full_clean()

    def test_container_service_requires_list_ports_and_volumes(self) -> None:
        stack_resource = self._resource(
            InfrastructureResource.ResourceType.CONTAINER_STACK,
            "Internal stack",
        )
        stack = ContainerStackProfile.objects.create(
            resource=stack_resource,
            orchestrator=ContainerStackProfile.Orchestrator.DOCKER_COMPOSE,
        )
        service = ContainerService(
            stack=stack,
            name="backend",
            ports="8000:8000",  # type: ignore[arg-type]
            volumes=[],
        )

        with self.assertRaises(ValidationError):
            service.full_clean()

    def test_kubernetes_namespace_must_share_cluster_scope(self) -> None:
        cluster_resource = self._resource(
            InfrastructureResource.ResourceType.KUBERNETES_CLUSTER,
            "Client cluster",
            client=self.client_record,
        )
        namespace_resource = self._resource(
            InfrastructureResource.ResourceType.KUBERNETES_NAMESPACE,
            "Other namespace",
            client=self.other_client,
        )
        cluster = KubernetesClusterProfile.objects.create(resource=cluster_resource)
        namespace = KubernetesNamespaceProfile(
            resource=namespace_resource,
            cluster=cluster,
            namespace="production",
        )

        with self.assertRaises(ValidationError):
            namespace.full_clean()

    def test_ingress_target_service_must_share_namespace(self) -> None:
        cluster_resource = self._resource(
            InfrastructureResource.ResourceType.KUBERNETES_CLUSTER,
            "Cluster",
        )
        cluster = KubernetesClusterProfile.objects.create(resource=cluster_resource)
        first_resource = self._resource(
            InfrastructureResource.ResourceType.KUBERNETES_NAMESPACE,
            "First namespace",
        )
        second_resource = self._resource(
            InfrastructureResource.ResourceType.KUBERNETES_NAMESPACE,
            "Second namespace",
        )
        first = KubernetesNamespaceProfile.objects.create(
            resource=first_resource,
            cluster=cluster,
            namespace="first",
        )
        second = KubernetesNamespaceProfile.objects.create(
            resource=second_resource,
            cluster=cluster,
            namespace="second",
        )
        service = KubernetesService.objects.create(
            namespace=first,
            name="web",
            service_type=KubernetesService.ServiceType.CLUSTER_IP,
        )
        ingress = KubernetesIngress(namespace=second, name="web", target_service=service)

        with self.assertRaises(ValidationError):
            ingress.full_clean()

    def test_kubernetes_workload_requires_workload_resource(self) -> None:
        cluster_resource = self._resource(
            InfrastructureResource.ResourceType.KUBERNETES_CLUSTER,
            "Cluster",
        )
        cluster = KubernetesClusterProfile.objects.create(resource=cluster_resource)
        namespace_resource = self._resource(
            InfrastructureResource.ResourceType.KUBERNETES_NAMESPACE,
            "Namespace",
        )
        namespace = KubernetesNamespaceProfile.objects.create(
            resource=namespace_resource,
            cluster=cluster,
            namespace="default",
        )
        wrong_resource = self._resource(InfrastructureResource.ResourceType.OTHER, "Wrong")
        workload = KubernetesWorkloadProfile(
            resource=wrong_resource,
            namespace=namespace,
            workload_kind=KubernetesWorkloadProfile.WorkloadKind.DEPLOYMENT,
            workload_name="api",
        )

        with self.assertRaises(ValidationError):
            workload.full_clean()

    def test_system_service_requires_server_host(self) -> None:
        service_resource = self._resource(
            InfrastructureResource.ResourceType.SYSTEM_SERVICE,
            "nginx",
        )
        wrong_host = self._resource(InfrastructureResource.ResourceType.STORAGE, "Storage")
        service = SystemServiceProfile(
            resource=service_resource,
            host_resource=wrong_host,
            manager=SystemServiceProfile.Manager.SYSTEMD,
            unit_name="nginx.service",
        )

        with self.assertRaises(ValidationError):
            service.full_clean()

    def test_scheduled_job_rejects_cross_scope_host(self) -> None:
        job_resource = self._resource(
            InfrastructureResource.ResourceType.SCHEDULED_JOB,
            "Nightly export",
            client=self.client_record,
        )
        host = self._resource(
            InfrastructureResource.ResourceType.SERVER,
            "Other host",
            client=self.other_client,
        )
        job = ScheduledJobProfile(
            resource=job_resource,
            scheduler=ScheduledJobProfile.Scheduler.CRON,
            host_resource=host,
        )

        with self.assertRaises(ValidationError):
            job.full_clean()
