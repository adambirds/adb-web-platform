from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.credentials.models import StoredCredential
from apps.infrastructure.models import InfrastructureResource
from apps.knowledge_base.models import KnowledgeBaseDocument, KnowledgeBaseSection
from apps.knowledge_base.services import DocumentWrite, create_document
from authentication.models import User


class KnowledgeBaseAPITests(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(
            email="knowledge-api@example.test",
            password="test-password",
            first_name="Knowledge",
            last_name="Editor",
            is_staff=True,
        )
        profile = StaffAccessProfile.objects.create(user=self.staff)
        self.visible_client = Client.objects.create(
            name="Visible",
            company="Visible Client",
            email="visible-kb@example.test",
        )
        self.hidden_client = Client.objects.create(
            name="Hidden",
            company="Hidden Client",
            email="hidden-kb@example.test",
        )
        ClientAccessGrant.objects.create(
            profile=profile,
            client=self.visible_client,
            granted_by=self.staff,
        )
        self.internal_section = KnowledgeBaseSection.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Internal runbooks",
        )
        self.visible_section = KnowledgeBaseSection.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.visible_client,
            name="Client operations",
        )
        self.hidden_section = KnowledgeBaseSection.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            name="Hidden operations",
        )
        self.internal_document = create_document(
            write=DocumentWrite(
                ownership_type=OwnershipType.INTERNAL,
                client_id=None,
                title="Internal deployment",
                summary="Deploy the platform.",
                section=self.internal_section,
                content="# Internal deployment",
            ),
            editor=self.staff,
        )
        self.visible_document = create_document(
            write=DocumentWrite(
                ownership_type=OwnershipType.CLIENT,
                client_id=self.visible_client.id,
                title="Visible client runbook",
                summary="Client operations.",
                section=self.visible_section,
                content="# Visible client",
            ),
            editor=self.staff,
        )
        self.hidden_document = create_document(
            write=DocumentWrite(
                ownership_type=OwnershipType.CLIENT,
                client_id=self.hidden_client.id,
                title="Hidden client runbook",
                summary="Must remain hidden.",
                section=self.hidden_section,
                content="# Hidden client",
            ),
            editor=self.staff,
        )
        self.visible_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.visible_client,
            name="Visible server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        self.hidden_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            name="Hidden server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        self.visible_credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.visible_client,
            name="Visible deployment credential",
        )
        self.hidden_credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            name="Hidden deployment credential",
        )
        self.client.force_login(self.staff)

    def grant(self, *permission_names: tuple[str, str]) -> None:
        for app_label, codename in permission_names:
            permission = Permission.objects.get(
                content_type__app_label=app_label,
                codename=codename,
            )
            self.staff.user_permissions.add(permission)

    def test_workspace_hides_out_of_scope_client_documents(self) -> None:
        self.grant(("knowledge_base", "view_knowledgebasedocument"))

        response = self.client.get("/api/admin/knowledge-base/workspace")
        hidden_filter = self.client.get(
            f"/api/admin/knowledge-base/workspace?client_id={self.hidden_client.id}"
        )

        self.assertEqual(response.status_code, 200)
        ids = {document["id"] for document in response.json()["documents"]}
        self.assertEqual(ids, {self.internal_document.id, self.visible_document.id})
        self.assertNotIn(self.hidden_document.id, ids)
        self.assertEqual(hidden_filter.status_code, 404)

    def test_workspace_search_and_archive_views_are_server_side(self) -> None:
        self.grant(
            ("knowledge_base", "view_knowledgebasedocument"),
            ("knowledge_base", "change_knowledgebasedocument"),
        )

        search = self.client.get("/api/admin/knowledge-base/workspace?q=deployment")
        archive = self.client.post(
            f"/api/admin/knowledge-base/documents/{self.internal_document.id}/archive"
        )
        current = self.client.get("/api/admin/knowledge-base/workspace?view=current")
        archived = self.client.get("/api/admin/knowledge-base/workspace?view=archived")

        self.assertEqual(search.status_code, 200)
        self.assertEqual(search.json()["documents"][0]["id"], self.internal_document.id)
        self.assertEqual(archive.status_code, 200)
        self.assertNotIn(
            self.internal_document.id,
            {document["id"] for document in current.json()["documents"]},
        )
        self.assertIn(
            self.internal_document.id,
            {document["id"] for document in archived.json()["documents"]},
        )

    def test_create_document_builds_version_tags_and_safe_links(self) -> None:
        self.grant(
            ("knowledge_base", "add_knowledgebasedocument"),
            ("knowledge_base", "view_knowledgebasedocument"),
            ("infrastructure", "view_infrastructureresource"),
            ("credentials", "view_storedcredential"),
        )
        payload = {
            "ownership_type": "client",
            "client_id": self.visible_client.id,
            "title": "Linked deployment runbook",
            "summary": "Safe linked metadata.",
            "section_id": self.visible_section.id,
            "content": "# Deploy",
            "tag_names": ["Deployment", "Runbook"],
            "resource_ids": [self.visible_resource.id],
            "credential_ids": [self.visible_credential.id],
        }

        response = self.client.post(
            "/api/admin/knowledge-base/documents",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["version_count"], 1)
        self.assertEqual(set(body["tags"]), {"Deployment", "Runbook"})
        self.assertEqual(body["resources"][0]["resource_id"], self.visible_resource.id)
        self.assertEqual(body["credentials"][0]["credential_id"], self.visible_credential.id)
        self.assertNotIn("password", body["credentials"][0])
        self.assertNotIn("encrypted_secret_payload", body["credentials"][0])

    def test_credential_links_are_omitted_without_vault_metadata_permission(self) -> None:
        self.grant(
            ("knowledge_base", "view_knowledgebasedocument"),
            ("knowledge_base", "add_knowledgebasedocument"),
            ("credentials", "view_storedcredential"),
        )
        create_response = self.client.post(
            "/api/admin/knowledge-base/documents",
            data={
                "ownership_type": "client",
                "client_id": self.visible_client.id,
                "title": "Credential reference",
                "section_id": self.visible_section.id,
                "content": "Use the linked Vault entry.",
                "credential_ids": [self.visible_credential.id],
            },
            content_type="application/json",
        )
        document_id = create_response.json()["id"]
        credential_permission = Permission.objects.get(
            content_type__app_label="credentials",
            codename="view_storedcredential",
        )
        self.staff.user_permissions.remove(credential_permission)

        detail = self.client.get(f"/api/admin/knowledge-base/documents/{document_id}")

        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["credentials"], [])

    def test_cross_client_link_targets_are_not_discoverable(self) -> None:
        self.grant(
            ("knowledge_base", "add_knowledgebasedocument"),
            ("infrastructure", "view_infrastructureresource"),
            ("credentials", "view_storedcredential"),
        )
        payload = {
            "ownership_type": "client",
            "client_id": self.visible_client.id,
            "title": "Unsafe links",
            "section_id": self.visible_section.id,
            "content": "# Unsafe",
            "resource_ids": [self.hidden_resource.id],
            "credential_ids": [self.hidden_credential.id],
        }

        response = self.client.post(
            "/api/admin/knowledge-base/documents",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(KnowledgeBaseDocument.objects.filter(title="Unsafe links").exists())

    def test_content_update_creates_version_and_version_endpoint_is_immutable_history(self) -> None:
        self.grant(
            ("knowledge_base", "view_knowledgebasedocument"),
            ("knowledge_base", "change_knowledgebasedocument"),
        )
        response = self.client.put(
            f"/api/admin/knowledge-base/documents/{self.visible_document.id}",
            data={
                "title": self.visible_document.title,
                "summary": self.visible_document.summary,
                "section_id": self.visible_section.id,
                "content": "# Visible client\n\nUpdated instructions.",
                "change_summary": "Update instructions",
            },
            content_type="application/json",
        )
        historical = self.client.get(
            f"/api/admin/knowledge-base/documents/{self.visible_document.id}/versions/1"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["version_count"], 2)
        self.assertEqual(historical.status_code, 200)
        self.assertEqual(historical.json()["content"], "# Visible client")
        self.assertEqual(historical.json()["version_number"], 1)

    def test_text_only_edit_preserves_hidden_resource_and_credential_links(self) -> None:
        self.grant(
            ("knowledge_base", "view_knowledgebasedocument"),
            ("knowledge_base", "add_knowledgebasedocument"),
            ("knowledge_base", "change_knowledgebasedocument"),
            ("infrastructure", "view_infrastructureresource"),
            ("credentials", "view_storedcredential"),
        )
        create_response = self.client.post(
            "/api/admin/knowledge-base/documents",
            data={
                "ownership_type": "client",
                "client_id": self.visible_client.id,
                "title": "Protected link references",
                "section_id": self.visible_section.id,
                "content": "# Original",
                "resource_ids": [self.visible_resource.id],
                "credential_ids": [self.visible_credential.id],
            },
            content_type="application/json",
        )
        document_id = create_response.json()["id"]
        self.staff.user_permissions.remove(
            Permission.objects.get(
                content_type__app_label="infrastructure",
                codename="view_infrastructureresource",
            ),
            Permission.objects.get(
                content_type__app_label="credentials",
                codename="view_storedcredential",
            ),
        )

        response = self.client.put(
            f"/api/admin/knowledge-base/documents/{document_id}",
            data={
                "title": "Protected link references",
                "section_id": self.visible_section.id,
                "content": "# Updated without link permissions",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        document = KnowledgeBaseDocument.objects.get(id=document_id)
        self.assertEqual(document.resource_links.count(), 1)
        self.assertEqual(document.credential_links.count(), 1)
        self.assertEqual(response.json()["resources"], [])
        self.assertEqual(response.json()["credentials"], [])
