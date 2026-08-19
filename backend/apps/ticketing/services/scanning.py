from __future__ import annotations

import os
import socket
import struct
from dataclasses import dataclass
from typing import BinaryIO, Protocol

DEFAULT_CLAMAV_HOST = "clamav"
DEFAULT_CLAMAV_PORT = 3310
DEFAULT_CLAMAV_TIMEOUT_SECONDS = 30
CLAMAV_STREAM_CHUNK_BYTES = 1024 * 1024
MAX_CLAMAV_REPLY_BYTES = 64 * 1024


class AttachmentScanError(RuntimeError):
    """Raised when an attachment scanner cannot return a trustworthy verdict."""


@dataclass(frozen=True, slots=True)
class AttachmentScanResult:
    clean: bool
    signature: str = ""


class AttachmentScanner(Protocol):
    engine_name: str

    def scan(self, stream: BinaryIO) -> AttachmentScanResult: ...


class ClamAVScanner:
    """Scan attachment bytes using clamd's framed INSTREAM protocol."""

    engine_name = "clamav"

    def __init__(
        self,
        host: str = DEFAULT_CLAMAV_HOST,
        port: int = DEFAULT_CLAMAV_PORT,
        *,
        timeout_seconds: int = DEFAULT_CLAMAV_TIMEOUT_SECONDS,
    ) -> None:
        self._host = host.strip()
        self._port = port
        self._timeout_seconds = timeout_seconds
        if not self._host:
            raise AttachmentScanError("ClamAV host must be configured.")
        if not (1 <= self._port <= 65535):
            raise AttachmentScanError("ClamAV port is invalid.")
        if self._timeout_seconds <= 0:
            raise AttachmentScanError("ClamAV timeout must be positive.")

    def scan(self, stream: BinaryIO) -> AttachmentScanResult:
        try:
            connection = socket.create_connection(
                (self._host, self._port),
                timeout=self._timeout_seconds,
            )
        except OSError as exc:
            raise AttachmentScanError("Unable to connect to the ClamAV scanner.") from exc

        try:
            with connection:
                connection.settimeout(self._timeout_seconds)
                connection.sendall(b"zINSTREAM\0")
                while True:
                    chunk = stream.read(CLAMAV_STREAM_CHUNK_BYTES)
                    if not chunk:
                        break
                    connection.sendall(struct.pack(">I", len(chunk)))
                    connection.sendall(chunk)
                connection.sendall(struct.pack(">I", 0))
                reply = self._read_reply(connection)
        except (OSError, TimeoutError) as exc:
            raise AttachmentScanError("ClamAV scan transport failed.") from exc

        return self._parse_reply(reply)

    @staticmethod
    def _read_reply(connection: socket.socket) -> bytes:
        response = bytearray()
        while b"\0" not in response:
            chunk = connection.recv(4096)
            if not chunk:
                break
            response.extend(chunk)
            if len(response) > MAX_CLAMAV_REPLY_BYTES:
                raise AttachmentScanError("ClamAV returned an oversized scan response.")

        record = bytes(response).split(b"\0", 1)[0]
        if not record:
            raise AttachmentScanError("ClamAV returned no scan verdict.")
        return record

    @staticmethod
    def _parse_reply(reply: bytes) -> AttachmentScanResult:
        text = reply.decode("utf-8", "replace").strip()
        if text == "stream: OK":
            return AttachmentScanResult(clean=True)
        if text.startswith("stream: ") and text.endswith(" FOUND"):
            signature = text[len("stream: ") : -len(" FOUND")].strip()
            return AttachmentScanResult(clean=False, signature=signature or "Malware detected")
        raise AttachmentScanError("ClamAV returned an indeterminate scan verdict.")


def clamav_scanner_from_environment() -> ClamAVScanner:
    """Build the ClamAV client from worker environment configuration."""
    return ClamAVScanner(
        host=os.environ.get("TICKETING_CLAMAV_HOST", DEFAULT_CLAMAV_HOST),
        port=_environment_int("TICKETING_CLAMAV_PORT", DEFAULT_CLAMAV_PORT),
        timeout_seconds=_environment_int(
            "TICKETING_CLAMAV_TIMEOUT_SECONDS",
            DEFAULT_CLAMAV_TIMEOUT_SECONDS,
        ),
    )


def _environment_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name, "").strip()
    if not raw_value:
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise AttachmentScanError(f"{name} must be an integer.") from exc
