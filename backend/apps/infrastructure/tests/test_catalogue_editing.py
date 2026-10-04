from __future__ import annotations

import json

from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.models import AuditEvent
from apps.infrastructure.models import (
    ApplicationProfile,
    ApplicationRepositoryLink,
    DomainProfile,
    InfrastructureResource,
    InfrastructureTag,
    ProviderAccount,
    ResourceRelationship,
    ServiceProvider,
    SourceRepository,
    TLSCertificate,
    TLSCertificateDomain,
)
from authentication.models import User


class InfrastructureEditingTests(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(
            email="create@example.test",
            password="test-password",
            first_name="Create",
            last_name="Staff",
            is_staff=True,
        )
        self.profile = StaffAccessProfile.objects.create(user=self.staff)
        self.client.force_login(self.staff)
        self.provider = ServiceProvider.objects.create(
            name="Example Cloud", slug="example-cloud", category="cloud"
        )
        self.allowed = Client.objects.create(name="Allowed", email="allowed@example.test")
        self.hidden = Client.objects.create(name="Hidden", email="hidden@example.test")
        ClientAccessGrant.objects.create(profile=self.profile, client=self.allowed)

    def grant(self, *names: str) -> None:
        self.staff.user_permissions.add(
            *Permission.objects.filter(content_type__app_label="infrastructure", codename__in=names)
        )

    def test_vendor_update_requires_change_permission_and_preserves_accounts(self) -> None:
        self.grant("view_serviceprovider")
        resource = InfrastructureResource.objects.create(
            name="Account", resource_type="provider_account"
        )
        account = ProviderAccount.objects.create(resource=resource, provider=self.provider)
        url = f"/api/admin/infrastructure/service-providers/{self.provider.id}"
        payload = {
            "name": "Updated vendor",
            "slug": "updated",
            "category": "hosting",
            "is_active": False,
            "notes": "Support notes",
        }
        self.assertEqual(
            self.client.patch(
                url, json.dumps(payload), content_type="application/json"
            ).status_code,
            403,
        )
        self.grant("change_serviceprovider")
        response = self.client.patch(url, json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.provider.refresh_from_db()
        account.refresh_from_db()
        self.assertEqual(self.provider.name, "Updated vendor")
        self.assertFalse(self.provider.is_active)
        self.assertEqual(account.provider_id, self.provider.id)
        self.assertTrue(
            AuditEvent.objects.filter(
                action="updated",
                target_id=str(self.provider.id),
                target_type="infrastructure.serviceprovider",
            ).exists()
        )
        payload["website_url"] = "invalid-url"
        payload["name"] = "Invalid update"
        self.assertEqual(
            self.client.patch(
                url, json.dumps(payload), content_type="application/json"
            ).status_code,
            400,
        )
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.name, "Updated vendor")
        self.assertEqual(
            self.client.patch(
                url.replace(str(self.provider.id), "99999"),
                json.dumps(payload),
                content_type="application/json",
            ).status_code,
            404,
        )

    def test_shared_tag_edit_changes_linked_resources_and_rejects_duplicates(self) -> None:
        self.grant("view_infrastructuretag")
        tag = InfrastructureTag.objects.create(name="Old", slug="old")
        resource = InfrastructureResource.objects.create(name="Tagged", resource_type="other")
        resource.tags.add(tag)
        url = f"/api/admin/infrastructure/tags/{tag.id}"
        payload = {"name": "New", "slug": "new", "colour": "cyan"}
        self.assertEqual(
            self.client.patch(
                url, json.dumps(payload), content_type="application/json"
            ).status_code,
            403,
        )
        self.grant("change_infrastructuretag")
        self.assertEqual(
            self.client.patch(
                url, json.dumps(payload), content_type="application/json"
            ).status_code,
            200,
        )
        self.assertEqual(resource.tags.get().name, "New")
        InfrastructureTag.objects.create(name="Duplicate", slug="duplicate")
        payload["slug"] = "duplicate"
        self.assertEqual(
            self.client.patch(
                url, json.dumps(payload), content_type="application/json"
            ).status_code,
            400,
        )
        tag.refresh_from_db()
        self.assertEqual(tag.slug, "new")

    def test_nested_links_edit_in_place_and_enforce_scope_and_change_permissions(self) -> None:
        self.grant(
            "view_infrastructureresource",
            "view_applicationprofile",
            "view_sourcerepository",
            "view_applicationrepositorylink",
            "view_tlscertificate",
            "view_domainprofile",
            "view_tlscertificatedomain",
        )
        application = ApplicationProfile.objects.create(
            resource=InfrastructureResource.objects.create(name="App", resource_type="application")
        )
        repository = SourceRepository.objects.create(
            resource=InfrastructureResource.objects.create(
                name="Repo", resource_type="source_repository"
            ),
            repository_name="repo",
        )
        repo_link = ApplicationRepositoryLink.objects.create(
            application=application, repository=repository
        )
        certificate = TLSCertificate.objects.create(
            resource=InfrastructureResource.objects.create(
                name="TLS", resource_type="tls_certificate"
            )
        )
        domain = DomainProfile.objects.create(
            resource=InfrastructureResource.objects.create(name="Domain", resource_type="domain"),
            domain_name="example.test",
        )
        tls_link = TLSCertificateDomain.objects.create(certificate=certificate, domain=domain)
        cases = [
            (
                f"applications/{application.resource_id}/repositories/{repo_link.id}",
                "change_applicationrepositorylink",
                {
                    "repository_resource_id": repository.resource_id,
                    "role": "backend",
                    "path": "services/api",
                    "notes": "Updated",
                },
                repo_link,
            ),
            (
                f"tls-certificates/{certificate.resource_id}/domains/{tls_link.id}",
                "change_tlscertificatedomain",
                {"domain_resource_id": domain.resource_id, "is_primary": True},
                tls_link,
            ),
        ]
        for path, capability, payload, link in cases:
            with self.subTest(path=path):
                url = f"/api/admin/infrastructure/{path}"
                self.assertEqual(
                    self.client.put(
                        url, json.dumps(payload), content_type="application/json"
                    ).status_code,
                    403,
                )
                self.grant(capability)
                self.assertEqual(
                    self.client.put(
                        url, json.dumps(payload), content_type="application/json"
                    ).status_code,
                    200,
                )
                link.refresh_from_db()
                owner = application.resource if link == repo_link else certificate.resource
                owner.ownership_type = "client"
                owner.client = self.hidden
                owner.save()
                self.assertEqual(
                    self.client.put(
                        url, json.dumps(payload), content_type="application/json"
                    ).status_code,
                    404,
                )
        self.assertEqual(repo_link.path, "services/api")
        self.assertTrue(tls_link.is_primary)

    def test_relationship_edit_rejects_hidden_target_and_invalid_type(self) -> None:
        self.grant("view_infrastructureresource")
        source = InfrastructureResource.objects.create(
            name="Source", resource_type="other", ownership_type="client", client=self.allowed
        )
        target = InfrastructureResource.objects.create(name="Target", resource_type="other")
        hidden = InfrastructureResource.objects.create(
            name="Hidden", resource_type="other", ownership_type="client", client=self.hidden
        )
        relationship = ResourceRelationship.objects.create(
            source_resource=source,
            target_resource=target,
            relationship_type="depends_on",
            notes="Keep",
        )
        url = f"/api/admin/infrastructure/resources/{source.id}/relationships/{relationship.id}"
        payload = {
            "target_resource_id": target.id,
            "relationship_type": "depends_on",
            "label": "New label",
            "notes": "Updated notes",
        }
        self.assertEqual(
            self.client.patch(
                url, json.dumps(payload), content_type="application/json"
            ).status_code,
            403,
        )
        self.grant("change_resourcerelationship")
        self.assertEqual(
            self.client.patch(
                url, json.dumps(payload), content_type="application/json"
            ).status_code,
            200,
        )
        payload["target_resource_id"] = hidden.id
        self.assertEqual(
            self.client.patch(
                url, json.dumps(payload), content_type="application/json"
            ).status_code,
            404,
        )
        payload["target_resource_id"] = target.id
        payload["relationship_type"] = "invalid"
        self.assertEqual(
            self.client.patch(
                url, json.dumps(payload), content_type="application/json"
            ).status_code,
            400,
        )
        relationship.refresh_from_db()
        self.assertEqual(relationship.label, "New label")
        self.assertEqual(relationship.notes, "Updated notes")
        self.assertTrue(
            AuditEvent.objects.filter(
                action="updated", resource_id=source.id, client_id=self.allowed.id
            ).exists()
        )
