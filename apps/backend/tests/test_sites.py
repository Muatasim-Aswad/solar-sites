import httpx
import pytest
from conftest import ORIGIN, SITE, create_site, register
from fastapi import FastAPI
from sqlalchemy import select
from test_auth import assert_error

from solar_sites.modules.sites.models import Site


async def test_site_crud_contract(client: httpx.AsyncClient) -> None:
    await register(client)
    assert (await client.get("/api/sites")).json() == []
    response = await client.post("/api/sites", json={**SITE, "roofAreaM2": 32.5})
    assert response.status_code == 201
    site = response.json()
    assert site == {**SITE, "roofAreaM2": 32.5, "id": site["id"]}
    assert (await client.get(f"/api/sites/{site['id']}")).json() == site
    assert (await client.get("/api/sites")).json() == [site]
    changed = {**SITE, "clientName": "  Updated client  ", "latitude": -90, "longitude": 180}
    response = await client.put(f"/api/sites/{site['id']}", json=changed)
    assert response.status_code == 200
    assert response.json() == {
        **changed,
        "clientName": "Updated client",
        "roofAreaM2": None,
        "id": site["id"],
    }
    response = await client.delete(f"/api/sites/{site['id']}")
    assert response.status_code == 204 and response.content == b""
    assert (await client.get("/api/sites")).json() == []
    assert_error(await client.get(f"/api/sites/{site['id']}"), 404, "NOT_FOUND")


async def test_independent_advisors(
    client: httpx.AsyncClient, app: FastAPI, upstream_requests: list[httpx.Request]
) -> None:
    await register(client)
    site_id = await create_site(client)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url=ORIGIN, headers={"Origin": ORIGIN}
    ) as other:
        await register(other, "second@example.com")
        assert (await other.get("/api/sites")).json() == []
        paths = [
            f"/api/sites/{site_id}",
            f"/api/sites/{site_id}/production",
            f"/api/sites/{site_id}/battery?capacityKwh=1&annualUseKwh=1000",
        ]
        for path in paths:
            assert_error(await other.get(path), 404, "NOT_FOUND")
        assert_error(await other.put(paths[0], json=SITE), 404, "NOT_FOUND")
        assert_error(await other.delete(paths[0]), 404, "NOT_FOUND")
        assert_error(await other.get("/api/sites/missing"), 404, "NOT_FOUND")
        assert upstream_requests == []
        second_id = await create_site(other)
        assert second_id != site_id
    assert [site["id"] for site in (await client.get("/api/sites")).json()] == [site_id]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("clientName", " "),
        ("clientName", "x" * 201),
        ("address", ""),
        ("address", "x" * 501),
        ("latitude", -90.1),
        ("latitude", 90.1),
        ("longitude", -180.1),
        ("longitude", 180.1),
        ("peakKwp", 0),
        ("peakKwp", -1),
        ("peakKwp", 100001),
        ("peakKwp", True),
        ("latitude", "52"),
        ("roofAreaM2", -1),
        ("roofAreaM2", 0),
        ("roofAreaM2", 1000001),
    ],
)
async def test_site_field_validation(client: httpx.AsyncClient, field: str, value: object) -> None:
    await register(client)
    response = await client.post("/api/sites", json={**SITE, field: value})
    error = assert_error(response, 422, "VALIDATION_ERROR")
    assert field in [issue["field"] for issue in error["issues"]]
    assert (await client.get("/api/sites")).json() == []


async def test_multiple_field_issues(client: httpx.AsyncClient) -> None:
    await register(client)
    response = await client.post("/api/sites", json={"clientName": "", "latitude": 200})
    error = assert_error(response, 422, "VALIDATION_ERROR")
    assert {"clientName", "latitude", "address", "longitude", "peakKwp"} <= {
        issue["field"] for issue in error["issues"]
    }


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
async def test_nonfinite_site_input(client: httpx.AsyncClient, value: str) -> None:
    await register(client)
    body = (
        '{"clientName":"Client","address":"Address","latitude":52,"longitude":4,"peakKwp":'
        + value
        + "}"
    )
    response = await client.post(
        "/api/sites", content=body, headers={"Content-Type": "application/json"}
    )
    assert_error(response, 422, "VALIDATION_ERROR")


async def test_update_validation_leaves_site_unchanged(client: httpx.AsyncClient) -> None:
    await register(client)
    site_id = await create_site(client)
    response = await client.put(f"/api/sites/{site_id}", json={**SITE, "peakKwp": -1})
    assert_error(response, 422, "VALIDATION_ERROR")
    assert (await client.get(f"/api/sites/{site_id}")).json()["peakKwp"] == 5


async def test_database_does_not_expose_ownership_fields(
    client: httpx.AsyncClient, app: FastAPI
) -> None:
    await register(client)
    site_id = await create_site(client)
    async with app.state.database.sessions() as db:
        site = await db.scalar(select(Site).where(Site.id == site_id))
        assert site.user_id
    assert set((await client.get(f"/api/sites/{site_id}")).json()) == {*SITE, "roofAreaM2", "id"}
