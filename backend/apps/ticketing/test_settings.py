from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.clients.models import Client
from apps.core.models import Brand
from apps.core.ownership import OwnershipType
from apps.credentials.models import StoredCredential
from apps.ticketing.models import Mailbox, MicrosoftGraphConnection, TicketQueue
from authentication.models import User


class TicketingSettingsTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="settings@example.test",
            password="not-a-real-password",
            first_name="Settings",
            last_name="Admin",
            is_staff=True,
        )
        self.client.force_login(self.user)
        self.brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="adb-test.example.test",
        )
        self.other_brand = Brand.objects.create(
            name="Other ADB",
            slug="other-adb",
            domain="other-adb.example.test",
        )
        self.queue = TicketQueue.objects.create(
            name="Support",
            key="support",
            brand=self.brand,
        )
        self.other_brand_queue = TicketQueue.objects.create(
            name="Other Support",
            key="other-support",
            brand=self.other_brand,
        )
        self.disabled_queue = TicketQueue.objects.create(
            name="Disabled",
            key="disabled",
            brand=self.brand,
            enabled=False,
        )
        self.client_account = Client.objects.create(
            name="Client",
            email="client@example.test",
        )
        self.internal_credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Graph certificate",
            private_key="test-private-key",
        )
        self.client_credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_account,
            name="Client credential",
            private_key="test-client-private-key",
        )
        self.connection = MicrosoftGraphConnection.objects.create(
            name="Existing Graph application",
            tenant_id="existing-tenant",
            client_id="existing-client",
            credential=self.internal_credential,
        )

    def _grant(self, *codenames: str) -> None:
        permissions = Permission.objects.filter(
            content_type__app_label="ticketing",
            codename__in=codenames,
        )
        self.user.user_permissions.add(*permissions)

    def _graph_payload(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "name": "New Graph application",
            "tenant_id": "new-tenant",
            "client_id": "new-client",
            "authentication_method": MicrosoftGraphConnection.AuthenticationMethod.CERTIFICATE,
            "credential_id": self.internal_credential.id,
            "enabled": True,
        }
        payload.update(overrides)
        return payload

    def _mailbox_payload(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "graph_connection_id": self.connection.id,
            "email_address": "Support@ADB-Test.Example.Test",
            "display_name": "Support",
            "brand_id": self.brand.id,
            "purpose": Mailbox.Purpose.SUPPORT,
            "default_queue_id": self.queue.id,
            "enabled": True,
        }
        payload.update(overrides)
        return payload

    def test_graph_connection_list_requires_view_permission(self) -> None:
        response = self.client.get("/api/admin/settings/ticketing/graph-connections")

        self.assertEqual(response.status_code, 403)

    def test_graph_connection_create_requires_configuration_permission(self) -> None:
        self._grant("view_microsoftgraphconnection")

        response = self.client.post(
            "/api/admin/settings/ticketing/graph-connections",
            data=self._graph_payload(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_graph_connection_accepts_internal_credential(self) -> None:
        self._grant("configure_graph_connections")

        response = self.client.post(
            "/api/admin/settings/ticketing/graph-connections",
            data=self._graph_payload(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        connection = MicrosoftGraphConnection.objects.get(tenant_id="new-tenant")
        self.assertEqual(connection.credential, self.internal_credential)
        self.assertEqual(response.json()["credential_id"], self.internal_credential.id)

    def test_graph_connection_rejects_client_owned_credential(self) -> None:
        self._grant("configure_graph_connections")

        response = self.client.post(
            "/api/admin/settings/ticketing/graph-connections",
            data=self._graph_payload(credential_id=self.client_credential.id),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "invalid_credential_scope")

    def test_graph_connection_rejects_duplicate_tenant_and_client(self) -> None:
        self._grant("configure_graph_connections")

        response = self.client.post(
            "/api/admin/settings/ticketing/graph-connections",
            data=self._graph_payload(
                tenant_id=self.connection.tenant_id,
                client_id=self.connection.client_id,
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "duplicate_connection")

    def test_mailbox_list_requires_view_permission(self) -> None:
        response = self.client.get("/api/admin/settings/ticketing/mailboxes")

        self.assertEqual(response.status_code, 403)

    def test_mailbox_create_requires_configuration_permission(self) -> None:
        self._grant("view_mailbox")

        response = self.client.post(
            "/api/admin/settings/ticketing/mailboxes",
            data=self._mailbox_payload(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_mailbox_create_normalises_email_and_links_routing(self) -> None:
        self._grant("configure_mailboxes")

        response = self.client.post(
            "/api/admin/settings/ticketing/mailboxes",
            data=self._mailbox_payload(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        mailbox = Mailbox.objects.get(graph_connection=self.connection)
        self.assertEqual(mailbox.email_address, "support@adb-test.example.test")
        self.assertEqual(mailbox.brand, self.brand)
        self.assertEqual(mailbox.default_queue, self.queue)

    def test_mailbox_uses_only_enabled_connection_when_not_selected(self) -> None:
        self._grant("configure_mailboxes")
        payload = self._mailbox_payload()
        payload.pop("graph_connection_id")

        response = self.client.post(
            "/api/admin/settings/ticketing/mailboxes",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        mailbox = Mailbox.objects.get(email_address="support@adb-test.example.test")
        self.assertEqual(mailbox.graph_connection, self.connection)

    def test_mailbox_requires_connection_selection_when_multiple_are_enabled(self) -> None:
        self._grant("configure_mailboxes")
        MicrosoftGraphConnection.objects.create(
            name="Second Graph application",
            tenant_id="second-tenant",
            client_id="second-client",
            credential=self.internal_credential,
        )
        payload = self._mailbox_payload()
        payload.pop("graph_connection_id")

        response = self.client.post(
            "/api/admin/settings/ticketing/mailboxes",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "connection_required")

    def test_mailbox_rejects_disabled_graph_connection(self) -> None:
        self._grant("configure_mailboxes")
        self.connection.enabled = False
        self.connection.save(update_fields=["enabled"])

        response = self.client.post(
            "/api/admin/settings/ticketing/mailboxes",
            data=self._mailbox_payload(),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "connection_disabled")

    def test_mailbox_rejects_queue_from_another_brand(self) -> None:
        self._grant("configure_mailboxes")

        response = self.client.post(
            "/api/admin/settings/ticketing/mailboxes",
            data=self._mailbox_payload(default_queue_id=self.other_brand_queue.id),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "queue_brand_mismatch")

    def test_mailbox_rejects_disabled_queue(self) -> None:
        self._grant("configure_mailboxes")

        response = self.client.post(
            "/api/admin/settings/ticketing/mailboxes",
            data=self._mailbox_payload(default_queue_id=self.disabled_queue.id),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "queue_not_found")

    def test_mailbox_rejects_case_insensitive_duplicate(self) -> None:
        self._grant("configure_mailboxes")
        Mailbox.objects.create(
            graph_connection=self.connection,
            email_address="support@adb-test.example.test",
            brand=self.brand,
            purpose=Mailbox.Purpose.SUPPORT,
            default_queue=self.queue,
        )

        response = self.client.post(
            "/api/admin/settings/ticketing/mailboxes",
            data=self._mailbox_payload(email_address="SUPPORT@ADB-TEST.EXAMPLE.TEST"),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "duplicate_mailbox")
