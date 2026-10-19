from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from solar_sites.config import Settings
from solar_sites.infra.database import Database


# settings
def get_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


SettingsDep = Annotated[Settings, Depends(get_settings)]


# database
def get_database(request: Request) -> Database:
    return cast(Database, request.app.state.database)


DatabaseDep = Annotated[Database, Depends(get_database)]


# session
async def get_session(database: DatabaseDep) -> AsyncIterator[AsyncSession]:
    async with database.sessions() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
