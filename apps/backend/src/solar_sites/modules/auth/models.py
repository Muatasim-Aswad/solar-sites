from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, LargeBinary, Text
from sqlalchemy.orm import Mapped, mapped_column

from solar_sites.infra.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(trim(email)) > 0"),
        CheckConstraint("length(password_hash) > 0"),
        {"sqlite_strict": True},
    )
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    email: Mapped[str] = mapped_column(Text(collation="NOCASE"), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint("length(session_token_hash) = 32"),
        CheckConstraint("length(csrf_token) > 0"),
        CheckConstraint("expires_at > created_at"),
        Index("ix_sessions_user_id", "user_id"),
        Index("ix_sessions_expires_at", "expires_at"),
        {"sqlite_strict": True},
    )
    session_token_hash: Mapped[bytes] = mapped_column(LargeBinary, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    csrf_token: Mapped[str] = mapped_column(Text)
    created_at: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[int] = mapped_column(Integer)
