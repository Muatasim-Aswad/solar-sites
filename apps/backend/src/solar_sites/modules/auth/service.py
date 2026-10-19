import hashlib
import secrets
import time
from dataclasses import dataclass
from uuid import uuid7

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from solar_sites.modules.auth import repository
from solar_sites.modules.auth.models import Session, User
from solar_sites.modules.auth.passwords import Passwords
from solar_sites.shared.errors import AppError


def token_hash(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()


@dataclass(frozen=True)
class Identity:
    user_id: str
    email: str
    session_hash: bytes
    csrf_token: str


@dataclass(frozen=True)
class NewSession:
    token: str
    csrf_token: str


async def register(
    db: AsyncSession,
    *,
    passwords: Passwords,
    session_age: int,
    email: str,
    password: str,
    previous_token: str | None,
) -> NewSession:
    password_hash = await passwords.hash(password=password)
    user = User(id=str(uuid7()), email=email, password_hash=password_hash)

    try:
        async with db.begin():
            await repository.add_user(db, user=user)
            session = await _create_session(
                db, session_age=session_age, user_id=user.id, previous_token=previous_token
            )
    except IntegrityError as exc:
        raise AppError("EMAIL_EXISTS", "An account with this email already exists.") from exc
    return session


async def login(
    db: AsyncSession,
    *,
    passwords: Passwords,
    session_age: int,
    email: str,
    password: str,
    previous_token: str | None,
) -> NewSession:
    async with db.begin():
        user = await repository.get_user_by_email(db, email=email)

    # Verify unknown accounts too, without holding a database transaction during hashing.
    verified = await passwords.verify(
        password=password, hashed=user.password_hash if user else passwords.dummy_hash
    )
    if user is None or not verified:
        raise AppError("INVALID_CREDENTIALS", "Email or password is incorrect.")

    async with db.begin():
        session = await _create_session(
            db, session_age=session_age, user_id=user.id, previous_token=previous_token
        )
    return session


async def _create_session(
    db: AsyncSession, *, session_age: int, user_id: str, previous_token: str | None
) -> NewSession:
    now = int(time.time())
    await repository.delete_expired_sessions(db, now=now)
    if previous_token and len(previous_token) <= 128:
        await repository.delete_session(
            db,
            session_hash=token_hash(previous_token),
        )

    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    await repository.add_session(
        db,
        session=Session(
            session_token_hash=token_hash(token),
            user_id=user_id,
            csrf_token=csrf,
            created_at=now,
            expires_at=now + session_age,
        ),
    )
    return NewSession(token, csrf)


async def authenticate(db: AsyncSession, *, token: str | None) -> Identity:
    if not token or len(token) > 128:
        raise AppError("UNAUTHENTICATED", "Please sign in.")

    async with db.begin():
        result = await repository.get_active_session(
            db,
            session_hash=token_hash(token),
            now=int(time.time()),
        )

        if result is None:
            raise AppError("UNAUTHENTICATED", "Your session is missing or expired. Please sign in.")
        session, user = result
        return Identity(user.id, user.email, session.session_token_hash, session.csrf_token)


async def logout(db: AsyncSession, *, identity: Identity) -> None:
    async with db.begin():
        await repository.delete_session(db, session_hash=identity.session_hash)
