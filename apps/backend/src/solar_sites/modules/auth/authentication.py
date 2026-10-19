import secrets

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from solar_sites.modules.auth.service import Identity, authenticate
from solar_sites.shared.errors import AppError

COOKIE_NAME = "solar_session"


async def authenticate_request(
    request: Request,
    db: AsyncSession,
    token: str | None,
    csrf_token: str | None,
) -> Identity:
    current_identity = await authenticate(db, token=token)
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        tokens = request.headers.getlist("x-csrf-token")
        if (
            len(tokens) != 1
            or csrf_token is None
            or not secrets.compare_digest(csrf_token.encode(), current_identity.csrf_token.encode())
        ):
            raise AppError(
                "CSRF_FAILED", "The security token is missing or invalid. Refresh and retry."
            )
    return current_identity
