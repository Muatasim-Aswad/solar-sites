import calendar
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated

from pydantic import BaseModel, Field, StrictFloat, ValidationError

from solar_sites.shared.errors import AppError


@dataclass(frozen=True)
class MonthlyEstimate:
    month: int
    kwh: float


@dataclass(frozen=True)
class ProductionEstimate:
    yearly_kwh: float
    monthly_kwh: tuple[MonthlyEstimate, ...]


EnergyNumber = Annotated[StrictFloat, Field(ge=0, le=1e12, allow_inf_nan=False)]


class _Month(BaseModel):
    month: Annotated[int, Field(ge=1, le=12, strict=True)]
    energy: EnergyNumber = Field(alias="E_m")


class _Monthly(BaseModel):
    fixed: list[_Month]


class _Totals(BaseModel):
    energy: EnergyNumber = Field(alias="E_y")


class _Yearly(BaseModel):
    fixed: _Totals


class _Production(BaseModel):
    monthly: _Monthly
    totals: _Yearly


class _ProductionResponse(BaseModel):
    outputs: _Production


class _Hour(BaseModel):
    time: str = Field(strict=True)
    power: EnergyNumber = Field(alias="P")


class _Hourly(BaseModel):
    hourly: list[_Hour] = Field(max_length=8784)


class _HourlyResponse(BaseModel):
    outputs: _Hourly


def parse_production(payload: bytes) -> ProductionEstimate:
    try:
        data = _ProductionResponse.model_validate_json(payload).outputs
        months = sorted(data.monthly.fixed, key=lambda month: month.month)
        if not months:
            raise AppError("PVGIS_NO_DATA", "PVGIS has no production data for this location.")
        if [month.month for month in months] != list(range(1, 13)):
            raise ValueError("Expected exactly twelve distinct months")
        total = math.fsum(month.energy for month in months)
        if not math.isclose(total, data.totals.fixed.energy, rel_tol=0.001, abs_tol=0.5):
            raise ValueError("Monthly energy does not agree with yearly energy")
        return ProductionEstimate(
            yearly_kwh=data.totals.fixed.energy,
            monthly_kwh=tuple(MonthlyEstimate(month.month, month.energy) for month in months),
        )
    except (ValidationError, ValueError) as exc:
        raise AppError("PVGIS_INVALID_RESPONSE", "PVGIS returned invalid production data.") from exc


def parse_hourly(payload: bytes, year: int) -> list[float]:
    try:
        hours = _HourlyResponse.model_validate_json(payload).outputs.hourly
        if not hours:
            raise AppError("PVGIS_NO_DATA", "PVGIS has no hourly data for this location.")
        count = 8784 if calendar.isleap(year) else 8760
        if len(hours) != count:
            raise ValueError("Incomplete hourly year")

        # PVGIS timestamps can share a nonzero minute offset within every hourly interval.
        first = datetime.strptime(hours[0].time, "%Y%m%d:%H%M").replace(tzinfo=UTC)
        start = datetime(year, 1, 1, tzinfo=UTC)
        if first.replace(minute=0) != start:
            raise ValueError("Hourly data starts outside the requested year")
        for index, hour in enumerate(hours):
            timestamp = datetime.strptime(hour.time, "%Y%m%d:%H%M").replace(tzinfo=UTC)
            if timestamp != first + timedelta(hours=index):
                raise ValueError("Hourly data must cover every hour chronologically")

        # Watts over each one-hour interval become kilowatt-hours.
        return [hour.power / 1000 for hour in hours]
    except (ValidationError, ValueError) as exc:
        raise AppError(
            "PVGIS_INVALID_RESPONSE", "PVGIS returned invalid or incomplete hourly data."
        ) from exc


def is_no_data(payload: bytes) -> bool:
    try:
        data: object = json.loads(payload)
    except ValueError, UnicodeDecodeError:
        return False
    if not isinstance(data, dict):
        return False
    message = data.get("message")
    if not isinstance(message, str):
        return False
    message = message.lower()
    return any(
        fragment in message
        for fragment in (
            "no data",
            "no radiation data",
            "no valid radiation",
            "location over the sea",
            "location is over the sea",
            "outside the database",
            "not covered",
        )
    )
