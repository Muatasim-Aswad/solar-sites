import copy
import json
from typing import Any

import httpx
import pytest
from conftest import ORIGIN, create_site, hourly_payload, monthly_payload, register
from test_auth import assert_error

from solar_sites.config import Settings
from solar_sites.infra.pvgis import Pvgis
from solar_sites.infra.pvgis.data import parse_hourly, parse_production
from solar_sites.main import create_app
from solar_sites.shared.errors import AppError


def encode(data: Any) -> bytes:
    return json.dumps(data).encode()


def test_valid_monthly_and_hourly_watts_to_kwh() -> None:
    assert parse_production(encode(monthly_payload())).yearly_kwh == 1200
    values = parse_hourly(encode(hourly_payload()), 2023)
    assert len(values) == 8760
    assert values[:4] == [2, 0, 2, 0]
    assert sum(values) == 8760
    assert len(parse_hourly(encode(hourly_payload(2024, minute=30)), 2024)) == 8784


@pytest.mark.parametrize(
    "change", ["missing", "duplicate", "negative", "nan", "string", "boolean", "total", "extra"]
)
def test_invalid_monthly(change: str) -> None:
    payload = monthly_payload()
    months = payload["outputs"]["monthly"]["fixed"]
    if change == "missing":
        months.pop()
    elif change == "duplicate":
        months[1]["month"] = 1
    elif change == "negative":
        months[0]["E_m"] = -1
    elif change == "nan":
        months[0]["E_m"] = float("nan")
    elif change == "string":
        months[0]["E_m"] = "100"
    elif change == "boolean":
        months[0]["E_m"] = True
    elif change == "total":
        payload["outputs"]["totals"]["fixed"]["E_y"] = 2000
    elif change == "extra":
        months.append({"month": 1, "E_m": 100})
    with pytest.raises(AppError) as caught:
        parse_production(encode(payload))
    assert caught.value.code == "PVGIS_INVALID_RESPONSE"


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "reordered",
        "wrong_year",
        "gap",
        "invalid_time",
        "negative",
        "nan",
        "string",
        "boolean",
        "too_long",
    ],
)
def test_invalid_hourly(change: str) -> None:
    payload = hourly_payload()
    hours = payload["outputs"]["hourly"]
    if change == "missing":
        hours.pop()
    elif change == "duplicate":
        hours[10] = copy.deepcopy(hours[9])
    elif change == "reordered":
        hours[0], hours[1] = hours[1], hours[0]
    elif change == "wrong_year":
        hours[0]["time"] = "20220101:0010"
    elif change == "gap":
        hours[10]["time"] = "20230101:1110"
    elif change == "invalid_time":
        hours[10]["time"] = "20230230:1010"
    elif change == "negative":
        hours[10]["P"] = -1
    elif change == "nan":
        hours[10]["P"] = float("inf")
    elif change == "string":
        hours[10]["P"] = "123"
    elif change == "boolean":
        hours[10]["P"] = False
    elif change == "too_long":
        hours.extend(copy.deepcopy(hours[:25]))
    with pytest.raises(AppError) as caught:
        parse_hourly(encode(payload), 2023)
    assert caught.value.code == "PVGIS_INVALID_RESPONSE"


@pytest.mark.parametrize("body", [b"{", b"null", b"[]", b'{"outputs":{}}'])
def test_malformed_responses(body: bytes) -> None:
    for parse in [parse_production, lambda raw: parse_hourly(raw, 2023)]:
        with pytest.raises(AppError) as caught:
            parse(body)
        assert caught.value.code == "PVGIS_INVALID_RESPONSE"


@pytest.mark.parametrize("kind", ["monthly", "hourly"])
def test_empty_data(kind: str) -> None:
    if kind == "monthly":
        payload = monthly_payload()
        payload["outputs"]["monthly"]["fixed"] = []
        parse = parse_production
    else:
        payload = {"outputs": {"hourly": []}}
        parse = lambda raw: parse_hourly(raw, 2023)  # noqa: E731
    with pytest.raises(AppError) as caught:
        parse(encode(payload))
    assert caught.value.code == "PVGIS_NO_DATA"


