from __future__ import annotations

import socket
import ssl
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from urllib.parse import urlparse

from django.utils import timezone
from icmplib import ICMPLibError, SocketPermissionError, ping

from .models import MonitorCheck
from .services import CheckObservation


def _timed_observation(
    operation: Callable[[], tuple[bool, str, int | None, str]],
) -> CheckObservation:
    started_at = timezone.now()
    started = time.monotonic()
    try:
        successful, message, status_code, observed_value = operation()
        execution_error = False
    except (OSError, ValueError, urllib.error.URLError) as error:
        successful = False
        message = str(error)
        status_code = None
        observed_value = ""
        execution_error = True
    finished_at = timezone.now()
    return CheckObservation(
        successful=successful,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=max(0, round((time.monotonic() - started) * 1000)),
        message=message,
        status_code=status_code,
        observed_value=observed_value,
        execution_error=execution_error,
    )


def execute_check(check: MonitorCheck) -> CheckObservation:
    """Execute supported unauthenticated probes without persisting secret material."""
    timeout = check.timeout_seconds

    if check.check_type == MonitorCheck.CheckType.ICMP:

        def icmp_probe() -> tuple[bool, str, int | None, str]:
            try:
                result = ping(check.target, count=1, interval=0, timeout=timeout, privileged=False)
            except SocketPermissionError as error:
                raise OSError(
                    "ICMP socket permission denied. On Linux, allow the monitoring worker's "
                    "group in net.ipv4.ping_group_range."
                ) from error
            except ICMPLibError as error:
                raise OSError(f"ICMP probe could not execute: {error}") from error
            successful = bool(result.is_alive)
            return (
                successful,
                "ICMP echo reply received."
                if successful
                else "ICMP echo request did not receive a reply.",
                None,
                check.target,
            )

        return _timed_observation(icmp_probe)

    if check.check_type == MonitorCheck.CheckType.TCP:

        def tcp_probe() -> tuple[bool, str, int | None, str]:
            assert check.port is not None
            with socket.create_connection((check.target, check.port), timeout=timeout):
                return True, "TCP connection succeeded.", None, f"{check.target}:{check.port}"

        return _timed_observation(tcp_probe)

    if check.check_type in [MonitorCheck.CheckType.HTTP, MonitorCheck.CheckType.CONTENT]:

        def http_probe() -> tuple[bool, str, int | None, str]:
            request = urllib.request.Request(
                check.target,
                headers={"User-Agent": "ADB-Monitor/1.0"},
            )
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    body = response.read(1_000_000).decode("utf-8", errors="replace")
                    status_code = response.status
            except urllib.error.HTTPError as error:
                try:
                    body = error.read(1_000_000).decode("utf-8", errors="replace")
                finally:
                    error.close()
                status_code = error.code

            successful = 200 <= status_code < 400
            if not successful:
                return False, f"HTTP {status_code}.", status_code, ""
            if check.check_type == MonitorCheck.CheckType.CONTENT:
                if check.expected_value and check.expected_value not in body:
                    return False, "Expected content was not present.", status_code, ""
                if check.forbidden_value and check.forbidden_value in body:
                    return False, "Forbidden content was present.", status_code, ""
            return True, f"HTTP {status_code}.", status_code, ""

        return _timed_observation(http_probe)

    if check.check_type == MonitorCheck.CheckType.DNS:

        def dns_probe() -> tuple[bool, str, int | None, str]:
            addresses = sorted({str(item[4][0]) for item in socket.getaddrinfo(check.target, None)})
            observed = ", ".join(addresses)
            matches = not check.expected_value or check.expected_value in addresses
            return (
                matches,
                "DNS lookup succeeded." if matches else "DNS value did not match.",
                None,
                observed,
            )

        return _timed_observation(dns_probe)

    if check.check_type == MonitorCheck.CheckType.TLS:

        def tls_probe() -> tuple[bool, str, int | None, str]:
            parsed = urlparse(check.target if "://" in check.target else f"https://{check.target}")
            hostname = parsed.hostname
            if not hostname:
                raise ValueError("TLS target does not contain a hostname.")
            port = parsed.port or check.port or 443
            context = ssl.create_default_context()
            with (
                socket.create_connection((hostname, port), timeout=timeout) as raw_socket,
                context.wrap_socket(raw_socket, server_hostname=hostname) as tls_socket,
            ):
                certificate = tls_socket.getpeercert()
            if certificate is None:
                raise ValueError("TLS peer did not provide certificate metadata.")
            expiry_text = str(certificate.get("notAfter", ""))
            expiry = datetime.strptime(expiry_text, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=UTC)
            days = (expiry - timezone.now()).days
            return (
                days >= check.expiry_warning_days,
                f"TLS certificate expires in {days} days.",
                None,
                expiry.isoformat(),
            )

        return _timed_observation(tls_probe)

    if check.check_type == MonitorCheck.CheckType.CERTIFICATE_EXPIRY:

        def certificate_expiry_probe() -> tuple[bool, str, int | None, str]:
            certificate = getattr(check.resource, "tls_certificate", None)
            if certificate is None or certificate.expires_at is None:
                raise ValueError("Certificate expiry is not configured for this resource.")
            if certificate.metadata_refresh_error:
                raise ValueError(
                    f"Certificate metadata refresh failed: {certificate.metadata_refresh_error}"
                )
            days = (certificate.expires_at - timezone.now()).days
            return (
                days >= check.expiry_warning_days,
                f"Certificate expires in {days} days.",
                None,
                certificate.expires_at.isoformat(),
            )

        return _timed_observation(certificate_expiry_probe)

    if check.check_type == MonitorCheck.CheckType.DOMAIN_EXPIRY:

        def domain_expiry_probe() -> tuple[bool, str, int | None, str]:
            domain_profile = getattr(check.resource, "domain_profile", None)
            if domain_profile is None:
                raise ValueError("Domain profile is not configured for this resource.")
            if domain_profile.expires_on is None:
                raise ValueError("Domain expiry date is not configured for this resource.")
            if domain_profile.metadata_refresh_error:
                raise ValueError(
                    f"Domain metadata refresh failed: {domain_profile.metadata_refresh_error}"
                )
            days = (domain_profile.expires_on - timezone.localdate()).days
            if days < 0:
                return (
                    False,
                    f"Domain expired {-days} days ago.",
                    None,
                    domain_profile.expires_on.isoformat(),
                )
            return (
                days >= check.expiry_warning_days,
                f"Domain expires in {days} days.",
                None,
                domain_profile.expires_on.isoformat(),
            )

        return _timed_observation(domain_expiry_probe)

    now = timezone.now()
    return CheckObservation(
        successful=False,
        started_at=now,
        finished_at=now,
        duration_ms=0,
        message=f"{check.get_check_type_display()} execution is not implemented yet.",
        execution_error=True,
    )
