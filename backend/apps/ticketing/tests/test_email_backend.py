from __future__ import annotations

import base64
from email import policy
from email.parser import BytesParser
from unittest.mock import Mock, patch

import requests
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage, EmailMultiAlternatives, send_mail
from django.test import SimpleTestCase, TestCase, override_settings

from apps.ticketing.email_backend import MicrosoftGraphEmailBackend
from apps.ticketing.models import Mailbox, MicrosoftGraphConnection, Ticket
from apps.ticketing.services.graph import MicrosoftGraphError
from apps.ticketing.tests import test_graph_auth as graph_auth_tests

BACKEND = "apps.ticketing.email_backend.MicrosoftGraphEmailBackend"
SENDER = "no-reply@adbsoftwaresolutions.co.uk"


@override_settings(EMAIL_BACKEND=BACKEND, DEFAULT_FROM_EMAIL=SENDER)
class GraphEmailBackendTests(SimpleTestCase):
    def setUp(self) -> None:
        self.session = Mock()
        self.session.post.return_value = Mock(status_code=202)
        session_patch = patch(
            "apps.ticketing.email_backend.requests.Session", return_value=self.session
        )
        session_patch.start()
        self.addCleanup(session_patch.stop)
        connection_patch = patch(
            "apps.ticketing.email_backend.environment_graph_connection",
            return_value=Mock(enabled=True),
        )
        self.connection = connection_patch.start()
        self.addCleanup(connection_patch.stop)
        provider_patch = patch("apps.ticketing.email_backend.MicrosoftGraphTokenProvider")
        provider = provider_patch.start()
        provider.return_value.get_access_token.return_value = "graph-access-token"
        self.addCleanup(provider_patch.stop)

    def test_django_send_mail_uses_shared_graph_connection_and_mime(self) -> None:
        self.assertEqual(
            send_mail(
                "Verify account", "Follow this private link", None, ["recipient@example.test"]
            ),
            1,
        )
        self.connection.assert_called_once()
        call = self.session.post.call_args
        self.assertEqual(
            call.args[0],
            "https://graph.microsoft.com/v1.0/users/no-reply%40adbsoftwaresolutions.co.uk/sendMail",
        )
        self.assertEqual(
            call.kwargs["headers"],
            {"Authorization": "Bearer graph-access-token", "Content-Type": "text/plain"},
        )
        self.assertEqual(call.kwargs["timeout"], 30)
        mime = BytesParser(policy=policy.default).parsebytes(base64.b64decode(call.kwargs["data"]))
        self.assertEqual(str(mime["From"]), SENDER)
        self.assertEqual(str(mime["To"]), "recipient@example.test")
        self.assertEqual(str(mime["Subject"]), "Verify account")
        self.assertIn("Follow this private link", mime.get_content())
        self.session.close.assert_called_once()

    def test_preserves_html_text_cc_bcc_reply_to_and_attachments(self) -> None:
        email = EmailMultiAlternatives(
            "Unicode ✓",
            "plain body",
            SENDER,
            ["to@example.test"],
            cc=["cc@example.test"],
            bcc=["bcc@example.test"],
            reply_to=["reply@example.test"],
        )
        email.attach_alternative("<p>HTML body</p>", "text/html")
        email.attach("file.txt", "attachment", "text/plain")
        backend = MicrosoftGraphEmailBackend()
        self.assertEqual(backend.send_messages([email]), 1)
        mime = BytesParser(policy=policy.default).parsebytes(
            base64.b64decode(self.session.post.call_args.kwargs["data"])
        )
        self.assertEqual(str(mime["Cc"]), "cc@example.test")
        self.assertEqual(str(mime["Bcc"]), "bcc@example.test")
        self.assertEqual(str(mime["Reply-To"]), "reply@example.test")
        self.assertEqual(str(mime["Subject"]), "Unicode ✓")
        plain = mime.get_body(preferencelist=("plain",))
        html = mime.get_body(preferencelist=("html",))
        assert plain is not None
        assert html is not None
        self.assertIn("plain body", plain.get_content())
        self.assertIn("HTML body", html.get_content())
        self.assertEqual(next(mime.iter_attachments()).get_filename(), "file.txt")

    def test_empty_recipient_lists_do_not_open_or_send(self) -> None:
        self.assertEqual(
            MicrosoftGraphEmailBackend().send_messages(
                [EmailMessage("No recipients", "body", SENDER)]
            ),
            0,
        )
        self.connection.assert_not_called()
        self.session.post.assert_not_called()

    def test_graph_rejection_is_safe_and_fail_silently_is_respected(self) -> None:
        self.session.post.return_value = Mock(status_code=403, text="secret body / reset token")
        email = EmailMessage("Reset", "private reset token", SENDER, ["to@example.test"])
        with self.assertRaisesMessage(MicrosoftGraphError, "status 403") as error:
            MicrosoftGraphEmailBackend().send_messages([email])
        self.assertNotIn("private", str(error.exception))
        self.assertEqual(MicrosoftGraphEmailBackend(fail_silently=True).send_messages([email]), 0)

    def test_network_errors_are_wrapped_without_exposing_token_or_body(self) -> None:
        self.session.post.side_effect = requests.ConnectionError("token / confidential body")
        with self.assertRaisesMessage(
            MicrosoftGraphError, "application email request failed"
        ) as error:
            send_mail("subject", "confidential body", SENDER, ["to@example.test"])
        self.assertNotIn("confidential", str(error.exception))

    def test_missing_or_disabled_graph_connection_fails_closed(self) -> None:
        for connection in [None, Mock(enabled=False)]:
            self.connection.return_value = connection
            with self.assertRaises(ImproperlyConfigured):
                send_mail("subject", "body", SENDER, ["to@example.test"])
            self.assertEqual(
                send_mail("subject", "body", SENDER, ["to@example.test"], fail_silently=True), 0
            )
        self.session.post.assert_not_called()

    def test_arbitrary_sender_is_rejected_before_graph_request(self) -> None:
        with self.assertRaisesMessage(MicrosoftGraphError, "DEFAULT_FROM_EMAIL"):
            send_mail("subject", "body", "another@example.test", ["to@example.test"])
        self.session.post.assert_not_called()

    def test_extra_headers_cannot_override_sender_or_recipient_lists(self) -> None:
        email = EmailMessage(
            "subject",
            "body",
            SENDER,
            ["real@example.test"],
            headers={
                "From": "spoof@example.test",
                "To": "injected@example.test",
                "Bcc": "injected@example.test",
                "Sender": "spoof@example.test",
            },
        )
        MicrosoftGraphEmailBackend().send_messages([email])
        mime = BytesParser(policy=policy.default).parsebytes(
            base64.b64decode(self.session.post.call_args.kwargs["data"])
        )
        self.assertEqual(str(mime["From"]), SENDER)
        self.assertEqual(str(mime["To"]), "real@example.test")
        self.assertIsNone(mime["Bcc"])
        self.assertIsNone(mime["Sender"])

    def test_batch_counts_only_accepted_messages_and_reuses_session(self) -> None:
        self.session.post.side_effect = [
            Mock(status_code=202),
            Mock(status_code=429),
            Mock(status_code=202),
        ]
        emails = [EmailMessage("subject", "body", SENDER, ["to@example.test"]) for _ in range(3)]
        self.assertEqual(MicrosoftGraphEmailBackend(fail_silently=True).send_messages(emails), 2)
        self.connection.assert_called_once()
        self.session.close.assert_called_once()


