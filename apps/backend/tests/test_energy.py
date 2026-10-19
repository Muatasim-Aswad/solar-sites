import math
import random

import httpx
import pytest
from conftest import ORIGIN, create_site, hourly_payload, monthly_payload, register
from test_auth import assert_error

from solar_sites.config import Settings
from solar_sites.main import create_app
from solar_sites.modules.energy.simulation import equal_hourly_consumption, simulate


def test_uniform_consumption_normal_and_leap_year() -> None:
    for hours in [8760, 8784]:
        assert equal_hourly_consumption(3000, hours) * hours == pytest.approx(3000)
    assert equal_hourly_consumption(0, 8760) == 0


@pytest.mark.parametrize(
    ("annual", "hours"), [(-1, 8760), (math.inf, 8760), (math.nan, 8760), (1, 0), (1, 8785)]
)
def test_invalid_consumption(annual: float, hours: int) -> None:
    with pytest.raises(ValueError):
        equal_hourly_consumption(annual, hours)


def test_battery_exact_flows_and_initially_empty() -> None:
    no_battery = simulate([0, 4, 0, 0], annual_use_kwh=4, capacity_kwh=0)
    battery = simulate([0, 4, 0, 0], annual_use_kwh=4, capacity_kwh=2)
    assert no_battery.self_used_kwh == 1
    assert no_battery.exported_kwh == 3
    assert no_battery.imported_kwh == 3
    assert battery.direct_kwh == 1
    assert battery.battery_supplied_kwh == 2
    assert battery.self_used_kwh == 3
    assert battery.imported_kwh == 1
    assert battery.exported_kwh == 1
    assert battery.stored_kwh == 0
    final_surplus = simulate([0, 5], 2, 10)
    assert final_surplus.self_used_kwh == 1
    assert final_surplus.stored_kwh == 4
    assert final_surplus.imported_kwh == 1


@pytest.mark.parametrize("capacity", [0, 0.1, 1, 10, 100000])
@pytest.mark.parametrize("annual_use", [0, 1000, 5000, 100000])
def test_energy_conservation_over_full_year(capacity: float, annual_use: float) -> None:
    rng = random.Random(42)
    production = [rng.uniform(0, 5) if index % 24 in range(8, 18) else 0 for index in range(8760)]
    balance = simulate(production, annual_use, capacity)
    assert balance.self_used_kwh + balance.exported_kwh + balance.stored_kwh == pytest.approx(
        math.fsum(production)
    )
    assert balance.self_used_kwh + balance.imported_kwh == pytest.approx(annual_use)
    assert 0 <= balance.stored_kwh <= capacity
    assert balance.self_used_kwh >= simulate(production, annual_use, 0).self_used_kwh
    assert balance.self_used_kwh <= min(math.fsum(production), annual_use) + 1e-7


@pytest.mark.parametrize("production", [[-1], [math.nan], [math.inf], []])
def test_invalid_production(production: list[float]) -> None:
    with pytest.raises(ValueError):
        simulate(production, 1, 1)


@pytest.mark.parametrize("capacity", [-1, math.inf, math.nan])
def test_invalid_capacity(capacity: float) -> None:
    with pytest.raises(ValueError):
        simulate([1], 1, capacity)


async def test_production_and_battery_contract(
    client: httpx.AsyncClient, upstream_requests: list[httpx.Request]
) -> None:
    await register(client)
    site = await create_site(client)
    response = await client.get(f"/api/sites/{site}/production")
    assert response.status_code == 200
    assert response.json() == {
        "yearlyKwh": 1200,
        "monthlyKwh": [{"month": month, "kwh": 100} for month in range(1, 13)],
    }
    response = await client.get(
        f"/api/sites/{site}/battery", params={"capacityKwh": 1, "annualUseKwh": 8760}
    )
    assert response.status_code == 200
    assert response.json() == {
        "productionKwh": 8760,
        "consumptionKwh": 8760,
        "withoutBattery": {"selfUsedKwh": 4380},
        "withBattery": {"selfUsedKwh": 8760},
    }
    assert len(upstream_requests) == 2
    hourly = upstream_requests[1]
    assert dict(hourly.url.params) == {
        "lat": "52.08",
        "lon": "4.31",
        "peakpower": "5.0",
        "loss": "14.0",
        "outputformat": "json",
        "pvcalculation": "1",
        "startyear": "2023",
        "endyear": "2023",
    }
    assert hourly.url.path == "/api/v5_3/seriescalc"
    await client.get(f"/api/sites/{site}/production")
    assert len(upstream_requests) == 3


async def test_zero_capacity_and_consumption(client: httpx.AsyncClient) -> None:
    await register(client)
    site = await create_site(client)
    response = await client.get(
        f"/api/sites/{site}/battery", params={"capacityKwh": 0, "annualUseKwh": 8760}
    )
    assert response.json()["withBattery"] == response.json()["withoutBattery"]
    response = await client.get(
        f"/api/sites/{site}/battery", params={"capacityKwh": 10, "annualUseKwh": 0}
    )
    assert response.json()["withBattery"]["selfUsedKwh"] == 0


@pytest.mark.parametrize(
    "query",
    [
        "",
        "capacityKwh=-1&annualUseKwh=1",
        "capacityKwh=NaN&annualUseKwh=1",
        "capacityKwh=1&annualUseKwh=Infinity",
        "capacityKwh=100001&annualUseKwh=1",
        "capacityKwh=1&annualUseKwh=-1",
        "capacityKwh=1&annualUseKwh=100000001",
    ],
)
async def test_battery_query_validation(
    client: httpx.AsyncClient, query: str, upstream_requests: list[httpx.Request]
) -> None:
    await register(client)
    site = await create_site(client)
    response = await client.get(f"/api/sites/{site}/battery?{query}")
    assert_error(response, 422, "VALIDATION_ERROR")
    assert upstream_requests == []


async def test_database_connections_released_before_pvgis(settings: Settings) -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert app.state.database.engine.pool.checkedout() == 0
        requests.append(request)
        payload = monthly_payload() if request.url.path.endswith("PVcalc") else hourly_payload()
        return httpx.Response(200, json=payload)

    app = create_app(settings, pvgis_transport=httpx.MockTransport(handler))
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url=ORIGIN, headers={"Origin": ORIGIN}
        ) as client:
            await register(client)
            site_id = await create_site(client)
            production = await client.get(f"/api/sites/{site_id}/production")
            assert production.status_code == 200
            battery = await client.get(
                f"/api/sites/{site_id}/battery", params={"capacityKwh": 1, "annualUseKwh": 8760}
            )
            assert battery.status_code == 200
            assert len(requests) == 2
