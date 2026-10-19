import { afterEach, beforeEach, expect, test } from "vite-plus/test";
import { createApiRuntime, type ApiRuntime } from "../../infra/api/runtime";
import type { components } from "../../infra/api/schema";
import { cacheSavedSite, removeCachedSite } from "./cache";

const site: components["schemas"]["SiteOutput"] = {
  id: "site-a",
  clientName: "Client A",
  address: "Example street 1",
  latitude: 52,
  longitude: 4,
  roofAreaM2: null,
  peakKwp: 5,
};
const otherSite = { ...site, id: "site-b", clientName: "Client B" };
let runtime: ApiRuntime;

beforeEach(() => {
  runtime = createApiRuntime(() => {});
});
afterEach(() => runtime.dispose());

function seedCache() {
  const { api, queryClient } = runtime;
  const path = { id: site.id };
  const otherPath = { id: otherSite.id };
  const keys = {
    list: api.queryOptions("get", "/api/sites").queryKey,
    detail: api.queryOptions("get", "/api/sites/{id}", { params: { path } }).queryKey,
    production: api.queryOptions("get", "/api/sites/{id}/production", { params: { path } })
      .queryKey,
    battery: api.queryOptions("get", "/api/sites/{id}/battery", {
      params: { path, query: { annualUseKwh: 4000, capacityKwh: 5 } },
    }).queryKey,
    largerBattery: api.queryOptions("get", "/api/sites/{id}/battery", {
      params: { path, query: { annualUseKwh: 6000, capacityKwh: 10 } },
    }).queryKey,
    otherDetail: api.queryOptions("get", "/api/sites/{id}", { params: { path: otherPath } })
      .queryKey,
    otherProduction: api.queryOptions("get", "/api/sites/{id}/production", {
      params: { path: otherPath },
    }).queryKey,
    otherBattery: api.queryOptions("get", "/api/sites/{id}/battery", {
      params: { path: otherPath, query: { annualUseKwh: 4000, capacityKwh: 5 } },
    }).queryKey,
    unrelated: ["unrelated"] as const,
  };

  for (const [name, queryKey] of Object.entries(keys)) {
    queryClient.setQueryData(queryKey, name);
  }
  queryClient.setQueryData(keys.list, [site, otherSite]);
  queryClient.setQueryData(keys.detail, site);
  queryClient.getMutationCache().build(queryClient, { mutationKey: ["unrelated-write"] });

  return keys;
}

test("saving a site updates its detail and invalidates only its list and energy results", async () => {
  const keys = seedCache();
  const saved = { ...site, peakKwp: 8 };

  await cacheSavedSite(runtime.queryClient, saved);

  expect(runtime.queryClient.getQueryData(keys.detail)).toEqual(saved);
  expect(runtime.queryClient.getQueryState(keys.detail)?.isInvalidated).toBe(false);
  for (const key of [keys.list, keys.production, keys.battery, keys.largerBattery]) {
    expect(runtime.queryClient.getQueryData(key)).toBeDefined();
    expect(runtime.queryClient.getQueryState(key)?.isInvalidated).toBe(true);
  }
  for (const key of [keys.otherDetail, keys.otherProduction, keys.otherBattery, keys.unrelated]) {
    expect(runtime.queryClient.getQueryData(key)).toBeDefined();
    expect(runtime.queryClient.getQueryState(key)?.isInvalidated).toBe(false);
  }
  expect(runtime.queryClient.getMutationCache().getAll()).toHaveLength(1);
});

test("creating a site seeds its detail and refreshes the site list", async () => {
  const keys = seedCache();
  runtime.queryClient.removeQueries({ queryKey: keys.detail });

  await cacheSavedSite(runtime.queryClient, site);

  expect(runtime.queryClient.getQueryData(keys.detail)).toEqual(site);
  expect(runtime.queryClient.getQueryState(keys.list)?.isInvalidated).toBe(true);
});

test("an older in-flight response cannot overwrite the saved site", async () => {
  const keys = seedCache();
  let resolveOlder!: (value: typeof site) => void;
  const olderResponse = new Promise<typeof site>((resolve) => {
    resolveOlder = resolve;
  });
  const pending = runtime.queryClient
    .query({ queryKey: keys.detail, queryFn: () => olderResponse, staleTime: 0 })
    .catch(() => undefined);
  const saved = { ...site, peakKwp: 8 };

  await cacheSavedSite(runtime.queryClient, saved);
  resolveOlder(site);
  await pending;

  expect(runtime.queryClient.getQueryData(keys.detail)).toEqual(saved);
});

test("deleting a site removes all its cached results while preserving other sites", async () => {
  const keys = seedCache();

  await removeCachedSite(runtime.queryClient, site.id);

  expect(runtime.queryClient.getQueryData(keys.list)).toEqual([otherSite]);
  expect(runtime.queryClient.getQueryState(keys.list)?.isInvalidated).toBe(true);
  for (const key of [keys.detail, keys.production, keys.battery, keys.largerBattery]) {
    expect(runtime.queryClient.getQueryState(key)).toBeUndefined();
  }
  for (const key of [keys.otherDetail, keys.otherProduction, keys.otherBattery, keys.unrelated]) {
    expect(runtime.queryClient.getQueryData(key)).toBeDefined();
    expect(runtime.queryClient.getQueryState(key)?.isInvalidated).toBe(false);
  }
  expect(runtime.queryClient.getMutationCache().getAll()).toHaveLength(1);
});

test("ending a session clears the entire query and mutation cache", () => {
  seedCache();

  runtime.dispose();

  expect(runtime.queryClient.getQueryCache().getAll()).toHaveLength(0);
  expect(runtime.queryClient.getMutationCache().getAll()).toHaveLength(0);
});
