import type { paths } from "../../infra/api/schema";
import { useSession } from "../auth/session/SessionProvider";

export type BatteryInput = paths["/api/sites/{id}/battery"]["get"]["parameters"]["query"];

export function useProduction(siteId: string) {
  const {
    runtime: { api },
  } = useSession();
  return api.useQuery("get", "/api/sites/{id}/production", { params: { path: { id: siteId } } });
}

export function useBatteryComparison(siteId: string, input: BatteryInput | null) {
  const {
    runtime: { api },
  } = useSession();
  return api.useQuery(
    "get",
    "/api/sites/{id}/battery",
    { params: { path: { id: siteId }, query: input ?? { annualUseKwh: 0, capacityKwh: 0 } } },
    { enabled: input !== null },
  );
}
