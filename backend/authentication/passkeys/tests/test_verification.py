"""Tests for passkey verification functions."""

from django.test import TestCase

from authentication.passkeys.verification import (
    VerificationError,
    encode_cbor_public_key,
    parse_authenticator_data,
    parse_cbor,
)


class ParseCBORTestCase(TestCase):
    """Tests for CBOR parsing."""

    def test_parse_unsigned_integer_small(self) -> None:
        """Test parsing small unsigned integers (< 24)."""
        # CBOR encoding of 5
        result = parse_cbor(bytes([5]))
        self.assertEqual(result, 5)

    def test_parse_unsigned_integer_one_byte(self) -> None:
        """Test parsing unsigned integers requiring one extra byte."""
        # CBOR encoding of 100 (24 followed by 100)
        result = parse_cbor(bytes([24, 100]))
        self.assertEqual(result, 100)

    def test_parse_negative_integer(self) -> None:
        """Test parsing negative integers."""
        # CBOR encoding of -1 (0x20)
        result = parse_cbor(bytes([0x20]))
        self.assertEqual(result, -1)

    def test_parse_byte_string(self) -> None:
        """Test parsing byte strings."""
        # CBOR encoding of b"hello" (0x45 followed by "hello")
        data = bytes([0x45]) + b"hello"
        result = parse_cbor(data)
        self.assertEqual(result, b"hello")

    def test_parse_text_string(self) -> None:
        """Test parsing text strings."""
        # CBOR encoding of "hello" (0x65 followed by "hello")
        data = bytes([0x65]) + b"hello"
        result = parse_cbor(data)
        self.assertEqual(result, "hello")

    def test_parse_array(self) -> None:
        """Test parsing arrays."""
        # CBOR encoding of [1, 2, 3]
        # 0x83 = array of 3 items, then 1, 2, 3
        data = bytes([0x83, 1, 2, 3])
        result = parse_cbor(data)
        self.assertEqual(result, [1, 2, 3])

    def test_parse_map(self) -> None:
        """Test parsing maps."""
        # CBOR encoding of {1: 2}
        # 0xA1 = map of 1 item, then key 1, value 2
        data = bytes([0xA1, 1, 2])
        result = parse_cbor(data)
        self.assertEqual(result, {1: 2})

    def test_parse_boolean_false(self) -> None:
        """Test parsing false."""
        # CBOR encoding of false (0xF4)
        result = parse_cbor(bytes([0xF4]))
        self.assertFalse(result)

    def test_parse_boolean_true(self) -> None:
        """Test parsing true."""
        # CBOR encoding of true (0xF5)
        result = parse_cbor(bytes([0xF5]))
        self.assertTrue(result)

    def test_parse_null(self) -> None:
        """Test parsing null."""
        # CBOR encoding of null (0xF6)
        result = parse_cbor(bytes([0xF6]))
        self.assertIsNone(result)


class EncodeCBORPublicKeyTestCase(TestCase):
    """Tests for CBOR public key encoding."""

    def test_encode_simple_map(self) -> None:
        """Test encoding a simple map."""
        key_data = {1: 2, 3: -7}
        result = encode_cbor_public_key(key_data)

        # Should be valid CBOR
        self.assertIsInstance(result, bytes)

        # Parse it back
        parsed = parse_cbor(result)
        self.assertEqual(parsed[1], 2)
        self.assertEqual(parsed[3], -7)

    def test_encode_ec2_public_key_structure(self) -> None:
        """Test encoding an EC2 public key structure."""
        # Simulated EC2 key data (COSE format)
        key_data = {
            1: 2,  # kty: EC2
            3: -7,  # alg: ES256
            -1: 1,  # crv: P-256
            -2: b"x" * 32,  # x coordinate
            -3: b"y" * 32,  # y coordinate
        }
        result = encode_cbor_public_key(key_data)

        self.assertIsInstance(result, bytes)


class ParseAuthenticatorDataTestCase(TestCase):
    """Tests for authenticator data parsing."""

    def test_parse_minimal_authenticator_data(self) -> None:
        """Test parsing minimal authenticator data (37 bytes)."""
        import hashlib
        import struct

        # Create minimal auth data: 32 bytes RP ID hash + 1 byte flags + 4 bytes counter
        rp_id_hash = hashlib.sha256(b"example.com").digest()
        flags = 0x01  # User presence
        sign_count = 5

        auth_data = rp_id_hash + bytes([flags]) + struct.pack(">I", sign_count)

        result = parse_authenticator_data(auth_data)

        self.assertEqual(result["rp_id_hash"], rp_id_hash)
        self.assertEqual(result["flags"], flags)
        self.assertEqual(result["sign_count"], sign_count)

    def test_parse_authenticator_data_too_short(self) -> None:
        """Test that parsing fails for data that's too short."""
        auth_data = b"too short"

        with self.assertRaises(VerificationError) as ctx:
            parse_authenticator_data(auth_data)

        self.assertIn("too short", str(ctx.exception))

    def test_parse_authenticator_data_user_presence_flag(self) -> None:
        """Test parsing user presence flag."""
        import hashlib
        import struct

        rp_id_hash = hashlib.sha256(b"example.com").digest()
        flags = 0x01  # User presence bit set
        sign_count = 0

        auth_data = rp_id_hash + bytes([flags]) + struct.pack(">I", sign_count)
        result = parse_authenticator_data(auth_data)

        self.assertTrue(result["flags"] & 0x01)  # UP flag is set

    def test_parse_authenticator_data_user_verified_flag(self) -> None:
        """Test parsing user verified flag."""
        import hashlib
        import struct

        rp_id_hash = hashlib.sha256(b"example.com").digest()
        flags = 0x05  # User presence + user verified
        sign_count = 0

        auth_data = rp_id_hash + bytes([flags]) + struct.pack(">I", sign_count)
        result = parse_authenticator_data(auth_data)

        self.assertTrue(result["flags"] & 0x04)  # UV flag is set


class VerificationErrorTestCase(TestCase):
    """Tests for VerificationError."""

    def test_verification_error_message(self) -> None:
        """Test that VerificationError contains the correct message."""
        error = VerificationError("Test error message")
        self.assertEqual(str(error), "Test error message")

    def test_verification_error_is_exception(self) -> None:
        """Test that VerificationError is an exception."""
        error = VerificationError("Test")
        self.assertIsInstance(error, Exception)

    def test_verification_error_can_be_raised(self) -> None:
        """Test that VerificationError can be raised and caught."""
        with self.assertRaises(VerificationError):
            raise VerificationError("Test error")
