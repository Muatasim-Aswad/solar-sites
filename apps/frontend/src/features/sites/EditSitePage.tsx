import { Link, useParams } from "react-router";
import { ErrorNotice, Loading } from "../../shared/ui/feedback";
import { SiteForm } from "./components/SiteForm";
import { useSite } from "./queries";
import { Panel, PageHeading } from "../../shared/ui/layout";

export function EditSitePage() {
  const { id = "" } = useParams();
  const site = useSite(id);
  return (
    <>
      <Link className="mb-[0.6rem] inline-block text-[0.92rem]" to={`/sites/${id}`}>
        Back to site
      </Link>
      <PageHeading>
        <h1>Edit client site</h1>
      </PageHeading>
      {site.isPending ? (
        <Loading>Loading site…</Loading>
      ) : site.isError ? (
        <ErrorNotice error={site.error} retry={() => void site.refetch()} />
      ) : (
        <Panel className="max-w-190">
          <SiteForm key={site.data.id} site={site.data} />
        </Panel>
      )}
    </>
  );
}