@override_settings(EMAIL_BACKEND=BACKEND, DEFAULT_FROM_EMAIL=SENDER)
class GraphEmailAuthenticationIntegrationTests(TestCase):
    def test_uses_infisical_auth_without_ticket_mailbox_or_secret_persistence(self) -> None:
        _, private_pem, certificate_pem, _ = (
            graph_auth_tests.MicrosoftGraphTokenProviderTests._certificate_material()
        )
        environment = {
            "MICROSOFT_GRAPH_TENANT_ID": "11111111-1111-1111-1111-111111111111",
            "MICROSOFT_GRAPH_CLIENT_ID": "22222222-2222-2222-2222-222222222222",
            "MICROSOFT_GRAPH_PRIVATE_KEY": private_pem,
            "MICROSOFT_GRAPH_CERTIFICATE": certificate_pem,
            "MICROSOFT_GRAPH_PRIVATE_KEY_PASSPHRASE": "test-passphrase",
        }
        session = Mock()
        token_response = Mock(status_code=200)
        token_response.json.return_value = {"access_token": "access-token", "expires_in": 3600}
        session.post.side_effect = [token_response, Mock(status_code=202)]
        with (
            patch.dict("os.environ", environment),
            patch("apps.ticketing.email_backend.requests.Session", return_value=session),
            patch(
                "apps.ticketing.services.graph_auth.load_credential_secrets_for_service"
            ) as vault,
        ):
            self.assertEqual(
                send_mail("Verify", "private account link", SENDER, ["user@example.test"]), 1
            )
        vault.assert_not_called()
        self.assertEqual(session.post.call_count, 2)
        self.assertFalse(Mailbox.objects.exists())
        self.assertFalse(Ticket.objects.exists())
        connection = MicrosoftGraphConnection.objects.get()
        self.assertEqual(connection.authentication_method, "environment_certificate")
        self.assertIsNone(connection.credential_id)
        self.assertNotIn("private account link", str(connection.__dict__))
