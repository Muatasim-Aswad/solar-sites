import { useSites } from "./queries";
import { ErrorNotice, Loading } from "../../shared/ui/feedback";
import { SitesTable } from "./components/SitesTable";
import { ButtonLink } from "../../shared/ui/buttons";
import { Panel, PageHeading } from "../../shared/ui/layout";

export function SitesPage() {
  return (
    <>
      <PageHeading>
        <div>
          <h1>Client sites</h1>
          <p>Choose a roof to assess its solar potential.</p>
        </div>
        <ButtonLink to="/sites/new">Add a site</ButtonLink>
      </PageHeading>
      <SitesList />
    </>
  );
}

function SitesList() {
  const sites = useSites();

  if (sites.isPending) return <Loading>Loading your sites…</Loading>;
  if (sites.isError) {
    return <ErrorNotice error={sites.error} retry={() => void sites.refetch()} />;
  }
  if (sites.data.length > 0) return <SitesTable sites={sites.data} />;

  return (
    <Panel padding="empty" className="text-center">
      <h2>Your first roof starts here.</h2>
      <p className="mx-auto mb-6 max-w-[55ch]">
        Add a client’s location and panel capacity to estimate production and compare a home
        battery.
      </p>
      <ButtonLink to="/sites/new">Add your first site</ButtonLink>
    </Panel>
  );
}
