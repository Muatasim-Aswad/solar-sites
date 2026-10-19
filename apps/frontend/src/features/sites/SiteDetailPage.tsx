import { Link, useParams } from "react-router";
import { useSite } from "./queries";
import { ProductionPanel } from "../energy/ProductionPanel";
import { BatteryPanel } from "../energy/BatteryPanel";
import { ErrorNotice, Loading } from "../../shared/ui/feedback";
import { SiteSummary } from "./components/SiteSummary";
import { DeleteSite } from "./components/DeleteSite";

export function SiteDetailPage() {
  const { id = "" } = useParams();
  const site = useSite(id);
  return (
    <>
      <Link className="mb-[0.6rem] inline-block text-[0.92rem]" to="/sites">
        All client sites
      </Link>
      {site.isPending ? (
        <Loading>Loading client site…</Loading>
      ) : site.isError ? (
        <ErrorNotice error={site.error} retry={() => void site.refetch()} />
      ) : (
        <>
          <SiteSummary site={site.data} />
          <div className="grid grid-cols-[minmax(0,0.9fr)_minmax(0,1.15fr)] items-start gap-6 max-wide:grid-cols-1">
            <ProductionPanel siteId={id} />
            <BatteryPanel key={id} siteId={id} />
          </div>
          <DeleteSite siteId={id} clientName={site.data.clientName} />
        </>
      )}
    </>
  );
}
