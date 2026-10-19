import type { components } from "../../../infra/api/schema";
import { energy, number } from "../../../shared/numbers";

export function BatteryResults({
  comparison,
  capacityKwh,
}: {
  comparison: components["schemas"]["BatteryOutput"];
  capacityKwh: number;
}) {
  const added = comparison.withBattery.selfUsedKwh - comparison.withoutBattery.selfUsedKwh;
  return (
    <div className="mt-[1.8rem] border-t border-line pt-[1.4rem]">
      <p className="text-[0.85rem] text-muted">
        {number(capacityKwh)} kWh battery · {energy(comparison.consumptionKwh)} yearly use
      </p>
      <EnergyTrack
        label="Without a battery"
        selfUsedKwh={comparison.withoutBattery.selfUsedKwh}
        productionKwh={comparison.productionKwh}
      />
      <EnergyTrack
        label="With a battery"
        selfUsedKwh={comparison.withBattery.selfUsedKwh}
        productionKwh={comparison.productionKwh}
        withBattery
      />
      <div className="mt-[1.8rem] mb-[1.2rem] border-l-4 border-solar py-[0.2rem] pl-4">
        <strong className="block text-[1.9rem] tracking-[-0.035em] tabular-nums">
          +{energy(Math.max(0, added))}
        </strong>
        <span className="text-[0.9rem]">additional solar energy used at home per year</span>
      </div>
      <p className="text-[0.82rem] text-muted">
        Compared with {energy(comparison.productionKwh)} of solar production in the simulation year.
        Monthly production uses a long-term estimate and may differ.
      </p>
    </div>
  );
}

function EnergyTrack({
  label,
  selfUsedKwh,
  productionKwh,
  withBattery = false,
}: {
  label: string;
  selfUsedKwh: number;
  productionKwh: number;
  withBattery?: boolean;
}) {
  const percentage =
    productionKwh > 0 ? Math.min(100, Math.max(0, (selfUsedKwh / productionKwh) * 100)) : 0;
  return (
    <div className="my-[1.2rem]">
      <div className="flex flex-wrap items-baseline justify-between gap-2 text-[0.95rem] tabular-nums">
        <span>{label}</span>
        <strong>{energy(selfUsedKwh)}</strong>
      </div>
      <div className="mt-2 h-3 overflow-hidden rounded-[3px] bg-track" aria-hidden="true">
        <span
          className={`block h-full ${withBattery ? "bg-teal" : "bg-track-fill"}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
