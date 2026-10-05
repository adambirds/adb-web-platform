from __future__ import annotations

import base64
import json
import time
from typing import Any
from urllib.parse import urlparse

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from django.conf import settings
from django.core.cache import cache


class GitHubError(RuntimeError):
    """Safe integration errors; never include remote response bodies or secrets."""


def app_token() -> str:
    if not settings.GITHUB_APP_ID or not settings.GITHUB_APP_PRIVATE_KEY:
        raise GitHubError("Configure GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY first.")
    try:
        pem = settings.GITHUB_APP_PRIVATE_KEY.replace("\\n", "\n").strip()
        key = serialization.load_pem_private_key(pem.encode(), password=None)
        if not isinstance(key, rsa.RSAPrivateKey):
            raise ValueError("RSA required")
        now = int(time.time())
        parts = [
            {"alg": "RS256", "typ": "JWT"},
            {"iat": now - 60, "exp": now + 540, "iss": str(settings.GITHUB_APP_ID)},
        ]
        encoded = b".".join(
            base64.urlsafe_b64encode(json.dumps(part, separators=(",", ":")).encode()).rstrip(b"=")
            for part in parts
        )
        signature = key.sign(encoded, padding.PKCS1v15(), hashes.SHA256())
        return (encoded + b"." + base64.urlsafe_b64encode(signature).rstrip(b"=")).decode()
    except Exception as exc:
        raise GitHubError(
            "GITHUB_APP_PRIVATE_KEY must contain a valid unencrypted RSA PEM key."
        ) from exc


class GitHubClient:
    def __init__(self, installation_id: int | None = None) -> None:
        self.installation_id = installation_id

    def request(self, method: str, path: str, data: dict[str, Any] | None = None) -> Any:
        if not path.startswith("/") or path.startswith("//"):
            raise GitHubError("Invalid GitHub API path.")
        try:
            response = requests.request(
                method,
                "https://api.github.com" + path,
                json=data,
                timeout=20,
                headers={
                    "Authorization": "Bearer " + self.token(),
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2026-03-10",
                },
                allow_redirects=False,
            )
            if response.status_code == 401 and self.installation_id:
                cache.delete(f"github-installation-token:{self.installation_id}")
            if response.status_code not in (200, 201, 202, 204):
                raise GitHubError(
                    f"GitHub returned HTTP {response.status_code}. Check App access and permissions."
                )
            return response.json() if response.content else None
        except requests.RequestException as exc:
            raise GitHubError("GitHub could not be reached. Try again shortly.") from exc

    def token(self) -> str:
        if self.installation_id is None:
            return app_token()
        cache_key = f"github-installation-token:{self.installation_id}"
        token = cache.get(cache_key)
        if isinstance(token, str):
            return token
        result = GitHubClient().request(
            "POST", f"/app/installations/{self.installation_id}/access_tokens"
        )
        token = str(result["token"])
        cache.set(cache_key, token, 2700)
        return token

    def pages(self, path: str, key: str | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        separator = "&" if "?" in path else "?"
        for page in range(1, 101):
            data = self.request("GET", f"{path}{separator}per_page=100&page={page}")
            batch = data[key] if key else data
            results.extend(batch)
            if len(batch) < 100:
                return results
        raise GitHubError("GitHub pagination limit reached; synchronisation is incomplete.")

    def job_logs(self, full_name: str, job_id: int) -> tuple[str, bool]:
        try:
            response = requests.get(
                f"https://api.github.com/repos/{full_name}/actions/jobs/{job_id}/logs",
                headers={
                    "Authorization": "Bearer " + self.token(),
                    "Accept": "application/vnd.github+json",
                },
                timeout=20,
                allow_redirects=False,
            )
            location = response.headers.get("Location", "")
            parsed = urlparse(location)
            hostname = parsed.hostname or ""
            if (
                response.status_code != 302
                or parsed.scheme != "https"
                or not any(
                    hostname.endswith("." + domain) or hostname == domain
                    for domain in ("githubusercontent.com", "blob.core.windows.net", "github.com")
                )
            ):
                raise GitHubError("GitHub logs are not available for this job.")
            # Never forward the installation token to signed object-storage URLs.
            with requests.get(location, timeout=20, stream=True, allow_redirects=False) as download:
                if download.status_code != 200:
                    raise GitHubError("GitHub logs could not be downloaded.")
                content = bytearray()
                for chunk in download.iter_content(8192):
                    content.extend(chunk)
                    if len(content) > 262144:
                        return bytes(content[:262144]).decode("utf-8", errors="replace"), True
                return bytes(content).decode("utf-8", errors="replace"), False
        except requests.RequestException as exc:
            raise GitHubError("GitHub logs could not be reached.") from exc
