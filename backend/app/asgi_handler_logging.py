# apps/village/patches/asgi_handler_logging.py
import asyncio
import logging
from collections.abc import Awaitable, Callable, Coroutine, Mapping, MutableMapping
from typing import Any

from django.core.handlers.asgi import ASGIHandler

# Define ASGI types that match Django's ASGIHandler.__call__ signature precisely
Scope = dict[str, Any]
Message = Mapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIAppCoroutine = Coroutine[Any, Any, None]

logger = logging.getLogger("django.request")

# Store the original __call__ method before patching
original_call: Callable[[ASGIHandler, Scope, Receive, Send], ASGIAppCoroutine] = (
    ASGIHandler.__call__
)


async def patched_asgi_handler(
    self: ASGIHandler, scope: Scope, receive: Receive, send: Send
) -> None:
    """
    A patched version of ASGIHandler.__call__ that logs the request body
    for GraphQL requests that result in a 400 Bad Request response.
    """
    if scope.get("type") != "http" or scope.get("path") != "/graphql/":
        await original_call(self, scope, receive, send)
        return

    body: bytes = b""
    more_body: bool = True
    # Internally, we create mutable messages (dicts)
    received_messages: list[MutableMapping[str, Any]] = []

    # Intercept and capture the full request body
    try:
        while more_body:
            message = await receive()
            received_messages.append(dict(message))  # Make a mutable copy
            if message["type"] == "http.request":
                body += message.get("body", b"")
                more_body = message.get("more_body", False)
    except Exception as e:
        logger.warning("[ASGI Patch] Error while reading body: %s", e)
        raise

    # Replay the captured messages to Django via a new receive channel
    message_queue: asyncio.Queue[MutableMapping[str, Any]] = asyncio.Queue()
    for msg in received_messages:
        await message_queue.put(msg)

    async def replay_receive() -> Message:
        return await message_queue.get()

    # Wrap the send channel to intercept the response status code
    status_code_holder: dict[str, int] = {}

    async def wrapped_send(message: Message) -> None:
        if message["type"] == "http.response.start":
            status_code_holder["status"] = message["status"]
        await send(message)

    # Let the original ASGIHandler process the request
    await original_call(self, scope, replay_receive, wrapped_send)

    # If the response status was 400, log the captured body
    if status_code_holder.get("status") == 400:
        logger.warning(
            "[GraphQL 400] Raw request body:\n%s", body.decode("utf-8", errors="replace")
        )


# Apply the patch. We ignore both mypy errors as this is intentional monkey-patching.
ASGIHandler.__call__ = patched_asgi_handler  # type: ignore[method-assign, assignment]
