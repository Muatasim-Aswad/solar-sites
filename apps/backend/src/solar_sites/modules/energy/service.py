import math

from sqlalchemy.ext.asyncio import AsyncSession

from solar_sites.modules.energy.schemas import BatteryOutput, ProductionOutput, SelfConsumption
from solar_sites.modules.energy.simulation import simulate
from solar_sites.modules.energy.solar_data_provider import SolarDataProvider
from solar_sites.modules.sites import get_site


async def production(
    db: AsyncSession, *, solar: SolarDataProvider, user_id: str, site_id: str
) -> ProductionOutput:
    site = await get_site(db, user_id=user_id, site_id=site_id)
    return await solar.production(
        latitude=site.latitude, longitude=site.longitude, peak_kwp=site.peak_kwp
    )


async def battery(
    db: AsyncSession,
    *,
    solar: SolarDataProvider,
    user_id: str,
    site_id: str,
    capacity_kwh: float,
    annual_use_kwh: float,
) -> BatteryOutput:
    site = await get_site(db, user_id=user_id, site_id=site_id)
    production = await solar.hourly(
        latitude=site.latitude, longitude=site.longitude, peak_kwp=site.peak_kwp
    )
    without = simulate(production, annual_use_kwh, 0)
    with_battery = simulate(production, annual_use_kwh, capacity_kwh)
    return BatteryOutput(
        production_kwh=math.fsum(production),
        consumption_kwh=annual_use_kwh,
        without_battery=SelfConsumption(self_used_kwh=without.self_used_kwh),
        with_battery=SelfConsumption(self_used_kwh=with_battery.self_used_kwh),
    )
