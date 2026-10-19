from pydantic import Field

from solar_sites.platform.schemas import ApiModel


class MonthlyEnergy(ApiModel):
    month: int = Field(ge=1, le=12)
    kwh: float = Field(ge=0)


class ProductionOutput(ApiModel):
    yearly_kwh: float = Field(ge=0)
    monthly_kwh: list[MonthlyEnergy] = Field(min_length=12, max_length=12)


class SelfConsumption(ApiModel):
    self_used_kwh: float = Field(ge=0)


class BatteryOutput(ApiModel):
    production_kwh: float = Field(ge=0)
    consumption_kwh: float = Field(ge=0)
    without_battery: SelfConsumption
    with_battery: SelfConsumption
