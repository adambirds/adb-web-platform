"""Import an offline WordPress archive as brand-scoped editorial drafts."""

from __future__ import annotations

import base64
import binascii
import hashlib
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any
from urllib.parse import unquote, urljoin, urlsplit

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from PIL import Image, ImageOps, UnidentifiedImageError

from apps.core.models import Brand
from apps.website.models import BlogCategory, BlogPost, BlogTag, Portfolio

from .wordpress_export import EXPORT_FORMAT, EXPORT_VERSION, MAX_MEDIA_BYTES, MAX_TOTAL_MEDIA_BYTES
from .wordpress_html import html_to_markdown, plain_text

COLLECTIONS = ("posts", "pages", "projects", "categories", "tags", "authors", "media")


class WordPressImportError(ValueError):
    """Reject inconsistent or unsafe archives before writing any CMS records."""


@dataclass
class ImportResult:
    posts: int = 0
    projects: int = 0
    skipped: list[str] = field(default_factory=list)
    images: int = 0


def rendered(record: dict[str, Any], name: str) -> str:
    value = record.get(name, {})
    if not isinstance(value, dict) or not isinstance(value.get("rendered", ""), str):
        raise WordPressImportError(
            f"Invalid rendered {name} in WordPress record {record.get('id')}."
        )
    if value.get("protected"):
        raise WordPressImportError(
            "Password-protected content requires a separate authenticated export."
        )
    return str(value.get("rendered", ""))


def validate_archive(archive: Any) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(archive, dict) or archive.get("format") != EXPORT_FORMAT:
        raise WordPressImportError(
            "Expected a complete adb-wordpress-export archive, not a posts-only list."
        )
    if archive.get("version") != EXPORT_VERSION:
        raise WordPressImportError("Unsupported WordPress export version.")
    source = urlsplit(str(archive.get("source", "")))
    if source.scheme != "https" or not source.hostname or source.username or source.password:
        raise WordPressImportError("Archive has an invalid public source URL.")
    collections = archive.get("collections")
    counts = archive.get("counts")
    if not isinstance(collections, dict) or not isinstance(counts, dict):
        raise WordPressImportError("Archive collections/counts are missing.")
    for name in COLLECTIONS:
        rows = collections.get(name)
        if not isinstance(rows, list) or counts.get(name) != len(rows):
            raise WordPressImportError(f"Archive count mismatch: {name}.")
        ids: set[int] = set()
        slugs: set[str] = set()
        for row in rows:
            if not isinstance(row, dict) or type(row.get("id")) is not int or row["id"] <= 0:
                raise WordPressImportError(f"Invalid WordPress ID in {name}.")
            if row["id"] in ids:
                raise WordPressImportError(f"Duplicate WordPress ID in {name}.")
            ids.add(row["id"])
            if name in {"posts", "projects", "categories", "tags"}:
                slug = row.get("slug")
                if not isinstance(slug, str) or not slug or len(slug) > 50 or slug in slugs:
                    raise WordPressImportError(f"Invalid, duplicate or overlong slug in {name}.")
                slugs.add(slug)
            if name in {"posts", "projects"}:
                if row.get("status") != "publish":
                    raise WordPressImportError(
                        "Only publicly published WordPress records may be imported."
                    )
                title = plain_text(rendered(row, "title"))
                if not title or len(title) > 200:
                    raise WordPressImportError(f"Invalid title for {row['slug']}.")
                rendered(row, "content")
                rendered(row, "excerpt")
                if urlsplit(str(row.get("link", ""))).hostname != source.hostname:
                    raise WordPressImportError(
                        "WordPress permalink does not belong to the source site."
                    )
    return collections


def media_file_key(url: str) -> str:
    path = unquote(urlsplit(url).path)
    marker = "/wp-content/uploads/"
    return path.split(marker, 1)[1] if marker in path else path


