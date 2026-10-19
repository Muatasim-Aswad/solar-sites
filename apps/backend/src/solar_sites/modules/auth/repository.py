from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from solar_sites.modules.auth.models import Session, User


async def add_user(db: AsyncSession, *, user: User) -> None:
    db.add(user)
    await db.flush()


async def get_user_by_email(db: AsyncSession, *, email: str) -> User | None:
    return await db.scalar(select(User).where(User.email == email))


async def add_session(db: AsyncSession, *, session: Session) -> None:
    db.add(session)
    await db.flush()


async def get_active_session(
    db: AsyncSession,
    *,
    session_hash: bytes,
    now: int,
) -> tuple[Session, User] | None:
    result = (
        await db.execute(
            select(Session, User)
            .join(User)
            .where(
                Session.session_token_hash == session_hash,
                Session.expires_at > now,
            )
        )
    ).one_or_none()
    if result is None:
        return None
    return result[0], result[1]


async def delete_expired_sessions(db: AsyncSession, *, now: int) -> None:
    await db.execute(delete(Session).where(Session.expires_at <= now))


async def delete_session(db: AsyncSession, *, session_hash: bytes) -> None:
    await db.execute(delete(Session).where(Session.session_token_hash == session_hash))
