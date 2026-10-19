import { Link, Navigate, Outlet, Route, Routes, useLocation } from "react-router";
import { useSession } from "../features/auth/session/SessionProvider";
import { AuthPage } from "../features/auth/AuthPage";
import { SitesPage } from "../features/sites/SitesPage";
import { NewSitePage } from "../features/sites/NewSitePage";
import { EditSitePage } from "../features/sites/EditSitePage";
import { SiteDetailPage } from "../features/sites/SiteDetailPage";
import { ErrorNotice, Loading } from "../shared/ui/feedback";
import { AppLayout } from "./components/AppLayout";

export function AppRoutes() {
  const { state, restore } = useSession();
  if (state.status === "restoring")
    return (
      <div className="mx-auto my-[15vh] max-w-150 p-8">
        <Loading>Restoring your session…</Loading>
      </div>
    );
  if (state.status === "error")
    return (
      <main className="mx-auto my-[15vh] max-w-150 p-8">
        <h1>Unable to restore your session</h1>
        <ErrorNotice error={state.error} retry={() => void restore()} />
      </main>
    );
  return (
    <AppLayout>
      <Routes key={state.status === "authenticated" ? state.email : "anonymous"}>
        <Route path="/login" element={<AuthPage key="login" mode="login" />} />
        <Route path="/register" element={<AuthPage key="register" mode="register" />} />
        <Route element={<PrivateLayout />}>
          <Route path="/sites" element={<SitesPage />} />
          <Route path="/sites/new" element={<NewSitePage />} />
          <Route path="/sites/:id" element={<SiteDetailPage />} />
          <Route path="/sites/:id/edit" element={<EditSitePage />} />
        </Route>
        <Route path="/" element={<Navigate to="/sites" replace />} />
        <Route
          path="*"
          element={
            <main
              id="main"
              className="mx-auto min-h-[calc(100vh-160px)] max-w-300 px-8 pt-10 pb-12 max-compact:px-4 max-compact:py-6"
            >
              <h1>Page not found</h1>
              <Link to="/sites">Return to client sites</Link>
            </main>
          }
        />
      </Routes>
    </AppLayout>
  );
}

function PrivateLayout() {
  const { state } = useSession();
  const location = useLocation();
  if (state.status !== "authenticated") return <Navigate to="/login" replace />;
  return (
    <main
      id="main"
      className="mx-auto min-h-[calc(100vh-160px)] max-w-300 px-8 pt-10 pb-12 max-compact:px-4 max-compact:py-6"
      key={location.pathname}
    >
      <Outlet />
    </main>
  );
}
