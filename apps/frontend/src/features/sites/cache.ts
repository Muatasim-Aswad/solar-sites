import type { QueryClient } from "@tanstack/react-query";
import type { components } from "../../infra/api/schema";

type Site = components["schemas"]["SiteOutput"];
const sitesKey = ["get", "/api/sites"] as const;

function siteQueryKeys(siteId: string) {
  const options = { params: { path: { id: siteId } } };

  // Partial keys match every battery input combination for this site.
  return [
    ["get", "/api/sites/{id}", options],
    ["get", "/api/sites/{id}/production", options],
    ["get", "/api/sites/{id}/battery", options],
  ] as const;
}

export async function cacheSavedSite(queryClient: QueryClient, site: Site) {
  const [siteKey, ...energyKeys] = siteQueryKeys(site.id);
  const affectedKeys = [sitesKey, siteKey, ...energyKeys];

  // Stop older responses from overwriting the saved site or its invalidation state.
  await Promise.all(affectedKeys.map((queryKey) => queryClient.cancelQueries({ queryKey })));
  queryClient.setQueryData(siteKey, site);

  await Promise.all(
    [sitesKey, ...energyKeys].map((queryKey) => queryClient.invalidateQueries({ queryKey })),
  );
}

export async function removeCachedSite(queryClient: QueryClient, siteId: string) {
  const relatedKeys = siteQueryKeys(siteId);

  await Promise.all(
    [sitesKey, ...relatedKeys].map((queryKey) => queryClient.cancelQueries({ queryKey })),
  );
  for (const queryKey of relatedKeys) {
    queryClient.removeQueries({ queryKey });
  }

  queryClient.setQueryData<Site[]>(sitesKey, (sites) =>
    sites?.filter((site) => site.id !== siteId),
  );
  await queryClient.invalidateQueries({ queryKey: sitesKey });
}
