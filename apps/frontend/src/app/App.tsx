import { BrowserRouter } from "react-router";
import { SessionProvider } from "../features/auth/session/SessionProvider";
import { AppRoutes } from "./AppRoutes";
import { AppErrorBoundary } from "./components/AppErrorBoundary";

export function App() {
  return (
    <AppErrorBoundary>
      <BrowserRouter>
        <SessionProvider>
          <AppRoutes />
        </SessionProvider>
      </BrowserRouter>
    </AppErrorBoundary>
  );
}
