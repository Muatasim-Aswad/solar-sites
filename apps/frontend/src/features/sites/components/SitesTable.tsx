import { Link } from "react-router";
import type { components } from "../../../infra/api/schema";
import { number } from "../../../shared/numbers";
import { Panel } from "../../../shared/ui/layout";
import { Table } from "../../../shared/ui/table";

export function SitesTable({ sites }: { sites: components["schemas"]["SiteOutput"][] }) {
  return (
    <Panel padding="none" className="overflow-x-auto" aria-label="Your client sites">
      <Table variant="sites">
        <thead>
          <tr>
            <th scope="col">Client / address</th>
            <th scope="col">Panel capacity</th>
            <th scope="col">Roof area</th>
            <th scope="col">
              <span className="sr-only">Open site</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {sites.map((site) => (
            <tr key={site.id}>
              <th scope="row">
                <Link className="font-bold" to={`/sites/${site.id}`}>
                  {site.clientName}
                </Link>
                <span className="block max-w-[36ch] text-[0.9rem] text-muted wrap-anywhere">
                  {site.address}
                </span>
              </th>
              <td>{number(site.peakKwp)} kWp</td>
              <td>{site.roofAreaM2 == null ? "Not entered" : `${number(site.roofAreaM2)} m²`}</td>
              <td>
                <Link to={`/sites/${site.id}`} aria-label={`View ${site.clientName}`}>
                  View site
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Panel>
  );
}
