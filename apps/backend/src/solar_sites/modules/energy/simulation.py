import math
from collections.abc import Sequence
from dataclasses import dataclass


def equal_hourly_consumption(annual_use_kwh: float, hours: int) -> float:
    if not math.isfinite(annual_use_kwh) or annual_use_kwh < 0 or not 1 <= hours <= 8784:
        raise ValueError(
            "Consumption must be finite and nonnegative; hours must describe one year."
        )
    return annual_use_kwh / hours


@dataclass(frozen=True)
class EnergyBalance:
    direct_kwh: float
    battery_supplied_kwh: float
    exported_kwh: float
    imported_kwh: float
    stored_kwh: float

    @property
    def self_used_kwh(self) -> float:
        return self.direct_kwh + self.battery_supplied_kwh


def simulate(
    production_kwh: Sequence[float], annual_use_kwh: float, capacity_kwh: float
) -> EnergyBalance:
    if not math.isfinite(capacity_kwh) or capacity_kwh < 0:
        raise ValueError("Battery capacity must be finite and nonnegative.")

    demand = equal_hourly_consumption(annual_use_kwh, len(production_kwh))
    direct = supplied = exported = imported = stored = 0.0

    for production in production_kwh:
        if not math.isfinite(production) or production < 0:
            raise ValueError("Hourly production must be finite and nonnegative.")

        used = min(production, demand)
        direct += used

        surplus = production - used
        charged = min(surplus, max(0.0, capacity_kwh - stored))
        stored += charged
        exported += surplus - charged

        discharged = min(stored, demand - used)
        stored -= discharged
        supplied += discharged
        imported += demand - used - discharged

    return EnergyBalance(direct, supplied, exported, imported, stored)
