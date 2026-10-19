import asyncio
from collections.abc import Awaitable, Callable
from typing import Literal

import httpx

from solar_sites.config import Settings
from solar_sites.infra.pvgis.data import (
    ProductionEstimate,
    is_no_data,
    parse_hourly,
    parse_production,
)
from solar_sites.shared.errors import AppError


class Pvgis:
    BASE_URL = "https://re.jrc.ec.europa.eu/api/v5_3/"
    MAX_RESPONSE_BYTES = 8 * 1024 * 1024

    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        settings: Settings,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.client = client
        self.settings = settings
        self.sleep = sleep
        self.slots = asyncio.Semaphore(settings.pvgis_concurrency)

    def _parameters(self, *, latitude: float, longitude: float, peak_kwp: float) -> dict[str, str]:
        params = {
            "lat": str(latitude),
            "lon": str(longitude),
            "peakpower": str(peak_kwp),
            "loss": str(self.settings.pvgis_loss),
            "outputformat": "json",
        }
        for key in (
            "angle",
            "aspect",
            "optimalangles",
            "raddatabase",
            "pvtechchoice",
            "mountingplace",
        ):
            value = getattr(self.settings, f"pvgis_{key}")
            if value is not None:
                params[key] = str(value)
        return params

    async def production(
        self, *, latitude: float, longitude: float, peak_kwp: float
    ) -> ProductionEstimate:
        payload = await self._request(
            tool="PVcalc",
            params=self._parameters(latitude=latitude, longitude=longitude, peak_kwp=peak_kwp),
        )
        return parse_production(payload)

    async def hourly(self, *, latitude: float, longitude: float, peak_kwp: float) -> list[float]:
        params = self._parameters(latitude=latitude, longitude=longitude, peak_kwp=peak_kwp)
        params.update(
            {
                "pvcalculation": "1",
                "startyear": str(self.settings.pvgis_year),
                "endyear": str(self.settings.pvgis_year),
            }
        )
        return parse_hourly(
            await self._request(tool="seriescalc", params=params), self.settings.pvgis_year
        )

    async def _request(
        self, *, tool: Literal["PVcalc", "seriescalc"], params: dict[str, str]
    ) -> bytes:
        try:
            await asyncio.wait_for(self.slots.acquire(), timeout=5)
        except TimeoutError as exc:
            raise AppError(
                "PVGIS_UNAVAILABLE", "Solar data requests are busy. Please try again."
            ) from exc
        try:
            return await self._request_with_retries(tool=tool, params=params)
        finally:
            self.slots.release()

    async def _request_with_retries(self, *, tool: str, params: dict[str, str]) -> bytes:
        for attempt in range(3):
            try:
                return await self._request_once(tool=tool, params=params)
            except (httpx.TransportError, httpx.HTTPStatusError, TimeoutError) as exc:
                if attempt == 2:
                    raise AppError(
                        "PVGIS_UNAVAILABLE", "PVGIS is temporarily unavailable. Please try again."
                    ) from exc
                await self.sleep(0.25 * 2**attempt)
        raise AssertionError("Unreachable")

    async def _request_once(self, *, tool: str, params: dict[str, str]) -> bytes:
        async with asyncio.timeout(self.settings.pvgis_timeout_seconds):
            async with self.client.stream("GET", self.BASE_URL + tool, params=params) as response:
                if response.status_code == 429 or 500 <= response.status_code <= 599:
                    raise httpx.HTTPStatusError(
                        "Temporary PVGIS failure", request=response.request, response=response
                    )
                body = await self._read_response(response=response)
                if response.status_code in {200, 400, 404, 422} and is_no_data(body):
                    raise AppError("PVGIS_NO_DATA", "PVGIS has no data for this location.")
                if response.status_code != 200:
                    raise AppError(
                        "PVGIS_INVALID_RESPONSE", "PVGIS could not process this location."
                    )
                return body

    async def _read_response(self, *, response: httpx.Response) -> bytes:
        payload = bytearray()
        async for chunk in response.aiter_bytes():
            if len(payload) + len(chunk) > self.MAX_RESPONSE_BYTES:
                raise AppError("PVGIS_INVALID_RESPONSE", "PVGIS returned too much data.")
            payload.extend(chunk)
        return bytes(payload)
