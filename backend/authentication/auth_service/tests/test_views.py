"""Tests for auth service REST API views."""

import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from authentication.passkeys.models import Passkey
from authentication.twofactor.models import TwoFactorChallenge, TwoFactorMethod
from authentication.twofactor.totp import generate_secret, generate_totp

User = get_user_model()


class AuthServiceLoginTestCase(TestCase):
    """Tests for login endpoint."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            email_verified=True,
        )

    def test_login_success(self) -> None:
        """Test successful login."""
        response = self.client.post(
            "/api/auth-service/login",
            data=json.dumps({"email": "test@example.com", "password": "testpass123"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Login successful")
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], "test@example.com")

    def test_login_invalid_credentials(self) -> None:
        """Test login with invalid credentials."""
        response = self.client.post(
            "/api/auth-service/login",
            data=json.dumps({"email": "test@example.com", "password": "wrongpass"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "The username and password entered are incorrect.")

    def test_login_inactive_user(self) -> None:
        """Test login with inactive user."""
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            "/api/auth-service/login",
            data=json.dumps({"email": "test@example.com", "password": "testpass123"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])
        # Django's authenticate returns None for inactive users, so we get "incorrect" message
        self.assertIn("incorrect", data["message"].lower())

    def test_login_requires_2fa(self) -> None:
        """Test login when 2FA is enabled."""
        TwoFactorMethod.objects.create(
            user=self.user,
            method_type="totp",
            secret=generate_secret(),
            is_verified=True,
        )

        response = self.client.post(
            "/api/auth-service/login",
            data=json.dumps({"email": "test@example.com", "password": "testpass123"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["requires2fa"])
        self.assertIn("challengeToken", data)


class AuthServiceLogoutTestCase(TestCase):
    """Tests for logout endpoint."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_logout_success(self) -> None:
        """Test successful logout."""
        self.client.login(username="test@example.com", password="testpass123")

        response = self.client.post("/api/auth-service/logout")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])


