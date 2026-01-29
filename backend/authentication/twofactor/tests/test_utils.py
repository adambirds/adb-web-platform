"""Tests for two-factor authentication utility functions."""

from datetime import timedelta

from django.test import RequestFactory, TestCase
from django.utils import timezone

from authentication.models import User
from authentication.twofactor.models import RecoveryCode, TwoFactorChallenge, TwoFactorMethod
from authentication.twofactor.recovery import (
    generate_recovery_codes,
    get_remaining_recovery_codes_count,
    use_recovery_code,
)
from authentication.twofactor.totp import generate_secret, generate_totp
from authentication.twofactor.utils import (
    CHALLENGE_EXPIRATION_MINUTES,
    complete_2fa_challenge,
    create_2fa_challenge,
    get_2fa_methods,
    get_client_ip,
    is_2fa_enabled,
    setup_totp,
    verify_2fa_challenge,
    verify_2fa_code,
    verify_totp_setup,
)


class Is2FAEnabledTestCase(TestCase):
    """Tests for is_2fa_enabled function."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_2fa_not_enabled_by_default(self) -> None:
        """Test that 2FA is not enabled for new users."""
        self.assertFalse(is_2fa_enabled(self.user))

    def test_2fa_not_enabled_with_unverified_method(self) -> None:
        """Test that unverified 2FA methods don't count as enabled."""
        TwoFactorMethod.objects.create(
            user=self.user,
            method_type="totp",
            secret=generate_secret(),
            is_verified=False,
        )
        self.assertFalse(is_2fa_enabled(self.user))

    def test_2fa_enabled_with_verified_method(self) -> None:
        """Test that verified 2FA methods count as enabled."""
        TwoFactorMethod.objects.create(
            user=self.user,
            method_type="totp",
            secret=generate_secret(),
            is_verified=True,
        )
        self.assertTrue(is_2fa_enabled(self.user))


class Get2FAMethodsTestCase(TestCase):
    """Tests for get_2fa_methods function."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_get_methods_returns_empty_when_no_method(self) -> None:
        """Test that get_2fa_methods returns empty list when no method exists."""
        methods = get_2fa_methods(self.user)
        self.assertEqual(len(methods), 0)

    def test_get_methods_returns_all_methods(self) -> None:
        """Test that get_2fa_methods returns all methods."""
        TwoFactorMethod.objects.create(
            user=self.user,
            method_type="totp",
            secret=generate_secret(),
            is_verified=True,
        )
        methods = get_2fa_methods(self.user)
        self.assertEqual(len(methods), 1)


class SetupTotpTestCase(TestCase):
    """Tests for setup_totp function."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_setup_totp_creates_method(self) -> None:
        """Test that setup_totp creates a new TOTP method."""
        secret, uri = setup_totp(self.user)

        self.assertIsNotNone(secret)
        self.assertIsNotNone(uri)
        self.assertIn("otpauth://", uri)

        method = TwoFactorMethod.objects.get(user=self.user)
        self.assertEqual(method.secret, secret)
        self.assertFalse(method.is_verified)

    def test_setup_totp_replaces_unverified_method(self) -> None:
        """Test that setup_totp replaces existing unverified methods."""
        # Create an unverified method
        old_secret = generate_secret()
        TwoFactorMethod.objects.create(
            user=self.user,
            method_type="totp",
            secret=old_secret,
            is_verified=False,
        )

        new_secret, uri = setup_totp(self.user)

        self.assertNotEqual(old_secret, new_secret)
        methods = TwoFactorMethod.objects.filter(user=self.user)
        self.assertEqual(methods.count(), 1)
        method = methods.first()
        assert method is not None
        self.assertEqual(method.secret, new_secret)

    def test_setup_totp_fails_if_already_verified(self) -> None:
        """Test that setup_totp fails if user already has verified TOTP."""
        TwoFactorMethod.objects.create(
            user=self.user,
            method_type="totp",
            secret=generate_secret(),
            is_verified=True,
        )

        with self.assertRaises(ValueError):
            setup_totp(self.user)


class VerifyTotpSetupTestCase(TestCase):
    """Tests for verify_totp_setup function."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_verify_totp_setup_valid_code(self) -> None:
        """Test verifying TOTP setup with valid code."""
        secret, _ = setup_totp(self.user)
        code = generate_totp(secret)

        result = verify_totp_setup(self.user, code)

        self.assertTrue(result)
        method = TwoFactorMethod.objects.get(user=self.user)
        self.assertTrue(method.is_verified)

    def test_verify_totp_setup_invalid_code(self) -> None:
        """Test verifying TOTP setup with invalid code."""
        setup_totp(self.user)

        result = verify_totp_setup(self.user, "000000")

        self.assertFalse(result)
        method = TwoFactorMethod.objects.get(user=self.user)
        self.assertFalse(method.is_verified)

    def test_verify_totp_setup_no_pending_method(self) -> None:
        """Test verifying TOTP setup when no pending method exists."""
        result = verify_totp_setup(self.user, "123456")

        self.assertFalse(result)


class Verify2FACodeTestCase(TestCase):
    """Tests for verify_2fa_code function."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.secret = generate_secret()
        self.method = TwoFactorMethod.objects.create(
            user=self.user,
            method_type="totp",
            secret=self.secret,
            is_verified=True,
        )

    def test_verify_valid_totp_code(self) -> None:
        """Test verifying a valid TOTP code."""
        code = generate_totp(self.secret)
        is_valid, method_used = verify_2fa_code(self.user, code)

        self.assertTrue(is_valid)
        self.assertEqual(method_used, "totp")

    def test_verify_invalid_totp_code(self) -> None:
        """Test verifying an invalid TOTP code."""
        is_valid, method_used = verify_2fa_code(self.user, "000000")

        self.assertFalse(is_valid)
        self.assertEqual(method_used, "")

    def test_verify_recovery_code(self) -> None:
        """Test verifying a recovery code."""
        # Generate recovery codes
        codes = generate_recovery_codes(self.user)
        code = codes[0]

        is_valid, method_used = verify_2fa_code(self.user, code)

        self.assertTrue(is_valid)
        self.assertEqual(method_used, "recovery")

    def test_verify_invalid_recovery_code(self) -> None:
        """Test verifying an invalid recovery code."""
        generate_recovery_codes(self.user)

        is_valid, method_used = verify_2fa_code(self.user, "XXXX-XXXX-XXXX")

        self.assertFalse(is_valid)


