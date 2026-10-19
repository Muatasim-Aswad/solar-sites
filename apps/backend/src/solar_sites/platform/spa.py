import re

from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send

CLIENT_ROUTE = re.compile(r"(?:|login|register|sites(?:/new|/[a-zA-Z0-9-]+(?:/edit)?)?)/?")


class SpaFiles(StaticFiles):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope["path"]
        if "\\" in path or any(part in {".", ".."} for part in path.split("/")):
            raise HTTPException(404)
        await super().__call__(scope, receive, send)

    async def get_response(self, path: str, scope: Scope) -> Response:
        if scope["method"] not in {"GET", "HEAD"}:
            raise HTTPException(405, headers={"Allow": "GET, HEAD"})
        if path == "." or CLIENT_ROUTE.fullmatch(path):
            response = await super().get_response("index.html", scope)
            response.headers["Cache-Control"] = "no-store"
            return response
        if path.startswith("assets/"):
            response = await super().get_response(path, scope)
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return response
        raise HTTPException(404)
