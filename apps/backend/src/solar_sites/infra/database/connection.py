from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import URL, Connection, event, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def run_migrations(connection: Connection) -> None:
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parent / "migrations"))
    config.attributes["connection"] = connection
    command.upgrade(config, "head")


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.engine = create_async_engine(
            URL.create("sqlite+aiosqlite", database=str(path)), connect_args={"timeout": 10}
        )
        event.listen(self.engine.sync_engine, "connect", self._configure_connection)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    @staticmethod
    def _configure_connection(connection: object, _: object) -> None:
        # SQLAlchemy's adapted sqlite connection exposes the DBAPI cursor protocol.
        from typing import Any, cast

        cursor = cast(Any, connection).cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=10000")
        cursor.close()

    async def start(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with self.engine.begin() as connection:
            await connection.exec_driver_sql("PRAGMA journal_mode=WAL")
            await connection.run_sync(run_migrations)

    async def ping(self) -> None:
        async with self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    async def close(self) -> None:
        await self.engine.dispose()
