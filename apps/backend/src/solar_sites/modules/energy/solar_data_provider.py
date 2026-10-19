from typing import Protocol

from solar_sites.modules.energy.schemas import ProductionOutput


class SolarDataProvider(Protocol):
    async def production(
        self, *, latitude: float, longitude: float, peak_kwp: float
    ) -> ProductionOutput: ...

    async def hourly(
        self, *, latitude: float, longitude: float, peak_kwp: float
    ) -> list[float]: ...