class ChallengeTestCase(TestCase):
    """Tests for 2FA challenge functions."""

    def setUp(self) -> None:
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_create_2fa_challenge(self) -> None:
        """Test creating a 2FA challenge."""
        request = self.factory.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        request.META["HTTP_USER_AGENT"] = "Test Browser"

        token = create_2fa_challenge(self.user, request)

        self.assertIsNotNone(token)
        self.assertGreater(len(token), 0)

        challenge = TwoFactorChallenge.objects.get(challenge_token=token)
        self.assertEqual(challenge.user, self.user)
        self.assertTrue(challenge.password_verified)

    def test_create_2fa_challenge_without_request(self) -> None:
        """Test creating a 2FA challenge without a request."""
        token = create_2fa_challenge(self.user)

        self.assertIsNotNone(token)
        challenge = TwoFactorChallenge.objects.get(challenge_token=token)
        self.assertEqual(challenge.user, self.user)

    def test_verify_2fa_challenge_valid(self) -> None:
        """Test verifying a valid 2FA challenge."""
        token = create_2fa_challenge(self.user)

        user = verify_2fa_challenge(token)

        self.assertEqual(user, self.user)

    def test_verify_2fa_challenge_invalid(self) -> None:
        """Test verifying an invalid 2FA challenge."""
        user = verify_2fa_challenge("invalid_token")

        self.assertIsNone(user)

    def test_verify_2fa_challenge_expired(self) -> None:
        """Test verifying an expired 2FA challenge."""
        token = create_2fa_challenge(self.user)

        # Make the challenge expired
        challenge = TwoFactorChallenge.objects.get(challenge_token=token)
        challenge.created_at = timezone.now() - timedelta(minutes=CHALLENGE_EXPIRATION_MINUTES + 1)
        challenge.save()

        user = verify_2fa_challenge(token)

        self.assertIsNone(user)

    def test_complete_2fa_challenge(self) -> None:
        """Test completing a 2FA challenge."""
        token = create_2fa_challenge(self.user)

        result = complete_2fa_challenge(token)

        self.assertTrue(result)
        # Challenge should be deleted after completion
        self.assertFalse(TwoFactorChallenge.objects.filter(challenge_token=token).exists())


class GetClientIPTestCase(TestCase):
    """Tests for get_client_ip function."""

    def setUp(self) -> None:
        """Set up test data."""
        self.factory = RequestFactory()

    def test_get_ip_from_remote_addr(self) -> None:
        """Test getting IP from REMOTE_ADDR."""
        request = self.factory.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"

        ip = get_client_ip(request)
        self.assertEqual(ip, "192.168.1.1")

    def test_get_ip_from_x_forwarded_for(self) -> None:
        """Test getting IP from X-Forwarded-For header."""
        request = self.factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.1, 192.168.1.1"
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        ip = get_client_ip(request)
        self.assertEqual(ip, "10.0.0.1")


class RecoveryCodeTestCase(TestCase):
    """Tests for recovery code functions."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_generate_recovery_codes(self) -> None:
        """Test generating recovery codes."""
        codes = generate_recovery_codes(self.user)

        self.assertEqual(len(codes), 10)  # Default count
        for code in codes:
            parts = code.split("-")
            self.assertEqual(len(parts), 3)

    def test_generate_recovery_codes_clears_existing(self) -> None:
        """Test that generating recovery codes clears existing ones."""
        # Generate first set
        first_codes = generate_recovery_codes(self.user)

        # Generate second set
        second_codes = generate_recovery_codes(self.user)

        # Should have same count in DB
        db_count = RecoveryCode.objects.filter(user=self.user).count()
        self.assertEqual(db_count, 10)

        # Codes should be different
        self.assertNotEqual(set(first_codes), set(second_codes))

    def test_use_recovery_code(self) -> None:
        """Test using a recovery code."""
        codes = generate_recovery_codes(self.user)
        code = codes[0]

        is_used = use_recovery_code(self.user, code)
        self.assertTrue(is_used)

        # Code should be marked as used
        remaining = get_remaining_recovery_codes_count(self.user)
        self.assertEqual(remaining, 9)

    def test_use_recovery_code_twice(self) -> None:
        """Test that a recovery code can't be used twice."""
        codes = generate_recovery_codes(self.user)
        code = codes[0]

        # First use
        is_used = use_recovery_code(self.user, code)
        self.assertTrue(is_used)

        # Second use should fail
        is_used = use_recovery_code(self.user, code)
        self.assertFalse(is_used)

    def test_get_remaining_recovery_codes_count(self) -> None:
        """Test getting remaining recovery codes count."""
        generate_recovery_codes(self.user)

        count = get_remaining_recovery_codes_count(self.user)
        self.assertEqual(count, 10)

        # Use some codes
        codes = list(RecoveryCode.objects.filter(user=self.user, is_used=False)[:3])
        for code_obj in codes:
            code_obj.is_used = True
            code_obj.save()

        count = get_remaining_recovery_codes_count(self.user)
        self.assertEqual(count, 7)
