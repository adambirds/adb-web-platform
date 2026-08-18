from unittest.mock import Mock, patch

import requests
from django.test import TestCase

from apps.ticketing.models import MicrosoftGraphConnection
from apps.ticketing.services.graph import (
    GRAPH_API_ROOT,
    MicrosoftGraphError,
    MicrosoftGraphPayloadError,
)
from apps.ticketing.services.mailbox_access import verify_graph_mailbox_access


class GraphMailboxAccessVerificationTests(TestCase):
    def setUp(self) -> None:
        self.connection = MicrosoftGraphConnection.objects.create(
            name="Microsoft 365",
            tenant_id="tenant-id",
            client_id="client-id",
        )
        self.session = Mock(spec=requests.Session)

    @staticmethod
    def _response(payload: object, status_code: int = 200) -> Mock:
        response = Mock()
        response.status_code = status_code
        response.headers = {}
        response.json.return_value = payload
        return response

    @patch("apps.ticketing.services.mailbox_access.MicrosoftGraphTokenProvider")
    def test_verification_uses_mail_folder_access_for_normalised_address(
        self,
        token_provider_class: Mock,
    ) -> None:
        token_provider_class.return_value.get_access_token.return_value = "access-token"
        self.session.get.return_value = self._response({"id": "inbox-folder-id"})

        verify_graph_mailbox_access(
            self.connection,
            " Support@ADB-Test.Example.Test ",
            session=self.session,
            timeout_seconds=5,
        )

        token_provider_class.assert_called_once_with(
            self.connection,
            session=self.session,
            timeout_seconds=5,
        )
        self.session.get.assert_called_once_with(
            f"{GRAPH_API_ROOT}/users/support%40adb-test.example.test/mailFolders/inbox",
            headers={
                "Authorization": "Bearer access-token",
                "Accept": "application/json",
            },
            params={"$select": "id"},
            timeout=5,
        )

    @patch("apps.ticketing.services.mailbox_access.MicrosoftGraphTokenProvider")
    def test_verification_rejects_mailbox_outside_graph_scope(
        self,
        token_provider_class: Mock,
    ) -> None:
        token_provider_class.return_value.get_access_token.return_value = "access-token"
        response = self._response({}, status_code=403)
        response.headers = {"request-id": "request-id"}
        self.session.get.return_value = response

        with self.assertRaisesMessage(
            MicrosoftGraphError,
            "status 403 (request ID request-id)",
        ):
            verify_graph_mailbox_access(
                self.connection,
                "person@example.test",
                session=self.session,
            )

    @patch("apps.ticketing.services.mailbox_access.MicrosoftGraphTokenProvider")
    def test_verification_requires_inbox_folder_response(
        self,
        token_provider_class: Mock,
    ) -> None:
        token_provider_class.return_value.get_access_token.return_value = "access-token"
        self.session.get.return_value = self._response({})

        with self.assertRaisesMessage(
            MicrosoftGraphPayloadError,
            "did not return the Inbox folder",
        ):
            verify_graph_mailbox_access(
                self.connection,
                "support@example.test",
                session=self.session,
            )
