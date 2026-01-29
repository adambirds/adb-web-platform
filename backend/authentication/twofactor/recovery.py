"""Recovery codes utility functions for two-factor authentication."""

import hashlib
import hmac
import secrets
from typing import TYPE_CHECKING

from django.utils import timezone

if TYPE_CHECKING:
    from authentication.models import User

# Number of recovery codes to generate per user
RECOVERY_CODE_COUNT = 10


def generate_recovery_code() -> str:
    """
    Generate a single recovery code in format XXXX-XXXX-XXXX.

    Uses a character set that avoids visually ambiguous characters
    (no I, O, 0, 1, l).
    """
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    code_parts = []
    for _ in range(3):
        part = "".join(secrets.choice(chars) for _ in range(4))
        code_parts.append(part)
    return "-".join(code_parts)


def hash_recovery_code(code: str) -> str:
    """
    Hash a recovery code for secure storage.

    Args:
        code: The plaintext recovery code

    Returns:
        SHA-256 hash of the normalized code
    """
    # Normalize: uppercase and remove dashes/spaces
    normalized = code.upper().replace("-", "").replace(" ", "")
    return hashlib.sha256(normalized.encode()).hexdigest()


def verify_recovery_code(code: str, code_hash: str) -> bool:
    """
    Verify a recovery code against its hash.

    Args:
        code: The plaintext recovery code to verify
        code_hash: The stored hash to compare against

    Returns:
        True if the code matches, False otherwise
    """
    computed_hash = hash_recovery_code(code)
    return hmac.compare_digest(computed_hash, code_hash)


def generate_recovery_codes(user: "User", count: int = RECOVERY_CODE_COUNT) -> list[str]:
    """
    Generate a new set of recovery codes for a user.

    This will delete any existing recovery codes and create new ones.
    The plaintext codes are returned once and should be shown to the user
    immediately - they cannot be retrieved later.

    Args:
        user: The user to generate codes for
        count: Number of codes to generate

    Returns:
        List of plaintext recovery codes (show to user immediately)
    """
    from authentication.twofactor.models import RecoveryCode, TwoFactorMethod

    # Delete existing recovery codes and method
    RecoveryCode.objects.filter(user=user).delete()
    TwoFactorMethod.objects.filter(
        user=user, method_type=TwoFactorMethod.MethodType.RECOVERY
    ).delete()

    # Generate new codes
    plaintext_codes = []
    for _ in range(count):
        code = generate_recovery_code()
        plaintext_codes.append(code)

        RecoveryCode.objects.create(
            user=user,
            code_hash=hash_recovery_code(code),
            is_used=False,
        )

    # Create the recovery method entry
    TwoFactorMethod.objects.create(
        user=user,
        method_type=TwoFactorMethod.MethodType.RECOVERY,
        name="Recovery Codes",
        is_verified=True,  # Recovery codes are immediately valid
    )

    return plaintext_codes


def use_recovery_code(user: "User", code: str) -> bool:
    """
    Attempt to use a recovery code for authentication.

    If valid, marks the code as used so it cannot be reused.

    Args:
        user: The user attempting to authenticate
        code: The recovery code to use

    Returns:
        True if the code was valid and has been consumed, False otherwise
    """
    from authentication.twofactor.models import RecoveryCode

    # Find all unused recovery codes for this user
    unused_codes = RecoveryCode.objects.filter(user=user, is_used=False)

    for recovery_code in unused_codes:
        if verify_recovery_code(code, recovery_code.code_hash):
            # Mark as used
            recovery_code.is_used = True
            recovery_code.used_at = timezone.now()
            recovery_code.save()
            return True

    return False


def get_remaining_recovery_codes_count(user: "User") -> int:
    """
    Get the count of remaining (unused) recovery codes for a user.

    Args:
        user: The user to check

    Returns:
        Number of unused recovery codes
    """
    from authentication.twofactor.models import RecoveryCode

    return RecoveryCode.objects.filter(user=user, is_used=False).count()
