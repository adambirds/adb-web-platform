from io import BytesIO
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.ticketing.services.scanning import (
    AttachmentScanError,
    ClamAVScanner,
)


class FakeSocket:
    def __init__(self, reply: bytes) -> None:
        self.reply = reply
        self.sent: list[bytes] = []
        self.timeout: int | None = None
        self._read = False

    def __enter__(self) -> "FakeSocket":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def settimeout(self, timeout: int) -> None:
        self.timeout = timeout

    def sendall(self, payload: bytes) -> None:
        self.sent.append(payload)

    def recv(self, size: int) -> bytes:
        del size
        if self._read:
            return b""
        self._read = True
        return self.reply


class ClamAVScannerTests(SimpleTestCase):
    @patch("apps.ticketing.services.scanning.socket.create_connection")
    def test_clean_stream_returns_safe_verdict(self, create_connection) -> None:
        fake_socket = FakeSocket(b"stream: OK\0")
        create_connection.return_value = fake_socket
        scanner = ClamAVScanner("clamav.internal", 3310, timeout_seconds=7)

        result = scanner.scan(BytesIO(b"safe attachment"))

        self.assertTrue(result.clean)
        self.assertEqual(result.signature, "")
        create_connection.assert_called_once_with(("clamav.internal", 3310), timeout=7)
        self.assertEqual(fake_socket.timeout, 7)
        self.assertEqual(fake_socket.sent[0], b"zINSTREAM\0")
        self.assertEqual(fake_socket.sent[-1], b"\x00\x00\x00\x00")
        self.assertIn(b"safe attachment", fake_socket.sent)

    @patch("apps.ticketing.services.scanning.socket.create_connection")
    def test_infected_stream_returns_signature(self, create_connection) -> None:
        create_connection.return_value = FakeSocket(b"stream: Eicar-Signature FOUND\0")
        scanner = ClamAVScanner()

        result = scanner.scan(BytesIO(b"malicious attachment"))

        self.assertFalse(result.clean)
        self.assertEqual(result.signature, "Eicar-Signature")

    @patch("apps.ticketing.services.scanning.socket.create_connection")
    def test_indeterminate_reply_fails_closed(self, create_connection) -> None:
        create_connection.return_value = FakeSocket(b"stream: scanner error ERROR\0")
        scanner = ClamAVScanner()

        with self.assertRaisesMessage(AttachmentScanError, "indeterminate"):
            scanner.scan(BytesIO(b"attachment"))

    @patch(
        "apps.ticketing.services.scanning.socket.create_connection",
        side_effect=OSError("connection refused"),
    )
    def test_connection_failure_is_a_scan_error(self, create_connection) -> None:
        scanner = ClamAVScanner()

        with self.assertRaisesMessage(AttachmentScanError, "connect"):
            scanner.scan(BytesIO(b"attachment"))

        create_connection.assert_called_once()
