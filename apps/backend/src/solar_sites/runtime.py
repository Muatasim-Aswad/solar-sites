from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx

from solar_sites.config import Settings
from solar_sites.infra.database import Database
from solar_sites.infra.pvgis import Pvgis
from solar_sites.modules.auth import Passwords
from solar_sites.modules.energy import PvgisSolarDataProvider, SolarDataProvider
from solar_sites.platform.logging import configure_logging


@dataclass
class Runtime:
    settings: Settings
    database: Database
    passwords: Passwords
    solar: SolarDataProvider


@asynccontextmanager
async def open_runtime(
    settings: Settings, *, pvgis_transport: httpx.AsyncBaseTransport | None = None
) -> AsyncGenerator[Runtime]:
    configure_logging()
    database = Database(settings.database_path)
    passwords = Passwords()

    try:
        await database.start()
        await passwords.start()

        async with httpx.AsyncClient(
            timeout=settings.pvgis_timeout_seconds,
            limits=httpx.Limits(max_connections=settings.pvgis_concurrency),
            transport=pvgis_transport,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            solar = PvgisSolarDataProvider(client=Pvgis(client=client, settings=settings))
            yield Runtime(settings, database, passwords, solar)
    finally:
        try:
            await passwords.close()
        finally:
            await database.close()
