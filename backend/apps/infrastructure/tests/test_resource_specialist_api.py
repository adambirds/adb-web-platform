from typing import cast

from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.core.ownership import OwnershipType
from apps.infrastructure.models import InfrastructureResource, Licence, LicenceResourceIdentity
from apps.infrastructure.ninja.resource_schemas import InfrastructureResourceDetailOut
from apps.infrastructure.ninja.resource_views import get_infrastructure_resource
from authentication.models import User


class SpecialistResourceApiTests(TestCase):
    def test_resource_detail_returns_safe_legacy_specialist_fields(self) -> None:
        user = User.objects.create_superuser(
            email="specialist-api@example.com",
            password="test-password",
            first_name="Specialist",
            last_name="Admin",
        )
        licence = Licence.objects.create(
            name="Operations subscription",
            licence_type="subscription",
            vendor="Example Vendor",
            renewal_date="2027-04-01",
            portal_url="https://vendor.example.com/account",
            licence_key="never-return-this-value",
            notes="Do not expose arbitrary legacy notes either.",
        )
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Operations subscription",
            resource_type=InfrastructureResource.ResourceType.LICENCE,
        )
        LicenceResourceIdentity.objects.create(licence=licence, resource=resource)
        request = RequestFactory().get(f"/api/admin/infrastructure/resources/{resource.id}")
        request.user = user

        result = cast(
            InfrastructureResourceDetailOut,
            get_infrastructure_resource(cast(HttpRequest, request), resource.id),
        )

        self.assertIsNotNone(result.legacy_reference)
        assert result.legacy_reference is not None
        fields = {field.key: field for field in result.legacy_reference.fields}
        self.assertEqual(result.legacy_reference.legacy_type, "licence")
        self.assertEqual(
            result.legacy_reference.register_path,
            "/admin/infrastructure/licences",
        )
        self.assertEqual(fields["vendor"].value, "Example Vendor")
        self.assertEqual(fields["portal_url"].kind, "url")
        self.assertNotIn("licence_key", fields)
        self.assertNotIn("notes", fields)
        self.assertNotIn(
            "never-return-this-value",
            {field.value for field in result.legacy_reference.fields},
        )
