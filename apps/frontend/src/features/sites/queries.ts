import { useSession } from "../auth/session/SessionProvider";

export function useSites() {
  const {
    runtime: { api },
  } = useSession();

  return api.useQuery("get", "/api/sites");
}

export function useSite(siteId: string) {
  const {
    runtime: { api },
  } = useSession();

  return api.useQuery("get", "/api/sites/{id}", { params: { path: { id: siteId } } });
}
