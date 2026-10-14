"""Export public WordPress content and media into a portable offline archive."""

from __future__ import annotations

import base64
import hashlib
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

import requests

EXPORT_FORMAT = "adb-wordpress-export"
EXPORT_VERSION = 1
MAX_MEDIA_BYTES = 8 * 1024 * 1024
MAX_TOTAL_MEDIA_BYTES = 128 * 1024 * 1024


class WordPressExportError(ValueError):
    """An incomplete or invalid WordPress export must not replace the archive."""


class WordPressExporter:
    def __init__(self, origin: str, progress: Callable[[str], None]) -> None:
        parsed = urlsplit(origin)
        if parsed.scheme != "https" or not parsed.hostname or parsed.query or parsed.fragment:
            raise WordPressExportError("Use the HTTPS URL of the WordPress site.")
        if parsed.username or parsed.password:
            raise WordPressExportError("The public export must not contain credentials.")
        self.origin = origin.rstrip("/")
        self.progress = progress
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "ADB public WordPress migration export"

    def collection(self, endpoint: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        total: int | None = None
        page = 1
        while True:
            params: dict[str, str | int] = {
                "per_page": 100,
                "page": page,
                "orderby": "id",
                "order": "asc",
            }
            response = self.session.get(
                f"{self.origin}/wp-json/wp/v2/{endpoint}",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
                raise WordPressExportError(f"{endpoint}: expected a WordPress record list.")
            try:
                expected = int(response.headers["X-WP-Total"])
                pages = max(1, int(response.headers["X-WP-TotalPages"]))
            except (KeyError, ValueError) as error:
                raise WordPressExportError(
                    f"{endpoint}: pagination headers are missing."
                ) from error
            if total is not None and expected != total:
                raise WordPressExportError(f"{endpoint}: content changed during export; run again.")
            total = expected
            records.extend(payload)
            self.progress(f"{endpoint}: page {page}/{pages}")
            if page >= pages:
                break
            page += 1
        ids = [row.get("id") for row in records]
        if len(records) != total or len(set(ids)) != len(ids):
            raise WordPressExportError(f"{endpoint}: incomplete or duplicate record inventory.")
        return records

    def media_bytes(self, record: dict[str, Any]) -> bytes:
        # Optimole can rewrite source_url. Prefer the original WordPress upload file.
        details = record.get("media_details", {})
        file = details.get("file") if isinstance(details, dict) else None
        url = (
            f"{self.origin}/wp-content/uploads/{file}"
            if isinstance(file, str) and file and ".." not in file.split("/")
            else record.get("source_url")
        )
        if not isinstance(url, str) or urlsplit(url).scheme not in {"https", "http"}:
            raise WordPressExportError(f"Media {record.get('id')}: no downloadable URL.")
        with self.session.get(url, timeout=30, stream=True) as response:
            response.raise_for_status()
            chunks: list[bytes] = []
            size = 0
            for chunk in response.iter_content(chunk_size=64 * 1024):
                size += len(chunk)
                if size > MAX_MEDIA_BYTES:
                    raise WordPressExportError(f"Media {record['id']} exceeds the 8 MB limit.")
                chunks.append(chunk)
        return b"".join(chunks)

    def export(self) -> dict[str, Any]:
        try:
            response = self.session.get(f"{self.origin}/wp-json/wp/v2/types", timeout=30)
            response.raise_for_status()
            types = response.json()
            if not isinstance(types, dict):
                raise WordPressExportError("WordPress content types are unavailable.")
            collections = {
                name: self.collection(endpoint)
                for name, endpoint in {
                    "posts": "posts",
                    "pages": "pages",
                    "categories": "categories",
                    "tags": "tags",
                    "authors": "users",
                    "media": "media",
                }.items()
            }
            project_type = types.get("project")
            collections["projects"] = (
                self.collection(project_type["rest_base"])
                if isinstance(project_type, dict) and project_type.get("rest_namespace") == "wp/v2"
                else []
            )
            total_size = 0
            for record in collections["media"]:
                data = self.media_bytes(record)
                total_size += len(data)
                if total_size > MAX_TOTAL_MEDIA_BYTES:
                    raise WordPressExportError("Media exceeds the 128 MB archive limit.")
                record["archive_file"] = {
                    "encoding": "base64",
                    "size": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "data": base64.b64encode(data).decode("ascii"),
                }
                self.progress(f"Archived media {record['id']}: {len(data)} bytes")
            return {
                "format": EXPORT_FORMAT,
                "version": EXPORT_VERSION,
                "source": self.origin,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "counts": {name: len(rows) for name, rows in collections.items()},
                "collections": collections,
                "scope": "Public content only. Pages are archived for reference, not imported as marketing pages.",
            }
        except requests.RequestException as error:
            raise WordPressExportError(f"WordPress request failed: {error}") from error
        finally:
            self.session.close()


def route_manifest(collections: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, str]]:
    """Small frontend routing data, kept separate from the media-filled archive."""
    ids: dict[str, str] = {}
    aliases: dict[str, str] = {}
    for name, query in (("pages", "page_id"), ("posts", "p"), ("projects", "p")):
        for row in collections[name]:
            path = urlsplit(row["link"]).path
            ids[f"{query}:{row['id']}"] = path
            if name in {"posts", "projects"}:
                destination = "blog" if name == "posts" else "portfolio"
                aliases[path.rstrip("/")] = f"/{destination}/{row['slug']}/"
    for row in collections["categories"]:
        aliases[urlsplit(row["link"]).path.rstrip("/")] = f"/blog/category/{row['slug']}/"
    return {"wordpress_urls": ids, "editorial_aliases": aliases}
