from time import perf_counter
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from solar_sites.config import Settings
from solar_sites.platform.errors import STATUSES, error_response
from solar_sites.platform.logging import log_request_completed, log_request_exception
from solar_sites.platform.requests import (
    read_body,
    replay_body,
    validate_host,
    validate_origin_and_content_type,
)
from solar_sites.shared.errors import AppError


class RequestBoundary:
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        self.app, self.settings = app, settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        started_at = perf_counter()
        status: int | None = None
        started = False

        async def secured_send(message: Message) -> None:
            nonlocal started, status
            if message["type"] == "http.response.start":
                started = True
                status = message["status"]
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                headers["X-Content-Type-Options"] = "nosniff"
                headers["Referrer-Policy"] = "same-origin"
                if scope["path"].startswith("/api/"):
                    headers["Cache-Control"] = "no-store"
            await send(message)

        # After headers are sent, propagate failures rather than send a second response.
        try:
            await self._serve(scope, receive, secured_send)
        except AppError as exc:
            if started:
                raise
            await error_response(
                request_id,
                exc.code,
                exc.message,
                exception=exc if STATUSES[exc.code] >= 500 else None,
            )(scope, receive, secured_send)
        except TimeoutError:
            if started:
                raise
            await error_response(request_id, "HTTP_ERROR", "Request body timed out.", status=408)(
                scope, receive, secured_send
            )
        except Exception:
            log_request_exception(scope, request_id)
            if started:
                raise
            await error_response(request_id, "INTERNAL_ERROR", "An unexpected error occurred.")(
                scope, receive, secured_send
            )
        finally:
            log_request_completed(scope, request_id, status, started_at)

    async def _serve(self, scope: Scope, receive: Receive, send: Send) -> None:
        headers = Headers(scope=scope)
        validate_host(headers=headers, allowed_hosts=self.settings.allowed_hosts)
        validate_origin_and_content_type(
            headers=headers,
            method=scope["method"],
            path=scope["path"],
            allowed_origins=self.settings.allowed_origins,
        )

        body = await read_body(receive=receive, max_bytes=self.settings.max_body_bytes)
        if body is None:
            return

        await self.app(scope, replay_body(body, receive), send)
