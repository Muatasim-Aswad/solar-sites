import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from solar_sites.config import Settings
from solar_sites.modules.auth.routes import router as auth_router
from solar_sites.modules.energy.routes import router as energy_router
from solar_sites.modules.sites.routes import router as sites_router
from solar_sites.platform.dependencies import DatabaseDep
from solar_sites.platform.errors import ERROR_RESPONSES, install_error_handlers
from solar_sites.platform.middleware import RequestBoundary
from solar_sites.platform.spa import SpaFiles
from solar_sites.runtime import open_runtime


class Health(BaseModel):
    status: str


def create_app(
    settings: Settings | None = None,
    *,
    pvgis_transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        async with open_runtime(settings, pvgis_transport=pvgis_transport) as resources:
            app.state.settings = resources.settings
            app.state.database = resources.database
            app.state.passwords = resources.passwords
            app.state.solar = resources.solar
            yield

    app = FastAPI(
        title="Solar sites",
        version="0.1.0",
        lifespan=lifespan,
        responses=ERROR_RESPONSES,
    )

    app.add_middleware(RequestBoundary, settings=settings)
    install_error_handlers(app)

    app.include_router(auth_router)
    app.include_router(sites_router)
    app.include_router(energy_router)

    @app.get("/healthz", response_model=Health, operation_id="health")
    async def health() -> Health:
        return Health(status="ok")

    @app.get("/readyz", response_model=Health, operation_id="ready")
    async def ready(database: DatabaseDep) -> Health:
        try:
            async with asyncio.timeout(2):
                await database.ping()
        except (TimeoutError, OSError, SQLAlchemyError) as exc:
            raise HTTPException(status_code=503) from exc
        return Health(status="ready")

    if settings.frontend_path is not None:
        app.mount(
            "/",
            SpaFiles(directory=settings.frontend_path),
            name="frontend",
        )

    return app
