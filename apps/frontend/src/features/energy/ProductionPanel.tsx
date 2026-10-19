import { ProductionTable } from "./components/ProductionTable";
import { useProduction } from "./queries";
import { ErrorNotice, Loading } from "../../shared/ui/feedback";
import { energy } from "../../shared/numbers";
import { Panel } from "../../shared/ui/layout";

export function ProductionPanel({ siteId }: { siteId: string }) {
  return (
    <Panel aria-labelledby="production-title">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="production-title">Solar production</h2>
        <span className="text-[0.8rem] text-muted">PVGIS estimate</span>
      </div>
      <ProductionEstimate siteId={siteId} />
    </Panel>
  );
}

function ProductionEstimate({ siteId }: { siteId: string }) {
  const production = useProduction(siteId);

  if (production.isPending) return <Loading>Estimating solar production…</Loading>;
  if (production.isError) {
    return <ErrorNotice error={production.error} retry={() => void production.refetch()} />;
  }

  return (
    <>
      <p className="mt-[0.4rem] mb-[1.4rem] text-[2.1rem] font-bold tracking-[-0.04em] tabular-nums max-compact:text-[1.8rem]">
        {energy(production.data.yearlyKwh)}
        <span className="block text-[0.85rem] font-normal tracking-normal text-muted">
          estimated yearly production
        </span>
      </p>
      <ProductionTable production={production.data} />
      <p className="mt-4 mb-0 text-[0.82rem] text-muted">
        An estimate based on location and panel capacity. Actual production varies with the roof and
        weather.
      </p>
    </>
  );
}
