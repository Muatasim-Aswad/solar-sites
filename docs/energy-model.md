# Energy model

## Production and units

PVGIS supplies solar production from the site's coordinates, panel capacity in kWp and configured solar parameters. kWp describes rated panel power; kWh measures energy produced, consumed or stored.

- **`PVcalc`:** Monthly and yearly production in kWh. The backend requires twelve distinct months, finite nonnegative energy and agreement between their sum and the yearly total within rounding tolerance.
- **`seriescalc`:** One complete chronological year of hourly production for the battery simulation. The backend treats each power value in watts as applying to a one-hour interval: `production_kWh = power_W / 1000 × 1 hour`.

These are separate PVGIS products, so their yearly totals need not match. Each battery comparison uses the same hourly production for both scenarios.

The hourly year defaults to `2023` (`PVGIS_YEAR`) and system loss to `14%` (`PVGIS_LOSS`). Other optional solar settings use PVGIS defaults unless configured. A fixed year makes comparisons reproducible for the same upstream data and settings.

## Consumption assumptions

The advisor supplies annual electricity use in kWh. Demand is spread equally across the simulation year's hours: 8,760, or 8,784 in a leap year.

```text
demand = annualUseKwh / hours
```

Equal hourly demand provides a reproducible baseline without requiring a household load profile. It misses seasonal use, occupancy and appliance schedules.

## Hourly battery calculation

The battery starts empty, has 100% efficiency and unlimited charge/discharge power, and charges only from surplus solar. Solar supplies demand directly, surplus charges the battery, and stored energy supplies remaining demand.

For each hour, `production` is that hour's solar energy, `capacity` is the entered battery capacity, and `stored` is battery energy at the start of the hour. All quantities below are in kWh.

```text
direct      = min(production, demand)
charge      = min(production - direct, max(0, capacity - stored))
discharge   = min(stored + charge, demand - direct)
stored_next = stored + charge - discharge
export      = production - direct - charge
import      = demand - direct - discharge
```

The next hour starts with `stored = stored_next`. These equations follow [simulation.py](../apps/backend/src/solar_sites/modules/energy/simulation.py).

## Yearly results and checks

Self-used solar includes direct use and battery discharge serving demand. Energy still stored at year-end is excluded.

```text
selfUsedKwh = sum(direct + discharge)
```

The same simulation runs with zero capacity and the entered capacity. The battery's contribution is:

```text
addedSelfUseKwh = withBattery.selfUsedKwh - withoutBattery.selfUsedKwh
```

The energy balances, checked in [test_energy.py](../apps/backend/tests/test_energy.py), are:

```text
totalProduction = selfUsedKwh + totalExport + finalStored
annualUseKwh    = selfUsedKwh + totalImport
0 <= stored <= capacity
```

## Limitations

The estimates do not model an individually surveyed roof's shading or panel layout. Flat demand and an ideal battery simplify household behavior and storage; degradation and tariffs are excluded. Results are indicative energy comparisons, not savings forecasts or battery-sizing recommendations.
