import type { components } from "../../../infra/api/schema";
import { coordinate, number } from "../../../shared/numbers";
import { ButtonLink } from "../../../shared/ui/buttons";
import { PageHeading } from "../../../shared/ui/layout";

export function SiteSummary({ site }: { site: components["schemas"]["SiteOutput"] }) {
  return (
    <>
      <PageHeading>
        <div>
          <h1>{site.clientName}</h1>
          <p>{site.address}</p>
        </div>
        <ButtonLink variant="secondary" to={`/sites/${site.id}/edit`}>
          Edit site
        </ButtonLink>
      </PageHeading>
      <dl className="-mt-4 mb-8 flex flex-wrap gap-x-12 gap-y-[1.2rem] border-y border-line py-[1.2rem] tabular-nums">
        <div>
          <dt>Panel capacity</dt>
          <dd>{number(site.peakKwp)} kWp</dd>
        </div>
        <div>
          <dt>Roof area</dt>
          <dd>{site.roofAreaM2 == null ? "Not entered" : `${number(site.roofAreaM2)} m²`}</dd>
        </div>
        <div>
          <dt>Coordinates</dt>
          <dd>
            {coordinate(site.latitude)}°, {coordinate(site.longitude)}°
          </dd>
        </div>
      </dl>
    </>
  );
}