class AuthServiceMeTestCase(TestCase):
    """Tests for me endpoint."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            email_verified=True,
        )

    def test_me_authenticated(self) -> None:
        """Test getting current user when authenticated."""
        self.client.login(username="test@example.com", password="testpass123")

        response = self.client.get("/api/auth-service/me")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], "test@example.com")

    def test_me_not_authenticated(self) -> None:
        """Test getting current user when not authenticated."""
        response = self.client.get("/api/auth-service/me")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])


class AuthServiceRegisterTestCase(TestCase):
    """Tests for registration endpoint."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()

    @patch("authentication.auth_service.views.send_verification_email")
    def test_register_success(self, mock_send_email: MagicMock) -> None:
        """Test successful registration."""
        response = self.client.post(
            "/api/auth-service/register",
            data=json.dumps(
                {
                    "email": "newuser@example.com",
                    "password": "securepass123",
                    "first_name": "New",
                    "last_name": "User",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # Verify user was created
        user = User.objects.get(email="newuser@example.com")
        self.assertEqual(user.first_name, "New")
        self.assertFalse(user.email_verified)

        # Verify email was sent
        mock_send_email.assert_called_once_with(user)

    def test_register_duplicate_email(self) -> None:
        """Test registration with existing email."""
        User.objects.create_user(
            email="existing@example.com",
            password="testpass123",
            first_name="Existing",
            last_name="User",
        )

        response = self.client.post(
            "/api/auth-service/register",
            data=json.dumps(
                {
                    "email": "existing@example.com",
                    "password": "securepass123",
                    "first_name": "New",
                    "last_name": "User",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])


class AuthServiceVerifyEmailTestCase(TestCase):
    """Tests for email verification endpoint."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            email_verified=False,
        )
        import uuid

        self.user.verification_token = uuid.uuid4()
        self.token = str(self.user.verification_token)
        self.user.save()

    def test_verify_email_success(self) -> None:
        """Test successful email verification."""
        response = self.client.post(
            "/api/auth-service/verify-email",
            data=json.dumps({"token": self.token}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # Verify user email is now verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_verify_email_invalid_token(self) -> None:
        """Test email verification with invalid token."""
        response = self.client.post(
            "/api/auth-service/verify-email",
            data=json.dumps({"token": "invalid-token"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])


class AuthService2FATestCase(TestCase):
    """Tests for 2FA endpoints."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            email_verified=True,
        )

    def test_2fa_verify_with_totp(self) -> None:
        """Test 2FA verification with TOTP code."""
        secret = generate_secret()
        TwoFactorMethod.objects.create(
            user=self.user, method_type="totp", secret=secret, is_verified=True
        )

        # Create challenge
        TwoFactorChallenge.objects.create(
            user=self.user,
            challenge_token="test-token-123",
        )

        # Generate valid TOTP code
        code = generate_totp(secret)

        response = self.client.post(
            "/api/auth-service/2fa/verify",
            data=json.dumps(
                {
                    "challenge_token": "test-token-123",
                    "code": code,
                    "is_recovery_code": False,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

    def test_2fa_status_not_enabled(self) -> None:
        """Test 2FA status when not enabled."""
        self.client.login(username="test@example.com", password="testpass123")

        response = self.client.get("/api/auth-service/2fa/status")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertFalse(data.get("is_enabled", data.get("isEnabled", False)))


class AuthServicePasswordTestCase(TestCase):
    """Tests for password management endpoints."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="oldpassword123",
            first_name="Test",
            last_name="User",
            email_verified=True,
        )

    def test_change_password_success(self) -> None:
        """Test successful password change."""
        self.client.login(username="test@example.com", password="oldpassword123")

        response = self.client.post(
            "/api/auth-service/change-password",
            data=json.dumps(
                {
                    "current_password": "oldpassword123",
                    "new_password": "newpassword123",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Debug output
        if not data.get("success"):
            print(f"Change password response: {data}")
        self.assertTrue(data["success"])

        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))

    @patch("authentication.auth_service.views.send_mail")
    def test_forgot_password(self, mock_send_mail: MagicMock) -> None:
        """Test forgot password request."""
        response = self.client.post(
            "/api/auth-service/forgot-password",
            data=json.dumps({"email": "test@example.com"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # Verify reset token was created
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.verification_token)

    def test_reset_password_success(self) -> None:
        """Test successful password reset."""
        import uuid

        from django.utils import timezone

        reset_token = uuid.uuid4()
        self.user.password_reset_token = reset_token
        self.user.password_reset_token_created = timezone.now()
        self.user.save()

        response = self.client.post(
            "/api/auth-service/reset-password",
            data=json.dumps(
                {
                    "token": str(reset_token),
                    "new_password": "newpassword456",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword456"))
        # Verify token was cleared
        self.assertIsNone(self.user.password_reset_token)
        self.assertIsNone(self.user.password_reset_token_created)

    def test_reset_password_expired_token(self) -> None:
        """Test that expired reset tokens are rejected."""
        import uuid
        from datetime import timedelta

        from django.utils import timezone

        reset_token = uuid.uuid4()
        # Set token created time to 2 hours ago (expired)
        self.user.password_reset_token = reset_token
        self.user.password_reset_token_created = timezone.now() - timedelta(hours=2)
        self.user.save()

        response = self.client.post(
            "/api/auth-service/reset-password",
            data=json.dumps(
                {
                    "token": str(reset_token),
                    "new_password": "newpassword456",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("expired", data["message"].lower())

    def test_reset_does_not_affect_verification_token(self) -> None:
        """Test that password reset doesn't overwrite email verification token."""

        original_verification_token = self.user.verification_token
        self.user.email_verified = False
        self.user.save()

        # Trigger password reset
        response = self.client.post(
            "/api/auth-service/forgot-password",
            data=json.dumps({"email": self.user.email}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()

        # Verification token should be unchanged
        self.assertEqual(self.user.verification_token, original_verification_token)
        # Password reset token should be set
        self.assertIsNotNone(self.user.password_reset_token)
        # They should be different
        self.assertNotEqual(str(self.user.verification_token), str(self.user.password_reset_token))


class AuthServicePasskeyTestCase(TestCase):
    """Tests for passkey endpoints."""

    def setUp(self) -> None:
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            email_verified=True,
        )

    def test_passkeys_list_empty(self) -> None:
        """Test listing passkeys when none exist."""
        self.client.login(username="test@example.com", password="testpass123")

        response = self.client.get("/api/auth-service/webauthn/passkeys")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["passkeys"]), 0)

    def test_passkey_delete(self) -> None:
        """Test deleting a passkey."""
        self.client.login(username="test@example.com", password="testpass123")

        passkey = Passkey.objects.create(
            user=self.user,
            credential_id=b"credential_1",
            public_key=b"public_key_1",
            name="Passkey 1",
        )

        response = self.client.post(
            "/api/auth-service/webauthn/delete",
            data=json.dumps({"passkey_id": str(passkey.id)}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # Verify passkey was deleted
        self.assertFalse(Passkey.objects.filter(id=passkey.id).exists())
