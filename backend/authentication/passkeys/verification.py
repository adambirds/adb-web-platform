"""WebAuthn credential verification."""

import hashlib
import struct
from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding

from authentication.passkeys.utils import base64url_to_bytes, get_allowed_origins, get_rp_id


class VerificationError(Exception):
    """Error during WebAuthn verification."""


def parse_cbor(data: bytes) -> Any:
    """
    Simple CBOR parser for WebAuthn data structures.
    Only handles the subset needed for WebAuthn.
    """
    import struct

    def decode(data: bytes, offset: int = 0) -> tuple[Any, int]:
        if offset >= len(data):
            raise ValueError("Unexpected end of CBOR data")

        initial_byte = data[offset]
        major_type = initial_byte >> 5
        additional_info = initial_byte & 0x1F
        offset += 1

        # Get the value/length
        if additional_info < 24:
            value = additional_info
        elif additional_info == 24:
            value = data[offset]
            offset += 1
        elif additional_info == 25:
            value = struct.unpack(">H", data[offset : offset + 2])[0]
            offset += 2
        elif additional_info == 26:
            value = struct.unpack(">I", data[offset : offset + 4])[0]
            offset += 4
        elif additional_info == 27:
            value = struct.unpack(">Q", data[offset : offset + 8])[0]
            offset += 8
        else:
            value = additional_info

        if major_type == 0:  # Unsigned integer
            return value, offset
        elif major_type == 1:  # Negative integer
            return -1 - value, offset
        elif major_type == 2:  # Byte string
            return data[offset : offset + value], offset + value
        elif major_type == 3:  # Text string
            return data[offset : offset + value].decode("utf-8"), offset + value
        elif major_type == 4:  # Array
            result_array: list[Any] = []
            for _ in range(value):
                item, offset = decode(data, offset)
                result_array.append(item)
            return result_array, offset
        elif major_type == 5:  # Map
            result_map: dict[Any, Any] = {}
            for _ in range(value):
                key, offset = decode(data, offset)
                val, offset = decode(data, offset)
                result_map[key] = val
            return result_map, offset
        elif major_type == 7:  # Special/float
            if additional_info == 20:
                return False, offset - 1 + 1
            elif additional_info == 21:
                return True, offset - 1 + 1
            elif additional_info == 22:
                return None, offset - 1 + 1
            else:
                return None, offset
        else:
            raise ValueError(f"Unsupported CBOR major type: {major_type}")

    result, _ = decode(data)
    return result


def encode_cbor_public_key(key_data: dict[int, Any]) -> bytes:
    """
    Encode a COSE public key to CBOR format.
    """

    def encode_value(value: Any) -> bytes:
        if isinstance(value, int):
            if value >= 0:
                if value < 24:
                    return bytes([value])
                elif value < 256:
                    return bytes([24, value])
                elif value < 65536:
                    return bytes([25]) + struct.pack(">H", value)
                else:
                    return bytes([26]) + struct.pack(">I", value)
            else:
                neg_val = -1 - value
                if neg_val < 24:
                    return bytes([0x20 | neg_val])
                elif neg_val < 256:
                    return bytes([0x38, neg_val])
                elif neg_val < 65536:
                    return bytes([0x39]) + struct.pack(">H", neg_val)
                else:
                    return bytes([0x3A]) + struct.pack(">I", neg_val)
        elif isinstance(value, bytes):
            if len(value) < 24:
                return bytes([0x40 | len(value)]) + value
            elif len(value) < 256:
                return bytes([0x58, len(value)]) + value
            else:
                return bytes([0x59]) + struct.pack(">H", len(value)) + value
        elif isinstance(value, str):
            encoded = value.encode("utf-8")
            if len(encoded) < 24:
                return bytes([0x60 | len(encoded)]) + encoded
            elif len(encoded) < 256:
                return bytes([0x78, len(encoded)]) + encoded
            else:
                return bytes([0x79]) + struct.pack(">H", len(encoded)) + encoded
        elif isinstance(value, dict):
            result = bytes([0xA0 | len(value)])
            for k, v in value.items():
                result += encode_value(k) + encode_value(v)
            return result
        else:
            raise ValueError(f"Unsupported type: {type(value)}")

    return encode_value(key_data)


