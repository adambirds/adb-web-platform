"""Tests for two-factor authentication models."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from authentication.models import User
from authentication.twofactor.models import RecoveryCode, TwoFactorChallenge, TwoFactorMethod
from authentication.twofactor.totp import generate_secret


class TwoFactorMethodModelTestCase(TestCase):
    """Tests for TwoFactorMethod model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_create_totp_method(self) -> None:
        """Test creating a TOTP method."""
        secret = generate_secret()
        method = TwoFactorMethod.objects.create(
            user=self.user,
            method_type="totp",
            secret=secret,
            is_verified=False,
        )

        self.assertEqual(method.user, self.user)
        self.assertEqual(method.method_type, "totp")
        self.assertEqual(method.secret, secret)
        self.assertFalse(method.is_verified)
        self.assertIsNotNone(method.created_at)

    def test_create_verified_totp_method(self) -> None:
        """Test creating a verified TOTP method."""
        secret = generate_secret()
        method = TwoFactorMethod.objects.create(
            user=self.user,
            method_type="totp",
            secret=secret,
            is_verified=True,
        )

        self.assertTrue(method.is_verified)

    def test_method_str_representation(self) -> None:
        """Test string representation of TwoFactorMethod."""
        secret = generate_secret()
        method = TwoFactorMethod.objects.create(
            user=self.user,
            method_type="totp",
            secret=secret,
            is_verified=True,
        )

        str_repr = str(method)
        self.assertIn(self.user.email, str_repr)
        # Check for the display name (Authenticator App) or TOTP
        self.assertTrue("TOTP" in str_repr or "Authenticator" in str_repr)

    def test_update_last_used(self) -> None:
        """Test updating last_used_at timestamp."""
        secret = generate_secret()
        method = TwoFactorMethod.objects.create(
            user=self.user,
            method_type="totp",
            secret=secret,
            is_verified=True,
        )

        self.assertIsNone(method.last_used_at)

        method.last_used_at = timezone.now()
        method.save()

        method.refresh_from_db()
        self.assertIsNotNone(method.last_used_at)


class RecoveryCodeModelTestCase(TestCase):
    """Tests for RecoveryCode model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_create_recovery_code(self) -> None:
        """Test creating a recovery code."""
        code = RecoveryCode.objects.create(
            user=self.user,
            code_hash="test_hash",
        )

        self.assertEqual(code.user, self.user)
        self.assertEqual(code.code_hash, "test_hash")
        self.assertFalse(code.is_used)
        self.assertIsNone(code.used_at)

    def test_generate_code_format(self) -> None:
        """Test that generated codes follow the XXXX-XXXX-XXXX format."""
        code = RecoveryCode.generate_code()

        parts = code.split("-")
        self.assertEqual(len(parts), 3)
        for part in parts:
            self.assertEqual(len(part), 4)
            # Check it uses the correct character set
            valid_chars = set("ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
            self.assertTrue(all(c in valid_chars for c in part))

    def test_generate_code_uniqueness(self) -> None:
        """Test that generated codes are unique."""
        codes = [RecoveryCode.generate_code() for _ in range(10)]
        self.assertEqual(len(codes), len(set(codes)))

    def test_mark_code_as_used(self) -> None:
        """Test marking a recovery code as used."""
        code = RecoveryCode.objects.create(
            user=self.user,
            code_hash="test_hash",
        )

        self.assertFalse(code.is_used)
        self.assertIsNone(code.used_at)

        code.is_used = True
        code.used_at = timezone.now()
        code.save()

        code.refresh_from_db()
        self.assertTrue(code.is_used)
        self.assertIsNotNone(code.used_at)


class TwoFactorChallengeModelTestCase(TestCase):
    """Tests for TwoFactorChallenge model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_create_challenge(self) -> None:
        """Test creating a 2FA challenge."""
        token = TwoFactorChallenge.generate_token()
        challenge = TwoFactorChallenge.objects.create(
            user=self.user,
            challenge_token=token,
            password_verified=True,
        )

        self.assertEqual(challenge.user, self.user)
        self.assertEqual(challenge.challenge_token, token)
        self.assertTrue(challenge.password_verified)
        self.assertIsNotNone(challenge.created_at)

    def test_generate_token_format(self) -> None:
        """Test that generated tokens are valid UUIDs or secure strings."""
        token = TwoFactorChallenge.generate_token()

        # Token should be a non-empty string
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)

    def test_generate_token_uniqueness(self) -> None:
        """Test that generated tokens are unique."""
        tokens = [TwoFactorChallenge.generate_token() for _ in range(10)]
        self.assertEqual(len(tokens), len(set(tokens)))

    def test_challenge_with_ip_and_user_agent(self) -> None:
        """Test creating a challenge with IP and user agent."""
        token = TwoFactorChallenge.generate_token()
        challenge = TwoFactorChallenge.objects.create(
            user=self.user,
            challenge_token=token,
            password_verified=True,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )

        self.assertEqual(challenge.ip_address, "192.168.1.1")
        self.assertEqual(challenge.user_agent, "Test Browser")

    def test_challenge_str_representation(self) -> None:
        """Test string representation of a challenge."""
        token = TwoFactorChallenge.generate_token()
        challenge = TwoFactorChallenge.objects.create(
            user=self.user,
            challenge_token=token,
            password_verified=True,
        )

        str_repr = str(challenge)
        self.assertIn(self.user.email, str_repr)

    def test_challenge_expiration_check(self) -> None:
        """Test that old challenges can be identified by created_at."""
        token = TwoFactorChallenge.generate_token()

        # Create a challenge
        challenge = TwoFactorChallenge.objects.create(
            user=self.user,
            challenge_token=token,
            password_verified=True,
        )

        # Should have created_at set
        self.assertIsNotNone(challenge.created_at)

        # Create an old challenge
        old_challenge = TwoFactorChallenge.objects.create(
            user=self.user,
            challenge_token=TwoFactorChallenge.generate_token(),
            password_verified=True,
        )
        # Manually set old created_at
        TwoFactorChallenge.objects.filter(id=old_challenge.id).update(
            created_at=timezone.now() - timedelta(hours=1)
        )

        old_challenge.refresh_from_db()
        # Old challenge should have older timestamp
        self.assertTrue(old_challenge.created_at < timezone.now() - timedelta(minutes=30))
