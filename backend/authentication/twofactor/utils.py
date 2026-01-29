"""Utility functions for two-factor authentication."""

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.utils import timezone

from authentication.twofactor.totp import generate_secret, generate_totp_uri, verify_totp

if TYPE_CHECKING:
    from authentication.models import User
    from authentication.twofactor.models import TwoFactorMethod


# Challenge expiration time in minutes
CHALLENGE_EXPIRATION_MINUTES = 10


def get_client_ip(request: Any) -> str | None:
    """Extract client IP from request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def is_2fa_enabled(user: "User") -> bool:
    """
    Check if 2FA is enabled for a user.

    2FA is considered enabled if the user has at least one verified
    TOTP method.

    Args:
        user: The user to check

    Returns:
        True if 2FA is enabled, False otherwise
    """
    from authentication.twofactor.models import TwoFactorMethod

    return TwoFactorMethod.objects.filter(
        user=user,
        method_type=TwoFactorMethod.MethodType.TOTP,
        is_verified=True,
    ).exists()


def get_2fa_methods(user: "User") -> list["TwoFactorMethod"]:
    """
    Get all 2FA methods for a user.

    Args:
        user: The user to get methods for

    Returns:
        List of TwoFactorMethod objects
    """
    from authentication.twofactor.models import TwoFactorMethod

    return list(TwoFactorMethod.objects.filter(user=user))


def setup_totp(user: "User", name: str = "Authenticator App") -> tuple[str, str]:
    """
    Begin TOTP setup for a user.

    Creates an unverified TOTP method with a new secret.
    The user must verify with a valid code before it becomes active.

    Args:
        user: The user to set up TOTP for
        name: A friendly name for this authenticator

    Returns:
        Tuple of (secret, otpauth_uri) for QR code generation
    """
    from authentication.twofactor.models import TwoFactorMethod

    # Check if user already has a verified TOTP method
    existing = TwoFactorMethod.objects.filter(
        user=user,
        method_type=TwoFactorMethod.MethodType.TOTP,
    ).first()

    if existing and existing.is_verified:
        raise ValueError("TOTP is already set up for this user")

    # Generate new secret
    secret = generate_secret()

    # Get issuer name from settings
    issuer = getattr(settings, "TWO_FACTOR_ISSUER", getattr(settings, "SITE_NAME", "App"))

    # Generate otpauth URI
    uri = generate_totp_uri(
        secret=secret,
        account_name=user.email,
        issuer=issuer,
    )

    # Create or update the TOTP method (unverified)
    if existing:
        existing.secret = secret
        existing.name = name
        existing.is_verified = False
        existing.save()
    else:
        TwoFactorMethod.objects.create(
            user=user,
            method_type=TwoFactorMethod.MethodType.TOTP,
            secret=secret,
            name=name,
            is_primary=True,
            is_verified=False,
        )

    return secret, uri


def verify_totp_setup(user: "User", code: str) -> bool:
    """
    Verify TOTP setup with a code from the authenticator app.

    Args:
        user: The user verifying their TOTP setup
        code: The 6-digit code from the authenticator app

    Returns:
        True if verification successful, False otherwise
    """
    from authentication.twofactor.models import TwoFactorMethod

    method = TwoFactorMethod.objects.filter(
        user=user,
        method_type=TwoFactorMethod.MethodType.TOTP,
        is_verified=False,
    ).first()

    if not method:
        return False

    if verify_totp(method.secret, code):
        method.is_verified = True
        method.is_primary = True
        method.last_used_at = timezone.now()
        method.save()
        return True

    return False


def verify_2fa_code(user: "User", code: str) -> tuple[bool, str]:
    """
    Verify a 2FA code (TOTP or recovery code).

    Args:
        user: The user to verify
        code: The code to verify (TOTP or recovery code)

    Returns:
        Tuple of (success, method_type) where method_type is 'totp' or 'recovery'
    """
    from authentication.twofactor.models import TwoFactorMethod
    from authentication.twofactor.recovery import use_recovery_code

    # First, try TOTP verification
    totp_method = TwoFactorMethod.objects.filter(
        user=user,
        method_type=TwoFactorMethod.MethodType.TOTP,
        is_verified=True,
    ).first()

    if totp_method:
        # Clean the code (remove spaces/dashes for TOTP)
        clean_code = code.replace(" ", "").replace("-", "")
        if len(clean_code) == 6 and clean_code.isdigit():
            if verify_totp(totp_method.secret, clean_code):
                totp_method.last_used_at = timezone.now()
                totp_method.save()
                return True, "totp"

    # Try recovery code
    if use_recovery_code(user, code):
        return True, "recovery"

    return False, ""


def create_2fa_challenge(user: "User", request: Any | None = None) -> str:
    """
    Create a 2FA challenge for a user during login.

    Args:
        user: The user to create a challenge for
        request: The HTTP request (for IP and user agent)

    Returns:
        The challenge token
    """
    from authentication.twofactor.models import TwoFactorChallenge

    # Clean up old challenges for this user
    TwoFactorChallenge.objects.filter(
        user=user,
        created_at__lt=timezone.now() - timedelta(minutes=CHALLENGE_EXPIRATION_MINUTES),
    ).delete()

    # Create new challenge
    token = TwoFactorChallenge.generate_token()

    ip_address = None
    user_agent = ""
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

    TwoFactorChallenge.objects.create(
        user=user,
        challenge_token=token,
        password_verified=True,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return token


def verify_2fa_challenge(token: str) -> "User | None":
    """
    Verify a 2FA challenge token and return the associated user.

    Args:
        token: The challenge token to verify

    Returns:
        The User if valid, None otherwise
    """
    from authentication.twofactor.models import TwoFactorChallenge

    challenge = TwoFactorChallenge.objects.filter(
        challenge_token=token,
        created_at__gt=timezone.now() - timedelta(minutes=CHALLENGE_EXPIRATION_MINUTES),
    ).first()

    if challenge:
        return challenge.user

    return None


def complete_2fa_challenge(token: str) -> bool:
    """
    Complete and delete a 2FA challenge.

    Args:
        token: The challenge token to complete

    Returns:
        True if the challenge was found and deleted, False otherwise
    """
    from authentication.twofactor.models import TwoFactorChallenge

    deleted, _ = TwoFactorChallenge.objects.filter(challenge_token=token).delete()
    return deleted > 0


def disable_2fa(user: "User") -> bool:
    """
    Disable all 2FA methods for a user.

    Args:
        user: The user to disable 2FA for

    Returns:
        True if 2FA was disabled, False if it wasn't enabled
    """
    from authentication.twofactor.models import RecoveryCode, TwoFactorMethod

    # Delete all 2FA methods and recovery codes
    methods_deleted, _ = TwoFactorMethod.objects.filter(user=user).delete()
    RecoveryCode.objects.filter(user=user).delete()

    return methods_deleted > 0
