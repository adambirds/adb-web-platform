from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncGenerator
from importlib import import_module
from urllib.parse import urlsplit

from channels.db import database_sync_to_async
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse, StreamingHttpResponse
from django.utils.crypto import constant_time_compare
from redis.asyncio import Redis
from redis.exceptions import RedisError

from authentication.models import User

from .events import LiveChange, can_receive, channel_name, topics_for


def stream_user(session_key: str, user_id: str) -> User | None:
    store = import_module(settings.SESSION_ENGINE).SessionStore(session_key=session_key)
    session = store.load()
    if str(session.get("_auth_user_id", "")) != user_id:
        return None
    user = User.objects.filter(pk=user_id, is_active=True, is_staff=True).first()
    if not user:
        return None
    stored_hash = session.get("_auth_user_hash", "")
    hashes = [user.get_session_auth_hash(), *user.get_session_auth_fallback_hash()]
    return user if any(constant_time_compare(stored_hash, value) for value in hashes) else None


def frame(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, separators=(',', ':'))}\n\n"


async def stream(session_key: str, user_id: str) -> AsyncGenerator[str, None]:
    client = None
    try:
        client = Redis.from_url(str(settings.CACHES["default"]["LOCATION"]), decode_responses=True)
        async with client.pubsub() as subscription:
            await subscription.subscribe(channel_name())
            yield "retry: 3000\n" + frame("ready", {})
            heartbeat = time.monotonic()
            while True:
                message = await subscription.get_message(ignore_subscribe_messages=True, timeout=1)
                if message or time.monotonic() - heartbeat >= 15:
                    user = await database_sync_to_async(stream_user)(session_key, user_id)
                    if user is None:
                        yield frame("expired", {})
                        return
                    if message and message["type"] == "message":
                        try:
                            change = LiveChange.decode(message["data"])
                        except (ValueError, TypeError, KeyError):
                            continue
                        if await database_sync_to_async(can_receive)(user, change):
                            # Only topics leave the server; internal scope IDs never reach the browser.
                            yield frame("change", {"topics": topics_for(change)})
                    if time.monotonic() - heartbeat >= 15:
                        yield ": heartbeat\n\n"
                        heartbeat = time.monotonic()
                await asyncio.sleep(0.01)
    except (RedisError, OSError, ValueError):
        yield frame("unavailable", {})
    finally:
        if client is not None:
            await client.aclose()


def live_events(request: HttpRequest) -> HttpResponse | StreamingHttpResponse:
    if request.method != "GET":
        return JsonResponse({"detail": "GET required."}, status=405)
    origin = request.headers.get("Origin")
    current = urlsplit(request.build_absolute_uri())
    same_origin = f"{current.scheme}://{current.netloc}"
    if origin and origin != same_origin and origin not in settings.CORS_ALLOWED_ORIGINS:
        return JsonResponse({"detail": "Origin not allowed."}, status=403)
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)
    if not request.user.is_active or not request.user.is_staff:
        return JsonResponse({"detail": "Staff access required."}, status=403)
    if not request.session.session_key:
        return JsonResponse({"detail": "A valid session is required."}, status=401)
    response = StreamingHttpResponse(
        stream(request.session.session_key, str(request.user.pk)), content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-store, no-transform"
    response["X-Accel-Buffering"] = "no"
    return response
