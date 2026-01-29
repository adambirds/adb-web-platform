"""Tests for passkey models."""

from django.test import TestCase
from django.utils import timezone

from authentication.models import User
from authentication.passkeys.models import Passkey, PasskeyChallenge
from authentication.passkeys.utils import generate_challenge


class PasskeyModelTestCase(TestCase):
    """Tests for the Passkey model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_create_passkey(self) -> None:
        """Test creating a passkey."""
        credential_id = b"test_credential_id"
        public_key = b"test_public_key"

        passkey = Passkey.objects.create(
            user=self.user,
            credential_id=credential_id,
            public_key=public_key,
            name="My Passkey",
            device_type="platform",
            backed_up=True,
            transports=["internal"],
        )

        self.assertEqual(passkey.user, self.user)
        self.assertEqual(bytes(passkey.credential_id), credential_id)
        self.assertEqual(bytes(passkey.public_key), public_key)
        self.assertEqual(passkey.name, "My Passkey")
        self.assertEqual(passkey.device_type, "platform")
        self.assertTrue(passkey.backed_up)
        self.assertEqual(passkey.transports, ["internal"])
        self.assertEqual(passkey.sign_count, 0)
        self.assertIsNotNone(passkey.created_at)
        self.assertIsNone(passkey.last_used_at)

    def test_passkey_str(self) -> None:
        """Test the string representation of a passkey."""
        passkey = Passkey.objects.create(
            user=self.user,
            credential_id=b"test_credential_id",
            public_key=b"test_public_key",
            name="My Passkey",
        )

        self.assertEqual(str(passkey), "My Passkey (test@example.com)")

    def test_passkey_sign_count_update(self) -> None:
        """Test updating the sign count."""
        passkey = Passkey.objects.create(
            user=self.user,
            credential_id=b"test_credential_id",
            public_key=b"test_public_key",
            name="My Passkey",
        )

        self.assertEqual(passkey.sign_count, 0)

        passkey.sign_count = 5
        passkey.save()
        passkey.refresh_from_db()

        self.assertEqual(passkey.sign_count, 5)

    def test_passkey_last_used_update(self) -> None:
        """Test updating the last used timestamp."""
        passkey = Passkey.objects.create(
            user=self.user,
            credential_id=b"test_credential_id",
            public_key=b"test_public_key",
            name="My Passkey",
        )

        self.assertIsNone(passkey.last_used_at)

        now = timezone.now()
        passkey.last_used_at = now
        passkey.save()
        passkey.refresh_from_db()

        self.assertIsNotNone(passkey.last_used_at)

    def test_passkey_ordering(self) -> None:
        """Test that passkeys are ordered by creation date descending."""
        passkey1 = Passkey.objects.create(
            user=self.user,
            credential_id=b"credential_1",
            public_key=b"public_key_1",
            name="Passkey 1",
        )
        passkey2 = Passkey.objects.create(
            user=self.user,
            credential_id=b"credential_2",
            public_key=b"public_key_2",
            name="Passkey 2",
        )

        passkeys = list(Passkey.objects.filter(user=self.user))
        self.assertEqual(passkeys[0], passkey2)  # Most recent first
        self.assertEqual(passkeys[1], passkey1)

    def test_passkey_unique_credential_id(self) -> None:
        """Test that credential_id must be unique."""
        from django.db import IntegrityError

        Passkey.objects.create(
            user=self.user,
            credential_id=b"same_credential_id",
            public_key=b"public_key_1",
            name="Passkey 1",
        )

        with self.assertRaises(IntegrityError):
            Passkey.objects.create(
                user=self.user,
                credential_id=b"same_credential_id",
                public_key=b"public_key_2",
                name="Passkey 2",
            )

    def test_passkey_cascade_delete(self) -> None:
        """Test that passkeys are deleted when user is deleted."""
        Passkey.objects.create(
            user=self.user,
            credential_id=b"test_credential_id",
            public_key=b"test_public_key",
            name="My Passkey",
        )

        self.assertEqual(Passkey.objects.filter(user=self.user).count(), 1)

        user_id = self.user.id
        self.user.delete()

        # Passkey should be deleted due to cascade
        self.assertEqual(Passkey.objects.filter(user_id=user_id).count(), 0)


class PasskeyChallengeModelTestCase(TestCase):
    """Tests for the PasskeyChallenge model."""

    def setUp(self) -> None:
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    def test_create_registration_challenge(self) -> None:
        """Test creating a registration challenge."""
        challenge = generate_challenge()

        passkey_challenge = PasskeyChallenge.objects.create(
            user=self.user,
            challenge=challenge,
            challenge_type="registration",
        )

        self.assertEqual(passkey_challenge.user, self.user)
        self.assertEqual(bytes(passkey_challenge.challenge), challenge)
        self.assertEqual(passkey_challenge.challenge_type, "registration")
        self.assertIsNotNone(passkey_challenge.created_at)
        self.assertIsNone(passkey_challenge.email)

    def test_create_authentication_challenge(self) -> None:
        """Test creating an authentication challenge without user."""
        challenge = generate_challenge()

        passkey_challenge = PasskeyChallenge.objects.create(
            challenge=challenge,
            challenge_type="authentication",
            email="test@example.com",
        )

        self.assertIsNone(passkey_challenge.user)
        self.assertEqual(passkey_challenge.email, "test@example.com")
        self.assertEqual(passkey_challenge.challenge_type, "authentication")

    def test_challenge_str(self) -> None:
        """Test the string representation of a challenge."""
        challenge = generate_challenge()

        passkey_challenge = PasskeyChallenge.objects.create(
            user=self.user,
            challenge=challenge,
            challenge_type="registration",
        )

        result = str(passkey_challenge)
        self.assertIn("registration challenge", result)

    def test_challenge_cascade_delete(self) -> None:
        """Test that challenges are deleted when user is deleted."""
        PasskeyChallenge.objects.create(
            user=self.user,
            challenge=generate_challenge(),
            challenge_type="registration",
        )

        self.assertEqual(PasskeyChallenge.objects.filter(user=self.user).count(), 1)

        user_id = self.user.id
        self.user.delete()

        # Challenge should be deleted due to cascade
        self.assertEqual(PasskeyChallenge.objects.filter(user_id=user_id).count(), 0)

    def test_multiple_challenges_per_user(self) -> None:
        """Test that a user can have multiple challenges."""
        PasskeyChallenge.objects.create(
            user=self.user,
            challenge=generate_challenge(),
            challenge_type="registration",
        )
        PasskeyChallenge.objects.create(
            user=self.user,
            challenge=generate_challenge(),
            challenge_type="registration",
        )

        self.assertEqual(PasskeyChallenge.objects.filter(user=self.user).count(), 2)
