from solar_sites.infra.pvgis import Pvgis
from solar_sites.modules.energy.schemas import MonthlyEnergy, ProductionOutput


class PvgisSolarDataProvider:
    def __init__(self, *, client: Pvgis) -> None:
        self.client = client

    async def production(
        self, *, latitude: float, longitude: float, peak_kwp: float
    ) -> ProductionOutput:
        estimate = await self.client.production(
            latitude=latitude, longitude=longitude, peak_kwp=peak_kwp
        )
        return ProductionOutput(
            yearly_kwh=estimate.yearly_kwh,
            monthly_kwh=[
                MonthlyEnergy(month=month.month, kwh=month.kwh) for month in estimate.monthly_kwh
            ],
        )

    async def hourly(self, *, latitude: float, longitude: float, peak_kwp: float) -> list[float]:
        return await self.client.hourly(latitude=latitude, longitude=longitude, peak_kwp=peak_kwp)
