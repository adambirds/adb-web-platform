import urllib.error
from datetime import timedelta
from email.message import Message
from io import BytesIO
from subprocess import CompletedProcess
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.core.ownership import OwnershipType
from apps.infrastructure.models import InfrastructureResource
from apps.infrastructure.web_domain_models import DomainProfile
from apps.monitoring.execution import execute_check
from apps.monitoring.models import MonitorCheck


class MonitorExecutionTests(TestCase):
    def test_icmp_probe_uses_bounded_non_shell_ping_command(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Ping target",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        check = MonitorCheck(
            resource=resource,
            name="ICMP reachability",
            check_type=MonitorCheck.CheckType.ICMP,
            target="192.0.2.10",
            timeout_seconds=4,
        )

        with patch("apps.monitoring.execution.subprocess.run") as run:
            run.return_value = CompletedProcess(args=["ping"], returncode=0)
            observation = execute_check(check)

        self.assertTrue(observation.successful)
        self.assertFalse(observation.execution_error)
        self.assertEqual(observation.observed_value, "192.0.2.10")
        run.assert_called_once_with(
            ["ping", "-n", "-c", "1", "-W", "4", "192.0.2.10"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

    def test_icmp_probe_records_no_reply_as_check_failure(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Unreachable target",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        check = MonitorCheck(
            resource=resource,
            name="ICMP reachability",
            check_type=MonitorCheck.CheckType.ICMP,
            target="198.51.100.10",
        )

        with patch("apps.monitoring.execution.subprocess.run") as run:
            run.return_value = CompletedProcess(args=["ping"], returncode=1)
            observation = execute_check(check)

        self.assertFalse(observation.successful)
        self.assertFalse(observation.execution_error)
        self.assertEqual(observation.message, "ICMP echo request did not receive a reply.")

    def test_http_error_status_is_a_failed_check_not_execution_error(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="HTTP target",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
        )
        check = MonitorCheck(
            resource=resource,
            name="Website health",
            check_type=MonitorCheck.CheckType.HTTP,
            target="https://example.test/health",
        )
        http_error = urllib.error.HTTPError(
            url=check.target,
            code=503,
            msg="Service Unavailable",
            hdrs=Message(),
            fp=BytesIO(b"maintenance"),
        )

        with patch(
            "apps.monitoring.execution.urllib.request.urlopen",
            side_effect=http_error,
        ):
            observation = execute_check(check)

        self.assertFalse(observation.successful)
        self.assertFalse(observation.execution_error)
        self.assertEqual(observation.status_code, 503)
        self.assertEqual(observation.message, "HTTP 503.")

    def test_domain_expiry_probe_uses_structured_domain_profile_expiry(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="example.test",
            resource_type=InfrastructureResource.ResourceType.DOMAIN,
        )
        expiry = timezone.localdate() + timedelta(days=45)
        DomainProfile.objects.create(
            resource=resource,
            domain_name="example.test",
            expires_on=expiry,
        )
        check = MonitorCheck(
            resource=resource,
            name="Domain expiry",
            check_type=MonitorCheck.CheckType.DOMAIN_EXPIRY,
            target="example.test",
            expiry_warning_days=30,
        )

        observation = execute_check(check)

        self.assertTrue(observation.successful)
        self.assertFalse(observation.execution_error)
        self.assertEqual(observation.observed_value, expiry.isoformat())
        self.assertEqual(observation.message, "Domain expires in 45 days.")

    def test_domain_expiry_probe_warns_inside_threshold(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="expiring.example.test",
            resource_type=InfrastructureResource.ResourceType.DOMAIN,
        )
        expiry = timezone.localdate() + timedelta(days=10)
        DomainProfile.objects.create(
            resource=resource,
            domain_name="expiring.example.test",
            expires_on=expiry,
        )
        check = MonitorCheck(
            resource=resource,
            name="Domain expiry",
            check_type=MonitorCheck.CheckType.DOMAIN_EXPIRY,
            target="expiring.example.test",
            expiry_warning_days=30,
        )

        observation = execute_check(check)

        self.assertFalse(observation.successful)
        self.assertFalse(observation.execution_error)
        self.assertEqual(observation.observed_value, expiry.isoformat())

    def test_domain_expiry_probe_requires_managed_expiry_metadata(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="unknown.example.test",
            resource_type=InfrastructureResource.ResourceType.DOMAIN,
        )
        DomainProfile.objects.create(
            resource=resource,
            domain_name="unknown.example.test",
        )
        check = MonitorCheck(
            resource=resource,
            name="Domain expiry",
            check_type=MonitorCheck.CheckType.DOMAIN_EXPIRY,
            target="unknown.example.test",
        )

        observation = execute_check(check)

        self.assertFalse(observation.successful)
        self.assertTrue(observation.execution_error)
        self.assertEqual(
            observation.message,
            "Domain expiry date is not configured for this resource.",
        )
