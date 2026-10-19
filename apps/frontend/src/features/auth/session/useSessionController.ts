import { useEffect, useEffectEvent, useRef, useState } from "react";
import { createApiRuntime, type ApiRuntime } from "../../../infra/api/runtime";
import type { components } from "../../../infra/api/schema";

type Me = components["schemas"]["MeOutput"];
type Credentials = components["schemas"]["Credentials"];
type SessionState =
  | { status: "restoring" }
  | { status: "anonymous"; expired: boolean }
  | { status: "error"; error: unknown }
  | { status: "authenticated"; email: string };

export function useSessionController() {
  const [state, setState] = useState<SessionState>({ status: "restoring" });
  const active = useRef<ApiRuntime | null>(null);
  const [runtime, setRuntime] = useState(() => makeRuntime());
  active.current = runtime;

  function makeRuntime(): ApiRuntime {
    const next = createApiRuntime(() => {
      // Ignore expired responses from a runtime that has already been replaced.
      if (active.current !== next) return;
      replaceRuntime();
      setState((previous) => ({
        status: "anonymous",
        expired: previous.status === "authenticated",
      }));
    });
    return next;
  }

  function replaceRuntime(token?: string) {
    // Every session gets a fresh cache so private data cannot cross accounts.
    active.current?.dispose();
    const next = makeRuntime();
    if (token) next.setCsrf(token);
    active.current = next;
    setRuntime(next);
    return next;
  }

  function acceptSession(me: Me) {
    replaceRuntime(me.csrfToken);
    setState({ status: "authenticated", email: me.email });
  }

  async function restore() {
    const current = active.current;
    if (!current) return;

    setState({ status: "restoring" });

    try {
      const { data } = await current.client.GET("/api/me");
      if (active.current === current && data) acceptSession(data);
    } catch (error) {
      if (active.current === current) setState({ status: "error", error });
    }
  }

  async function authenticate(mode: "login" | "register", credentials: Credentials) {
    const current = active.current;
    if (!current) return;

    const response =
      mode === "login"
        ? await current.client.POST("/api/login", { body: credentials })
        : await current.client.POST("/api/register", { body: credentials });
    const { data } = response;
    if (!data || active.current !== current) return;

    current.setCsrf(data.csrfToken);
    const me = await current.client.GET("/api/me");
    if (me.data && active.current === current) acceptSession(me.data);
  }

  async function logout() {
    const current = active.current;
    if (!current) return;

    await current.client.POST("/api/logout");
    if (active.current !== current) return;

    replaceRuntime();
    setState({ status: "anonymous", expired: false });
  }

  const restoreOnMount = useEffectEvent(() => {
    void restore();
  });
  useEffect(() => {
    restoreOnMount();
    return () => {
      active.current?.dispose();
    };
  }, []);

  return { state, runtime, authenticate, logout, restore };
}