def parse_authenticator_data(auth_data: bytes) -> dict[str, Any]:
    """
    Parse authenticator data from WebAuthn response.

    Returns:
        Dictionary containing:
        - rp_id_hash: SHA-256 hash of the RP ID
        - flags: Flags byte
        - sign_count: Signature counter
        - attested_credential_data: Optional credential data (for registration)
        - extensions: Optional extension data
    """
    if len(auth_data) < 37:
        raise VerificationError("Authenticator data too short")

    result: dict[str, Any] = {
        "rp_id_hash": auth_data[:32],
        "flags": auth_data[32],
        "sign_count": struct.unpack(">I", auth_data[33:37])[0],
    }

    # Check if attested credential data is present (bit 6)
    if result["flags"] & 0x40:
        if len(auth_data) < 55:
            raise VerificationError("Authenticator data too short for attested credential")

        aaguid = auth_data[37:53]
        cred_id_length = struct.unpack(">H", auth_data[53:55])[0]

        if len(auth_data) < 55 + cred_id_length:
            raise VerificationError("Authenticator data too short for credential ID")

        credential_id = auth_data[55 : 55 + cred_id_length]

        # The rest is the CBOR-encoded public key
        public_key_cbor = auth_data[55 + cred_id_length :]
        public_key = parse_cbor(public_key_cbor)

        result["attested_credential_data"] = {
            "aaguid": aaguid,
            "credential_id": credential_id,
            "public_key": public_key,
            "public_key_cbor": public_key_cbor,
        }

    return result


def verify_registration(
    credential: dict[str, Any],
    expected_challenge: bytes,
    allowed_origins: list[str] | None = None,
    expected_rp_id: str | None = None,
) -> dict[str, Any]:
    """
    Verify a WebAuthn registration response.

    Args:
        credential: The credential response from the client
        expected_challenge: The challenge that was sent to the client
        allowed_origins: Allowed origins (defaults to settings)
        expected_rp_id: Expected RP ID (defaults to settings)

    Returns:
        Dictionary containing verified credential data:
        - credential_id: The credential ID
        - public_key: The public key in CBOR format
        - sign_count: Initial signature counter
        - backed_up: Whether the credential is backed up
        - device_type: The device type
        - transports: List of supported transports

    Raises:
        VerificationError: If verification fails
    """
    if allowed_origins is None:
        allowed_origins = get_allowed_origins()
    if expected_rp_id is None:
        expected_rp_id = get_rp_id()

    try:
        # Get the response data
        response = credential.get("response", {})
        client_data_json = base64url_to_bytes(response.get("clientDataJSON", ""))
        attestation_object = base64url_to_bytes(response.get("attestationObject", ""))

        # Parse client data
        import json

        client_data = json.loads(client_data_json.decode("utf-8"))

        # Verify client data type
        if client_data.get("type") != "webauthn.create":
            raise VerificationError("Invalid client data type")

        # Verify challenge
        received_challenge = base64url_to_bytes(client_data.get("challenge", ""))
        if received_challenge != expected_challenge:
            raise VerificationError("Challenge mismatch")

        # Verify origin
        actual_origin = client_data.get("origin")
        if actual_origin not in allowed_origins:
            raise VerificationError(f"Origin mismatch: {actual_origin} not in {allowed_origins}")

        # Parse attestation object (CBOR encoded)
        attestation = parse_cbor(attestation_object)
        auth_data = attestation.get("authData", b"")

        # Parse authenticator data
        parsed_auth_data = parse_authenticator_data(auth_data)

        # Verify RP ID hash
        expected_rp_id_hash = hashlib.sha256(expected_rp_id.encode("utf-8")).digest()
        if parsed_auth_data["rp_id_hash"] != expected_rp_id_hash:
            raise VerificationError("RP ID hash mismatch")

        # Verify user presence (bit 0)
        if not (parsed_auth_data["flags"] & 0x01):
            raise VerificationError("User presence flag not set")

        # Get credential data
        attested_data = parsed_auth_data.get("attested_credential_data")
        if not attested_data:
            raise VerificationError("No attested credential data")

        # Determine if credential is backed up (bit 4)
        backed_up = bool(parsed_auth_data["flags"] & 0x10)

        # Get transports from credential if available
        transports = credential.get("response", {}).get("transports", [])
        if not transports:
            transports = credential.get("transports", [])

        # Determine device type based on authenticator attachment
        device_type = credential.get("authenticatorAttachment", "platform")

        return {
            "credential_id": attested_data["credential_id"],
            "public_key": encode_cbor_public_key(attested_data["public_key"]),
            "sign_count": parsed_auth_data["sign_count"],
            "backed_up": backed_up,
            "device_type": device_type,
            "transports": transports,
        }

    except VerificationError:
        raise
    except Exception as e:
        raise VerificationError(f"Registration verification failed: {e!s}") from e


