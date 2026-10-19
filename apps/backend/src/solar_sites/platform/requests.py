import asyncio
from urllib.parse import urlsplit

from starlette.datastructures import Headers
from starlette.types import Message, Receive

from solar_sites.shared.errors import AppError


def validate_host(*, headers: Headers, allowed_hosts: list[str]) -> None:
    hosts = headers.getlist("host")

    try:
        parsed = urlsplit("//" + hosts[0]) if len(hosts) == 1 else None
        host = parsed.hostname if parsed is not None else None
        if parsed is not None:
            # Accessing the port also rejects malformed port values.
            _ = parsed.port
            if parsed.username or parsed.path or parsed.query or parsed.fragment:
                host = None
    except ValueError:
        host = None

    if host not in allowed_hosts:
        raise AppError("HOST_FORBIDDEN", "This request host is not allowed.")


def validate_origin_and_content_type(
    *, headers: Headers, method: str, path: str, allowed_origins: list[str]
) -> None:
    if method in {"GET", "HEAD", "OPTIONS"}:
        return

    origins = headers.getlist("origin")
    if len(origins) != 1 or origins[0] not in allowed_origins:
        raise AppError("ORIGIN_FORBIDDEN", "This request origin is not allowed.")

    if method in {"POST", "PUT", "PATCH"} and path != "/api/logout":
        content_type = headers.get("content-type", "").split(";", 1)[0].lower()
        if content_type != "application/json":
            raise AppError("UNSUPPORTED_MEDIA_TYPE", "Send the request as application/json.")


async def read_body(*, receive: Receive, max_bytes: int) -> bytes | None:
    body = bytearray()
    async with asyncio.timeout(10):
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return None

            chunk = message.get("body", b"")
            if len(body) + len(chunk) > max_bytes:
                raise AppError("REQUEST_TOO_LARGE", "The request body is too large.")
            body.extend(chunk)
            if not message.get("more_body", False):
                return bytes(body)


def replay_body(body: bytes, receive: Receive) -> Receive:
    consumed = False

    async def bounded_receive() -> Message:
        nonlocal consumed
        if consumed:
            return await receive()

        # Replay the validated body once, then forward disconnects to the application.
        consumed = True
        return {"type": "http.request", "body": body, "more_body": False}

    return bounded_receive
