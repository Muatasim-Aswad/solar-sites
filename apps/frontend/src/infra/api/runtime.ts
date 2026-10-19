import { QueryClient } from "@tanstack/react-query";
import createQueryClient from "openapi-react-query";
import { createHttpClient } from "./http";

export function createApiRuntime(onExpired: () => void) {
  const http = createHttpClient(onExpired);
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 30_000,
        refetchOnWindowFocus: false,
      },
      mutations: { retry: false },
    },
  });

  return {
    client: http.client,
    api: createQueryClient(http.client),
    queryClient,
    setCsrf(token: string) {
      http.setCsrf(token);
    },
    dispose() {
      http.dispose();
      void queryClient.cancelQueries();
      queryClient.clear();
    },
  };
}

export type ApiRuntime = ReturnType<typeof createApiRuntime>;
