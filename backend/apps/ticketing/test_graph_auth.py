import base64
import json
from datetime import timedelta
from unittest.mock import Mock

import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.credentials.models import StoredCredential
from apps.credentials.secrets import store_credential_secrets
from apps.ticketing.models import MicrosoftGraphConnection
from apps.ticketing.services.graph_auth import (
    CLIENT_ASSERTION_TYPE,
    GRAPH_SCOPE,
    MicrosoftGraphAuthenticationError,
    MicrosoftGraphTokenProvider,
)


class MicrosoftGraphTokenProviderTests(TestCase):
    def setUp(self) -> None:
        self.encryption_key = base64.urlsafe_b64encode(b"a" * 32).decode("ascii")
        self.credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Graph credential",
        )
        self.session = Mock(spec=requests.Session)

    @staticmethod
    def _token_response(*, status_code: int = 200) -> Mock:
        response = Mock()
        response.status_code = status_code
        response.headers = {}
        response.json.return_value = {
            "access_token": "graph-access-token",
            "expires_in": 3600,
        }
        return response

    def test_client_secret_auth_uses_encrypted_secret_and_caches_token(self) -> None:
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.encryption_key]):
            store_credential_secrets(
                self.credential,
                {"client_secret": "encrypted-client-secret"},
            )
            connection = MicrosoftGraphConnection.objects.create(
                name="Client secret Graph",
                tenant_id="tenant-id",
                client_id="client-id",
                authentication_method=MicrosoftGraphConnection.AuthenticationMethod.CLIENT_SECRET,
                credential=self.credential,
            )
            self.session.post.return_value = self._token_response()
            provider = MicrosoftGraphTokenProvider(connection, session=self.session)

            first = provider.get_access_token()
            second = provider.get_access_token()

        self.assertEqual(first, "graph-access-token")
        self.assertEqual(second, "graph-access-token")
        self.session.post.assert_called_once()
        url, kwargs = self.session.post.call_args
        self.assertEqual(
            url,
            "https://login.microsoftonline.com/tenant-id/oauth2/v2.0/token",
        )
        self.assertEqual(kwargs["data"]["client_id"], "client-id")
        self.assertEqual(kwargs["data"]["client_secret"], "encrypted-client-secret")
        self.assertEqual(kwargs["data"]["scope"], GRAPH_SCOPE)
        self.assertEqual(kwargs["data"]["grant_type"], "client_credentials")
        connection.refresh_from_db()
        self.assertIsNotNone(connection.last_verified_at)
        self.assertEqual(connection.last_error, "")

    def test_certificate_auth_builds_verifiable_ps256_assertion(self) -> None:
        private_key, private_pem, certificate_pem, certificate = self._certificate_material()
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.encryption_key]):
            store_credential_secrets(
                self.credential,
                {
                    "private_key": private_pem,
                    "certificate": certificate_pem,
                    "passphrase": "test-passphrase",
                },
            )
            connection = MicrosoftGraphConnection.objects.create(
                name="Certificate Graph",
                tenant_id="tenant-id",
                client_id="client-id",
                authentication_method=MicrosoftGraphConnection.AuthenticationMethod.CERTIFICATE,
                credential=self.credential,
            )
            self.session.post.return_value = self._token_response()
            provider = MicrosoftGraphTokenProvider(connection, session=self.session)

            token = provider.get_access_token()

        self.assertEqual(token, "graph-access-token")
        url, kwargs = self.session.post.call_args
        data = kwargs["data"]
        self.assertEqual(data["client_assertion_type"], CLIENT_ASSERTION_TYPE)
        self.assertNotIn("client_secret", data)

        assertion = data["client_assertion"]
        encoded_header, encoded_claims, encoded_signature = assertion.split(".")
        header = json.loads(self._base64url_decode(encoded_header))
        claims = json.loads(self._base64url_decode(encoded_claims))
        signature = self._base64url_decode(encoded_signature)
        signing_input = f"{encoded_header}.{encoded_claims}".encode("ascii")

        self.assertEqual(header["alg"], "PS256")
        self.assertEqual(header["typ"], "JWT")
        self.assertEqual(
            header["x5t#S256"],
            self._base64url_encode(certificate.fingerprint(hashes.SHA256())),
        )
        self.assertEqual(claims["aud"], url)
        self.assertEqual(claims["iss"], "client-id")
        self.assertEqual(claims["sub"], "client-id")
        self.assertLessEqual(claims["exp"] - claims["nbf"], 310)
        private_key.public_key().verify(
            signature,
            signing_input,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=hashes.SHA256().digest_size,
            ),
            hashes.SHA256(),
        )

    def test_delegated_auth_is_rejected_for_background_sync(self) -> None:
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.encryption_key]):
            store_credential_secrets(self.credential, {"client_secret": "unused"})
            connection = MicrosoftGraphConnection.objects.create(
                name="Delegated Graph",
                tenant_id="tenant-id",
                client_id="client-id",
                authentication_method=MicrosoftGraphConnection.AuthenticationMethod.DELEGATED,
                credential=self.credential,
            )
            provider = MicrosoftGraphTokenProvider(connection, session=self.session)

            with self.assertRaisesMessage(
                MicrosoftGraphAuthenticationError,
                "Delegated Microsoft Graph authentication is not supported",
            ):
                provider.get_access_token()

        self.session.post.assert_not_called()
        connection.refresh_from_db()
        self.assertIn("Delegated Microsoft Graph authentication", connection.last_error)

    def test_client_owned_credential_is_rejected_even_if_linked_directly(self) -> None:
        client = Client.objects.create(
            name="Client",
            email="client@example.test",
        )
        client_credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=client,
            name="Client credential",
        )
        connection = MicrosoftGraphConnection.objects.create(
            name="Invalid Graph",
            tenant_id="tenant-id",
            client_id="client-id",
            credential=client_credential,
        )
        provider = MicrosoftGraphTokenProvider(connection, session=self.session)

        with self.assertRaisesMessage(
            MicrosoftGraphAuthenticationError,
            "requires an internal credential",
        ):
            provider.get_access_token()

        self.session.post.assert_not_called()

    def test_identity_platform_failure_records_safe_error(self) -> None:
        with override_settings(CREDENTIAL_ENCRYPTION_KEYS=[self.encryption_key]):
            store_credential_secrets(
                self.credential,
                {"client_secret": "must-not-appear-in-errors"},
            )
            connection = MicrosoftGraphConnection.objects.create(
                name="Failing Graph",
                tenant_id="tenant-id",
                client_id="client-id",
                authentication_method=MicrosoftGraphConnection.AuthenticationMethod.CLIENT_SECRET,
                credential=self.credential,
            )
            response = self._token_response(status_code=401)
            response.headers = {"x-ms-request-id": "request-id"}
            self.session.post.return_value = response
            provider = MicrosoftGraphTokenProvider(connection, session=self.session)

            with self.assertRaises(MicrosoftGraphAuthenticationError):
                provider.get_access_token()

        connection.refresh_from_db()
        self.assertIn("status 401", connection.last_error)
        self.assertIn("request-id", connection.last_error)
        self.assertNotIn("must-not-appear-in-errors", connection.last_error)

    @staticmethod
    def _certificate_material() -> tuple[rsa.RSAPrivateKey, str, str, x509.Certificate]:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "ADB Graph Test")])
        now = timezone.now()
        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=30))
            .sign(private_key, hashes.SHA256())
        )
        private_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.BestAvailableEncryption(b"test-passphrase"),
        ).decode("utf-8")
        certificate_pem = certificate.public_bytes(serialization.Encoding.PEM).decode("utf-8")
        return private_key, private_pem, certificate_pem, certificate

    @staticmethod
    def _base64url_decode(value: str) -> bytes:
        padding_length = (-len(value)) % 4
        return base64.urlsafe_b64decode(value + "=" * padding_length)

    @staticmethod
    def _base64url_encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")