def prepare_media(rows: list[dict[str, Any]]) -> dict[int, tuple[bytes, str]]:
    prepared: dict[int, tuple[bytes, str]] = {}
    total_size = 0
    for row in rows:
        file = row.get("archive_file")
        if not isinstance(file, dict) or file.get("encoding") != "base64":
            raise WordPressImportError(f"Media {row['id']} is missing its offline file data.")
        encoded = file.get("data")
        if not isinstance(encoded, str) or len(encoded) > (MAX_MEDIA_BYTES + 2) * 4 // 3:
            raise WordPressImportError(f"Media {row['id']} has invalid or oversized data.")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as error:
            raise WordPressImportError("Corrupt base64 image data.") from error
        total_size += len(data)
        digest = hashlib.sha256(data).hexdigest()
        if len(data) != file.get("size") or digest != file.get("sha256"):
            raise WordPressImportError(f"Media {row['id']} failed its integrity check.")
        if len(data) > MAX_MEDIA_BYTES or total_size > MAX_TOTAL_MEDIA_BYTES:
            raise WordPressImportError("Archive media exceeds import limits.")
        if row.get("mime_type") not in {"image/jpeg", "image/png", "image/webp"}:
            # Non-editorial file types remain in the versioned archive for manual review.
            continue
        try:
            with Image.open(BytesIO(data)) as image:
                if (
                    image.format not in {"JPEG", "PNG", "WEBP"}
                    or image.width * image.height > 20_000_000
                ):
                    raise WordPressImportError("Unsupported image or excessive dimensions.")
                clean = ImageOps.exif_transpose(image).convert("RGBA")
                clean.thumbnail((2400, 2400))
                output = BytesIO()
                clean.save(output, format="WEBP", quality=88)
                prepared[row["id"]] = (output.getvalue(), digest)
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
            raise WordPressImportError(f"Media {row['id']} is not a valid raster image.") from error
    return prepared


