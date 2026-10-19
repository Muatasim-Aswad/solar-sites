import createFetchClient from "openapi-fetch";
import type { paths } from "./schema";
import { ApiError, readErrorBody } from "./errors";

export function createHttpClient(onExpired: () => void) {
  let csrfToken: string | undefined;
  let disposed = false;
  const client = createFetchClient<paths>({ baseUrl: "/", credentials: "same-origin" });

  client.use({
    onRequest({ request }) {
      if (disposed) throw new Error("This session has ended.");
      if (csrfToken && !["GET", "HEAD"].includes(request.method)) {
        request.headers.set("X-CSRF-Token", csrfToken);
      }
      return request;
    },
    async onResponse({ response, schemaPath }) {
      if (disposed) throw new Error("This session has ended.");
      if (response.ok) return response;

      const envelope: unknown = await response
        .clone()
        .json()
        .catch(() => null);
      const error = new ApiError(response.status, readErrorBody(envelope));

      // Rejected credentials leave the login form active; other 401s end the session.
      if (response.status === 401 && !["/api/login", "/api/register"].includes(schemaPath)) {
        csrfToken = undefined;
        onExpired();
      }
      throw error;
    },
  });

  return {
    client,
    setCsrf(token: string) {
      csrfToken = token;
    },
    dispose() {
      disposed = true;
      csrfToken = undefined;
    },
  };
}
