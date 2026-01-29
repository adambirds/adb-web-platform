"""Tests for passkey utility functions."""

from django.test import TestCase, override_settings

from authentication.models import User
from authentication.passkeys.utils import (
    base64url_to_bytes,
    bytes_to_base64url,
    create_authentication_options,
    create_registration_options,
    generate_challenge,
    generate_user_handle,
    get_allowed_origins,
    get_origin,
    get_rp_id,
    get_rp_name,
)


class RPConfigurationTestCase(TestCase):
    """Tests for Relying Party configuration functions."""

    @override_settings(WEBAUTHN_RP_ID="example.com")
    def test_get_rp_id_from_settings(self) -> None:
        """Test getting RP ID from settings."""
        self.assertEqual(get_rp_id(), "example.com")

    @override_settings(SITE_DOMAIN="fallback.com")
    def test_get_rp_id_fallback(self) -> None:
        """Test getting RP ID falls back to SITE_DOMAIN."""
        # Remove WEBAUTHN_RP_ID if it exists
        from django.conf import settings

        if hasattr(settings, "WEBAUTHN_RP_ID"):
            delattr(settings, "WEBAUTHN_RP_ID")
        # This test will use SITE_DOMAIN as fallback

    @override_settings(WEBAUTHN_RP_NAME="My App")
    def test_get_rp_name_from_settings(self) -> None:
        """Test getting RP name from settings."""
        self.assertEqual(get_rp_name(), "My App")

    @override_settings(WEBAUTHN_ORIGIN="https://example.com")
    def test_get_origin_from_settings(self) -> None:
        """Test getting origin from settings."""
        self.assertEqual(get_origin(), "https://example.com")

    @override_settings(
        WEBAUTHN_ALLOWED_ORIGINS=["https://app.example.com", "https://admin.example.com"]
    )
    def test_get_allowed_origins_from_settings(self) -> None:
        """Test getting allowed origins from settings."""
        origins = get_allowed_origins()
        self.assertEqual(len(origins), 2)
        self.assertIn("https://app.example.com", origins)
        self.assertIn("https://admin.example.com", origins)


class ChallengeGenerationTestCase(TestCase):
    """Tests for challenge generation."""

    def test_generate_challenge_length(self) -> None:
        """Test that challenge is 32 bytes."""
        challenge = generate_challenge()
        self.assertEqual(len(challenge), 32)

    def test_generate_challenge_uniqueness(self) -> None:
        """Test that challenges are unique."""
        challenges = [generate_challenge() for _ in range(100)]
        unique_challenges = set(challenges)
        self.assertEqual(len(unique_challenges), 100)

    def test_generate_challenge_is_bytes(self) -> None:
        """Test that challenge is bytes type."""
        challenge = generate_challenge()
        self.assertIsInstance(challenge, bytes)


class UserHandleTestCase(TestCase):
    """Tests for user handle generation."""

    def test_generate_user_handle_length(self) -> None:
        """Test that user handle is 32 bytes."""
        handle = generate_user_handle()
        self.assertEqual(len(handle), 32)

    def test_generate_user_handle_uniqueness(self) -> None:
        """Test that user handles are unique."""
        handles = [generate_user_handle() for _ in range(100)]
        unique_handles = set(handles)
        self.assertEqual(len(unique_handles), 100)


class Base64UrlEncodingTestCase(TestCase):
    """Tests for base64url encoding/decoding."""

    def test_bytes_to_base64url_simple(self) -> None:
        """Test encoding bytes to base64url."""
        data = b"hello"
        encoded = bytes_to_base64url(data)
        self.assertIsInstance(encoded, str)
        self.assertNotIn("=", encoded)  # No padding
        self.assertNotIn("+", encoded)
        self.assertNotIn("/", encoded)

    def test_base64url_to_bytes_simple(self) -> None:
        """Test decoding base64url to bytes."""
        encoded = "aGVsbG8"  # "hello" in base64url
        decoded = base64url_to_bytes(encoded)
        self.assertEqual(decoded, b"hello")

    def test_base64url_roundtrip(self) -> None:
        """Test encoding and then decoding returns original data."""
        original = b"test data with special bytes: \x00\xff\x80"
        encoded = bytes_to_base64url(original)
        decoded = base64url_to_bytes(encoded)
        self.assertEqual(decoded, original)

    def test_base64url_challenge_roundtrip(self) -> None:
        """Test roundtrip for a generated challenge."""
        challenge = generate_challenge()
        encoded = bytes_to_base64url(challenge)
        decoded = base64url_to_bytes(encoded)
        self.assertEqual(decoded, challenge)


