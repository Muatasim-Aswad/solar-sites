import calendar
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from solar_sites.config import Settings
from solar_sites.main import create_app

ORIGIN = "http://testserver"
PASSWORD = "correct horse battery staple"
SITE = {
    "clientName": "Sample household",
    "address": "Example street 10",
    "latitude": 52.08,
    "longitude": 4.31,
    "peakKwp": 5,
}


def monthly_payload() -> dict[str, Any]:
    return {
        "outputs": {
            "monthly": {"fixed": [{"month": month, "E_m": 100.0} for month in range(1, 13)]},
            "totals": {"fixed": {"E_y": 1200.0}},
        }
    }


def hourly_payload(year: int = 2023, minute: int = 10) -> dict[str, Any]:
    start = datetime(year, 1, 1, 0, minute)
    return {
        "outputs": {
            "hourly": [
                {
                    "time": (start + timedelta(hours=index)).strftime("%Y%m%d:%H%M"),
                    "P": 2000.0 if index % 2 == 0 else 0.0,
                }
                for index in range(8784 if calendar.isleap(year) else 8760)
            ]
        }
    }


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_path=tmp_path / "database.sqlite3",
        allowed_hosts=["testserver"],
        allowed_origins=[ORIGIN],
    )


@pytest.fixture
def upstream_requests() -> list[httpx.Request]:
    return []


@pytest.fixture
def app(settings: Settings, upstream_requests: list[httpx.Request]) -> FastAPI:
    def handler(request: httpx.Request) -> httpx.Response:
        upstream_requests.append(request)
        payload = monthly_payload() if request.url.path.endswith("PVcalc") else hourly_payload()
        return httpx.Response(200, json=payload)

    return create_app(settings, pvgis_transport=httpx.MockTransport(handler))


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url=ORIGIN, headers={"Origin": ORIGIN}
        ) as client:
            yield client


async def register(client: httpx.AsyncClient, email: str = "advisor@example.com") -> str:
    response = await client.post("/api/register", json={"email": email, "password": PASSWORD})
    assert response.status_code == 201, response.text
    csrf = response.json()["csrfToken"]
    client.headers["X-CSRF-Token"] = csrf
    return str(csrf)


async def create_site(client: httpx.AsyncClient) -> str:
    response = await client.post("/api/sites", json=SITE)
    assert response.status_code == 201, response.text
    return str(response.json()["id"])
