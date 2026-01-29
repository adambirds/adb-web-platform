"""
TOTP (Time-Based One-Time Password) implementation.

Implements RFC 6238 (TOTP) and RFC 4226 (HOTP) for two-factor authentication.
This is a custom implementation without third-party dependencies.
"""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from typing import Any
from urllib.parse import quote


def generate_secret(length: int = 32) -> str:
    """
    Generate a random base32-encoded secret key.

    Args:
        length: Number of random bytes (default 32 for 256 bits of entropy)

    Returns:
        Base32-encoded secret string
    """
    random_bytes = secrets.token_bytes(length)
    # Base32 encode and remove padding
    return base64.b32encode(random_bytes).decode("ascii").rstrip("=")


def _decode_secret(secret: str) -> bytes:
    """
    Decode a base32-encoded secret to bytes.

    Handles secrets with or without padding.
    """
    # Add padding if needed (base32 requires length to be multiple of 8)
    padding = (8 - len(secret) % 8) % 8
    secret_padded = secret.upper() + "=" * padding
    return base64.b32decode(secret_padded)


def _hotp(secret: bytes, counter: int, digits: int = 6) -> str:
    """
    Generate an HOTP value (RFC 4226).

    Args:
        secret: The shared secret as bytes
        counter: The counter value
        digits: Number of digits in the OTP (default 6)

    Returns:
        The OTP as a zero-padded string
    """
    # Pack counter as big-endian 8-byte integer
    counter_bytes = struct.pack(">Q", counter)

    # Calculate HMAC-SHA1
    hmac_hash = hmac.new(secret, counter_bytes, hashlib.sha1).digest()

    # Dynamic truncation (RFC 4226 section 5.4)
    offset = hmac_hash[-1] & 0x0F
    binary = struct.unpack(">I", hmac_hash[offset : offset + 4])[0]
    binary &= 0x7FFFFFFF  # Clear the most significant bit

    # Generate OTP
    otp = binary % (10**digits)
    return str(otp).zfill(digits)


def generate_totp(
    secret: str, time_step: int = 30, digits: int = 6, timestamp: float | None = None
) -> str:
    """
    Generate a TOTP value (RFC 6238).

    Args:
        secret: Base32-encoded secret key
        time_step: Time step in seconds (default 30)
        digits: Number of digits in the OTP (default 6)
        timestamp: Unix timestamp to use (default: current time)

    Returns:
        The current TOTP value as a string
    """
    if timestamp is None:
        timestamp = time.time()

    # Calculate the counter (number of time steps since epoch)
    counter = int(timestamp) // time_step

    # Decode the secret and generate HOTP
    secret_bytes = _decode_secret(secret)
    return _hotp(secret_bytes, counter, digits)


def verify_totp(
    secret: str,
    code: str,
    time_step: int = 30,
    digits: int = 6,
    window: int = 1,
    timestamp: float | None = None,
) -> bool:
    """
    Verify a TOTP code with a time window.

    Args:
        secret: Base32-encoded secret key
        code: The OTP code to verify
        time_step: Time step in seconds (default 30)
        digits: Number of digits in the OTP (default 6)
        window: Number of time steps to check before/after current (default 1)
        timestamp: Unix timestamp to use (default: current time)

    Returns:
        True if the code is valid, False otherwise
    """
    if timestamp is None:
        timestamp = time.time()

    # Normalize the code (remove spaces, ensure correct length)
    code = code.replace(" ", "").replace("-", "")
    if len(code) != digits:
        return False

    # Check codes within the window
    for offset in range(-window, window + 1):
        check_time = timestamp + (offset * time_step)
        expected = generate_totp(secret, time_step, digits, check_time)
        if hmac.compare_digest(code, expected):
            return True

    return False


def generate_totp_uri(
    secret: str,
    account_name: str,
    issuer: str = "App",
    algorithm: str = "SHA1",
    digits: int = 6,
    period: int = 30,
) -> str:
    """
    Generate an otpauth:// URI for provisioning authenticator apps.

    This URI can be encoded as a QR code for easy setup.

    Args:
        secret: Base32-encoded secret key
        account_name: The user's account identifier (usually email)
        issuer: The service name
        algorithm: Hash algorithm (SHA1, SHA256, or SHA512)
        digits: Number of digits in the OTP
        period: Time step in seconds

    Returns:
        otpauth:// URI string
    """
    # URL-encode the account name and issuer
    label = f"{quote(issuer)}:{quote(account_name)}"

    params: dict[str, Any] = {
        "secret": secret.upper(),
        "issuer": issuer,
        "algorithm": algorithm.upper(),
        "digits": digits,
        "period": period,
    }

    param_str = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
    return f"otpauth://totp/{label}?{param_str}"


def get_totp_remaining_seconds(time_step: int = 30, timestamp: float | None = None) -> int:
    """
    Get the number of seconds remaining until the current TOTP expires.

    Args:
        time_step: Time step in seconds (default 30)
        timestamp: Unix timestamp to use (default: current time)

    Returns:
        Seconds remaining until the current code expires
    """
    if timestamp is None:
        timestamp = time.time()

    elapsed = int(timestamp) % time_step
    return time_step - elapsed
