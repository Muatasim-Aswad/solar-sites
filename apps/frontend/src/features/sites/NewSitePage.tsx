import { Link } from "react-router";
import { SiteForm } from "./components/SiteForm";
import { Panel, PageHeading } from "../../shared/ui/layout";

export function NewSitePage() {
  return (
    <>
      <Link className="mb-[0.6rem] inline-block text-[0.92rem]" to="/sites">
        All client sites
      </Link>
      <PageHeading>
        <div>
          <h1>Add a client site</h1>
          <p>Use the roof’s coordinates and planned or installed panel capacity.</p>
        </div>
      </PageHeading>
      <Panel className="max-w-190">
        <SiteForm />
      </Panel>
    </>
  );
}