def verify_authentication(
    credential: dict[str, Any],
    expected_challenge: bytes,
    stored_public_key: bytes,
    stored_sign_count: int,
    allowed_origins: list[str] | None = None,
    expected_rp_id: str | None = None,
) -> dict[str, Any]:
    """
    Verify a WebAuthn authentication response.

    Args:
        credential: The credential response from the client
        expected_challenge: The challenge that was sent to the client
        stored_public_key: The stored public key in CBOR format
        stored_sign_count: The stored signature counter
        allowed_origins: Allowed origins (defaults to settings)
        expected_rp_id: Expected RP ID (defaults to settings)

    Returns:
        Dictionary containing:
        - new_sign_count: The new signature counter

    Raises:
        VerificationError: If verification fails
    """
    if allowed_origins is None:
        allowed_origins = get_allowed_origins()
    if expected_rp_id is None:
        expected_rp_id = get_rp_id()

    try:
        # Get the response data
        response = credential.get("response", {})
        client_data_json = base64url_to_bytes(response.get("clientDataJSON", ""))
        authenticator_data = base64url_to_bytes(response.get("authenticatorData", ""))
        signature = base64url_to_bytes(response.get("signature", ""))

        # Parse client data
        import json

        client_data = json.loads(client_data_json.decode("utf-8"))

        # Verify client data type
        if client_data.get("type") != "webauthn.get":
            raise VerificationError("Invalid client data type")

        # Verify challenge
        received_challenge = base64url_to_bytes(client_data.get("challenge", ""))
        if received_challenge != expected_challenge:
            raise VerificationError("Challenge mismatch")

        # Verify origin
        actual_origin = client_data.get("origin")
        if actual_origin not in allowed_origins:
            raise VerificationError(f"Origin mismatch: {actual_origin} not in {allowed_origins}")

        # Parse authenticator data
        parsed_auth_data = parse_authenticator_data(authenticator_data)

        # Verify RP ID hash
        expected_rp_id_hash = hashlib.sha256(expected_rp_id.encode("utf-8")).digest()
        if parsed_auth_data["rp_id_hash"] != expected_rp_id_hash:
            raise VerificationError("RP ID hash mismatch")

        # Verify user presence (bit 0)
        if not (parsed_auth_data["flags"] & 0x01):
            raise VerificationError("User presence flag not set")

        # Verify signature counter (should be greater than stored, unless it's 0)
        new_sign_count = parsed_auth_data["sign_count"]
        if stored_sign_count > 0 and new_sign_count <= stored_sign_count:
            raise VerificationError(
                "Signature counter not incremented - possible cloned authenticator"
            )

        # Verify signature
        # The signature is over: authenticator_data || SHA-256(client_data_json)
        client_data_hash = hashlib.sha256(client_data_json).digest()
        signed_data = authenticator_data + client_data_hash

        # Parse the stored public key
        public_key_data = parse_cbor(stored_public_key)

        # Get algorithm (key type 3)
        alg = public_key_data.get(3)
        kty = public_key_data.get(1)

        if alg == -7 and kty == 2:  # ES256 (ECDSA with P-256)
            # Build the public key from x and y coordinates
            x = public_key_data.get(-2)
            y = public_key_data.get(-3)
            if not x or not y:
                raise VerificationError("Invalid public key: missing coordinates")

            # Create the EC public key
            from cryptography.hazmat.primitives.asymmetric.ec import (
                SECP256R1,
                EllipticCurvePublicNumbers,
            )

            x_int = int.from_bytes(x, "big")
            y_int = int.from_bytes(y, "big")
            ec_public_numbers = EllipticCurvePublicNumbers(x_int, y_int, SECP256R1())
            ec_public_key = ec_public_numbers.public_key(default_backend())

            # Verify the signature
            try:
                ec_public_key.verify(signature, signed_data, ec.ECDSA(hashes.SHA256()))
            except Exception:
                raise VerificationError("Signature verification failed")

        elif alg == -257 and kty == 3:  # RS256 (RSASSA-PKCS1-v1_5 with SHA-256)
            # Get the RSA public key components
            n = public_key_data.get(-1)  # modulus
            e = public_key_data.get(-2)  # exponent
            if not n or not e:
                raise VerificationError("Invalid public key: missing RSA components")

            from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers

            n_int = int.from_bytes(n, "big")
            e_int = int.from_bytes(e, "big")
            rsa_public_numbers = RSAPublicNumbers(e_int, n_int)
            rsa_public_key = rsa_public_numbers.public_key(default_backend())

            try:
                rsa_public_key.verify(signature, signed_data, padding.PKCS1v15(), hashes.SHA256())
            except Exception:
                raise VerificationError("Signature verification failed")
        else:
            raise VerificationError(f"Unsupported algorithm: kty={kty}, alg={alg}")

        return {
            "new_sign_count": new_sign_count,
        }

    except VerificationError:
        raise
    except Exception as e:
        raise VerificationError(f"Authentication verification failed: {e!s}") from e