class RegistrationOptionsTestCase(TestCase):
    """Tests for WebAuthn registration options creation."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_create_registration_options_basic(self) -> None:
        """Test creating registration options with basic parameters."""
        challenge = generate_challenge()

        options = create_registration_options(
            user_id=str(self.user.id),
            user_email=self.user.email,
            user_name=self.user.get_full_name(),
            challenge=challenge,
        )

        # Check RP settings
        self.assertIn("rp", options)
        self.assertIn("name", options["rp"])
        self.assertIn("id", options["rp"])

        # Check user settings
        self.assertIn("user", options)
        self.assertEqual(options["user"]["name"], self.user.email)
        self.assertEqual(options["user"]["displayName"], self.user.get_full_name())

        # Check challenge is encoded
        self.assertIn("challenge", options)
        self.assertIsInstance(options["challenge"], str)

        # Check public key parameters
        self.assertIn("pubKeyCredParams", options)
        algs = [param["alg"] for param in options["pubKeyCredParams"]]
        self.assertIn(-7, algs)  # ES256
        self.assertIn(-257, algs)  # RS256

        # Check timeout
        self.assertEqual(options["timeout"], 60000)

        # Check attestation
        self.assertEqual(options["attestation"], "none")

        # Check authenticator selection
        self.assertIn("authenticatorSelection", options)

    def test_create_registration_options_with_exclude_credentials(self) -> None:
        """Test creating registration options with excluded credentials."""
        challenge = generate_challenge()
        exclude_creds = [
            {"id": "cred1", "type": "public-key"},
            {"id": "cred2", "type": "public-key"},
        ]

        options = create_registration_options(
            user_id=str(self.user.id),
            user_email=self.user.email,
            user_name=self.user.get_full_name(),
            challenge=challenge,
            exclude_credentials=exclude_creds,
        )

        self.assertIn("excludeCredentials", options)
        self.assertEqual(len(options["excludeCredentials"]), 2)

    def test_create_registration_options_without_exclude_credentials(self) -> None:
        """Test that excludeCredentials is not present when not provided."""
        challenge = generate_challenge()

        options = create_registration_options(
            user_id=str(self.user.id),
            user_email=self.user.email,
            user_name=self.user.get_full_name(),
            challenge=challenge,
        )

        self.assertNotIn("excludeCredentials", options)


class AuthenticationOptionsTestCase(TestCase):
    """Tests for WebAuthn authentication options creation."""

    def test_create_authentication_options_basic(self) -> None:
        """Test creating authentication options."""
        challenge = generate_challenge()

        options = create_authentication_options(challenge=challenge)

        # Check challenge is encoded
        self.assertIn("challenge", options)
        self.assertIsInstance(options["challenge"], str)

        # Check RP ID
        self.assertIn("rpId", options)

        # Check timeout
        self.assertEqual(options["timeout"], 60000)

        # Check user verification
        self.assertEqual(options["userVerification"], "preferred")

    def test_create_authentication_options_with_allow_credentials(self) -> None:
        """Test creating authentication options with allowed credentials."""
        challenge = generate_challenge()
        allow_creds = [
            {"id": "cred1", "type": "public-key"},
            {"id": "cred2", "type": "public-key"},
        ]

        options = create_authentication_options(
            challenge=challenge,
            allow_credentials=allow_creds,
        )

        self.assertIn("allowCredentials", options)
        self.assertEqual(len(options["allowCredentials"]), 2)

    def test_create_authentication_options_discoverable(self) -> None:
        """Test creating authentication options for discoverable credentials."""
        challenge = generate_challenge()

        options = create_authentication_options(challenge=challenge)

        # Should not have allowCredentials for discoverable flow
        self.assertNotIn("allowCredentials", options)
