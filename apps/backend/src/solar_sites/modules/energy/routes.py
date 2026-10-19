from typing import Annotated

from fastapi import APIRouter, Path, Query

from solar_sites.modules.auth import IdentityDep
from solar_sites.modules.energy import service
from solar_sites.modules.energy.dependencies import SolarDep
from solar_sites.modules.energy.schemas import BatteryOutput, ProductionOutput
from solar_sites.platform.dependencies import SessionDep

router = APIRouter(prefix="/api/sites", tags=["energy"])


@router.get("/{id}/production", response_model=ProductionOutput, operation_id="siteProduction")
async def production(
    site_id: Annotated[str, Path(alias="id")],
    current_identity: IdentityDep,
    db: SessionDep,
    solar: SolarDep,
) -> ProductionOutput:
    return await service.production(
        db,
        solar=solar,
        user_id=current_identity.user_id,
        site_id=site_id,
    )


@router.get("/{id}/battery", response_model=BatteryOutput, operation_id="siteBattery")
async def battery(
    site_id: Annotated[str, Path(alias="id")],
    current_identity: IdentityDep,
    db: SessionDep,
    solar: SolarDep,
    capacity_kwh: Annotated[
        float, Query(alias="capacityKwh", ge=0, le=100_000, allow_inf_nan=False)
    ],
    annual_use_kwh: Annotated[
        float, Query(alias="annualUseKwh", ge=0, le=100_000_000, allow_inf_nan=False)
    ],
) -> BatteryOutput:
    return await service.battery(
        db,
        solar=solar,
        user_id=current_identity.user_id,
        site_id=site_id,
        capacity_kwh=capacity_kwh,
        annual_use_kwh=annual_use_kwh,
    )
