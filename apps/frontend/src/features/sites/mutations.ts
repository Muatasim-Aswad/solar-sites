import { useMutation } from "@tanstack/react-query";
import type { components } from "../../infra/api/schema";
import { useSession } from "../auth/session/SessionProvider";
import { cacheSavedSite, removeCachedSite } from "./cache";

type Site = components["schemas"]["SiteOutput"];
type SiteInput = components["schemas"]["SiteInput"];

export function useCreateSite() {
  const {
    runtime: { client, queryClient },
  } = useSession();

  return useMutation(
    {
      mutationFn: async (body: SiteInput) =>
        requireSite((await client.POST("/api/sites", { body })).data),
      onSuccess: (site) => cacheSavedSite(queryClient, site),
    },
    queryClient,
  );
}

export function useUpdateSite() {
  const {
    runtime: { client, queryClient },
  } = useSession();

  return useMutation(
    {
      mutationFn: async ({ siteId, body }: { siteId: string; body: SiteInput }) =>
        requireSite(
          (await client.PUT("/api/sites/{id}", { params: { path: { id: siteId } }, body })).data,
        ),
      onSuccess: (site) => cacheSavedSite(queryClient, site),
    },
    queryClient,
  );
}

export function useDeleteSite() {
  const {
    runtime: { client, queryClient },
  } = useSession();

  return useMutation(
    {
      mutationFn: async (siteId: string) => {
        await client.DELETE("/api/sites/{id}", { params: { path: { id: siteId } } });
      },
      onSuccess: (_, siteId) => removeCachedSite(queryClient, siteId),
    },
    queryClient,
  );
}

function requireSite(site: Site | undefined): Site {
  if (!site) throw new Error("The server returned no site. Please try again.");
  return site;
}
