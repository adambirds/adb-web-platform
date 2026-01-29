"""Tests for two-factor authentication TOTP functionality."""

from django.test import TestCase

from authentication.twofactor.totp import (
    generate_secret,
    generate_totp,
    generate_totp_uri,
    verify_totp,
)


class TOTPGenerationTestCase(TestCase):
    """Test TOTP secret and code generation."""

    def test_generate_secret_returns_base32_string(self) -> None:
        """Test that generate_secret returns a valid base32 string."""
        secret = generate_secret()
        # Default is 32 bytes which becomes 52 base32 chars (without padding)
        self.assertGreater(len(secret), 0)
        # Base32 alphabet check
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
        self.assertTrue(all(c in valid_chars for c in secret))

    def test_generate_secret_is_unique(self) -> None:
        """Test that each generated secret is unique."""
        secrets = [generate_secret() for _ in range(10)]
        self.assertEqual(len(secrets), len(set(secrets)))

    def test_generate_totp_uri_format(self) -> None:
        """Test that generate_totp_uri returns properly formatted URI."""
        secret = generate_secret()
        email = "test@example.com"
        issuer = "App"

        uri = generate_totp_uri(secret, email, issuer)

        self.assertTrue(uri.startswith("otpauth://totp/"))
        # Email is URL encoded in the URI
        self.assertIn("test%40example.com", uri)
        self.assertIn(secret.upper(), uri)  # Secret is uppercased
        self.assertIn(issuer, uri)

    def test_generate_totp_returns_6_digit_code(self) -> None:
        """Test that generate_totp returns a 6-digit code."""
        secret = generate_secret()
        code = generate_totp(secret)

        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

    def test_generate_totp_consistent_within_window(self) -> None:
        """Test that generate_totp returns consistent code within time window."""
        secret = generate_secret()
        code1 = generate_totp(secret)
        code2 = generate_totp(secret)

        # Codes generated in quick succession should be the same
        self.assertEqual(code1, code2)


class TOTPVerificationTestCase(TestCase):
    """Test TOTP verification."""

    def test_verify_totp_with_valid_code(self) -> None:
        """Test that verify_totp returns True for a valid code."""
        secret = generate_secret()
        code = generate_totp(secret)

        is_valid = verify_totp(secret, code)
        self.assertTrue(is_valid)

    def test_verify_totp_with_invalid_code(self) -> None:
        """Test that verify_totp returns False for an invalid code."""
        secret = generate_secret()

        is_valid = verify_totp(secret, "000000")
        self.assertFalse(is_valid)

    def test_verify_totp_with_wrong_secret(self) -> None:
        """Test that verify_totp returns False when using wrong secret."""
        secret1 = generate_secret()
        secret2 = generate_secret()
        code = generate_totp(secret1)

        is_valid = verify_totp(secret2, code)
        self.assertFalse(is_valid)

    def test_verify_totp_with_window(self) -> None:
        """Test that verify_totp allows codes within the time window."""
        secret = generate_secret()
        # Generate the code
        code = generate_totp(secret)

        # Should still be valid immediately
        is_valid = verify_totp(secret, code, window=1)
        self.assertTrue(is_valid)

    def test_verify_totp_with_non_numeric_code(self) -> None:
        """Test that verify_totp handles non-numeric codes gracefully."""
        secret = generate_secret()

        is_valid = verify_totp(secret, "abcdef")
        self.assertFalse(is_valid)

    def test_verify_totp_with_short_code(self) -> None:
        """Test that verify_totp handles short codes gracefully."""
        secret = generate_secret()

        is_valid = verify_totp(secret, "123")
        self.assertFalse(is_valid)

    def test_verify_totp_with_long_code(self) -> None:
        """Test that verify_totp handles long codes gracefully."""
        secret = generate_secret()

        is_valid = verify_totp(secret, "12345678")
        self.assertFalse(is_valid)
