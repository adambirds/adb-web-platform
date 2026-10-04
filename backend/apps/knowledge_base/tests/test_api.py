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

        response = self.client.get(
            f"/api/admin/knowledge-base/workspace?client_id={self.visible_client.id}"
        )
        hidden_filter = self.client.get(
            f"/api/admin/knowledge-base/workspace?client_id={self.hidden_client.id}"
        )

        self.assertEqual(response.status_code, 200)
        ids = {document["id"] for document in response.json()["documents"]}
        self.assertEqual(ids, {self.visible_document.id})
        self.assertNotIn(self.hidden_document.id, ids)
        self.assertEqual(hidden_filter.status_code, 404)

    def test_workspace_search_and_archive_views_are_server_side(self) -> None:
        self.grant(
            ("knowledge_base", "view_knowledgebasedocument"),
            ("knowledge_base", "change_knowledgebasedocument"),
        )

        search = self.client.get(
            "/api/admin/knowledge-base/workspace?ownership_type=internal&q=deployment"
        )
        archive = self.client.post(
            f"/api/admin/knowledge-base/documents/{self.internal_document.id}/archive"
        )
        current = self.client.get(
            "/api/admin/knowledge-base/workspace?ownership_type=internal&view=current"
        )
        archived = self.client.get(
            "/api/admin/knowledge-base/workspace?ownership_type=internal&view=archived"
        )

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

    def test_read_collections_require_a_single_context(self) -> None:
        self.grant(("knowledge_base", "view_knowledgebasedocument"))
        for endpoint in ("workspace", "options"):
            for query in (
                "",
                "?ownership_type=client",
                "?ownership_type=all",
                f"?ownership_type=internal&client_id={self.visible_client.id}",
            ):
                with self.subTest(endpoint=endpoint, query=query):
                    self.assertEqual(
                        self.client.get(f"/api/admin/knowledge-base/{endpoint}{query}").status_code,
                        400,
                    )
            self.assertEqual(
                self.client.get(
                    f"/api/admin/knowledge-base/{endpoint}?client_id={self.hidden_client.id}"
                ).status_code,
                404,
            )

    def test_client_picker_is_scoped_searchable_and_paginated(self) -> None:
        self.grant(("knowledge_base", "view_knowledgebasedocument"))
        result = self.client.get("/api/admin/knowledge-base/contexts?page_size=1")
        self.assertEqual(result.status_code, 200)
        self.assertEqual([item["id"] for item in result.json()["items"]], [self.visible_client.id])
        self.assertEqual(result.json()["total"], 1)
        self.assertNotIn("sections", result.json())
        self.assertEqual(
            self.client.get("/api/admin/knowledge-base/contexts?q=Hidden").json()["items"], []
        )
        self.assertEqual(
            self.client.get("/api/admin/knowledge-base/contexts?page=2&page_size=1").json()[
                "items"
            ],
            [],
        )

    def test_independent_trees_for_two_accessible_clients_and_internal(self) -> None:
        self.grant(
            ("knowledge_base", "view_knowledgebasedocument"),
            ("knowledge_base", "add_knowledgebasesection"),
        )
        profile = StaffAccessProfile.objects.get(user=self.staff)
        ClientAccessGrant.objects.create(profile=profile, client=self.hidden_client)
        sections = []
        for ownership, client_id in (
            ("internal", None),
            ("client", self.visible_client.id),
            ("client", self.hidden_client.id),
        ):
            result = self.client.post(
                "/api/admin/knowledge-base/sections",
                data={"ownership_type": ownership, "client_id": client_id, "name": "Runbooks"},
                content_type="application/json",
            )
            self.assertEqual(result.status_code, 201)
            sections.append(result.json()["id"])
        self.assertEqual(len(set(sections)), 3)
        for index, query in enumerate(
            (
                "ownership_type=internal",
                f"client_id={self.visible_client.id}",
                f"client_id={self.hidden_client.id}",
            )
        ):
            for endpoint in ("workspace", "options"):
                result = self.client.get(f"/api/admin/knowledge-base/{endpoint}?{query}")
                ids = {section["id"] for section in result.json()["sections"]}
                self.assertIn(sections[index], ids)
                self.assertTrue(set(sections).difference({sections[index]}).isdisjoint(ids))
        mismatch = self.client.get(
            f"/api/admin/knowledge-base/workspace?client_id={self.visible_client.id}&section_id={sections[2]}"
        )
        self.assertEqual(mismatch.status_code, 404)

    def test_options_scope_link_choices_before_returning_them(self) -> None:
        self.grant(
            ("knowledge_base", "view_knowledgebasedocument"),
            ("infrastructure", "view_infrastructureresource"),
            ("credentials", "view_storedcredential"),
        )
        ClientAccessGrant.objects.create(
            profile=StaffAccessProfile.objects.get(user=self.staff), client=self.hidden_client
        )
        result = self.client.get(
            f"/api/admin/knowledge-base/options?client_id={self.visible_client.id}"
        )
        self.assertEqual(
            [item["id"] for item in result.json()["resources"]], [self.visible_resource.id]
        )
        self.assertEqual(
            [item["id"] for item in result.json()["credentials"]], [self.visible_credential.id]
        )
        internal = self.client.get("/api/admin/knowledge-base/options?ownership_type=internal")
        self.assertEqual(internal.json()["resources"], [])
        self.assertEqual(internal.json()["credentials"], [])
        self.assertEqual(
            [section["id"] for section in internal.json()["sections"]], [self.internal_section.id]
        )

    def test_resource_context_infers_owner_and_rejects_mismatches(self) -> None:
        self.grant(("knowledge_base", "view_knowledgebasedocument"))
        url = f"/api/admin/knowledge-base/workspace?resource_id={self.visible_resource.id}"
        self.assertEqual(self.client.get(url).status_code, 403)
        self.grant(("infrastructure", "view_infrastructureresource"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["client_id"], self.visible_client.id)
        self.assertEqual([s["id"] for s in response.json()["sections"]], [self.visible_section.id])
        self.assertEqual(self.client.get(url + "&ownership_type=internal").status_code, 400)
        self.assertEqual(
            self.client.get(
                f"/api/admin/knowledge-base/workspace?resource_id={self.hidden_resource.id}"
            ).status_code,
            404,
        )

    def test_cross_context_parent_and_document_folder_writes_are_rejected(self) -> None:
        self.grant(
            ("knowledge_base", "add_knowledgebasesection"),
            ("knowledge_base", "add_knowledgebasedocument"),
        )
        folder = self.client.post(
            "/api/admin/knowledge-base/sections",
            data={
                "ownership_type": "client",
                "client_id": self.visible_client.id,
                "parent_id": self.internal_section.id,
                "name": "Invalid child",
            },
            content_type="application/json",
        )
        self.assertEqual(folder.status_code, 404)
        article = self.client.post(
            "/api/admin/knowledge-base/documents",
            data={
                "ownership_type": "client",
                "client_id": self.visible_client.id,
                "section_id": self.internal_section.id,
                "title": "Invalid article",
            },
            content_type="application/json",
        )
        self.assertEqual(article.status_code, 404)
        self.assertFalse(KnowledgeBaseSection.objects.filter(name="Invalid child").exists())
        self.assertFalse(KnowledgeBaseDocument.objects.filter(title="Invalid article").exists())

    def test_context_reads_require_staff_and_document_view_capability(self) -> None:
        for endpoint in (
            "contexts",
            "workspace?ownership_type=internal",
            "options?ownership_type=internal",
        ):
            self.assertEqual(
                self.client.get(f"/api/admin/knowledge-base/{endpoint}").status_code, 403
            )
        self.grant(("knowledge_base", "view_knowledgebasedocument"))
        self.staff.is_staff = False
        self.staff.save(update_fields=["is_staff"])
        self.assertEqual(self.client.get("/api/admin/knowledge-base/contexts").status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get("/api/admin/knowledge-base/contexts").status_code, 401)

    def test_directory_browsing_returns_only_articles_directly_in_the_open_folder(self) -> None:
        self.grant(("knowledge_base", "view_knowledgebasedocument"))
        child = KnowledgeBaseSection.objects.create(
            ownership_type="client",
            client=self.visible_client,
            parent=self.visible_section,
            name="Child",
        )
        nested_document = create_document(
            write=DocumentWrite(
                ownership_type="client",
                client_id=self.visible_client.id,
                title="Nested runbook",
                summary="",
                section=child,
                content="# Nested",
            ),
            editor=self.staff,
        )
        root = self.client.get(
            f"/api/admin/knowledge-base/workspace?client_id={self.visible_client.id}&browse=true"
        )
        self.assertEqual(root.status_code, 200)
        self.assertEqual(root.json()["documents"], [])
        direct = self.client.get(
            f"/api/admin/knowledge-base/workspace?client_id={self.visible_client.id}&browse=true&section_id={self.visible_section.id}"
        )
        self.assertEqual([d["id"] for d in direct.json()["documents"]], [self.visible_document.id])
        nested = self.client.get(
            f"/api/admin/knowledge-base/workspace?client_id={self.visible_client.id}&browse=true&section_id={child.id}"
        )
        self.assertEqual([d["id"] for d in nested.json()["documents"]], [nested_document.id])
        panel = self.client.get(
            f"/api/admin/knowledge-base/workspace?client_id={self.visible_client.id}"
        )
        self.assertEqual(panel.json()["total_documents"], 2)
        hidden = self.client.get(
            f"/api/admin/knowledge-base/workspace?client_id={self.visible_client.id}&browse=true&section_id={self.hidden_section.id}"
        )
        self.assertEqual(hidden.status_code, 404)

    def test_directory_search_includes_descendants_and_excludes_siblings_and_other_clients(
        self,
    ) -> None:
        self.grant(("knowledge_base", "view_knowledgebasedocument"))
        child = KnowledgeBaseSection.objects.create(
            ownership_type="client",
            client=self.visible_client,
            parent=self.visible_section,
            name="Child",
        )
        child_document = create_document(
            write=DocumentWrite(
                ownership_type="client",
                client_id=self.visible_client.id,
                title="Nested runbook",
                summary="",
                section=child,
                content="# Nested",
            ),
            editor=self.staff,
        )
        sibling = KnowledgeBaseSection.objects.create(
            ownership_type="client", client=self.visible_client, name="Sibling"
        )
        sibling_document = create_document(
            write=DocumentWrite(
                ownership_type="client",
                client_id=self.visible_client.id,
                title="Sibling runbook",
                summary="",
                section=sibling,
                content="# Sibling",
            ),
            editor=self.staff,
        )
        ClientAccessGrant.objects.create(
            profile=StaffAccessProfile.objects.get(user=self.staff), client=self.hidden_client
        )
        query = f"/api/admin/knowledge-base/workspace?client_id={self.visible_client.id}&browse=true&q=runbook"
        root = self.client.get(query)
        self.assertEqual(
            {d["id"] for d in root.json()["documents"]},
            {self.visible_document.id, child_document.id, sibling_document.id},
        )
        folder = self.client.get(query + f"&section_id={self.visible_section.id}")
        self.assertEqual(
            {d["id"] for d in folder.json()["documents"]},
            {self.visible_document.id, child_document.id},
        )
        self.assertNotIn(self.hidden_document.id, {d["id"] for d in folder.json()["documents"]})
