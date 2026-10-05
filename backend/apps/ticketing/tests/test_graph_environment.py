from __future__ import annotations

from unittest.mock import Mock, patch

from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.core.models import AuditEvent
from apps.ticketing.models import MicrosoftGraphConnection
from apps.ticketing.services.graph_auth import (
    MicrosoftGraphAuthenticationError,
    MicrosoftGraphTokenProvider,
    environment_graph_connection,
)
from apps.ticketing.tests import test_graph_auth as graph_auth_tests
from authentication.models import User


class GraphEnvironmentTests(TestCase):
    def setUp(self) -> None:
        _, private_pem, certificate_pem, _ = (
            graph_auth_tests.MicrosoftGraphTokenProviderTests._certificate_material()
        )
        self.environment = {
            "MICROSOFT_GRAPH_TENANT_ID": "11111111-1111-1111-1111-111111111111",
            "MICROSOFT_GRAPH_CLIENT_ID": "22222222-2222-2222-2222-222222222222",
            "MICROSOFT_GRAPH_PRIVATE_KEY": private_pem,
            "MICROSOFT_GRAPH_CERTIFICATE": certificate_pem,
            "MICROSOFT_GRAPH_PRIVATE_KEY_PASSPHRASE": "test-passphrase",
        }

    def discover(self) -> MicrosoftGraphConnection | None:
        with patch.dict("os.environ", self.environment):
            return environment_graph_connection()

    def test_creates_only_routing_record_without_persisting_configuration(self) -> None:
        self.discover()
        self.discover()
        self.assertEqual(MicrosoftGraphConnection.objects.count(), 1)
        connection = MicrosoftGraphConnection.objects.get()
        self.assertIsNone(connection.credential_id)
        self.assertEqual(connection.authentication_method, "environment_certificate")
        self.assertEqual(connection.tenant_id, "environment")
        self.assertEqual(connection.client_id, "environment")
        self.assertEqual(
            AuditEvent.objects.filter(
                action="ticketing.graph_connection.environment_discovered"
            ).count(),
            1,
        )

    def test_rerun_does_not_reenable_disabled_connection(self) -> None:
        self.discover()
        connection = MicrosoftGraphConnection.objects.get()
        connection.enabled = False
        connection.save()
        self.discover()
        connection.refresh_from_db()
        self.assertFalse(connection.enabled)

    def test_rejects_missing_configuration_without_creating_connection(self) -> None:
        self.environment["MICROSOFT_GRAPH_PRIVATE_KEY"] = ""
        with self.assertRaisesMessage(
            MicrosoftGraphAuthenticationError, "MICROSOFT_GRAPH_PRIVATE_KEY"
        ):
            self.discover()
        self.assertFalse(MicrosoftGraphConnection.objects.exists())

    def test_rejects_invalid_certificate_without_persisting_it(self) -> None:
        self.environment["MICROSOFT_GRAPH_CERTIFICATE"] = "invalid-certificate"
        with self.assertRaisesMessage(MicrosoftGraphAuthenticationError, "invalid PEM"):
            self.discover()
        self.assertFalse(MicrosoftGraphConnection.objects.exists())

    def test_tokens_use_current_environment_without_vault_decryption(self) -> None:
        self.discover()
        connection = MicrosoftGraphConnection.objects.get()
        response = Mock(status_code=200)
        response.json.return_value = {"access_token": "token", "expires_in": 3600}
        session = Mock()
        session.post.return_value = response
        self.environment["MICROSOFT_GRAPH_CLIENT_ID"] = "33333333-3333-3333-3333-333333333333"
        with (
            patch.dict("os.environ", self.environment),
            patch(
                "apps.ticketing.services.graph_auth.load_credential_secrets_for_service"
            ) as decrypt,
        ):
            self.assertEqual(
                MicrosoftGraphTokenProvider(connection, session=session).get_access_token(), "token"
            )
            decrypt.assert_not_called()
        self.assertEqual(
            session.post.call_args.kwargs["data"]["client_id"],
            self.environment["MICROSOFT_GRAPH_CLIENT_ID"],
        )
        connection.refresh_from_db()
        self.assertEqual(connection.client_id, "environment")

    def test_accepts_escaped_newlines_for_dotenv_secrets(self) -> None:
        self.environment["MICROSOFT_GRAPH_PRIVATE_KEY"] = self.environment[
            "MICROSOFT_GRAPH_PRIVATE_KEY"
        ].replace("\n", "\\n")
        self.environment["MICROSOFT_GRAPH_CERTIFICATE"] = self.environment[
            "MICROSOFT_GRAPH_CERTIFICATE"
        ].replace("\n", "\\n")
        self.discover()
        self.assertEqual(MicrosoftGraphConnection.objects.count(), 1)

    def test_rejects_mismatched_certificate_and_private_key(self) -> None:
        _, _, different_certificate, _ = (
            graph_auth_tests.MicrosoftGraphTokenProviderTests._certificate_material()
        )
        self.environment["MICROSOFT_GRAPH_CERTIFICATE"] = different_certificate
        with self.assertRaisesMessage(MicrosoftGraphAuthenticationError, "does not match"):
            self.discover()
        self.assertFalse(MicrosoftGraphConnection.objects.exists())

    def test_settings_discovers_environment_connection_without_setup_action(self) -> None:
        user = User.objects.create_user(
            email="graph-view@example.test",
            password="test",
            first_name="Graph",
            last_name="Viewer",
            is_staff=True,
        )
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="ticketing", codename="view_microsoftgraphconnection"
            )
        )
        self.client.force_login(user)
        with patch.dict("os.environ", self.environment):
            response = self.client.get("/api/admin/settings/ticketing/graph-connections")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["authentication_method"], "environment_certificate")
        self.assertIsNone(response.json()[0]["credential_id"])
        self.assertNotIn(self.environment["MICROSOFT_GRAPH_CLIENT_ID"], response.content.decode())
        self.assertNotIn("BEGIN", response.content.decode())

    def test_settings_permission_checked_before_environment_discovery(self) -> None:
        user = User.objects.create_user(
            email="graph-denied@example.test",
            password="test",
            first_name="Graph",
            last_name="Denied",
            is_staff=True,
        )
        self.client.force_login(user)
        with patch.dict("os.environ", self.environment):
            response = self.client.get("/api/admin/settings/ticketing/graph-connections")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(MicrosoftGraphConnection.objects.exists())
