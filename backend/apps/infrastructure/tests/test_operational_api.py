from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import (
    InfrastructureResource,
    KubernetesClusterProfile,
    KubernetesNamespaceProfile,
    KubernetesService,
    KubernetesWorkloadProfile,
    ProviderAccount,
    ServiceProvider,
)
from authentication.models import User


class OperationalSpecialistAPITests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="operations@example.test",
            password="test-password",
            first_name="Operations",
            last_name="User",
            is_staff=True,
        )
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
        self.client.force_login(self.user)
        self._grant(
            "view_infrastructureresource",
            "add_infrastructureresource",
            "change_infrastructureresource",
            "add_storageprofile",
            "add_kubernetesnamespaceprofile",
            "add_kubernetesservice",
        )

    def _grant(self, *codenames: str) -> None:
        permissions = Permission.objects.filter(
            content_type__app_label="infrastructure",
            codename__in=codenames,
        )
        self.user.user_permissions.add(*permissions)

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
            lifecycle_status=InfrastructureResource.LifecycleStatus.ACTIVE,
        )

    def _namespace(self) -> KubernetesNamespaceProfile:
        cluster_resource = self._resource(
            InfrastructureResource.ResourceType.KUBERNETES_CLUSTER,
            "Internal cluster",
        )
        cluster = KubernetesClusterProfile.objects.create(resource=cluster_resource)
        namespace_resource = self._resource(
            InfrastructureResource.ResourceType.KUBERNETES_NAMESPACE,
            "Internal namespace",
        )
        return KubernetesNamespaceProfile.objects.create(
            resource=namespace_resource,
            cluster=cluster,
            namespace="internal",
        )

    def test_options_only_return_visible_resources(self) -> None:
        visible = self._resource(InfrastructureResource.ResourceType.SERVER, "Internal server")
        self._resource(
            InfrastructureResource.ResourceType.SERVER,
            "Other client server",
            client=self.other_client,
        )

        response = self.client.get("/api/admin/infrastructure/operations/options")

        self.assertEqual(response.status_code, 200)
        server_ids = {item["resource_id"] for item in response.json()["servers"]}
        self.assertIn(visible.id, server_ids)
        self.assertEqual(len(server_ids), 1)

    def test_storage_create_rejects_cross_scope_provider_account(self) -> None:
        provider = ServiceProvider.objects.create(name="Provider", slug="provider")
        provider_resource = self._resource(
            InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
            "Other provider account",
            client=self.other_client,
        )
        ProviderAccount.objects.create(resource=provider_resource, provider=provider)

        response = self.client.post(
            "/api/admin/infrastructure/operations/storage",
            data={
                "ownership_type": "internal",
                "name": "Internal volume",
                "lifecycle_status": "active",
                "environment": "production",
                "criticality": "normal",
                "description": "",
                "storage_type": "block",
                "provider_account_resource_id": provider_resource.id,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            InfrastructureResource.objects.filter(
                name="Internal volume",
                resource_type=InfrastructureResource.ResourceType.STORAGE,
            ).exists()
        )

    def test_namespace_create_rejects_inaccessible_cluster(self) -> None:
        cluster_resource = self._resource(
            InfrastructureResource.ResourceType.KUBERNETES_CLUSTER,
            "Other cluster",
            client=self.other_client,
        )
        KubernetesClusterProfile.objects.create(resource=cluster_resource)

        response = self.client.post(
            "/api/admin/infrastructure/operations/kubernetes/namespaces",
            data={
                "ownership_type": "internal",
                "name": "Production namespace",
                "lifecycle_status": "active",
                "environment": "production",
                "criticality": "normal",
                "description": "",
                "cluster_resource_id": cluster_resource.id,
                "namespace": "production",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

    def test_kubernetes_service_rejects_workload_from_another_namespace(self) -> None:
        cluster_resource = self._resource(
            InfrastructureResource.ResourceType.KUBERNETES_CLUSTER,
            "Internal cluster",
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
        workload_resource = self._resource(
            InfrastructureResource.ResourceType.KUBERNETES_WORKLOAD,
            "Second API",
        )
        KubernetesWorkloadProfile.objects.create(
            resource=workload_resource,
            namespace=second,
            workload_kind=KubernetesWorkloadProfile.WorkloadKind.DEPLOYMENT,
            workload_name="api",
        )

        response = self.client.post(
            f"/api/admin/infrastructure/operations/kubernetes/namespaces/{first.resource_id}/services",
            data={
                "name": "api",
                "service_type": "cluster_ip",
                "workload_resource_id": workload_resource.id,
                "ports": ["80:8000"],
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

    def test_nested_kubernetes_creates_require_parent_change_permission(self) -> None:
        namespace = self._namespace()
        self._grant(
            "add_kubernetesingress",
            "add_helmrelease",
            "add_kubernetespersistentstorage",
        )
        change_permission = Permission.objects.get(
            content_type__app_label="infrastructure",
            codename="change_infrastructureresource",
        )
        self.user.user_permissions.remove(change_permission)

        requests = [
            (
                f"/api/admin/infrastructure/operations/kubernetes/namespaces/{namespace.resource_id}/services",
                {"name": "api", "service_type": "cluster_ip"},
            ),
            (
                f"/api/admin/infrastructure/operations/kubernetes/namespaces/{namespace.resource_id}/ingresses",
                {"name": "public"},
            ),
            (
                f"/api/admin/infrastructure/operations/kubernetes/namespaces/{namespace.resource_id}/helm-releases",
                {"name": "ingress", "chart": "ingress-nginx/ingress-nginx"},
            ),
            (
                f"/api/admin/infrastructure/operations/kubernetes/namespaces/{namespace.resource_id}/persistent-storage",
                {"name": "data"},
            ),
        ]

        for path, payload in requests:
            with self.subTest(path=path):
                response = self.client.post(
                    path,
                    data=payload,
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 403)

        self.assertFalse(KubernetesService.objects.exists())
