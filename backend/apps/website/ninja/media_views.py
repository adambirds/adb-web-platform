"""Capability-protected raster image uploads for editorial content."""

from io import BytesIO
from typing import Literal
from uuid import uuid4

from django.core.files.base import ContentFile
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import File, Router
from ninja.files import UploadedFile
from PIL import Image, ImageOps, UnidentifiedImageError

from apps.website.models import BlogPost, Portfolio, Testimonial
from authentication.ninja.schemas import ProblemDetail

from .admin_views import require_permission
from .schemas import ContentImageOut
from .views import build_image_url

website_media_router = Router()

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000


def content_image_item(kind: str, item_id: int) -> Portfolio | BlogPost | Testimonial:
    if kind == "portfolio":
        return get_object_or_404(Portfolio, id=item_id)
    if kind == "blogpost":
        return get_object_or_404(BlogPost, id=item_id)
    return get_object_or_404(Testimonial, id=item_id)


def allowed_image_field(kind: str, field: str) -> bool:
    return (
        field
        in {
            "portfolio": {"image", "featured_image"},
            "blogpost": {"featured_image"},
            "testimonial": {"image"},
        }[kind]
    )


@website_media_router.post(
    "/website/media/{kind}/{item_id}/{field}",
    response={
        200: ContentImageOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        413: ProblemDetail,
    },
)
def upload_content_image(
    request: HttpRequest,
    kind: Literal["portfolio", "blogpost", "testimonial"],
    item_id: int,
    field: str,
    image: File[UploadedFile],
) -> ContentImageOut | tuple[int, dict[str, str | bool]]:
    permission_error = require_permission(request, f"website.change_{kind}")
    if permission_error:
        return permission_error
    if not allowed_image_field(kind, field):
        return 400, {"message": "Invalid image field.", "success": False, "code": "invalid_field"}
    if image.size is None or image.size > MAX_IMAGE_BYTES:
        return 413, {
            "message": "Images must be smaller than 8 MB.",
            "success": False,
            "code": "too_large",
        }
    item = content_image_item(kind, item_id)
    try:
        with Image.open(image) as source:
            if (
                source.format not in {"PNG", "JPEG", "WEBP"}
                or source.width * source.height > MAX_IMAGE_PIXELS
            ):
                raise ValueError("Unsupported image or excessive dimensions.")
            clean = ImageOps.exif_transpose(source).convert("RGBA")
            clean.thumbnail((2400, 2400))
            output = BytesIO()
            clean.save(output, format="WEBP", quality=88)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        return 400, {
            "message": "Upload a valid PNG, JPEG or WebP image.",
            "success": False,
            "code": "invalid_image",
        }
    stored = getattr(item, field)
    previous = stored.name
    stored.save(f"{uuid4().hex}.webp", ContentFile(output.getvalue()), save=True)
    if previous and previous != stored.name:
        stored.storage.delete(previous)
    return ContentImageOut(image_url=build_image_url(request, stored))


@website_media_router.delete(
    "/website/media/{kind}/{item_id}/{field}",
    response={200: ContentImageOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail},
)
def remove_content_image(
    request: HttpRequest,
    kind: Literal["portfolio", "blogpost", "testimonial"],
    item_id: int,
    field: str,
) -> ContentImageOut | tuple[int, dict[str, str | bool]]:
    permission_error = require_permission(request, f"website.change_{kind}")
    if permission_error:
        return permission_error
    if not allowed_image_field(kind, field):
        return 400, {"message": "Invalid image field.", "success": False, "code": "invalid_field"}
    stored = getattr(content_image_item(kind, item_id), field)
    stored.delete(save=True)
    return ContentImageOut(image_url=None)