def import_wordpress_archive(
    archive: Any, brand: Brand, *, media_base_url: str, dry_run: bool = False
) -> ImportResult:
    collections = validate_archive(archive)
    origin = str(archive["source"])
    if (
        urlsplit(origin).hostname
        != urlsplit(
            "https://" + brand.domain.removeprefix("https://").removeprefix("http://")
        ).hostname
    ):
        raise WordPressImportError("The archive source must match the selected Brand's domain.")
    prepared = prepare_media(collections["media"])
    if prepared and not dry_run and not urlsplit(str(default_storage.url("test.webp"))).scheme:
        parsed_base = urlsplit(media_base_url)
        if parsed_base.scheme not in {"https", "http"} or not parsed_base.hostname:
            raise WordPressImportError(
                "Set --media-base-url to the publicly reachable backend/media origin."
            )
    result = ImportResult()
    posts = [
        row
        for row in collections["posts"]
        if not BlogPost.objects.filter(slug=row["slug"]).exists()
    ]
    projects = [
        row
        for row in collections["projects"]
        if not Portfolio.objects.filter(slug=row["slug"]).exists()
    ]
    result.skipped = [
        f"post:{row['slug']} (existing record preserved)"
        for row in collections["posts"]
        if row not in posts
    ]
    result.skipped += [
        f"project:{row['slug']} (existing record preserved)"
        for row in collections["projects"]
        if row not in projects
    ]
    category_rows = {row["id"]: row for row in collections["categories"]}
    tag_rows = {row["id"]: row for row in collections["tags"]}
    author_rows = {row["id"]: row for row in collections["authors"]}
    for post_record in posts:
        for name, records in (("categories", category_rows), ("tags", tag_rows)):
            values = post_record.get(name, [])
            if not isinstance(values, list) or any(
                type(value) is not int or value not in records for value in values
            ):
                raise WordPressImportError(f"Missing or invalid {name} for {post_record['slug']}.")
    for model, rows in ((BlogCategory, collections["categories"]), (BlogTag, collections["tags"])):
        for row in rows:
            existing = model.objects.filter(slug=row["slug"]).first()
            if existing is not None and not existing.brands.filter(pk=brand.pk).exists():
                raise WordPressImportError(
                    f"Taxonomy collision: {row['slug']} belongs outside this Brand. No records changed."
                )
    for row in posts + projects:
        featured = row.get("featured_media", 0)
        if type(featured) is not int or (featured and featured not in prepared):
            raise WordPressImportError(
                f"Missing/unsupported offline featured image for {row['slug']}."
            )
    result.posts = len(posts)
    result.projects = len(projects)
    if dry_run or (not posts and not projects):
        return result
    saved_files: list[str] = []
    image_names: dict[int, str] = {}
    source_images: dict[str, int] = {}
    for row in collections["media"]:
        source_images[media_file_key(str(row.get("source_url", "")))] = row["id"]
        details = row.get("media_details", {})
        if isinstance(details, dict) and details.get("file"):
            source_images[str(details["file"])] = row["id"]
    permalink_map = {
        row["link"].rstrip("/"): f"/blog/{row['slug']}/" for row in collections["posts"]
    }
    permalink_map.update(
        {row["link"].rstrip("/"): f"/portfolio/{row['slug']}/" for row in collections["projects"]}
    )

    def image_name(media_id: int) -> str:
        if media_id not in image_names:
            data, digest = prepared[media_id]
            name = f"wordpress-import/{digest}.webp"
            if not default_storage.exists(name):
                name = default_storage.save(name, ContentFile(data))
                saved_files.append(name)
            image_names[media_id] = name
        return image_names[media_id]

    def image_url(url: str) -> str:
        media_id = source_images.get(media_file_key(url))
        if media_id in prepared:
            return urljoin(
                media_base_url.rstrip("/") + "/", default_storage.url(image_name(media_id))
            )
        return url

    def markdown(row: dict[str, Any], name: str) -> str:
        return html_to_markdown(
            rendered(row, name),
            origin,
            lambda url: permalink_map.get(url.rstrip("/"), url),
            image_url,
        )

    try:
        with transaction.atomic():
            categories: dict[int, BlogCategory] = {}
            tags: dict[int, BlogTag] = {}
            for row in collections["categories"]:
                item, created = BlogCategory.objects.get_or_create(
                    slug=row["slug"],
                    defaults={
                        "name": str(row["name"])[:100],
                        "description": plain_text(str(row.get("description", ""))),
                    },
                )
                if created:
                    item.brands.add(brand)
                categories[row["id"]] = item
            for row in collections["tags"]:
                tag, created = BlogTag.objects.get_or_create(
                    slug=row["slug"], defaults={"name": str(row["name"])[:100]}
                )
                if created:
                    tag.brands.add(brand)
                tags[row["id"]] = tag
            for row in posts:
                metadata = row.get("yoast_head_json", {})
                post = BlogPost.objects.create(
                    title=plain_text(rendered(row, "title")),
                    slug=row["slug"],
                    excerpt=plain_text(rendered(row, "excerpt"))[:500],
                    content=markdown(row, "content"),
                    author=str(
                        author_rows.get(row.get("author"), {}).get("name", "Unknown author")
                    )[:100],
                    published=False,
                    published_at=None,
                    featured=False,
                    meta_description=str(metadata.get("description", ""))[:160]
                    if isinstance(metadata, dict)
                    else "",
                    featured_image=image_name(row["featured_media"])
                    if row.get("featured_media")
                    else "",
                    featured_image_alt=plain_text(
                        str(
                            next(
                                (
                                    media.get("alt_text", "")
                                    for media in collections["media"]
                                    if media["id"] == row.get("featured_media")
                                ),
                                "",
                            )
                        )
                    )[:300],
                )
                post.brands.add(brand)
                post.categories.set([categories[value] for value in row.get("categories", [])])
                post.tags.set([tags[value] for value in row.get("tags", [])])
            for row in projects:
                portfolio = Portfolio.objects.create(
                    title=plain_text(rendered(row, "title")),
                    slug=row["slug"],
                    description=plain_text(rendered(row, "excerpt")),
                    challenge="",
                    solution=markdown(row, "content"),
                    results="",
                    technologies="",
                    published=False,
                    featured=False,
                    image=image_name(row["featured_media"]) if row.get("featured_media") else "",
                )
                portfolio.brands.add(brand)
    except Exception:
        for name in saved_files:
            default_storage.delete(name)
        raise
    result.images = len(image_names)
    return result
