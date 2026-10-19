import { createContext, useContext, type ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { useSessionController } from "./useSessionController";

type SessionContextValue = ReturnType<typeof useSessionController>;
const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const session = useSessionController();

  return (
    <SessionContext.Provider value={session}>
      <QueryClientProvider client={session.runtime.queryClient}>{children}</QueryClientProvider>
    </SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) throw new Error("SessionProvider is missing.");

  return context;
}
