import { useState } from "react";
import { ErrorNotice, Loading } from "../../shared/ui/feedback";
import { useBatteryComparison, type BatteryInput } from "./queries";
import { BatteryForm } from "./components/BatteryForm";
import { BatteryResults } from "./components/BatteryResults";
import { Panel } from "../../shared/ui/layout";

export function BatteryPanel({ siteId }: { siteId: string }) {
  const [submitted, setSubmitted] = useState<BatteryInput | null>(null);
  const comparison = useBatteryComparison(siteId, submitted);

  function submitComparison(values: BatteryInput) {
    if (
      submitted?.annualUseKwh === values.annualUseKwh &&
      submitted.capacityKwh === values.capacityKwh
    ) {
      // Repeating the same inputs retries the request without changing its query key.
      void comparison.refetch();
      return;
    }

    setSubmitted(values);
  }

  return (
    <Panel aria-labelledby="battery-title">
      <h2 id="battery-title">What does a battery add?</h2>
      <p>Compare how much solar energy the client would use at home.</p>
      <BatteryForm
        pending={comparison.isFetching}
        error={comparison.error}
        onSubmit={submitComparison}
      />
      <div aria-live="polite" aria-atomic="true">
        <BatteryComparison submitted={submitted} comparison={comparison} />
      </div>
      <details className="mt-[1.6rem] border-t border-line-soft pt-4 text-[0.85rem] text-muted">
        <summary>How this comparison works</summary>
        <p>
          Electricity use is spread equally across every hour. The battery starts empty, has 100%
          efficiency, and has no charging or discharging power limit. Energy left in the battery at
          year-end is excluded. This is an indicative comparison, not a savings forecast.
        </p>
      </details>
    </Panel>
  );
}

function BatteryComparison({
  submitted,
  comparison,
}: {
  submitted: BatteryInput | null;
  comparison: ReturnType<typeof useBatteryComparison>;
}) {
  if (!submitted) {
    return (
      <p className="mt-6 mb-0 border-t border-line-soft py-6 text-muted">
        Enter electricity use and a battery capacity to see the difference.
      </p>
    );
  }
  if (comparison.isFetching) return <Loading>Calculating hourly energy use…</Loading>;
  if (comparison.isError) {
    return <ErrorNotice error={comparison.error} retry={() => void comparison.refetch()} />;
  }
  if (!comparison.data) return null;

  return <BatteryResults comparison={comparison.data} capacityKwh={submitted.capacityKwh} />;
}
