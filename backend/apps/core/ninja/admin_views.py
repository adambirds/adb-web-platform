from django.http import HttpRequest
from ninja import Router

from apps.core.models import Brand
from authentication.ninja.schemas import ProblemDetail

from .schemas import BrandOut

core_admin_router = Router(tags=["admin-core"])


@core_admin_router.get(
    "/brands",
    response={200: list[BrandOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_brands(request: HttpRequest):
    if not request.user.is_authenticated:
        return 401, {
            "message": "User not authenticated",
            "success": False,
            "code": "unauthenticated",
        }
    if not (request.user.is_staff or request.user.is_superuser):
        return 403, {
            "message": "You do not have permission to access this resource.",
            "success": False,
            "code": "forbidden",
        }
    if not request.user.has_perm("core.view_brand"):
        return 403, {
            "message": "You do not have permission to view brands.",
            "success": False,
            "code": "forbidden",
        }

    return [
        BrandOut(
            id=brand.id,
            name=brand.name,
            slug=brand.slug,
            domain=brand.domain,
            is_active=brand.is_active,
        )
        for brand in Brand.objects.order_by("name")
    ]