@pytest.mark.parametrize("failure", [429, 500, 502, 503, 504, 529, "timeout", "connection"])
@pytest.mark.parametrize("recover", [True, False])
async def test_bounded_retry_and_backoff(
    settings: Settings, failure: int | str, recover: bool
) -> None:
    requests: list[httpx.Request] = []
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if recover and len(requests) == 3:
            return httpx.Response(200, json=monthly_payload())
        if failure == "timeout":
            raise httpx.ReadTimeout("timed out", request=request)
        if failure == "connection":
            raise httpx.ConnectError("unreachable", request=request)
        return httpx.Response(int(failure))

    async def sleep(delay: float) -> None:
        delays.append(delay)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        pvgis = Pvgis(client=client, settings=settings, sleep=sleep)
        if recover:
            assert (await pvgis.production(latitude=52, longitude=4, peak_kwp=5)).yearly_kwh == 1200
        else:
            with pytest.raises(AppError) as caught:
                await pvgis.production(latitude=52, longitude=4, peak_kwp=5)
            assert caught.value.code == "PVGIS_UNAVAILABLE"
    assert len(requests) == 3
    assert delays == [0.25, 0.5]


@pytest.mark.parametrize(
    ("status", "payload", "code"),
    [
        (400, {"message": "Location over the sea"}, "PVGIS_NO_DATA"),
        (400, {"message": "No valid radiation database found"}, "PVGIS_NO_DATA"),
        (200, {"message": "No data for this location"}, "PVGIS_NO_DATA"),
        (400, {"message": "Invalid parameters"}, "PVGIS_INVALID_RESPONSE"),
        (404, {"message": "Unknown route"}, "PVGIS_INVALID_RESPONSE"),
        (200, {"outputs": {}}, "PVGIS_INVALID_RESPONSE"),
        (302, {}, "PVGIS_INVALID_RESPONSE"),
    ],
)
async def test_no_retry_for_permanent_data_errors(
    settings: Settings, status: int, payload: dict, code: str
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(status, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(AppError) as caught:
            await Pvgis(client=client, settings=settings).production(
                latitude=52, longitude=4, peak_kwp=5
            )
        assert caught.value.code == code
    assert len(requests) == 1


async def test_optional_parameters_only_when_configured(settings: Settings) -> None:
    settings.pvgis_angle = 35
    settings.pvgis_aspect = 0
    settings.pvgis_optimalangles = 0
    settings.pvgis_loss = 12
    settings.pvgis_year = 2024
    settings.pvgis_raddatabase = "PVGIS-ERA5"
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=hourly_payload(2024))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await Pvgis(client=client, settings=settings).hourly(latitude=52, longitude=4, peak_kwp=5)
    params = requests[0].url.params
    assert params["angle"] == "35"
    assert params["aspect"] == "0"
    assert params["optimalangles"] == "0"
    assert params["loss"] == "12"
    assert params["startyear"] == params["endyear"] == "2024"
    assert params["raddatabase"] == "PVGIS-ERA5"
    assert "mountingplace" not in params


async def test_response_size_limit(settings: Settings) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"x" * 101))
    ) as client:
        pvgis = Pvgis(client=client, settings=settings)
        pvgis.MAX_RESPONSE_BYTES = 100
        with pytest.raises(AppError) as caught:
            await pvgis.production(latitude=52, longitude=4, peak_kwp=5)
        assert caught.value.code == "PVGIS_INVALID_RESPONSE"


@pytest.mark.parametrize(
    ("response_status", "payload", "expected_status", "expected_code"),
    [
        (400, {"message": "Location over the sea"}, 422, "PVGIS_NO_DATA"),
        (200, {"outputs": {}}, 502, "PVGIS_INVALID_RESPONSE"),
        (529, {}, 503, "PVGIS_UNAVAILABLE"),
    ],
)
async def test_pvgis_http_error_contract(
    settings: Settings,
    response_status: int,
    payload: dict,
    expected_status: int,
    expected_code: str,
) -> None:
    app = create_app(
        settings,
        pvgis_transport=httpx.MockTransport(
            lambda _: httpx.Response(response_status, json=payload)
        ),
    )
    async with app.router.lifespan_context(app):

        async def no_sleep(_: float) -> None:
            pass

        app.state.solar.client.sleep = no_sleep
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url=ORIGIN, headers={"Origin": ORIGIN}
        ) as client:
            await register(client)
            site = await create_site(client)
            assert_error(
                await client.get(f"/api/sites/{site}/production"), expected_status, expected_code
            )
